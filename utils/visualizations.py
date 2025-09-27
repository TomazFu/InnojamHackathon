import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_age_distribution_chart(sales_df):
    """Create age distribution pie chart"""
    age_dist = sales_df['age_group'].value_counts().reset_index()
    age_dist.columns = ['Age Group', 'Transactions']
    
    fig = px.pie(
        age_dist, 
        values='Transactions', 
        names='Age Group',
        color_discrete_sequence=px.colors.sequential.RdBu,
        hole=0.4,
        title="Customer Age Distribution"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_customer_type_chart(sales_df):
    """Create customer type bar chart"""
    type_dist = sales_df['customer_type'].value_counts().reset_index()
    type_dist.columns = ['Customer Type', 'Transactions']
    
    fig = px.bar(
        type_dist, 
        x='Customer Type', 
        y='Transactions',
        color='Transactions', 
        color_continuous_scale='Viridis',
        title="Customer Types"
    )
    return fig

def create_revenue_trend_chart(sales_df):
    """Create revenue trend over time"""
    sales_df['date'] = pd.to_datetime(sales_df['date'])
    daily_revenue = sales_df.groupby('date')['amount'].sum().reset_index()
    
    # 7-day moving average
    daily_revenue['ma_7'] = daily_revenue['amount'].rolling(window=7).mean()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_revenue['date'],
        y=daily_revenue['amount'],
        mode='lines',
        name='Daily Revenue',
        line=dict(color='#3498db', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_revenue['date'],
        y=daily_revenue['ma_7'],
        mode='lines',
        name='7-Day Average',
        line=dict(color='#e74c3c', width=3, dash='dash')
    ))
    
    fig.update_layout(
        title="Revenue Trend Analysis",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_disease_spike_chart(disease_df):
    """Create disease spike timeline"""
    import pandas as pd
    
    disease_df['date'] = pd.to_datetime(disease_df['date'])
    
    fig = px.line(
        disease_df, 
        x='date', 
        y='spike_percentage', 
        color='district',
        title="Disease Outbreak Pattern - Medicine Sales Spike %",
        labels={'spike_percentage': 'Spike %', 'date': 'Date'}
    )
    
    # Add threshold lines
    fig.add_hline(y=50, line_dash="dash", line_color="orange", 
                  annotation_text="Warning (50%)", annotation_position="right")
    fig.add_hline(y=100, line_dash="dash", line_color="red",
                  annotation_text="Critical (100%)", annotation_position="right")
    
    fig.update_layout(height=450)
    return fig

def create_inventory_status_chart(inventory_df):
    """Create inventory status visualization"""
    status_summary = inventory_df.groupby(['category', 'status']).size().reset_index(name='count')
    
    fig = px.bar(
        status_summary, 
        x='category', 
        y='count',
        color='status', 
        barmode='stack',
        title="Inventory Status by Category",
        color_discrete_map={'Critical': '#ff4444', 'Low': '#ffaa00', 'Good': '#00cc66'}
    )
    
    return fig

def create_staff_optimization_chart(staff_df, branch_name):
    """Create staff vs transaction chart"""
    branch_data = staff_df[staff_df['branch_name'] == branch_name] if branch_name != 'All Branches' else staff_df.groupby('hour').mean().reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=branch_data['hour'],
        y=branch_data['current_staff'],
        mode='lines+markers',
        name='Current Staff',
        line=dict(color='#ff6b6b', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=branch_data['hour'],
        y=branch_data['recommended_staff'],
        mode='lines+markers',
        name='Recommended Staff',
        line=dict(color='#4ecdc4', width=3, dash='dash')
    ))
    
    fig.add_trace(go.Bar(
        x=branch_data['hour'],
        y=branch_data['avg_transactions'],
        name='Transactions',
        yaxis='y2',
        opacity=0.3,
        marker_color='#95e1d3'
    ))
    
    fig.update_layout(
        title=f"Staff Optimization - {branch_name}",
        xaxis_title="Hour of Day",
        yaxis_title="Number of Staff",
        yaxis2=dict(title="Transactions", overlaying='y', side='right'),
        hovermode='x unified',
        height=450
    )
    
    return fig

import pandas as pd  # Add this at the top