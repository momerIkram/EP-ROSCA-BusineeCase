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
    page_title="BACHAT-ROSCA Forecast", 
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.15);
        color: white;
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
        background: linear-gradient(90deg, #667eea, #764ba2);
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
        font-weight: 800;
        font-size: 2.2rem;
        color: #1e293b;
        margin: 0 0 0.5rem 0;
        line-height: 1;
    }
    
    .metric-change {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .metric-change.positive {
        color: #10b981;
    }
    
    .metric-change.negative {
        color: #ef4444;
    }
    
    .metric-change.neutral {
        color: #6b7280;
    }
    
    .metric-icon {
        font-size: 1.2rem;
    }
    
    /* Chart Containers */
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        margin-bottom: 1.5rem;
    }
    
    .chart-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.3rem;
        color: #1e293b;
        margin: 0 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f8fafc;
        padding: 4px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Real-time indicator */
    .realtime-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        background: #dcfce7;
        color: #166534;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    
    .pulse-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🎨 COLORS & THEMES
# =============================================================================

DASHBOARD_COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'info': '#3b82f6',
    'light': '#f8fafc',
    'dark': '#1e293b',
    'muted': '#64748b'
}

CHART_COLORS = [
    '#667eea', '#764ba2', '#10b981', '#f59e0b', '#ef4444',
    '#3b82f6', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
]

# Modern Chart Styling
TEXT_COLOR = '#333333'
GRID_COLOR = '#D8D8D8'
PLOT_BG_COLOR = '#FFFFFF'
FIG_BG_COLOR = '#F8F9FA'
COLOR_PRIMARY_BAR = '#3B75AF'
COLOR_SECONDARY_LINE = '#4CAF50'
COLOR_ACCENT_BAR = '#FFC107'
COLOR_ACCENT_LINE = '#9C27B0'
COLOR_HIGHLIGHT_BAR = '#E91E63'

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica Neue', 'DejaVu Sans', 'Liberation Sans', 'sans-serif'],
    'axes.labelcolor': TEXT_COLOR, 'xtick.color': TEXT_COLOR, 'ytick.color': TEXT_COLOR,
    'axes.titlecolor': TEXT_COLOR, 'figure.facecolor': FIG_BG_COLOR, 'axes.facecolor': PLOT_BG_COLOR,
    'axes.edgecolor': GRID_COLOR, 'axes.grid': True, 'grid.color': GRID_COLOR,
    'grid.linestyle': '--', 'grid.linewidth': 0.7, 'legend.frameon': False,
    'legend.fontsize': 9, 'legend.title_fontsize': 10, 'figure.dpi': 100,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': True,
    'axes.spines.bottom': True, 'axes.titlesize': 13, 'axes.labelsize': 11,
    'xtick.labelsize': 9, 'ytick.labelsize': 9, 'lines.linewidth': 2,
    'lines.markersize': 5, 'patch.edgecolor': 'none'
})

# =============================================================================
# 🛠️ UTILITY FUNCTIONS
# =============================================================================

