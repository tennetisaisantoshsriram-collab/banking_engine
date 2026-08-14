import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sklearn.ensemble import RandomForestClassifier
from pydantic import BaseModel
import os
import random
import json
import hashlib
import secrets

app = FastAPI(title="Legendary Banking AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

data = None
rf_model = None
feature_cols = ['age', 'income', 'employment_length', 'credit_score', 'loan_amount']
product_cols = ['Checking', 'Savings', 'Credit Card', 'Auto Loan', 'Mortgage', 'Personal Loan', 'Investment']
cross_sell_rules = {}
portfolio_stats = {}

class SimulationRequest(BaseModel):
    customer_id: int
    age: int
    income: float
    employment_length: int
    credit_score: int
    loan_amount: float
    environment: str = "Neutral"

def train_models():
    global data, rf_model, cross_sell_rules, portfolio_stats
    print("Loading data and training models...")
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'banking_data.csv')
    data = pd.read_csv(data_path)
    
    # 1. Train Risk Model
    X = data[feature_cols]
    y = data['default']
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X, y)
    
    # 2. Compute Cross-Sell Rules
    for product in product_cols:
        cross_sell_rules[product] = {}
        users_with_product = data[data[product] == 1]
        for other_product in product_cols:
            if product == other_product: continue
            prob = len(users_with_product[users_with_product[other_product] == 1]) / len(users_with_product) if len(users_with_product) > 0 else 0
            cross_sell_rules[product][other_product] = prob
            
    # 3. Compute Portfolio Stats for Dashboard
    portfolio_stats = {
        "total_customers": len(data),
        "total_loan_exposure": float(data['loan_amount'].sum()),
        "average_credit_score": float(data['credit_score'].mean()),
        "avg_default_rate": float(data['default'].mean() * 100),
        "product_adoption": {p: int(data[p].sum()) for p in product_cols}
    }

@app.on_event("startup")
async def startup_event():
    train_models()
    users = load_users()
    if "demo" not in users:
        users["demo"] = hash_password("demo123")
        save_users(users)
        print("Demo user created: demo / demo123")

@app.get("/api/portfolio")
async def get_portfolio():
    return portfolio_stats

@app.get("/api/customers")
async def get_customers():
    return data[['customer_id', 'age', 'income', 'credit_score']].head(100).to_dict(orient='records')

def calculate_shap_approximation(cust, prob_default):
    base_value = 25.0 
    
    cs_impact = ((650 - cust['credit_score']) / 100) * 15
    inc_impact = ((60000 - cust['income']) / 40000) * 10
    emp_impact = ((5 - cust['employment_length']) / 5) * 5
    dti = cust['loan_amount'] / max(cust['income'], 1)
    dti_impact = (dti - 0.3) * 30
    
    total_impact = cs_impact + inc_impact + emp_impact + dti_impact
    diff = (prob_default * 100) - base_value
    scale = diff / total_impact if total_impact != 0 else 0
    
    return [
        {"feature": "Credit Score", "impact": round(cs_impact * scale, 1), "value": int(cust['credit_score'])},
        {"feature": "Income", "impact": round(inc_impact * scale, 1), "value": f"${int(cust['income'])}"},
        {"feature": "Debt-to-Income", "impact": round(dti_impact * scale, 1), "value": f"{round(dti*100, 1)}%"},
        {"feature": "Employment", "impact": round(emp_impact * scale, 1), "value": f"{int(cust['employment_length'])} yrs"}
    ], base_value

def calculate_fraud_and_clv(cust):
    # Simulate a sophisticated Fraud score based on anomalies
    # e.g., very high income but very low credit score
    fraud_prob = 1.0
    if cust['income'] > 150000 and cust['credit_score'] < 500:
        fraud_prob += 45.0
    if cust['employment_length'] == 0 and cust['loan_amount'] > 50000:
        fraud_prob += 30.0
    fraud_prob += random.uniform(0.5, 5.0)
    
    # Simulate Customer Lifetime Value (CLV)
    # Base CLV is 5% of income, modified by credit score
    clv = (cust['income'] * 0.05) * (cust['credit_score'] / 600)
    
    return min(fraud_prob, 99.9), round(clv, 2)

@app.post("/api/simulate")
async def simulate_scenario(req: SimulationRequest):
    # This endpoint recalculates Risk, SHAP, Fraud, and CLV based on slider inputs
    cust = req.dict()
    
    X_cust = pd.DataFrame([cust])[feature_cols]
    prob_default = rf_model.predict_proba(X_cust)[0][1]
    
    shap_values, base_value = calculate_shap_approximation(cust, prob_default)
    fraud_prob, clv = calculate_fraud_and_clv(cust)
    
    if req.environment == "Recession":
        prob_default = min(prob_default * 1.5, 0.99)
        clv = max(clv * 0.7, 0)
    elif req.environment == "High Interest":
        prob_default = min(prob_default * 1.2, 0.99)
        clv = max(clv * 0.85, 0)
    elif req.environment == "Booming":
        prob_default = max(prob_default * 0.7, 0.01)
        clv = clv * 1.3
        
    return {
        "risk_assessment": {
            "default_probability": round(prob_default * 100, 1),
            "risk_level": "High" if prob_default > 0.5 else "Medium" if prob_default > 0.2 else "Low"
        },
        "advanced_metrics": {
            "fraud_probability": round(fraud_prob, 1),
            "clv": clv
        },
        "xai": {
            "base_value": base_value,
            "shap_values": shap_values
        }
    }

