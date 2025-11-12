import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
import math
from datetime import date, timedelta, datetime
import warnings
warnings.filterwarnings('ignore')

# Try to import plotly, fallback to matplotlib if not available
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# =============================================================================
# 🎨 MODERN UI CONFIGURATION
# =============================================================================

st.set_page_config(
    layout="wide", 
    page_title="BACHAT ROSCA PRICING", 
    page_icon="🚀", 
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    .main {
        padding-top: 1rem;
    }
    
    /* Dashboard Header */
    .dashboard-header {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
        padding: 2rem 1.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        color: #1a1a1a;
        border: 2px solid #00D084;
    }
    
    .dashboard-header h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.8rem;
        margin: 0;
        text-align: center;
    }
    
    .dashboard-header p {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        text-align: center;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 48px rgba(0,0,0,0.12);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #00D084, #00C978);
    }
    
    .metric-title {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        color: #64748b;
        margin: 0 0 0.5rem 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.2rem;
        color: #1e293b;
        margin: 0;
        line-height: 1.2;
    }
    
    .metric-change {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    .metric-change.positive {
        color: #00D084;
    }
    
    .metric-change.negative {
        color: #ef4444;
    }
    
    /* Chart Containers */
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    
    .chart-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #00D084, #00C978);
    }
    
    .chart-title {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.3rem;
        color: #1e293b;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f5f5f5 0%, #e8e8e8 100%);
    }
    
    /* Success/Info/Warning/Error Boxes */
    .success-box {
        background: linear-gradient(135deg, #00D084 0%, #00C978 100%);
        color: #1a1a1a;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 208, 132, 0.3);
        border-left: 4px solid #00C978;
    }
    
    .info-box {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
        color: #1a1a1a;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #00D084;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.2);
        border-left: 4px solid #d97706;
    }
    
    .error-box {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(239, 68, 68, 0.2);
        border-left: 4px solid #dc2626;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #00D084 0%, #00C978 100%);
        color: #1a1a1a;
        border: none;
        border-radius: 12px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 208, 132, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 208, 132, 0.5);
        background: linear-gradient(135deg, #00C978 0%, #00D084 100%);
    }
    
    /* Selectbox Styling */
    .stSelectbox > div > div {
        background: white;
        border-radius: 12px;
        border: 1px solid rgba(0, 208, 132, 0.3);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Number Input Styling */
    .stNumberInput > div > div > input {
        border-radius: 12px;
        border: 1px solid rgba(0, 208, 132, 0.3);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Text Input Styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 1px solid rgba(0, 208, 132, 0.3);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Multiselect Styling */
    .stMultiSelect > div > div {
        background: white;
        border-radius: 12px;
        border: 1px solid rgba(0, 208, 132, 0.3);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
        border-radius: 12px;
        border: 1px solid rgba(0, 208, 132, 0.3);
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        color: #1a1a1a;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #00D084 0%, #00C978 100%);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #00D084;
    }
    
    /* Data Editor Styling */
    .stDataEditor {
        border-radius: 12px;
        border: 1px solid rgba(0, 208, 132, 0.3);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Table Styling */
    .stDataFrame {
        border-radius: 12px;
        border: 1px solid rgba(0, 208, 132, 0.3);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Sidebar Section Headers */
    .sidebar-section {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid rgba(0, 208, 132, 0.3);
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .sidebar-section h3 {
        color: #1a1a1a;
        font-size: 1.1rem;
        margin: 0 0 1rem 0;
        font-weight: 600;
    }
    
    /* Slot Configuration Cards */
    .slot-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .slot-card h4 {
        color: #374151;
        font-size: 0.9rem;
        margin: 0 0 0.5rem 0;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🌍 CURRENCY CONFIGURATION
# =============================================================================

CURRENCY_OPTIONS = {
    "PKR": {"symbol": "₨", "name": "Pakistani Rupee", "format": "lakhs"},
    "USD": {"symbol": "$", "name": "US Dollar", "format": "millions"},
    "EUR": {"symbol": "€", "name": "Euro", "format": "millions"},
    "GBP": {"symbol": "£", "name": "British Pound", "format": "millions"},
    "INR": {"symbol": "₹", "name": "Indian Rupee", "format": "lakhs"},
    "AED": {"symbol": "د.إ", "name": "UAE Dirham", "format": "millions"},
    "SAR": {"symbol": "﷼", "name": "Saudi Riyal", "format": "millions"}
}

# =============================================================================
# 🛠️ UTILITY FUNCTIONS
# =============================================================================

def format_currency(amount, currency_symbol="₨", currency_name="PKR"):
    """Format currency with appropriate symbols and units"""
    if currency_name in ["PKR", "INR"]:
        if amount >= 10000000:  # 1 crore
            return f"{currency_symbol}{amount/10000000:.2f} Cr"
        elif amount >= 100000:  # 1 lakh
            return f"{currency_symbol}{amount/100000:.2f} L"
        else:
            return f"{currency_symbol}{amount:,.0f}"
    else:
        if amount >= 1000000000:  # 1 billion
            return f"{currency_symbol}{amount/1000000000:.2f} B"
        elif amount >= 1000000:  # 1 million
            return f"{currency_symbol}{amount/1000000:.2f} M"
        else:
            return f"{currency_symbol}{amount:,.0f}"

def days_between_specific_dates(start_date, end_date):
    """Calculate days between two specific dates"""
    return (end_date - start_date).days

def calculate_nii(principal, rate, days):
    """Calculate Net Interest Income"""
    return principal * (rate / 100) * (days / 365)

def calculate_fee_nii(fee_amount, rate, days):
    """Calculate Fee NII"""
    return fee_amount * (rate / 100) * (days / 365)

def calculate_pool_growth_nii(pool_amount, rate, days):
    """Calculate Pool Growth NII"""
    return pool_amount * (rate / 100) * (days / 365)

def validate_slot_distribution(slot_distribution, duration):
    """Validate that slot distribution sums to 100%"""
    total = sum(slot_distribution.values())
    return abs(total - 100.0) < 0.1

def validate_percentage_distribution(distribution, level_name):
    """Validate that distribution sums to 100%"""
    total = sum(distribution.values())
    if abs(total - 100.0) > 0.1:
        return False, f"{level_name} distribution is {total:.1f}% (should be 100%)"
    return True, "Valid"

def apply_rounding_correction(allocations, total_target):
    """Apply rounding correction to ensure integer totals"""
    current_total = sum(allocations.values())
    difference = total_target - current_total
    
    if difference != 0:
        largest_key = max(allocations.keys(), key=lambda k: allocations[k])
        allocations[largest_key] += difference
    
    return allocations

# ============================================================================= 
# 🧩 TAM USER DISTRIBUTION SYSTEM (From add.txt)
# ============================================================================= 

def calculate_new_users_tam(prev_total_users, growth_rate):
    """Calculate new users for current month (TAM system)"""
    return int(prev_total_users * (growth_rate / 100))

def determine_returning_users_tam(month, user_history, durations, rest_periods):
    """Determine returning users for current month (TAM system)"""
    returning_users = 0
    
    for join_month, user_data in user_history.items():
        for duration, user_count in user_data.items():
            rest_period = rest_periods.get(duration, 1)
            return_month = join_month + duration + rest_period
            
            if return_month == month:
                returning_users += user_count
    
    return returning_users

def allocate_users_by_duration(users, duration_share):
    """Allocate users by duration with integer rounding"""
    allocations = {}
    total_allocated = 0
    
    for duration, percentage in duration_share.items():
        allocated = int(users * percentage / 100)
        allocations[duration] = allocated
        total_allocated += allocated
    
    allocations = apply_rounding_correction(allocations, users)
    
    return allocations

def allocate_users_by_slab(duration_users, slab_share):
    """Allocate users by slab for each duration"""
    allocations = {}
    
    for duration, users in duration_users.items():
        if duration in slab_share:
            slab_allocations = {}
            total_allocated = 0
            
            for slab, percentage in slab_share[duration].items():
                allocated = int(users * percentage / 100)
                slab_allocations[slab] = allocated
                total_allocated += allocated
            
            slab_allocations = apply_rounding_correction(slab_allocations, users)
            allocations[duration] = slab_allocations
        else:
            allocations[duration] = {}
    
    return allocations

def allocate_users_by_slot(slab_users, slot_share):
    """Allocate users by slot for each duration and slab"""
    allocations = {}
    
    for duration, slabs in slab_users.items():
        allocations[duration] = {}
        
        for slab, users in slabs.items():
            if duration in slot_share:
                slot_allocations = {}
                total_allocated = 0
                
                for slot, percentage in slot_share[duration].items():
                    allocated = int(users * percentage / 100)
                    slot_allocations[slot] = allocated
                    total_allocated += allocated
                
                slot_allocations = apply_rounding_correction(slot_allocations, users)
                allocations[duration][slab] = slot_allocations
            else:
                allocations[duration][slab] = {}
    
    return allocations

def month_index_to_ym(start_year, start_month, month_index):
    """Convert month index to year and month"""
    total_months = start_month - 1 + month_index
    year = start_year + (total_months - 1) // 12
    month = ((total_months - 1) % 12) + 1
    return year, month

def held_days_exact(deposit_month_index, payout_month_index, start_year=2024, start_month=1,
                    deposit_day=1, payout_day=15):
    """
    Calculate exact days between deposit and payout dates
    
    Args:
        deposit_month_index: Month when deposit is collected (1-based)
        payout_month_index: Month when payout happens (1-based)
        start_year: Starting year (default 2024)
        start_month: Starting month (default 1)
        deposit_day: Day of month for deposit collection
        payout_day: Day of month for payout
    
    Returns:
        int: Number of days between deposit and payout
    """
    dy, dm = month_index_to_ym(start_year, start_month, deposit_month_index)
    py, pm = month_index_to_ym(start_year, start_month, payout_month_index)
    
    try:
        d0 = date(dy, dm, deposit_day)
    except ValueError:
        # Handle invalid date (e.g., Feb 30)
        d0 = date(dy, dm, 28 if dm == 2 else 30)
    
    try:
        d1 = date(py, pm, payout_day)
    except ValueError:
        # Handle invalid date
        d1 = date(py, pm, 28 if pm == 2 else 30)
    
    return (d1 - d0).days

def calculate_collection_dates(month, duration, collection_day=1, disbursement_day=15):
    """Calculate collection and disbursement dates for a given month and duration"""
    from calendar import monthrange
    
    # Calculate which year this month belongs to (assuming Year 1 starts in 2024)
    year = 2024 + ((month - 1) // 12)
    actual_month = ((month - 1) % 12) + 1
    
    # Ensure collection_day doesn't exceed maximum days in month
    max_days = monthrange(year, actual_month)[1]
    safe_collection_day = min(collection_day, max_days)
    
    try:
        collection_date = date(year, actual_month, safe_collection_day)
    except ValueError:
        # Fallback to last day of month
        collection_date = date(year, actual_month, max_days)
    
    # Calculate disbursement month and year
    total_months_from_start = month + duration - 1
    disbursement_year = 2024 + ((total_months_from_start - 1) // 12)
    disbursement_month = ((total_months_from_start - 1) % 12) + 1
    
    # Ensure disbursement_day doesn't exceed maximum days in disbursement month
    max_disburse_days = monthrange(disbursement_year, disbursement_month)[1]
    safe_disbursement_day = min(disbursement_day, max_disburse_days)
    
    try:
        disbursement_date = date(disbursement_year, disbursement_month, safe_disbursement_day)
    except ValueError:
        # Fallback to last day of disbursement month
        disbursement_date = date(disbursement_year, disbursement_month, max_disburse_days)
    
    # Use held_days_exact for precise calculation
    days_between = held_days_exact(
        deposit_month_index=month,
        payout_month_index=month + duration,
        start_year=2024,
        start_month=1,
        deposit_day=safe_collection_day,
        payout_day=safe_disbursement_day
    )
    
    return collection_date, disbursement_date, days_between

def calculate_monthly_nii_tam(principal, rate, collection_date, disbursement_date):
    """Calculate monthly NII based on collection and disbursement dates"""
    days = (disbursement_date - collection_date).days
    if days < 0:
        days = 30 - abs(days)
    return principal * (rate / 100) * (days / 365)

def calculate_nii_with_exact_days(principal, rate, deposit_month, payout_month, 
                                  deposit_day, payout_day, start_year=2024):
    """
    Calculate NII using exact days calculation (held_days_exact logic)
    
    Args:
        principal: Principal amount
        rate: Interest rate (as percentage)
        deposit_month: Month when deposit collected (1-based)
        payout_month: Month when payout happens (1-based)
        deposit_day: Day of month for deposit
        payout_day: Day of month for payout
        start_year: Starting year
    
    Returns:
        float: Calculated NII
    """
    days = held_days_exact(
        deposit_month_index=deposit_month,
        payout_month_index=payout_month,
        start_year=start_year,
        start_month=1,
        deposit_day=deposit_day,
        payout_day=payout_day
    )
    
    # NII = Principal × Rate × (Days / 365)
    return principal * (rate / 100) * (days / 365)

def create_slot_configuration_ui(duration, slab_amount, slot_fees, slot_distribution, currency_symbol):
    """Create UI for slot configuration"""
    st.markdown(f"**🎯 Slot Configuration for {duration}M, {currency_symbol}{slab_amount:,}**")
    
    total_distribution = 0
    for slot in range(1, duration + 1):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Handle both dict and numeric formats for slot_fees
            if slot in slot_fees and slot_fees[slot] is not None:
                if isinstance(slot_fees[slot], dict):
                    default_fee = slot_fees[slot].get('fee_pct', 2.0)
                else:
                    default_fee = slot_fees[slot]
            else:
                default_fee = 2.0
            
            fee_pct = st.number_input(
                f"Fee % for Slot {slot}",
                min_value=0.0,
                max_value=20.0,
                value=default_fee,
                step=0.1,
                key=f"fee_{duration}_{slab_amount}_{slot}"
            )
        
        with col2:
            # Handle both dict and numeric formats for slot_fees
            if slot in slot_fees and slot_fees[slot] is not None:
                if isinstance(slot_fees[slot], dict):
                    default_blocked = slot_fees[slot].get('blocked', False)
                else:
                    default_blocked = False
            else:
                default_blocked = False
            
            blocked = st.checkbox(
                f"Block Slot {slot}",
                value=default_blocked,
                key=f"block_{duration}_{slab_amount}_{slot}"
            )
        
        with col3:
            if not blocked:
                distribution = st.number_input(
                    f"Distribution % for Slot {slot}",
                    min_value=0.0,
                    max_value=100.0,
                    value=slot_distribution.get(slot, 100.0/duration),
                    step=0.1,
                    key=f"dist_{duration}_{slab_amount}_{slot}"
                )
                total_distribution += distribution
            else:
                st.info("🚫 Blocked")
                distribution = 0
        
        # Update configuration
        if duration not in slot_fees:
            slot_fees[duration] = {}
        if duration not in slot_distribution:
            slot_distribution[duration] = {}
        
        slot_fees[duration][slot] = {"fee_pct": fee_pct, "blocked": blocked}
        slot_distribution[duration][slot] = distribution
    
    # Validation
    if abs(total_distribution - 100.0) > 0.1:
        st.warning(f"⚠️ Total distribution is {total_distribution:.1f}% (should be 100%)")
    
    return slot_fees, slot_distribution

def create_quick_setup_ui(duration, slab_amount, currency_symbol):
    """Create quick setup UI for slot configuration"""
    st.markdown(f"**⚡ Quick Setup for {duration}M, {currency_symbol}{slab_amount:,}**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fee_pct = st.number_input(
            f"Fee % for all slots",
            min_value=0.0,
            max_value=20.0,
            value=2.0,
            step=0.1,
            key=f"quick_fee_{duration}_{slab_amount}"
        )
    
    with col2:
        blocked_slots = st.multiselect(
            f"Block slots",
            list(range(1, duration + 1)),
            key=f"quick_block_{duration}_{slab_amount}"
        )
    
    # Create configuration
    slot_fees = {}
    slot_distribution = {}
    
    for slot in range(1, duration + 1):
        slot_fees[slot] = {
            "fee_pct": fee_pct,
            "blocked": slot in blocked_slots
        }
        
        if slot in blocked_slots:
            slot_distribution[slot] = 0
        else:
            # Distribute remaining slots equally
            remaining_slots = duration - len(blocked_slots)
            if remaining_slots > 0:
                slot_distribution[slot] = 100.0 / remaining_slots
            else:
                slot_distribution[slot] = 0
    
    return slot_fees, slot_distribution

def create_compact_setup_ui(duration, slab_amount, currency_symbol):
    """Create compact setup UI for slot configuration"""
    st.markdown(f"**📋 Compact Setup for {duration}M, {currency_symbol}{slab_amount:,}**")
    
    # Create a data editor for slot configuration
    slot_data = []
    for slot in range(1, duration + 1):
        slot_data.append({
            "Slot": slot,
            "Fee %": 2.0,
            "Blocked": False,
            "Distribution %": 100.0 / duration
        })
    
    df_slots = pd.DataFrame(slot_data)
    
    edited_df = st.data_editor(
        df_slots,
        num_rows="fixed",
        use_container_width=True,
        key=f"compact_{duration}_{slab_amount}"
    )
    
    # Convert back to configuration
    slot_fees = {}
    slot_distribution = {}
    
    for _, row in edited_df.iterrows():
        slot = int(row["Slot"])
        slot_fees[slot] = {
            "fee_pct": row["Fee %"],
            "blocked": row["Blocked"]
        }
        
        if row["Blocked"]:
            slot_distribution[slot] = 0
        else:
            slot_distribution[slot] = row["Distribution %"]
    
    return slot_fees, slot_distribution

# =============================================================================
# 📊 DASHBOARD FUNCTIONS
# =============================================================================

def create_dashboard_overview(df_monthly_summary, scenario_name, currency_symbol, currency_name):
    """Create the main dashboard overview"""
    st.markdown(f"""
    <div class="dashboard-header">
        <h1>📊 {scenario_name}</h1>
        <p>ROSCA Forecast Dashboard - Real-time Analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_revenue = df_monthly_summary['Total Revenue'].sum()
        st.metric("Total Revenue", format_currency(total_revenue, currency_symbol, currency_name))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_profit = df_monthly_summary['Gross Profit'].sum()
        st.metric("Gross Profit", format_currency(total_profit, currency_symbol, currency_name))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_users = df_monthly_summary['Users Joining This Month'].sum()
        st.metric("Total Users", f"{total_users:,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        st.metric("Profit Margin", f"{profit_margin:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)

def create_nii_analysis(df_forecast, currency_symbol, currency_name):
    """Create NII analysis section"""
    st.markdown("### 💰 NII (Net Interest Income) Analysis")
    
    # Calculate NII metrics
    total_base_nii = df_forecast['Base NII (Lifetime)'].sum()
    total_fee_nii = df_forecast['Fee NII (Lifetime)'].sum()
    total_pool_growth_nii = df_forecast['Pool Growth NII (Lifetime)'].sum()
    total_nii = df_forecast['Total NII (Lifetime)'].sum()
    
    # NII metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Base NII", format_currency(total_base_nii, currency_symbol, currency_name), 
                 help="Interest earned on monthly installments")
    
    with col2:
        st.metric("Fee NII", format_currency(total_fee_nii, currency_symbol, currency_name), 
                 help="Interest earned on collected fees")
    
    with col3:
        st.metric("Pool Growth NII", format_currency(total_pool_growth_nii, currency_symbol, currency_name), 
                 help="Interest on accumulated deposits")
    
    with col4:
        st.metric("Total NII", format_currency(total_nii, currency_symbol, currency_name), 
                 help="Total Net Interest Income")
    
    # NII breakdown chart
    st.markdown("#### 📊 NII Components Breakdown")
    
    nii_data = {
        'Component': ['Base NII', 'Fee NII', 'Pool Growth NII'],
        'Amount': [total_base_nii, total_fee_nii, total_pool_growth_nii]
    }
    
    df_nii = pd.DataFrame(nii_data)
    
    if PLOTLY_AVAILABLE:
        fig = px.pie(df_nii, values='Amount', names='Component', 
                     title="NII Components Distribution",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(df_nii['Amount'], labels=df_nii['Component'], autopct='%1.1f%%')
        ax.set_title("NII Components Distribution")
        st.pyplot(fig)
    
    # NII explanation
    st.markdown("""
    **💡 NII Calculation Explanation:**
    - **Base NII**: Interest earned on monthly installments until user's turn
    - **Fee NII**: Interest earned on collected fees (upfront or monthly)
    - **Pool Growth NII**: Interest on accumulated deposits in the pool
    - **Total NII**: Sum of all NII components
    """)

def create_revenue_profit_analysis(df_forecast, currency_symbol, currency_name):
    """Create revenue and profit analysis section"""
    st.markdown("### 💰 Revenue & Profit Analysis")
    
    # Calculate revenue metrics
    total_fees = df_forecast['Total Fees Collected'].sum()
    total_nii = df_forecast['Total NII (Lifetime)'].sum()
    total_revenue = df_forecast['Total Revenue'].sum()
    total_losses = df_forecast['Total Losses'].sum()
    gross_profit = df_forecast['Gross Profit'].sum()
    
    # Revenue metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Fees", format_currency(total_fees, currency_symbol, currency_name))
    
    with col2:
        st.metric("Total NII", format_currency(total_nii, currency_symbol, currency_name))
    
    with col3:
        st.metric("Total Revenue", format_currency(total_revenue, currency_symbol, currency_name))
    
    with col4:
        st.metric("Total Losses", format_currency(total_losses, currency_symbol, currency_name))
    
    with col5:
        st.metric("Gross Profit", format_currency(gross_profit, currency_symbol, currency_name))
    
    # Profit margin
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    st.metric("Profit Margin", f"{profit_margin:.1f}%")
    
    # Revenue breakdown chart
    st.markdown("#### 📊 Revenue Breakdown")
    
    revenue_data = {
        'Component': ['Fees', 'NII'],
        'Amount': [total_fees, total_nii]
    }
    
    df_revenue = pd.DataFrame(revenue_data)
    
    if PLOTLY_AVAILABLE:
        fig = px.bar(df_revenue, x='Component', y='Amount', 
                     title="Revenue Components",
                     color='Component',
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.bar(df_revenue['Component'], df_revenue['Amount'], color=['#00D084', '#00C978'])
        ax.set_title("Revenue Components")
        ax.set_ylabel("Amount")
        st.pyplot(fig)

def create_profit_share_analysis(df_forecast, profit_split, currency_symbol, currency_name):
    """Create profit share analysis section - FIXED VERSION"""
    st.markdown("### 🤝 Revenue Share Distribution Analysis")
    
    # Calculate profit share
    total_profit = df_forecast['Gross Profit'].sum()
    party_a_share = total_profit * (profit_split / 100)
    party_b_share = total_profit * ((100 - profit_split) / 100)
    
    # Profit share metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Gross Profit", format_currency(total_profit, currency_symbol, currency_name))
    
    with col2:
        st.metric(f"Party A Share ({profit_split}%)", format_currency(party_a_share, currency_symbol, currency_name))
    
    with col3:
        st.metric(f"Party B Share ({100-profit_split}%)", format_currency(party_b_share, currency_symbol, currency_name))
    
    # Profit share chart
    st.markdown("#### 📊 Profit Share Distribution")
    
    share_data = {
        'Party': ['Party A', 'Party B'],
        'Share %': [profit_split, 100 - profit_split],
        'Amount': [party_a_share, party_b_share]
    }
    
    df_share = pd.DataFrame(share_data)
    
    if PLOTLY_AVAILABLE:
        fig = px.pie(df_share, values='Amount', names='Party', 
                     title="Profit Share Distribution",
                     color_discrete_sequence=['#00D084', '#00C978'])
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(df_share['Amount'], labels=df_share['Party'], autopct='%1.1f%%')
        ax.set_title("Profit Share Distribution")
        st.pyplot(fig)

def create_default_impact_analysis(df_forecast, currency_symbol, currency_name):
    """Create default impact analysis section"""
    st.markdown("### ⚠️ Default Impact Analysis")
    
    # Calculate default metrics
    total_defaulters = df_forecast['Total Defaulters'].sum()
    total_default_loss = df_forecast['Total Default Loss'].sum()
    default_recovery = df_forecast['Default Recovery Amount'].sum()
    net_default_loss = df_forecast['Net Default Loss (After Recovery)'].sum()
    default_fees = df_forecast['Default Fees Collected'].sum()
    
    # Default metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Defaulters", f"{total_defaulters:,}")
    
    with col2:
        st.metric("Total Default Loss", format_currency(total_default_loss, currency_symbol, currency_name))
    
    with col3:
        st.metric("Default Recovery", format_currency(default_recovery, currency_symbol, currency_name))
    
    with col4:
        st.metric("Net Default Loss", format_currency(net_default_loss, currency_symbol, currency_name))
    
    with col5:
        st.metric("Default Fees", format_currency(default_fees, currency_symbol, currency_name))
    
    # Default impact chart
    st.markdown("#### 📊 Default Impact on Revenue")
    
    impact_data = {
        'Impact Type': ['Pre-Payout Defaults', 'Post-Payout Defaults', 'Recovery Amount'],
        'Amount': [
            df_forecast['Pre-Payout Default Loss'].sum(),
            df_forecast['Post-Payout Default Loss'].sum(),
            default_recovery
        ]
    }
    
    df_impact = pd.DataFrame(impact_data)
    
    if PLOTLY_AVAILABLE:
        fig = px.bar(df_impact, x='Impact Type', y='Amount', 
                     title="Default Impact on Revenue",
                     color='Impact Type',
                     color_discrete_sequence=['#ef4444', '#f59e0b', '#10b981'])
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#ef4444', '#f59e0b', '#10b981']
        ax.bar(df_impact['Impact Type'], df_impact['Amount'], color=colors)
        ax.set_title("Default Impact on Revenue")
        ax.set_ylabel("Amount")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

# =============================================================================
# 📈 CHART FUNCTIONS
# =============================================================================

def create_revenue_chart(df_results, currency_symbol):
    """Create revenue visualization"""
    if PLOTLY_AVAILABLE:
        fig = px.bar(
            df_results.groupby('Duration')['Total Revenue'].sum().reset_index(),
            x='Duration',
            y='Total Revenue',
            title="Revenue by Duration",
            color='Total Revenue',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=400)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        df_grouped = df_results.groupby('Duration')['Total Revenue'].sum()
        ax.bar(df_grouped.index, df_grouped.values, color='#00D084')
        ax.set_title('Revenue by Duration')
        ax.set_xlabel('Duration')
        ax.set_ylabel('Total Revenue')
        ax.grid(True, alpha=0.3)
        return fig

def create_profit_chart(df_results, currency_symbol):
    """Create profit visualization"""
    if PLOTLY_AVAILABLE:
        fig = px.bar(
            df_results.groupby('Slab')['Net Profit'].sum().reset_index(),
            x='Slab',
            y='Net Profit',
            title="Profit by Slab",
            color='Net Profit',
            color_continuous_scale='Plasma'
        )
        fig.update_layout(height=400)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        df_grouped = df_results.groupby('Slab')['Net Profit'].sum()
        ax.bar(df_grouped.index, df_grouped.values, color='#00C978')
        ax.set_title('Profit by Slab')
        ax.set_xlabel('Slab')
        ax.set_ylabel('Net Profit')
        ax.grid(True, alpha=0.3)
        return fig

def create_monthly_pools_chart(df_forecast, currency_symbol, currency_name):
    """Create monthly pools chart"""
    if PLOTLY_AVAILABLE:
        fig = px.line(
            df_forecast.groupby('Month')['Pool Size'].sum().reset_index(),
            x='Month',
            y='Pool Size',
            title="Monthly Pool Size",
            color_discrete_sequence=['#00D084']
        )
        fig.update_layout(height=400)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        df_grouped = df_forecast.groupby('Month')['Pool Size'].sum()
        ax.plot(df_grouped.index, df_grouped.values, color='#00D084', linewidth=2)
        ax.set_title('Monthly Pool Size')
        ax.set_xlabel('Month')
        ax.set_ylabel('Pool Size')
        ax.grid(True, alpha=0.3)
        return fig

def create_users_vs_profit_chart(df_forecast, currency_symbol, currency_name):
    """Create users vs profit chart"""
    if PLOTLY_AVAILABLE:
        fig = px.scatter(
            df_forecast,
            x='Users',
            y='Gross Profit',
            title="Users vs Gross Profit",
            color='Duration',
            size='Pool Size',
            hover_data=['Month', 'Slab Amount']
        )
        fig.update_layout(height=400)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        scatter = ax.scatter(df_forecast['Users'], df_forecast['Gross Profit'], 
                           c=df_forecast['Duration'], s=df_forecast['Pool Size']/1000)
        ax.set_title('Users vs Gross Profit')
        ax.set_xlabel('Users')
        ax.set_ylabel('Gross Profit')
        ax.grid(True, alpha=0.3)
        plt.colorbar(scatter, label='Duration')
        return fig

def create_annual_pools_chart(df_forecast, currency_symbol, currency_name):
    """Create annual pools chart"""
    if PLOTLY_AVAILABLE:
        fig = px.bar(
            df_forecast.groupby('Year')['Pool Size'].sum().reset_index(),
            x='Year',
            y='Pool Size',
            title="Annual Pool Size",
            color='Pool Size',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        df_grouped = df_forecast.groupby('Year')['Pool Size'].sum()
        ax.bar(df_grouped.index, df_grouped.values, color='#3b82f6')
        ax.set_title('Annual Pool Size')
        ax.set_xlabel('Year')
        ax.set_ylabel('Pool Size')
        ax.grid(True, alpha=0.3)
        return fig

def create_annual_users_chart(df_forecast, currency_symbol, currency_name):
    """Create annual users chart"""
    if PLOTLY_AVAILABLE:
        fig = px.bar(
            df_forecast.groupby('Year')['Users'].sum().reset_index(),
            x='Year',
            y='Users',
            title="Annual Users",
            color='Users',
            color_continuous_scale='Greens'
        )
        fig.update_layout(height=400)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        df_grouped = df_forecast.groupby('Year')['Users'].sum()
        ax.bar(df_grouped.index, df_grouped.values, color='#10b981')
        ax.set_title('Annual Users')
        ax.set_xlabel('Year')
        ax.set_ylabel('Users')
        ax.grid(True, alpha=0.3)
        return fig

def create_external_capital_chart(df_forecast, currency_symbol, currency_name):
    """Create external capital chart"""
    if PLOTLY_AVAILABLE:
        fig = px.line(
            df_forecast.groupby('Month')['External Capital'].sum().reset_index(),
            x='Month',
            y='External Capital',
            title="External Capital Over Time",
            color_discrete_sequence=['#f59e0b']
        )
        fig.update_layout(height=400)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        df_grouped = df_forecast.groupby('Month')['External Capital'].sum()
        ax.plot(df_grouped.index, df_grouped.values, color='#f59e0b', linewidth=2)
        ax.set_title('External Capital Over Time')
        ax.set_xlabel('Month')
        ax.set_ylabel('External Capital')
        ax.grid(True, alpha=0.3)
        return fig

# =============================================================================
# 📊 SUMMARY FUNCTIONS
# =============================================================================

def create_monthly_summary(df_forecast):
    """Create monthly summary from forecast data with proper monthly aggregation"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    # Determine which columns exist (handle both standard and TAM format)
    has_users = 'Users' in df_forecast.columns
    has_users_in_slot = 'Users in Slot' in df_forecast.columns
    has_total_fees_collected = 'Total Fees Collected' in df_forecast.columns
    has_total_fees = 'Total Fees' in df_forecast.columns
    has_total_nii_lifetime = 'Total NII (Lifetime)' in df_forecast.columns
    has_total_nii = 'Total NII' in df_forecast.columns
    
    # Get user column
    if has_users:
        users_col = 'Users'
    elif has_users_in_slot:
        users_col = 'Users in Slot'
    else:
        users_col = None
    
    # Get fees column
    if has_total_fees_collected:
        fees_col = 'Total Fees Collected'
    elif has_total_fees:
        fees_col = 'Total Fees'
    else:
        fees_col = None
    
    # Get NII column
    if has_total_nii_lifetime:
        nii_col = 'Total NII (Lifetime)'
    elif has_total_nii:
        nii_col = 'Total NII'
    else:
        nii_col = None
    
    # Group by actual Month column to get monthly breakdowns
    if 'Month' in df_forecast.columns:
        monthly_grouped = df_forecast.groupby('Month').agg({
            users_col: 'sum' if users_col else 'sum',
            'Total Revenue': 'sum',
            'Gross Profit': 'sum',
            fees_col: 'sum' if fees_col else 'sum',
            nii_col: 'sum' if nii_col else 'sum'
        }).reset_index()
        
        monthly_grouped.columns = ['Month', 'Users Joining This Month', 'Total Revenue', 'Gross Profit', 'Total Fees', 'Total NII']
        
        # Format Month column
        monthly_grouped['Month'] = 'Month ' + monthly_grouped['Month'].astype(str)
        
        return monthly_grouped
    else:
        # Fallback if no Month column
        monthly_data = []
        for month in range(1, 13):
            month_data = {
                'Month': f"Month {month}",
                'Users Joining This Month': 0,
                'Total Revenue': 0,
                'Gross Profit': 0,
                'Total Fees': 0,
                'Total NII': 0
            }
            monthly_data.append(month_data)
        
        return pd.DataFrame(monthly_data)

def create_yearly_summary(df_monthly):
    """Create yearly summary with 5-year YoY projections"""
    if df_monthly.empty:
        return pd.DataFrame()
    
    # Get Year 1 data
    year1_users = df_monthly['Users Joining This Month'].sum()
    year1_revenue = df_monthly['Total Revenue'].sum()
    year1_profit = df_monthly['Gross Profit'].sum()
    year1_fees = df_monthly['Total Fees'].sum()
    year1_nii = df_monthly['Total NII'].sum()
    
    # Get YoY growth rate from session state, default to 15%
    yoy_growth_rate = st.session_state.get('yoy_growth_rate', 15.0)
    yearly_growth = 1 + (yoy_growth_rate / 100)
    
    # Create 5 years
    yearly_data = []
    for year in range(1, 6):
        if year == 1:
            # Actual data from forecast
            users = year1_users
            revenue = year1_revenue
            profit = year1_profit
            fees = year1_fees
            nii = year1_nii
        else:
            # Project future years with growth
            growth_factor = yearly_growth ** (year - 1)
            users = int(year1_users * growth_factor)
            revenue = year1_revenue * growth_factor
            profit = year1_profit * growth_factor
            fees = year1_fees * growth_factor
            nii = year1_nii * growth_factor
        
        yearly_data.append({
            'Year': f'Year {year}',
            'Total Users': users,
            'Total Revenue': revenue,
            'Gross Profit': profit,
            'Total Fees': fees,
            'Total NII': nii
        })
    
    return pd.DataFrame(yearly_data)

def create_profit_share_analysis_simple(df_yearly, profit_split):
    """Create profit share analysis - simple version"""
    if df_yearly.empty:
        return pd.DataFrame()
    
    total_profit = df_yearly['Gross Profit'].sum()
    party_a_share = total_profit * (profit_split / 100)
    party_b_share = total_profit * ((100 - profit_split) / 100)
    
    return pd.DataFrame({
        'Party': ['Party A', 'Party B'],
        'Share %': [profit_split, 100 - profit_split],
        'Amount': [party_a_share, party_b_share]
    })

def create_deposit_log(df_forecast):
    """Create deposit log"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    # Determine user column
    users_col = 'Users in Slot' if 'Users in Slot' in df_forecast.columns else 'Users'
    fees_col = 'Total Fees' if 'Total Fees' in df_forecast.columns else 'Total Fees Collected'
    monthly_fee_col = 'Monthly Fee' if 'Monthly Fee' in df_forecast.columns else 'Monthly Fee Collection'
    
    deposit_data = []
    for _, row in df_forecast.iterrows():
        for month in range(1, 13):
            users = row[users_col] if users_col in df_forecast.columns else 0
            slab_amt = row.get('Slab Amount', 0)
            deposit_data.append({
                'Month': f"Month {month}",
                'Duration': row.get('Duration', 0),
                'Slab Amount': slab_amt,
                'Users': users,
                'Monthly Deposit': slab_amt,
                'Total Deposits': slab_amt * users,
                'Fee Collected': row.get(monthly_fee_col, 0),
                'Total Fee': row.get(fees_col, 0)
            })
    
    return pd.DataFrame(deposit_data)

def create_default_log(df_forecast):
    """Create default log"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    # Determine user column
    users_col = 'Users in Slot' if 'Users in Slot' in df_forecast.columns else 'Users'
    
    default_data = []
    for _, row in df_forecast.iterrows():
        for month in range(1, 13):
            default_data.append({
                'Month': f"Month {month}",
                'Duration': row.get('Duration', 0),
                'Slab Amount': row.get('Slab Amount', 0),
                'Users': row.get(users_col, 0),
                'Pre-Payout Defaults': row.get('Pre-Payout Default Loss', 0),
                'Post-Payout Defaults': row.get('Post-Payout Default Loss', 0),
                'Total Defaults': row.get('Total Default Loss', 0),
                'Recovery Amount': row.get('Default Recovery', 0) or row.get('Default Recovery Amount', 0),
                'Net Default Loss': row.get('Net Default Loss', 0) or row.get('Net Default Loss (After Recovery)', 0)
            })
    
    return pd.DataFrame(default_data)

def create_lifecycle_log(df_forecast):
    """Create lifecycle log"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    # Determine user column
    users_col = 'Users in Slot' if 'Users in Slot' in df_forecast.columns else 'Users'
    
    lifecycle_data = []
    for _, row in df_forecast.iterrows():
        for month in range(1, 13):
            users = row.get(users_col, 0)
            lifecycle_data.append({
                'Month': f"Month {month}",
                'Duration': row.get('Duration', 0),
                'Slab Amount': row.get('Slab Amount', 0),
                'Users': users,
                'New Users': users // 12,
                'Rejoining Users': row.get('Returning Users', 0),
                'Churned Users': row.get('Churned Users', 0),
                'Active Users': users,
                'Pool Size': row.get('Pool Size', 0)
            })
    
    return pd.DataFrame(lifecycle_data)

def create_forecast_summary(df_forecast):
    """Create forecast summary"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    summary_data = {
        'Metric': [
            'Total Users',
            'Total Revenue',
            'Gross Profit',
            'Total Fees',
            'Total NII',
            'Total Defaults',
            'Net Profit',
            'Profit Margin (%)'
        ],
        'Value': [
            df_forecast['Users'].sum(),
            df_forecast['Total Revenue'].sum(),
            df_forecast['Gross Profit'].sum(),
            df_forecast['Total Fees Collected'].sum(),
            df_forecast['Total NII (Lifetime)'].sum(),
            df_forecast['Total Default Loss'].sum(),
            df_forecast['Net Profit'].sum(),
            (df_forecast['Gross Profit'].sum() / df_forecast['Total Revenue'].sum() * 100) if df_forecast['Total Revenue'].sum() > 0 else 0
        ]
    }
    
    return pd.DataFrame(summary_data)

def create_duration_analysis(df_forecast):
    """Create duration analysis"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    duration_data = []
    for duration in df_forecast['Duration'].unique():
        duration_df = df_forecast[df_forecast['Duration'] == duration]
        duration_data.append({
            'Duration': f"{duration}M",
            'Users': duration_df['Users'].sum(),
            'Revenue': duration_df['Total Revenue'].sum(),
            'Profit': duration_df['Gross Profit'].sum(),
            'Fees': duration_df['Total Fees Collected'].sum(),
            'NII': duration_df['Total NII (Lifetime)'].sum(),
            'Defaults': duration_df['Total Default Loss'].sum()
        })
    
    return pd.DataFrame(duration_data)

def create_slab_analysis(df_forecast):
    """Create slab analysis"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    slab_data = []
    for slab in df_forecast['Slab Amount'].unique():
        slab_df = df_forecast[df_forecast['Slab Amount'] == slab]
        slab_data.append({
            'Slab Amount': f"₨{slab:,}",
            'Users': slab_df['Users'].sum(),
            'Revenue': slab_df['Total Revenue'].sum(),
            'Profit': slab_df['Gross Profit'].sum(),
            'Fees': slab_df['Total Fees Collected'].sum(),
            'NII': slab_df['Total NII (Lifetime)'].sum(),
            'Defaults': slab_df['Total Default Loss'].sum()
        })
    
    return pd.DataFrame(slab_data)

def create_scenario_comparison(scenarios_data):
    """Create scenario comparison"""
    if not scenarios_data:
        return pd.DataFrame()
    
    comparison_data = []
    for scenario_name, df_forecast in scenarios_data.items():
        if not df_forecast.empty:
            comparison_data.append({
                'Scenario': scenario_name,
                'Users': df_forecast['Users'].sum(),
                'Revenue': df_forecast['Total Revenue'].sum(),
                'Profit': df_forecast['Gross Profit'].sum(),
                'Fees': df_forecast['Total Fees Collected'].sum(),
                'NII': df_forecast['Total NII (Lifetime)'].sum(),
                'Defaults': df_forecast['Total Default Loss'].sum(),
                'Profit Margin (%)': (df_forecast['Gross Profit'].sum() / df_forecast['Total Revenue'].sum() * 100) if df_forecast['Total Revenue'].sum() > 0 else 0
            })
    
    return pd.DataFrame(comparison_data)

def create_cohort_analysis(df_forecast):
    """Create cohort analysis"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    cohort_data = []
    for month in range(1, 13):
        month_df = df_forecast[df_forecast['Month'] == month]
        cohort_data.append({
            'Cohort Month': f"Month {month}",
            'New Users': month_df['Users'].sum(),
            'Revenue': month_df['Total Revenue'].sum(),
            'Profit': month_df['Gross Profit'].sum(),
            'Retention Rate (%)': 100.0,  # Placeholder
            'LTV': month_df['Gross Profit'].sum() / month_df['Users'].sum() if month_df['Users'].sum() > 0 else 0
        })
    
    return pd.DataFrame(cohort_data)
def create_user_lifecycle_summary(config, duration):
    """Create a comprehensive 12-month user lifecycle summary"""
    user_lifecycle = calculate_user_lifecycle(config, duration)
    
    # Create summary DataFrame
    summary_data = []
    for month in range(1, 13):
        summary_data.append({
            'Month': f"Month {month}",
            'New Users': user_lifecycle['new_users'][month],
            'Returning Users': user_lifecycle['returning_users'][month],
            'Resting Users': user_lifecycle['resting_users'][month],
            'Active Users': user_lifecycle['active_users'][month],
            'Total Users to Date': user_lifecycle['total_users'][month]
        })
    
    return pd.DataFrame(summary_data)

def create_monthly_view(df_forecast, currency_symbol, currency_name):
    """Create detailed monthly view"""
    st.markdown("#### 📅 Monthly Detailed View")
    
    # Get the first duration for the summary
    if not df_forecast.empty:
        first_duration = df_forecast['Duration'].iloc[0]
        lifecycle_summary = create_user_lifecycle_summary(st.session_state.get('config', {}), first_duration)
        
        # Add additional metrics
        monthly_data = df_forecast.groupby('Month').agg({
            'New Users': 'sum',
            'Returning Users': 'sum',
            'Churned Users': 'sum',
            'Rest Period Users': 'sum',
            'Users': 'sum',
            'Total Users to Date': 'sum',
            'Pool Size': 'sum',
            'Total Revenue': 'sum',
            'Gross Profit': 'sum'
        }).reset_index()
        
        # Calculate month-over-month growth rates
        monthly_data['New Users Growth %'] = monthly_data['New Users'].pct_change() * 100
        monthly_data['Total Users Growth %'] = monthly_data['Total Users to Date'].pct_change() * 100
        monthly_data['Revenue Growth %'] = monthly_data['Total Revenue'].pct_change() * 100
        
        # Format the data
        monthly_data['New Users Growth %'] = monthly_data['New Users Growth %'].fillna(0).round(1)
        monthly_data['Total Users Growth %'] = monthly_data['Total Users Growth %'].fillna(0).round(1)
        monthly_data['Revenue Growth %'] = monthly_data['Revenue Growth %'].fillna(0).round(1)
        
        # Store original numeric values BEFORE formatting for display
        monthly_data_numeric = monthly_data.copy()
        
        # Format Month column
        monthly_data['Month'] = monthly_data['Month'].apply(lambda x: f"Month {x+1}")
        
        # Format all numeric columns with commas (except percentages) for display only
        numeric_cols = ['New Users', 'Returning Users', 'Churned Users', 'Rest Period Users', 
                       'Users', 'Total Users to Date', 'Pool Size', 'Total Revenue', 'Gross Profit']
        for col in numeric_cols:
            if col in monthly_data.columns:
                monthly_data[col] = monthly_data[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else x)
        
        # Display the table
        st.dataframe(monthly_data, use_container_width=True)
        
        # Monthly metrics summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_monthly_growth = monthly_data['New Users Growth %'].mean()
            st.metric("Avg Monthly Growth", f"{avg_monthly_growth:.1f}%")
        
        with col2:
            peak_month_idx = monthly_data_numeric['Users'].idxmax()
            peak_month = monthly_data_numeric.loc[peak_month_idx, 'Month']
            peak_users = monthly_data_numeric['Users'].max()
            st.metric("Peak Month", f"Month {int(peak_month)+1}")
        
        with col3:
            total_revenue = monthly_data_numeric['Total Revenue'].sum()
            st.metric("Total Revenue", format_currency(total_revenue, currency_symbol, currency_name))
        
        with col4:
            total_users_sum = monthly_data_numeric['Users'].sum()
            avg_revenue_per_user = total_revenue / total_users_sum if total_users_sum > 0 else 0
            st.metric("Revenue per User", format_currency(avg_revenue_per_user, currency_symbol, currency_name))
        
        # Fancy Monthly Charts
        st.markdown("#### 📊 Monthly Trend Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # User Trends Chart
            if PLOTLY_AVAILABLE:
                fig_users = go.Figure()
                
                # Add traces with trendy colors - use numeric data for charts
                fig_users.add_trace(go.Scatter(
                    x=monthly_data_numeric['Month'].apply(lambda x: f"M{int(x)+1}"), 
                    y=monthly_data_numeric['New Users'],
                    mode='lines+markers',
                    name='New Users',
                    line=dict(color='#00D084', width=3),
                    marker=dict(size=8, color='#00D084')
                ))
                
                fig_users.add_trace(go.Scatter(
                    x=monthly_data_numeric['Month'].apply(lambda x: f"M{int(x)+1}"), 
                    y=monthly_data_numeric['Returning Users'],
                    mode='lines+markers',
                    name='Returning Users',
                    line=dict(color='#00C978', width=3),
                    marker=dict(size=8, color='#00C978')
                ))
                
                fig_users.add_trace(go.Scatter(
                    x=monthly_data_numeric['Month'].apply(lambda x: f"M{int(x)+1}"), 
                    y=monthly_data_numeric['Users'],
                    mode='lines+markers',
                    name='Active Users',
                    line=dict(color='#f093fb', width=3),
                    marker=dict(size=8, color='#f093fb')
                ))
                
                fig_users.update_layout(
                    title="📈 Monthly User Trends",
                    xaxis_title="Month",
                    yaxis_title="Number of Users",
                    height=400,
                    template="plotly_white",
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_users, use_container_width=True)
            else:
                fig, ax = plt.subplots(figsize=(10, 6))
                months_labels = monthly_data_numeric['Month'].apply(lambda x: f"M{int(x)+1}")
                ax.plot(months_labels, monthly_data_numeric['New Users'], 'o-', color='#00D084', linewidth=3, markersize=8, label='New Users')
                ax.plot(months_labels, monthly_data_numeric['Returning Users'], 'o-', color='#00C978', linewidth=3, markersize=8, label='Returning Users')
                ax.plot(months_labels, monthly_data_numeric['Users'], 'o-', color='#f093fb', linewidth=3, markersize=8, label='Active Users')
                ax.set_title("📈 Monthly User Trends", fontsize=16, fontweight='bold')
                ax.set_xlabel("Month", fontsize=12)
                ax.set_ylabel("Number of Users", fontsize=12)
                ax.legend(fontsize=10)
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
        
        with col2:
            # Revenue Trends Chart
            if PLOTLY_AVAILABLE:
                fig_revenue = go.Figure()
                months_labels = monthly_data_numeric['Month'].apply(lambda x: f"M{int(x)+1}")
                
                fig_revenue.add_trace(go.Scatter(
                    x=months_labels, 
                    y=monthly_data_numeric['Total Revenue'],
                    mode='lines+markers',
                    name='Total Revenue',
                    line=dict(color='#4facfe', width=3),
                    marker=dict(size=8, color='#4facfe'),
                    fill='tonexty'
                ))
                
                fig_revenue.add_trace(go.Scatter(
                    x=months_labels, 
                    y=monthly_data_numeric['Gross Profit'],
                    mode='lines+markers',
                    name='Gross Profit',
                    line=dict(color='#00f2fe', width=3),
                    marker=dict(size=8, color='#00f2fe')
                ))
                
                fig_revenue.update_layout(
                    title="💰 Monthly Revenue Trends",
                    xaxis_title="Month",
                    yaxis_title="Amount",
                    height=400,
                    template="plotly_white",
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_revenue, use_container_width=True)
            else:
                fig, ax = plt.subplots(figsize=(10, 6))
                months_labels = monthly_data_numeric['Month'].apply(lambda x: f"M{int(x)+1}")
                ax.plot(months_labels, monthly_data_numeric['Total Revenue'], 'o-', color='#4facfe', linewidth=3, markersize=8, label='Total Revenue')
                ax.plot(months_labels, monthly_data_numeric['Gross Profit'], 'o-', color='#00f2fe', linewidth=3, markersize=8, label='Gross Profit')
                ax.set_title("💰 Monthly Revenue Trends", fontsize=16, fontweight='bold')
                ax.set_xlabel("Month", fontsize=12)
                ax.set_ylabel("Amount", fontsize=12)
                ax.legend(fontsize=10)
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
        
        # Growth Rate Chart
        if PLOTLY_AVAILABLE:
            fig_growth = go.Figure()
            
            fig_growth.add_trace(go.Scatter(
                x=monthly_data['Month'], 
                y=monthly_data['New Users Growth %'],
                mode='lines+markers',
                name='New Users Growth %',
                line=dict(color='#fa709a', width=3),
                marker=dict(size=8, color='#fa709a')
            ))
            
            fig_growth.add_trace(go.Scatter(
                x=monthly_data['Month'], 
                y=monthly_data['Revenue Growth %'],
                mode='lines+markers',
                name='Revenue Growth %',
                line=dict(color='#fee140', width=3),
                marker=dict(size=8, color='#fee140')
            ))
            
            fig_growth.update_layout(
                title="📈 Monthly Growth Rates",
                xaxis_title="Month",
                yaxis_title="Growth %",
                height=400,
                template="plotly_white",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(monthly_data['Month'], monthly_data['New Users Growth %'], 'o-', color='#fa709a', linewidth=3, markersize=8, label='New Users Growth %')
            ax.plot(monthly_data['Month'], monthly_data['Revenue Growth %'], 'o-', color='#fee140', linewidth=3, markersize=8, label='Revenue Growth %')
            ax.set_title("📈 Monthly Growth Rates", fontsize=16, fontweight='bold')
            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Growth %", fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

def create_yearly_view(df_forecast, currency_symbol, currency_name):
    """Create yearly summary view"""
    st.markdown("#### 📆 Yearly Summary View")
    
    # Group by year
    yearly_data = df_forecast.groupby('Year').agg({
        'New Users': 'sum',
        'Returning Users': 'sum',
        'Churned Users': 'sum',
        'Rest Period Users': 'sum',
        'Users': 'sum',
        'Total Users to Date': 'sum',
        'Pool Size': 'sum',
        'Total Revenue': 'sum',
        'Gross Profit': 'sum',
        'Total Fees Collected': 'sum',
        'Total NII (Lifetime)': 'sum'
    }).reset_index()
    
    # Calculate yearly metrics
    yearly_data['User Growth %'] = yearly_data['Total Users to Date'].pct_change() * 100
    yearly_data['Revenue Growth %'] = yearly_data['Total Revenue'].pct_change() * 100
    yearly_data['Profit Margin %'] = (yearly_data['Gross Profit'] / yearly_data['Total Revenue'] * 100).round(1)
    yearly_data['Revenue per User'] = (yearly_data['Total Revenue'] / yearly_data['Users']).round(0)
    
    # Fill NaN values
    yearly_data['User Growth %'] = yearly_data['User Growth %'].fillna(0)
    yearly_data['Revenue Growth %'] = yearly_data['Revenue Growth %'].fillna(0)
    
    # Display yearly table
    st.dataframe(yearly_data, use_container_width=True)
    
    # Yearly metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_years = len(yearly_data)
        st.metric("Total Years", f"{total_years}")
    
    with col2:
        avg_yearly_growth = yearly_data['User Growth %'].mean()
        st.metric("Avg Yearly Growth", f"{avg_yearly_growth:.1f}%")
    
    with col3:
        total_revenue = yearly_data['Total Revenue'].sum()
        st.metric("Total Revenue", format_currency(total_revenue, currency_symbol, currency_name))
    
    with col4:
        total_profit = yearly_data['Gross Profit'].sum()
        st.metric("Total Profit", format_currency(total_profit, currency_symbol, currency_name))
    
    # Fancy Yearly Charts
    st.markdown("#### 📊 Yearly Analysis Charts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Yearly User Distribution Pie Chart
        if PLOTLY_AVAILABLE:
            fig_pie = go.Figure(data=[go.Pie(
                labels=['New Users', 'Returning Users', 'Churned Users', 'Rest Period Users'],
                values=[
                    yearly_data['New Users'].sum(),
                    yearly_data['Returning Users'].sum(),
                    yearly_data['Churned Users'].sum(),
                    yearly_data['Rest Period Users'].sum()
                ],
                hole=0.4,
                marker_colors=['#00D084', '#00C978', '#ef4444', '#f59e0b']
            )])
            
            fig_pie.update_layout(
                title="👥 Yearly User Distribution",
                height=400,
                template="plotly_white",
                showlegend=True
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(8, 8))
            labels = ['New Users', 'Returning Users', 'Churned Users', 'Rest Period Users']
            values = [
                yearly_data['New Users'].sum(),
                yearly_data['Returning Users'].sum(),
                yearly_data['Churned Users'].sum(),
                yearly_data['Rest Period Users'].sum()
            ]
            colors = ['#00D084', '#00C978', '#ef4444', '#f59e0b']
            
            wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title("👥 Yearly User Distribution", fontsize=16, fontweight='bold')
            st.pyplot(fig)
    
    with col2:
        # Revenue vs Profit Bar Chart
        if PLOTLY_AVAILABLE:
            fig_bar = go.Figure()
            
            fig_bar.add_trace(go.Bar(
                x=yearly_data['Year'],
                y=yearly_data['Total Revenue'],
                name='Total Revenue',
                marker_color='#4facfe',
                text=yearly_data['Total Revenue'],
                textposition='auto'
            ))
            
            fig_bar.add_trace(go.Bar(
                x=yearly_data['Year'],
                y=yearly_data['Gross Profit'],
                name='Gross Profit',
                marker_color='#00f2fe',
                text=yearly_data['Gross Profit'],
                textposition='auto'
            ))
            
            fig_bar.update_layout(
                title="💰 Yearly Revenue vs Profit",
                xaxis_title="Year",
                yaxis_title="Amount",
                height=400,
                template="plotly_white",
                barmode='group'
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            x = yearly_data['Year']
            width = 0.35
            
            ax.bar(x - width/2, yearly_data['Total Revenue'], width, label='Total Revenue', color='#4facfe')
            ax.bar(x + width/2, yearly_data['Gross Profit'], width, label='Gross Profit', color='#00f2fe')
            
            ax.set_title("💰 Yearly Revenue vs Profit", fontsize=16, fontweight='bold')
            ax.set_xlabel("Year", fontsize=12)
            ax.set_ylabel("Amount", fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
    
    # Profit Margin Trend
    if PLOTLY_AVAILABLE:
        fig_margin = go.Figure()
        
        fig_margin.add_trace(go.Scatter(
            x=yearly_data['Year'],
            y=yearly_data['Profit Margin %'],
            mode='lines+markers',
            name='Profit Margin %',
            line=dict(color='#fa709a', width=4),
            marker=dict(size=12, color='#fa709a')
        ))
        
        fig_margin.update_layout(
            title="📈 Yearly Profit Margin Trend",
            xaxis_title="Year",
            yaxis_title="Profit Margin %",
            height=400,
            template="plotly_white",
            showlegend=True
        )
        
        st.plotly_chart(fig_margin, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(yearly_data['Year'], yearly_data['Profit Margin %'], 'o-', color='#fa709a', linewidth=4, markersize=12, label='Profit Margin %')
        ax.set_title("📈 Yearly Profit Margin Trend", fontsize=16, fontweight='bold')
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Profit Margin %", fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

def create_mom_growth_view(df_forecast, currency_symbol, currency_name):
    """Create month-on-month growth analysis"""
    st.markdown("#### 📈 Month-on-Month Growth Analysis")
    
    # Calculate month-over-month metrics
    monthly_data = df_forecast.groupby('Month').agg({
        'New Users': 'sum',
        'Returning Users': 'sum',
        'Users': 'sum',
        'Total Users to Date': 'sum',
        'Pool Size': 'sum',
        'Total Revenue': 'sum',
        'Gross Profit': 'sum'
    }).reset_index()
    
    # Calculate growth rates
    monthly_data['New Users MoM %'] = monthly_data['New Users'].pct_change() * 100
    monthly_data['Returning Users MoM %'] = monthly_data['Returning Users'].pct_change() * 100
    monthly_data['Active Users MoM %'] = monthly_data['Users'].pct_change() * 100
    monthly_data['Total Users MoM %'] = monthly_data['Total Users to Date'].pct_change() * 100
    monthly_data['Revenue MoM %'] = monthly_data['Total Revenue'].pct_change() * 100
    monthly_data['Profit MoM %'] = monthly_data['Gross Profit'].pct_change() * 100
    
    # Fill NaN values and round
    growth_columns = ['New Users MoM %', 'Returning Users MoM %', 'Active Users MoM %', 
                     'Total Users MoM %', 'Revenue MoM %', 'Profit MoM %']
    for col in growth_columns:
        monthly_data[col] = monthly_data[col].fillna(0).round(1)
    
    # Display growth table
    st.dataframe(monthly_data, use_container_width=True)
    
    # Growth analysis metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_new_users_growth = monthly_data['New Users MoM %'].mean()
        st.metric("Avg New Users MoM", f"{avg_new_users_growth:.1f}%")
    
    with col2:
        avg_revenue_growth = monthly_data['Revenue MoM %'].mean()
        st.metric("Avg Revenue MoM", f"{avg_revenue_growth:.1f}%")
    
    with col3:
        max_growth_month = monthly_data.loc[monthly_data['Revenue MoM %'].idxmax(), 'Month']
        max_growth_rate = monthly_data['Revenue MoM %'].max()
        st.metric("Peak Growth Month", f"Month {max_growth_month}")
    
    with col4:
        min_growth_month = monthly_data.loc[monthly_data['Revenue MoM %'].idxmin(), 'Month']
        min_growth_rate = monthly_data['Revenue MoM %'].min()
        st.metric("Lowest Growth Month", f"Month {min_growth_month}")
    
    # Fancy MoM Growth Charts
    st.markdown("#### 📊 Month-on-Month Growth Charts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # User Growth Rates Chart
        if PLOTLY_AVAILABLE:
            fig_user_growth = go.Figure()
            
            fig_user_growth.add_trace(go.Scatter(
                x=monthly_data['Month'],
                y=monthly_data['New Users MoM %'],
                mode='lines+markers',
                name='New Users MoM %',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8, color='#667eea')
            ))
            
            fig_user_growth.add_trace(go.Scatter(
                x=monthly_data['Month'],
                y=monthly_data['Returning Users MoM %'],
                mode='lines+markers',
                name='Returning Users MoM %',
                line=dict(color='#764ba2', width=3),
                marker=dict(size=8, color='#764ba2')
            ))
            
            fig_user_growth.add_trace(go.Scatter(
                x=monthly_data['Month'],
                y=monthly_data['Active Users MoM %'],
                mode='lines+markers',
                name='Active Users MoM %',
                line=dict(color='#f093fb', width=3),
                marker=dict(size=8, color='#f093fb')
            ))
            
            fig_user_growth.update_layout(
                title="👥 User Growth Rates (MoM)",
                xaxis_title="Month",
                yaxis_title="Growth %",
                height=400,
                template="plotly_white",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_user_growth, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(monthly_data['Month'], monthly_data['New Users MoM %'], 'o-', color='#667eea', linewidth=3, markersize=8, label='New Users MoM %')
            ax.plot(monthly_data['Month'], monthly_data['Returning Users MoM %'], 'o-', color='#764ba2', linewidth=3, markersize=8, label='Returning Users MoM %')
            ax.plot(monthly_data['Month'], monthly_data['Active Users MoM %'], 'o-', color='#f093fb', linewidth=3, markersize=8, label='Active Users MoM %')
            ax.set_title("👥 User Growth Rates (MoM)", fontsize=16, fontweight='bold')
            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Growth %", fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
    
    with col2:
        # Financial Growth Rates Chart
        if PLOTLY_AVAILABLE:
            fig_financial_growth = go.Figure()
            
            fig_financial_growth.add_trace(go.Scatter(
                x=monthly_data['Month'],
                y=monthly_data['Revenue MoM %'],
                mode='lines+markers',
                name='Revenue MoM %',
                line=dict(color='#4facfe', width=3),
                marker=dict(size=8, color='#4facfe')
            ))
            
            fig_financial_growth.add_trace(go.Scatter(
                x=monthly_data['Month'],
                y=monthly_data['Profit MoM %'],
                mode='lines+markers',
                name='Profit MoM %',
                line=dict(color='#00f2fe', width=3),
                marker=dict(size=8, color='#00f2fe')
            ))
            
            fig_financial_growth.update_layout(
                title="💰 Financial Growth Rates (MoM)",
                xaxis_title="Month",
                yaxis_title="Growth %",
                height=400,
                template="plotly_white",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_financial_growth, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(monthly_data['Month'], monthly_data['Revenue MoM %'], 'o-', color='#4facfe', linewidth=3, markersize=8, label='Revenue MoM %')
            ax.plot(monthly_data['Month'], monthly_data['Profit MoM %'], 'o-', color='#00f2fe', linewidth=3, markersize=8, label='Profit MoM %')
            ax.set_title("💰 Financial Growth Rates (MoM)", fontsize=16, fontweight='bold')
            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Growth %", fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
    
    # Growth Heatmap
    if PLOTLY_AVAILABLE:
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=[
                monthly_data['New Users MoM %'].tolist(),
                monthly_data['Returning Users MoM %'].tolist(),
                monthly_data['Active Users MoM %'].tolist(),
                monthly_data['Revenue MoM %'].tolist(),
                monthly_data['Profit MoM %'].tolist()
            ],
            x=monthly_data['Month'].tolist(),
            y=['New Users', 'Returning Users', 'Active Users', 'Revenue', 'Profit'],
            colorscale='RdYlBu_r',
            showscale=True
        ))
        
        fig_heatmap.update_layout(
            title="🔥 Growth Rate Heatmap (MoM)",
            xaxis_title="Month",
            yaxis_title="Metric",
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        data = [
            monthly_data['New Users MoM %'].tolist(),
            monthly_data['Returning Users MoM %'].tolist(),
            monthly_data['Active Users MoM %'].tolist(),
            monthly_data['Revenue MoM %'].tolist(),
            monthly_data['Profit MoM %'].tolist()
        ]
        im = ax.imshow(data, cmap='RdYlBu_r', aspect='auto')
        ax.set_xticks(range(len(monthly_data['Month'])))
        ax.set_xticklabels(monthly_data['Month'])
        ax.set_yticks(range(5))
        ax.set_yticklabels(['New Users', 'Returning Users', 'Active Users', 'Revenue', 'Profit'])
        ax.set_title("🔥 Growth Rate Heatmap (MoM)", fontsize=16, fontweight='bold')
        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Metric", fontsize=12)
        plt.colorbar(im, ax=ax)
        st.pyplot(fig)

def create_yoy_comparison_view(df_forecast, currency_symbol, currency_name):
    """Create year-over-year comparison view"""
    st.markdown("#### 🔄 Year-over-Year Comparison")
    
    # Since we only have one year of data, create a simulated comparison
    # This would normally compare different years
    
    # Group by year and month for comparison
    monthly_yearly_data = df_forecast.groupby(['Year', 'Month']).agg({
        'New Users': 'sum',
        'Returning Users': 'sum',
        'Users': 'sum',
        'Total Users to Date': 'sum',
        'Total Revenue': 'sum',
        'Gross Profit': 'sum'
    }).reset_index()
    
    # Create comparison table (simulated for demonstration)
    comparison_data = []
    for month in range(1, 13):
        month_data = monthly_yearly_data[monthly_yearly_data['Month'] == month]
        if not month_data.empty:
            current_year_data = month_data.iloc[0]
            
            # Simulate previous year data (for demonstration)
            prev_year_multiplier = 0.85  # Assume 15% growth year-over-year
            comparison_data.append({
                'Month': f"Month {month}",
                'Current Year Users': int(current_year_data['Users']),
                'Previous Year Users': int(current_year_data['Users'] * prev_year_multiplier),
                'YoY Growth %': ((current_year_data['Users'] - current_year_data['Users'] * prev_year_multiplier) / (current_year_data['Users'] * prev_year_multiplier) * 100),
                'Current Year Revenue': current_year_data['Total Revenue'],
                'Previous Year Revenue': current_year_data['Total Revenue'] * prev_year_multiplier,
                'Revenue YoY Growth %': ((current_year_data['Total Revenue'] - current_year_data['Total Revenue'] * prev_year_multiplier) / (current_year_data['Total Revenue'] * prev_year_multiplier) * 100)
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df['YoY Growth %'] = comparison_df['YoY Growth %'].round(1)
    comparison_df['Revenue YoY Growth %'] = comparison_df['Revenue YoY Growth %'].round(1)
    
    # Display comparison table
    st.dataframe(comparison_df, use_container_width=True)
    
    # YoY metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_yoy_growth = comparison_df['YoY Growth %'].mean()
        st.metric("Avg YoY Growth", f"{avg_yoy_growth:.1f}%")
    
    with col2:
        avg_revenue_yoy = comparison_df['Revenue YoY Growth %'].mean()
        st.metric("Avg Revenue YoY", f"{avg_revenue_yoy:.1f}%")
    
    with col3:
        best_yoy_month = comparison_df.loc[comparison_df['YoY Growth %'].idxmax(), 'Month']
        best_yoy_rate = comparison_df['YoY Growth %'].max()
        st.metric("Best YoY Month", f"{best_yoy_month}")
    
    with col4:
        total_yoy_impact = comparison_df['Current Year Users'].sum() - comparison_df['Previous Year Users'].sum()
        st.metric("Total YoY Impact", f"{total_yoy_impact:,} users")
    
    # Fancy YoY Comparison Charts
    st.markdown("#### 📊 Year-over-Year Comparison Charts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # User Comparison Chart
        if PLOTLY_AVAILABLE:
            fig_users_yoy = go.Figure()
            
            fig_users_yoy.add_trace(go.Scatter(
                x=comparison_df['Month'],
                y=comparison_df['Current Year Users'],
                mode='lines+markers',
                name='Current Year Users',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8, color='#667eea')
            ))
            
            fig_users_yoy.add_trace(go.Scatter(
                x=comparison_df['Month'],
                y=comparison_df['Previous Year Users'],
                mode='lines+markers',
                name='Previous Year Users',
                line=dict(color='#764ba2', width=3, dash='dash'),
                marker=dict(size=8, color='#764ba2')
            ))
            
            fig_users_yoy.update_layout(
                title="👥 User Count Comparison (YoY)",
                xaxis_title="Month",
                yaxis_title="Number of Users",
                height=400,
                template="plotly_white",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_users_yoy, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(comparison_df['Month'], comparison_df['Current Year Users'], 'o-', color='#667eea', linewidth=3, markersize=8, label='Current Year Users')
            ax.plot(comparison_df['Month'], comparison_df['Previous Year Users'], 'o--', color='#764ba2', linewidth=3, markersize=8, label='Previous Year Users')
            ax.set_title("👥 User Count Comparison (YoY)", fontsize=16, fontweight='bold')
            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Number of Users", fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
    
    with col2:
        # Revenue Comparison Chart
        if PLOTLY_AVAILABLE:
            fig_revenue_yoy = go.Figure()
            
            fig_revenue_yoy.add_trace(go.Scatter(
                x=comparison_df['Month'],
                y=comparison_df['Current Year Revenue'],
                mode='lines+markers',
                name='Current Year Revenue',
                line=dict(color='#4facfe', width=3),
                marker=dict(size=8, color='#4facfe')
            ))
            
            fig_revenue_yoy.add_trace(go.Scatter(
                x=comparison_df['Month'],
                y=comparison_df['Previous Year Revenue'],
                mode='lines+markers',
                name='Previous Year Revenue',
                line=dict(color='#00f2fe', width=3, dash='dash'),
                marker=dict(size=8, color='#00f2fe')
            ))
            
            fig_revenue_yoy.update_layout(
                title="💰 Revenue Comparison (YoY)",
                xaxis_title="Month",
                yaxis_title="Revenue",
                height=400,
                template="plotly_white",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_revenue_yoy, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(comparison_df['Month'], comparison_df['Current Year Revenue'], 'o-', color='#4facfe', linewidth=3, markersize=8, label='Current Year Revenue')
            ax.plot(comparison_df['Month'], comparison_df['Previous Year Revenue'], 'o--', color='#00f2fe', linewidth=3, markersize=8, label='Previous Year Revenue')
            ax.set_title("💰 Revenue Comparison (YoY)", fontsize=16, fontweight='bold')
            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Revenue", fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
    
    # YoY Growth Rates Chart
    if PLOTLY_AVAILABLE:
        fig_growth_yoy = go.Figure()
        
        fig_growth_yoy.add_trace(go.Scatter(
            x=comparison_df['Month'],
            y=comparison_df['YoY Growth %'],
            mode='lines+markers',
            name='User YoY Growth %',
            line=dict(color='#fa709a', width=3),
            marker=dict(size=8, color='#fa709a')
        ))
        
        fig_growth_yoy.add_trace(go.Scatter(
            x=comparison_df['Month'],
            y=comparison_df['Revenue YoY Growth %'],
            mode='lines+markers',
            name='Revenue YoY Growth %',
            line=dict(color='#fee140', width=3),
            marker=dict(size=8, color='#fee140')
        ))
        
        fig_growth_yoy.update_layout(
            title="📈 Year-over-Year Growth Rates",
            xaxis_title="Month",
            yaxis_title="Growth %",
            height=400,
            template="plotly_white",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_growth_yoy, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(comparison_df['Month'], comparison_df['YoY Growth %'], 'o-', color='#fa709a', linewidth=3, markersize=8, label='User YoY Growth %')
        ax.plot(comparison_df['Month'], comparison_df['Revenue YoY Growth %'], 'o-', color='#fee140', linewidth=3, markersize=8, label='Revenue YoY Growth %')
        ax.set_title("📈 Year-over-Year Growth Rates", fontsize=16, fontweight='bold')
        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Growth %", fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    # YoY Impact Bar Chart
    if PLOTLY_AVAILABLE:
        fig_impact = go.Figure()
        
        # Calculate monthly impact
        monthly_impact = comparison_df['Current Year Users'] - comparison_df['Previous Year Users']
        
        fig_impact.add_trace(go.Bar(
            x=comparison_df['Month'],
            y=monthly_impact,
            name='Monthly User Impact',
            marker_color='#667eea',
            text=monthly_impact,
            textposition='auto'
        ))
        
        fig_impact.update_layout(
            title="📊 Monthly YoY User Impact",
            xaxis_title="Month",
            yaxis_title="Additional Users",
            height=400,
            template="plotly_white",
            showlegend=False
        )
        
        st.plotly_chart(fig_impact, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        monthly_impact = comparison_df['Current Year Users'] - comparison_df['Previous Year Users']
        ax.bar(comparison_df['Month'], monthly_impact, color='#667eea', alpha=0.8)
        ax.set_title("📊 Monthly YoY User Impact", fontsize=16, fontweight='bold')
        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Additional Users", fontsize=12)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

def create_customer_lifecycle_analysis(df_forecast, currency_symbol, currency_name):
    """Create customer lifecycle analysis section"""
    st.markdown("### 🔄 Customer Lifecycle Analysis")
    
    # Calculate lifecycle metrics
    total_new_users = df_forecast['New Users'].sum()
    total_returning_users = df_forecast['Returning Users'].sum()
    total_churned_users = df_forecast['Churned Users'].sum()
    total_rest_period_users = df_forecast['Rest Period Users'].sum()
    total_users = df_forecast['Users'].sum()
    
    # Calculate growth and churn metrics
    monthly_growth_rate = ((df_forecast['New Users'].iloc[-1] / df_forecast['New Users'].iloc[0]) ** (1/11) - 1) * 100 if len(df_forecast) > 1 else 0
    overall_churn_rate = (total_churned_users / total_new_users * 100) if total_new_users > 0 else 0
    retention_rate = (total_returning_users / total_new_users * 100) if total_new_users > 0 else 0
    
    # Lifecycle metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("New Users", f"{total_new_users:,}")
    
    with col2:
        st.metric("Returning Users", f"{total_returning_users:,}")
    
    with col3:
        st.metric("Churned Users", f"{total_churned_users:,}")
    
    with col4:
        st.metric("Retention Rate", f"{retention_rate:.1f}%")
    
    with col5:
        st.metric("Churn Rate", f"{overall_churn_rate:.1f}%")
    
    # Growth and churn analysis
    st.markdown("#### 📈 Growth & Churn Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Monthly Growth Rate", f"{monthly_growth_rate:.1f}%")
    
    with col2:
        st.metric("Rest Period Users", f"{total_rest_period_users:,}")
    
    # View Mode Selector
    st.markdown("#### 📊 Analysis View Options")
    view_mode = st.selectbox(
        "Select Analysis View",
        ["📅 Monthly View", "📆 Yearly View", "📈 Month-on-Month Growth", "🔄 Year-over-Year Comparison"],
        help="Choose how to view the user lifecycle data"
    )
    
    # Display based on selected view mode
    if view_mode == "📅 Monthly View":
        create_monthly_view(df_forecast, currency_symbol, currency_name)
    elif view_mode == "📆 Yearly View":
        create_yearly_view(df_forecast, currency_symbol, currency_name)
    elif view_mode == "📈 Month-on-Month Growth":
        create_mom_growth_view(df_forecast, currency_symbol, currency_name)
    elif view_mode == "🔄 Year-over-Year Comparison":
        create_yoy_comparison_view(df_forecast, currency_symbol, currency_name)
    
    # Lifecycle breakdown chart
    st.markdown("#### 📊 User Lifecycle Breakdown")
    
    lifecycle_data = {
        'User Type': ['New Users', 'Returning Users', 'Churned Users', 'Rest Period Users'],
        'Count': [total_new_users, total_returning_users, total_churned_users, total_rest_period_users]
    }
    
    df_lifecycle = pd.DataFrame(lifecycle_data)
    
    if PLOTLY_AVAILABLE:
        fig = px.pie(df_lifecycle, values='Count', names='User Type', 
                     title="User Lifecycle Distribution",
                     color_discrete_sequence=['#667eea', '#764ba2', '#ef4444', '#f59e0b'])
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ['#667eea', '#764ba2', '#ef4444', '#f59e0b']
        ax.pie(df_lifecycle['Count'], labels=df_lifecycle['User Type'], autopct='%1.1f%%', colors=colors)
        ax.set_title("User Lifecycle Distribution")
        st.pyplot(fig)
    
    # Monthly user trends with growth
    st.markdown("#### 📈 Monthly User Trends & Growth")
    
    monthly_lifecycle = df_forecast.groupby('Month').agg({
        'New Users': 'sum',
        'Returning Users': 'sum',
        'Churned Users': 'sum',
        'Rest Period Users': 'sum',
        'Users': 'sum'
    }).reset_index()
    
    # Calculate month-over-month growth
    monthly_lifecycle['Growth Rate %'] = monthly_lifecycle['New Users'].pct_change() * 100
    monthly_lifecycle['Growth Rate %'] = monthly_lifecycle['Growth Rate %'].fillna(0)
    
    if PLOTLY_AVAILABLE:
        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add user type lines
        fig.add_trace(
            go.Scatter(x=monthly_lifecycle['Month'], y=monthly_lifecycle['New Users'], 
                      name='New Users', line=dict(color='#667eea')),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=monthly_lifecycle['Month'], y=monthly_lifecycle['Returning Users'], 
                      name='Returning Users', line=dict(color='#764ba2')),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=monthly_lifecycle['Month'], y=monthly_lifecycle['Churned Users'], 
                      name='Churned Users', line=dict(color='#ef4444')),
            secondary_y=False,
        )
        
        # Add growth rate line
        fig.add_trace(
            go.Scatter(x=monthly_lifecycle['Month'], y=monthly_lifecycle['Growth Rate %'], 
                      name='Growth Rate %', line=dict(color='#10b981', dash='dash')),
            secondary_y=True,
        )
        
        # Update layout
        fig.update_xaxes(title_text="Month")
        fig.update_yaxes(title_text="Number of Users", secondary_y=False)
        fig.update_yaxes(title_text="Growth Rate %", secondary_y=True)
        fig.update_layout(title_text="Monthly User Trends & Growth Rate", height=500)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Plot user types
        ax1.plot(monthly_lifecycle['Month'], monthly_lifecycle['New Users'], label='New Users', color='#667eea')
        ax1.plot(monthly_lifecycle['Month'], monthly_lifecycle['Returning Users'], label='Returning Users', color='#764ba2')
        ax1.plot(monthly_lifecycle['Month'], monthly_lifecycle['Churned Users'], label='Churned Users', color='#ef4444')
        ax1.set_xlabel("Month")
        ax1.set_ylabel("Number of Users")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add growth rate on secondary y-axis
        ax2 = ax1.twinx()
        ax2.plot(monthly_lifecycle['Month'], monthly_lifecycle['Growth Rate %'], 
                label='Growth Rate %', color='#10b981', linestyle='--')
        ax2.set_ylabel("Growth Rate %")
        ax2.legend(loc='upper right')
        
        plt.title("Monthly User Trends & Growth Rate")
        st.pyplot(fig)
    
    # Churn analysis
    st.markdown("#### ⚠️ Churn Analysis")
    
    churn_analysis_data = {
        'Metric': [
            'Total Churned Users',
            'Average Monthly Churn',
            'Churn Rate (%)',
            'Retention Rate (%)',
            'Net User Growth',
            'Churn Impact on Revenue'
        ],
        'Value': [
            f"{total_churned_users:,}",
            f"{total_churned_users / 12:.0f}",
            f"{overall_churn_rate:.1f}%",
            f"{retention_rate:.1f}%",
            f"{total_new_users - total_churned_users:,}",
            f"{currency_symbol}{(total_churned_users * 5000):,}"  # Assuming average loss per churned user
        ]
    }
    
    df_churn_analysis = pd.DataFrame(churn_analysis_data)
    st.dataframe(df_churn_analysis, use_container_width=True)
    
    # 12-Month User Lifecycle Summary
    st.markdown("#### 📋 12-Month User Lifecycle Summary")
    
    # Get the first duration for the summary
    if not df_forecast.empty:
        first_duration = df_forecast['Duration'].iloc[0]
        lifecycle_summary = create_user_lifecycle_summary(st.session_state.get('config', {}), first_duration)
        st.dataframe(lifecycle_summary, use_container_width=True)
    
    # Comprehensive User Lifecycle Logic Explanation
    st.markdown("#### 🧠 Advanced User Lifecycle Logic Explanation")
    
    with st.expander("🔍 **Detailed User Lifecycle Algorithm**", expanded=True):
        st.markdown("""
        **🎯 Core Concept**: Our user lifecycle model simulates realistic user behavior with organic growth, rest periods, and returning users.
        
        **📊 1. New User Growth Logic (Delta Calculation)**
        ```
        Formula: new_users[m] = total_users[m] - total_users[m-1]
        Growth: total_users[m] = total_users[m-1] × (1 + growth_rate/100)
        
        Example (2% monthly growth):
        Month 1: 1,000 total → 1,000 new users (starting base)
        Month 2: 1,020 total → 20 new users (+2% of 1,000)
        Month 3: 1,040 total → 20 new users (+2% of 1,020)
        Month 4: 1,061 total → 21 new users (+2% of 1,040)
        ```
        
        **🔄 2. Rest Period Logic (Cohort Tracking)**
        ```
        Process:
        1. Users participate for defined duration (e.g., 3 months)
        2. After duration, they enter rest period (e.g., 1 month)
        3. While resting, users are inactive in any committee
        4. Rest period is mandatory between cycles
        
        Example (3M duration + 1M rest):
        Month 1: Cohort 1 starts (1,000 users)
        Month 2: Cohort 1 active (1,000 users)
        Month 3: Cohort 1 active (1,000 users)
        Month 4: Cohort 1 resting (1,000 users) ← Finished cycle
        Month 5: Cohort 1 returns (1,000 users) ← Back to active
        ```
        
        **🔄 3. Returning User Logic (Automatic Return)**
        ```
        Process:
        1. Users automatically return after (duration + rest_period) months
        2. They rejoin as part of active user base
        3. Returning users behave like new participants
        4. Return schedule is tracked in advance
        
        Example (3M committee + 1M rest):
        Month 1: 1,000 new, 0 returning → 1,000 active
        Month 2: 20 new, 0 returning → 20 active
        Month 3: 20 new, 0 returning → 20 active
        Month 4: 21 new, 0 returning → 21 active (1,000 resting)
        Month 5: 21 new, 1,000 returning → 1,021 active
        Month 6: 21 new, 20 returning → 41 active
        ```
        
        **📈 4. User State Tracking**
        ```
        Active Users = New Users + Returning Users
        Rest Period Users = Users who just finished their cycle
        Churned Users = Users who don't return (based on churn rate)
        Total Users to Date = Cumulative user base with growth
        ```
        
        **🎯 5. Key Features**
        - **No Participation Caps**: No TAM limits, all users can participate
        - **Integer Counts**: All user counts are whole numbers (rounded)
        - **Cohort Tracking**: Proper tracking of when each cohort finishes and returns
        - **Return Scheduling**: Dictionary-based scheduling of user returns
        - **Growth Integration**: Growth rate affects both new users and returning user calculations
        """)
    
    # Visual Flow Diagram
    st.markdown("#### 🔄 User Lifecycle Flow Diagram")
    
    if PLOTLY_AVAILABLE:
        # Create a flowchart using Plotly
        fig_flow = go.Figure()
        
        # Add nodes
        nodes = [
            "New Users\n(Delta Growth)",
            "Active Users\n(New + Returning)",
            "Committee\nParticipation",
            "Rest Period\n(Mandatory)",
            "Returning Users\n(Automatic)",
            "Churned Users\n(Exit)"
        ]
        
        x_pos = [0, 1, 2, 3, 4, 5]
        y_pos = [0, 0, 0, 0, 0, 0]
        
        fig_flow.add_trace(go.Scatter(
            x=x_pos,
            y=y_pos,
            mode='markers+text',
            text=nodes,
            textposition="middle center",
            marker=dict(size=100, color=['#667eea', '#f093fb', '#4facfe', '#f59e0b', '#764ba2', '#ef4444']),
            textfont=dict(size=12, color="white"),
            showlegend=False
        ))
        
        # Add arrows
        arrows_x = [0.5, 1.5, 2.5, 3.5, 4.5, 1, 2, 3, 4]
        arrows_y = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        arrows_text = ["→", "→", "→", "→", "→", "↓", "↓", "↓", "↓"]
        
        fig_flow.add_trace(go.Scatter(
            x=arrows_x,
            y=arrows_y,
            mode='markers+text',
            text=arrows_text,
            textposition="middle center",
            marker=dict(size=30, color='black'),
            textfont=dict(size=16, color="white"),
            showlegend=False
        ))
        
        fig_flow.update_layout(
            title="🔄 User Lifecycle Flow",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=200,
            template="plotly_white",
            showlegend=False
        )
        
        st.plotly_chart(fig_flow, use_container_width=True)
    else:
        # Simple text-based flow
        st.markdown("""
        ```
        New Users → Active Users → Committee Participation → Rest Period → Returning Users
            ↓              ↓              ↓              ↓
        Churned Users ← Churned Users ← Churned Users ← Churned Users
        ```
        """)
    
    # Mathematical Formulas
    st.markdown("#### 🧮 Mathematical Formulas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 User Growth Formulas:**
        ```
        total_users[m] = total_users[m-1] × (1 + growth_rate/100)
        new_users[m] = total_users[m] - total_users[m-1]
        active_users[m] = new_users[m] + returning_users[m]
        ```
        """)
    
    with col2:
        st.markdown("""
        **🔄 Lifecycle Formulas:**
        ```
        returning_users[m] = return_schedule[m]
        resting_users[m] = new_users[m-duration] (if m > duration)
        churned_users[m] = new_users[m] × churn_rate/100
        ```
        """)
    
    # Configuration Parameters
    st.markdown("#### ⚙️ Configuration Parameters")
    
    config_params = {
        "Starting Users": "Initial user base (e.g., 1,000)",
        "Monthly Growth Rate": "Month-on-month growth percentage (e.g., 2%)",
        "Rest Period": "Months between cycles (e.g., 1 month)",
        "Returning User Rate": "Percentage who return (e.g., 100%)",
        "Churn Rate": "Percentage who don't return (e.g., 0%)"
    }
    
    for param, description in config_params.items():
        st.markdown(f"**{param}**: {description}")
    
    # Lifecycle explanation
    st.markdown("""
    **💡 Customer Lifecycle Summary:**
    - **New Users**: First-time customers joining ROSCA (delta from previous month's total)
    - **Returning Users**: Customers who completed a cycle and returned after rest period
    - **Churned Users**: Customers who left and didn't return (tracked monthly)
    - **Rest Period Users**: Customers in mandatory rest period between cycles
    - **Active Users**: New Users + Returning Users (currently participating)
    - **Total Users to Date**: Cumulative total user base (with growth)
    - **Growth Rate**: Month-on-month growth in total user base
    - **Churn Rate**: Percentage of users who don't return (monthly churn)
    - **Retention Rate**: Percentage of new users who return after completing their cycle
    """)

def create_market_analysis(market_size, sam_size, som_size, market_growth_rate, df_forecast, currency_symbol, currency_name):
    """Create market analysis section"""
    st.markdown("### 🌍 Market Analysis")
    
    # Market metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("TAM", format_currency(market_size, currency_symbol, currency_name))
    
    with col2:
        st.metric("SAM", format_currency(sam_size, currency_symbol, currency_name))
    
    with col3:
        st.metric("SOM", format_currency(som_size, currency_symbol, currency_name))
    
    with col4:
        st.metric("Growth Rate", f"{market_growth_rate:.1f}%")
    
    # Market penetration
    if not df_forecast.empty:
        total_revenue = df_forecast['Total Revenue'].sum()
        market_penetration = (total_revenue / som_size * 100) if som_size > 0 else 0
        
        st.metric("Market Penetration", f"{market_penetration:.2f}%")
    
    # Market analysis chart
    st.markdown("#### 📊 Market Size Breakdown")
    
    market_data = {
        'Market Segment': ['TAM', 'SAM', 'SOM'],
        'Size': [market_size, sam_size, som_size]
    }
    
    df_market = pd.DataFrame(market_data)
    
    if PLOTLY_AVAILABLE:
        fig = px.bar(df_market, x='Market Segment', y='Size', 
                     title="Market Size Analysis",
                     color='Market Segment',
                     color_discrete_sequence=['#667eea', '#764ba2', '#f59e0b'])
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#667eea', '#764ba2', '#f59e0b']
        ax.bar(df_market['Market Segment'], df_market['Size'], color=colors)
        ax.set_title("Market Size Analysis")
        ax.set_ylabel("Market Size")
        st.pyplot(fig)
    
    # Market opportunity analysis
    st.markdown("#### 💡 Market Opportunity Analysis")
    
    opportunity_data = {
        'Metric': [
            'TAM Opportunity',
            'SAM Opportunity', 
            'SOM Opportunity',
            'Current Revenue',
            'Market Penetration %',
            'Growth Potential'
        ],
        'Value': [
            format_currency(market_size, currency_symbol, currency_name),
            format_currency(sam_size, currency_symbol, currency_name),
            format_currency(som_size, currency_symbol, currency_name),
            format_currency(total_revenue, currency_symbol, currency_name) if not df_forecast.empty else "N/A",
            f"{market_penetration:.2f}%" if not df_forecast.empty else "N/A",
            f"{market_growth_rate:.1f}%"
        ]
    }
    
    df_opportunity = pd.DataFrame(opportunity_data)
    st.dataframe(df_opportunity, use_container_width=True)
def create_risk_analysis(df_forecast):
    """Create risk analysis"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    risk_data = {
        'Risk Metric': [
            'Default Rate (%)',
            'Pre-Payout Default %',
            'Post-Payout Default %',
            'Recovery Rate (%)',
            'Penalty Rate (%)',
            'Total Risk Exposure',
            'Risk-Adjusted Profit'
        ],
        'Value': [
            (df_forecast['Total Default Loss'].sum() / df_forecast['Total Revenue'].sum() * 100) if df_forecast['Total Revenue'].sum() > 0 else 0,
            30.0,  # Placeholder
            70.0,  # Placeholder
            (df_forecast['Default Recovery Amount'].sum() / df_forecast['Total Default Loss'].sum() * 100) if df_forecast['Total Default Loss'].sum() > 0 else 0,
            2.0,  # Placeholder
            df_forecast['Total Default Loss'].sum(),
            df_forecast['Gross Profit'].sum() - df_forecast['Total Default Loss'].sum()
        ]
    }
    
    return pd.DataFrame(risk_data)

# =============================================================================
# 🌍 TAM-SPECIFIC DASHBOARD FUNCTIONS (From add.txt)
# =============================================================================

def create_tam_dashboard_overview(df_forecast, scenario_name, currency_symbol, currency_name):
    """Create TAM-focused dashboard overview"""
    st.markdown(f"""
    <div class="dashboard-header">
        <h1>🌍 {scenario_name} - TAM Distribution System</h1>
        <p>Advanced ROSCA Forecasting with Total Addressable Market Distribution</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key TAM metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_tam_users = df_forecast['Total TAM Users'].iloc[-1] if not df_forecast.empty else 0
        st.metric("Total TAM Users", f"{total_tam_users:,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        # Get unique active users (not sum across months)
        total_active_users = df_forecast['Total Active Users'].iloc[-1] if not df_forecast.empty else 0
        st.metric("Total Active Users", f"{total_active_users:,}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_revenue = df_forecast['Total Revenue'].sum() if not df_forecast.empty else 0
        st.metric("Total Revenue", format_currency(total_revenue, currency_symbol, currency_name))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_profit = df_forecast['Gross Profit'].sum() if not df_forecast.empty else 0
        st.metric("Gross Profit", format_currency(total_profit, currency_symbol, currency_name))
        st.markdown('</div>', unsafe_allow_html=True)

def create_user_lifecycle_analysis_tam(df_forecast, currency_symbol, currency_name):
    """Create comprehensive user lifecycle analysis (TAM version)"""
    st.markdown("### 🔄 User Lifecycle Analysis")
    
    # Calculate lifecycle metrics
    total_new_users = df_forecast['New Users'].sum()
    total_returning_users = df_forecast['Returning Users'].sum()
    total_resting_users = df_forecast['Resting Users'].sum()
    total_active_users = df_forecast['Total Active Users'].iloc[-1] if not df_forecast.empty else 0  # Last month's active users
    total_tam_users = df_forecast['Total TAM Users'].iloc[-1] if not df_forecast.empty else 0
    
    # Lifecycle metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("New Users", f"{total_new_users:,}")
    
    with col2:
        st.metric("Returning Users", f"{total_returning_users:,}")
    
    with col3:
        st.metric("Resting Users", f"{total_resting_users:,}")
    
    with col4:
        st.metric("Active Users", f"{total_active_users:,}")
    
    with col5:
        st.metric("Total TAM", f"{total_tam_users:,}")
    
    # Monthly user trends
    st.markdown("#### 📈 Monthly User Trends")
    
    monthly_summary = df_forecast.groupby('Month').agg({
        'New Users': 'first',
        'Returning Users': 'first',
        'Resting Users': 'first',
        'Total Active Users': 'first',
        'Total TAM Users': 'first'
    }).reset_index()
    
    if PLOTLY_AVAILABLE:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=monthly_summary['Month'],
            y=monthly_summary['New Users'],
            mode='lines+markers',
            name='New Users',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8, color='#667eea')
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_summary['Month'],
            y=monthly_summary['Returning Users'],
            mode='lines+markers',
            name='Returning Users',
            line=dict(color='#764ba2', width=3),
            marker=dict(size=8, color='#764ba2')
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_summary['Month'],
            y=monthly_summary['Total Active Users'],
            mode='lines+markers',
            name='Total Active Users',
            line=dict(color='#f093fb', width=3),
            marker=dict(size=8, color='#f093fb')
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_summary['Month'],
            y=monthly_summary['Total TAM Users'],
            mode='lines+markers',
            name='Total TAM Users',
            line=dict(color='#10b981', width=3),
            marker=dict(size=8, color='#10b981')
        ))
        
        fig.update_layout(
            title="👥 User Lifecycle Trends",
            xaxis_title="Month",
            yaxis_title="Number of Users",
            height=500,
            template="plotly_white",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(monthly_summary['Month'], monthly_summary['New Users'], 'o-', color='#667eea', linewidth=3, markersize=8, label='New Users')
        ax.plot(monthly_summary['Month'], monthly_summary['Returning Users'], 'o-', color='#764ba2', linewidth=3, markersize=8, label='Returning Users')
        ax.plot(monthly_summary['Month'], monthly_summary['Total Active Users'], 'o-', color='#f093fb', linewidth=3, markersize=8, label='Total Active Users')
        ax.plot(monthly_summary['Month'], monthly_summary['Total TAM Users'], 'o-', color='#10b981', linewidth=3, markersize=8, label='Total TAM Users')
        ax.set_title("👥 User Lifecycle Trends", fontsize=16, fontweight='bold')
        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Number of Users", fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

def create_distribution_analysis_tam(df_forecast, currency_symbol, currency_name):
    """Create distribution hierarchy analysis"""
    st.markdown("### 🧩 TAM Distribution Hierarchy Analysis")
    
    # Duration distribution
    st.markdown("#### 📅 Duration Distribution")
    duration_summary = df_forecast.groupby('Duration')['Users in Slot'].sum().reset_index()
    duration_summary['Percentage'] = (duration_summary['Users in Slot'] / duration_summary['Users in Slot'].sum() * 100).round(1)
    
    if PLOTLY_AVAILABLE:
        fig_duration = px.pie(
            duration_summary, 
            values='Users in Slot', 
            names='Duration',
            title="Duration Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_duration, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(duration_summary['Users in Slot'], labels=duration_summary['Duration'], autopct='%1.1f%%')
        ax.set_title("Duration Distribution")
        st.pyplot(fig)
    
    # Slab distribution
    st.markdown("#### 💵 Slab Distribution")
    slab_summary = df_forecast.groupby(['Duration', 'Slab Amount'])['Users in Slot'].sum().reset_index()
    
    if PLOTLY_AVAILABLE:
        fig_slab = px.bar(
            slab_summary,
            x='Duration',
            y='Users in Slot',
            color='Slab Amount',
            title="Slab Distribution by Duration",
            barmode='group'
        )
        st.plotly_chart(fig_slab, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        for duration in slab_summary['Duration'].unique():
            duration_data = slab_summary[slab_summary['Duration'] == duration]
            ax.bar(duration_data['Slab Amount'], duration_data['Users in Slot'], label=f'{duration}M', alpha=0.7)
        ax.set_title("Slab Distribution by Duration")
        ax.set_xlabel("Slab Amount")
        ax.set_ylabel("Users")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

def create_collection_analysis_tam(df_forecast, currency_symbol, currency_name):
    """Create collection and disbursement analysis"""
    st.markdown("### 📅 Collection & Disbursement Analysis")
    
    # Collection metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_days_between = df_forecast['Days Between'].mean()
        st.metric("Avg Collection Period", f"{avg_days_between:.0f} days")
    
    with col2:
        total_deposits = df_forecast['Total Deposits'].sum()
        st.metric("Total Deposits", format_currency(total_deposits, currency_symbol, currency_name))
    
    with col3:
        total_fees = df_forecast['Total Fees'].sum()
        st.metric("Total Fees", format_currency(total_fees, currency_symbol, currency_name))
    
    with col4:
        total_nii = df_forecast['Total NII'].sum()
        st.metric("Total NII", format_currency(total_nii, currency_symbol, currency_name))
    
    # Collection timeline
    st.markdown("#### 📊 Collection Timeline")
    
    collection_timeline = df_forecast.groupby('Month').agg({
        'Collection Date': 'first',
        'Disbursement Date': 'first',
        'Days Between': 'first',
        'Total Deposits': 'sum',
        'Total Fees': 'sum'
    }).reset_index()
    
    if PLOTLY_AVAILABLE:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=collection_timeline['Month'],
            y=collection_timeline['Total Deposits'],
            mode='lines+markers',
            name='Total Deposits',
            line=dict(color='#4facfe', width=3),
            marker=dict(size=8, color='#4facfe')
        ))
        
        fig.add_trace(go.Scatter(
            x=collection_timeline['Month'],
            y=collection_timeline['Total Fees'],
            mode='lines+markers',
            name='Total Fees',
            line=dict(color='#00f2fe', width=3),
            marker=dict(size=8, color='#00f2fe')
        ))
        
        fig.update_layout(
            title="💰 Monthly Collection & Fee Trends",
            xaxis_title="Month",
            yaxis_title="Amount",
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(collection_timeline['Month'], collection_timeline['Total Deposits'], 'o-', color='#4facfe', linewidth=3, markersize=8, label='Total Deposits')
        ax.plot(collection_timeline['Month'], collection_timeline['Total Fees'], 'o-', color='#00f2fe', linewidth=3, markersize=8, label='Total Fees')
        ax.set_title("💰 Monthly Collection & Fee Trends", fontsize=16, fontweight='bold')
        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Amount", fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

def create_financial_dashboard_tam(df_forecast, currency_symbol, currency_name):
    """Create comprehensive financial dashboard"""
    st.markdown("### 💰 Financial Performance Dashboard")
    
    # Financial metrics summary
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_deposits = df_forecast['Total Deposits'].sum()
        st.metric("Total Deposits", format_currency(total_deposits, currency_symbol, currency_name))
    
    with col2:
        total_fees = df_forecast['Total Fees'].sum()
        st.metric("Total Fees", format_currency(total_fees, currency_symbol, currency_name))
    
    with col3:
        total_nii = df_forecast['Total NII'].sum()
        st.metric("Total NII", format_currency(total_nii, currency_symbol, currency_name))
    
    with col4:
        total_revenue = df_forecast['Total Revenue'].sum()
        st.metric("Total Revenue", format_currency(total_revenue, currency_symbol, currency_name))
    
    with col5:
        total_profit = df_forecast['Net Profit'].sum()
        st.metric("Net Profit", format_currency(total_profit, currency_symbol, currency_name))

# =============================================================================
# 🔧 MAIN FORECASTING ENGINE
# =============================================================================

# In the run_forecast function, replace the fee calculation section:

def calculate_user_lifecycle(config, duration):
    """
    Calculate user lifecycle with proper cohort tracking, rest periods, and returning users
    
    Returns:
        dict: Monthly data with new_users, returning_users, resting_users, active_users, total_users
    """
    starting_users = config['starting_users']
    monthly_growth_rate = config['monthly_growth_rate'] / 100
    rest_period_months = config['rest_period_months']
    returning_user_rate = config['returning_user_rate'] / 100
    churn_rate = config['churn_rate'] / 100
    
    # Initialize tracking structures
    total_users_by_month = {}
    new_users_by_month = {}
    returning_users_by_month = {}
    resting_users_by_month = {}
    active_users_by_month = {}
    
    # Cohort tracking: when each cohort will return
    return_schedule = {}
    
    # Month 1: Starting users
    total_users_by_month[1] = starting_users
    new_users_by_month[1] = starting_users
    returning_users_by_month[1] = 0
    resting_users_by_month[1] = 0
    active_users_by_month[1] = starting_users
    
    # Schedule when the first cohort will return
    return_month = 1 + duration + rest_period_months
    return_schedule[return_month] = int(starting_users * returning_user_rate * (1 - churn_rate))
    
    # Calculate months 2-60 (5 years)
    for month in range(2, 61):
        # 1. Calculate total users (with growth)
        total_users_by_month[month] = int(total_users_by_month[month-1] * (1 + monthly_growth_rate))
        
        # 2. Calculate new users (delta from previous month)
        new_users_by_month[month] = total_users_by_month[month] - total_users_by_month[month-1]
        
        # 3. Calculate returning users (from return_schedule)
        returning_users_by_month[month] = return_schedule.get(month, 0)
        
        # 4. Calculate resting users (users who just finished their cycle)
        if month > duration:
            # Users who started (month - duration) months ago are now finishing
            start_month = month - duration
            if start_month >= 1:
                # These users are now resting
                resting_users_by_month[month] = new_users_by_month[start_month]
                
                # Schedule their return
                return_month = month + rest_period_months
                if return_month <= 60:  # Only schedule if within our 60-month (5-year) window
                    return_schedule[return_month] = int(new_users_by_month[start_month] * returning_user_rate * (1 - churn_rate))
        else:
            resting_users_by_month[month] = 0
        
        # 5. Calculate active users
        active_users_by_month[month] = new_users_by_month[month] + returning_users_by_month[month]
    
    return {
        'total_users': total_users_by_month,
        'new_users': new_users_by_month,
        'returning_users': returning_users_by_month,
        'resting_users': resting_users_by_month,
        'active_users': active_users_by_month
    }

def run_forecast(config, fee_collection_mode, currency_symbol, currency_name):
    """Main forecasting engine - complete version with all features"""
    results = []
    
    # Initialize scenario data
    scenario_data = {
        'Month': [],
        'Year': [],
        'Duration': [],
        'Slab Amount': [],
        'Users': [],
        'New Users': [],
        'Returning Users': [],
        'Churned Users': [],
        'Rest Period Users': [],
        'Total Users to Date': [],
        'Pool Size': [],
        'External Capital': [],
        'Total Commitment': [],
        'Collection Date': [],
        'Disbursement Date': [],
        'Days Between': [],
        'Fee %': [],
        'Total Fees Collected': [],
        'Monthly Fee Collection': [],
        'Base NII (Lifetime)': [],
        'Fee NII (Lifetime)': [],
        'Pool Growth NII (Lifetime)': [],
        'Total NII (Lifetime)': [],
        'Pre-Payout Default Loss': [],
        'Post-Payout Default Loss': [],
        'Total Default Loss': [],
        'Default Recovery Amount': [],
        'Net Default Loss (After Recovery)': [],
        'Default Fees Collected': [],
        'Total Defaulters': [],
        'Total Revenue': [],
        'Total Losses': [],
        'Gross Profit': [],
        'Net Profit': [],
        'Party A Share': [],
        'Party B Share': []
    }
    
    # Run forecast for each duration and slab combination
    for duration in config['durations']:
        for slab_amount in config['slab_amounts']:
            # Get slot-specific fees and distribution
            slot_fees = config['slot_fees'].get(duration, {}).get(slab_amount, {})
            slot_distribution = config['slot_distribution'].get(duration, {}).get(slab_amount, {})
            
            # Ensure slot_fees and slot_distribution are not None and are dictionaries
            if slot_fees is None or not isinstance(slot_fees, dict):
                slot_fees = {}
            if slot_distribution is None or not isinstance(slot_distribution, dict):
                slot_distribution = {}
            
            # Basic calculations (needed for fee calculation)
            total_commitment = slab_amount * duration
            
            # Calculate slot-wise fees
            total_fee = 0
            monthly_fee = 0
            
            if fee_collection_mode == "Upfront Fee (Entire Pool)":
                # Calculate upfront fee based on slot distribution
                for slot in range(1, duration + 1):
                    # Check if slot configuration exists and is valid
                    has_slot_fee = slot in slot_fees and slot_fees[slot] is not None
                    has_slot_distribution = slot in slot_distribution and slot_distribution[slot] is not None
                    
                    if has_slot_fee and has_slot_distribution:
                        # Handle both dictionary and float formats for slot_fees
                        if isinstance(slot_fees[slot], dict):
                            slot_fee_pct = slot_fees[slot]['fee_pct']
                        else:
                            slot_fee_pct = slot_fees[slot]
                        
                        slot_distribution_pct = slot_distribution[slot]
                        if slot_distribution_pct > 0:  # Only if slot is not blocked
                            # Upfront: Pay total commitment × fee% × distribution for all slots
                            slot_fee = (total_commitment * (slot_fee_pct / 100) * (slot_distribution_pct / 100))
                            total_fee += slot_fee
                    else:
                        # Fallback: use default fee if slot configuration is missing
                        default_fee_pct = 2.0  # Default 2% fee
                        default_distribution = 100.0 / duration  # Equal distribution
                        slot_fee = (total_commitment * (default_fee_pct / 100) * (default_distribution / 100))
                        total_fee += slot_fee
            else:
                # Calculate monthly fee based on slot distribution
                for slot in range(1, duration + 1):
                    # Check if slot configuration exists and is valid
                    has_slot_fee = slot in slot_fees and slot_fees[slot] is not None
                    has_slot_distribution = slot in slot_distribution and slot_distribution[slot] is not None
                    
                    if has_slot_fee and has_slot_distribution:
                        # Handle both dictionary and float formats for slot_fees
                        if isinstance(slot_fees[slot], dict):
                            slot_fee_pct = slot_fees[slot]['fee_pct']
                        else:
                            slot_fee_pct = slot_fees[slot]
                        
                        slot_distribution_pct = slot_distribution[slot]
                        if slot_distribution_pct > 0:  # Only if slot is not blocked
                            slot_monthly_fee = (slab_amount * (slot_fee_pct / 100) * (slot_distribution_pct / 100))
                            monthly_fee += slot_monthly_fee
                    else:
                        # Fallback: use default fee if slot configuration is missing
                        default_fee_pct = 2.0  # Default 2% fee
                        default_distribution = 100.0 / duration  # Equal distribution
                        slot_monthly_fee = (slab_amount * (default_fee_pct / 100) * (default_distribution / 100))
                        monthly_fee += slot_monthly_fee
                total_fee = monthly_fee * duration
            
            # Default calculations (used for all months)
            pre_payout_default_loss = total_commitment * (config['default_rate'] / 100) * (config['default_pre_pct'] / 100)
            post_payout_default_loss = total_commitment * (config['default_rate'] / 100) * (config['default_post_pct'] / 100)
            total_default_loss = pre_payout_default_loss + post_payout_default_loss
            default_recovery = total_default_loss * (config['recovery_rate'] / 100)
            net_default_loss = total_default_loss - default_recovery
            default_fees = total_default_loss * (config['penalty_pct'] / 100)
            
            # Calculate user lifecycle for this duration (60 months)
            user_lifecycle = calculate_user_lifecycle(config, duration)
            
            # Generate monthly data for 60 months (5 years)
            for month in range(1, 61):
                # Calculate which year this month belongs to (Year 1-5)
                year = ((month - 1) // 12) + 1
                
                # Get user data from lifecycle calculation
                new_users = user_lifecycle['new_users'][month]
                returning_users = user_lifecycle['returning_users'][month]
                resting_users = user_lifecycle['resting_users'][month]
                active_users = user_lifecycle['active_users'][month]
                total_users = user_lifecycle['total_users'][month]
                
                # Calculate churned users (users who left this month)
                churned_users = int(new_users * (config['churn_rate'] / 100))
                
                # Calculate pool size
                pool_size = active_users * slab_amount
                
                # Calculate external capital
                external_capital = pool_size * 0.1  # Placeholder - 10% external capital
                
                # Calculate collection and disbursement dates for this month
                collection_day = config.get('collection_day', 1)
                disbursement_day = config.get('disbursement_day', 15)
                collection_date, disbursement_date, days_between = calculate_collection_dates(
                    month, duration, collection_day, disbursement_day
                )
                
                # Calculate NII using exact days (held_days_exact logic)
                # NII = Principal × Rate × (Days / 365)
                rate = config['kibor_rate'] + config['spread']
                
                # Base NII: on the deposit amount
                base_nii = calculate_nii_with_exact_days(
                    principal=total_commitment,
                    rate=rate,
                    deposit_month=month,
                    payout_month=month + duration,
                    deposit_day=collection_day,
                    payout_day=disbursement_day,
                    start_year=2024
                )
                
                # Fee NII: on the collected fees
                fee_nii = calculate_nii_with_exact_days(
                    principal=total_fee,
                    rate=rate,
                    deposit_month=month,
                    payout_month=month + duration,
                    deposit_day=collection_day,
                    payout_day=disbursement_day,
                    start_year=2024
                )
                
                # Pool Growth NII: on the pool size
                pool_growth_nii = calculate_nii_with_exact_days(
                    principal=total_commitment,
                    rate=rate,
                    deposit_month=month,
                    payout_month=month + duration,
                    deposit_day=collection_day,
                    payout_day=disbursement_day,
                    start_year=2024
                )
                
                total_nii = base_nii + fee_nii + pool_growth_nii
                
                # Revenue calculations (Proper Accounting Logic)
                # Total Revenue = All Income Sources
                # Income Sources: Fees + NII + Default Penalty Fees
                total_revenue = total_fee + total_nii + default_fees
                
                # Gross Profit = Revenue - Direct Costs (Default Losses)
                gross_profit = total_revenue - net_default_loss
                
                # Net Profit = Gross Profit - Operating Expenses
                # (No operating expenses currently, so Net = Gross)
                net_profit = gross_profit
                
                # Total Losses (for reporting)
                total_losses = net_default_loss
                
                # Party A/B split
                party_a_share = net_profit * (config['profit_split'] / 100)
                party_b_share = net_profit * ((100 - config['profit_split']) / 100)
                
                # Add to scenario data
                scenario_data['Month'].append(month)
                scenario_data['Year'].append(year)
                scenario_data['Duration'].append(duration)
                scenario_data['Slab Amount'].append(slab_amount)
                scenario_data['Users'].append(active_users)
                scenario_data['New Users'].append(new_users)
                scenario_data['Returning Users'].append(returning_users)
                scenario_data['Churned Users'].append(churned_users)
                scenario_data['Rest Period Users'].append(resting_users)
                scenario_data['Total Users to Date'].append(total_users)
                scenario_data['Pool Size'].append(pool_size)
                scenario_data['External Capital'].append(external_capital)
                scenario_data['Total Commitment'].append(total_commitment)
                
                scenario_data['Collection Date'].append(collection_date)
                scenario_data['Disbursement Date'].append(disbursement_date)
                scenario_data['Days Between'].append(days_between)
                
                # Calculate average fee percentage - handle both dict and numeric formats
                fee_percentages = []
                for slot in range(1, duration + 1):
                    if slot in slot_fees and slot_fees[slot] is not None:
                        if isinstance(slot_fees[slot], dict):
                            fee_percentages.append(slot_fees[slot].get('fee_pct', 0))
                        else:
                            fee_percentages.append(slot_fees[slot])
                    else:
                        fee_percentages.append(0)
                
                avg_fee_pct = sum(fee_percentages) / duration if duration > 0 else 0
                scenario_data['Fee %'].append(avg_fee_pct)
                scenario_data['Total Fees Collected'].append(total_fee)
                scenario_data['Monthly Fee Collection'].append(monthly_fee)
                scenario_data['Base NII (Lifetime)'].append(base_nii)
                scenario_data['Fee NII (Lifetime)'].append(fee_nii)
                scenario_data['Pool Growth NII (Lifetime)'].append(pool_growth_nii)
                scenario_data['Total NII (Lifetime)'].append(total_nii)
                scenario_data['Pre-Payout Default Loss'].append(pre_payout_default_loss)
                scenario_data['Post-Payout Default Loss'].append(post_payout_default_loss)
                scenario_data['Total Default Loss'].append(total_default_loss)
                scenario_data['Default Recovery Amount'].append(default_recovery)
                scenario_data['Net Default Loss (After Recovery)'].append(net_default_loss)
                scenario_data['Default Fees Collected'].append(default_fees)
                scenario_data['Total Defaulters'].append(int(active_users * config['default_rate'] / 100))
                scenario_data['Total Revenue'].append(total_revenue)
                scenario_data['Total Losses'].append(total_losses)
                scenario_data['Gross Profit'].append(gross_profit)
                scenario_data['Net Profit'].append(net_profit)
                scenario_data['Party A Share'].append(party_a_share)
                scenario_data['Party B Share'].append(party_b_share)
    
    # Convert to DataFrame
    df_forecast = pd.DataFrame(scenario_data)
    
    return df_forecast

def run_tam_forecast(config, fee_collection_mode, currency_symbol, currency_name):
    """Main forecasting engine with TAM-based user distribution"""
    monthly_data = {
        'Month': [],
        'Year': [],
        'New Users': [],
        'Returning Users': [],
        'Resting Users': [],
        'Total Active Users': [],
        'Total TAM Users': [],
        'Duration': [],
        'Slab Amount': [],
        'Slot': [],
        'Users in Slot': [],
        'Collection Date': [],
        'Disbursement Date': [],
        'Days Between': [],
        'Monthly Deposit': [],
        'Total Deposits': [],
        'Fee %': [],
        'Total Fees': [],
        'Monthly Fee': [],
        'Base NII': [],
        'Fee NII': [],
        'Pool Growth NII': [],
        'Total NII': [],
        'Pre-Payout Default Loss': [],
        'Post-Payout Default Loss': [],
        'Total Default Loss': [],
        'Default Recovery': [],
        'Net Default Loss': [],
        'Default Fees': [],
        'Total Defaulters': [],
        'Total Revenue': [],
        'Total Losses': [],
        'Gross Profit': [],
        'Net Profit': [],
        'Party A Share': [],
        'Party B Share': []
    }
    
    # Extract configuration
    initial_tam = config['initial_tam']
    monthly_growth_rate = config['monthly_growth_rate']
    durations = config['durations']
    duration_share = config['duration_share']
    slab_share = config['slab_share']
    slot_share = config['slot_share']
    rest_periods = config['rest_periods']
    slot_fees = config['slot_fees']
    slot_distribution = config['slot_distribution']
    
    # Financial parameters
    kibor_rate = config['kibor_rate']
    spread = config['spread']
    default_rate = config['default_rate']
    default_pre_pct = config['default_pre_pct']
    default_post_pct = config['default_post_pct']
    penalty_pct = config['penalty_pct']
    recovery_rate = config['recovery_rate']
    profit_split = config['profit_split']
    
    # Track total TAM users
    total_tam_users = initial_tam
    user_history = {}
    
    # Run simulation for 60 months (5 years)
    for month in range(1, 61):
        # Calculate which year this month belongs to (Year 1-5)
        year = ((month - 1) // 12) + 1
        
        # Step 1: Calculate new users
        if month == 1:
            new_users = initial_tam
        else:
            new_users = calculate_new_users_tam(total_tam_users, monthly_growth_rate)
        
        # Update total TAM users
        total_tam_users += new_users
        
        # Step 2: Determine returning users
        returning_users = determine_returning_users_tam(month, user_history, durations, rest_periods)
        
        # Step 3: Calculate total active users
        total_active_users = new_users + returning_users
        
        # Step 4: Calculate resting users
        resting_users = 0
        for join_month, user_data in user_history.items():
            for duration, user_count in user_data.items():
                completion_month = join_month + duration
                if completion_month == month:
                    resting_users += user_count
        
        # Step 5: Distribute users using 3-level hierarchy
        users_by_duration = allocate_users_by_duration(total_active_users, duration_share)
        users_by_slab = allocate_users_by_slab(users_by_duration, slab_share)
        users_by_slot = allocate_users_by_slot(users_by_slab, slot_share)
        
        # Step 6: Process each duration/slab/slot combination
        for duration in durations:
            if duration not in users_by_duration:
                continue
                
            for slab_amount in slab_share.get(duration, {}).keys():
                if slab_amount not in users_by_slab.get(duration, {}):
                    continue
                    
                for slot in slot_share.get(duration, {}).keys():
                    if slot not in users_by_slot.get(duration, {}).get(slab_amount, {}):
                        continue
                    
                    users_in_slot = users_by_slot[duration][slab_amount][slot]
                    
                    if users_in_slot == 0:
                        continue
                    
                    # Calculate collection and disbursement dates
                    collection_date, disbursement_date, days_between = calculate_collection_dates(
                        month, duration, config.get('collection_day', 1), config.get('disbursement_day', 15)
                    )
                    
                    # Calculate financial metrics
                    monthly_deposit = slab_amount
                    total_deposits = users_in_slot * monthly_deposit
                    
                    # Fee calculations
                    if duration in slot_fees and slot in slot_fees[duration]:
                        if isinstance(slot_fees[duration][slot], dict):
                            fee_pct = slot_fees[duration][slot]['fee_pct']
                        else:
                            fee_pct = slot_fees[duration][slot]
                    else:
                        fee_pct = 2.0
                    
                    if fee_collection_mode == "Upfront Fee (Entire Pool)":
                        total_fees = total_deposits * duration * (fee_pct / 100)
                        monthly_fee = total_fees / duration
                    else:
                        monthly_fee = total_deposits * (fee_pct / 100)
                        total_fees = monthly_fee * duration
                    
                    # NII calculations using exact days (held_days_exact logic)
                    # Get the configured days from config
                    deposit_day = config.get('collection_day', 1)
                    payout_day = config.get('disbursement_day', 15)
                    
                    # Get days using exact calculation
                    days_for_nii = held_days_exact(
                        deposit_month_index=month,
                        payout_month_index=month + duration,
                        start_year=2024,
                        start_month=1,
                        deposit_day=deposit_day,
                        payout_day=payout_day
                    )
                    
                    # NII = Principal × Rate × (Days / 365)
                    rate = kibor_rate + spread
                    
                    base_nii = total_deposits * (rate / 100) * (days_for_nii / 365)
                    fee_nii = total_fees * (rate / 100) * (days_for_nii / 365)
                    pool_growth_nii = total_deposits * (rate / 100) * (days_for_nii / 365)
                    total_nii = base_nii + fee_nii + pool_growth_nii
                    
                    # Default calculations
                    pre_payout_default_loss = total_deposits * (default_rate / 100) * (default_pre_pct / 100)
                    post_payout_default_loss = total_deposits * (default_rate / 100) * (default_post_pct / 100)
                    total_default_loss = pre_payout_default_loss + post_payout_default_loss
                    default_recovery = total_default_loss * (recovery_rate / 100)
                    net_default_loss = total_default_loss - default_recovery
                    default_fees = total_default_loss * (penalty_pct / 100)
                    
                    # Revenue calculations (Proper Accounting Logic)
                    # Total Revenue = All Income Sources
                    total_revenue = total_fees + total_nii + default_fees
                    
                    # Gross Profit = Revenue - Direct Costs (Default Losses)
                    gross_profit = total_revenue - net_default_loss
                    
                    # Net Profit = Gross Profit (no operating expenses)
                    net_profit = gross_profit
                    
                    # Total Losses (for reporting)
                    total_losses = net_default_loss
                    
                    # Party A/B split
                    party_a_share = net_profit * (profit_split / 100)
                    party_b_share = net_profit * ((100 - profit_split) / 100)
                    
                    # Store results
                    monthly_data['Month'].append(month)
                    monthly_data['Year'].append(year)
                    monthly_data['New Users'].append(new_users)
                    monthly_data['Returning Users'].append(returning_users)
                    monthly_data['Resting Users'].append(resting_users)
                    monthly_data['Total Active Users'].append(total_active_users)
                    monthly_data['Total TAM Users'].append(total_tam_users)
                    monthly_data['Duration'].append(duration)
                    monthly_data['Slab Amount'].append(slab_amount)
                    monthly_data['Slot'].append(slot)
                    monthly_data['Users in Slot'].append(users_in_slot)
                    monthly_data['Collection Date'].append(collection_date)
                    monthly_data['Disbursement Date'].append(disbursement_date)
                    monthly_data['Days Between'].append(days_between)
                    monthly_data['Monthly Deposit'].append(monthly_deposit)
                    monthly_data['Total Deposits'].append(total_deposits)
                    monthly_data['Fee %'].append(fee_pct)
                    monthly_data['Total Fees'].append(total_fees)
                    monthly_data['Monthly Fee'].append(monthly_fee)
                    monthly_data['Base NII'].append(base_nii)
                    monthly_data['Fee NII'].append(fee_nii)
                    monthly_data['Pool Growth NII'].append(pool_growth_nii)
                    monthly_data['Total NII'].append(total_nii)
                    monthly_data['Pre-Payout Default Loss'].append(pre_payout_default_loss)
                    monthly_data['Post-Payout Default Loss'].append(post_payout_default_loss)
                    monthly_data['Total Default Loss'].append(total_default_loss)
                    monthly_data['Default Recovery'].append(default_recovery)
                    monthly_data['Net Default Loss'].append(net_default_loss)
                    monthly_data['Default Fees'].append(default_fees)
                    monthly_data['Total Defaulters'].append(int(users_in_slot * default_rate / 100))
                    monthly_data['Total Revenue'].append(total_revenue)
                    monthly_data['Total Losses'].append(total_losses)
                    monthly_data['Gross Profit'].append(gross_profit)
                    monthly_data['Net Profit'].append(net_profit)
                    monthly_data['Party A Share'].append(party_a_share)
                    monthly_data['Party B Share'].append(party_b_share)
        
        # Step 7: Update user history
        if month == 1:
            user_history[month] = {}
            for duration in durations:
                if duration in users_by_duration:
                    user_history[month][duration] = users_by_duration[duration]
        else:
            if new_users > 0:
                user_history[month] = {}
                for duration in durations:
                    if duration in users_by_duration:
                        user_history[month][duration] = users_by_duration[duration]
    
    # Convert to DataFrame
    df_forecast = pd.DataFrame(monthly_data)
    
    return df_forecast

def run_scenario_analysis(config, fee_collection_mode, currency_symbol, currency_name):
    """Run scenario analysis"""
    scenarios = {}
    
    # Base case scenario
    scenarios['Base Case'] = run_forecast(config, fee_collection_mode, currency_symbol, currency_name)
    
    # Optimistic scenario
    optimistic_config = config.copy()
    optimistic_config['default_rate'] = config['default_rate'] * 0.5
    optimistic_config['kibor_rate'] = config['kibor_rate'] * 1.1
    scenarios['Optimistic'] = run_forecast(optimistic_config, fee_collection_mode, currency_symbol, currency_name)
    
    # Pessimistic scenario
    pessimistic_config = config.copy()
    pessimistic_config['default_rate'] = config['default_rate'] * 2.0
    pessimistic_config['kibor_rate'] = config['kibor_rate'] * 0.9
    scenarios['Pessimistic'] = run_forecast(pessimistic_config, fee_collection_mode, currency_symbol, currency_name)
    
    return scenarios

def validate_configuration(config):
    """Validate configuration parameters"""
    errors = []
    
    # Check durations
    if not config['durations']:
        errors.append("No durations selected")
    
    # Check slab amounts
    if not config['slab_amounts']:
        errors.append("No slab amounts selected")
    
    # Check slot distribution
    for duration in config['durations']:
        for slab_amount in config['slab_amounts']:
            if duration in config['slot_distribution'] and slab_amount in config['slot_distribution'][duration]:
                total_distribution = sum(config['slot_distribution'][duration][slab_amount].values())
                if abs(total_distribution - 100.0) > 0.1:
                    errors.append(f"Slot distribution for {duration}M, {slab_amount}K is {total_distribution:.1f}% (should be 100%)")
    
    # Check financial parameters
    if config['kibor_rate'] < 0 or config['kibor_rate'] > 50:
        errors.append("KIBOR rate should be between 0% and 50%")
    
    if config['spread'] < 0 or config['spread'] > 20:
        errors.append("Spread should be between 0% and 20%")
    
    if config['default_rate'] < 0 or config['default_rate'] > 50:
        errors.append("Default rate should be between 0% and 50%")
    
    if config['profit_split'] < 0 or config['profit_split'] > 100:
        errors.append("Profit split should be between 0% and 100%")
    
    return errors

def create_configuration_summary(config, fee_collection_mode, currency_symbol, currency_name):
    """Create configuration summary"""
    summary = {
        'Parameter': [
            'Currency',
            'Fee Collection Mode',
            'KIBOR Rate (%)',
            'Spread (%)',
            'Default Rate (%)',
            'Profit Split - Party A (%)',
            'Durations (months)',
            'Slab Amounts',
            'Total Combinations'
        ],
        'Value': [
            f"{currency_name} ({currency_symbol})",
            fee_collection_mode,
            f"{config['kibor_rate']:.1f}%",
            f"{config['spread']:.1f}%",
            f"{config['default_rate']:.1f}%",
            f"{config['profit_split']:.1f}%",
            ', '.join(map(str, config['durations'])),
            ', '.join([f"{currency_symbol}{amount:,}" for amount in config['slab_amounts']]),
            len(config['durations']) * len(config['slab_amounts'])
        ]
    }
    
    return pd.DataFrame(summary)

def create_export_data(df_forecast, df_monthly_summary, df_yearly_summary, df_profit_share, 
                      df_deposit_log, df_default_log, df_lifecycle_log, scenario_name):
    """Create export data for Excel"""
    export_data = {
        'Forecast': df_forecast,
        'Monthly Summary': df_monthly_summary,
        'Yearly Summary': df_yearly_summary,
        'Profit Share': df_profit_share,
        'Deposit Log': df_deposit_log,
        'Default Log': df_default_log,
        'Lifecycle Log': df_lifecycle_log
    }
    
    return export_data

def create_analytics_dashboard(df_forecast, config, fee_collection_mode, currency_symbol, currency_name):
    """Create analytics dashboard"""
    st.markdown("### 📊 Analytics Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", f"{df_forecast['Users'].sum():,}")
    
    with col2:
        st.metric("Total Revenue", format_currency(df_forecast['Total Revenue'].sum(), currency_symbol, currency_name))
    
    with col3:
        st.metric("Gross Profit", format_currency(df_forecast['Gross Profit'].sum(), currency_symbol, currency_name))
    
    with col4:
        profit_margin = (df_forecast['Gross Profit'].sum() / df_forecast['Total Revenue'].sum() * 100) if df_forecast['Total Revenue'].sum() > 0 else 0
        st.metric("Profit Margin", f"{profit_margin:.1f}%")
    
    # Charts
    st.markdown("#### 📈 Key Charts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly pools chart
        fig_pools = create_monthly_pools_chart(df_forecast, currency_symbol, currency_name)
        if PLOTLY_AVAILABLE:
            st.plotly_chart(fig_pools, use_container_width=True)
        else:
            st.pyplot(fig_pools)
    
    with col2:
        # Users vs profit chart
        fig_users = create_users_vs_profit_chart(df_forecast, currency_symbol, currency_name)
        if PLOTLY_AVAILABLE:
            st.plotly_chart(fig_users, use_container_width=True)
        else:
            st.pyplot(fig_users)
    
    # Additional charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Annual pools chart
        fig_annual_pools = create_annual_pools_chart(df_forecast, currency_symbol, currency_name)
        if PLOTLY_AVAILABLE:
            st.plotly_chart(fig_annual_pools, use_container_width=True)
        else:
            st.pyplot(fig_annual_pools)
    
    with col2:
        # Annual users chart
        fig_annual_users = create_annual_users_chart(df_forecast, currency_symbol, currency_name)
        if PLOTLY_AVAILABLE:
            st.plotly_chart(fig_annual_users, use_container_width=True)
        else:
            st.pyplot(fig_annual_users)
    
    # External capital chart
    fig_external = create_external_capital_chart(df_forecast, currency_symbol, currency_name)
    if PLOTLY_AVAILABLE:
        st.plotly_chart(fig_external, use_container_width=True)
    else:
        st.pyplot(fig_external)

def create_yoy_dashboard(df_forecast, config, currency_symbol, currency_name):
    """Create comprehensive Year-on-Year dashboard"""
    st.markdown("## 📅 Year-on-Year Dashboard")
    
    if df_forecast.empty:
        st.warning("No forecast data available. Please run a forecast first.")
        return
    
    # Create YoY comparison data
    yoy_data = create_yoy_comparison_data(df_forecast, config)
    
    # Key YoY Metrics
    st.markdown("### 📊 Key Year-on-Year Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_yoy_growth = yoy_data['User YoY Growth %'].mean()
        st.metric("Avg User YoY Growth", f"{total_yoy_growth:.1f}%")
    
    with col2:
        total_revenue_yoy = yoy_data['Revenue YoY Growth %'].mean()
        st.metric("Avg Revenue YoY Growth", f"{total_revenue_yoy:.1f}%")
    
    with col3:
        best_yoy_month = yoy_data.loc[yoy_data['User YoY Growth %'].idxmax(), 'Month']
        best_yoy_rate = yoy_data['User YoY Growth %'].max()
        st.metric("Best YoY Month", f"{best_yoy_month}")
    
    with col4:
        total_yoy_impact = yoy_data['Current Year Users'].sum() - yoy_data['Previous Year Users'].sum()
        st.metric("Total YoY Impact", f"{total_yoy_impact:,} users")
    
    # YoY Comparison Charts
    st.markdown("### 📈 Year-on-Year Comparison Charts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # User Count Comparison
        if PLOTLY_AVAILABLE:
            fig_users = go.Figure()
            
            fig_users.add_trace(go.Scatter(
                x=yoy_data['Month'],
                y=yoy_data['Current Year Users'],
                mode='lines+markers',
                name='Current Year Users',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8, color='#667eea')
            ))
            
            fig_users.add_trace(go.Scatter(
                x=yoy_data['Month'],
                y=yoy_data['Previous Year Users'],
                mode='lines+markers',
                name='Previous Year Users',
                line=dict(color='#764ba2', width=3, dash='dash'),
                marker=dict(size=8, color='#764ba2')
            ))
            
            fig_users.update_layout(
                title="👥 User Count Comparison (YoY)",
                xaxis_title="Month",
                yaxis_title="Number of Users",
                height=400,
                template="plotly_white",
                showlegend=True
            )
            
            st.plotly_chart(fig_users, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(yoy_data['Month'], yoy_data['Current Year Users'], 'o-', color='#667eea', linewidth=3, markersize=8, label='Current Year Users')
            ax.plot(yoy_data['Month'], yoy_data['Previous Year Users'], 'o--', color='#764ba2', linewidth=3, markersize=8, label='Previous Year Users')
            ax.set_title("👥 User Count Comparison (YoY)", fontsize=16, fontweight='bold')
            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Number of Users", fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
    
    with col2:
        # Revenue Comparison
        if PLOTLY_AVAILABLE:
            fig_revenue = go.Figure()
            
            fig_revenue.add_trace(go.Scatter(
                x=yoy_data['Month'],
                y=yoy_data['Current Year Revenue'],
                mode='lines+markers',
                name='Current Year Revenue',
                line=dict(color='#4facfe', width=3),
                marker=dict(size=8, color='#4facfe')
            ))
            
            fig_revenue.add_trace(go.Scatter(
                x=yoy_data['Month'],
                y=yoy_data['Previous Year Revenue'],
                mode='lines+markers',
                name='Previous Year Revenue',
                line=dict(color='#00f2fe', width=3, dash='dash'),
                marker=dict(size=8, color='#00f2fe')
            ))
            
            fig_revenue.update_layout(
                title="💰 Revenue Comparison (YoY)",
                xaxis_title="Month",
                yaxis_title="Revenue",
                height=400,
                template="plotly_white",
                showlegend=True
            )
            
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(yoy_data['Month'], yoy_data['Current Year Revenue'], 'o-', color='#4facfe', linewidth=3, markersize=8, label='Current Year Revenue')
            ax.plot(yoy_data['Month'], yoy_data['Previous Year Revenue'], 'o--', color='#00f2fe', linewidth=3, markersize=8, label='Previous Year Revenue')
            ax.set_title("💰 Revenue Comparison (YoY)", fontsize=16, fontweight='bold')
            ax.set_xlabel("Month", fontsize=12)
            ax.set_ylabel("Revenue", fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
    
    # YoY Growth Rates
    if PLOTLY_AVAILABLE:
        fig_growth = go.Figure()
        
        fig_growth.add_trace(go.Scatter(
            x=yoy_data['Month'],
            y=yoy_data['User YoY Growth %'],
            mode='lines+markers',
            name='User YoY Growth %',
            line=dict(color='#fa709a', width=3),
            marker=dict(size=8, color='#fa709a')
        ))
        
        fig_growth.add_trace(go.Scatter(
            x=yoy_data['Month'],
            y=yoy_data['Revenue YoY Growth %'],
            mode='lines+markers',
            name='Revenue YoY Growth %',
            line=dict(color='#fee140', width=3),
            marker=dict(size=8, color='#fee140')
        ))
        
        fig_growth.update_layout(
            title="📈 Year-over-Year Growth Rates",
            xaxis_title="Month",
            yaxis_title="Growth %",
            height=400,
            template="plotly_white",
            showlegend=True
        )
        
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(yoy_data['Month'], yoy_data['User YoY Growth %'], 'o-', color='#fa709a', linewidth=3, markersize=8, label='User YoY Growth %')
        ax.plot(yoy_data['Month'], yoy_data['Revenue YoY Growth %'], 'o-', color='#fee140', linewidth=3, markersize=8, label='Revenue YoY Growth %')
        ax.set_title("📈 Year-over-Year Growth Rates", fontsize=16, fontweight='bold')
        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Growth %", fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    # YoY Impact Analysis
    st.markdown("### 📊 YoY Impact Analysis")
    
    monthly_impact = yoy_data['Current Year Users'] - yoy_data['Previous Year Users']
    yoy_data['Monthly Impact'] = monthly_impact
    
    if PLOTLY_AVAILABLE:
        fig_impact = go.Figure()
        
        fig_impact.add_trace(go.Bar(
            x=yoy_data['Month'],
            y=monthly_impact,
            name='Monthly User Impact',
            marker_color='#667eea',
            text=monthly_impact,
            textposition='auto'
        ))
        
        fig_impact.update_layout(
            title="📊 Monthly YoY User Impact",
            xaxis_title="Month",
            yaxis_title="Additional Users",
            height=400,
            template="plotly_white",
            showlegend=False
        )
        
        st.plotly_chart(fig_impact, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(yoy_data['Month'], monthly_impact, color='#667eea', alpha=0.8)
        ax.set_title("📊 Monthly YoY User Impact", fontsize=16, fontweight='bold')
        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Additional Users", fontsize=12)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    # YoY Summary Table
    st.markdown("### 📋 YoY Summary Table")
    st.dataframe(yoy_data, use_container_width=True)
    
    # YoY Insights
    st.markdown("### 💡 YoY Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📈 Growth Patterns:**")
        if total_yoy_growth > 0:
            st.success(f"✅ Positive YoY growth: {total_yoy_growth:.1f}%")
        else:
            st.warning(f"⚠️ Negative YoY growth: {total_yoy_growth:.1f}%")
        
        st.markdown(f"**🏆 Best Performing Month:** {best_yoy_month}")
        st.markdown(f"**📊 Total YoY Impact:** {total_yoy_impact:,} additional users")
    
    with col2:
        st.markdown("**💰 Revenue Insights:**")
        if total_revenue_yoy > 0:
            st.success(f"✅ Revenue growing YoY: {total_revenue_yoy:.1f}%")
        else:
            st.warning(f"⚠️ Revenue declining YoY: {total_revenue_yoy:.1f}%")
        
        st.markdown("**📅 Analysis Period:** 12 months")
        st.markdown("**🔄 Comparison:** Current vs Previous Year")

def create_yoy_comparison_data(df_forecast, config):
    """Create YoY comparison data"""
    # Group by month
    monthly_data = df_forecast.groupby('Month').agg({
        'Users': 'sum',
        'Total Revenue': 'sum',
        'Gross Profit': 'sum',
        'New Users': 'sum',
        'Returning Users': 'sum'
    }).reset_index()
    
    # Create comparison data (simulated previous year)
    comparison_data = []
    for _, row in monthly_data.iterrows():
        month = row['Month']
        current_users = row['Users']
        current_revenue = row['Total Revenue']
        
        # Simulate previous year data (85% of current year for 15% growth)
        prev_year_multiplier = 0.85
        prev_users = int(current_users * prev_year_multiplier)
        prev_revenue = current_revenue * prev_year_multiplier
        
        # Calculate YoY growth
        user_yoy_growth = ((current_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
        revenue_yoy_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        comparison_data.append({
            'Month': f"Month {month}",
            'Current Year Users': current_users,
            'Previous Year Users': prev_users,
            'User YoY Growth %': user_yoy_growth,
            'Current Year Revenue': current_revenue,
            'Previous Year Revenue': prev_revenue,
            'Revenue YoY Growth %': revenue_yoy_growth
        })
    
    return pd.DataFrame(comparison_data)

# =============================================================================
# 🧩 MODULAR USER GROWTH SYSTEM
# =============================================================================

def generate_user_growth(initial_users, growth_rate, months=12):
    """
    Generate month-on-month user growth
    
    Args:
        initial_users: Starting number of users in Month 1
        growth_rate: Monthly growth rate as percentage (e.g., 20 for 20%)
        months: Number of months to simulate
    
    Returns:
        dict: Monthly user data with new_users, total_users
    """
    new_users_by_month = {}
    total_users_by_month = {}
    
    # Month 1: Initial users
    new_users_by_month[1] = initial_users
    total_users_by_month[1] = initial_users
    
    # Months 2+: Calculate growth
    for month in range(2, months + 1):
        # New users = previous month total * growth rate
        new_users = int(total_users_by_month[month - 1] * (growth_rate / 100))
        new_users_by_month[month] = new_users
        
        # Total users = previous total + new users
        total_users_by_month[month] = total_users_by_month[month - 1] + new_users
    
    return {
        'new_users': new_users_by_month,
        'total_users': total_users_by_month
    }

def simulate_resting_and_returning_users(user_growth_data, durations, rest_periods, months=12):
    """
    Simulate resting and returning users based on duration and rest periods
    
    Args:
        user_growth_data: Output from generate_user_growth()
        durations: List of durations (e.g., [3, 6, 10])
        rest_periods: Dict of rest periods per duration (e.g., {3: 1, 6: 2, 10: 2})
        months: Number of months to simulate
    
    Returns:
        dict: Monthly data with returning_users, resting_users, active_users
    """
    returning_users_by_month = {}
    resting_users_by_month = {}
    active_users_by_month = {}
    
    # Initialize all months
    for month in range(1, months + 1):
        returning_users_by_month[month] = 0
        resting_users_by_month[month] = 0
        active_users_by_month[month] = 0
    
    # Track cohorts for each duration
    for duration in durations:
        rest_period = rest_periods.get(duration, 1)
        
        # Track when each cohort starts and when they return
        for start_month in range(1, months + 1):
            # Calculate when this cohort finishes and returns
            finish_month = start_month + duration
            return_month = finish_month + rest_period
            
            # If return month is within our simulation period
            if return_month <= months:
                # Get the number of users who started in this month
                if start_month == 1:
                    cohort_size = user_growth_data['new_users'][1]
                else:
                    cohort_size = user_growth_data['new_users'][start_month]
                
                # Add to returning users in return month
                returning_users_by_month[return_month] += cohort_size
                
                # Add to resting users in finish month
                if finish_month <= months:
                    resting_users_by_month[finish_month] += cohort_size
    
    # Calculate active users (new + returning)
    for month in range(1, months + 1):
        new_users = user_growth_data['new_users'][month]
        returning_users = returning_users_by_month[month]
        active_users_by_month[month] = new_users + returning_users
    
    return {
        'returning_users': returning_users_by_month,
        'resting_users': resting_users_by_month,
        'active_users': active_users_by_month
    }

def allocate_users_to_slabs(active_users_data, slab_configs, months=12):
    """
    Allocate users to different contribution slabs
    
    Args:
        active_users_data: Output from simulate_resting_and_returning_users()
        slab_configs: Dict of slab allocations per duration
                     e.g., {3: {1000: 30, 2000: 30, 5000: 40}, 6: {...}}
        months: Number of months to simulate
    
    Returns:
        dict: Monthly slab allocation data
    """
    slab_allocation_by_month = {}
    
    for month in range(1, months + 1):
        month_data = {}
        total_active = active_users_data['active_users'][month]
        
        for duration, slab_allocation in slab_configs.items():
            duration_data = {}
            
            # Calculate users for each slab
            total_allocated = 0
            for slab_amount, percentage in slab_allocation.items():
                users_in_slab = int(total_active * (percentage / 100))
                duration_data[slab_amount] = users_in_slab
                total_allocated += users_in_slab
            
            # Rounding correction to ensure total equals total_active
            if total_allocated != total_active:
                # Find the largest slab and adjust
                largest_slab = max(slab_allocation.keys())
                correction = total_active - total_allocated
                duration_data[largest_slab] += correction
            
            month_data[duration] = duration_data
        
        slab_allocation_by_month[month] = month_data
    
    return slab_allocation_by_month

def allocate_users_to_slots(slab_allocation_data, slot_configs, months=12):
    """
    Allocate users to slots within each duration and slab
    
    Args:
        slab_allocation_data: Output from allocate_users_to_slabs()
        slot_configs: Dict of slot configurations per duration
                     e.g., {3: {1: {'fee_pct': 5, 'blocked': False}, 2: {...}}}
        months: Number of months to simulate
    
    Returns:
        dict: Monthly slot allocation data
    """
    slot_allocation_by_month = {}
    
    for month in range(1, months + 1):
        month_data = {}
        
        for duration, slab_data in slab_allocation_data[month].items():
            duration_data = {}
            
            for slab_amount, users_in_slab in slab_data.items():
                slab_data_slots = {}
                
                # Get slot configuration for this duration
                slot_config = slot_configs.get(duration, {})
                
                # Find available (non-blocked) slots
                available_slots = [slot for slot, config in slot_config.items() 
                                 if not config.get('blocked', False)]
                
                if available_slots and users_in_slab > 0:
                    # Distribute users equally among available slots
                    users_per_slot = int(users_in_slab / len(available_slots))
                    remaining_users = users_in_slab % len(available_slots)
                    
                    for i, slot in enumerate(available_slots):
                        users_in_slot = users_per_slot
                        if i < remaining_users:  # Distribute remaining users
                            users_in_slot += 1
                        
                        slab_data_slots[slot] = {
                            'users': users_in_slot,
                            'fee_pct': slot_config[slot].get('fee_pct', 2.0),
                            'blocked': slot_config[slot].get('blocked', False)
                        }
                
                duration_data[slab_amount] = slab_data_slots
            
            month_data[duration] = duration_data
        
        slot_allocation_by_month[month] = month_data
    
    return slot_allocation_by_month

def calculate_monthly_metrics(user_growth_data, user_lifecycle_data, slab_allocation_data, 
                            slot_allocation_data, slab_amounts, months=12):
    """
    Calculate comprehensive monthly metrics
    
    Args:
        user_growth_data: Output from generate_user_growth()
        user_lifecycle_data: Output from simulate_resting_and_returning_users()
        slab_allocation_data: Output from allocate_users_to_slabs()
        slot_allocation_data: Output from allocate_users_to_slots()
        slab_amounts: List of slab amounts
        months: Number of months to simulate
    
    Returns:
        pd.DataFrame: Monthly metrics
    """
    monthly_metrics = []
    
    for month in range(1, months + 1):
        # User metrics
        new_users = user_growth_data['new_users'][month]
        returning_users = user_lifecycle_data['returning_users'][month]
        resting_users = user_lifecycle_data['resting_users'][month]
        total_active = user_lifecycle_data['active_users'][month]
        
        # Financial metrics
        total_deposits = 0
        total_fees = 0
        
        # Calculate deposits and fees for each duration and slab
        for duration, slab_data in slab_allocation_data[month].items():
            for slab_amount, users_in_slab in slab_data.items():
                # Calculate deposits
                monthly_deposits = users_in_slab * slab_amount
                total_deposits += monthly_deposits
                
                # Calculate fees for each slot
                slot_data = slot_allocation_data[month][duration][slab_amount]
                for slot, slot_info in slot_data.items():
                    if not slot_info['blocked']:
                        users_in_slot = slot_info['users']
                        fee_pct = slot_info['fee_pct']
                        slot_fees = users_in_slot * slab_amount * (fee_pct / 100)
                        total_fees += slot_fees
        
        monthly_metrics.append({
            'Month': month,
            'New Users': new_users,
            'Returning Users': returning_users,
            'Resting Users': resting_users,
            'Total Active Users': total_active,
            'Total Deposits': total_deposits,
            'Total Fees': total_fees
        })
    
    return pd.DataFrame(monthly_metrics)

def create_advanced_user_growth_ui():
    """Create advanced user growth configuration UI"""
    st.markdown("### 🧩 Advanced User Growth Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Growth Parameters")
        initial_users = st.number_input("Initial Users", min_value=100, value=1000, step=100, 
                                      help="Starting number of users in Month 1")
        growth_rate = st.number_input("Monthly Growth Rate (%)", min_value=0.0, max_value=100.0, 
                                    value=20.0, step=0.1, help="Month-on-month growth rate")
        simulation_months = st.number_input("Simulation Months", min_value=1, max_value=60, 
                                          value=12, step=1, help="Number of months to simulate")
    
    with col2:
        st.markdown("#### 🔄 Duration & Rest Configuration")
        durations = st.multiselect("Durations (months)", [3, 6, 9, 12, 18, 24], default=[3, 6, 12])
        
        rest_periods = {}
        for duration in durations:
            rest_periods[duration] = st.number_input(
                f"Rest Period for {duration}M", 
                min_value=0, max_value=12, value=1, step=1,
                key=f"rest_{duration}"
            )
    
    # Slab Configuration
    st.markdown("#### 💵 Slab Configuration")
    slab_configs = {}
    
    for duration in durations:
        with st.expander(f"📅 {duration}M Duration Slab Allocation"):
            st.markdown(f"**Configure slab allocation for {duration}-month duration**")
            
            # Default slab amounts
            default_slabs = [1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000]
            selected_slabs = st.multiselect(
                f"Select Slabs for {duration}M", 
                default_slabs, 
                default=default_slabs[:4],
                key=f"slabs_{duration}"
            )
            
            if selected_slabs:
                slab_allocation = {}
                total_percentage = 0
                
                for slab in selected_slabs:
                    percentage = st.number_input(
                        f"Allocation % for {slab:,}", 
                        min_value=0.0, max_value=100.0, 
                        value=100.0/len(selected_slabs), step=0.1,
                        key=f"slab_{duration}_{slab}"
                    )
                    slab_allocation[slab] = percentage
                    total_percentage += percentage
                
                # Validation
                if abs(total_percentage - 100.0) > 0.1:
                    st.warning(f"⚠️ Total allocation is {total_percentage:.1f}% (should be 100%)")
                else:
                    st.success(f"✅ Total allocation: {total_percentage:.1f}%")
                
                slab_configs[duration] = slab_allocation
    
    # Slot Configuration
    st.markdown("#### 🎯 Slot Configuration")
    slot_configs = {}
    
    for duration in durations:
        with st.expander(f"🎯 {duration}M Duration Slot Configuration"):
            st.markdown(f"**Configure slots for {duration}-month duration**")
            
            slot_config = {}
            for slot in range(1, duration + 1):
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    fee_pct = st.number_input(
                        f"Fee % for Slot {slot}", 
                        min_value=0.0, max_value=20.0, 
                        value=2.0, step=0.1,
                        key=f"fee_{duration}_{slot}"
                    )
                
                with col2:
                    blocked = st.checkbox(
                        f"Block Slot {slot}", 
                        key=f"block_{duration}_{slot}"
                    )
                
                with col3:
                    if not blocked:
                        st.info(f"Slot {slot}: {fee_pct}% fee")
                    else:
                        st.warning(f"Slot {slot}: Blocked")
                
                slot_config[slot] = {
                    'fee_pct': fee_pct,
                    'blocked': blocked
                }
            
            slot_configs[duration] = slot_config
    
    return {
        'initial_users': initial_users,
        'growth_rate': growth_rate,
        'simulation_months': simulation_months,
        'durations': durations,
        'rest_periods': rest_periods,
        'slab_configs': slab_configs,
        'slot_configs': slot_configs
    }

# =============================================================================
# 🎯 MAIN APPLICATION
# =============================================================================

# Main header
st.markdown("""
<div class="dashboard-header">
    <h1>💰 ROSCA Forecast Pro</h1>
    <p>Advanced Rotating Savings and Credit Association Forecasting & Analytics</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    # Currency selection
    selected_currency = st.selectbox("💱 Currency", list(CURRENCY_OPTIONS.keys()))
    CURRENCY_SYMBOL = CURRENCY_OPTIONS[selected_currency]["symbol"]
    CURRENCY_NAME = CURRENCY_OPTIONS[selected_currency]["name"]
    
    # Financial parameters
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 💰 Financial Parameters")
    kibor_rate = st.number_input("KIBOR Rate (%)", min_value=0.0, max_value=50.0, value=22.0, step=0.1)
    spread = st.number_input("Spread (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    profit_split = st.number_input("Profit Split - Party A (%)", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Default parameters
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### ⚠️ Default Parameters")
    default_rate = st.number_input("Default Rate (%)", min_value=0.0, max_value=50.0, value=5.0, step=0.1)
    default_pre_pct = st.number_input("Pre-Payout Default %", min_value=0.0, max_value=100.0, value=30.0, step=1.0)
    default_post_pct = st.number_input("Post-Payout Default %", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
    penalty_pct = st.number_input("Penalty Rate (%)", min_value=0.0, max_value=50.0, value=2.0, step=0.1)
    recovery_rate = st.number_input("Recovery Rate (%)", min_value=0.0, max_value=100.0, value=50.0, step=1.0)
    st.markdown('</div>', unsafe_allow_html=True)
    # Add this after the Default Parameters section in the sidebar:

    # Market & TAM Configuration
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 🌍 Market & TAM Configuration")
    market_size = st.number_input("Total Addressable Market (TAM)", min_value=0, value=1000000, step=10000, help="Total market size in your currency")
    sam_size = st.number_input("Serviceable Addressable Market (SAM)", min_value=0, value=500000, step=10000, help="Addressable market size")
    som_size = st.number_input("Serviceable Obtainable Market (SOM)", min_value=0, value=50000, step=1000, help="Realistic market capture")
    market_growth_rate = st.number_input("Market Growth Rate (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.1, help="Annual market growth rate")
    yoy_growth_rate = st.number_input("Year-over-Year Growth Rate (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.1, help="YoY growth rate for 5-year projections")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Customer Lifecycle Configuration
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 🔄 Customer Lifecycle")
    starting_users = st.number_input("Starting Users", min_value=100, value=1000, step=100, help="Initial number of users in month 1")
    monthly_growth_rate = st.number_input("Monthly Growth Rate (%)", min_value=0.0, max_value=50.0, value=2.0, step=0.1, help="Month-on-month growth rate for total user base")
    rest_period_months = st.number_input("Rest Period (months)", min_value=0, max_value=24, value=1, step=1, help="Months users rest between ROSCA cycles")
    returning_user_rate = st.number_input("Returning User Rate (%)", min_value=0.0, max_value=100.0, value=100.0, step=1.0, help="Percentage of users who return after rest period")
    churn_rate = st.number_input("Churn Rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, help="Percentage of users who don't return (set to 0 for automatic return)")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Fee collection mode
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 💳 Fee Collection")
    fee_collection_mode = st.selectbox(
        "Fee Collection Method",
        ["Upfront Fee (Entire Pool)", "Monthly Fee Collection"]
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Collection & Disbursement Configuration
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 📅 Collection & Disbursement Schedule")
    collection_day = st.number_input("Collection Day", min_value=1, max_value=28, value=1, step=1, help="Day of month to collect deposits")
    disbursement_day = st.number_input("Disbursement Day", min_value=1, max_value=28, value=15, step=1, help="Day of month to disburse funds")
    st.markdown('</div>', unsafe_allow_html=True)

    # Scenario configuration
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 📊 Scenario")
    scenario_name = st.text_input("Scenario Name", value="Base Case")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Duration configuration
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 📅 Duration Configuration")
    durations = st.multiselect(
        "Select Durations (months)",
        [3, 4, 5, 6, 8, 9, 10, 12, 18, 24, 36],
        default=[6, 12, 24]
    )
    
    if not durations:
        st.error("Please select at least one duration")
        st.stop()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Slab configuration
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 💵 Slab Configuration")
    slab_amounts = st.multiselect(
        "Select Slab Amounts",
        [1000, 2000, 3000, 5000, 10000, 15000, 20000, 25000, 30000, 50000],
        default=[2000, 3000, 5000]
    )
    
    if not slab_amounts:
        st.error("Please select at least one slab amount")
        st.stop()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Forecasting Engine Selection
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 🚀 Forecasting Engine")
    forecasting_engine = st.radio(
        "Forecast Mode",
        ["🧩 Standard Forecast", "🌍 TAM Distribution"],
        help="Standard: Advanced lifecycle tracking. TAM: 3-level hierarchy (Duration→Slab→Slot)"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Slot configuration - BEAUTIFUL UI RESTORED
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 🎯 Slot Configuration")
    
    # Configuration mode selection
    config_mode = st.radio(
        "Configuration Mode",
        ["⚡ Quick Setup", "📋 Compact View", "🔧 Detailed View"],
        help="Choose how to configure slots"
    )
    
    slot_fees = {}
    slot_distribution = {}
    
    for duration in durations:
        with st.expander(f"📅 Duration: {duration} months", expanded=True):
            for slab in slab_amounts:
                st.markdown(f"**💰 Slab: {CURRENCY_SYMBOL}{slab:,}**")
                
                if config_mode == "⚡ Quick Setup":
                    # Quick setup - simple interface
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fee_pct = st.number_input(
                            f"Fee % for all slots",
                            min_value=0.0,
                            max_value=20.0,
                            value=2.0,
                            step=0.1,
                            key=f"quick_fee_{duration}_{slab}"
                        )
                    
                    with col2:
                        blocked_slots = st.multiselect(
                            f"Block slots",
                            list(range(1, duration + 1)),
                            key=f"quick_block_{duration}_{slab}"
                        )
                    
                    # Create configuration
                    if duration not in slot_fees:
                        slot_fees[duration] = {}
                    if duration not in slot_distribution:
                        slot_distribution[duration] = {}
                    
                    slot_fees[duration][slab] = fee_pct
                    
                    # Distribute remaining slots equally
                    remaining_slots = duration - len(blocked_slots)
                    if remaining_slots > 0:
                        equal_distribution = 100.0 / remaining_slots
                    else:
                        equal_distribution = 0
                    
                    slot_distribution[duration][slab] = {}
                    for slot in range(1, duration + 1):
                        if slot in blocked_slots:
                            slot_distribution[duration][slab][slot] = 0
                        else:
                            slot_distribution[duration][slab][slot] = equal_distribution
                
                elif config_mode == "📋 Compact View":
                    # Compact view - data editor
                    slot_data = []
                    for slot in range(1, duration + 1):
                        slot_data.append({
                            "Slot": slot,
                            "Fee %": 2.0,
                            "Blocked": False,
                            "Distribution %": 100.0 / duration
                        })
                    
                    df_slots = pd.DataFrame(slot_data)
                    
                    edited_df = st.data_editor(
                        df_slots,
                        num_rows="fixed",
                        use_container_width=True,
                        key=f"compact_{duration}_{slab}"
                    )
                    
                    # Convert back to configuration
                    if duration not in slot_fees:
                        slot_fees[duration] = {}
                    if duration not in slot_distribution:
                        slot_distribution[duration] = {}
                    
                    slot_fees[duration][slab] = edited_df['Fee %'].iloc[0]  # Use first row's fee
                    slot_distribution[duration][slab] = {}
                    
                    for _, row in edited_df.iterrows():
                        slot = int(row["Slot"])
                        if row["Blocked"]:
                            slot_distribution[duration][slab][slot] = 0
                        else:
                            slot_distribution[duration][slab][slot] = row["Distribution %"]

                else:  # Detailed View
                    # Detailed view - individual slot configuration
                    st.markdown(f"**🔧 Detailed Configuration for {duration}M, {CURRENCY_SYMBOL}{slab:,}**")
                    
                    # Fee configuration for each slot
                    st.markdown("**💰 Slot-wise Fee Configuration:**")
                    
                    total_distribution = 0
                    slot_configs = {}
                    
                    for slot in range(1, duration + 1):
                        st.markdown(f"**Slot {slot}:**")
                        col1, col2, col3 = st.columns([2, 1, 2])
                        
                        with col1:
                            fee_pct = st.number_input(
                                f"Fee %",
                                min_value=0.0,
                                max_value=20.0,
                                value=2.0,
                                step=0.1,
                                key=f"fee_{duration}_{slab}_{slot}"
                            )
                        
                        with col2:
                            blocked = st.checkbox(
                                f"Block",
                                key=f"block_{duration}_{slab}_{slot}",
                                help=f"Block Slot {slot}"
                            )
                        
                        with col3:
                            if not blocked:
                                distribution = st.number_input(
                                    f"Distribution %",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=100.0 / duration,
                                    step=0.1,
                                    key=f"dist_{duration}_{slab}_{slot}"
                                )
                                total_distribution += distribution
                            else:
                                distribution = 0
                                st.info("🚫 Blocked")
                        
                        # Store slot configuration
                        slot_configs[slot] = {
                            'fee_pct': fee_pct,
                            'blocked': blocked,
                            'distribution': distribution
                        }
                    
                    # Validation
                    if abs(total_distribution - 100.0) > 0.1:
                        st.warning(f"⚠️ Total distribution is {total_distribution:.1f}% (should be 100%)")
                    
                    # Store configuration
                    if duration not in slot_fees:
                        slot_fees[duration] = {}
                    if duration not in slot_distribution:
                        slot_distribution[duration] = {}
                    
                    slot_fees[duration][slab] = {slot: config['fee_pct'] for slot, config in slot_configs.items()}
                    slot_distribution[duration][slab] = {slot: config['distribution'] for slot, config in slot_configs.items()}
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main content
st.markdown("## 📊 Forecast Results")
st.info("📅 **5-Year Projection**: This forecast runs for 60 months with Month-on-Month growth and Year-on-Year analysis. Select 'Monthly Pool & Slab Stats' view to see detailed monthly breakdowns by Pool, Slab, and Slot.")

# Create configuration
config = {
    'kibor_rate': kibor_rate,
    'spread': spread,
    'profit_split': profit_split,
    'default_rate': default_rate,
    'default_pre_pct': default_pre_pct,
    'default_post_pct': default_post_pct,
    'penalty_pct': penalty_pct,
    'recovery_rate': recovery_rate,
    'durations': durations,
    'slab_amounts': slab_amounts,
    'slot_fees': slot_fees,
    'slot_distribution': slot_distribution,
    'starting_users': starting_users,
    'monthly_growth_rate': monthly_growth_rate,
    'rest_period_months': rest_period_months,
    'returning_user_rate': returning_user_rate,
    'churn_rate': churn_rate,
    'collection_day': collection_day,
    'disbursement_day': disbursement_day
}

# View mode selection
view_mode = st.selectbox(
    "Select View Mode",
    ["📊 Dashboard View", "🔧 Detailed Forecast", "📈 Analytics View", "⚙️ Configuration Mode"]
)

# Run forecast
if st.button("🚀 Run Forecast", type="primary"):
    with st.spinner("Running forecast..."):
        # Validate configuration
        errors = validate_configuration(config)
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
            st.stop()
        
        # Run forecast based on selected engine
        if forecasting_engine == "🌍 TAM Distribution":
            # Prepare config for TAM forecasting
            # Note: TAM mode requires specific config format
            if 'initial_tam' not in config:
                config['initial_tam'] = starting_users
            if 'duration_share' not in config:
                # Create equal distribution for durations
                config['duration_share'] = {d: 100.0/len(durations) for d in durations}
            if 'slab_share' not in config:
                # Create equal distribution for slabs
                config['slab_share'] = {}
                for d in durations:
                    config['slab_share'][d] = {s: 100.0/len(slab_amounts) for s in slab_amounts}
            if 'slot_share' not in config:
                # Create equal distribution for slots
                config['slot_share'] = {}
                for d in durations:
                    config['slot_share'][d] = {s: 100.0/d for s in range(1, d+1)}
            if 'rest_periods' not in config:
                config['rest_periods'] = {d: 1 for d in durations}
            
            df_forecast = run_tam_forecast(config, fee_collection_mode, CURRENCY_SYMBOL, CURRENCY_NAME)
        else:
            df_forecast = run_forecast(config, fee_collection_mode, CURRENCY_SYMBOL, CURRENCY_NAME)
        
        if not df_forecast.empty:
            st.success("✅ Forecast completed successfully!")
            
            # Create summaries
            df_monthly_summary = create_monthly_summary(df_forecast)
            df_yearly_summary = create_yearly_summary(df_monthly_summary)
            df_profit_share = create_profit_share_analysis_simple(df_yearly_summary, profit_split)
            
            # Create detailed logs
            df_deposit_log = create_deposit_log(df_forecast)
            df_default_log = create_default_log(df_forecast)
            df_lifecycle_log = create_lifecycle_log(df_forecast)
            
            # Store in session state
            st.session_state['df_forecast'] = df_forecast
            st.session_state['df_monthly_summary'] = df_monthly_summary
            st.session_state['df_yearly_summary'] = df_yearly_summary
            st.session_state['df_profit_share'] = df_profit_share
            st.session_state['df_deposit_log'] = df_deposit_log
            st.session_state['df_default_log'] = df_default_log
            st.session_state['df_lifecycle_log'] = df_lifecycle_log
            st.session_state['config'] = config
            st.session_state['fee_collection_mode'] = fee_collection_mode
            st.session_state['scenario_name'] = scenario_name
            st.session_state['forecasting_engine'] = forecasting_engine
            
            # Store market data in session state
            st.session_state['market_size'] = market_size
            st.session_state['sam_size'] = sam_size
            st.session_state['som_size'] = som_size
            st.session_state['market_growth_rate'] = market_growth_rate
            st.session_state['yoy_growth_rate'] = yoy_growth_rate
            
        else:
            st.error("❌ No forecast data generated")
            st.error("💡 **Troubleshooting Tips:**")
            st.error("1. Check that you have selected durations and slabs")
            st.error("2. Ensure slot distribution totals 100% for each slab")
            st.error("3. Verify that not all slots are blocked")
            st.error("4. Try using 'Configuration Mode' for easier setup")

# Display results based on view mode
if 'df_forecast' in st.session_state and not st.session_state['df_forecast'].empty:
    df_forecast = st.session_state['df_forecast']
    df_monthly_summary = st.session_state['df_monthly_summary']
    df_yearly_summary = st.session_state['df_yearly_summary']
    df_profit_share = st.session_state['df_profit_share']
    df_deposit_log = st.session_state['df_deposit_log']
    df_default_log = st.session_state['df_default_log']
    df_lifecycle_log = st.session_state['df_lifecycle_log']
    config = st.session_state['config']
    fee_collection_mode = st.session_state['fee_collection_mode']
    scenario_name = st.session_state['scenario_name']
    forecasting_engine = st.session_state.get('forecasting_engine', '🧩 Standard Forecast')
    
    if view_mode == "📊 Dashboard View":
        # Show TAM dashboard if TAM mode is selected
        if forecasting_engine == "🌍 TAM Distribution":
            create_tam_dashboard_overview(df_forecast, scenario_name, CURRENCY_SYMBOL, CURRENCY_NAME)
            create_user_lifecycle_analysis_tam(df_forecast, CURRENCY_SYMBOL, CURRENCY_NAME)
            create_distribution_analysis_tam(df_forecast, CURRENCY_SYMBOL, CURRENCY_NAME)
            create_collection_analysis_tam(df_forecast, CURRENCY_SYMBOL, CURRENCY_NAME)
            create_financial_dashboard_tam(df_forecast, CURRENCY_SYMBOL, CURRENCY_NAME)
            st.stop()
        
        # Otherwise show standard dashboard
        # Dashboard overview
        create_dashboard_overview(df_monthly_summary, scenario_name, CURRENCY_SYMBOL, CURRENCY_NAME)
        
        # === Year-on-Year Visual Summary ===
        st.markdown("### 📊 5-Year Financial Overview")
        
        # Add summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Total 5-Year Revenue", 
                     format_currency(df_forecast['Total Revenue'].sum(), CURRENCY_SYMBOL, CURRENCY_NAME),
                     help="Cumulative revenue across all 5 years")
        with col2:
            st.metric("📈 Total 5-Year Profit", 
                     format_currency(df_forecast['Gross Profit'].sum(), CURRENCY_SYMBOL, CURRENCY_NAME),
                     help="Cumulative gross profit across all 5 years")
        with col3:
            total_users_end = df_forecast['Users'].iloc[-1] if not df_forecast.empty else 0
            st.metric("👥 Users at Year 5", f"{int(total_users_end):,}")
        with col4:
            avg_profit_margin = (df_forecast['Gross Profit'].sum() / df_forecast['Total Revenue'].sum() * 100) if df_forecast['Total Revenue'].sum() > 0 else 0
            st.metric("💰 Avg Profit Margin", f"{avg_profit_margin:.1f}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("**📝 Note**: Users shown are at END of each year. Revenue and Profit are cumulative for that year across all durations, slabs, and slots.")
        
        # Aggregate by Year - need to be careful with revenue aggregation
        # Sum revenue across all month/duration/slab combinations for each year
        yearly_agg_dict = {'Total Revenue': 'sum', 'Gross Profit': 'sum'}
        if 'Total Fees Collected' in df_forecast.columns:
            yearly_agg_dict['Total Fees Collected'] = 'sum'
        
        if 'Total NII (Lifetime)' in df_forecast.columns:
            yearly_agg_dict['Total NII (Lifetime)'] = 'sum'
        
        # Get users at END of each year (last month of year)
        yearly_stats = df_forecast.groupby('Year').agg(yearly_agg_dict).reset_index()
        
        # Debug: Show what we're aggregating
        # st.write(f"Debug: Found {len(yearly_stats)} years in data")
        # st.write(f"Debug: Years = {yearly_stats['Year'].tolist()}")
        
        # Add all user type columns - users at END of each year
        for user_col in ['Users', 'New Users', 'Returning Users', 'Rest Period Users', 'Total Users to Date']:
            if user_col in df_forecast.columns:
                yearly_stats[user_col] = 0
                for idx, row in yearly_stats.iterrows():
                    year = row['Year']
                    year_data = df_forecast[df_forecast['Year'] == year]
                    if not year_data.empty:
                        # Get the last month for this year
                        last_month = year_data['Month'].max()
                        # Get all rows for the last month
                        last_month_data = year_data[year_data['Month'] == last_month]
                        # Sum users across all combinations in the last month
                        total_users = last_month_data[user_col].sum()
                        yearly_stats.at[idx, user_col] = total_users
        
        # Calculate profit split for two parties
        profit_split_pct = config.get('profit_split', 70.0)  # Default 70% if not found
        yearly_stats['Party A Share'] = yearly_stats['Gross Profit'] * (profit_split_pct / 100)
        yearly_stats['Party B Share'] = yearly_stats['Gross Profit'] * ((100 - profit_split_pct) / 100)
        
        # Format for display
        yearly_stats['Year'] = yearly_stats['Year'].apply(lambda x: f"Year {x}")
        
        # Helper function to format with commas - defined OUTSIDE the loop
        def format_with_comma(x):
            if pd.isna(x):
                return '0'
            elif isinstance(x, (int, float)):
                return f"{int(x):,}"
            elif isinstance(x, str) and x == 'N/A':
                return x
            else:
                return str(x)
        
        # Format user columns with comma separation
        for user_col in ['Users', 'New Users', 'Returning Users', 'Rest Period Users', 'Total Users to Date']:
            if user_col in yearly_stats.columns:
                yearly_stats[user_col] = yearly_stats[user_col].apply(format_with_comma)
        
        # Format financial columns
        yearly_stats['Total Revenue'] = yearly_stats['Total Revenue'].apply(lambda x: f"{int(x):,}")
        yearly_stats['Gross Profit'] = yearly_stats['Gross Profit'].apply(lambda x: f"{int(x):,}")
        yearly_stats['Party A Share'] = yearly_stats['Party A Share'].apply(lambda x: f"{int(x):,}")
        yearly_stats['Party B Share'] = yearly_stats['Party B Share'].apply(lambda x: f"{int(x):,}")
        
        # Display in fancy, trendy modern cards
        st.markdown("<br>", unsafe_allow_html=True)
        
        for idx, row in yearly_stats.iterrows():
            year = row['Year']
            
            # Get all user metrics - already formatted with commas
            active_users = row.get('Users', 0)
            new_users = row.get('New Users', 'N/A')
            returning_users = row.get('Returning Users', 'N/A')
            resting_users = row.get('Rest Period Users', 'N/A')
            total_users = row.get('Total Users to Date', 'N/A')
            
            # Get financial metrics - already formatted with commas
            revenue = row['Total Revenue']
            profit = row['Gross Profit']
            party_a = row['Party A Share']
            party_b = row['Party B Share']
            
            # Create a modern card with gradient - easypaisa theme (lightened)
            html_content = f"""<div style="background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%); padding: 2rem; border-radius: 20px; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1); border: 2px solid #00D084;">
<h2 style="color: #00D084; margin: 0 0 1rem 0; text-align: center; font-size: 2rem; font-weight: bold;">{year}</h2>
<h3 style="color: #00D084; margin: 1rem 0 0.5rem 0; font-size: 1.1rem; text-align: center;"> &#x1F465; USER METRICS</h3>
<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.8rem; margin-bottom: 1.5rem;">
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F7E2; ACTIVE</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">{active_users}</div>
</div>
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F195; NEW</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">{new_users}</div>
</div>
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F504; RETURNING</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">{returning_users}</div>
</div>
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F634; RESTING</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">{resting_users}</div>
</div>
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F465; TOTAL SERVICED</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">{total_users}</div>
</div>
</div>
<h3 style="color: #00D084; margin: 1rem 0 0.5rem 0; font-size: 1.1rem; text-align: center;"> &#x1F4B0; FINANCIAL METRICS</h3>
<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.8rem;">
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F4B0; REVENUE</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">Rs {revenue}</div>
</div>
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F4C8; PROFIT</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">Rs {profit}</div>
</div>
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F91D; PARTY A</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">Rs {party_a}</div>
</div>
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F91D; PARTY B</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">Rs {party_b}</div>
</div>
<div style="background: rgba(0, 208, 132, 0.08); padding: 0.8rem; border-radius: 10px; border: 1px solid rgba(0, 208, 132, 0.3);">
<div style="color: #00D084; font-size: 0.75rem; margin-bottom: 0.3rem; opacity: 0.9;"> &#x1F4CA; PROFIT%</div>
<div style="color: #1a1a1a; font-size: 1.1rem; font-weight: bold;">N/A</div>
</div>
</div>
</div>"""
            st.markdown(html_content, unsafe_allow_html=True)
        
        # Collection & Disbursement Timeline (if available)
        if 'Collection Date' in df_forecast.columns and 'Disbursement Date' in df_forecast.columns:
            st.markdown("### 📅 Collection & Disbursement Timeline")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_days = df_forecast['Days Between'].mean() if 'Days Between' in df_forecast.columns else 0
                st.metric("Avg Days Between Collection & Disbursement", f"{avg_days:.1f} days")
            
            with col2:
                total_deposits = df_forecast['Total Deposits'].sum() if 'Total Deposits' in df_forecast.columns else 0
                st.metric("Total Deposits Expected", format_currency(total_deposits, CURRENCY_SYMBOL, CURRENCY_NAME))
            
            with col3:
                st.metric("Collection Day", f"Day {collection_day}")
            
            with col4:
                st.metric("Disbursement Day", f"Day {disbursement_day}")
            
            # Show timeline table
            timeline_cols = ['Month', 'Collection Date', 'Disbursement Date', 'Days Between', 'Total Deposits']
            available_cols = [col for col in timeline_cols if col in df_forecast.columns]
            
            if available_cols and 'Month' in available_cols:
                # Group by Month, get first row for each month (to avoid duplicates)
                # Exclude 'Month' from the selection since it's used for grouping
                cols_to_select = [col for col in available_cols if col != 'Month']
                if cols_to_select:
                    timeline_df = df_forecast.groupby('Month')[cols_to_select].first().reset_index()
                    
                    # Format Month column first
                    timeline_df['Month'] = timeline_df['Month'].apply(lambda x: f"Month {x+1}")
                    
                    # Remove actual dates and show abstract references instead
                    if 'Collection Date' in timeline_df.columns:
                        timeline_df['Collection Date'] = timeline_df['Month'].str.replace('Month ', 'Collection Period ')
                    if 'Disbursement Date' in timeline_df.columns:
                        timeline_df['Disbursement Date'] = timeline_df['Month'].str.replace('Month ', 'Disbursement Period ')
                    
                    # Format amounts with commas
                    if 'Days Between' in timeline_df.columns:
                        timeline_df['Days Between'] = timeline_df['Days Between'].apply(lambda x: f"{float(x):.1f} days")
                    if 'Total Deposits' in timeline_df.columns:
                        timeline_df['Total Deposits'] = timeline_df['Total Deposits'].apply(lambda x: format_currency(x, CURRENCY_SYMBOL, CURRENCY_NAME))
                    
                    st.dataframe(timeline_df, use_container_width=True)
            
            # NII Impact Explanation
            st.info(f"""
            **💰 NII Calculation Impact**: 
            - **Collection Day**: Day {collection_day} of each month (when deposits are collected)
            - **Disbursement Day**: Day {disbursement_day} of each month (when funds are disbursed)
            - **Formula**: NII = Principal × Rate × (Days Between / 365)
            - **Your Configuration**: {avg_days:.1f} days average holding period
            - The more days between collection and disbursement, the higher the NII!
            """)
        
        # Fee Collection Mode Analysis
        st.subheader("💳 Fee Collection Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if fee_collection_mode == "Upfront Fee (Entire Pool)":
                st.success("**✅ UPFRONT FEE MODE ACTIVE**")
                st.markdown("**How it works:**")
                st.markdown("- Customer pays entire fee when joining")
                st.markdown("- Fee = Total Commitment × Fee %")
                st.markdown("- Example: 6M, 5K/month, 2% fee = 600 fee upfront")
            else:
                st.info("**📅 MONTHLY FEE MODE ACTIVE**")
                st.markdown("**How it works:**")
                st.markdown("- Customer pays fee monthly with installments")
                st.markdown("- Monthly Fee = (Total Commitment × Fee %) ÷ Duration")
                st.markdown("- Example: 6M, 5K/month, 2% fee = 100/month")
        
        with col2:
            st.markdown("**💡 Business Impact:**")
            if fee_collection_mode == "Upfront Fee (Entire Pool)":
                st.markdown("**✅ Benefits:**")
                st.markdown("- Immediate cash flow")
                st.markdown("- No collection risk")
                st.markdown("- Better liquidity")
                st.markdown("**⚠️ Challenges:**")
                st.markdown("- Higher barrier to entry")
                st.markdown("- May reduce customer acquisition")
            else:
                st.markdown("**✅ Benefits:**")
                st.markdown("- Lower barrier to entry")
                st.markdown("- Better customer experience")
                st.markdown("- Higher acquisition potential")
                st.markdown("**⚠️ Challenges:**")
                st.markdown("- Delayed fee collection")
                st.markdown("- Collection risk")
        
        # NII Analysis
        create_nii_analysis(df_forecast, CURRENCY_SYMBOL, CURRENCY_NAME)
        
        # Revenue & Profit Analysis
        create_revenue_profit_analysis(df_forecast, CURRENCY_SYMBOL, CURRENCY_NAME)
        
        # Profit Share Analysis - FIXED VERSION
        create_profit_share_analysis(df_forecast, profit_split, CURRENCY_SYMBOL, CURRENCY_NAME)
        
        # Default Impact Analysis
        create_default_impact_analysis(df_forecast, CURRENCY_SYMBOL, CURRENCY_NAME)
        
        # Customer Lifecycle Analysis
        create_customer_lifecycle_analysis(df_forecast, CURRENCY_SYMBOL, CURRENCY_NAME)
        
        # === NEW: Monthly Pool & Slab Stats ===
        st.markdown("---")
        st.markdown("### 🗓️ Monthly Pool, Slab & Slot Breakdown")
        
        # Year selector
        selected_year = st.selectbox("Filter by Year", ["All Years", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"], key="year_selector")
        
        if selected_year != "All Years":
            year_num = int(selected_year.split(" ")[1])
            df_filtered = df_forecast[df_forecast['Year'] == year_num].copy()
        else:
            df_filtered = df_forecast.copy()
        
        # Monthly Breakdown
        st.markdown("#### 📊 Monthly Pool & Slab Breakdown")
        
        agg_dict = {'Users': 'sum', 'Total Revenue': 'sum', 'Gross Profit': 'sum'}
        
        if 'Total Fees Collected' in df_filtered.columns:
            agg_dict['Total Fees Collected'] = 'sum'
        elif 'Total Fees' in df_filtered.columns:
            agg_dict['Total Fees'] = 'sum'
            
        if 'Total NII (Lifetime)' in df_filtered.columns:
            agg_dict['Total NII (Lifetime)'] = 'sum'
        elif 'Total NII' in df_filtered.columns:
            agg_dict['Total NII'] = 'sum'
        
        monthly_pool_stats = df_filtered.groupby(['Month', 'Duration', 'Slab Amount']).agg(agg_dict).reset_index()
        
        if 'Users' in monthly_pool_stats.columns and 'Slab Amount' in monthly_pool_stats.columns:
            monthly_pool_stats['Pool Size'] = monthly_pool_stats['Users'] * monthly_pool_stats['Slab Amount']
        
        # Format Month column
        if 'Month' in monthly_pool_stats.columns:
            monthly_pool_stats = monthly_pool_stats.copy()
            monthly_pool_stats['Month'] = monthly_pool_stats['Month'].apply(lambda x: f"Month {x}")
        
        # Format numeric columns with commas
        numeric_cols = monthly_pool_stats.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in ['Month', 'Duration']:
                monthly_pool_stats[col] = monthly_pool_stats[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")
        
        st.dataframe(monthly_pool_stats, use_container_width=True)
        
        # === 5-Year YoY Summary ===
        st.markdown("#### 📈 5-Year Year-over-Year Summary")
        
        yearly_agg_dict = {'Users': 'sum', 'Total Revenue': 'sum', 'Gross Profit': 'sum'}
        
        if 'Total Fees Collected' in df_forecast.columns:
            yearly_agg_dict['Total Fees Collected'] = 'sum'
        elif 'Total Fees' in df_forecast.columns:
            yearly_agg_dict['Total Fees'] = 'sum'
            
        if 'Total NII (Lifetime)' in df_forecast.columns:
            yearly_agg_dict['Total NII (Lifetime)'] = 'sum'
        elif 'Total NII' in df_forecast.columns:
            yearly_agg_dict['Total NII'] = 'sum'
        
        yearly_stats = df_forecast.groupby('Year').agg(yearly_agg_dict).reset_index()
        
        if 'Year' in yearly_stats.columns:
            yearly_stats['Year'] = yearly_stats['Year'].apply(lambda x: f"Year {x}")
        
        # Format numeric columns with commas
        numeric_cols_yearly = yearly_stats.select_dtypes(include=[np.number]).columns
        for col in numeric_cols_yearly:
            if col != 'Year':
                yearly_stats[col] = yearly_stats[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")
        
        st.dataframe(yearly_stats, use_container_width=True)
        
        # Market Analysis
        if 'market_size' in st.session_state:
            create_market_analysis(
                st.session_state['market_size'],
                st.session_state['sam_size'], 
                st.session_state['som_size'],
                st.session_state['market_growth_rate'],
                df_forecast,
                CURRENCY_SYMBOL,
                CURRENCY_NAME
            )
        
        # Export options
        st.subheader("📥 Export Data")
        
        # Prepare unformatted dataframes for export
        # Monthly Pool Stats (unformatted)
        monthly_pool_stats_export = df_filtered.groupby(['Month', 'Duration', 'Slab Amount']).agg(agg_dict).reset_index()
        if 'Users' in monthly_pool_stats_export.columns and 'Slab Amount' in monthly_pool_stats_export.columns:
            monthly_pool_stats_export['Pool Size'] = monthly_pool_stats_export['Users'] * monthly_pool_stats_export['Slab Amount']
        
        # Yearly Stats (unformatted) - use same aggregation dict as yearly_stats
        yearly_agg_dict_export = {'Users': 'sum', 'Total Revenue': 'sum', 'Gross Profit': 'sum'}
        if 'Total Fees Collected' in df_forecast.columns:
            yearly_agg_dict_export['Total Fees Collected'] = 'sum'
        elif 'Total Fees' in df_forecast.columns:
            yearly_agg_dict_export['Total Fees'] = 'sum'
        if 'Total NII (Lifetime)' in df_forecast.columns:
            yearly_agg_dict_export['Total NII (Lifetime)'] = 'sum'
        elif 'Total NII' in df_forecast.columns:
            yearly_agg_dict_export['Total NII'] = 'sum'
        yearly_stats_export = df_forecast.groupby('Year').agg(yearly_agg_dict_export).reset_index()
        
        # Pool Breakdown (unformatted)
        pool_breakdown_export = df_filtered.groupby(['Duration', 'Slab Amount']).agg({
            'Users': 'sum',
            'Pool Size': 'sum' if 'Pool Size' in df_filtered.columns else (df_filtered['Users'] * df_filtered['Slab Amount']).sum(),
            'Total Revenue': 'sum',
            'Gross Profit': 'sum'
        }).reset_index()
        if 'Pool Size' in pool_breakdown_export.columns and 'Users' in pool_breakdown_export.columns:
            pool_breakdown_export['Avg Pool Size'] = pool_breakdown_export['Pool Size'] / pool_breakdown_export['Users']
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df_forecast.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"rosca_forecast_{scenario_name}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Comprehensive Excel export
            from io import BytesIO
            output = BytesIO()
            try:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Main forecast data
                    df_forecast.to_excel(writer, sheet_name='Forecast', index=False)
                    
                    # Summary sheets
                    if not df_monthly_summary.empty:
                        df_monthly_summary.to_excel(writer, sheet_name='Monthly Summary', index=False)
                    if not df_yearly_summary.empty:
                        df_yearly_summary.to_excel(writer, sheet_name='Yearly Summary', index=False)
                    if not df_profit_share.empty:
                        df_profit_share.to_excel(writer, sheet_name='Profit Share', index=False)
                    
                    # Detailed breakdowns
                    if not monthly_pool_stats_export.empty:
                        monthly_pool_stats_export.to_excel(writer, sheet_name='Monthly Pool Stats', index=False)
                    if not yearly_stats_export.empty:
                        yearly_stats_export.to_excel(writer, sheet_name='Yearly Stats', index=False)
                    if not pool_breakdown_export.empty:
                        pool_breakdown_export.to_excel(writer, sheet_name='Pool Breakdown', index=False)
                    
                    # Log sheets
                    if not df_deposit_log.empty:
                        df_deposit_log.to_excel(writer, sheet_name='Deposit Log', index=False)
                    if not df_default_log.empty:
                        df_default_log.to_excel(writer, sheet_name='Default Log', index=False)
                    if not df_lifecycle_log.empty:
                        df_lifecycle_log.to_excel(writer, sheet_name='Lifecycle Log', index=False)
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📊 Download Complete Excel",
                    data=excel_data,
                    file_name=f"rosca_complete_export_{scenario_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error creating Excel file: {str(e)}")
                st.info("Please ensure 'openpyxl' is installed: pip install openpyxl")
    
    elif view_mode == "🔧 Detailed Forecast":
        # Detailed forecast table
        st.subheader("📋 Detailed Forecast Results")
        st.dataframe(df_forecast.style.format(precision=0, thousands=","))
        
        # Summary tables
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Monthly Summary")
            # Format with commas
            df_monthly_display = df_monthly_summary.copy()
            numeric_cols = df_monthly_display.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                df_monthly_display[col] = df_monthly_display[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")
            st.dataframe(df_monthly_display, use_container_width=True)
        
        with col2:
            st.subheader("📈 Yearly Summary")
            # Format with commas
            df_yearly_display = df_yearly_summary.copy()
            numeric_cols = df_yearly_display.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                df_yearly_display[col] = df_yearly_display[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")
            st.dataframe(df_yearly_display, use_container_width=True)
        
        # Profit share analysis
        st.subheader("🤝 Profit Share Analysis")
        st.dataframe(df_profit_share)
    
    elif view_mode == "📈 Analytics View":
        # Analytics dashboard
        create_analytics_dashboard(df_forecast, config, fee_collection_mode, CURRENCY_SYMBOL, CURRENCY_NAME)
        
        # Additional analysis
        st.subheader("📊 Additional Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Duration analysis
            df_duration_analysis = create_duration_analysis(df_forecast)
            st.subheader("📅 Duration Analysis")
            st.dataframe(df_duration_analysis)
        
        with col2:
            # Slab analysis
            df_slab_analysis = create_slab_analysis(df_forecast)
            st.subheader("💵 Slab Analysis")
            st.dataframe(df_slab_analysis)
        
        # Risk analysis
        df_risk_analysis = create_risk_analysis(df_forecast)
        st.subheader("⚠️ Risk Analysis")
        st.dataframe(df_risk_analysis)
    
    elif view_mode == "🧩 Advanced User Growth":
        # This view mode has been removed - functionality integrated into Dashboard View  
        st.info("✅ Advanced Growth, Monthly Pool & Slab Stats, and Year-on-Year are now all part of the Dashboard View!")
    
    elif view_mode == "⚙️ Configuration Mode":
        # Configuration summary
        st.subheader("⚙️ Configuration Summary")
        df_config_summary = create_configuration_summary(config, fee_collection_mode, CURRENCY_SYMBOL, CURRENCY_NAME)
        st.dataframe(df_config_summary)
        
        # Configuration editor
        st.subheader("🔧 Edit Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Financial Parameters**")
            new_kibor_rate = st.number_input("KIBOR Rate (%)", value=config['kibor_rate'], step=0.1)
            new_spread = st.number_input("Spread (%)", value=config['spread'], step=0.1)
            new_profit_split = st.number_input("Profit Split - Party A (%)", value=config['profit_split'], step=1.0)
        
        with col2:
            st.markdown("**Default Parameters**")
            new_default_rate = st.number_input("Default Rate (%)", value=config['default_rate'], step=0.1)
            new_penalty_pct = st.number_input("Penalty Rate (%)", value=config['penalty_pct'], step=0.1)
            new_recovery_rate = st.number_input("Recovery Rate (%)", value=config['recovery_rate'], step=1.0)
        
        if st.button("🔄 Update Configuration"):
            # Update configuration
            config['kibor_rate'] = new_kibor_rate
            config['spread'] = new_spread
            config['profit_split'] = new_profit_split
            config['default_rate'] = new_default_rate
            config['penalty_pct'] = new_penalty_pct
            config['recovery_rate'] = new_recovery_rate
            
            # Store updated configuration
            st.session_state['config'] = config
            
            st.success("✅ Configuration updated successfully!")
            st.rerun()
    
    elif view_mode == "🧩 Advanced User Growth":
        # Advanced User Growth system
        st.markdown("## 🧩 Advanced User Growth System")
        st.markdown("**Comprehensive Month-on-Month User Growth with Slab & Slot Distribution**")
        
        # Create configuration UI
        growth_config = create_advanced_user_growth_ui()
        
        if st.button("🚀 Run Advanced Growth Simulation", type="primary"):
            with st.spinner("Running advanced growth simulation..."):
                # Run the modular growth system
                user_growth_data = generate_user_growth(
                    growth_config['initial_users'],
                    growth_config['growth_rate'],
                    growth_config['simulation_months']
                )
                
                user_lifecycle_data = simulate_resting_and_returning_users(
                    user_growth_data,
                    growth_config['durations'],
                    growth_config['rest_periods'],
                    growth_config['simulation_months']
                )
                
                slab_allocation_data = allocate_users_to_slabs(
                    user_lifecycle_data,
                    growth_config['slab_configs'],
                    growth_config['simulation_months']
                )
                
                slot_allocation_data = allocate_users_to_slots(
                    slab_allocation_data,
                    growth_config['slot_configs'],
                    growth_config['simulation_months']
                )
                
                # Calculate monthly metrics
                monthly_metrics = calculate_monthly_metrics(
                    user_growth_data,
                    user_lifecycle_data,
                    slab_allocation_data,
                    slot_allocation_data,
                    [1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000],
                    growth_config['simulation_months']
                )
                
                # Store in session state
                st.session_state['advanced_growth_data'] = {
                    'user_growth': user_growth_data,
                    'user_lifecycle': user_lifecycle_data,
                    'slab_allocation': slab_allocation_data,
                    'slot_allocation': slot_allocation_data,
                    'monthly_metrics': monthly_metrics,
                    'config': growth_config
                }
                
                st.success("✅ Advanced growth simulation completed!")
        
        # Display results if available
        if 'advanced_growth_data' in st.session_state:
            data = st.session_state['advanced_growth_data']
            monthly_metrics = data['monthly_metrics']
            
            # Key Metrics
            st.markdown("### 📊 Key Growth Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_new_users = monthly_metrics['New Users'].sum()
                st.metric("Total New Users", f"{total_new_users:,}")
            
            with col2:
                total_returning = monthly_metrics['Returning Users'].sum()
                st.metric("Total Returning Users", f"{total_returning:,}")
            
            with col3:
                total_deposits = monthly_metrics['Total Deposits'].sum()
                st.metric("Total Deposits", format_currency(total_deposits, CURRENCY_SYMBOL, CURRENCY_NAME))
            
            with col4:
                total_fees = monthly_metrics['Total Fees'].sum()
                st.metric("Total Fees", format_currency(total_fees, CURRENCY_SYMBOL, CURRENCY_NAME))
            
            # Monthly Metrics Table
            st.markdown("### 📋 Monthly Growth Metrics")
            st.dataframe(monthly_metrics, use_container_width=True)
            
            # Growth Charts
            st.markdown("### 📈 Growth Visualization")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # User Growth Chart
                if PLOTLY_AVAILABLE:
                    fig_users = go.Figure()
                    
                    fig_users.add_trace(go.Scatter(
                        x=monthly_metrics['Month'],
                        y=monthly_metrics['New Users'],
                        mode='lines+markers',
                        name='New Users',
                        line=dict(color='#667eea', width=3),
                        marker=dict(size=8, color='#667eea')
                    ))
                    
                    fig_users.add_trace(go.Scatter(
                        x=monthly_metrics['Month'],
                        y=monthly_metrics['Returning Users'],
                        mode='lines+markers',
                        name='Returning Users',
                        line=dict(color='#764ba2', width=3),
                        marker=dict(size=8, color='#764ba2')
                    ))
                    
                    fig_users.add_trace(go.Scatter(
                        x=monthly_metrics['Month'],
                        y=monthly_metrics['Total Active Users'],
                        mode='lines+markers',
                        name='Total Active Users',
                        line=dict(color='#f093fb', width=3),
                        marker=dict(size=8, color='#f093fb')
                    ))
                    
                    fig_users.update_layout(
                        title="👥 User Growth Trends",
                        xaxis_title="Month",
                        yaxis_title="Number of Users",
                        height=400,
                        template="plotly_white"
                    )
                    
                    st.plotly_chart(fig_users, use_container_width=True)
                else:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(monthly_metrics['Month'], monthly_metrics['New Users'], 'o-', color='#667eea', linewidth=3, markersize=8, label='New Users')
                    ax.plot(monthly_metrics['Month'], monthly_metrics['Returning Users'], 'o-', color='#764ba2', linewidth=3, markersize=8, label='Returning Users')
                    ax.plot(monthly_metrics['Month'], monthly_metrics['Total Active Users'], 'o-', color='#f093fb', linewidth=3, markersize=8, label='Total Active Users')
                    ax.set_title("👥 User Growth Trends", fontsize=16, fontweight='bold')
                    ax.set_xlabel("Month", fontsize=12)
                    ax.set_ylabel("Number of Users", fontsize=12)
                    ax.legend(fontsize=10)
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
            
            with col2:
                # Financial Metrics Chart
                if PLOTLY_AVAILABLE:
                    fig_financial = go.Figure()
                    
                    fig_financial.add_trace(go.Scatter(
                        x=monthly_metrics['Month'],
                        y=monthly_metrics['Total Deposits'],
                        mode='lines+markers',
                        name='Total Deposits',
                        line=dict(color='#4facfe', width=3),
                        marker=dict(size=8, color='#4facfe')
                    ))
                    
                    fig_financial.add_trace(go.Scatter(
                        x=monthly_metrics['Month'],
                        y=monthly_metrics['Total Fees'],
                        mode='lines+markers',
                        name='Total Fees',
                        line=dict(color='#00f2fe', width=3),
                        marker=dict(size=8, color='#00f2fe')
                    ))
                    
                    fig_financial.update_layout(
                        title="💰 Financial Metrics",
                        xaxis_title="Month",
                        yaxis_title="Amount",
                        height=400,
                        template="plotly_white"
                    )
                    
                    st.plotly_chart(fig_financial, use_container_width=True)
                else:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(monthly_metrics['Month'], monthly_metrics['Total Deposits'], 'o-', color='#4facfe', linewidth=3, markersize=8, label='Total Deposits')
                    ax.plot(monthly_metrics['Month'], monthly_metrics['Total Fees'], 'o-', color='#00f2fe', linewidth=3, markersize=8, label='Total Fees')
                    ax.set_title("💰 Financial Metrics", fontsize=16, fontweight='bold')
                    ax.set_xlabel("Month", fontsize=12)
                    ax.set_ylabel("Amount", fontsize=12)
                    ax.legend(fontsize=10)
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
    
    elif view_mode == "⚙️ Configuration Mode":
        # Configuration summary
        st.subheader("⚙️ Configuration Summary")
        df_config_summary = create_configuration_summary(config, fee_collection_mode, CURRENCY_SYMBOL, CURRENCY_NAME)
        st.dataframe(df_config_summary)
        
        # Configuration editor
        st.subheader("🔧 Edit Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Financial Parameters**")
            new_kibor_rate = st.number_input("KIBOR Rate (%)", value=config['kibor_rate'], step=0.1)
            new_spread = st.number_input("Spread (%)", value=config['spread'], step=0.1)
            new_profit_split = st.number_input("Profit Split - Party A (%)", value=config['profit_split'], step=1.0)
        
        with col2:
            st.markdown("**Default Parameters**")
            new_default_rate = st.number_input("Default Rate (%)", value=config['default_rate'], step=0.1)
            new_penalty_pct = st.number_input("Penalty Rate (%)", value=config['penalty_pct'], step=0.1)
            new_recovery_rate = st.number_input("Recovery Rate (%)", value=config['recovery_rate'], step=1.0)
        
        if st.button("🔄 Update Configuration"):
            # Update configuration
            config['kibor_rate'] = new_kibor_rate
            config['spread'] = new_spread
            config['profit_split'] = new_profit_split
            config['default_rate'] = new_default_rate
            config['penalty_pct'] = new_penalty_pct
            config['recovery_rate'] = new_recovery_rate
            
            # Store updated configuration
            st.session_state['config'] = config
            
            st.success("✅ Configuration updated successfully!")
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 2rem;">
    <p>💰 BACHAT KOMMITTEE Forecast/Pricing</p>
</div>
""", unsafe_allow_html=True)
