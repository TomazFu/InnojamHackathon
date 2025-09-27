import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ============================================================================
# CONFIGURATION - SINGLE PHARMACY CHAIN WITH MULTIPLE BRANCHES
# ============================================================================

COMPANY_NAME = "Guardian Pharmacy"

BRANCHES = [
    {'id': 'B001', 'name': 'Guardian Ang Mo Kio', 'district': 'North', 'lat': 1.369, 'lon': 103.845},
    {'id': 'B002', 'name': 'Guardian Bedok', 'district': 'East', 'lat': 1.324, 'lon': 103.930},
    {'id': 'B003', 'name': 'Guardian Jurong', 'district': 'West', 'lat': 1.335, 'lon': 103.744},
    {'id': 'B004', 'name': 'Guardian Tampines', 'district': 'East', 'lat': 1.353, 'lon': 103.945},
    {'id': 'B005', 'name': 'Guardian Orchard', 'district': 'Central', 'lat': 1.304, 'lon': 103.832}
]

START_DATE = datetime.now() - timedelta(days=90)

# Medicine categories
MEDICINE_CATEGORIES = {
    'Cold & Flu': [
        {'name': 'Paracetamol 500mg', 'price': 8.50, 'prescription': False},
        {'name': 'Cough Syrup', 'price': 12.90, 'prescription': False},
        {'name': 'Lozenges', 'price': 6.50, 'prescription': False},
        {'name': 'Decongestant', 'price': 15.00, 'prescription': False}
    ],
    'Pain Relief': [
        {'name': 'Ibuprofen 400mg', 'price': 10.50, 'prescription': False},
        {'name': 'Aspirin', 'price': 8.00, 'prescription': False},
        {'name': 'Muscle Relaxant', 'price': 25.00, 'prescription': True}
    ],
    'Digestive': [
        {'name': 'Antacid', 'price': 12.00, 'prescription': False},
        {'name': 'Probiotics', 'price': 35.00, 'prescription': False},
        {'name': 'Anti-diarrheal', 'price': 18.00, 'prescription': False}
    ],
    'Chronic': [
        {'name': 'Blood Pressure Med', 'price': 45.00, 'prescription': True},
        {'name': 'Diabetes Med', 'price': 65.00, 'prescription': True},
        {'name': 'Cholesterol Med', 'price': 55.00, 'prescription': True}
    ],
    'Vitamins': [
        {'name': 'Multivitamin', 'price': 28.00, 'prescription': False},
        {'name': 'Vitamin C', 'price': 15.00, 'prescription': False},
        {'name': 'Vitamin D', 'price': 22.00, 'prescription': False}
    ],
    'Antibiotics': [
        {'name': 'Amoxicillin', 'price': 35.00, 'prescription': True},
        {'name': 'Azithromycin', 'price': 42.00, 'prescription': True}
    ],
    'Skin Care': [
        {'name': 'Antibiotic Cream', 'price': 18.00, 'prescription': False},
        {'name': 'Antifungal Cream', 'price': 22.00, 'prescription': False},
        {'name': 'Moisturizer', 'price': 25.00, 'prescription': False}
    ]
}

CUSTOMER_TYPES = ['Regular', 'Walk-in', 'Chronic Patient', 'First-time']
AGE_GROUPS = ['0-12', '13-25', '26-40', '41-60', '60+']

# Disease outbreak simulation
FLU_OUTBREAK_START = 60  # Day 60
FLU_OUTBREAK_PEAK = 70   # Day 70
FLU_OUTBREAK_END = 80    # Day 80
OUTBREAK_DISTRICT = 'East'  # Bedok & Tampines affected

print(f"🏥 Generating Data for {COMPANY_NAME}")
print(f"📍 Branches: {len(BRANCHES)}\n")

# ============================================================================
# 1. SALES TRANSACTIONS
# ============================================================================
print("1. Generating sales transactions with disease outbreak simulation...")
sales_data = []
transaction_id = 1

