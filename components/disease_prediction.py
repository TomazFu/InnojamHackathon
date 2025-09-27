import streamlit as st
import pandas as pd
from utils.visualizations import create_disease_spike_chart
from utils.ai_insights import analyze_outbreak

def format_factors_description(factors):
    """Format factors into a readable description for the AI Factors column"""
    if not factors or len(factors) == 0:
        return "No factors detected"

    # Create short descriptive names for each factor type
    factor_descriptions = []

    for factor in factors:
        factor_type = factor.get('type', '')
        impact = factor.get('impact', 'unknown')
        details = factor.get('details', '')

        # Create readable factor descriptions
        if factor_type == 'campaign':
            factor_descriptions.append(f"📢 Campaign ({impact})")
        elif factor_type == 'geographic_spread':
            factor_descriptions.append(f"🌍 Geographic spread ({impact})")
        elif factor_type == 'demographics':
            factor_descriptions.append(f"👥 Multi-demographic ({impact})")
        elif factor_type == 'sustained_pattern':
            factor_descriptions.append(f"📈 Sustained pattern ({impact})")
        elif factor_type == 'cross_category':
            factor_descriptions.append(f"🔄 Cross-category purchases ({impact})")
        elif factor_type == 'seasonal_expected':
            factor_descriptions.append(f"🗓️ Seasonal pattern ({impact})")
        else:
            factor_descriptions.append(f"🔍 {factor_type.replace('_', ' ').title()} ({impact})")

    # Join factors with line breaks for better readability
    if len(factor_descriptions) <= 2:
        return " • ".join(factor_descriptions)
    else:
        # For more than 2 factors, show count and top factors
        return f"{len(factor_descriptions)} factors: {' • '.join(factor_descriptions[:2])}{' + more' if len(factor_descriptions) > 2 else ''}"