@app.get("/api/customers/{customer_id}")
async def get_customer_details(customer_id: int):
    customer_data = data[data['customer_id'] == customer_id]
    if customer_data.empty: raise HTTPException(status_code=404)
    cust = customer_data.iloc[0].to_dict()
    
    X_cust = pd.DataFrame([cust])[feature_cols]
    prob_default = rf_model.predict_proba(X_cust)[0][1]
    
    shap_values, base_value = calculate_shap_approximation(cust, prob_default)
    fraud_prob, clv = calculate_fraud_and_clv(cust)
    
    owned_products = [p for p in product_cols if cust[p] == 1]
    unowned = [p for p in product_cols if cust[p] == 0]
    
    recs = []
    for un in unowned:
        score = sum([cross_sell_rules[owned].get(un, 0) for owned in owned_products])
        if un == 'Mortgage' and cust['income'] > 80000: score += 1.0
        if un == 'Investment' and cust['income'] > 100000: score += 0.8
        
        recs.append({
            "product": un,
            "confidence": min(score / max(len(owned_products), 1) * 100, 95) + (np.random.rand()*5),
            "reasons": [f"High profile affinity"]
        })
    recs.sort(key=lambda x: x['confidence'], reverse=True)
    top_recs = recs[:3]
    for r in top_recs: r['confidence'] = round(r['confidence'], 1)
    
    return {
        "customer": {
            "customer_id": int(cust['customer_id']),
            "age": int(cust['age']),
            "income": float(cust['income']),
            "employment_length": int(cust['employment_length']),
            "credit_score": int(cust['credit_score']),
            "loan_amount": float(cust['loan_amount']),
            "owned_products": owned_products
        },
        "risk_assessment": {
            "default_probability": round(prob_default * 100, 1),
            "risk_level": "High" if prob_default > 0.5 else "Medium" if prob_default > 0.2 else "Low"
        },
        "advanced_metrics": {
            "fraud_probability": round(fraud_prob, 1),
            "clv": clv
        },
        "xai": {
            "base_value": base_value,
            "shap_values": shap_values
        },
        "recommendations": top_recs
    }

@app.get("/api/portfolio/scatter")
async def get_scatter_data():
    sample = data.sample(min(100, len(data)))
    X_sample = sample[feature_cols]
    probs = rf_model.predict_proba(X_sample)[:, 1] * 100
    
    scatter_data = []
    for i in range(len(sample)):
        scatter_data.append({
            "income": float(sample.iloc[i]['income']),
            "prob": float(probs[i])
        })
    return {"scatter": scatter_data}

@app.get("/api/customers/{customer_id}/history")
async def get_customer_history(customer_id: int):
    cust_row = data[data['customer_id'] == customer_id]
    if len(cust_row) == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    cust = cust_row.iloc[0]
    
    events = []
    events.append({
        "date": "5 years ago",
        "title": "Account Opened",
        "description": "Customer opened initial checking account.",
        "icon": "🏦"
    })
    
    if cust['loan_amount'] > 30000:
        events.append({
            "date": "3 years ago",
            "title": "Major Loan Originated",
            "description": f"Took out a large loan of ${int(cust['loan_amount']):,}.",
            "icon": "🏠"
        })
        
    if cust['credit_score'] < 650:
        events.append({
            "date": "1 year ago",
            "title": "Credit Score Drop",
            "description": "Late payments reported to bureaus.",
            "icon": "⚠️"
        })
        
    if cust['income'] > 80000:
        events.append({
            "date": "6 months ago",
            "title": "Wealth Management Inquiry",
            "description": "Customer inquired about investment portfolios.",
            "icon": "📈"
        })
        
    events.append({
        "date": "Today",
        "title": "Credit Application",
        "description": "Applying for new loan product.",
        "icon": "📝"
    })
    
    return {"history": events}

NOTES_FILE = "notes.json"

SESSIONS: dict = {}  # token -> username (in-memory, cleared on restart)
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users: dict) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class AuthRequest(BaseModel):
    username: str
    password: str

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_notes(notes):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f)

class NoteRequest(BaseModel):
    note: str

@app.get("/api/customers/{customer_id}/notes")
async def get_customer_notes(customer_id: str):
    notes = load_notes()
    return {"notes": notes.get(customer_id, "")}

@app.post("/api/customers/{customer_id}/notes")
async def save_customer_note(customer_id: str, req: NoteRequest):
    notes = load_notes()
    notes[customer_id] = req.note
    save_notes(notes)
    return {"status": "success"}

@app.post("/api/auth/signup")
async def signup(req: AuthRequest):
    if len(req.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    users = load_users()
    if req.username in users:
        raise HTTPException(status_code=400, detail="Username already exists")
    users[req.username] = hash_password(req.password)
    save_users(users)
    token = secrets.token_hex(32)
    SESSIONS[token] = req.username
    return {"token": token, "username": req.username}

@app.post("/api/auth/login")
async def login(req: AuthRequest):
    users = load_users()
    stored = users.get(req.username)
    if not stored or stored != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = secrets.token_hex(32)
    SESSIONS[token] = req.username
    return {"token": token, "username": req.username}

@app.get("/api/auth/verify")
async def verify_token(token: str):
    username = SESSIONS.get(token)
    if username:
        return {"valid": True, "username": username}
    raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

# Serve frontend static files (must come AFTER all API routes)
_frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
