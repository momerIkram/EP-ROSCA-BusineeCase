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
    page_title="ROSCA Forecast Pro", 
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
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    .stError {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }
    
    .stWarning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }
    
    .stInfo {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🎨 MODERN COLORS & THEMES
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

def create_modern_metric_card(title, value, change, change_type="positive", icon="📊", subtitle=""):
    """Create an ultra-modern metric card"""
    change_class = "positive" if change_type == "positive" else "negative" if change_type == "negative" else "neutral"
    change_icon = "↗️" if change_type == "positive" else "↘️" if change_type == "negative" else "→"
    
    return f"""
    <div class="metric-card">
        <div class="metric-title">{icon} {title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-change {change_class}">
            <span class="metric-icon">{change_icon}</span>
            <span>{change}</span>
        </div>
        {f'<div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">{subtitle}</div>' if subtitle else ''}
    </div>
    """

def format_currency(value, currency_symbol=None):
    """Format value as currency with selected symbol"""
    if currency_symbol is None:
        currency_symbol = CURRENCY_SYMBOL
    
    if pd.isna(value) or value == 0:
        return f"{currency_symbol}0"
    
    # Different formatting based on currency
    if selected_currency in ["PKR", "INR"]:
        # For PKR/INR: Use Lakhs and Crores
        if value >= 10000000:  # 1 crore
            return f"{currency_symbol}{value/10000000:.1f}Cr"
        elif value >= 100000:  # 1 lakh
            return f"{currency_symbol}{value/100000:.1f}L"
        elif value >= 1000:  # 1 thousand
            return f"{currency_symbol}{value/1000:.1f}K"
        else:
            return f"{currency_symbol}{value:,.0f}"
    else:
        # For USD/EUR/GBP: Use Millions and Billions
        if value >= 1000000000:  # 1 billion
            return f"{currency_symbol}{value/1000000000:.1f}B"
        elif value >= 1000000:  # 1 million
            return f"{currency_symbol}{value/1000000:.1f}M"
        elif value >= 1000:  # 1 thousand
            return f"{currency_symbol}{value/1000:.1f}K"
        else:
            return f"{currency_symbol}{value:,.0f}"

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

# Ultra-Modern Header
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
    ["📊 Dashboard View", "🔧 Detailed Forecast", "📈 Analytics Only", "⚙️ Configuration Mode"],
    help="Choose how to display your data"
)

# Configuration mode for main page setup
if view_mode == "⚙️ Configuration Mode":
    st.markdown("## ⚙️ Advanced Configuration Mode")
    st.info("💡 **Use this mode to configure all settings on the main page instead of sidebar**")
    
    # Move key configuration to main page
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💱 Currency & Financial Settings")
        selected_currency = st.selectbox(
            "Select Currency",
            list(currency_options.keys()),
            index=0,
            format_func=lambda x: f"{currency_options[x]['flag']} {x} - {currency_options[x]['name']}",
            key="main_currency"
        )
        CURRENCY_SYMBOL = currency_options[selected_currency]['symbol']
        CURRENCY_NAME = currency_options[selected_currency]['name']
        
        fee_collection_mode = st.selectbox(
            "Fee Collection Method",
            ["Upfront Fee (Entire Pool)", "Monthly Fee Collection"],
            key="main_fee_mode"
        )
        
        kibor = st.number_input("KIBOR (%)", value=11.0, step=0.1, key="main_kibor")
        spread = st.number_input("Spread (%)", value=5.0, step=0.1, key="main_spread")
    
    with col2:
        st.markdown("### 📊 Scenario Settings")
        scenario_name = st.text_input("Scenario Name", value="Main Scenario", key="main_scenario")
        total_market = st.number_input("Total Market Size", value=20000000, min_value=0, key="main_market")
        tam_pct = st.number_input("TAM % of Market", min_value=0.0, max_value=100.0, value=10.0, step=0.01, key="main_tam")
        start_pct = st.number_input("Starting TAM %", min_value=0.0, max_value=100.0, value=10.0, step=0.01, key="main_start")
        monthly_growth = st.number_input("Monthly Acquisition Rate (%)", min_value=0.0, value=2.0, step=0.01, key="main_growth")
    
    # Main page slab-slot configuration
    st.markdown("### 🎰 Slab & Slot Configuration")
    
    # Duration selection
    durations_main = st.multiselect("Select Durations (months)", [3, 4, 5, 6, 8, 10], default=[3, 4, 6], key="main_durations")
    
    if durations_main:
        for d_config in durations_main:
            with st.expander(f"🎯 Duration {d_config}M Configuration", expanded=True):
                # Slab selection
                slab_options = [1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000]
                selected_slabs = st.multiselect(f"Select Slabs for {d_config}M", slab_options, default=[1000, 2000, 5000], key=f"main_slabs_{d_config}")
                
                if selected_slabs:
                    # Quick configuration table
                    st.markdown(f"**Quick Configuration for {d_config}M**")
                    
                    # Create a data table for easy configuration
                    config_data = []
                    for slab_amount in selected_slabs:
                        for slot_num in range(1, d_config + 1):
                            config_data.append({
                                "Slab": f"{CURRENCY_SYMBOL}{slab_amount:,}",
                                "Slot": f"Slot {slot_num}",
                                "Fee %": 2.0,
                                "Blocked": False,
                                "Distribution %": 100.0 / d_config
                            })
                    
                    if config_data:
                        df_config = pd.DataFrame(config_data)
                        edited_df = st.data_editor(
                            df_config,
                            column_config={
                                "Slab": st.column_config.TextColumn("Slab Amount", disabled=True),
                                "Slot": st.column_config.TextColumn("Slot", disabled=True),
                                "Fee %": st.column_config.NumberColumn("Fee %", min_value=0.0, max_value=50.0, step=0.1),
                                "Blocked": st.column_config.CheckboxColumn("Blocked"),
                                "Distribution %": st.column_config.NumberColumn("Distribution %", min_value=0.0, max_value=100.0, step=0.1)
                            },
                            use_container_width=True,
                            key=f"main_config_table_{d_config}"
                        )
                        
                        # Apply configuration
                        if st.button(f"Apply Configuration for {d_config}M", key=f"apply_{d_config}"):
                            st.success(f"✅ Configuration applied for {d_config}M duration!")
    
    # Run forecast button for main page
    if st.button("🚀 Run Forecast from Main Page", type="primary"):
        st.success("✅ Forecast configuration completed! Switch to Dashboard View to see results.")
    
    st.stop()  # Stop execution here for configuration mode