for branch in BRANCHES:
    for day in range(90):
        date = START_DATE + timedelta(days=day)
        
        # Base transactions per day per branch
        base_transactions = np.random.randint(50, 100)
        
        # Weekend pattern (pharmacies busier on weekends)
        if date.weekday() >= 5:
            base_transactions = int(base_transactions * 1.2)
        
        # Monday spike (weekend accumulation)
        if date.weekday() == 0:
            base_transactions = int(base_transactions * 1.4)
        
        # DISEASE OUTBREAK in East district
        flu_multiplier = 1.0
        if branch['district'] == OUTBREAK_DISTRICT and FLU_OUTBREAK_START <= day <= FLU_OUTBREAK_END:
            if day <= FLU_OUTBREAK_PEAK:
                progress = (day - FLU_OUTBREAK_START) / (FLU_OUTBREAK_PEAK - FLU_OUTBREAK_START)
                flu_multiplier = 1 + (progress * 2.5)  # Up to 3.5x spike
            else:
                progress = (FLU_OUTBREAK_END - day) / (FLU_OUTBREAK_END - FLU_OUTBREAK_PEAK)
                flu_multiplier = 1 + (progress * 2.5)
        
        num_transactions = int(base_transactions * flu_multiplier)
        
        for tx in range(num_transactions):
            # Customer demographics
            age_weights = [0.10, 0.20, 0.30, 0.25, 0.15]
            age_group = np.random.choice(AGE_GROUPS, p=age_weights)
            
            customer_type = np.random.choice(CUSTOMER_TYPES, p=[0.40, 0.35, 0.15, 0.10])
            
            # Select category based on customer type
            if customer_type == 'Chronic Patient':
                category = 'Chronic'
            elif branch['district'] == OUTBREAK_DISTRICT and FLU_OUTBREAK_START <= day <= FLU_OUTBREAK_END:
                # During outbreak, 70% buy flu medicine
                if np.random.random() < 0.70:
                    category = 'Cold & Flu'
                else:
                    category = np.random.choice(list(MEDICINE_CATEGORIES.keys()))
            else:
                # Normal distribution
                category_weights = [0.25, 0.15, 0.15, 0.15, 0.15, 0.05, 0.10]
                category = np.random.choice(list(MEDICINE_CATEGORIES.keys()), p=category_weights)
            
            # Select medicine from category
            medicine = np.random.choice(MEDICINE_CATEGORIES[category])
            
            # Quantity
            if category == 'Chronic':
                quantity = np.random.randint(1, 3)
            else:
                quantity = np.random.randint(1, 5)
            
            # Calculate amount
            amount = medicine['price'] * quantity
            
            sales_data.append({
                'transaction_id': f'TXN{transaction_id:07d}',
                'branch_id': branch['id'],
                'branch_name': branch['name'],
                'district': branch['district'],
                'date': date.strftime('%Y-%m-%d'),
                'day_of_week': date.strftime('%A'),
                'hour': np.random.choice(range(9, 21), p=[0.05, 0.08, 0.12, 0.12, 0.08, 0.05, 0.08, 0.12, 0.12, 0.10, 0.05, 0.03]),
                'customer_type': customer_type,
                'age_group': age_group,
                'category': category,
                'medicine_name': medicine['name'],
                'quantity': quantity,
                'unit_price': medicine['price'],
                'amount': round(amount, 2),
                'is_prescription': medicine['prescription'],
                'is_weekend': date.weekday() >= 5,
                'day_number': day
            })
            
            transaction_id += 1

sales_df = pd.DataFrame(sales_data)

# ============================================================================
# 2. CUSTOMER PROFILES
# ============================================================================
print("2. Generating customer profiles...")
customer_data = []

# Generate customers based on transaction patterns
customer_segments = sales_df.groupby(['customer_type', 'age_group']).size().reset_index()