def analyze_sales_spike_factors(medicine_name, period_type, sales_df, campaigns_df):
    """
    Analyze if sales spike is due to disease outbreak or other factors
    Using weekly or monthly analysis periods
    """

    # Work on a copy to prevent mutation of original DataFrame
    sales_df_copy = sales_df.copy()

    # Convert dates to datetime
    sales_df_copy['date'] = pd.to_datetime(sales_df_copy['date'])

    # Get medicine sales data
    medicine_sales = sales_df_copy[sales_df_copy['medicine_name'] == medicine_name].copy()

    if len(medicine_sales) == 0:
        return None

    # Group by period
    if period_type == "Weekly":
        medicine_sales['period'] = medicine_sales['date'].dt.isocalendar().week
        medicine_sales['year'] = medicine_sales['date'].dt.year
        medicine_sales['period_key'] = medicine_sales['year'].astype(str) + "-W" + medicine_sales['period'].astype(str).str.zfill(2)
        period_label = "Week"
    else:  # Monthly
        medicine_sales['period_key'] = medicine_sales['date'].dt.to_period('M').astype(str)
        period_label = "Month"

    # Calculate sales by period
    period_sales = medicine_sales.groupby('period_key').agg({
        'quantity': 'sum',
        'date': ['min', 'max']
    }).reset_index()

    period_sales.columns = ['period', 'total_quantity', 'start_date', 'end_date']

    # Sort by start_date to ensure chronological order
    period_sales = period_sales.sort_values('start_date').reset_index(drop=True)


    # Filter out incomplete periods for baseline calculation
    if period_type == "Weekly":
        min_days = 5  # At least 5 days for a week
    else:  # Monthly
        min_days = 20  # At least 20 days for a month

    # Add period length to DataFrame
    period_sales['period_days'] = (period_sales['end_date'] - period_sales['start_date']).dt.days + 1
    valid_periods = period_sales[period_sales['period_days'] >= min_days].copy()


    # More flexible baseline calculation
    if len(valid_periods) < 2:
        # If not enough period data, compare against overall average
        total_days = (medicine_sales['date'].max() - medicine_sales['date'].min()).days + 1
        daily_avg = medicine_sales['quantity'].sum() / total_days

        # Calculate expected period length dynamically
        if period_type == "Weekly":
            expected_period_days = 7
        else:  # Monthly
            expected_period_days = 30  # Use 30 as default, but this could be refined

        expected_period_sales = daily_avg * expected_period_days

        # Get actual recent period sales (not entire dataset!)
        if period_type == "Weekly":
            recent_cutoff = medicine_sales['date'].max() - pd.Timedelta(days=6)  # Last 7 days
        else:  # Monthly
            recent_cutoff = medicine_sales['date'].max() - pd.Timedelta(days=29)  # Last 30 days

        recent_period_data = medicine_sales[medicine_sales['date'] >= recent_cutoff]
        recent_period_sales = recent_period_data['quantity'].sum()
        

        spike_percentage = ((recent_period_sales - expected_period_sales) / expected_period_sales * 100) if expected_period_sales > 0 else 0

        analysis = {
            'medicine': medicine_name,
            'period_type': period_type,
            'current_period': f"Latest {period_type.lower()}",
            'current_sales': recent_period_sales,
            'baseline_avg': expected_period_sales,
            'spike_percentage': spike_percentage,
            'period_start': medicine_sales['date'].min(),
            'period_end': medicine_sales['date'].max(),
            'factors': [],
            'insufficient_data': True,
            'period_count': 1  # Only one period available
        }
    else:
        recent_period = valid_periods.iloc[-1]
        baseline_periods = valid_periods.iloc[:-1]
        baseline_avg = baseline_periods['total_quantity'].mean()


        spike_percentage = ((recent_period['total_quantity'] - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0

        analysis = {
            'medicine': medicine_name,
            'period_type': period_type,
            'current_period': recent_period['period'],
            'current_sales': recent_period['total_quantity'],
            'baseline_avg': baseline_avg,
            'spike_percentage': spike_percentage,
            'period_start': recent_period['start_date'],
            'period_end': recent_period['end_date'],
            'factors': [],
            'insufficient_data': False,
            'period_count': len(valid_periods)
        }

    # Get period dates for factor analysis
    period_start = analysis['period_start']
    period_end = analysis['period_end']

    # Factor 1: Check for active campaigns during the period

    # Find campaigns that overlap with the analysis period
    if len(medicine_sales) > 0 and 'category' in medicine_sales.columns:
        medicine_category = medicine_sales['category'].iloc[0]
        active_campaigns = campaigns_df[
            (pd.to_datetime(campaigns_df['start_date']) <= period_end) &
            (pd.to_datetime(campaigns_df['end_date']) >= period_start) &
            (campaigns_df['category'] == medicine_category)
        ]
    else:
        active_campaigns = pd.DataFrame()  # No campaigns if no medicine data

    if len(active_campaigns) > 0:
        campaign = active_campaigns.iloc[0]
        # Calculate campaign overlap with period
        campaign_start = max(pd.to_datetime(campaign['start_date']), period_start)
        campaign_end = min(pd.to_datetime(campaign['end_date']), period_end)
        overlap_days = (campaign_end - campaign_start).days + 1
        period_days = (period_end - period_start).days + 1
        overlap_percentage = (overlap_days / period_days) * 100

        analysis['factors'].append({
            'type': 'campaign',
            'impact': 'high' if overlap_percentage > 50 else 'medium',
            'details': f"Campaign '{campaign['campaign_name']}' ({campaign['discount_pct']}% off) active for {overlap_percentage:.0f}% of period",
            'reduces_outbreak_probability': True
        })

    # Get current period medicine sales for detailed analysis
    if analysis['insufficient_data']:
        # For insufficient data, use recent data (last week/month)
        if period_type == "Weekly":
            recent_cutoff = medicine_sales['date'].max() - pd.Timedelta(days=6)  # Last 7 days
        else:  # Monthly
            recent_cutoff = medicine_sales['date'].max() - pd.Timedelta(days=29)  # Last 30 days

        current_period_sales = medicine_sales[medicine_sales['date'] >= recent_cutoff]
    else:
        current_period_sales = medicine_sales[
            (medicine_sales['date'] >= period_start) &
            (medicine_sales['date'] <= period_end)
        ]

    # Factor 2: Multi-branch pattern (disease spreads across locations)
    affected_branches = current_period_sales['branch_name'].nunique()
    total_branches = sales_df_copy['branch_name'].nunique()

    # More realistic thresholds for geographic spread
    spread_percentage = affected_branches / total_branches if total_branches > 0 else 0

    if spread_percentage >= 0.8:  # 80%+ of branches affected
        analysis['factors'].append({
            'type': 'geographic_spread',
            'impact': 'high',
            'details': f"{affected_branches}/{total_branches} branches affected ({spread_percentage*100:.0f}%) - widespread distribution",
            'increases_outbreak_probability': True
        })
    elif spread_percentage >= 0.5:  # 50%+ of branches affected
        analysis['factors'].append({
            'type': 'geographic_spread',
            'impact': 'medium',
            'details': f"{affected_branches}/{total_branches} branches affected ({spread_percentage*100:.0f}%) - moderate spread",
            'increases_outbreak_probability': True
        })

    # Factor 3: Age group analysis (diseases affect specific demographics)
    age_groups = current_period_sales['age_group'].nunique()
    total_age_groups = sales_df_copy['age_group'].nunique()

    # More realistic demographic thresholds
    demo_percentage = age_groups / total_age_groups if total_age_groups > 0 else 0

    if demo_percentage >= 0.9:  # 90%+ age groups (very unusual)
        analysis['factors'].append({
            'type': 'demographics',
            'impact': 'high',
            'details': f"{age_groups}/{total_age_groups} age groups affected ({demo_percentage*100:.0f}%) - unusual broad spread",
            'increases_outbreak_probability': True
        })
    elif demo_percentage >= 0.7:  # 70%+ age groups
        analysis['factors'].append({
            'type': 'demographics',
            'impact': 'medium',
            'details': f"{age_groups}/{total_age_groups} age groups affected ({demo_percentage*100:.0f}%) - broad community spread",
            'increases_outbreak_probability': True
        })

    # Factor 4: Sustained vs spike pattern (over the period)
    if period_type == "Weekly":
        daily_sales = current_period_sales.groupby('date')['quantity'].sum()
        if len(daily_sales) >= 3:
            # Check if sales are consistently high vs just 1-2 spike days
            high_days = sum(daily_sales > daily_sales.mean() * 1.5)
            if high_days >= len(daily_sales) * 0.6:  # 60% of days are high
                analysis['factors'].append({
                    'type': 'sustained_pattern',
                    'impact': 'high',
                    'details': f"{high_days}/{len(daily_sales)} days show elevated sales - indicates sustained demand",
                    'increases_outbreak_probability': True
                })

    # Factor 5: Cross-category correlation (people buying multiple medicine types)
    customer_purchases = current_period_sales.groupby(['branch_name', 'date', 'hour']).agg({
        'category': 'nunique',
        'quantity': 'sum'
    }).reset_index()

    multi_category_purchases = customer_purchases[customer_purchases['category'] > 1]
    if len(multi_category_purchases) > len(customer_purchases) * 0.3:  # 30% buy multiple categories
        analysis['factors'].append({
            'type': 'cross_category',
            'impact': 'medium',
            'details': f"{len(multi_category_purchases)/len(customer_purchases)*100:.0f}% of purchases include multiple medicine categories",
            'increases_outbreak_probability': True
        })

    # Factor 6: Seasonal baseline adjustment
    current_month = period_start.month
    flu_season_months = [10, 11, 12, 1, 2, 3]  # Oct-Mar
    allergy_season_months = [3, 4, 5, 9, 10]  # Spring/Fall

    medicine_category = medicine_sales['category'].iloc[0] if len(medicine_sales) > 0 else ""

    if medicine_category == "Cold & Flu" and current_month in flu_season_months:
        analysis['factors'].append({
            'type': 'seasonal_expected',
            'impact': 'medium',
            'details': f"Flu season (Month {current_month}) - elevated sales are partially expected",
            'reduces_outbreak_probability': True
        })
    elif "allergy" in medicine_category.lower() and current_month in allergy_season_months:
        analysis['factors'].append({
            'type': 'seasonal_expected',
            'impact': 'medium',
            'details': f"Allergy season (Month {current_month}) - elevated sales are partially expected",
            'reduces_outbreak_probability': True
        })

    return analysis

def calculate_outbreak_confidence(analysis_result):
    """Calculate confidence score for outbreak vs other factors"""
    if not analysis_result:
        return 0

    # Start with spike-based confidence - more conservative medical approach
    spike_pct = analysis_result.get('spike_percentage', 0)

    # Negative spikes (decreasing sales) should indicate LOW outbreak risk
    if spike_pct < 0:
        # Decreasing sales = lower disease activity
        abs_spike = abs(spike_pct)
        if abs_spike > 50:
            confidence = 1   # Very large decrease = extremely low risk
        elif abs_spike > 30:
            confidence = 2   # Large decrease = very low risk
        elif abs_spike > 15:
            confidence = 4   # Medium decrease = low risk
        elif abs_spike > 5:
            confidence = 7   # Small decrease = low-medium risk
        else:
            confidence = 10  # Tiny decrease = medium-low risk
    else:
        # Positive spikes (increasing sales) = potential outbreak
        # More conservative thresholds - need significant spikes for outbreak concern
        if spike_pct < 15:
            confidence = 5   # Small increase = very low risk
        elif spike_pct < 30:
            confidence = 10  # Moderate increase = low risk
        elif spike_pct < 60:
            confidence = 20  # Significant increase = medium-low risk
        elif spike_pct < 100:
            confidence = 35  # Large increase = medium risk
        elif spike_pct < 200:
            confidence = 55  # Very large increase = high risk
        else:
            confidence = 75  # Extreme increase = very high risk

    # Count reducing vs increasing factors
    reducing_factors = [f for f in analysis_result['factors'] if f.get('reduces_outbreak_probability')]
    increasing_factors = [f for f in analysis_result['factors'] if f.get('increases_outbreak_probability')]

    # Apply factor adjustments - much more conservative for decreasing sales
    if spike_pct < 0:
        # For decreasing sales, factor adjustments should be minimal
        for factor in reducing_factors:
            if factor['impact'] == 'high':
                confidence -= 2   # Very small adjustment
            elif factor['impact'] == 'medium':
                confidence -= 1   # Minimal adjustment
            else:
                confidence -= 0.5 # Tiny adjustment

        for factor in increasing_factors:
            if factor['impact'] == 'high':
                confidence += 2   # Very small adjustment
            elif factor['impact'] == 'medium':
                confidence += 1   # Minimal adjustment
            else:
                confidence += 0.5 # Tiny adjustment
    else:
        # For increasing sales, use normal factor adjustments
        for factor in reducing_factors:
            if factor['impact'] == 'high':
                confidence -= 15
            elif factor['impact'] == 'medium':
                confidence -= 8
            else:
                confidence -= 4

        for factor in increasing_factors:
            if factor['impact'] == 'high':
                confidence += 12
            elif factor['impact'] == 'medium':
                confidence += 6
            else:
                confidence += 3
    
    # Special logic for decreasing sales - factors should have minimal impact
    if spike_pct < 0:
        # For decreasing sales, cap the maximum risk based on the size of decrease
        if abs(spike_pct) > 50:
            max_risk = 5   # Very large decrease: max 5% risk
        elif abs(spike_pct) > 20:
            max_risk = 10  # Large decrease: max 10% risk
        else:
            max_risk = 15  # Small decrease: max 15% risk
        
        confidence = min(confidence, max_risk)

    # Add debug info to analysis result
    analysis_result['debug_info'] = {
        'spike_percentage': spike_pct,
        'spike_direction': 'Decreasing' if spike_pct < 0 else 'Increasing',
        'base_risk_from_spike': confidence,
        'reducing_factors_count': len(reducing_factors),
        'increasing_factors_count': len(increasing_factors),
        'factor_adjustments': {
            'reducing_total': sum([-2 if f['impact'] == 'high' else -1 if f['impact'] == 'medium' else -0.5 for f in reducing_factors]) if spike_pct < 0 else sum([-15 if f['impact'] == 'high' else -8 if f['impact'] == 'medium' else -4 for f in reducing_factors]),
            'increasing_total': sum([2 if f['impact'] == 'high' else 1 if f['impact'] == 'medium' else 0.5 for f in increasing_factors]) if spike_pct < 0 else sum([12 if f['impact'] == 'high' else 6 if f['impact'] == 'medium' else 3 for f in increasing_factors])
        },
        'final_confidence': max(0, min(100, confidence)),
        'current_sales': analysis_result.get('current_sales', 0),
        'baseline_avg': analysis_result.get('baseline_avg', 0),
        'calculation_method': 'insufficient_data' if analysis_result.get('insufficient_data') else 'sufficient_periods',
        'decreasing_sales_cap_applied': spike_pct < 0,
        'max_risk_cap': 5 if spike_pct < -50 else 10 if spike_pct < -20 else 15 if spike_pct < 0 else 100
    }

    return max(0, min(100, confidence))

def render_disease_prediction(sales_df, disease_df, branches_df):
    """Render disease outbreak detection section"""

    st.header("🦠 Intelligent Disease Outbreak Detection")
    st.markdown("*Multi-factor analysis considering promotions, campaigns, and genuine disease patterns*")

    # Load campaign data for analysis
    try:
        campaigns_df = pd.read_csv('data/campaigns.csv')
    except Exception as e:
        st.error(f"Could not load campaign data: {e}")
        campaigns_df = pd.DataFrame()

    # Intelligent Analysis Section
    st.subheader("🧠 Smart Spike Analysis")
    st.markdown("*Analyzes whether sales spikes are due to disease outbreaks or other factors*")

    col1, col2 = st.columns(2)

    with col1:
        # Select medicine for analysis
        medicines = sales_df['medicine_name'].unique()
        selected_medicine = st.selectbox("Select Medicine to Analyze", medicines)

    with col2:
        # Select analysis period
        analysis_period = st.selectbox(
            "Analysis Period",
            ["Weekly", "Monthly"]
        )

    if st.button("🔍 Analyze Sales Spike", type="primary"):
        with st.spinner("Analyzing sales patterns and external factors..."):

            # Perform intelligent analysis
            print(f"\n🎯 UI ANALYSIS REQUEST: {selected_medicine} ({analysis_period})")
            analysis = analyze_sales_spike_factors(
                selected_medicine, analysis_period, sales_df, campaigns_df
            )

            if analysis:
                print(f"🎯 UI DISPLAYING: {analysis['medicine']} - {analysis['current_sales']} units, {analysis['spike_percentage']:.1f}% spike")
                confidence = calculate_outbreak_confidence(analysis)

                # Display results
                st.subheader(f"📊 Analysis Results - {analysis['current_period']}")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Outbreak Confidence",
                        f"{confidence}%",
                        delta="High Risk" if confidence > 70 else "Low Risk" if confidence < 30 else "Medium Risk"
                    )

                with col2:
                    spike_pct = analysis['spike_percentage']
                    delta_text = f"{spike_pct:+.1f}% vs baseline"
                    delta_color = "inverse" if spike_pct > 0 else "normal"  # Red for increases, green for decreases

                    st.metric(
                        f"{analysis_period} Sales",
                        f"{analysis['current_sales']} units",
                        delta=delta_text,
                        delta_color=delta_color
                    )

                with col3:
                    st.metric(
                        "Baseline Average",
                        f"{analysis['baseline_avg']:.0f} units",
                        delta=f"Previous periods"
                    )

                with col4:
                    factors_count = len(analysis['factors'])
                    st.metric(
                        "Factors Detected",
                        factors_count,
                        delta="Multiple influences" if factors_count > 2 else "Simple pattern"
                    )

                # Show data quality info
                if analysis.get('insufficient_data'):
                    st.info(f"ℹ️ **Limited Data Warning**: Only {analysis.get('period_count', 'few')} {analysis_period.lower()} periods found for {selected_medicine}. Analysis uses overall average as baseline.")


                # Factor breakdown
                st.subheader("📊 Factor Analysis")

                if len(analysis['factors']) > 0:
                    for factor in analysis['factors']:
                        if factor.get('reduces_outbreak_probability'):
                            st.success(f"✅ **{factor['type'].replace('_', ' ').title()}**: {factor['details']}")
                        else:
                            st.warning(f"⚠️ **{factor['type'].replace('_', ' ').title()}**: {factor['details']}")
                else:
                    st.info("No significant external factors detected - spike may be random or due to genuine outbreak")

                # Recommendation
                st.subheader("💡 Recommendation")

                if confidence >= 70:
                    st.error(f"""
                    **High Outbreak Probability ({confidence}%)**
                    - Increase stock of {selected_medicine} and related medicines
                    - Monitor neighboring branches closely
                    - Consider alerting health authorities
                    - Prepare for sustained demand increase
                    """)
                elif confidence <= 30:
                    st.success(f"""
                    **Low Outbreak Probability ({confidence}%)**
                    - Sales spike likely due to promotional/external factors
                    - Maintain normal stock levels
                    - Monitor for pattern changes
                    - No immediate action required
                    """)
                else:
                    st.info(f"""
                    **Moderate Uncertainty ({confidence}%)**
                    - Mixed signals detectedk
                    - Increase monitoring frequency
                    - Prepare moderate stock increase
                    - Watch for pattern development over next 2-3 days
                    """)

            else:
                st.warning(f"No sales data found for {selected_medicine} on {analysis_period.lower()}")

    st.divider()

    # Intelligent Alert Overview - Replace old disease_df system
    st.subheader("🚨 Intelligent Disease Monitoring Overview")

    # Analyze the same medicines as the table for consistency
    overview_medicines = sales_df['medicine_name'].unique()[:10]  # Same as table
    high_risk_count = 0
    total_analyzed = 0
    total_confidence = 0

    for med in overview_medicines:
        overview_analysis = analyze_sales_spike_factors(med, "Weekly", sales_df, campaigns_df)
        if overview_analysis:
            confidence = calculate_outbreak_confidence(overview_analysis)
            total_analyzed += 1
            total_confidence += confidence
            if confidence >= 70:
                high_risk_count += 1

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "High Risk Medicines",
            high_risk_count,
            delta="Urgent Action" if high_risk_count > 0 else "Clear",
            delta_color="inverse" if high_risk_count > 0 else "off"
        )

    with col2:
        st.metric(
            "Medicines Analyzed",
            total_analyzed,
            delta=f"out of {len(overview_medicines)} top medicines"
        )

    with col3:
        # Calculate average confidence across analyzed medicines
        avg_confidence = total_confidence / total_analyzed if total_analyzed > 0 else 0

        st.metric(
            "Avg Risk Level",
            f"{avg_confidence:.0f}%",
            delta="Network-wide confidence"
        )

    with col4:
        # Count affected branches across all high-risk medicines
        affected_branches = set()
        for med in overview_medicines:
            if med in sales_df['medicine_name'].values:
                med_analysis = analyze_sales_spike_factors(med, "Weekly", sales_df, campaigns_df)
                if med_analysis and calculate_outbreak_confidence(med_analysis) >= 70:
                    med_sales = sales_df[sales_df['medicine_name'] == med]
                    affected_branches.update(med_sales['branch_name'].unique())

        st.metric("Affected Branches", len(affected_branches))
    
    st.divider()

    # Medicine Risk Analysis Table
    st.subheader("📋 Medicine Risk Analysis")


    # Create a comprehensive analysis table
    analysis_results = []
    detailed_factors = {}
    
    for med in sales_df['medicine_name'].unique()[:10]:  # Top 10 medicines
        med_analysis = analyze_sales_spike_factors(med, "Weekly", sales_df, campaigns_df)
        if med_analysis:
            confidence = calculate_outbreak_confidence(med_analysis)
            
            # Store detailed factors for display outside table
            detailed_factors[med] = med_analysis['factors']
            
            # Calculate more meaningful metrics
            baseline = med_analysis.get('baseline_avg', 0)
            current = med_analysis.get('current_sales', 0)
            spike_pct = med_analysis.get('spike_percentage', 0)
            
            
            # Determine status based on clearer logic
            if confidence >= 70:
                status = 'High Risk'
                status_color = '🔴'
            elif confidence >= 40:
                status = 'Monitor'
                status_color = '🟡'
            else:
                status = 'Low Risk'
                status_color = '🟢'

            analysis_results.append({
                'Medicine': med,
                'Baseline Sales': f"{baseline:.0f}",
                'Current Sales': f"{current:.0f}",
                'Change %': f"{spike_pct:+.1f}%",
                'Outbreak Risk': f"{confidence:.0f}%",
                'Status': f"{status_color} {status}"
            })

    if analysis_results:
        analysis_df = pd.DataFrame(analysis_results)
        
        # Reset index to start from 1 instead of 0
        analysis_df.index = range(1, len(analysis_df) + 1)
        analysis_df.index.name = '#'

        # Color code the status column
        def highlight_status(val):
            if 'High Risk' in val:
                return 'background-color: #ffebee; color: #c62828'
            elif 'Monitor' in val:
                return 'background-color: #fff3e0; color: #ef6c00'
            else:
                return 'background-color: #e8f5e8; color: #2e7d32'

        # Display the table
        st.dataframe(
            analysis_df.style.applymap(highlight_status, subset=['Status']),
            use_container_width=True
        )
        
        # Display detailed factors outside the table
        st.subheader("🔍 Detailed Risk Factors Analysis")
        
        for med, factors in detailed_factors.items():
            if factors:  # Only show if there are factors
                with st.expander(f"📊 {med} - Risk Factors ({len(factors)} factors)"):
                    # Show calculation breakdown
                    med_analysis = analyze_sales_spike_factors(med, "Weekly", sales_df, campaigns_df)
                    if med_analysis and 'debug_info' in med_analysis:
                        debug = med_analysis['debug_info']
                        st.markdown("**🧮 Risk Calculation Breakdown:**")
                        
                        # Calculate step-by-step
                        base_risk = debug['base_risk_from_spike']
                        reducing_adj = debug['factor_adjustments']['reducing_total']
                        increasing_adj = debug['factor_adjustments']['increasing_total']
                        final_risk = debug['final_confidence']
                        
                        st.markdown(f"""
                        **Step 1 - Sales Analysis:**
                        - Sales Change: {debug['spike_direction']} by {debug['spike_percentage']:.1f}%
                        - Base Risk from Sales: {base_risk:.0f}%
                        
                        **Step 2 - Factor Adjustments:**
                        - Reducing Factors: {debug['reducing_factors_count']} factors → {reducing_adj:+.0f}%
                        - Increasing Factors: {debug['increasing_factors_count']} factors → {increasing_adj:+.0f}%
                        
                        **Step 3 - Calculation:**
                        - Before cap: {base_risk:.0f}% + {reducing_adj:+.0f}% + {increasing_adj:+.0f}% = {base_risk + reducing_adj + increasing_adj:.0f}%
                        - Max allowed for {debug['spike_percentage']:.1f}% decrease: {debug['max_risk_cap']}%
                        - **Final Risk: {final_risk:.0f}%** (capped at {debug['max_risk_cap']}%)
                        
                        **🔍 Debug Info:**
                        - Current Sales: {debug['current_sales']:.0f} units
                        - Baseline Avg: {debug['baseline_avg']:.0f} units
                        - Calculation Method: {debug['calculation_method']}
                        """)
                        st.divider()
                    
                    for i, factor in enumerate(factors, 1):
                        factor_type = factor.get('type', 'unknown')
                        impact = factor.get('impact', 'unknown')
                        details = factor.get('details', 'No details available')
                        
                        # Create readable factor descriptions
                        if factor_type == 'campaign':
                            icon = "📢"
                            factor_name = "Marketing Campaign"
                        elif factor_type == 'geographic_spread':
                            icon = "🌍"
                            factor_name = "Geographic Spread"
                        elif factor_type == 'demographics':
                            icon = "👥"
                            factor_name = "Demographic Pattern"
                        elif factor_type == 'sustained_pattern':
                            icon = "📈"
                            factor_name = "Sustained Pattern"
                        elif factor_type == 'cross_category':
                            icon = "🔄"
                            factor_name = "Cross-Category Purchases"
                        elif factor_type == 'seasonal_expected':
                            icon = "🗓️"
                            factor_name = "Seasonal Pattern"
                        else:
                            icon = "🔍"
                            factor_name = factor_type.replace('_', ' ').title()
                        
                        # Impact color coding
                        impact_color = {
                            'high': '🔴',
                            'medium': '🟡', 
                            'low': '🟢'
                        }.get(impact, '⚪')
                        
                        # Direction indicator
                        direction = "⬆️ Increases" if factor.get('increases_outbreak_probability') else "⬇️ Reduces" if factor.get('reduces_outbreak_probability') else "➡️ Neutral"
                        
                        st.markdown(f"""
                        **{i}. {icon} {factor_name}** {impact_color} {impact.upper()}
                        
                        {direction} outbreak probability
                        
                        *{details}*
                        """)
    else:
        st.info("No medicine analysis data available")