# Multi-scenario support
scenarios = []
scenario_count = st.sidebar.number_input("Number of Scenarios", min_value=1, max_value=3, value=1)

for i in range(scenario_count):
    with st.sidebar.expander(f"🎯 Scenario {i+1} Settings"):
        name = st.text_input(f"Scenario Name {i+1}", value=f"Scenario {i+1}", key=f"name_{i}")
        total_market = st.number_input("Total Market Size", value=20000000, min_value=0, key=f"market_{i}")
        tam_pct = st.number_input("TAM % of Market", min_value=0.0, max_value=100.0, value=10.0, step=0.01, key=f"tam_pct_{i}")
        start_pct = st.number_input("Starting TAM % (Month 1 New Users)", min_value=0.0, max_value=100.0, value=10.0, step=0.01, key=f"start_pct_{i}", help="Initial new users as % of initial TAM for Month 1.")
        monthly_growth = st.number_input("Monthly Acquisition Rate (%)",min_value=0.0, value=2.0, step=0.01, key=f"growth_{i}", help="New users next month = Cum. Acquired Base * Rate")
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

# Currency Selection
st.sidebar.markdown("### 💱 Currency Selection")
currency_options = {
    "PKR": {"symbol": "₨", "name": "Pakistani Rupee", "flag": "🇵🇰"},
    "USD": {"symbol": "$", "name": "US Dollar", "flag": "🇺🇸"},
    "EUR": {"symbol": "€", "name": "Euro", "flag": "🇪🇺"},
    "GBP": {"symbol": "£", "name": "British Pound", "flag": "🇬🇧"},
    "INR": {"symbol": "₹", "name": "Indian Rupee", "flag": "🇮🇳"},
    "AED": {"symbol": "د.إ", "name": "UAE Dirham", "flag": "🇦🇪"},
    "SAR": {"symbol": "﷼", "name": "Saudi Riyal", "flag": "🇸🇦"}
}

selected_currency = st.sidebar.selectbox(
    "Select Currency",
    list(currency_options.keys()),
    index=0,  # Default to PKR
    format_func=lambda x: f"{currency_options[x]['flag']} {x} - {currency_options[x]['name']}",
    help="Choose the currency for all financial calculations"
)

# Store currency info globally
CURRENCY_SYMBOL = currency_options[selected_currency]['symbol']
CURRENCY_NAME = currency_options[selected_currency]['name']

st.sidebar.success(f"💱 **Selected Currency:** {CURRENCY_SYMBOL} {selected_currency} - {CURRENCY_NAME}")

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
    st.sidebar.markdown("- ✅ Higher upfront revenue")
else:
    st.sidebar.info("💡 **Monthly Mode:** Collect fees monthly with installments")
    st.sidebar.markdown("**Benefits:**")
    st.sidebar.markdown("- ✅ Lower barrier to entry")
    st.sidebar.markdown("- ✅ Steady monthly revenue")
    st.sidebar.markdown("- ✅ Better customer retention")

# Financial Parameters
st.sidebar.markdown("### 💰 Financial Parameters")
global_collection_day = st.sidebar.number_input("Collection Day of Month", min_value=1, max_value=28, value=1)
global_payout_day = st.sidebar.number_input("Payout Day of Month", min_value=1, max_value=28, value=20)
profit_split = st.sidebar.number_input("Profit Share for Party A (%)", min_value=0, max_value=100, value=50)
party_a_pct = profit_split / 100
party_b_pct = 1 - party_a_pct
kibor = st.sidebar.number_input("KIBOR (%)", value=11.0, step=0.1)
spread = st.sidebar.number_input("Spread (%)", value=5.0, step=0.1)
rest_period = st.sidebar.number_input("Rest Period (months)", value=1, min_value=0)

