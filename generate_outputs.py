"""
Run this script to generate all output images into outputs/
python generate_outputs.py
"""
import os, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix, precision_recall_curve, f1_score, precision_score, recall_score
from xgboost import XGBClassifier
import shap
from mlxtend.frequent_patterns import fpgrowth, association_rules as mlxtend_rules

os.makedirs("outputs", exist_ok=True)

GRADE_MAP = {"A":1,"B":2,"C":3,"D":4,"E":5,"F":6,"G":7}
NUMERIC_COLS = ["person_age","person_income","person_emp_length","loan_amnt","loan_int_rate","loan_percent_income","debt_to_income"]
MEDIAN_IMPUTE = ["loan_int_rate","person_emp_length"]
REQUIRED = ["person_age","person_income","person_emp_length","loan_amnt","loan_int_rate",
            "loan_percent_income","loan_grade","loan_intent","home_ownership","cb_person_default_on_file","loan_status"]
INTENT_PRODUCT = {"EDUCATION":["Student Loan","Credit Card"],"MEDICAL":["Health Insurance","Personal Loan"],
                  "VENTURE":["Business Loan","Investment Account"],"PERSONAL":["Personal Loan","Credit Card"],
                  "HOMEIMPROVEMENT":["Home Loan","Savings Account"],"DEBTCONSOLIDATION":["Balance Transfer Card","Personal Loan"]}
GRADE_PRODUCT = {"A":["Investment Account","Premium Credit Card"],"B":["Investment Account"],"C":["Savings Account"]}

class FeatureEngineer:
    def __init__(self): self.scaler=StandardScaler(); self.medians={}; self.encoded_columns=[]
    def _base(self,X):
        X=X.copy()
        for c in MEDIAN_IMPUTE: X[c]=X[c].fillna(self.medians.get(c,0))
        X["debt_to_income"]=(X["loan_amnt"]/X["person_income"].replace(0,np.nan)).fillna(0)
        X["loan_grade"]=X["loan_grade"].map(GRADE_MAP)
        X["cb_person_default_on_file"]=(X["cb_person_default_on_file"]=="Y").astype(int)
        return pd.get_dummies(X,columns=["loan_intent","home_ownership"])
    def fit_transform(self,X):
        for c in MEDIAN_IMPUTE: self.medians[c]=X[c].median()
        out=self._base(X); self.encoded_columns=out.columns.tolist(); return out
    def transform(self,X):
        out=self._base(X)
        for c in self.encoded_columns:
            if c not in out.columns: out[c]=0
        return out[self.encoded_columns]
    def fit_transform_scaled(self,X):
        enc=self.fit_transform(X); sc=enc.copy()
        p=[c for c in NUMERIC_COLS if c in sc.columns]
        sc[p]=self.scaler.fit_transform(enc[p]); return sc
    def transform_scaled(self,X):
        enc=self.transform(X); sc=enc.copy()
        p=[c for c in NUMERIC_COLS if c in sc.columns]
        sc[p]=self.scaler.transform(enc[p]); return sc

def make_demo_data(n=5000,seed=42):
    rng=np.random.default_rng(seed)
    grades=rng.choice(["A","B","C","D","E","F","G"],n,p=[.15,.20,.22,.18,.12,.08,.05])
    intents=rng.choice(["EDUCATION","MEDICAL","VENTURE","PERSONAL","HOMEIMPROVEMENT","DEBTCONSOLIDATION"],n)
    owners=rng.choice(["RENT","MORTGAGE","OWN","OTHER"],n,p=[.40,.35,.20,.05])
    cb=rng.choice(["N","Y"],n,p=[.78,.22])
    age=rng.integers(20,70,n); income=rng.integers(15000,180000,n)
    emp=rng.uniform(0,30,n); loan=rng.integers(1000,35000,n); rate=rng.uniform(5,24,n)
    pct=loan/income; gnum=np.array([GRADE_MAP[g] for g in grades])
    logit=-3+0.4*gnum+0.06*rate-0.00002*income+0.5*(cb=="Y").astype(int)+rng.normal(0,0.5,n)
    prob=1/(1+np.exp(-logit)); status=(rng.random(n)<prob).astype(int)
    return pd.DataFrame({"person_age":age,"person_income":income,"person_emp_length":emp,
        "loan_amnt":loan,"loan_int_rate":rate,"loan_percent_income":pct,"loan_grade":grades,
        "loan_intent":intents,"home_ownership":owners,"cb_person_default_on_file":cb,"loan_status":status})

print("Loading data...")
if os.path.exists("data/credit_risk_dataset.csv"):
    df = pd.read_csv("data/credit_risk_dataset.csv")[REQUIRED].copy()
    print("  Using Kaggle dataset")
