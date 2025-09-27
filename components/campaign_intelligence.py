import streamlit as st
import pandas as pd
from utils.ai_insights import generate_campaign_strategy

def render_campaign_intelligence(sales_df, customer_df, campaigns_df):
    """Render campaign and promotion intelligence section"""
    
    st.header("🎯 AI-Powered Campaign & Promotion Intelligence")
    
    # Campaign Performance Summary
    st.subheader("Past Campaign Performance")
    
    if len(campaigns_df) > 0:
        for idx, campaign in campaigns_df.iterrows():
            with st.expander(f"{campaign['campaign_name']} ({campaign['status']})"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Duration", f"{campaign['start_date']} to {campaign['end_date']}")
                
                with col2:
                    st.metric("Target", campaign['target_segment'])
                
                with col3:
                    st.metric("Discount", f"{campaign['discount_pct']}%")
                
                with col4:
                    st.metric("Budget", f"${campaign['budget']:,}")
    else:
        st.info("No past campaigns recorded. Create your first campaign below!")
    
    st.divider()
    
    # New Campaign Generator
    st.subheader("✨ Create New Campaign Strategy")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        target_segment = st.selectbox(
            "Target Customer Segment",
            ['All Customers', 'Chronic Patients', 'Regular Customers', 'Walk-in', 'First-time', 'Seniors (60+)', 'Young Adults (13-25)']
        )
    
    with col2:
        campaign_type = st.selectbox(
            "Campaign Type",
            ['Seasonal Health Drive', 'Chronic Care Program', 'Flu Season Prep', 'Health Awareness Month', 'Loyalty Rewards', 'New Customer Welcome', 'Clearance Sale']
        )
    
    with col3:
        campaign_budget = st.number_input(
            "Campaign Budget ($)",
            min_value=1000,
            max_value=50000,
            value=5000,
            step=1000
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_category = st.multiselect(
            "Medicine Categories to Promote",
            sales_df['category'].unique(),
            default=[sales_df['category'].value_counts().index[0]]
        )
    
    with col2:
        campaign_duration = st.slider(
            "Campaign Duration (days)",
            min_value=3,
            max_value=30,
            value=7
        )
    
    if st.button("🚀 Generate AI Campaign Strategy", type="primary"):
        with st.spinner("🧠 AI analyzing customer data and generating campaign strategy..."):
            
            # Prepare customer insights
            if target_segment == 'All Customers':
                segment_data = customer_df
                segment_sales = sales_df
            elif target_segment == 'Chronic Patients':
                segment_data = customer_df[customer_df['has_chronic'] == True]
                segment_sales = sales_df[sales_df['customer_type'] == 'Chronic Patient']
            elif target_segment == 'Seniors (60+)':
                segment_data = customer_df[customer_df['age_group'] == '60+']
                segment_sales = sales_df[sales_df['age_group'] == '60+']
            elif target_segment == 'Young Adults (13-25)':
                segment_data = customer_df[customer_df['age_group'].isin(['13-25', '26-40'])]
                segment_sales = sales_df[sales_df['age_group'].isin(['13-25', '26-40'])]
            else:
                segment_data = customer_df[customer_df['customer_type'] == target_segment]
                segment_sales = sales_df[sales_df['customer_type'] == target_segment]
            
            # Customer insights
            customer_context = f"""
Target Segment: {target_segment}
- Size: {len(segment_data):,} customers
- Avg Monthly Spend: ${segment_data['monthly_spend'].mean():.2f}
- Avg Visits/Month: {segment_data['monthly_visits'].mean():.1f}
- Preferred Categories: {segment_sales['category'].value_counts().head(3).to_dict()}
"""
            
            # Sales patterns
            sales_context = f"""
Purchase Patterns:
- Total Transactions: {len(segment_sales):,}
- Avg Transaction: ${segment_sales['amount'].mean():.2f}
- Peak Shopping Days: {segment_sales['day_of_week'].value_counts().head(3).index.tolist()}
- Peak Hours: {segment_sales['hour'].value_counts().head(3).index.tolist()}
- Prescription vs OTC: {(len(segment_sales[segment_sales['is_prescription']==True]) / len(segment_sales) * 100):.1f}% prescription
"""
            
            full_context = f"""
CAMPAIGN STRATEGY REQUEST:

Campaign Parameters:
- Type: {campaign_type}
- Budget: ${campaign_budget:,}
- Duration: {campaign_duration} days
- Target Categories: {', '.join(target_category)}

{customer_context}

{sales_context}

Historical Performance:
- Overall Conversion Rate: {(len(sales_df) / len(customer_df) * 100):.1f}%
- Weekend vs Weekday Sales: Weekend is {(len(sales_df[sales_df['is_weekend']==True]) / len(sales_df[sales_df['is_weekend']==False])):.1%} of weekday
"""
            
            ai_campaign = generate_campaign_strategy(
                target_segment, campaign_type, campaign_budget,
                customer_context, sales_context
            )
            
            st.markdown("### AI Campaign Strategy")
            st.success(ai_campaign)
            
            # Download
            st.download_button(
                label="Download Campaign Plan",
                data=ai_campaign,
                file_name=f"campaign_{campaign_type.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    st.divider()
    
    