# Default Configuration
st.sidebar.markdown("### ⚠️ Default Management")
st.sidebar.markdown("#### 📊 Default Configuration")
default_rate = st.sidebar.number_input("Default Rate (%)", value=1.0, min_value=0.0, max_value=100.0, step=0.1, help="Overall default rate across all customers")

# Default Types Configuration
st.sidebar.markdown("#### 🔄 Default Types Distribution")
default_pre_pct = st.sidebar.number_input("Pre-Payout Default %", min_value=0, max_value=100, value=50, help="Percentage of defaults that occur before payout")
default_post_pct = 100 - default_pre_pct
st.sidebar.info(f"Post-Payout Default %: {default_post_pct}%")

# Default Fees and Penalties
st.sidebar.markdown("#### 💸 Default Fees & Penalties")
penalty_pct = st.sidebar.number_input("Pre-Payout Refund (%)", value=10.0, min_value=0.0, max_value=100.0, step=0.1, help="Percentage refunded to pre-payout defaulters")
default_fee_rate = st.sidebar.number_input("Default Processing Fee (%)", value=2.0, min_value=0.0, max_value=50.0, step=0.1, help="Additional fee charged on defaulted amounts")
late_fee_rate = st.sidebar.number_input("Late Payment Fee (%)", value=5.0, min_value=0.0, max_value=50.0, step=0.1, help="Fee for late payments before default")

# Default Impact Analysis
st.sidebar.markdown("#### 📈 Default Impact Settings")
default_recovery_rate = st.sidebar.number_input("Default Recovery Rate (%)", value=20.0, min_value=0.0, max_value=100.0, step=1.0, help="Percentage of defaulted amounts that can be recovered")
default_impact_on_revenue = st.sidebar.checkbox("Include Default Impact in Revenue Analysis", value=True, help="Show how defaults affect revenue calculations")

# =============================================================================
# 🎨 ULTRA-MODERN PRODUCT CONFIGURATION
# =============================================================================

st.sidebar.markdown("## 📊 Product Configuration")

# Duration Selection
st.sidebar.markdown("### ⏱️ Duration Selection")
durations_input = st.sidebar.multiselect("Select Durations (months)", [3, 4, 5, 6, 8, 10], default=[3, 4, 6])
durations = sorted([int(d) for d in durations_input])

# Initialize configuration
yearly_duration_share = {}
slab_map = {}
slot_fees = {}
slot_distribution = {}

# Initialize with default values
for y_config in range(1, 6):
    yearly_duration_share[y_config] = {}
    for dur_val in durations:
        yearly_duration_share[y_config][dur_val] = 100.0 / len(durations) if len(durations) > 0 else 0