customer_id = 1
for _, segment in customer_segments.iterrows():
    num_customers = np.random.randint(30, 150)
    
    for _ in range(num_customers):
        is_chronic = segment['customer_type'] == 'Chronic Patient'
        
        # Chronic conditions
        if is_chronic:
            conditions = np.random.choice(
                ['Type 2 Diabetes', 'Hypertension', 'High Cholesterol', 'Asthma', 'Arthritis'],
                size=np.random.randint(1, 3),
                replace=False
            ).tolist()
        else:
            conditions = []
        
        # Visit frequency
        if segment['customer_type'] == 'Regular':
            monthly_visits = np.random.randint(3, 8)
        elif is_chronic:
            monthly_visits = np.random.randint(4, 12)
        else:
            monthly_visits = np.random.randint(1, 3)
        
        # Preferred branch (some loyalty)
        preferred_branch = np.random.choice([b['name'] for b in BRANCHES], 
                                           p=[0.30, 0.20, 0.15, 0.20, 0.15])
        
        customer_data.append({
            'customer_id': f'CUST{customer_id:06d}',
            'customer_type': segment['customer_type'],
            'age_group': segment['age_group'],
            'chronic_conditions': ', '.join(conditions) if conditions else 'None',
            'has_chronic': is_chronic,
            'monthly_visits': monthly_visits,
            'preferred_branch': preferred_branch,
            'monthly_spend': np.random.uniform(50, 400) if is_chronic else np.random.uniform(20, 150),
            'member_since_months': np.random.randint(1, 60)
        })
        
        customer_id += 1

customer_df = pd.DataFrame(customer_data)

# ============================================================================
# 3. INVENTORY MANAGEMENT
# ============================================================================
print("3. Generating inventory data...")
inventory_data = []

for branch in BRANCHES:
    for category, medicines in MEDICINE_CATEGORIES.items():
        for medicine in medicines:
            # Calculate sales velocity for this medicine at this branch
            branch_sales = sales_df[
                (sales_df['branch_id'] == branch['id']) & 
                (sales_df['medicine_name'] == medicine['name'])
            ]['quantity'].sum()
            
            daily_velocity = branch_sales / 90
            
            # Current stock (based on velocity)
            if category == 'Chronic':
                current_stock = int(daily_velocity * np.random.randint(30, 60))
            elif category == 'Antibiotics':
                current_stock = int(daily_velocity * np.random.randint(20, 40))
            else:
                current_stock = int(daily_velocity * np.random.randint(15, 45))
            
            current_stock = max(10, current_stock)  # Minimum 10 units
            
            # Expiry tracking
            if category in ['Chronic', 'Antibiotics']:
                days_to_expiry = np.random.randint(180, 730)
            else:
                days_to_expiry = np.random.randint(90, 540)
            
            # Calculate stockout days
            days_until_stockout = int(current_stock / daily_velocity) if daily_velocity > 0 else 999
            
            # Reorder point (2 weeks buffer)
            reorder_point = int(daily_velocity * 14)
            
            # Status
            if days_until_stockout < 7 or days_to_expiry < 30:
                status = 'Critical'
            elif days_until_stockout < 21 or days_to_expiry < 90:
                status = 'Low'
            else:
                status = 'Good'
            
            inventory_data.append({
                'branch_id': branch['id'],
                'branch_name': branch['name'],
                'category': category,
                'medicine_name': medicine['name'],
                'sku': f"SKU{len(inventory_data)+1000:04d}",
                'current_stock': current_stock,
                'unit_cost': round(medicine['price'] * 0.6, 2),  # 40% margin
                'unit_price': medicine['price'],
                'daily_velocity': round(daily_velocity, 2),
                'days_until_stockout': days_until_stockout,
                'days_to_expiry': days_to_expiry,
                'reorder_point': reorder_point,
                'status': status,
                'is_prescription': medicine['prescription']
            })

inventory_df = pd.DataFrame(inventory_data)

# ============================================================================
# 4. STAFF SCHEDULING
# ============================================================================
print("4. Generating staff schedules...")
staff_data = []

