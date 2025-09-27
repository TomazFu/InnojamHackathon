from openai import OpenAI
import os
import streamlit as st

@st.cache_resource
def get_openai_client():
    """Initialize OpenAI client with caching"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY not found in environment")
        st.info("Add to .env file: OPENAI_API_KEY=your_key_here")
        st.stop()
    return OpenAI(api_key=api_key)

def generate_ai_insight(prompt, context, max_tokens=800):
    """Generate AI insights using OpenAI"""
    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            messages=[{
                "role": "user",
                "content": f"""{context}

{prompt}"""
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return "Unable to generate AI insights at this time."

def analyze_outbreak(disease_df, sales_df, context_data):
    """Specialized AI function for outbreak analysis"""
    
    outbreak_records = disease_df[disease_df['alert_level'].isin(['Critical', 'Warning'])]
    
    if len(outbreak_records) == 0:
        return "No disease outbreaks detected. All areas are normal."
    
    context = f"""
DISEASE OUTBREAK ANALYSIS:

Affected Areas:
- Districts: {outbreak_records['district'].unique().tolist()}
- Branches: {outbreak_records['branch_name'].unique().tolist()}
- Peak Spike: {outbreak_records['spike_percentage'].max():.1f}%
- Duration: {len(outbreak_records['date'].unique())} days

Sales Pattern:
- Daily Sales (Outbreak): {outbreak_records['daily_sales_units'].mean():.1f} units/day
- Baseline Average: {outbreak_records['baseline_avg'].mean():.1f} units/day
- Total Affected Patients (est.): {outbreak_records['estimated_affected_patients'].sum():,}

Recent Data:
{outbreak_records.tail(10).to_string()}
"""
    
    prompt = """Analyze this disease outbreak and provide:

1. **Severity Assessment** (scale 1-10 and why)
2. **Disease Identification** (most likely illness based on medicine sales)
3. **Spread Prediction** (will it affect other districts?)
4. **Stock Impact** (which medicines need urgent restocking)
5. **Public Health Alert** (should authorities be notified? Yes/No and why)
6. **Timeline Forecast** (when will outbreak subside?)
7. **Immediate Actions** (3 urgent steps for pharmacy)

Be specific and actionable."""
    
    return generate_ai_insight(prompt, context, max_tokens=1200)

def generate_campaign_strategy(target_segment, campaign_type, budget, customer_data, sales_data):
    """Generate AI campaign strategy"""
    
    context = f"""
CAMPAIGN PLANNING REQUEST:

Parameters:
- Target Segment: {target_segment}
- Campaign Type: {campaign_type}
- Budget: ${budget:,}

Customer Insights:
{customer_data}

Sales Patterns:
{sales_data}
"""
    
    prompt = """Create a detailed campaign strategy:

1. **Campaign Name** (creative and memorable)
2. **Timing** (best dates/hours based on data)
3. **Promotion Mechanics** (discount/offer details)
4. **Target Products** (which medicines to promote)
5. **Marketing Channels** (SMS, email, in-store, etc.)
6. **Expected ROI** (revenue projection)
7. **Success Metrics** (KPIs to track)
8. **Action Plan** (5 specific steps)

Make it practical and data-driven."""
    
    return generate_ai_insight(prompt, context, max_tokens=1000)