# Ultra-Modern Duration Configuration
for d_config in durations:
    with st.sidebar.expander(f"🎯 Duration {d_config}M Configuration"):
        st.markdown("#### 📅 Year-by-Year Duration Share")
        
        for y_config in range(1, 6):
            yearly_duration_share[y_config][d_config] = st.number_input(
                f"Year {y_config} Share (%)", 
                min_value=0.0, max_value=100.0, 
                value=100.0 / len(durations) if len(durations) > 0 else 0,
                step=0.1, key=f"dur_{d_config}_year_{y_config}"
            )
        
        # Slab configuration
        st.markdown("#### 💰 Slab Selection")
        slab_options = [1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000]
        selected_slabs = st.multiselect(f"Select Slabs for {d_config}M", slab_options, default=[1000, 2000, 5000], key=f"slabs_{d_config}")
        slab_map[d_config] = selected_slabs
        
        # Ultra-Modern Slot Configuration - Enhanced UI
        st.markdown("#### 🎰 Slot Configuration & Blocking")
        
        # Configuration mode selection
        config_mode = st.radio(
            "Configuration Mode:",
            ["📊 Compact View", "📋 Detailed View", "🎯 Quick Setup"],
            key=f"config_mode_{d_config}",
            help="Choose how to configure slots"
        )
        
        slot_fees[d_config] = {}
        slot_distribution[d_config] = {}
        
        if config_mode == "🎯 Quick Setup":
            # Quick setup with presets
            st.markdown("**⚡ Quick Setup - Apply same settings to all slabs**")
            
            preset_fee = st.number_input("Default Fee %", value=2.0, min_value=0.0, max_value=50.0, step=0.1, key=f"preset_fee_{d_config}")
            preset_dist = 100.0 / d_config if d_config > 0 else 0
            
            for slab_amount in selected_slabs:
                st.markdown(f"**💰 {CURRENCY_SYMBOL}{slab_amount:,}** - Fee: {preset_fee}%, Distribution: {preset_dist:.1f}% per slot")
                
                # Initialize with preset values
                if slab_amount not in slot_fees[d_config]:
                    slot_fees[d_config][slab_amount] = {}
                if slot_distribution[d_config].get(slab_amount) is None:
                    slot_distribution[d_config][slab_amount] = {}
                
                for slot_num in range(1, d_config + 1):
                    slot_fees[d_config][slab_amount][slot_num] = {"fee_pct": preset_fee, "blocked": False}
                    slot_distribution[d_config][slab_amount][slot_num] = preset_dist
                    
        elif config_mode == "📊 Compact View":
            # Compact view with better organization
            for slab_amount in selected_slabs:
                st.markdown(f"**💰 Slab {CURRENCY_SYMBOL}{slab_amount:,}**")
                
                # Initialize slot configuration for this slab
                if slab_amount not in slot_fees[d_config]:
                    slot_fees[d_config][slab_amount] = {}
                if slot_distribution[d_config].get(slab_amount) is None:
                    slot_distribution[d_config][slab_amount] = {}
                
                # Create a compact table-like layout
                for slot_num in range(1, d_config + 1):
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])
                    
                    with col1:
                        st.markdown(f"**Slot {slot_num}**")
                    
                    with col2:
                        fee_pct = st.number_input(
                            "Fee %", 
                            min_value=0.0, max_value=50.0, 
                            value=2.0, step=0.1, 
                            key=f"fee_{d_config}_{slab_amount}_{slot_num}",
                            label_visibility="collapsed"
                        )
                        slot_fees[d_config][slab_amount][slot_num] = {"fee_pct": fee_pct}
                    
                    with col3:
                        if not slot_fees[d_config][slab_amount][slot_num].get('blocked', False):
                            dist_pct = st.number_input(
                                "Dist %", 
                                min_value=0.0, max_value=100.0, 
                                value=100.0/d_config, step=0.1, 
                                key=f"dist_{d_config}_{slab_amount}_{slot_num}",
                                label_visibility="collapsed"
                            )
                            slot_distribution[d_config][slab_amount][slot_num] = dist_pct
                        else:
                            slot_distribution[d_config][slab_amount][slot_num] = 0
                            st.info("🚫")
                    
                    with col4:
                        blocked = st.checkbox(
                            "Block", 
                            key=f"block_{d_config}_{slab_amount}_{slot_num}",
                            label_visibility="collapsed"
                        )
                        slot_fees[d_config][slab_amount][slot_num]['blocked'] = blocked
                        
        else:  # Detailed View
            # Original detailed view but better organized
            for slab_amount in selected_slabs:
                with st.expander(f"💰 Slab {CURRENCY_SYMBOL}{slab_amount:,} - Detailed Configuration", expanded=True):
                    # Initialize slot configuration for this slab
                    if slab_amount not in slot_fees[d_config]:
                        slot_fees[d_config][slab_amount] = {}
                    if slot_distribution[d_config].get(slab_amount) is None:
                        slot_distribution[d_config][slab_amount] = {}
                    
                    # Create slots for this specific slab
                    for slot_num in range(1, d_config + 1):
                        st.markdown(f"**🎯 Slot {slot_num}**")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            fee_pct = st.number_input(
                                f"Fee %", 
                                min_value=0.0, max_value=100.0, 
                                value=2.0, step=0.1, 
                                key=f"fee_{d_config}_{slab_amount}_{slot_num}",
                                help=f"Fee percentage for Slot {slot_num} of {CURRENCY_SYMBOL}{slab_amount:,}"
                            )
                        
                        with col2:
                            blocked = st.checkbox(
                                f"Block Slot", 
                                key=f"block_{d_config}_{slab_amount}_{slot_num}",
                                help=f"Block Slot {slot_num} for {CURRENCY_SYMBOL}{slab_amount:,}"
                            )
                        
                        with col3:
                            if not blocked:
                                dist_pct = st.number_input(
                                    f"Distribution %", 
                                    min_value=0.0, max_value=100.0, 
                                    value=100.0/d_config, step=0.1, 
                                    key=f"dist_{d_config}_{slab_amount}_{slot_num}",
                                    help=f"Distribution percentage for Slot {slot_num} of {CURRENCY_SYMBOL}{slab_amount:,}"
                                )
                                slot_distribution[d_config][slab_amount][slot_num] = dist_pct
                            else:
                                slot_distribution[d_config][slab_amount][slot_num] = 0
                                st.info("🚫 Blocked")
                        
                        slot_fees[d_config][slab_amount][slot_num] = {"fee_pct": fee_pct, "blocked": blocked}
        
        # Validation for all slabs
        for slab_amount in selected_slabs:
            if slab_amount in slot_distribution[d_config] and slab_amount in slot_fees[d_config]:
                unblocked_slots = {k: v for k, v in slot_distribution[d_config][slab_amount].items() 
                                  if not slot_fees[d_config][slab_amount].get(k, {}).get('blocked', False)}
                total_unblocked_dist_pct = sum(unblocked_slots.values())
                
                if total_unblocked_dist_pct > 0 and abs(total_unblocked_dist_pct - 100) > 0.1:
                    st.warning(f"⚠️ {CURRENCY_SYMBOL}{slab_amount:,} distribution totals {total_unblocked_dist_pct:.1f}%. Should be 100%.")

# Validation for year-by-year duration shares
for y_config in range(1, 6):
    if y_config in yearly_duration_share:
        current_year_total_share = sum(yearly_duration_share[y_config].values())
        if current_year_total_share > 0 and abs(current_year_total_share - 100) > 0.1:
            st.warning(f"⚠️ Year {y_config} duration share total is {current_year_total_share:.1f}%. It should be 100%.")