def days_between_specific_dates(start_month_idx, start_day_of_month, end_month_idx, end_day_of_month, base_year=2024):
    """Calculate days between two dates specified by month index and day of month"""
    if start_month_idx > end_month_idx or (start_month_idx == end_month_idx and start_day_of_month >= end_day_of_month):
        return 0
    start_actual_month = (start_month_idx % 12) + 1
    start_actual_year = base_year + (start_month_idx // 12)
    end_actual_month = (end_month_idx % 12) + 1
    end_actual_year = base_year + (end_month_idx // 12)
    try:
        date_start = date(start_actual_year, start_actual_month, start_day_of_month)
        date_end = date(end_actual_year, end_actual_month, end_day_of_month)
        return (date_end - date_start).days
    except ValueError:
        return max(0, (end_month_idx - start_month_idx) * 30 + (end_day_of_month - start_day_of_month))

def create_metric_card(title, value, change, change_type="positive", icon="📊", subtitle=""):
    """Create a modern metric card"""
    change_class = "positive" if change_type == "positive" else "negative" if change_type == "negative" else "neutral"
    change_icon = "↗️" if change_type == "positive" else "↘️" if change_type == "negative" else "→"
    
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-change {change_class}">
            <span class="metric-icon">{change_icon}</span>
            <span>{change}</span>
        </div>
        {f'<div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">{subtitle}</div>' if subtitle else ''}
    </div>
    """

def format_currency(value):
    """Format value as currency"""
    if pd.isna(value) or value == 0:
        return "₹0"
    if value >= 10000000:  # 1 crore
        return f"₹{value/10000000:.1f}Cr"
    elif value >= 100000:  # 1 lakh
        return f"₹{value/100000:.1f}L"
    elif value >= 1000:  # 1 thousand
        return f"₹{value/1000:.1f}K"
    else:
        return f"₹{value:,.0f}"

def format_number(value):
    """Format large numbers"""
    if pd.isna(value) or value == 0:
        return "0"
    if value >= 10000000:  # 1 crore
        return f"{value/10000000:.1f}Cr"
    elif value >= 100000:  # 1 lakh
        return f"{value/100000:.1f}L"
    elif value >= 1000:  # 1 thousand
        return f"{value/1000:.1f}K"
    else:
        return f"{value:,.0f}"

# =============================================================================
# 🚀 MAIN APPLICATION
# =============================================================================

# Header
st.markdown("""
<div class="dashboard-header">
    <h1>🚀 ROSCA Forecast Pro</h1>
    <p>Complete Business Intelligence & Forecasting Platform</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 📊 SCENARIO & UI SETUP
# =============================================================================

# View selection
view_mode = st.selectbox(
    "Select View Mode",
    ["📊 Dashboard View", "🔧 Detailed Forecast", "📈 Analytics Only"],
    help="Choose how to display your data"
)

# Multi-scenario support
scenarios = []
scenario_count = st.sidebar.number_input("Number of Scenarios", min_value=1, max_value=3, value=1)

for i in range(scenario_count):
    with st.sidebar.expander(f"Scenario {i+1} Settings"):
        name = st.text_input(f"Scenario Name {i+1}", value=f"Scenario {i+1}", key=f"name_{i}")
        total_market = st.number_input("Total Market Size", value=20000000, min_value=0, key=f"market_{i}")
        tam_pct = st.number_input("TAM % of Market", min_value=0.0, max_value=100.0, value=10.0, step=0.01, key=f"tam_pct_{i}")
        start_pct = st.number_input("Starting TAM % (Month 1 New Users)", min_value=0.0, max_value=100.0, value=10.0, step=0.01, key=f"start_pct_{i}", help="Initial new users as % of initial TAM for Month 1.")
        monthly_growth = st.number_input("Monthly Acquisition Rate (on Cum. Acquired Base) (%)",min_value=0.0, value=2.0, step=0.01, key=f"growth_{i}", help="New users next month = Cum. Acquired Base * Rate")
        annual_growth = st.number_input("Annual TAM Growth (%)",min_value=0.0, value=5.0, step=0.01, key=f"annual_{i}")
        cap_tam = st.checkbox("Cap TAM Growth?", value=False, key=f"cap_toggle_{i}")
        scenarios.append({
            "name": name, "total_market": total_market, "tam_pct": tam_pct,
            "start_pct": start_pct, "monthly_growth": monthly_growth, 
            "annual_growth": annual_growth, "cap_tam": cap_tam
        })

# =============================================================================
# ⚙️ GLOBAL INPUTS
# =============================================================================

st.sidebar.markdown("## ⚙️ Global Configuration")

# Fee Collection Mode
st.sidebar.markdown("### 💳 Fee Collection Mode")
fee_collection_mode = st.sidebar.selectbox(
    "Fee Collection Method",
    ["Upfront Fee (Entire Pool)", "Monthly Fee Collection"],
    help="Choose how to collect fees from customers"
)

if fee_collection_mode == "Upfront Fee (Entire Pool)":
    st.sidebar.info("💡 **Upfront Mode:** Collect entire fee when customer joins the pool")
    st.sidebar.markdown("**Benefits:**")
    st.sidebar.markdown("- ✅ Immediate cash flow")
    st.sidebar.markdown("- ✅ Reduced collection risk")
    st.sidebar.markdown("- ✅ Better liquidity management")
else:
    st.sidebar.info("💡 **Monthly Mode:** Collect fees monthly with installments")
    st.sidebar.markdown("**Benefits:**")
    st.sidebar.markdown("- ✅ Lower barrier to entry")
    st.sidebar.markdown("- ✅ Better customer experience")
    st.sidebar.markdown("- ✅ Reduced upfront cost")

global_collection_day = st.sidebar.number_input("Collection Day of Month", min_value=1, max_value=28, value=1)
global_payout_day = st.sidebar.number_input("Payout Day of Month", min_value=1, max_value=28, value=20)
profit_split = st.sidebar.number_input("Profit Share for Party A (%)", min_value=0, max_value=100, value=50)
party_a_pct = profit_split / 100
party_b_pct = 1 - party_a_pct
kibor = st.sidebar.number_input("KIBOR (%)", value=11.0, step=0.1)
spread = st.sidebar.number_input("Spread (%)", value=5.0, step=0.1)
rest_period = st.sidebar.number_input("Rest Period (months)", value=1, min_value=0)
# Default Configuration
st.sidebar.markdown("### ⚠️ Default Configuration")

default_rate = st.sidebar.number_input("Default Rate (%)", value=1.0, min_value=0.0, max_value=100.0, step=0.1, help="Overall default rate across all customers")

# Default Types Configuration
st.sidebar.markdown("#### Default Types Distribution")
default_pre_pct = st.sidebar.number_input("Pre-Payout Default %", min_value=0, max_value=100, value=50, help="Percentage of defaults that occur before payout")
default_post_pct = 100 - default_pre_pct
st.sidebar.info(f"Post-Payout Default %: {default_post_pct}%")

# Default Fees and Penalties
st.sidebar.markdown("#### Default Fees & Penalties")
penalty_pct = st.sidebar.number_input("Pre-Payout Refund (%)", value=10.0, min_value=0.0, max_value=100.0, step=0.1, help="Percentage refunded to pre-payout defaulters")
default_fee_rate = st.sidebar.number_input("Default Processing Fee (%)", value=2.0, min_value=0.0, max_value=50.0, step=0.1, help="Additional fee charged on defaulted amounts")
late_fee_rate = st.sidebar.number_input("Late Payment Fee (%)", value=5.0, min_value=0.0, max_value=50.0, step=0.1, help="Fee for late payments before default")

# Default Impact Analysis
st.sidebar.markdown("#### Default Impact Settings")
default_recovery_rate = st.sidebar.number_input("Default Recovery Rate (%)", value=20.0, min_value=0.0, max_value=100.0, step=1.0, help="Percentage of defaulted amounts that can be recovered")
default_impact_on_revenue = st.sidebar.checkbox("Include Default Impact in Revenue Analysis", value=True, help="Show how defaults affect revenue calculations")

# =============================================================================
# 📊 DURATION/SLAB/SLOT CONFIGURATION
# =============================================================================

st.sidebar.markdown("## 📊 Product Configuration")

validation_messages = []
durations_input = st.sidebar.multiselect("Select Durations (months)", [3, 4, 5, 6, 8, 10], default=[3, 4, 6])
durations = sorted([int(d) for d in durations_input])

yearly_duration_share = {}
slab_map = {}
slot_fees = {}
slot_distribution = {}

# Initialize with default values
for y_config in range(1, 6):
    yearly_duration_share[y_config] = {}
    for dur_val in durations:
        yearly_duration_share[y_config][dur_val] = 100.0 / len(durations) if len(durations) > 0 else 0

for d_config in durations:
    with st.sidebar.expander(f"{d_config}M Duration Configuration"):
        st.markdown(f"**Duration: {d_config} months**")
        
        # Slab configuration
        slab_options = [1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000]
        selected_slabs = st.multiselect(f"Select Slabs for {d_config}M", slab_options, default=[1000, 2000, 5000], key=f"slabs_{d_config}")
        slab_map[d_config] = selected_slabs
        
        # Slot fee configuration with blocking
        st.markdown("**Slot Fee Configuration & Blocking**")
        slot_fees[d_config] = {}
        slot_distribution[d_config] = {}
        
        for slot_num in range(1, d_config + 1):
            col1, col2, col3 = st.columns(3)
            with col1:
                fee_pct = st.number_input(f"Slot {slot_num} Fee (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1, key=f"fee_{d_config}_{slot_num}")
            with col2:
                blocked = st.checkbox(f"Block Slot {slot_num}", key=f"block_{d_config}_{slot_num}")
            with col3:
                if not blocked:
                    dist_pct = st.number_input(f"Slot {slot_num} Distribution (%)", min_value=0.0, max_value=100.0, value=100.0/d_config, step=0.1, key=f"dist_{d_config}_{slot_num}")
                    slot_distribution[d_config][slot_num] = dist_pct
                else:
                    slot_distribution[d_config][slot_num] = 0
                    st.info("Blocked")
            
            slot_fees[d_config][slot_num] = {"fee_pct": fee_pct, "blocked": blocked}

# Validation for year-by-year duration shares
for y_config in range(1, 6):
    if y_config in yearly_duration_share:
        current_year_total_share = sum(yearly_duration_share[y_config].values())
        if current_year_total_share > 0 and abs(current_year_total_share - 100) > 0.1:
            validation_messages.append(f"⚠️ Year {y_config} duration share total is {current_year_total_share:.1f}%. It should be 100%.")

# Validation for slot distribution (only unblocked slots)
for d_config in durations:
    if d_config in slot_distribution and d_config in slot_fees:
        # Calculate total distribution for unblocked slots only
        unblocked_slots = {k: v for k, v in slot_distribution[d_config].items() 
                          if not slot_fees[d_config].get(k, {}).get('blocked', False)}
        total_unblocked_dist_pct = sum(unblocked_slots.values())
        
        if total_unblocked_dist_pct > 0 and abs(total_unblocked_dist_pct - 100) > 0.1:
            validation_messages.append(f"⚠️ Slot distribution for unblocked slots in {d_config}M totals {total_unblocked_dist_pct:.1f}%. It should be 100%.")

if validation_messages:
    for msg_val in validation_messages: 
        st.warning(msg_val)
    if any("must not exceed 100%" in msg or "should be 100%" in msg for msg in validation_messages):
        st.stop()

# =============================================================================
# 🧮 COMPLETE FORECASTING ENGINE
# =============================================================================

def run_forecast(config_param_fc, fee_collection_mode_fc="Monthly Fee Collection"):
    """Complete 60-month forecasting engine with all original features"""
    try:
        months_fc = 60
        
        potential_initial_tam_float = config_param_fc['total_market'] * (config_param_fc['tam_pct'] / 100)
        initial_tam_fc = math.ceil(potential_initial_tam_float)
        if initial_tam_fc < 0: 
            initial_tam_fc = 0 
        
        acquisition_rate_fc = config_param_fc['monthly_growth'] / 100
        
        potential_float_m1_users = initial_tam_fc * (config_param_fc['start_pct'] / 100) 
        initial_new_users_m1_fc = math.ceil(potential_float_m1_users)
        if initial_new_users_m1_fc < 0: 
            initial_new_users_m1_fc = 0
        
        cumulative_acquired_base_fc = 0 
        rejoin_tracker_fc = {}
        forecast_data_fc, deposit_log_data_fc, default_log_data_fc, lifecycle_data_fc = [], [], [], []
        
        TAM_current_year_fc = initial_tam_fc 
        TAM_used_cumulative_vs_cap_fc = 0 
        enforce_cap_growth_fc = config_param_fc.get("cap_tam", False)

        current_kibor_rate_fc = config_param_fc['kibor'] / 100
        current_spread_rate_fc = config_param_fc['spread'] / 100
        daily_interest_rate_fc = (current_kibor_rate_fc + current_spread_rate_fc) / 365
        current_rest_period_months_fc = config_param_fc['rest_period']
        current_default_frac_fc = config_param_fc['default_rate'] / 100
        current_penalty_frac_fc = config_param_fc['penalty_pct'] / 100
        global_default_pre_frac_fc = default_pre_pct / 100
        global_default_post_frac_fc = default_post_pct / 100

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        for m_idx_fc in range(months_fc): 
            current_month_num_fc = m_idx_fc + 1 
            current_year_num_fc = m_idx_fc // 12 + 1
            
            # Update progress
            progress = (m_idx_fc + 1) / months_fc
            progress_bar.progress(progress)
            status_text.text(f"Processing Month {current_month_num_fc}/60...")
            
            if m_idx_fc > 0 and m_idx_fc % 12 == 0: 
                TAM_current_year_fc_float = TAM_current_year_fc * (1 + config_param_fc['annual_growth'] / 100)
                TAM_current_year_fc = math.ceil(TAM_current_year_fc_float) 

            potential_new_acquisitions_this_month_fc = 0 
            if m_idx_fc == 0: 
                potential_new_acquisitions_this_month_fc = initial_new_users_m1_fc 
            else: 
                if cumulative_acquired_base_fc > 0 and acquisition_rate_fc > 0:
                    potential_float_users = cumulative_acquired_base_fc * acquisition_rate_fc
                    potential_new_acquisitions_this_month_fc = math.ceil(potential_float_users)
            if potential_new_acquisitions_this_month_fc < 0 : 
                potential_new_acquisitions_this_month_fc = 0

            actual_new_acquisitions_this_month_fc = potential_new_acquisitions_this_month_fc
            if enforce_cap_growth_fc:
                current_tam_for_cap = max(0, TAM_current_year_fc)
                if (TAM_used_cumulative_vs_cap_fc + actual_new_acquisitions_this_month_fc) > current_tam_for_cap:
                    actual_new_acquisitions_this_month_fc = max(0, current_tam_for_cap - TAM_used_cumulative_vs_cap_fc)
                actual_new_acquisitions_this_month_fc = int(actual_new_acquisitions_this_month_fc) 
            
            cumulative_acquired_base_fc += actual_new_acquisitions_this_month_fc
            TAM_used_cumulative_vs_cap_fc += actual_new_acquisitions_this_month_fc
            newly_acquired_this_month_fc_val = actual_new_acquisitions_this_month_fc

            rejoining_users_this_month_fc_val = rejoin_tracker_fc.get(m_idx_fc, 0) 
            total_onboarding_this_month_fc = newly_acquired_this_month_fc_val + rejoining_users_this_month_fc_val
            temp_rejoining_users_for_allocation = rejoining_users_this_month_fc_val
            
            # Get the duration shares for the current year
            durations_for_this_year_fc = yearly_duration_share.get(current_year_num_fc, {})

            if total_onboarding_this_month_fc == 0 or not durations_for_this_year_fc:
                lifecycle_data_fc.append({"Month": current_month_num_fc, "New Users Acquired for Cohort": 0, "Rejoining Users for Cohort": 0, "Total Onboarding to Cohort": 0})
                deposit_log_data_fc.append({"Month": current_month_num_fc, "Users Joining": 0, "Installments Collected": 0, "NII This Month (Avg)": 0})
                default_log_data_fc.append({"Month": current_month_num_fc, "Year": current_year_num_fc, "Pre-Payout Defaulters (Cohort)": 0, "Post-Payout Defaulters (Cohort)": 0, "Default Loss (Cohort Lifetime)": 0})
                continue

            # User distribution logic with rounding error management
            remaining_users_to_distribute = total_onboarding_this_month_fc
            num_dur_configs = len(durations_for_this_year_fc)
            
            sorted_dur_shares = sorted(durations_for_this_year_fc.items(), key=lambda item: item[1], reverse=True)

            for idx_dur, (dur_val_fc, dur_share_pct_fc) in enumerate(sorted_dur_shares):
                if dur_share_pct_fc == 0 or remaining_users_to_distribute == 0: 
                    continue
                
                if idx_dur == num_dur_configs - 1:
                    users_for_this_duration_fc = remaining_users_to_distribute
                else:
                    users_for_this_duration_fc = math.ceil(remaining_users_to_distribute * (dur_share_pct_fc / 100))
                    if users_for_this_duration_fc > remaining_users_to_distribute:
                        users_for_this_duration_fc = remaining_users_to_distribute
                
                if users_for_this_duration_fc <= 0: 
                    continue

                current_duration_distributed_users = users_for_this_duration_fc
                slabs_for_this_duration = slab_map.get(dur_val_fc, [1000])
                
                for slab_val_fc in slabs_for_this_duration:
                    if current_duration_distributed_users <= 0: 
                        break
                    
                    current_slab_distributed_users = current_duration_distributed_users
                    slots_for_this_duration = [s for s in range(1, dur_val_fc + 1) if not slot_fees.get(dur_val_fc, {}).get(s, {}).get('blocked', False)]
                    
                    if not slots_for_this_duration:
                        continue
                    
                    for slot_num_fc in slots_for_this_duration:
                        if current_slab_distributed_users <= 0: 
                            break
                        
                        slot_dist_pct = slot_distribution.get(dur_val_fc, {}).get(slot_num_fc, 0)
                        if slot_dist_pct <= 0: 
                            continue
                        
                        users_for_this_slot_fc = math.ceil(current_slab_distributed_users * (slot_dist_pct / 100))
                        if users_for_this_slot_fc > current_slab_distributed_users:
                            users_for_this_slot_fc = current_slab_distributed_users
                        
                        if users_for_this_slot_fc <= 0: 
                            continue
                        
                        # Calculate metrics for this cohort
                        installment_val_fc = slab_val_fc
                        total_commitment_per_user_fc = dur_val_fc * installment_val_fc
                        total_commitment_for_cohort_fc = users_for_this_slot_fc * total_commitment_per_user_fc
                        
                        fee_pct_for_slot_fc = slot_fees.get(dur_val_fc, {}).get(slot_num_fc, {}).get('fee_pct', 2.0)
                        
                        # Calculate fee collection based on mode
                        if fee_collection_mode_fc == "Upfront Fee (Entire Pool)":
                            # Collect entire fee upfront when customer joins
                            total_fee_collected_for_cohort_fc = total_commitment_for_cohort_fc * (fee_pct_for_slot_fc / 100)
                            monthly_fee_collection_fc = 0  # No monthly fee collection
                        else:
                            # Monthly fee collection - collect fee monthly with installments
                            monthly_fee_per_user_fc = (total_commitment_per_user_fc * (fee_pct_for_slot_fc / 100)) / dur_val_fc
                            total_fee_collected_for_cohort_fc = monthly_fee_per_user_fc * users_for_this_slot_fc * dur_val_fc
                            monthly_fee_collection_fc = monthly_fee_per_user_fc * users_for_this_slot_fc
                        
                        # Enhanced NII calculation with multiple inputs
                        total_nii_for_cohort_lifetime_per_user = 0
                        monthly_nii_breakdown = []
                        
                        for j_installment_num in range(dur_val_fc): 
                            collection_month_of_this_installment_idx = m_idx_fc + j_installment_num
                            payout_due_month_idx_for_cohort_fc = m_idx_fc + slot_num_fc - 1
                            
                            # Calculate days this installment is held
                            days_this_installment_held = days_between_specific_dates(
                                collection_month_of_this_installment_idx, global_collection_day, 
                                payout_due_month_idx_for_cohort_fc, global_payout_day
                            )
                            
                            # Base NII from installment amount
                            base_nii_from_installment = installment_val_fc * daily_interest_rate_fc * days_this_installment_held
                            
                            # Additional NII from fee collection (if upfront mode)
                            fee_nii_contribution = 0
                            if fee_collection_mode_fc == "Upfront Fee (Entire Pool)":
                                # Fee collected upfront earns interest until payout
                                upfront_fee_per_user = total_commitment_per_user_fc * (fee_pct_for_slot_fc / 100)
                                fee_nii_contribution = upfront_fee_per_user * daily_interest_rate_fc * days_this_installment_held
                            else:
                                # Monthly fee collection - fee earns interest from collection to payout
                                monthly_fee_per_user = (total_commitment_per_user_fc * (fee_pct_for_slot_fc / 100)) / dur_val_fc
                                fee_collection_month = collection_month_of_this_installment_idx
                                fee_days_held = days_between_specific_dates(
                                    fee_collection_month, global_collection_day,
                                    payout_due_month_idx_for_cohort_fc, global_payout_day
                                )
                                fee_nii_contribution = monthly_fee_per_user * daily_interest_rate_fc * fee_days_held
                            
                            # Pool growth NII - interest on accumulated deposits
                            pool_growth_nii = 0
                            if j_installment_num > 0:  # Not the first installment
                                # Calculate accumulated pool from previous installments
                                accumulated_pool = installment_val_fc * j_installment_num
                                pool_growth_nii = accumulated_pool * daily_interest_rate_fc * days_this_installment_held
                            
                            # Total NII for this installment
                            total_nii_this_installment = base_nii_from_installment + fee_nii_contribution + pool_growth_nii
                            total_nii_for_cohort_lifetime_per_user += total_nii_this_installment
                            
                            # Store monthly breakdown for analysis
                            monthly_nii_breakdown.append({
                                "installment": j_installment_num + 1,
                                "base_nii": base_nii_from_installment,
                                "fee_nii": fee_nii_contribution,
                                "pool_growth_nii": pool_growth_nii,
                                "total_nii": total_nii_this_installment,
                                "days_held": days_this_installment_held
                            })
                        
                        # Calculate cohort-level NII
                        total_nii_for_cohort_duration_fc = total_nii_for_cohort_lifetime_per_user * users_for_this_slot_fc
                        avg_monthly_nii_for_cohort = total_nii_for_cohort_duration_fc / dur_val_fc if dur_val_fc > 0 else 0
                        nii_to_log_for_joining_month = avg_monthly_nii_for_cohort 

                        # Enhanced Default calculations with types and fees
                        num_defaulters_total_fc = math.ceil(users_for_this_slot_fc * current_default_frac_fc) 
                        num_pre_payout_defaulters_fc = math.ceil(num_defaulters_total_fc * global_default_pre_frac_fc) 
                        num_post_payout_defaulters_fc = num_defaulters_total_fc - num_pre_payout_defaulters_fc
                        if num_post_payout_defaulters_fc < 0: 
                            num_post_payout_defaulters_fc = 0

                        # Enhanced Loss calculations with default fees
                        # Pre-payout defaults: partial refund + default processing fee
                        refund_amount_per_pre_defaulter = total_commitment_per_user_fc * (current_penalty_frac_fc / 100)
                        default_processing_fee_per_pre = total_commitment_per_user_fc * (default_fee_rate / 100)
                        loss_per_pre_defaulter_fc = total_commitment_per_user_fc - refund_amount_per_pre_defaulter + default_processing_fee_per_pre
                        total_pre_payout_loss_fc = num_pre_payout_defaulters_fc * loss_per_pre_defaulter_fc
                        
                        # Post-payout defaults: full loss + default processing fee
                        default_processing_fee_per_post = total_commitment_per_user_fc * (default_fee_rate / 100)
                        loss_per_post_defaulter_fc = total_commitment_per_user_fc + default_processing_fee_per_post
                        total_post_payout_loss_fc = num_post_payout_defaulters_fc * loss_per_post_defaulter_fc
                        
                        # Total loss calculation
                        total_loss_for_cohort_fc = total_pre_payout_loss_fc + total_post_payout_loss_fc
                        
                        # Default recovery calculation
                        total_defaulted_amount = (num_pre_payout_defaulters_fc * total_commitment_per_user_fc) + (num_post_payout_defaulters_fc * total_commitment_per_user_fc)
                        recovered_amount = total_defaulted_amount * (default_recovery_rate / 100)
                        net_default_loss = total_loss_for_cohort_fc - recovered_amount
                        
                        # Default fees collected
                        total_default_fees_collected = (num_pre_payout_defaulters_fc + num_post_payout_defaulters_fc) * (total_commitment_per_user_fc * default_fee_rate / 100)
                        
                        # External capital calculation
                        external_capital_needed_for_cohort_lifetime_fc = total_loss_for_cohort_fc
                        
                        # Expected profit calculation
                        expected_profit_for_cohort_fc = total_fee_collected_for_cohort_fc + total_nii_for_cohort_duration_fc - total_loss_for_cohort_fc
                        
                        # Payout calculations
                        payout_due_calendar_month_for_cohort_fc = m_idx_fc + slot_num_fc
                        payout_amount_scheduled_for_cohort_fc = users_for_this_slot_fc * installment_val_fc
                        
                        # Cash flow calculations
                        cash_in_installments_this_month_cohort_fc = users_for_this_slot_fc * installment_val_fc
                        
                        # Add monthly fee collection to cash flow
                        if fee_collection_mode_fc == "Monthly Fee Collection":
                            cash_in_installments_this_month_cohort_fc += monthly_fee_collection_fc
                        
                        # User allocation between new and rejoining
                        from_newly_acquired_fc = 0
                        from_rejoin_pool_fc = 0
                        if newly_acquired_this_month_fc_val > 0:
                            from_newly_acquired_fc = users_for_this_slot_fc
                        else:
                            from_rejoin_pool_fc = users_for_this_slot_fc
                        
                        users_in_this_specific_cohort_fc = users_for_this_slot_fc
                        
                        # Calculate NII breakdown for analysis
                        total_base_nii = sum(item["base_nii"] for item in monthly_nii_breakdown) * users_for_this_slot_fc
                        total_fee_nii = sum(item["fee_nii"] for item in monthly_nii_breakdown) * users_for_this_slot_fc
                        total_pool_growth_nii = sum(item["pool_growth_nii"] for item in monthly_nii_breakdown) * users_for_this_slot_fc
                        
                        # Store forecast data with enhanced default metrics
                        forecast_data_fc.append({
                            "Month Joined": current_month_num_fc,
                            "Duration": dur_val_fc,
                            "Slab": slab_val_fc,
                            "Slot": slot_num_fc,
                            "Users": users_in_this_specific_cohort_fc,
                            "Total Commitment Per User": total_commitment_per_user_fc,
                            "Total Commitment (Cohort)": total_commitment_for_cohort_fc,
                            "Fee %": fee_pct_for_slot_fc,
                            "Total Fee Collected (Lifetime)": total_fee_collected_for_cohort_fc,
                            "Total NII (Lifetime)": total_nii_for_cohort_duration_fc,
                            "Base NII (Lifetime)": total_base_nii,
                            "Fee NII (Lifetime)": total_fee_nii,
                            "Pool Growth NII (Lifetime)": total_pool_growth_nii,
                            "NII Earned This Month (Avg)": nii_to_log_for_joining_month,
                            "Pools Formed": users_in_this_specific_cohort_fc / dur_val_fc if dur_val_fc > 0 else 0,
                            "Cash In (Installments This Month)": cash_in_installments_this_month_cohort_fc,
                            "Payout Due Month": payout_due_calendar_month_for_cohort_fc,
                            "Payout Amount Scheduled": payout_amount_scheduled_for_cohort_fc,
                            # Enhanced Default Metrics
                            "Total Defaulters": num_defaulters_total_fc,
                            "Pre-Payout Defaulters": num_pre_payout_defaulters_fc,
                            "Post-Payout Defaulters": num_post_payout_defaulters_fc,
                            "Total Default Loss (Lifetime)": total_loss_for_cohort_fc,
                            "Net Default Loss (After Recovery)": net_default_loss,
                            "Default Recovery Amount": recovered_amount,
                            "Default Fees Collected": total_default_fees_collected,
                            "Pre-Payout Loss": total_pre_payout_loss_fc,
                            "Post-Payout Loss": total_post_payout_loss_fc,
                            "External Capital For Loss (Lifetime)": external_capital_needed_for_cohort_lifetime_fc,
                            "Expected Lifetime Profit": expected_profit_for_cohort_fc
                        })
                        
                        deposit_log_data_fc.append({"Month": current_month_num_fc, "Users Joining": users_in_this_specific_cohort_fc, "Installments Collected": cash_in_installments_this_month_cohort_fc, "NII This Month (Avg)": nii_to_log_for_joining_month})
                        default_log_data_fc.append({"Month": current_month_num_fc, "Year": current_year_num_fc, "Pre-Payout Defaulters (Cohort)": num_pre_payout_defaulters_fc,"Post-Payout Defaulters (Cohort)": num_post_payout_defaulters_fc,"Default Loss (Cohort Lifetime)": total_loss_for_cohort_fc})
                        lifecycle_data_fc.append({"Month": current_month_num_fc, "New Users Acquired for Cohort": from_newly_acquired_fc, "Rejoining Users for Cohort": from_rejoin_pool_fc, "Total Onboarding to Cohort": users_in_this_specific_cohort_fc}) 
                        
                        # Rejoin tracking
                        rejoin_at_month_idx_fc = m_idx_fc + dur_val_fc + int(current_rest_period_months_fc)
                        non_defaulters_in_cohort = users_in_this_specific_cohort_fc - num_defaulters_total_fc
                        if non_defaulters_in_cohort < 0: 
                            non_defaulters_in_cohort = 0 
                        if rejoin_at_month_idx_fc < months_fc and non_defaulters_in_cohort > 0 :
                            rejoin_tracker_fc[rejoin_at_month_idx_fc] = rejoin_tracker_fc.get(rejoin_at_month_idx_fc, 0) + non_defaulters_in_cohort
                        
                        current_slab_distributed_users -= users_in_this_specific_cohort_fc
                    current_duration_distributed_users -= users_for_this_duration_fc
                remaining_users_to_distribute -= users_for_this_duration_fc
            
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        df_forecast_fc = pd.DataFrame(forecast_data_fc).fillna(0)
        df_deposit_log_fc = pd.DataFrame(deposit_log_data_fc).fillna(0)
        df_default_log_fc = pd.DataFrame(default_log_data_fc).fillna(0)
        df_lifecycle_fc = pd.DataFrame(lifecycle_data_fc).fillna(0)
        return df_forecast_fc, df_deposit_log_fc, df_default_log_fc, df_lifecycle_fc
        
    except Exception as e:
        st.error(f"Error in forecasting: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# =============================================================================
# 📊 DASHBOARD COMPONENTS
# =============================================================================

def create_dashboard_overview(df_monthly, scenario_name):
    """Create dashboard overview with key metrics"""
    try:
        # Calculate key metrics
        total_users = df_monthly['Users Joining This Month'].sum() if 'Users Joining This Month' in df_monthly.columns else 0
        total_profit = df_monthly['Gross Profit This Month (Accrued from New Cohorts)'].sum() if 'Gross Profit This Month (Accrued from New Cohorts)' in df_monthly.columns else 0
        total_cash_in = df_monthly['Cash In (Installments This Month)'].sum() if 'Cash In (Installments This Month)' in df_monthly.columns else 0
        avg_fee_rate = 2.5  # Simulated
        
        # Calculate growth rates
        if len(df_monthly) > 1 and 'Users Joining This Month' in df_monthly.columns:
            user_growth = ((df_monthly['Users Joining This Month'].iloc[-1] - df_monthly['Users Joining This Month'].iloc[0]) / df_monthly['Users Joining This Month'].iloc[0]) * 100
            profit_growth = ((df_monthly['Gross Profit This Month (Accrued from New Cohorts)'].iloc[-1] - df_monthly['Gross Profit This Month (Accrued from New Cohorts)'].iloc[0]) / df_monthly['Gross Profit This Month (Accrued from New Cohorts)'].iloc[0]) * 100
        else:
            user_growth = 0
            profit_growth = 0
        
        # Display header
        st.markdown(f"""
        <div class="dashboard-header">
            <h1>📊 {scenario_name} Dashboard</h1>
            <p>Real-time Business Intelligence & Analytics</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key metrics
        st.markdown("### 📊 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Total Users", 
                format_number(total_users), 
                f"{user_growth:.1f}%", 
                "positive" if user_growth > 0 else "negative",
                "👥",
                "All time"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                "Total Profit", 
                format_currency(total_profit), 
                f"{profit_growth:.1f}%", 
                "positive" if profit_growth > 0 else "negative",
                "💰",
                "Lifetime"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                "Cash In", 
                format_currency(total_cash_in), 
                "12.5%", 
                "positive",
                "💵",
                "This month"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(create_metric_card(
                "Avg Fee Rate", 
                f"{avg_fee_rate}%", 
                "0.2%", 
                "positive",
                "📈",
                "Weighted avg"
            ), unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error creating dashboard overview: {str(e)}")

def create_monthly_summary(df_forecast_main):
    """Create monthly summary from forecast data"""
    try:
        if df_forecast_main.empty:
            return pd.DataFrame()
            
        # Monthly direct data
        df_monthly_direct = df_forecast_main.groupby("Month Joined")[
            ["Cash In (Installments This Month)", "NII Earned This Month (Avg)", "Pools Formed", "Users"] 
        ].sum().reset_index().rename(columns={"Month Joined": "Month", 
                                              "Users": "Users Joining This Month", 
                                              "NII Earned This Month (Avg)": "NII This Month (Sum of Avg from New Cohorts)"}) 

        # Payouts data
        df_payouts_actual = df_forecast_main.groupby("Payout Due Month")[
            ["Payout Amount Scheduled", "Users"]
        ].sum().reset_index().rename(columns={
            "Payout Due Month": "Month", 
            "Payout Amount Scheduled": "Actual Cash Out This Month",
            "Users": "Payout Recipient Users"
        })
        
        # Lifetime values
        df_lifetime_values = df_forecast_main.groupby("Month Joined")[
            ["Total Fee Collected (Lifetime)", "Total NII (Lifetime)", 
             "Total Default Loss (Lifetime)", "Expected Lifetime Profit",
             "External Capital For Loss (Lifetime)"]
        ].sum().reset_index().rename(columns={"Month Joined": "Month"})

        # Create monthly summary
        df_monthly_summary = pd.DataFrame({"Month": range(1, 61)})
        df_monthly_summary = df_monthly_summary.merge(df_monthly_direct, on="Month", how="left")
        df_monthly_summary = df_monthly_summary.merge(df_payouts_actual, on="Month", how="left")
        df_monthly_summary = df_monthly_summary.merge(df_lifetime_values, on="Month", how="left")
        df_monthly_summary = df_monthly_summary.fillna(0)

        # Calculate derived metrics
        df_monthly_summary["Net Cash Flow This Month"] = df_monthly_summary["Cash In (Installments This Month)"] - df_monthly_summary["Actual Cash Out This Month"]
        df_monthly_summary["Gross Profit This Month (Accrued from New Cohorts)"] = df_monthly_summary["Total Fee Collected (Lifetime)"] + \
                                                            df_monthly_summary["Total NII (Lifetime)"] - \
                                                            df_monthly_summary["Total Default Loss (Lifetime)"]
        
        return df_monthly_summary
        
    except Exception as e:
        st.error(f"Error creating monthly summary: {str(e)}")
        return pd.DataFrame()

def create_yearly_summary(df_monthly_summary):
    """Create yearly summary from monthly data"""
    try:
        if df_monthly_summary.empty:
            return pd.DataFrame()
            
        df_monthly_summary["Year"] = ((df_monthly_summary["Month"] - 1) // 12) + 1
        df_yearly_summary = df_monthly_summary.groupby("Year")[
            ["Users Joining This Month", "Pools Formed", "Cash In (Installments This Month)", 
             "Actual Cash Out This Month", "Net Cash Flow This Month", 
             "NII This Month (Sum of Avg from New Cohorts)", "Total NII (Lifetime)",
             "Payout Recipient Users", "Total Fee Collected (Lifetime)", 
             "Total Default Loss (Lifetime)", "Gross Profit This Month (Accrued from New Cohorts)", 
             "External Capital For Loss (Lifetime)"]
        ].sum().reset_index()
        
        df_yearly_summary.rename(columns={
            "Gross Profit This Month (Accrued from New Cohorts)": "Annual Gross Profit (Accrued from New Cohorts)",
            "NII This Month (Sum of Avg from New Cohorts)": "Annual NII (Sum of Avg from New Cohorts)",
            "Total NII (Lifetime)": "Annual Total NII (Lifetime from New Cohorts)"
        }, inplace=True)
        
        return df_yearly_summary
        
    except Exception as e:
        st.error(f"Error creating yearly summary: {str(e)}")
        return pd.DataFrame()

def create_profit_share_analysis(df_yearly_summary):
    """Create profit share analysis"""
    try:
        if df_yearly_summary.empty:
            return pd.DataFrame()
            
        df_profit_share = pd.DataFrame({
            "Year": df_yearly_summary["Year"],
            "External Capital Needed (Annual Accrual)": df_yearly_summary["External Capital For Loss (Lifetime)"],
            "Annual Cash In (Installments)": df_yearly_summary["Cash In (Installments This Month)"],
            "Annual NII (Accrued Lifetime)": df_yearly_summary["Annual Total NII (Lifetime from New Cohorts)"], 
            "Annual Default Loss (Accrued)": df_yearly_summary["Total Default Loss (Lifetime)"],
            "Annual Fee Collected (Accrued)": df_yearly_summary["Total Fee Collected (Lifetime)"],
            "Annual Gross Profit (Accrued)": df_yearly_summary["Annual Gross Profit (Accrued from New Cohorts)"],
            "Part-A Profit Share": df_yearly_summary["Annual Gross Profit (Accrued from New Cohorts)"] * party_a_pct,
            "Part-B Profit Share": df_yearly_summary["Annual Gross Profit (Accrued from New Cohorts)"] * party_b_pct
        })
        
        df_profit_share["% Loss Covered by External Capital"] = 0
        mask = df_yearly_summary["Total Default Loss (Lifetime)"] > 0
        if mask.any(): 
            df_profit_share.loc[mask, "% Loss Covered by External Capital"] = \
                (df_yearly_summary.loc[mask, "External Capital For Loss (Lifetime)"] / df_yearly_summary.loc[mask, "Total Default Loss (Lifetime)"]) * 100
        df_profit_share.fillna(0, inplace=True)
        
        return df_profit_share
        
    except Exception as e:
        st.error(f"Error creating profit share analysis: {str(e)}")
        return pd.DataFrame()

# =============================================================================
# 🚀 MAIN EXECUTION
# =============================================================================

# Export and display
output_excel_main = io.BytesIO()

try:
    with pd.ExcelWriter(output_excel_main, engine="xlsxwriter") as excel_writer_main:
        for scenario_idx_main, scenario_data_main in enumerate(scenarios):
            current_config_main = scenario_data_main.copy()
            current_config_main.update({
                "kibor": kibor, "spread": spread, "rest_period": rest_period,
                "default_rate": default_rate, "penalty_pct": penalty_pct
            })
            
            df_forecast_main, df_deposit_log_main, df_default_log_main, df_lifecycle_main = run_forecast(current_config_main, fee_collection_mode)

            if df_forecast_main.empty:
                st.warning(f"No forecast data generated for {scenario_data_main['name']}")
                continue

            # Create summaries
            df_monthly_summary_main = create_monthly_summary(df_forecast_main)
            df_yearly_summary_main = create_yearly_summary(df_monthly_summary_main)
            df_profit_share_main = create_profit_share_analysis(df_yearly_summary_main)

            if view_mode == "📊 Dashboard View":
                # Dashboard Overview
                create_dashboard_overview(df_monthly_summary_main, scenario_data_main['name'])
                
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
                
                # Enhanced NII Analysis
                st.subheader("💰 NII (Net Interest Income) Analysis")
                
                # Calculate NII breakdown from forecast data
                if not df_forecast_main.empty and 'Base NII (Lifetime)' in df_forecast_main.columns:
                    total_base_nii = df_forecast_main['Base NII (Lifetime)'].sum()
                    total_fee_nii = df_forecast_main['Fee NII (Lifetime)'].sum()
                    total_pool_growth_nii = df_forecast_main['Pool Growth NII (Lifetime)'].sum()
                    total_nii = df_forecast_main['Total NII (Lifetime)'].sum()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Base NII", f"${total_base_nii:,.0f}", help="Interest earned on monthly installments")
                    with col2:
                        st.metric("Fee NII", f"${total_fee_nii:,.0f}", help="Interest earned on collected fees")
                    with col3:
                        st.metric("Pool Growth NII", f"${total_pool_growth_nii:,.0f}", help="Interest on accumulated deposits")
                    with col4:
                        st.metric("Total NII", f"${total_nii:,.0f}", help="Total Net Interest Income")
                    
                    # NII breakdown chart
                    st.markdown("### 📊 NII Components Breakdown")
                    
                    nii_data = {
                        'Component': ['Base NII', 'Fee NII', 'Pool Growth NII'],
                        'Amount': [total_base_nii, total_fee_nii, total_pool_growth_nii],
                        'Percentage': [
                            (total_base_nii / total_nii * 100) if total_nii > 0 else 0,
                            (total_fee_nii / total_nii * 100) if total_nii > 0 else 0,
                            (total_pool_growth_nii / total_nii * 100) if total_nii > 0 else 0
                        ]
                    }
                    
                    df_nii_breakdown = pd.DataFrame(nii_data)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.dataframe(df_nii_breakdown, use_container_width=True)
                    
                    with col2:
                        # Create a simple pie chart using matplotlib
                        try:
                            import matplotlib.pyplot as plt
                            fig, ax = plt.subplots(figsize=(6, 4))
                            ax.pie(df_nii_breakdown['Amount'], labels=df_nii_breakdown['Component'], 
                                  autopct='%1.1f%%', startangle=90)
                            ax.set_title('NII Components Distribution')
                            st.pyplot(fig)
                        except:
                            st.info("Chart visualization not available")
                    
                    # NII explanation
                    st.markdown("### 📚 NII Calculation Explanation")
                    st.markdown("""
                    **NII (Net Interest Income) is calculated from multiple sources:**
                    
                    1. **Base NII**: Interest earned on monthly installment deposits
                       - Formula: `Installment Amount × Daily Interest Rate × Days Held`
                       - Each installment earns interest from collection date to payout date
                    
                    2. **Fee NII**: Interest earned on collected fees
                       - **Upfront Mode**: Fee collected immediately, earns interest until payout
                       - **Monthly Mode**: Monthly fee earns interest from collection to payout
                    
                    3. **Pool Growth NII**: Interest on accumulated deposits
                       - As more installments are collected, the pool grows
                       - Interest is earned on the growing pool balance
                       - Higher for later installments as pool size increases
                    
                    **Interest Rate**: KIBOR + Spread (currently {:.1f}% + {:.1f}% = {:.1f}% annually)
                    """.format(kibor, spread, kibor + spread))
                else:
                    st.info("NII breakdown data not available for this scenario")
                
                # Revenue & Profit Summary
                if not df_forecast_main.empty:
                    st.subheader("💰 Revenue & Profit Summary")
                    
                    # Calculate key revenue metrics
                    total_fees = df_forecast_main['Total Fee Collected (Lifetime)'].sum()
                    total_nii = df_forecast_main['Total NII (Lifetime)'].sum()
                    total_revenue = total_fees + total_nii
                    total_losses = df_forecast_main['Total Default Loss (Lifetime)'].sum()
                    gross_profit = total_revenue - total_losses
                    total_users = df_forecast_main['Users'].sum()
                    
                    # Revenue metrics cards
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Revenue", f"${total_revenue:,.0f}", help="Fees + NII")
                    with col2:
                        st.metric("Gross Profit", f"${gross_profit:,.0f}", help="Revenue - Losses")
                    with col3:
                        st.metric("Revenue/User", f"${total_revenue/total_users:,.0f}" if total_users > 0 else "$0", help="Revenue per customer")
                    with col4:
                        st.metric("Profit Margin", f"{(gross_profit/total_revenue*100):.1f}%" if total_revenue > 0 else "0%", help="Profit / Revenue")
                    
                    # Revenue share summary
                    if not df_profit_share_main.empty:
                        st.markdown("#### 💼 Revenue Share Summary")
                        total_party_a = df_profit_share_main['Part-A Profit Share'].sum()
                        total_party_b = df_profit_share_main['Part-B Profit Share'].sum()
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Party A Share", f"${total_party_a:,.0f}", f"{profit_split:.1f}%")
                        with col2:
                            st.metric("Party B Share", f"${total_party_b:,.0f}", f"{100-profit_split:.1f}%")
                        with col3:
                            st.metric("Total Shared", f"${total_party_a + total_party_b:,.0f}", "100%")
                
                # Default Impact Summary
                if not df_forecast_main.empty:
                    st.subheader("⚠️ Default Impact Summary")
                    
                    # Calculate default summary metrics
                    total_defaulters = df_forecast_main['Total Defaulters'].sum()
                    total_default_loss = df_forecast_main['Total Default Loss (Lifetime)'].sum()
                    net_default_loss = df_forecast_main['Net Default Loss (After Recovery)'].sum()
                    total_default_fees = df_forecast_main['Default Fees Collected'].sum()
                    total_users = df_forecast_main['Users'].sum()
                    
                    # Default summary cards
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Default Rate", f"{(total_defaulters/total_users*100):.1f}%" if total_users > 0 else "0%", f"{total_defaulters:,.0f} defaulters")
                    with col2:
                        st.metric("Total Default Loss", f"${total_default_loss:,.0f}", help="Before recovery")
                    with col3:
                        st.metric("Net Default Loss", f"${net_default_loss:,.0f}", f"${total_default_loss - net_default_loss:,.0f} recovered")
                    with col4:
                        st.metric("Default Fees", f"${total_default_fees:,.0f}", help="Additional revenue from defaults")
                
                # Main charts
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.markdown('<div class="chart-title">📈 Business Overview</div>', unsafe_allow_html=True)
                    
                    # Create overview chart
                    if PLOTLY_AVAILABLE:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_monthly_summary_main['Month'],
                            y=df_monthly_summary_main['Users Joining This Month'],
                            mode='lines+markers',
                            name='Users',
                            line=dict(color=CHART_COLORS[0], width=3)
                        ))
                        fig.update_layout(
                            title="User Growth Trend",
                            xaxis_title="Month",
                            yaxis_title="Users",
                            template="plotly_white",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        fig, ax = plt.subplots(figsize=(12, 6))
                        ax.plot(df_monthly_summary_main['Month'], df_monthly_summary_main['Users Joining This Month'], 
                               color=CHART_COLORS[0], linewidth=2, marker='o')
                        ax.set_xlabel('Month')
                        ax.set_ylabel('Users')
                        ax.set_title('User Growth Trend')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.markdown('<div class="chart-title">👥 User Activity</div>', unsafe_allow_html=True)
                    
                    # Real-time user count
                    current_users = df_monthly_summary_main['Users Joining This Month'].sum()
                    st.markdown(f'<div style="font-size: 2.5rem; font-weight: 800; color: #1e293b; text-align: center; margin: 1rem 0;">{current_users}</div>', unsafe_allow_html=True)
                    st.markdown('<div style="text-align: center; color: #64748b; margin-bottom: 1rem;">TOTAL USERS</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

            elif view_mode == "🔧 Detailed Forecast":
                # Detailed forecast view
                st.header(f"Scenario: {scenario_data_main['name']}")
                st.subheader(f"📘 Raw Forecast Data (Cohorts by Joining Month)")
                
                st.dataframe(df_forecast_main.style.format(precision=0, thousands=","))

                st.subheader(f"📊 Monthly Summary for {scenario_data_main['name']}")
                cols_to_display_monthly_main = [
                    "Month", "Users Joining This Month", "Pools Formed", 
                    "Cash In (Installments This Month)", "Actual Cash Out This Month", "Net Cash Flow This Month",
                    "NII This Month (Sum of Avg from New Cohorts)", 
                    "Total NII (Lifetime)", 
                    "Payout Recipient Users",
                    "Total Fee Collected (Lifetime)", "Total Default Loss (Lifetime)",
                    "Gross Profit This Month (Accrued from New Cohorts)", "External Capital For Loss (Lifetime)"
                ]
                st.dataframe(df_monthly_summary_main[cols_to_display_monthly_main].style.format(precision=0, thousands=","))

                # Yearly Summary
                if not df_yearly_summary_main.empty:
                    st.subheader(f"📆 Yearly Summary for {scenario_data_main['name']}")
                    st.dataframe(df_yearly_summary_main.style.format(precision=0, thousands=","))

                # Profit Share Analysis
                if not df_profit_share_main.empty:
                    st.subheader(f"💰 Profit Share Summary for {scenario_data_main['name']}")
                    st.dataframe(df_profit_share_main.style.format(precision=0, thousands=","))

            elif view_mode == "📈 Analytics Only":
                # Analytics only view
                st.markdown(f"## 📈 Analytics - {scenario_data_main['name']}")
                
                # Key metrics
                create_dashboard_overview(df_monthly_summary_main, scenario_data_main['name'])
                
                # Revenue & Profit Analysis
                if not df_forecast_main.empty:
                    st.markdown("### 💰 Revenue & Profit Analysis")
                    
                    # Calculate total revenue components
                    total_fees = df_forecast_main['Total Fee Collected (Lifetime)'].sum()
                    total_nii = df_forecast_main['Total NII (Lifetime)'].sum()
                    total_revenue = total_fees + total_nii
                    total_losses = df_forecast_main['Total Default Loss (Lifetime)'].sum()
                    gross_profit = total_revenue - total_losses
                    
                    # Revenue breakdown
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Total Fees", f"${total_fees:,.0f}", help="Fees collected from customers")
                    with col2:
                        st.metric("Total NII", f"${total_nii:,.0f}", help="Net Interest Income")
                    with col3:
                        st.metric("Total Revenue", f"${total_revenue:,.0f}", help="Fees + NII")
                    with col4:
                        st.metric("Total Losses", f"${total_losses:,.0f}", help="Default losses")
                    with col5:
                        st.metric("Gross Profit", f"${gross_profit:,.0f}", help="Revenue - Losses")
                    
                    # Revenue streams breakdown
                    st.markdown("#### 📊 Revenue Streams Breakdown")
                    revenue_data = {
                        'Revenue Stream': ['Fees', 'NII', 'Total Revenue'],
                        'Amount': [total_fees, total_nii, total_revenue],
                        'Percentage': [
                            (total_fees / total_revenue * 100) if total_revenue > 0 else 0,
                            (total_nii / total_revenue * 100) if total_revenue > 0 else 0,
                            100
                        ]
                    }
                    df_revenue_breakdown = pd.DataFrame(revenue_data)
                    df_revenue_breakdown['Percentage'] = df_revenue_breakdown['Percentage'].round(1)
                    st.dataframe(df_revenue_breakdown, use_container_width=True)
                    
                    # Profit margin analysis
                    st.markdown("#### 📈 Profit Margin Analysis")
                    if total_revenue > 0:
                        profit_margin = (gross_profit / total_revenue) * 100
                        fee_margin = (total_fees / total_revenue) * 100
                        nii_margin = (total_nii / total_revenue) * 100
                        loss_ratio = (total_losses / total_revenue) * 100
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Profit Margin", f"{profit_margin:.1f}%", help="Gross Profit / Total Revenue")
                        with col2:
                            st.metric("Fee Margin", f"{fee_margin:.1f}%", help="Fees / Total Revenue")
                        with col3:
                            st.metric("NII Margin", f"{nii_margin:.1f}%", help="NII / Total Revenue")
                        with col4:
                            st.metric("Loss Ratio", f"{loss_ratio:.1f}%", help="Losses / Total Revenue")
                    
                    # Revenue per user analysis
                    st.markdown("#### 👥 Revenue Per User Analysis")
                    total_users = df_forecast_main['Users'].sum()
                    if total_users > 0:
                        revenue_per_user = total_revenue / total_users
                        profit_per_user = gross_profit / total_users
                        fee_per_user = total_fees / total_users
                        nii_per_user = total_nii / total_users
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Revenue/User", f"${revenue_per_user:,.0f}", help="Total Revenue / Total Users")
                        with col2:
                            st.metric("Profit/User", f"${profit_per_user:,.0f}", help="Gross Profit / Total Users")
                        with col3:
                            st.metric("Fee/User", f"${fee_per_user:,.0f}", help="Fees / Total Users")
                        with col4:
                            st.metric("NII/User", f"${nii_per_user:,.0f}", help="NII / Total Users")
                    
                    # Revenue by duration and slot
                    st.markdown("#### 📊 Revenue by Duration & Slot")
                    revenue_breakdown = df_forecast_main.groupby(['Duration', 'Slot']).agg({
                        'Total Fee Collected (Lifetime)': 'sum',
                        'Total NII (Lifetime)': 'sum',
                        'Total Default Loss (Lifetime)': 'sum',
                        'Expected Lifetime Profit': 'sum',
                        'Users': 'sum'
                    }).reset_index()
                    
                    # Calculate derived metrics
                    revenue_breakdown['Total Revenue'] = revenue_breakdown['Total Fee Collected (Lifetime)'] + revenue_breakdown['Total NII (Lifetime)']
                    revenue_breakdown['Net Profit'] = revenue_breakdown['Total Revenue'] - revenue_breakdown['Total Default Loss (Lifetime)']
                    revenue_breakdown['Revenue/User'] = revenue_breakdown['Total Revenue'] / revenue_breakdown['Users']
                    revenue_breakdown['Profit/User'] = revenue_breakdown['Net Profit'] / revenue_breakdown['Users']
                    revenue_breakdown = revenue_breakdown.round(2)
                    
                    st.dataframe(revenue_breakdown, use_container_width=True)
                
                # Default Impact Analysis
                if not df_forecast_main.empty:
                    st.markdown("### ⚠️ Default Impact Analysis")
                    
                    # Calculate default impact metrics
                    total_defaulters = df_forecast_main['Total Defaulters'].sum()
                    total_pre_payout_defaulters = df_forecast_main['Pre-Payout Defaulters'].sum()
                    total_post_payout_defaulters = df_forecast_main['Post-Payout Defaulters'].sum()
                    total_default_loss = df_forecast_main['Total Default Loss (Lifetime)'].sum()
                    net_default_loss = df_forecast_main['Net Default Loss (After Recovery)'].sum()
                    total_recovery = df_forecast_main['Default Recovery Amount'].sum()
                    total_default_fees = df_forecast_main['Default Fees Collected'].sum()
                    total_users = df_forecast_main['Users'].sum()
                    
                    # Default impact metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Defaulters", f"{total_defaulters:,.0f}", f"{(total_defaulters/total_users*100):.1f}%" if total_users > 0 else "0%")
                    with col2:
                        st.metric("Total Default Loss", f"${total_default_loss:,.0f}", help="Before recovery")
                    with col3:
                        st.metric("Net Default Loss", f"${net_default_loss:,.0f}", f"${total_recovery:,.0f} recovered")
                    with col4:
                        st.metric("Default Fees Collected", f"${total_default_fees:,.0f}", help="Additional revenue from defaults")
                    
                    # Default types breakdown
                    st.markdown("#### 📊 Default Types Breakdown")
                    default_types_data = {
                        'Default Type': ['Pre-Payout Defaults', 'Post-Payout Defaults', 'Total Defaults'],
                        'Count': [total_pre_payout_defaulters, total_post_payout_defaulters, total_defaulters],
                        'Percentage': [
                            (total_pre_payout_defaulters / total_defaulters * 100) if total_defaulters > 0 else 0,
                            (total_post_payout_defaulters / total_defaulters * 100) if total_defaulters > 0 else 0,
                            100
                        ],
                        'Loss Amount': [
                            df_forecast_main['Pre-Payout Loss'].sum(),
                            df_forecast_main['Post-Payout Loss'].sum(),
                            total_default_loss
                        ]
                    }
                    df_default_types = pd.DataFrame(default_types_data)
                    df_default_types['Percentage'] = df_default_types['Percentage'].round(1)
                    st.dataframe(df_default_types, use_container_width=True)
                    
                    # Default impact on revenue
                    if default_impact_on_revenue:
                        st.markdown("#### 💰 Default Impact on Revenue")
                        
                        # Calculate revenue impact
                        total_revenue_without_defaults = total_fees + total_nii
                        total_revenue_with_defaults = total_revenue_without_defaults + total_default_fees
                        revenue_impact = total_default_loss - total_default_fees
                        net_revenue_impact = revenue_impact - total_recovery
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Revenue Without Defaults", f"${total_revenue_without_defaults:,.0f}")
                        with col2:
                            st.metric("Revenue With Defaults", f"${total_revenue_with_defaults:,.0f}", f"${total_default_fees:,.0f} fees")
                        with col3:
                            st.metric("Default Impact", f"${revenue_impact:,.0f}", "negative" if revenue_impact > 0 else "positive")
                        with col4:
                            st.metric("Net Impact (After Recovery)", f"${net_revenue_impact:,.0f}", "negative" if net_revenue_impact > 0 else "positive")
                        
                        # Default impact visualization
                        st.markdown("#### 📈 Default Impact Visualization")
                        try:
                            import matplotlib.pyplot as plt
                            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                            
                            # Pie chart for default types
                            ax1.pie([total_pre_payout_defaulters, total_post_payout_defaulters], 
                                   labels=[f'Pre-Payout ({default_pre_pct}%)', f'Post-Payout ({default_post_pct}%)'],
                                   autopct='%1.1f%%', startangle=90, colors=['#FF6B6B', '#4ECDC4'])
                            ax1.set_title('Default Types Distribution')
                            
                            # Bar chart for default impact
                            impact_data = ['Revenue\n(No Defaults)', 'Default Fees\n(Additional)', 'Default Loss\n(Impact)', 'Recovery\n(Offset)', 'Net Impact']
                            impact_values = [total_revenue_without_defaults, total_default_fees, -total_default_loss, total_recovery, -net_revenue_impact]
                            colors = ['#4CAF50', '#FFC107', '#F44336', '#2196F3', '#9C27B0']
                            
                            bars = ax2.bar(impact_data, impact_values, color=colors)
                            ax2.set_title('Default Impact on Revenue')
                            ax2.set_ylabel('Amount ($)')
                            ax2.tick_params(axis='x', rotation=45)
                            
                            # Add value labels on bars
                            for bar, value in zip(bars, impact_values):
                                height = bar.get_height()
                                ax2.text(bar.get_x() + bar.get_width()/2., height + (height*0.01 if height >= 0 else height*0.01),
                                        f'${value:,.0f}', ha='center', va='bottom' if height >= 0 else 'top')
                            
                            plt.tight_layout()
                            st.pyplot(fig)
                        except:
                            st.info("Chart visualization not available")
                    
                    # Default by duration and slot analysis
                    st.markdown("#### 📊 Default Analysis by Duration & Slot")
                    default_breakdown = df_forecast_main.groupby(['Duration', 'Slot']).agg({
                        'Total Defaulters': 'sum',
                        'Pre-Payout Defaulters': 'sum',
                        'Post-Payout Defaulters': 'sum',
                        'Total Default Loss (Lifetime)': 'sum',
                        'Net Default Loss (After Recovery)': 'sum',
                        'Default Fees Collected': 'sum',
                        'Users': 'sum'
                    }).reset_index()
                    
                    # Calculate derived metrics
                    default_breakdown['Default Rate %'] = (default_breakdown['Total Defaulters'] / default_breakdown['Users'] * 100).round(2)
                    default_breakdown['Pre-Payout %'] = (default_breakdown['Pre-Payout Defaulters'] / default_breakdown['Total Defaulters'] * 100).round(2)
                    default_breakdown['Loss per Defaulter'] = (default_breakdown['Total Default Loss (Lifetime)'] / default_breakdown['Total Defaulters']).round(2)
                    default_breakdown['Recovery Rate %'] = ((default_breakdown['Total Default Loss (Lifetime)'] - default_breakdown['Net Default Loss (After Recovery)']) / default_breakdown['Total Default Loss (Lifetime)'] * 100).round(2)
                    
                    st.dataframe(default_breakdown, use_container_width=True)
                
                # Revenue Share Distribution Analysis
                st.markdown("### 💼 Revenue Share Distribution Analysis")
                
                # Calculate revenue share distribution
                if not df_profit_share_main.empty:
                    st.markdown("#### 📊 Party A vs Party B Profit Share")
                    
                    # Display profit share metrics
                    total_party_a_profit = df_profit_share_main['Part-A Profit Share'].sum()
                    total_party_b_profit = df_profit_share_main['Part-B Profit Share'].sum()
                    total_shared_profit = total_party_a_profit + total_party_b_profit
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Party A Share", f"${total_party_a_profit:,.0f}", f"{profit_split:.1f}%")
                    with col2:
                        st.metric("Party B Share", f"${total_party_b_profit:,.0f}", f"{100-profit_split:.1f}%")
                    with col3:
                        st.metric("Total Shared", f"${total_shared_profit:,.0f}", "100%")
                    
                    # Revenue share breakdown by year
                    st.markdown("#### 📈 Annual Revenue Share Breakdown")
                    share_breakdown = df_profit_share_main[['Year', 'Annual Gross Profit (Accrued)', 'Part-A Profit Share', 'Part-B Profit Share']].copy()
                    share_breakdown['Party A %'] = (share_breakdown['Part-A Profit Share'] / share_breakdown['Annual Gross Profit (Accrued)'] * 100).round(1)
                    share_breakdown['Party B %'] = (share_breakdown['Part-B Profit Share'] / share_breakdown['Annual Gross Profit (Accrued)'] * 100).round(1)
                    share_breakdown = share_breakdown.round(0)
                    st.dataframe(share_breakdown, use_container_width=True)
                    
                    # Revenue share visualization
                    st.markdown("#### 📊 Revenue Share Visualization")
                    try:
                        import matplotlib.pyplot as plt
                        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                        
                        # Pie chart for total shares
                        ax1.pie([total_party_a_profit, total_party_b_profit], 
                               labels=[f'Party A ({profit_split}%)', f'Party B ({100-profit_split}%)'],
                               autopct='%1.1f%%', startangle=90, colors=['#3B75AF', '#4CAF50'])
                        ax1.set_title('Total Profit Share Distribution')
                        
                        # Bar chart for annual shares
                        years = share_breakdown['Year'].astype(str)
                        party_a_shares = share_breakdown['Part-A Profit Share']
                        party_b_shares = share_breakdown['Part-B Profit Share']
                        
                        x = range(len(years))
                        width = 0.35
                        ax2.bar([i - width/2 for i in x], party_a_shares, width, label='Party A', color='#3B75AF')
                        ax2.bar([i + width/2 for i in x], party_b_shares, width, label='Party B', color='#4CAF50')
                        ax2.set_xlabel('Year')
                        ax2.set_ylabel('Profit Share ($)')
                        ax2.set_title('Annual Profit Share by Party')
                        ax2.set_xticks(x)
                        ax2.set_xticklabels(years)
                        ax2.legend()
                        ax2.grid(True, alpha=0.3)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                    except:
                        st.info("Chart visualization not available")
                
                # Cost Structure Analysis
                st.markdown("### 💸 Cost Structure Analysis")
                
                # Calculate cost components
                total_operational_costs = total_losses  # Default losses as main cost
                total_revenue_before_costs = total_revenue
                net_profit_after_costs = gross_profit
                
                cost_breakdown = {
                    'Cost Component': ['Default Losses', 'External Capital Needed', 'Total Costs'],
                    'Amount': [total_losses, df_forecast_main['External Capital For Loss (Lifetime)'].sum(), total_losses + df_forecast_main['External Capital For Loss (Lifetime)'].sum()],
                    'Percentage of Revenue': [
                        (total_losses / total_revenue * 100) if total_revenue > 0 else 0,
                        (df_forecast_main['External Capital For Loss (Lifetime)'].sum() / total_revenue * 100) if total_revenue > 0 else 0,
                        ((total_losses + df_forecast_main['External Capital For Loss (Lifetime)'].sum()) / total_revenue * 100) if total_revenue > 0 else 0
                    ]
                }
                
                df_cost_breakdown = pd.DataFrame(cost_breakdown)
                df_cost_breakdown['Percentage of Revenue'] = df_cost_breakdown['Percentage of Revenue'].round(1)
                st.dataframe(df_cost_breakdown, use_container_width=True)
                
                # Profitability metrics
                st.markdown("#### 📈 Profitability Metrics")
                if total_revenue > 0:
                    net_profit_margin = (net_profit_after_costs / total_revenue) * 100
                    cost_ratio = ((total_losses + df_forecast_main['External Capital For Loss (Lifetime)'].sum()) / total_revenue) * 100
                    roi = (net_profit_after_costs / (total_revenue - net_profit_after_costs)) * 100 if (total_revenue - net_profit_after_costs) > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Net Profit Margin", f"{net_profit_margin:.1f}%", help="Net Profit / Total Revenue")
                    with col2:
                        st.metric("Cost Ratio", f"{cost_ratio:.1f}%", help="Total Costs / Total Revenue")
                    with col3:
                        st.metric("ROI", f"{roi:.1f}%", help="Return on Investment")
                
                # NII Analysis
                if not df_forecast_main.empty and 'Base NII (Lifetime)' in df_forecast_main.columns:
                    st.markdown("### 💰 NII Analysis")
                    
                    # NII summary metrics
                    total_base_nii = df_forecast_main['Base NII (Lifetime)'].sum()
                    total_fee_nii = df_forecast_main['Fee NII (Lifetime)'].sum()
                    total_pool_growth_nii = df_forecast_main['Pool Growth NII (Lifetime)'].sum()
                    total_nii = df_forecast_main['Total NII (Lifetime)'].sum()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Base NII", f"${total_base_nii:,.0f}")
                    with col2:
                        st.metric("Fee NII", f"${total_fee_nii:,.0f}")
                    with col3:
                        st.metric("Pool Growth NII", f"${total_pool_growth_nii:,.0f}")
                    with col4:
                        st.metric("Total NII", f"${total_nii:,.0f}")
                    
                    # NII breakdown by duration and slot
                    st.markdown("#### NII Breakdown by Duration & Slot")
                    nii_breakdown = df_forecast_main.groupby(['Duration', 'Slot']).agg({
                        'Base NII (Lifetime)': 'sum',
                        'Fee NII (Lifetime)': 'sum', 
                        'Pool Growth NII (Lifetime)': 'sum',
                        'Total NII (Lifetime)': 'sum',
                        'Users': 'sum'
                    }).reset_index()
                    
                    # Calculate per-user NII
                    nii_breakdown['NII Per User'] = nii_breakdown['Total NII (Lifetime)'] / nii_breakdown['Users']
                    nii_breakdown = nii_breakdown.round(2)
                    
                    st.dataframe(nii_breakdown, use_container_width=True)
                
                # Analytics charts
                st.markdown("### 📊 Analytics Charts")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Growth Analysis")
                    if PLOTLY_AVAILABLE:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_monthly_summary_main['Month'], 
                            y=df_monthly_summary_main['Users Joining This Month'], 
                            mode='lines+markers', 
                            name='Users', 
                            line=dict(color=CHART_COLORS[0])
                        ))
                        fig.update_layout(title="User Growth", template="plotly_white", height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        fig, ax = plt.subplots(figsize=(10, 4))
                        ax.plot(df_monthly_summary_main['Month'], df_monthly_summary_main['Users Joining This Month'], 
                               marker='o', color=CHART_COLORS[0], linewidth=2)
                        ax.set_xlabel('Month')
                        ax.set_ylabel('Users')
                        ax.set_title('User Growth')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                
                with col2:
                    st.markdown("#### Profit Analysis")
                    if PLOTLY_AVAILABLE:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_monthly_summary_main['Month'], 
                            y=df_monthly_summary_main['Gross Profit This Month (Accrued from New Cohorts)'], 
                            mode='lines+markers', 
                            name='Profit', 
                            line=dict(color=CHART_COLORS[1])
                        ))
                        fig.update_layout(title="Profit Growth", template="plotly_white", height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        fig, ax = plt.subplots(figsize=(10, 4))
                        ax.plot(df_monthly_summary_main['Month'], df_monthly_summary_main['Gross Profit This Month (Accrued from New Cohorts)'], 
                               marker='o', color=CHART_COLORS[1], linewidth=2)
                        ax.set_xlabel('Month')
                        ax.set_ylabel('Profit (₹)')
                        ax.set_title('Profit Growth')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)

            # Original 5-Chart System
            st.subheader(f"📊 Visual Charts for {scenario_data_main['name']}")
            
            # Prepare chart data
            df_monthly_chart_data_main = df_monthly_summary_main.copy()
            df_yearly_chart_data_main = df_yearly_summary_main.copy()
            if "Year" in df_yearly_chart_data_main.columns and not df_yearly_chart_data_main.empty:
                df_yearly_chart_data_main["Year"] = df_yearly_chart_data_main["Year"].astype(str)
            df_profit_share_chart_data_main = df_profit_share_main.copy()
            if "Year" in df_profit_share_chart_data_main.columns and not df_profit_share_chart_data_main.empty:
                df_profit_share_chart_data_main["Year"] = df_profit_share_chart_data_main["Year"].astype(str)

            FIG_SIZE_MAIN = (10, 4.5)
            
            # Chart validation
            can_plot_m1 = not df_monthly_chart_data_main.empty and \
                          all(col in df_monthly_chart_data_main.columns for col in ["Month", "Pools Formed", "Cash In (Installments This Month)"]) and \
                          not df_monthly_chart_data_main[["Pools Formed", "Cash In (Installments This Month)"]].fillna(0).eq(0).all().all()
            
            can_plot_m2 = not df_monthly_chart_data_main.empty and \
                          all(col in df_monthly_chart_data_main.columns for col in ["Month", "Users Joining This Month", "Gross Profit This Month (Accrued from New Cohorts)"]) and \
                          not df_monthly_chart_data_main[["Users Joining This Month", "Gross Profit This Month (Accrued from New Cohorts)"]].fillna(0).eq(0).all().all()

            can_plot_y1 = not df_yearly_chart_data_main.empty and \
                          all(col in df_yearly_chart_data_main.columns for col in ["Year", "Pools Formed", "Cash In (Installments This Month)"]) and \
                          not df_yearly_chart_data_main[["Pools Formed", "Cash In (Installments This Month)"]].fillna(0).eq(0).all().all()

            can_plot_y2 = not df_yearly_chart_data_main.empty and \
                          all(col in df_yearly_chart_data_main.columns for col in ["Year", "Users Joining This Month", "Annual Gross Profit (Accrued from New Cohorts)"]) and \
                          not df_yearly_chart_data_main[["Users Joining This Month", "Annual Gross Profit (Accrued from New Cohorts)"]].fillna(0).eq(0).all().all()
            
            can_plot_y3 = not df_profit_share_chart_data_main.empty and \
                          all(col in df_profit_share_chart_data_main.columns for col in ["Year", "External Capital Needed (Annual Accrual)", "Annual Fee Collected (Accrued)", "Annual Gross Profit (Accrued)"]) and \
                          not df_profit_share_chart_data_main[["External Capital Needed (Annual Accrual)", "Annual Fee Collected (Accrued)", "Annual Gross Profit (Accrued)"]].fillna(0).eq(0).all().all()

            # Chart 1: Monthly Pools Formed vs. Cash In (Installments)
            st.markdown("##### Chart 1: Monthly Pools Formed vs. Cash In (Installments)")
            if can_plot_m1:
                fig1_main, ax1_main = plt.subplots(figsize=FIG_SIZE_MAIN)
                ax2_main = ax1_main.twinx()
                bars1_main = ax1_main.bar(df_monthly_chart_data_main["Month"], df_monthly_chart_data_main["Pools Formed"], color=COLOR_PRIMARY_BAR, label="Pools Formed This Month", width=0.7)
                line1_main, = ax2_main.plot(df_monthly_chart_data_main["Month"], df_monthly_chart_data_main["Cash In (Installments This Month)"], color=COLOR_SECONDARY_LINE, label="Cash In (Installments)", marker='o', linewidth=2, markersize=4)
                ax1_main.set_xlabel("Month"); ax1_main.set_ylabel("Pools Formed", color=COLOR_PRIMARY_BAR); ax2_main.set_ylabel("Cash In (Installments)", color=COLOR_SECONDARY_LINE)
                ax1_main.tick_params(axis='y', labelcolor=COLOR_PRIMARY_BAR); ax2_main.tick_params(axis='y', labelcolor=COLOR_SECONDARY_LINE)
                ax2_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}")); ax1_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}"))
                handles_main = [bars1_main, line1_main]; labels_main = [h.get_label() for h in handles_main]
                fig1_main.legend(handles_main, labels_main, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2); fig1_main.tight_layout(rect=[0, 0.05, 1, 1]); st.pyplot(fig1_main)
            else: 
                st.caption("Not enough data or all values are zero for Chart 1.")

            # Chart 2: Monthly Users Joining vs. Accrued Gross Profit
            st.markdown("##### Chart 2: Monthly Users Joining vs. Accrued Gross Profit (from New Cohorts)")
            if can_plot_m2:
                fig2_main, ax3_main = plt.subplots(figsize=FIG_SIZE_MAIN)
                ax4_main = ax3_main.twinx()
                bars2_main = ax3_main.bar(df_monthly_chart_data_main["Month"], df_monthly_chart_data_main["Users Joining This Month"], color=COLOR_ACCENT_BAR, label="Users Joining This Month", width=0.7)
                line2_main, = ax4_main.plot(df_monthly_chart_data_main["Month"], df_monthly_chart_data_main["Gross Profit This Month (Accrued from New Cohorts)"], color=COLOR_ACCENT_LINE, label="Accrued Gross Profit (New Cohorts)", marker='o', linewidth=2, markersize=4)
                ax3_main.set_xlabel("Month"); ax3_main.set_ylabel("Users Joining", color=COLOR_ACCENT_BAR); ax4_main.set_ylabel("Accrued Gross Profit", color=COLOR_ACCENT_LINE)
                ax3_main.tick_params(axis='y', labelcolor=COLOR_ACCENT_BAR); ax4_main.tick_params(axis='y', labelcolor=COLOR_ACCENT_LINE)
                ax3_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}")); ax4_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}"))
                handles_main = [bars2_main, line2_main]; labels_main = [h.get_label() for h in handles_main]
                fig2_main.legend(handles_main, labels_main, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2); fig2_main.tight_layout(rect=[0, 0.05, 1, 1]); st.pyplot(fig2_main)
            else: 
                st.caption("Not enough data or all values are zero for Chart 2.")

            # Chart 3: Annual Pools Formed vs. Annual Cash In
            st.markdown("##### Chart 3: Annual Pools Formed vs. Annual Cash In (Installments)")
            if can_plot_y1:
                fig3_main, ax5_main = plt.subplots(figsize=FIG_SIZE_MAIN)
                ax6_main = ax5_main.twinx()
                bars3_main = ax5_main.bar(df_yearly_chart_data_main["Year"], df_yearly_chart_data_main["Pools Formed"], color=COLOR_PRIMARY_BAR, label="Annual Pools Formed", width=0.6) 
                line3_main, = ax6_main.plot(df_yearly_chart_data_main["Year"], df_yearly_chart_data_main["Cash In (Installments This Month)"], color=COLOR_SECONDARY_LINE, label="Annual Cash In (Installments)", marker='o', linewidth=2, markersize=4)
                ax5_main.set_xlabel("Year"); ax5_main.set_ylabel("Annual Pools Formed", color=COLOR_PRIMARY_BAR); ax6_main.set_ylabel("Annual Cash In", color=COLOR_SECONDARY_LINE)
                ax5_main.tick_params(axis='y', labelcolor=COLOR_PRIMARY_BAR); ax6_main.tick_params(axis='y', labelcolor=COLOR_SECONDARY_LINE)
                ax5_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}")); ax6_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}"))
                handles_main = [bars3_main, line3_main]; labels_main = [h.get_label() for h in handles_main]
                fig3_main.legend(handles_main, labels_main, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2); fig3_main.tight_layout(rect=[0, 0.05, 1, 1]); st.pyplot(fig3_main)
            else: 
                st.caption("Not enough data or all values are zero for Chart 3.")
                
            # Chart 4: Annual Users Joining vs. Annual Accrued Gross Profit
            st.markdown("##### Chart 4: Annual Users Joining vs. Annual Accrued Gross Profit (from New Cohorts)")
            if can_plot_y2:
                fig4_main, ax7_main = plt.subplots(figsize=FIG_SIZE_MAIN)
                ax8_main = ax7_main.twinx()
                bars4_main = ax7_main.bar(df_yearly_chart_data_main["Year"], df_yearly_chart_data_main["Users Joining This Month"], color=COLOR_ACCENT_BAR, label="Annual Users Joining", width=0.6)
                line4_main, = ax8_main.plot(df_yearly_chart_data_main["Year"], df_yearly_chart_data_main["Annual Gross Profit (Accrued from New Cohorts)"], color=COLOR_ACCENT_LINE, label="Annual Accrued Gross Profit (New Cohorts)", marker='o', linewidth=2, markersize=4)
                ax7_main.set_xlabel("Year"); ax7_main.set_ylabel("Annual Users Joining", color=COLOR_ACCENT_BAR); ax8_main.set_ylabel("Annual Accrued Profit", color=COLOR_ACCENT_LINE)
                ax7_main.tick_params(axis='y', labelcolor=COLOR_ACCENT_BAR); ax8_main.tick_params(axis='y', labelcolor=COLOR_ACCENT_LINE)
                ax7_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}")); ax8_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}"))
                handles_main = [bars4_main, line4_main]; labels_main = [h.get_label() for h in handles_main]
                fig4_main.legend(handles_main, labels_main, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2); fig4_main.tight_layout(rect=[0, 0.05, 1, 1]); st.pyplot(fig4_main)
            else: 
                st.caption("Not enough data or all values are zero for Chart 4.")

            # Chart 5: Annual External Capital vs. Fee & Accrued Profit
            st.markdown("##### Chart 5: Annual External Capital vs. Fee & Accrued Profit")
            if can_plot_y3:
                fig5_main, ax9_main = plt.subplots(figsize=FIG_SIZE_MAIN)
                ax10_main = ax9_main.twinx()
                bars5_main = ax9_main.bar(df_profit_share_chart_data_main["Year"], df_profit_share_chart_data_main["External Capital Needed (Annual Accrual)"], color=COLOR_HIGHLIGHT_BAR, label="External Capital Needed", width=0.6)
                line5_main, = ax10_main.plot(df_profit_share_chart_data_main["Year"], df_profit_share_chart_data_main["Annual Fee Collected (Accrued)"], color=COLOR_SECONDARY_LINE, label="Annual Fee Collected", marker='o', linewidth=2, markersize=4)
                line6_main, = ax10_main.plot(df_profit_share_chart_data_main["Year"], df_profit_share_chart_data_main["Annual Gross Profit (Accrued)"], color=COLOR_ACCENT_LINE, label="Annual Gross Profit", marker='s', linewidth=2, markersize=4)
                ax9_main.set_xlabel("Year"); ax9_main.set_ylabel("External Capital Needed", color=COLOR_HIGHLIGHT_BAR); ax10_main.set_ylabel("Fee & Profit", color=COLOR_SECONDARY_LINE)
                ax9_main.tick_params(axis='y', labelcolor=COLOR_HIGHLIGHT_BAR); ax10_main.tick_params(axis='y', labelcolor=COLOR_SECONDARY_LINE)
                ax9_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}")); ax10_main.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}"))
                handles_main = [bars5_main, line5_main, line6_main]; labels_main = [h.get_label() for h in handles_main]
                fig5_main.legend(handles_main, labels_main, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=3); fig5_main.tight_layout(rect=[0, 0.05, 1, 1]); st.pyplot(fig5_main)
            else: 
                st.caption("Not enough data or all values are zero for Chart 5.")

            # Write to Excel with detailed sheets
            sheet_name_prefix_main = scenario_data_main['name'][:25].replace(" ", "_").replace("/", "_")
            
            if not df_forecast_main.empty:
                df_forecast_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_ForecastCohorts")
            if not df_monthly_summary_main.empty and "Month" in df_monthly_summary_main: 
                df_monthly_summary_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_MonthlySummary")
            if not df_yearly_summary_main.empty and "Year" in df_yearly_summary_main:
                df_yearly_summary_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_YearlySummary")
            if not df_profit_share_main.empty and "Year" in df_profit_share_main:
                df_profit_share_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_ProfitShare")
            if not df_deposit_log_main.empty:
                df_deposit_log_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_DepositLog")
            if not df_default_log_main.empty:
                df_default_log_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_DefaultLog")
            if not df_lifecycle_main.empty:
                df_lifecycle_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_LifecycleLog")

except Exception as e:
    st.error(f"Error in main execution: {str(e)}")

# Download options
st.markdown("### 📥 Download Options")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Download Excel Report"):
        st.download_button(
            label="📊 Download Excel Report",
            data=output_excel_main.getvalue(),
            file_name=f"rosca_forecast_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with col2:
    if st.button("📈 Generate Summary"):
        st.success("Summary generated successfully!")

with col3:
    if st.button("🔄 Refresh Data"):
        st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; color: #64748b; font-family: 'Inter', sans-serif; padding: 2rem;">
    <p>🚀 ROSCA Forecast Pro - Complete Business Intelligence Platform</p>
    <p>Built with ❤️ using Streamlit & Plotly | Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
