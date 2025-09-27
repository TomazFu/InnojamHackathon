import streamlit as st
import pandas as pd
from utils.visualizations import create_inventory_status_chart
from utils.ai_insights import generate_ai_insight

def render_inventory_management(inventory_df, sales_df):
    """Render inventory management section"""
    
    st.header("Smart Inventory Management & Forecasting")
    
    # Critical Metrics
    critical_items = len(inventory_df[inventory_df['status'] == 'Critical'])
    low_items = len(inventory_df[inventory_df['status'] == 'Low'])
    total_stock_value = (inventory_df['current_stock'] * inventory_df['unit_cost']).sum()
    avg_stockout_days = inventory_df['days_until_stockout'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Critical Stock", 
            critical_items,
            delta="Urgent reorder needed" if critical_items > 0 else "All clear",
            delta_color="inverse" if critical_items > 0 else "off"
        )
    
    with col2:
        st.metric("Low Stock Items", low_items, delta="Monitor closely")
    
    with col3:
        st.metric("Total Stock Value", f"${total_stock_value:,.0f}")
    
    with col4:
        st.metric(
            "Avg Days to Stockout", 
            f"{int(avg_stockout_days)}",
            delta="Healthy" if avg_stockout_days > 30 else "Risk",
            delta_color="normal" if avg_stockout_days > 30 else "inverse"
        )
    
    st.divider()
    
    # Critical Stock Alerts
    if critical_items > 0:
        st.error("**URGENT: Items Need Immediate Reorder**")
        
        critical_stock = inventory_df[inventory_df['status'] == 'Critical'].sort_values(
            'days_until_stockout'
        )
        
        display_critical = critical_stock[[
            'branch_name', 'category', 'medicine_name', 'current_stock', 
            'daily_velocity', 'days_until_stockout', 'reorder_point'
        ]].head(10)
        
        display_critical.columns = [
            'Branch', 'Category', 'Medicine', 'Stock', 
            'Daily Sales', 'Days Left', 'Reorder Qty'
        ]
        
        st.dataframe(
            display_critical.style.background_gradient(
                subset=['Days Left'], 
                cmap='RdYlGn'
            ),
            use_container_width=True
        )
        
        # Quick reorder summary
        reorder_cost = (critical_stock['reorder_point'] * critical_stock['unit_cost']).sum()
        st.info(f"💵 **Estimated Reorder Cost:** ${reorder_cost:,.2f}")
    
    # Inventory Health Visualization
    st.subheader("Inventory Health by Category")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_inv_status = create_inventory_status_chart(inventory_df)
        st.plotly_chart(fig_inv_status, use_container_width=True)
    
    with col2:
        import plotly.express as px
        
        # Stock vs velocity scatter
        fig_velocity = px.scatter(
            inventory_df, 
            x='daily_velocity', 
            y='current_stock',
            size='days_until_stockout', 
            color='status',
            hover_data=['medicine_name', 'branch_name'],
            title="Stock Level vs Sales Velocity",
            labels={'daily_velocity': 'Daily Sales Velocity', 'current_stock': 'Current Stock'},
            color_discrete_map={'Critical': '#ff4444', 'Low': '#ffaa00', 'Good': '#00cc66'}
        )
        st.plotly_chart(fig_velocity, use_container_width=True)
    
    # Expiry Management
    st.subheader("Medicine Expiry Tracking")
    
    expiring_soon = inventory_df[inventory_df['days_to_expiry'] < 90].sort_values('days_to_expiry')
    
    if len(expiring_soon) > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.warning(f"⏳ **{len(expiring_soon)} medicines expiring within 90 days**")
            
            display_expiry = expiring_soon[[
                'branch_name', 'medicine_name', 'current_stock', 
                'days_to_expiry', 'unit_cost'
            ]].head(10)
            
            display_expiry['potential_loss'] = display_expiry['current_stock'] * display_expiry['unit_cost']
            display_expiry.columns = ['Branch', 'Medicine', 'Stock', 'Days to Expiry', 'Unit Cost', 'Potential Loss']
            
            st.dataframe(
                display_expiry.style.format({
                    'Unit Cost': '${:.2f}',
                    'Potential Loss': '${:.2f}'
                }).background_gradient(subset=['Days to Expiry'], cmap='Reds_r'),
                use_container_width=True
            )
        
        with col2:
            total_expiry_value = expiring_soon['current_stock'].sum() * expiring_soon['unit_cost'].mean()
            st.metric("At-Risk Value", f"${total_expiry_value:,.0f}")
            
            st.markdown("### 💡 Actions")
            st.info("• Run clearance promotions")
            st.info("• Discount 20-30%")
            st.info("• Notify chronic patients")
    else:
        st.success("No medicines expiring soon. Inventory rotation is healthy.")
    
    # AI Demand Forecasting
    st.subheader("AI-Powered Demand Forecasting")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        forecast_category = st.selectbox(
            "Select Category for 7-Day Forecast",
            inventory_df['category'].unique()
        )
    
    with col2:
        forecast_branch = st.selectbox(
            "Select Branch",
            ['All Branches'] + inventory_df['branch_name'].unique().tolist()
        )
    
    if st.button("Generate Demand Forecast", type="primary"):
        with st.spinner("AI analyzing sales patterns and generating forecast..."):
            
            # Get historical data
            if forecast_branch == 'All Branches':
                category_sales = sales_df[sales_df['category'] == forecast_category]
                category_inventory = inventory_df[inventory_df['category'] == forecast_category]
            else:
                category_sales = sales_df[
                    (sales_df['category'] == forecast_category) & 
                    (sales_df['branch_name'] == forecast_branch)
                ]
                category_inventory = inventory_df[
                    (inventory_df['category'] == forecast_category) & 
                    (inventory_df['branch_name'] == forecast_branch)
                ]
            
            # Calculate metrics with error handling
            if len(category_sales) == 0:
                st.error(f"No sales data found for {forecast_category} in {forecast_branch}")
                return

            daily_sales = category_sales.groupby('date')['quantity'].sum()
            avg_daily = daily_sales.mean() if len(daily_sales) > 0 else 0
            recent_trend = (daily_sales.tail(7).mean() - daily_sales.head(7).mean()) if len(daily_sales) >= 7 else 0
            current_stock = category_inventory['current_stock'].sum() if len(category_inventory) > 0 else 0

            # Handle NaN values
            avg_daily = avg_daily if not pd.isna(avg_daily) else 0
            recent_trend = recent_trend if not pd.isna(recent_trend) else 0
            
            context = f"""
DEMAND FORECAST REQUEST:

Category: {forecast_category}
Branch: {forecast_branch}

Historical Performance (Last 90 Days):
- Average Daily Sales: {avg_daily:.1f} units
- Recent Trend: {'Increasing' if recent_trend > 0 else 'Decreasing'} by {abs(recent_trend):.1f} units/day
- Current Stock: {current_stock} units
- Days of Stock Remaining: {current_stock / avg_daily if avg_daily > 0 else 0:.1f} days

Weekly Pattern:
{daily_sales.tail(30).to_dict()}

Top Selling Medicines in Category:
{category_sales.groupby('medicine_name')['quantity'].sum().nlargest(5).to_dict()}
"""
            
            prompt = """Based on this data, provide a 7-day demand forecast:

1. **Daily Forecast** (predict units for next 7 days with confidence level)
2. **Key Drivers** (what factors are influencing demand?)
3. **Reorder Recommendation** (when to order, how much, which medicines)
4. **Risk Assessment** (stockout probability %, expiry risk)
5. **Promotional Strategy** (should we run promotion or hold stock?)
6. **Cost Optimization** (ordering strategy to minimize costs)

Be specific with numbers and actionable recommendations."""
            
            try:
                ai_forecast = generate_ai_insight(prompt, context, max_tokens=1000)

                st.markdown("### 📋 AI Forecast Report")
                st.success(ai_forecast)
            except Exception as e:
                st.error(f"Failed to generate AI forecast: {str(e)}")
                st.info("Please check your OpenAI API key is set correctly in environment variables.")
                return
            
            # Download
            st.download_button(
                label="Download Forecast Report",
                data=ai_forecast,
                file_name=f"demand_forecast_{forecast_category}_{pd.Timestamp.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    # Slow-Moving Inventory
    st.subheader("Slow-Moving Inventory Analysis")
    
    # Calculate sell-through rate (sales vs stock)
    inventory_df['sell_through_rate'] = (
        inventory_df['daily_velocity'] * 30 / inventory_df['current_stock'] * 100
    ).fillna(0)
    
    slow_movers = inventory_df[inventory_df['sell_through_rate'] < 30].sort_values('sell_through_rate')
    
    if len(slow_movers) > 0:
        st.warning(f"**{len(slow_movers)} items have low sell-through rates (<30%)**")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            import plotly.express as px
            fig_slow = px.bar(
                slow_movers.head(10), 
                x='medicine_name', 
                y='sell_through_rate',
                color='branch_name',
                title="Slowest Moving Items (Bottom 10)",
                labels={'sell_through_rate': 'Sell-Through Rate %', 'medicine_name': 'Medicine'}
            )
            st.plotly_chart(fig_slow, use_container_width=True)
        
        with col2:
            st.markdown("### 💡 Clearance Actions")
            
            for idx, row in slow_movers.head(3).iterrows():
                st.error(
                    f"**{row['medicine_name']}**  \n"
                    f"Branch: {row['branch_name']}  \n"
                    f"Sell-through: {row['sell_through_rate']:.1f}%  \n"
                    f"Suggest 30-40% discount"
                )
    else:
        st.success("All inventory moving well. No clearance needed.")