else:
    df = make_demo_data()
    print("  Using synthetic demo data")

X=df.drop(columns=["loan_status"]); y=df["loan_status"]
X_tr,X_tmp,y_tr,y_tmp=train_test_split(X,y,test_size=.30,stratify=y,random_state=42)
X_val,X_te,y_val,y_te=train_test_split(X_tmp,y_tmp,test_size=.50,stratify=y_tmp,random_state=42)

fe=FeatureEngineer()
X_tr_sc=fe.fit_transform_scaled(X_tr); X_val_sc=fe.transform_scaled(X_val); X_te_sc=fe.transform_scaled(X_te)
X_tr_enc=fe.transform(X_tr); X_val_enc=fe.transform(X_val); X_te_enc=fe.transform(X_te)
fn=X_te_enc.columns.tolist()

print("Training models...")
lr=LogisticRegression(solver="lbfgs",max_iter=1000,class_weight="balanced",random_state=42)
lr.fit(X_tr_sc,y_tr)
spw=float((y_tr==0).sum()/(y_tr==1).sum())
xgb=XGBClassifier(scale_pos_weight=spw,max_depth=5,learning_rate=0.05,n_estimators=200,
                   subsample=0.8,colsample_bytree=0.8,random_state=42,eval_metric="auc",verbosity=0)
xgb.fit(X_tr_enc,y_tr)

p_,r_,t_=precision_recall_curve(y_val,xgb.predict_proba(X_val_enc)[:,1])
f1s=2*p_*r_/(p_+r_+1e-9); threshold=float(t_[np.argmax(f1s[:-1])])
print(f"  Threshold: {threshold:.4f}")

lr_proba=lr.predict_proba(X_te_sc)[:,1]; xgb_proba=xgb.predict_proba(X_te_enc)[:,1]
xgb_pred=(xgb_proba>=threshold).astype(int)
print(f"  LR  AUC={roc_auc_score(y_te,lr_proba):.3f}")
print(f"  XGB AUC={roc_auc_score(y_te,xgb_proba):.3f}")

explainer=shap.TreeExplainer(xgb)
sv=explainer.shap_values(X_te_enc)
sv=sv[1] if isinstance(sv,list) else sv

plt.style.use("default")
sns.set_style("whitegrid")

# 1. ROC Curves
print("Saving outputs/roc_curves.png")
fig,ax=plt.subplots(figsize=(7,5)); fig.patch.set_facecolor("white")
for name,proba,color in [("Logistic Regression",lr_proba,"#635bff"),("XGBoost",xgb_proba,"#00c896")]:
    fpr,tpr,_=roc_curve(y_te,proba); auc=roc_auc_score(y_te,proba)
    ax.plot(fpr,tpr,color=color,lw=2.5,label=f"{name} (AUC={auc:.3f})")
ax.plot([0,1],[0,1],"--",color="#b0bec5",lw=1.5,label="Random Classifier")
ax.set_xlabel("False Positive Rate",fontsize=11); ax.set_ylabel("True Positive Rate",fontsize=11)
ax.set_title("ROC Curves — Model Comparison",fontsize=13,fontweight="bold",pad=12)
ax.legend(fontsize=9); ax.set_facecolor("#fafbfd")
plt.tight_layout(); plt.savefig("outputs/roc_curves.png",dpi=150,bbox_inches="tight"); plt.close()

# 2. Confusion Matrix
print("Saving outputs/confusion_matrix.png")
cm=confusion_matrix(y_te,xgb_pred)
fig,ax=plt.subplots(figsize=(5,4)); fig.patch.set_facecolor("white")
sns.heatmap(cm,annot=True,fmt="d",cmap="Blues",ax=ax,
            xticklabels=["No Default","Default"],yticklabels=["No Default","Default"],
            annot_kws={"size":14,"weight":"bold"})
ax.set_xlabel("Predicted",fontsize=10); ax.set_ylabel("Actual",fontsize=10)
ax.set_title("Confusion Matrix — XGBoost",fontsize=13,fontweight="bold",pad=10)
plt.tight_layout(); plt.savefig("outputs/confusion_matrix.png",dpi=150,bbox_inches="tight"); plt.close()

# 3. SHAP Importance
print("Saving outputs/shap_importance.png")
mean_abs=np.abs(sv).mean(axis=0); top10=np.argsort(mean_abs)[-10:]
fig,ax=plt.subplots(figsize=(8,5)); fig.patch.set_facecolor("white")
colors_bar=["#635bff" if mean_abs[i]>np.median(mean_abs) else "#a89fff" for i in top10]
ax.barh([fn[i][:25] for i in top10],mean_abs[top10],color=colors_bar,edgecolor="white")
ax.set_xlabel("Mean |SHAP Value|",fontsize=11)
ax.set_title("Top 10 Feature Importances (SHAP)",fontsize=13,fontweight="bold",pad=10)
ax.set_facecolor("#fafbfd"); ax.grid(alpha=0.3,axis="x")
plt.tight_layout(); plt.savefig("outputs/shap_importance.png",dpi=150,bbox_inches="tight"); plt.close()