for branch in BRANCHES:
    # Get hourly transaction pattern
    branch_hourly = sales_df[sales_df['branch_id'] == branch['id']].groupby('hour').size()
    
    for hour in range(9, 21):  # 9am to 9pm
        avg_hourly_tx = branch_hourly.get(hour, 10)
        
        # 1 staff per 20 transactions/hour
        recommended_staff = max(2, int(avg_hourly_tx / 20))  # Minimum 2
        
        # Current staffing (sometimes sub-optimal)
        current_staff = recommended_staff + np.random.randint(-1, 2)
        current_staff = max(1, current_staff)
        
        # Staff roles
        if hour in [9, 10, 20]:  # Opening/closing hours
            pharmacist_needed = 1
            assistant_needed = current_staff - 1
        else:
            pharmacist_needed = max(1, int(current_staff * 0.4))
            assistant_needed = current_staff - pharmacist_needed
        
        staff_data.append({
            'branch_id': branch['id'],
            'branch_name': branch['name'],
            'hour': hour,
            'avg_transactions': int(avg_hourly_tx),
            'current_staff': current_staff,
            'recommended_staff': recommended_staff,
            'pharmacists': pharmacist_needed,
            'assistants': assistant_needed,
            'staff_gap': recommended_staff - current_staff,
            'status': 'Understaffed' if current_staff < recommended_staff else 
                     'Overstaffed' if current_staff > recommended_staff else 'Optimal'
        })

staff_df = pd.DataFrame(staff_data)

# ============================================================================
# 5. DISEASE OUTBREAK TRACKING
# ============================================================================
print("5. Generating disease outbreak tracking data...")
disease_data = []

for day in range(90):
    date = START_DATE + timedelta(days=day)
    
    for branch in BRANCHES:
        # Get flu medicine sales for this day
        day_flu_sales = sales_df[
            (sales_df['branch_id'] == branch['id']) & 
            (sales_df['date'] == date.strftime('%Y-%m-%d')) &
            (sales_df['category'] == 'Cold & Flu')
        ]['quantity'].sum()
        
        # Calculate baseline (7-day average before this day)
        if day >= 7:
            baseline_dates = [(date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]
            baseline_sales = sales_df[
                (sales_df['branch_id'] == branch['id']) &
                (sales_df['date'].isin(baseline_dates)) &
                (sales_df['category'] == 'Cold & Flu')
            ]['quantity'].sum() / 7
        else:
            baseline_sales = 15  # Initial baseline
        
        # Calculate spike
        if baseline_sales > 0:
            spike_pct = ((day_flu_sales - baseline_sales) / baseline_sales) * 100
        else:
            spike_pct = 0
        
        # Alert level
        if spike_pct > 100:
            alert = 'Critical'
        elif spike_pct > 50:
            alert = 'Warning'
        elif spike_pct > 20:
            alert = 'Monitor'
        else:
            alert = 'Normal'
        
        # Estimated affected people (rough estimate)
        estimated_patients = int(day_flu_sales * 0.8)  # Assume 0.8 patient per unit
        
        disease_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'branch_id': branch['id'],
            'branch_name': branch['name'],
            'district': branch['district'],
            'disease_category': 'Cold & Flu',
            'daily_sales_units': int(day_flu_sales),
            'baseline_avg': round(baseline_sales, 2),
            'spike_percentage': round(spike_pct, 2),
            'alert_level': alert,
            'estimated_affected_patients': estimated_patients,
            'day_number': day
        })

disease_df = pd.DataFrame(disease_data)

# ============================================================================
# 6. CAMPAIGN TRACKING (Historical campaigns)
# ============================================================================
print("6. Generating campaign history...")
campaign_data = [
    {
        'campaign_id': 'CAMP001',
        'campaign_name': 'Flu Season Prep',
        'start_date': (START_DATE + timedelta(days=45)).strftime('%Y-%m-%d'),
        'end_date': (START_DATE + timedelta(days=52)).strftime('%Y-%m-%d'),
        'target_segment': 'All Customers',
        'category': 'Cold & Flu',
        'discount_pct': 15,
        'budget': 5000,
        'branches': 'All',
        'status': 'Completed'
    },
    {
        'campaign_id': 'CAMP002',
        'campaign_name': 'Chronic Care Month',
        'start_date': (START_DATE + timedelta(days=30)).strftime('%Y-%m-%d'),
        'end_date': (START_DATE + timedelta(days=60)).strftime('%Y-%m-%d'),
        'target_segment': 'Chronic Patient',
        'category': 'Chronic',
        'discount_pct': 10,
        'budget': 8000,
        'branches': 'All',
        'status': 'Completed'
    }
]

