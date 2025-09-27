import streamlit as st
import pandas as pd
from utils.visualizations import create_staff_optimization_chart
from utils.ai_insights import generate_ai_insight

def render_staff_optimization(staff_df, sales_df):
    """Render staff optimization section"""
    
    st.header("Dynamic Staff Optimization & Scheduling")
    
    # Staff Metrics
    understaffed = len(staff_df[staff_df['status'] == 'Understaffed'])
    overstaffed = len(staff_df[staff_df['status'] == 'Overstaffed'])
    optimal = len(staff_df[staff_df['status'] == 'Optimal'])
    efficiency = (optimal / len(staff_df)) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Understaffed Hours", 
            understaffed,
            delta=f"{understaffed} gaps to fill",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "Overstaffed Hours", 
            overstaffed,
            delta=f"Reduce by {overstaffed}"
        )
    
    with col3:
        st.metric("Optimal Hours", optimal, delta="Target")
    
    with col4:
        st.metric(
            "⚡ Staffing Efficiency", 
            f"{efficiency:.1f}%",
            delta=f"{efficiency - 75:.1f}% vs target"
        )
    
    st.divider()
    
    # Branch Selection
    st.subheader("📅 Staff Schedule Analysis")

    if len(staff_df) == 0:
        st.error("No staff data available")
        return

    selected_branch = st.selectbox(
        "Select Branch for Detailed View",
        staff_df['branch_name'].unique()
    )

    # Staffing Chart
    try:
        fig_staff = create_staff_optimization_chart(staff_df, selected_branch)
        st.plotly_chart(fig_staff, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating staff chart: {str(e)}")
        st.info("Chart visualization temporarily unavailable")
    
    # Staffing Gaps Table
    branch_staff = staff_df[staff_df['branch_name'] == selected_branch]
    urgent_gaps = branch_staff[branch_staff['staff_gap'] < -1].sort_values('staff_gap')
    
    if len(urgent_gaps) > 0:
        st.error(f"**{len(urgent_gaps)} hours critically understaffed at {selected_branch}**")
        
        for idx, row in urgent_gaps.iterrows():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                st.metric("Hour", f"{row['hour']}:00")
            
            with col2:
                st.warning(
                    f"Need **{abs(row['staff_gap'])} more staff** | "
                    f"Expected: {row['avg_transactions']} transactions | "
                    f"Current: {row['current_staff']} staff"
                )
            
            with col3:
                if st.button(f"Fix Hour {row['hour']}", key=f"fix_{idx}"):
                    st.info(f"💡 Add {abs(row['staff_gap'])} staff at {row['hour']}:00")
    else:
        st.success(f"✅ **{selected_branch}** is optimally staffed!")
    
    st.divider()
    
    # Staff Productivity Analysis
    st.subheader("Staff Productivity Metrics")
    
    # Calculate transactions per staff with error handling
    productivity = branch_staff.copy()
    # Avoid division by zero
    productivity['transactions_per_staff'] = productivity.apply(
        lambda row: row['avg_transactions'] / row['current_staff'] if row['current_staff'] > 0 else 0,
        axis=1
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        import plotly.express as px
        
        fig_prod = px.bar(
            productivity,
            x='hour',
            y='transactions_per_staff',
            title=f"Transactions per Staff - {selected_branch}",
            labels={'transactions_per_staff': 'Transactions/Staff', 'hour': 'Hour'},
            color='transactions_per_staff',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig_prod, use_container_width=True)
    
    with col2:
        # Calculate revenue per staff (approximate) with error handling
        hourly_revenue = sales_df[sales_df['branch_name'] == selected_branch].groupby('hour')['amount'].sum()

        def calculate_revenue_per_staff(hour):
            revenue = hourly_revenue.get(hour, 0)
            staff_row = productivity[productivity['hour'] == hour]
            if len(staff_row) > 0 and staff_row['current_staff'].values[0] > 0:
                return revenue / staff_row['current_staff'].values[0]
            return 0

        productivity['revenue_per_staff'] = productivity['hour'].map(calculate_revenue_per_staff)
        
        fig_rev = px.bar(
            productivity,
            x='hour',
            y='revenue_per_staff',
            title=f"Revenue per Staff - {selected_branch}",
            labels={'revenue_per_staff': 'Revenue/Staff ($)', 'hour': 'Hour'},
            color='revenue_per_staff',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_rev, use_container_width=True)
    
    # AI Staff Scheduler
    st.subheader("🤖 AI-Powered Staff Scheduling Assistant")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        schedule_day = st.selectbox(
            "Day to Schedule",
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )
    
    with col2:
        total_staff = st.number_input(
            "Total Staff Available",
            min_value=3,
            max_value=30,
            value=12
        )
    
    with col3:
        shift_duration = st.selectbox(
            "Shift Duration",
            [8, 9, 12]
        )
    
    if st.button("📋 Generate Optimal Schedule", type="primary"):
        with st.spinner("AI optimizing staff allocation..."):
            
            # Get traffic pattern for the day
            day_pattern = sales_df[
                (sales_df['branch_name'] == selected_branch) & 
                (sales_df['day_of_week'] == schedule_day)
            ].groupby('hour').size()
            
            # Current staffing issues
            context = f"""
STAFF SCHEDULING REQUEST:

Branch: {selected_branch}
Day: {schedule_day}
Total Staff Available: {total_staff}
Shift Duration: {shift_duration} hours
Operating Hours: 9:00 AM - 9:00 PM (12 hours)

Hourly Transaction Pattern for {schedule_day}:
{day_pattern.to_dict()}

Current Issues:
- Understaffed Hours: {len(branch_staff[branch_staff['status'] == 'Understaffed'])}
- Peak Hours: {branch_staff.nlargest(3, 'avg_transactions')['hour'].tolist()}
- Minimum Staff Required: 1 pharmacist + 1 assistant at all times

Staff Roles:
- Pharmacist: Can handle prescriptions and consultations
- Pharmacy Assistant: Can handle OTC sales and support

Constraints:
- Each staff works one {shift_duration}-hour shift
- 30-minute break during shift (need coverage)
- Minimum 2 staff at all times
"""
            
            prompt = """Create an optimal staff schedule with:

1. **Shift Structure** (how many shifts, specific timing: e.g., Shift A: 9am-5pm)
2. **Staff Allocation by Hour** (table format with hour, pharmacists, assistants, total)
3. **Break Coverage Plan** (how to maintain service during breaks)
4. **Role Distribution** (pharmacist vs assistant allocation)
5. **Cost Analysis** (labor cost estimate, overtime if needed)
6. **Contingency Plan** (what if 1-2 people call in sick?)
7. **Efficiency Score** (how well this matches demand)

Format the hourly allocation as a clear table."""
            
            ai_schedule = generate_ai_insight(prompt, context, max_tokens=1200)
            
            st.markdown("### AI-Generated Staff Schedule")
            st.success(ai_schedule)
            
            # Download
            st.download_button(
                label="Download Schedule",
                data=ai_schedule,
                file_name=f"staff_schedule_{selected_branch}_{schedule_day}_{pd.Timestamp.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    # Weekly Staff Summary
    st.subheader("📊 Weekly Staffing Overview")
    
    weekly_summary = staff_df.groupby('branch_name').agg({
        'current_staff': 'sum',
        'recommended_staff': 'sum',
        'staff_gap': 'sum'
    }).reset_index()
    
    weekly_summary.columns = ['Branch', 'Current Staff Hours', 'Recommended Hours', 'Gap (Hours)']
    weekly_summary['Efficiency %'] = (weekly_summary['Current Staff Hours'] / weekly_summary['Recommended Hours'] * 100).round(1)
    
    st.dataframe(
        weekly_summary.style.background_gradient(
            subset=['Efficiency %'], 
            cmap='RdYlGn',
            vmin=80,
            vmax=120
        ),
        use_container_width=True
    )

