import pandas as pd
import numpy as np
import os
import json

def generate_synthetic_data(num_samples=1000):
    np.random.seed(42)
    
    # 1. Customer Demographics
    ages = np.random.randint(21, 75, num_samples)
    incomes = np.random.lognormal(mean=11.0, sigma=0.8, size=num_samples) # Roughly 20k to 200k+
    incomes = np.clip(incomes, 20000, 500000)
    employment_lengths = np.random.randint(0, 40, num_samples)
    credit_scores = np.random.normal(loc=650, scale=80, size=num_samples)
    credit_scores = np.clip(credit_scores, 300, 850).astype(int)
    
    # 2. Loan Details
    loan_amounts = np.random.lognormal(mean=9.5, sigma=1.0, size=num_samples)
    loan_amounts = np.clip(loan_amounts, 1000, 100000)
    
    # Risk factors logic
    # Higher risk if: low income, low credit score, high loan amount relative to income
    dti = loan_amounts / (incomes + 1)
    
    # Calculate base risk score (higher is riskier)
    risk_score_raw = (
        -0.005 * credit_scores + 
        0.5 * dti + 
        -0.00001 * incomes + 
        -0.02 * employment_lengths + 
        np.random.normal(0, 0.5, num_samples)
    )
    
    # Normalize risk score to probability
    probability_of_default = 1 / (1 + np.exp(-risk_score_raw))
    
    # Assign default status based on probability
    defaults = (np.random.rand(num_samples) < probability_of_default).astype(int)
    
    # Create DataFrame for Risk Model
    df_risk = pd.DataFrame({
        'customer_id': range(1, num_samples + 1),
        'age': ages,
        'income': incomes,
        'employment_length': employment_lengths,
        'credit_score': credit_scores,
        'loan_amount': loan_amounts,
        'default': defaults
    })
    
    # 3. Product Ownership (for Cross-Sell)
    # Products: 'Checking', 'Savings', 'Credit Card', 'Auto Loan', 'Mortgage', 'Personal Loan', 'Investment'
    products = ['Checking', 'Savings', 'Credit Card', 'Auto Loan', 'Mortgage', 'Personal Loan', 'Investment']
    
    customer_products = []
    
    for _, row in df_risk.iterrows():
        owned = ['Checking'] # everyone has checking
        
        if np.random.rand() > 0.3:
            owned.append('Savings')
            
        if row['credit_score'] > 600 and np.random.rand() > 0.4:
            owned.append('Credit Card')
            
        # Rules to create associations
        if row['income'] > 80000 and row['credit_score'] > 700 and np.random.rand() > 0.5:
            owned.append('Mortgage')
            
        if 'Mortgage' in owned and np.random.rand() > 0.3:
            owned.append('Investment') # Association: Mortgage -> Investment
            
        if np.random.rand() > 0.7:
            owned.append('Auto Loan')
            
        if 'Auto Loan' in owned and row['credit_score'] > 650 and np.random.rand() > 0.4:
            owned.append('Credit Card') # Association: Auto Loan -> Credit Card
            
        if row['credit_score'] < 650 and np.random.rand() > 0.6:
            owned.append('Personal Loan')
            
        customer_products.append(owned)
        
    # Create a DataFrame of binary flags for products
    product_dict = {p: [] for p in products}
    for owned in customer_products:
        for p in products:
            product_dict[p].append(1 if p in owned else 0)
            
    df_products = pd.DataFrame(product_dict)
    df_products['customer_id'] = df_risk['customer_id']
    
    # Merge datasets
    df_final = pd.merge(df_risk, df_products, on='customer_id')
    
    return df_final

if __name__ == "__main__":
    print("Generating synthetic data...")
    df = generate_synthetic_data(2000)
    
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/banking_data.csv', index=False)
    print("Data saved to data/banking_data.csv")
    
    # Save a sample customer to json for easy frontend testing
    sample_customers = df.head(10).to_dict(orient='records')
    with open('data/sample_customers.json', 'w') as f:
        json.dump(sample_customers, f, indent=4)
