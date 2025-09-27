import streamlit as st
import pandas as pd
from utils.visualizations import create_age_distribution_chart, create_customer_type_chart

def render_customer_analytics(sales_df, customer_df):
    """Render complete customer analytics section"""
    
    st.header("Customer Analytics & Behavior Insights")
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_customers = len(customer_df)
        st.metric("Total Customers", f"{total_customers:,}")
    
    with col2:
        chronic_patients = len(customer_df[customer_df['has_chronic'] == True])
        chronic_pct = (chronic_patients / total_customers * 100)
        st.metric("Chronic Patients", f"{chronic_patients:,}", 
                 delta=f"{chronic_pct:.1f}% of base")
    
    with col3:
        avg_spend = customer_df['monthly_spend'].mean()
        st.metric("Avg Monthly Spend", f"${avg_spend:.2f}")
    
    with col4:
        prescription_rate = (len(sales_df[sales_df['is_prescription'] == True]) / 
                           len(sales_df) * 100)
        st.metric("Prescription Rate", f"{prescription_rate:.1f}%")
    
    st.divider()
    
    # Demographics
    st.subheader("Customer Demographics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_age = create_age_distribution_chart(sales_df)
        st.plotly_chart(fig_age, use_container_width=True)
    
    with col2:
        fig_type = create_customer_type_chart(sales_df)
        st.plotly_chart(fig_type, use_container_width=True)
    
    # Chronic Patient Deep Dive
    st.subheader("Chronic Patient Analysis")
    
    chronic_customers = customer_df[customer_df['has_chronic'] == True]
    
    if len(chronic_customers) > 0:
        # Parse chronic conditions
        all_conditions = chronic_customers['chronic_conditions'].str.split(', ').explode()
        condition_counts = all_conditions.value_counts()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            import plotly.express as px
            fig_conditions = px.bar(
                condition_counts.reset_index(), 
                x='chronic_conditions', 
                y='count',
                labels={'chronic_conditions': 'Condition', 'count': 'Number of Patients'},
                title="Most Common Chronic Conditions",
                color='count',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_conditions, use_container_width=True)
        
        with col2:
            st.markdown("###Chronic Care Insights")
            
            total_chronic_revenue = chronic_customers['monthly_spend'].sum()
            st.metric("Monthly Chronic Revenue", f"${total_chronic_revenue:,.0f}")
            
            avg_chronic_spend = chronic_customers['monthly_spend'].mean()
            st.metric("Avg Chronic Spend", f"${avg_chronic_spend:.2f}")
            
            st.info(f"**Top Condition:** {condition_counts.index[0]}")
            st.success("**Opportunity:** Launch chronic care loyalty program")
    
    # Purchase Behavior
    st.subheader("🛒 Purchase Behavior Patterns")
    
    category_purchase = sales_df.groupby(['category', 'is_prescription']).size().reset_index(name='count')
    category_purchase['type'] = category_purchase['is_prescription'].map({True: 'Prescription', False: 'OTC'})
    
    import plotly.express as px
    fig_purchase = px.bar(
        category_purchase, 
        x='category', 
        y='count', 
        color='type',
        title="Medicine Categories: Prescription vs OTC",
        barmode='group',
        color_discrete_map={'Prescription': '#e74c3c', 'OTC': '#3498db'}
    )
    st.plotly_chart(fig_purchase, use_container_width=True)
    
    # Customer Segmentation Table
    st.subheader("Customer Segment Summary")
    
    segment_summary = customer_df.groupby('customer_type').agg({
        'customer_id': 'count',
        'monthly_spend': 'mean',
        'monthly_visits': 'mean'
    }).reset_index()
    
    segment_summary.columns = ['Segment', 'Count', 'Avg Monthly Spend', 'Avg Monthly Visits']
    segment_summary['Total Monthly Revenue'] = segment_summary['Count'] * segment_summary['Avg Monthly Spend']
    
    segment_summary = segment_summary.sort_values('Total Monthly Revenue', ascending=False)
    
    st.dataframe(
        segment_summary.style.format({
            'Avg Monthly Spend': '${:.2f}',
            'Total Monthly Revenue': '${:,.2f}',
            'Avg Monthly Visits': '{:.1f}'
        }).background_gradient(subset=['Total Monthly Revenue'], cmap='Greens'),
        use_container_width=True
    )