import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import utilities
from utils.data_loader import (
    load_all_data, 
    filter_by_branch, 
    filter_by_date_range,
    get_branch_list,
    calculate_metrics
)

# Import components
from components.customer_analytics import render_customer_analytics
from components.disease_prediction import render_disease_prediction
from components.inventory_manager import render_inventory_management
from components.staff_optimizer import render_staff_optimization
from components.campaign_intelligence import render_campaign_intelligence
from components.regional_intelligence import render_regional_intelligence

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="PharmaFlow AI",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #4A90E2;
        --secondary-color: #7B68EE;
        --success-color: #00C851;
        --warning-color: #ffbb33;
        --danger-color: #ff4444;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: black;
        margin-bottom: 20px;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 10px 20px;
        background-color: #f0f2f6;
        border-radius: 5px;
        font-weight: 500;
        color: black;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: black;
    }
    
    /* Alert styling */
    .alert-critical {
        background-color: #ffe6e6;
        border-left: 4px solid #ff4444;
        padding: 10px;
        border-radius: 5px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD DATA
# ============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_data():
    return load_all_data()

# Cache clearing button for testing
if st.sidebar.button("🔄 Clear Cache & Reload Data"):
    st.cache_data.clear()
    st.rerun()

try:
    sales_df, customer_df, inventory_df, staff_df, disease_df, campaigns_df, branches_df = get_data()
    COMPANY_NAME = "Guardian Pharmacy"
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please run: `python generate_pharmacy_data.py` first")
    st.stop()

# ============================================================================
# SIDEBAR NAVIGATION & FILTERS
# ============================================================================

with st.sidebar:
    # Company Logo/Header
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h2 style='margin: 5px 0;'>PharmaFlow AI</h2>
        <p style='color: #666; margin: 0;'>Intelligent Pharmacy Analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Filters Section
    st.header("🎛️ Filters")
    
    # Branch filter
    branch_list = get_branch_list(branches_df)
    selected_branch = st.selectbox(
        "Select Branch",
        branch_list,
        help="Filter data by specific branch or view all"
    )
    
    # Date range filter
    min_date = pd.to_datetime(sales_df['date'].min()).date()
    max_date = pd.to_datetime(sales_df['date'].max()).date()
    
    date_range = st.date_input(
        "Date Range",
        value=(max_date - timedelta(days=30), max_date),
        min_value=min_date,
        max_value=max_date,
        help="Select date range for analysis"
    )
    
    st.divider()
    
    # Quick Stats
    st.header("📊 Quick Stats")
    
    # Apply filters for stats
    filtered_sales = filter_by_branch(sales_df, selected_branch)
    filtered_customers = filter_by_branch(customer_df, selected_branch) if 'branch_name' in customer_df.columns else customer_df
    
    if len(date_range) == 2:
        filtered_sales = filter_by_date_range(filtered_sales, date_range[0], date_range[1])
    
    # Calculate metrics
    total_revenue = filtered_sales['amount'].sum()
    total_transactions = len(filtered_sales)
    avg_transaction = filtered_sales['amount'].mean() if len(filtered_sales) > 0 else 0
    
    st.metric("Revenue", f"${total_revenue:,.0f}")
    st.metric("Transactions", f"{total_transactions:,}")
    st.metric("Avg Transaction", f"${avg_transaction:.2f}")
    
    # Branch info
    if selected_branch != 'All Branches':
        branch_info = branches_df[branches_df['name'] == selected_branch].iloc[0]
        st.info(f"**District:** {branch_info['district']}")
    
    st.divider()
    
    # System Status
    st.header("🚦 System Status")
    
    critical_alerts = len(disease_df[disease_df['alert_level'] == 'Critical'])
    critical_stock = len(inventory_df[inventory_df['status'] == 'Critical'])
    
    if critical_alerts > 0:
        st.error(f"{critical_alerts} Disease Alerts")
    else:
        st.success("No Disease Alerts")
    
    if critical_stock > 0:
        st.warning(f"📦 {critical_stock} Stock Alerts")
    else:
        st.success("Stock Healthy")
    
    st.divider()
    
    # Footer
    st.caption(f"{COMPANY_NAME}")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ============================================================================
# MAIN HEADER
# ============================================================================

st.markdown(f"""
<div class='main-header'>
    <h1>{COMPANY_NAME} - PharmaFlow AI</h1>
    <p style='margin: 5px 0 0 0; opacity: 0.9;'>
        AI-Powered Pharmacy Analytics & Health Intelligence Platform
    </p>
</div>
""", unsafe_allow_html=True)

# Key Business Metrics Row
col1, col2, col3, col4, col5, col6 = st.columns(6)

metrics = calculate_metrics(filtered_sales, customer_df, inventory_df)

with col1:
    st.metric(
        "Total Revenue",
        f"${metrics['total_revenue']:,.0f}",
        delta="+12.3%"
    )

with col2:
    st.metric(
        "Customers",
        f"{metrics['total_customers']:,}",
        delta="+8.5%"
    )

with col3:
    st.metric(
        "Chronic Patients",
        f"{metrics['chronic_patients']:,}",
        delta=f"{(metrics['chronic_patients']/metrics['total_customers']*100):.1f}%"
    )

with col4:
    st.metric(
        "Prescription Rate",
        f"{metrics['prescription_rate']:.1f}%",
        delta="Target: 35%"
    )

with col5:
    st.metric(
        "Stock Alerts",
        metrics['critical_stock_items'],
        delta="Critical" if metrics['critical_stock_items'] > 0 else "Good",
        delta_color="inverse" if metrics['critical_stock_items'] > 0 else "off"
    )

with col6:
    disease_alerts = len(disease_df[disease_df['alert_level'].isin(['Critical', 'Warning'])])
    st.metric(
        "Health Alerts",
        disease_alerts,
        delta="Monitor" if disease_alerts > 0 else "Clear",
        delta_color="inverse" if disease_alerts > 0 else "off"
    )

st.divider()

# ============================================================================
# MAIN NAVIGATION TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    
    "Business Dashboard",
    "Customer Analytics",
    "Disease Prediction",
    "Inventory Manager",
    "Staff Optimizer",
    "Campaign Intelligence",
    "Regional Intelligence",
])