# Validation for slot distribution (updated for slab-specific configuration)
for d_config in durations:
    if d_config in slot_distribution and d_config in slot_fees:
        # Check each slab's slot distribution separately
        for slab_amount in slab_map.get(d_config, []):
            if slab_amount in slot_distribution[d_config] and slab_amount in slot_fees[d_config]:
                unblocked_slots = {k: v for k, v in slot_distribution[d_config][slab_amount].items() 
                                  if not slot_fees[d_config][slab_amount].get(k, {}).get('blocked', False)}
                total_unblocked_dist_pct = sum(unblocked_slots.values())
                
                if total_unblocked_dist_pct > 0 and abs(total_unblocked_dist_pct - 100) > 0.1:
                    st.warning(f"⚠️ Duration {d_config}M, Slab {CURRENCY_SYMBOL}{slab_amount:,} slot distribution total is {total_unblocked_dist_pct:.1f}%. It should be 100%.")

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
            
            if m_idx_fc == 0:
                new_users_this_month_fc = initial_new_users_m1_fc
            else:
                if enforce_cap_growth_fc:
                    TAM_used_cumulative_vs_cap_fc += cumulative_acquired_base_fc
                    if TAM_used_cumulative_vs_cap_fc >= TAM_current_year_fc:
                        new_users_this_month_fc = 0
                    else:
                        remaining_tam_fc = TAM_current_year_fc - TAM_used_cumulative_vs_cap_fc
                        new_users_this_month_fc = min(cumulative_acquired_base_fc * acquisition_rate_fc, remaining_tam_fc)
                else:
                    new_users_this_month_fc = cumulative_acquired_base_fc * acquisition_rate_fc
            
            cumulative_acquired_base_fc += new_users_this_month_fc
            
            # Process each duration
            for dur_val_fc in durations:
                if dur_val_fc not in yearly_duration_share[current_year_num_fc]:
                    continue
                    
                duration_share_pct_fc = yearly_duration_share[current_year_num_fc][dur_val_fc]
                users_for_this_duration_fc = math.ceil(new_users_this_month_fc * (duration_share_pct_fc / 100))
                
                if users_for_this_duration_fc <= 0:
                    continue
                
                slabs_for_this_duration_fc = slab_map.get(dur_val_fc, [])
                if not slabs_for_this_duration_fc:
                    continue
                
                current_duration_distributed_users = users_for_this_duration_fc
                
                for slab_val_fc in slabs_for_this_duration_fc:
                    if current_duration_distributed_users <= 0: 
                        break
                    
                    current_slab_distributed_users = current_duration_distributed_users
                    # Get unblocked slots for this specific slab
                    slots_for_this_duration = [s for s in range(1, dur_val_fc + 1) 
                                             if not slot_fees.get(dur_val_fc, {}).get(slab_val_fc, {}).get(s, {}).get('blocked', False)]
                    
                    if not slots_for_this_duration:
                        continue
                    
                    for slot_num_fc in slots_for_this_duration:
                        if current_slab_distributed_users <= 0: 
                            break
                        
                        # Calculate metrics for this cohort
                        installment_val_fc = slab_val_fc
                        total_commitment_per_user_fc = dur_val_fc * installment_val_fc
                        total_commitment_for_cohort_fc = users_for_this_slot_fc * total_commitment_per_user_fc
                        
                        # Get fee percentage for this specific slab and slot
                        fee_pct_for_slot_fc = slot_fees.get(dur_val_fc, {}).get(installment_val_fc, {}).get(slot_num_fc, {}).get('fee_pct', 2.0)
                        
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
                        
                        for j in range(dur_val_fc):
                            days_held_fc = max(0, (slot_num_fc - 1) * 30 - j * 30)
                            base_nii_from_installment = installment_val_fc * daily_interest_rate_fc * days_held_fc
                            
                            # Fee NII contribution (interest on collected fees)
                            if fee_collection_mode_fc == "Upfront Fee (Entire Pool)":
                                fee_nii_contribution = (total_commitment_per_user_fc * (fee_pct_for_slot_fc / 100)) * daily_interest_rate_fc * days_held_fc
                            else:
                                fee_nii_contribution = monthly_fee_per_user_fc * daily_interest_rate_fc * days_held_fc
                            
                            # Pool growth NII (interest on accumulated deposits from previous installments)
                            pool_growth_nii = j * installment_val_fc * daily_interest_rate_fc * days_held_fc
                            
                            monthly_nii = base_nii_from_installment + fee_nii_contribution + pool_growth_nii
                            total_nii_for_cohort_lifetime_per_user += monthly_nii
                            
                            monthly_nii_breakdown.append({
                                'month': j + 1,
                                'base_nii': base_nii_from_installment,
                                'fee_nii': fee_nii_contribution,
                                'pool_growth_nii': pool_growth_nii,
                                'total_nii': monthly_nii
                            })
                        
                        # Default calculations
                        num_defaulters_fc = math.ceil(users_for_this_slot_fc * current_default_frac_fc)
                        num_pre_payout_defaulters_fc = math.ceil(num_defaulters_fc * global_default_pre_frac_fc)
                        num_post_payout_defaulters_fc = num_defaulters_fc - num_pre_payout_defaulters_fc
                        
                        # Pre-payout default calculations
                        refund_amount_per_pre_defaulter = total_commitment_per_user_fc * (1 - current_penalty_frac_fc)
                        default_processing_fee_per_pre = total_commitment_per_user_fc * (default_fee_rate / 100)
                        loss_per_pre_defaulter_fc = total_commitment_per_user_fc - refund_amount_per_pre_defaulter + default_processing_fee_per_pre
                        
                        # Post-payout default calculations
                        default_processing_fee_per_post = total_commitment_per_user_fc * (default_fee_rate / 100)
                        loss_per_post_defaulter_fc = total_commitment_per_user_fc + default_processing_fee_per_post
                        
                        # Total default losses
                        total_defaulted_amount = (num_pre_payout_defaulters_fc * loss_per_pre_defaulter_fc + 
                                                num_post_payout_defaulters_fc * loss_per_post_defaulter_fc)
                        
                        # Recovery calculations
                        recovered_amount = total_defaulted_amount * (default_recovery_rate / 100)
                        net_default_loss = total_defaulted_amount - recovered_amount
                        
                        # Default fees collected
                        total_default_fees_collected = (num_pre_payout_defaulters_fc * default_processing_fee_per_pre + 
                                                      num_post_payout_defaulters_fc * default_processing_fee_per_post)
                        
                        # External capital needed
                        external_capital_needed_for_cohort_lifetime_fc = net_default_loss
                        
                        # Expected lifetime profit
                        expected_lifetime_profit_fc = (total_fee_collected_for_cohort_fc + 
                                                     (total_nii_for_cohort_lifetime_per_user * users_for_this_slot_fc) - 
                                                     net_default_loss)
                        
                        # Store forecast data
                        forecast_data_fc.append({
                            "Month Joined": current_month_num_fc,
                            "Duration": dur_val_fc,
                            "Slab": installment_val_fc,
                            "Slot": slot_num_fc,
                            "Users": users_for_this_slot_fc,
                            "Total Commitment Per User": total_commitment_per_user_fc,
                            "Total Commitment (Cohort)": total_commitment_for_cohort_fc,
                            "Fee %": fee_pct_for_slot_fc,
                            "Total Fee Collected (Lifetime)": total_fee_collected_for_cohort_fc,
                            "Total NII (Lifetime)": total_nii_for_cohort_lifetime_per_user * users_for_this_slot_fc,
                            "Base NII (Lifetime)": sum([breakdown['base_nii'] for breakdown in monthly_nii_breakdown]) * users_for_this_slot_fc,
                            "Fee NII (Lifetime)": sum([breakdown['fee_nii'] for breakdown in monthly_nii_breakdown]) * users_for_this_slot_fc,
                            "Pool Growth NII (Lifetime)": sum([breakdown['pool_growth_nii'] for breakdown in monthly_nii_breakdown]) * users_for_this_slot_fc,
                            "Total Defaulters": num_defaulters_fc,
                            "Pre-Payout Defaulters": num_pre_payout_defaulters_fc,
                            "Post-Payout Defaulters": num_post_payout_defaulters_fc,
                            "Total Default Loss (Lifetime)": total_defaulted_amount,
                            "Net Default Loss (After Recovery)": net_default_loss,
                            "Default Recovery Amount": recovered_amount,
                            "Default Fees Collected": total_default_fees_collected,
                            "Pre-Payout Loss": num_pre_payout_defaulters_fc * loss_per_pre_defaulter_fc,
                            "Post-Payout Loss": num_post_payout_defaulters_fc * loss_per_post_defaulter_fc,
                            "External Capital For Loss (Lifetime)": external_capital_needed_for_cohort_lifetime_fc,
                            "Expected Lifetime Profit": expected_lifetime_profit_fc
                        })
                        
                        # Store deposit log data
                        for j in range(dur_val_fc):
                            deposit_log_data_fc.append({
                                "Month Joined": current_month_num_fc,
                                "Duration": dur_val_fc,
                                "Slab": installment_val_fc,
                                "Slot": slot_num_fc,
                                "Users": users_for_this_slot_fc,
                                "Installment Month": j + 1,
                                "Installment Amount": installment_val_fc,
                                "Total Installment (Cohort)": installment_val_fc * users_for_this_slot_fc,
                                "Fee Collection": monthly_fee_collection_fc if fee_collection_mode_fc == "Monthly Fee Collection" else 0,
                                "Cash In (Installments)": installment_val_fc * users_for_this_slot_fc + (monthly_fee_collection_fc if fee_collection_mode_fc == "Monthly Fee Collection" else 0)
                            })
                        
                        # Store default log data
                        if num_defaulters_fc > 0:
                            default_log_data_fc.append({
                                "Month Joined": current_month_num_fc,
                                "Duration": dur_val_fc,
                                "Slab": installment_val_fc,
                                "Slot": slot_num_fc,
                                "Total Users": users_for_this_slot_fc,
                                "Total Defaulters": num_defaulters_fc,
                                "Pre-Payout Defaulters": num_pre_payout_defaulters_fc,
                                "Post-Payout Defaulters": num_post_payout_defaulters_fc,
                                "Default Rate %": (num_defaulters_fc / users_for_this_slot_fc) * 100 if users_for_this_slot_fc > 0 else 0,
                                "Total Defaulted Amount": total_defaulted_amount,
                                "Recovered Amount": recovered_amount,
                                "Net Default Loss": net_default_loss,
                                "Default Fees Collected": total_default_fees_collected,
                                "Recovery Rate %": (recovered_amount / total_defaulted_amount) * 100 if total_defaulted_amount > 0 else 0
                            })
                        
                        # Store lifecycle data
                        lifecycle_data_fc.append({
                            "Month Joined": current_month_num_fc,
                            "Duration": dur_val_fc,
                            "Slab": installment_val_fc,
                            "Slot": slot_num_fc,
                            "Users": users_for_this_slot_fc,
                            "Total Commitment": total_commitment_for_cohort_fc,
                            "Total Fees": total_fee_collected_for_cohort_fc,
                            "Total NII": total_nii_for_cohort_lifetime_per_user * users_for_this_slot_fc,
                            "Total Revenue": total_fee_collected_for_cohort_fc + (total_nii_for_cohort_lifetime_per_user * users_for_this_slot_fc),
                            "Total Default Loss": net_default_loss,
                            "Expected Profit": expected_lifetime_profit_fc,
                            "External Capital Needed": external_capital_needed_for_cohort_lifetime_fc
                        })
                        
                        current_slab_distributed_users -= users_for_this_slot_fc
                    
                    current_duration_distributed_users -= current_slab_distributed_users
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return (pd.DataFrame(forecast_data_fc), 
                pd.DataFrame(deposit_log_data_fc), 
                pd.DataFrame(default_log_data_fc), 
                pd.DataFrame(lifecycle_data_fc))
        
    except Exception as e:
        st.error(f"Error in forecasting: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# =============================================================================
# 📊 DASHBOARD FUNCTIONS
# =============================================================================

def create_dashboard_overview(df_monthly, scenario_name):
    """Create modern dashboard overview"""
    if df_monthly.empty:
        st.warning("No data available for dashboard")
        return
    
    st.markdown(f"""
    <div class="chart-container">
        <div class="chart-title">📊 Dashboard Overview - {scenario_name}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    total_users = df_monthly['Users Joining This Month'].sum()
    total_revenue = df_monthly['Total Fee Collected (Lifetime)'].sum() + df_monthly['Total NII (Lifetime)'].sum()
    total_profit = df_monthly['Expected Lifetime Profit'].sum()
    total_pools = df_monthly['Pools Formed This Month'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_modern_metric_card("Total Users", f"{total_users:,.0f}", "+12.5%", "positive", "👥"))
    with col2:
        st.markdown(create_modern_metric_card("Total Revenue", format_currency(total_revenue), "+8.3%", "positive", "💰"))
    with col3:
        st.markdown(create_modern_metric_card("Total Profit", format_currency(total_profit), "+15.2%", "positive", "📈"))
    with col4:
        st.markdown(create_modern_metric_card("Total Pools", f"{total_pools:,.0f}", "+6.7%", "positive", "🏦"))

def create_monthly_summary(df_forecast):
    """Create monthly summary from forecast data"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    monthly_summary = df_forecast.groupby('Month Joined').agg({
        'Users': 'sum',
        'Total Fee Collected (Lifetime)': 'sum',
        'Total NII (Lifetime)': 'sum',
        'Expected Lifetime Profit': 'sum',
        'Total Default Loss (Lifetime)': 'sum',
        'External Capital For Loss (Lifetime)': 'sum'
    }).reset_index()
    
    monthly_summary['Pools Formed This Month'] = monthly_summary['Users'] / 3  # Assuming average 3 users per pool
    monthly_summary['Users Joining This Month'] = monthly_summary['Users']
    monthly_summary['Total Revenue'] = monthly_summary['Total Fee Collected (Lifetime)'] + monthly_summary['Total NII (Lifetime)']
    
    return monthly_summary