# 4. Default Rate by Grade
print("Saving outputs/default_by_grade.png")
gr=df.groupby("loan_grade")["loan_status"].mean().reindex(["A","B","C","D","E","F","G"])
fig,ax=plt.subplots(figsize=(7,4)); fig.patch.set_facecolor("white")
palette=["#00c896","#3dd9ac","#ffa502","#ff7043","#ff5252","#ff4757","#cc2233"]
bars=ax.bar(gr.index,gr.values,color=palette,edgecolor="white",width=0.6)
ax.set_ylabel("Default Rate",fontsize=11); ax.set_xlabel("Loan Grade",fontsize=11)
ax.set_title("Default Rate by Loan Grade",fontsize=13,fontweight="bold",pad=10)
ax.set_ylim(0,1); ax.set_facecolor("#fafbfd"); ax.grid(alpha=0.3,axis="y")
for b,v in zip(bars,gr.values):
    ax.text(b.get_x()+b.get_width()/2,v+0.02,f"{v:.0%}",ha="center",fontsize=9,fontweight="bold")
plt.tight_layout(); plt.savefig("outputs/default_by_grade.png",dpi=150,bbox_inches="tight"); plt.close()

# 5. EDA overview
print("Saving outputs/eda_overview.png")
fig,axes=plt.subplots(2,3,figsize=(15,8)); fig.patch.set_facecolor("white")
fig.suptitle("Exploratory Data Analysis — Credit Risk Dataset",fontsize=14,fontweight="bold",y=1.01)
counts=df["loan_status"].value_counts()
axes[0,0].bar(["No Default","Default"],[counts[0],counts[1]],color=["#00c896","#ff4757"],width=0.5,edgecolor="white")
axes[0,0].set_title("Class Distribution"); axes[0,0].set_facecolor("#fafbfd")
axes[0,1].hist(df["person_age"],bins=30,color="#635bff",edgecolor="white",alpha=0.85)
axes[0,1].set_title("Age Distribution"); axes[0,1].set_facecolor("#fafbfd")
axes[0,2].hist(df["person_income"].clip(upper=200000),bins=30,color="#00c896",edgecolor="white",alpha=0.85)
axes[0,2].set_title("Income Distribution (capped 200K)"); axes[0,2].set_facecolor("#fafbfd")
axes[1,0].bar(gr.index,gr.values,color=palette,edgecolor="white")
axes[1,0].set_title("Default Rate by Grade"); axes[1,0].set_facecolor("#fafbfd")
df[df["loan_status"]==0]["loan_int_rate"].dropna().hist(ax=axes[1,1],bins=20,alpha=0.65,label="No Default",color="#00c896")
df[df["loan_status"]==1]["loan_int_rate"].dropna().hist(ax=axes[1,1],bins=20,alpha=0.65,label="Default",color="#ff4757")
axes[1,1].set_title("Interest Rate by Status"); axes[1,1].legend(fontsize=8); axes[1,1].set_facecolor("#fafbfd")
ic=df["loan_intent"].value_counts()
axes[1,2].barh(ic.index,ic.values,color="#635bff",alpha=0.8,edgecolor="white")
axes[1,2].set_title("Loan Intent Distribution"); axes[1,2].set_facecolor("#fafbfd")
plt.tight_layout(); plt.savefig("outputs/eda_overview.png",dpi=150,bbox_inches="tight"); plt.close()

# 6. PR curve
print("Saving outputs/pr_curve.png")
p,r,t=precision_recall_curve(y_te,xgb_proba)
fig,ax=plt.subplots(figsize=(6,4)); fig.patch.set_facecolor("white")
ax.plot(r[:-1],p[:-1],color="#635bff",lw=2.5)
idx=int(np.argmin(np.abs(t-threshold)))
ax.scatter([r[idx]],[p[idx]],color="#ff4757",s=100,zorder=5,label=f"Threshold={threshold:.2f}")
ax.set_xlabel("Recall",fontsize=11); ax.set_ylabel("Precision",fontsize=11)
ax.set_title("Precision-Recall Curve (XGBoost)",fontsize=13,fontweight="bold",pad=10)
ax.legend(fontsize=9); ax.set_facecolor("#fafbfd")
plt.tight_layout(); plt.savefig("outputs/pr_curve.png",dpi=150,bbox_inches="tight"); plt.close()

print("\nAll output images saved to outputs/")
for f in sorted(os.listdir("outputs")):
    print(f"  outputs/{f}")