# TAB 1: BUSINESS DASHBOARD
with tab1:
    st.header("Executive Business Dashboard")
    
    # Revenue Trends
    st.subheader("Revenue Performance")
    
    sales_df['date'] = pd.to_datetime(sales_df['date'])
    daily_revenue = filtered_sales.groupby('date')['amount'].sum().reset_index()
    daily_revenue['ma_7'] = daily_revenue['amount'].rolling(window=7).mean()
    
    import plotly.graph_objects as go
    
    fig_revenue = go.Figure()
    
    fig_revenue.add_trace(go.Scatter(
        x=daily_revenue['date'],
        y=daily_revenue['amount'],
        mode='lines',
        name='Daily Revenue',
        line=dict(color='#3498db', width=2),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.1)'
    ))
    
    fig_revenue.add_trace(go.Scatter(
        x=daily_revenue['date'],
        y=daily_revenue['ma_7'],
        mode='lines',
        name='7-Day Average',
        line=dict(color='#e74c3c', width=3, dash='dash')
    ))
    
    fig_revenue.update_layout(
        title="Revenue Trend with Moving Average",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Category Performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Categories by Revenue")
        
        category_revenue = filtered_sales.groupby('category')['amount'].sum().sort_values(ascending=False).reset_index()
        
        import plotly.express as px
        
        fig_cat = px.bar(
            category_revenue,
            x='category',
            y='amount',
            color='amount',
            color_continuous_scale='Blues',
            labels={'amount': 'Revenue ($)', 'category': 'Category'}
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        st.subheader("Branch Performance")
        
        branch_revenue = filtered_sales.groupby('branch_name')['amount'].sum().sort_values(ascending=False).reset_index()
        
        fig_branch = px.bar(
            branch_revenue,
            x='branch_name',
            y='amount',
            color='amount',
            color_continuous_scale='Greens',
            labels={'amount': 'Revenue ($)', 'branch_name': 'Branch'}
        )
        fig_branch.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_branch, use_container_width=True)
    
    # Time Analysis
    st.subheader("Peak Performance Hours")
    
    hourly_performance = filtered_sales.groupby('hour').agg({
        'amount': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    hourly_performance.columns = ['Hour', 'Revenue', 'Transactions']
    
    fig_hourly = go.Figure()
    
    fig_hourly.add_trace(go.Bar(
        x=hourly_performance['Hour'],
        y=hourly_performance['Revenue'],
        name='Revenue',
        marker_color='#3498db'
    ))
    
    fig_hourly.add_trace(go.Scatter(
        x=hourly_performance['Hour'],
        y=hourly_performance['Transactions'],
        name='Transactions',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#e74c3c', width=3)
    ))
    
    fig_hourly.update_layout(
        title="Hourly Revenue & Transaction Volume",
        xaxis_title="Hour of Day",
        yaxis_title="Revenue ($)",
        yaxis2=dict(title="Transactions", overlaying='y', side='right'),
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Key Insights
    st.subheader("Key Business Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_day = filtered_sales.groupby('day_of_week')['amount'].sum().idxmax()
        best_day_revenue = filtered_sales.groupby('day_of_week')['amount'].sum().max()
        st.info(f"**Best Day:** {best_day}  \nRevenue: ${best_day_revenue:,.0f}")
    
    with col2:
        peak_hour = filtered_sales.groupby('hour')['amount'].sum().idxmax()
        st.info(f"**Peak Hour:** {peak_hour}:00  \nHighest revenue time")
    
    with col3:
        top_medicine = filtered_sales.groupby('medicine_name')['quantity'].sum().idxmax()
        top_med_qty = filtered_sales.groupby('medicine_name')['quantity'].sum().max()
        st.info(f"**Top Medicine:** {top_medicine}  \n{top_med_qty} units sold")

# TAB 2: CUSTOMER ANALYTICS
with tab2:
    render_customer_analytics(filtered_sales, customer_df)

# TAB 3: DISEASE PREDICTION
with tab3:
    render_disease_prediction(filtered_sales, disease_df, branches_df)

# TAB 4: INVENTORY MANAGER
with tab4:
    render_inventory_management(
        filter_by_branch(inventory_df, selected_branch),
        filtered_sales
    )

# TAB 5: STAFF OPTIMIZER
with tab5:
    render_staff_optimization(
        filter_by_branch(staff_df, selected_branch),
        filtered_sales
    )

# TAB 6: CAMPAIGN INTELLIGENCE
with tab6:
    render_campaign_intelligence(filtered_sales, customer_df, campaigns_df)

with tab7:
    render_regional_intelligence(filtered_sales, disease_df, branches_df)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()

# Summary Footer
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_medicines = inventory_df['current_stock'].sum()
    st.metric("Total Medicines", f"{total_medicines:,}")

with col2:
    total_branches = len(branches_df)
    st.metric("Branches", total_branches)

with col3:
    staff_hours = staff_df['current_staff'].sum()
    st.metric("Staff Hours", f"{staff_hours:,}")

with col4:
    active_campaigns = len(campaigns_df[campaigns_df['status'] == 'Active']) if 'status' in campaigns_df.columns else 0
    st.metric("Active Campaigns", active_campaigns)

with col5:
    inventory_value = (inventory_df['current_stock'] * inventory_df['unit_cost']).sum()
    st.metric("Inventory Value", f"${inventory_value:,.0f}")

st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666; padding: 20px 0;'>
    <p style='margin: 5px 0;'>🏥 <strong>{COMPANY_NAME}</strong> - PharmaFlow AI</p>
    <p style='margin: 5px 0; font-size: 0.9em;'>Powered by Claude AI | Real-time Analytics & Disease Prediction</p>
    <p style='margin: 5px 0; font-size: 0.8em;'>© 2025 All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)