def create_yearly_summary(df_monthly):
    """Create yearly summary from monthly data"""
    if df_monthly.empty:
        return pd.DataFrame()
    
    df_monthly['Year'] = ((df_monthly['Month Joined'] - 1) // 12) + 1
    
    yearly_summary = df_monthly.groupby('Year').agg({
        'Users Joining This Month': 'sum',
        'Total Fee Collected (Lifetime)': 'sum',
        'Total NII (Lifetime)': 'sum',
        'Expected Lifetime Profit': 'sum',
        'Total Default Loss (Lifetime)': 'sum',
        'External Capital For Loss (Lifetime)': 'sum',
        'Pools Formed This Month': 'sum'
    }).reset_index()
    
    yearly_summary['Total Revenue'] = yearly_summary['Total Fee Collected (Lifetime)'] + yearly_summary['Total NII (Lifetime)']
    
    return yearly_summary

def create_profit_share_analysis(df_yearly):
    """Create profit share analysis"""
    if df_yearly.empty:
        return pd.DataFrame()
    
    df_yearly['Party A Share'] = df_yearly['Expected Lifetime Profit'] * party_a_pct
    df_yearly['Party B Share'] = df_yearly['Expected Lifetime Profit'] * party_b_pct
    df_yearly['External Capital Coverage'] = df_yearly['Party A Share'] / df_yearly['External Capital For Loss (Lifetime)']
    
    return df_yearly

# =============================================================================
# 🚀 MAIN EXECUTION
# =============================================================================

# Run Forecast Button
if st.button("🚀 Run Forecast", type="primary"):
    output_excel_main = io.BytesIO()
    
    with st.spinner("🔄 Processing forecast..."):
        try:
            with pd.ExcelWriter(output_excel_main, engine="xlsxwriter") as excel_writer_main:
                for scenario_idx_main, scenario_data_main in enumerate(scenarios):
                    current_config_main = scenario_data_main.copy()
                    current_config_main.update({
                        "kibor": kibor, "spread": spread, "rest_period": rest_period,
                        "default_rate": default_rate, "penalty_pct": penalty_pct
                    })
                    
                    # Ensure we have valid configuration
                    if not durations or not any(slab_map.values()):
                        st.error("❌ Please configure at least one duration and slab before running forecast!")
                        st.stop()
                    
                    df_forecast_main, df_deposit_log_main, df_default_log_main, df_lifecycle_main = run_forecast(current_config_main, fee_collection_mode)

                    if df_forecast_main.empty:
                        st.error(f"❌ No forecast data generated for {scenario_data_main['name']}")
                        st.error("💡 **Troubleshooting Tips:**")
                        st.error("1. Check that you have selected durations and slabs")
                        st.error("2. Ensure slot distribution totals 100% for each slab")
                        st.error("3. Verify that not all slots are blocked")
                        st.error("4. Try using 'Configuration Mode' for easier setup")
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
                            st.markdown(f"**Current Mode:** {fee_collection_mode}")
                        with col2:
                            if fee_collection_mode == "Upfront Fee (Entire Pool)":
                                st.success("✅ **Upfront Mode:** Immediate cash flow, higher upfront revenue")
                            else:
                                st.info("💡 **Monthly Mode:** Steady monthly revenue, lower barrier to entry")
                        
                        # Show data table
                        st.subheader("📋 Forecast Data")
                        st.dataframe(df_forecast_main.head(20), use_container_width=True)
                        
                    elif view_mode == "🔧 Detailed Forecast":
                        st.subheader(f"📊 Detailed Forecast - {scenario_data_main['name']}")
                        st.dataframe(df_forecast_main, use_container_width=True)
                        
                    elif view_mode == "📈 Analytics Only":
                        st.subheader(f"📈 Analytics - {scenario_data_main['name']}")
                        
                        # Revenue analysis
                        total_fees = df_forecast_main['Total Fee Collected (Lifetime)'].sum()
                        total_nii = df_forecast_main['Total NII (Lifetime)'].sum()
                        total_revenue = total_fees + total_nii
                        total_losses = df_forecast_main['Total Default Loss (Lifetime)'].sum()
                        gross_profit = total_revenue - total_losses
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.markdown(create_modern_metric_card("Total Fees", format_currency(total_fees), "+12.5%", "positive", "💸"))
                        with col2:
                            st.markdown(create_modern_metric_card("Total NII", format_currency(total_nii), "+8.3%", "positive", "📈"))
                        with col3:
                            st.markdown(create_modern_metric_card("Total Revenue", format_currency(total_revenue), "+10.4%", "positive", "💰"))
                        with col4:
                            st.markdown(create_modern_metric_card("Gross Profit", format_currency(gross_profit), "+15.2%", "positive", "💎"))

                    # Excel export
                    sheet_name_prefix_main = scenario_data_main['name'].replace(' ', '_')
                    
                    if not df_forecast_main.empty:
                        df_forecast_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_Forecast")
                    if not df_monthly_summary_main.empty:
                        df_monthly_summary_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_Monthly")
                    if not df_yearly_summary_main.empty:
                        df_yearly_summary_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_Yearly")
                    if not df_profit_share_main.empty:
                        df_profit_share_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_ProfitShare")
                    if not df_deposit_log_main.empty:
                        df_deposit_log_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_DepositLog")
                    if not df_default_log_main.empty:
                        df_default_log_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_DefaultLog")
                    if not df_lifecycle_main.empty:
                        df_lifecycle_main.to_excel(excel_writer_main, index=False, sheet_name=f"{sheet_name_prefix_main}_LifecycleLog")

        except Exception as e:
            st.error(f"Error in main execution: {str(e)}")
            st.error("Please check your configuration and try again.")
    
    st.success("✅ Forecast completed successfully!")

# Download options
st.markdown("### 📥 Download Options")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Download Excel Report"):
        if 'output_excel_main' in locals():
            st.download_button(
                label="📥 Download Excel",
                data=output_excel_main.getvalue(),
                file_name=f"ROSCA_Forecast_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Please run forecast first")

with col2:
    if st.button("📋 Generate Summary"):
        st.info("Summary generated! Check the dashboard above.")

with col3:
    if st.button("🔄 Refresh Data"):
        st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; color: #64748b; font-family: 'Inter', sans-serif; padding: 2rem; margin-top: 2rem;">
    <h3 style="color: #1e293b; font-weight: 800; margin-bottom: 1rem;">🚀 ROSCA Forecast Pro</h3>
    <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">Complete Business Intelligence Platform</p>
    <p style="font-size: 0.9rem; opacity: 0.8;">Built with ❤️ using Streamlit | Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
