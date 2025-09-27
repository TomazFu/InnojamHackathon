import pandas as pd
import streamlit as st
from datetime import datetime

@st.cache_data
def load_all_data():
    """Load all pharmacy datasets with caching"""
    try:
        sales = pd.read_csv('data/sales.csv')
        customers = pd.read_csv('data/customers.csv')
        inventory = pd.read_csv('data/inventory.csv')
        staff = pd.read_csv('data/staff.csv')
        disease_alerts = pd.read_csv('data/disease_alerts.csv')
        campaigns = pd.read_csv('data/campaigns.csv')
        branches = pd.read_csv('data/branches.csv')
        
        return sales, customers, inventory, staff, disease_alerts, campaigns, branches
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        st.info("Please run: python generate_pharmacy_data.py")
        st.stop()

def filter_by_branch(df, branch_name):
    """Filter dataframe by branch"""
    if branch_name == 'All Branches':
        return df
    return df[df['branch_name'] == branch_name]

def filter_by_date_range(df, start_date, end_date):
    """Filter dataframe by date range"""
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    return df_copy[(df_copy['date'] >= pd.to_datetime(start_date)) & 
                   (df_copy['date'] <= pd.to_datetime(end_date))]

def get_branch_list(branches_df):
    """Get list of branch names"""
    return ['All Branches'] + branches_df['name'].tolist()

def calculate_metrics(sales_df, customers_df, inventory_df):
    """Calculate key business metrics"""
    metrics = {
        'total_revenue': sales_df['amount'].sum(),
        'total_transactions': len(sales_df),
        'avg_transaction': sales_df['amount'].mean(),
        'total_customers': len(customers_df),
        'chronic_patients': len(customers_df[customers_df['has_chronic'] == True]),
        'critical_stock_items': len(inventory_df[inventory_df['status'] == 'Critical']),
        'prescription_rate': (len(sales_df[sales_df['is_prescription'] == True]) / len(sales_df) * 100),
        'total_units_sold': sales_df['quantity'].sum()
    }
    return metrics