campaign_df = pd.DataFrame(campaign_data)

# ============================================================================
# SAVE ALL DATA
# ============================================================================
print("\n💾 Saving all data files...")

sales_df.to_csv('data/sales.csv', index=False)
customer_df.to_csv('data/customers.csv', index=False)
inventory_df.to_csv('data/inventory.csv', index=False)
staff_df.to_csv('data/staff.csv', index=False)
disease_df.to_csv('data/disease_alerts.csv', index=False)
campaign_df.to_csv('data/campaigns.csv', index=False)

# Branch master data
branch_df = pd.DataFrame(BRANCHES)
branch_df.to_csv('data/branches.csv', index=False)

# ============================================================================
# SUMMARY REPORT
# ============================================================================
print("\n" + "="*60)
print(f"✅ {COMPANY_NAME} - Data Generation Complete!")
print("="*60)

print(f"\n📊 DATA SUMMARY:")
print(f"  Branches: {len(BRANCHES)}")
print(f"  Sales Transactions: {len(sales_df):,}")
print(f"  Unique Customers: {len(customer_df):,}")
print(f"  Medicine SKUs: {len(inventory_df)}")
print(f"  Staff Records: {len(staff_df)}")
print(f"  Disease Alerts: {len(disease_df):,}")
print(f"  Campaigns: {len(campaign_df)}")

print(f"\n💰 BUSINESS METRICS:")
print(f"  Total Revenue: ${sales_df['amount'].sum():,.2f}")
print(f"  Avg Transaction: ${sales_df['amount'].mean():.2f}")
print(f"  Total Units Sold: {sales_df['quantity'].sum():,}")
print(f"  Prescription %: {(len(sales_df[sales_df['is_prescription']==True])/len(sales_df)*100):.1f}%")

print(f"\n🦠 OUTBREAK SIMULATION:")
print(f"  Alert: FLU OUTBREAK DETECTED")
print(f"  Location: {OUTBREAK_DISTRICT} District")
print(f"  Affected Branches: {', '.join([b['name'] for b in BRANCHES if b['district']==OUTBREAK_DISTRICT])}")
print(f"  Period: Day {FLU_OUTBREAK_START}-{FLU_OUTBREAK_END}")
print(f"  Peak: Day {FLU_OUTBREAK_PEAK}")
max_spike = disease_df[disease_df['district']==OUTBREAK_DISTRICT]['spike_percentage'].max()
print(f"  Max Spike: {max_spike:.1f}% above baseline")
print(f"  Critical Alerts: {len(disease_df[disease_df['alert_level']=='Critical'])}")

print(f"\n📦 INVENTORY STATUS:")
print(f"  Critical Stock: {len(inventory_df[inventory_df['status']=='Critical'])}")
print(f"  Low Stock: {len(inventory_df[inventory_df['status']=='Low'])}")
print(f"  Total Stock Value: ${(inventory_df['current_stock'] * inventory_df['unit_cost']).sum():,.2f}")

print(f"\n👥 CUSTOMER INSIGHTS:")
print(f"  Chronic Patients: {len(customer_df[customer_df['has_chronic']==True]):,}")
print(f"  Regular Customers: {len(customer_df[customer_df['customer_type']=='Regular']):,}")
print(f"  Avg Monthly Spend: ${customer_df['monthly_spend'].mean():.2f}")

print("\n" + "="*60)
print("🚀 Ready to run: streamlit run app.py")
print("="*60 + "\n")