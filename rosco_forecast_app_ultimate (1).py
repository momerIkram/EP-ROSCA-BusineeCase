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
        color: #10b981;
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
        background: linear-gradient(90deg, #667eea, #764ba2);
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
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Success/Info/Warning/Error Boxes */
    .success-box {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.2);
        border-left: 4px solid #059669;
    }
    
    .info-box {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.2);
        border-left: 4px solid #2563eb;
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4);
    }
    
    /* Selectbox Styling */
    .stSelectbox > div > div {
        background: white;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Number Input Styling */
    .stNumberInput > div > div > input {
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Text Input Styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Multiselect Styling */
    .stMultiSelect > div > div {
        background: white;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.1);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea;
    }
    
    /* Data Editor Styling */
    .stDataEditor {
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Table Styling */
    .stDataFrame {
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Sidebar Section Headers */
    .sidebar-section {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid rgba(102, 126, 234, 0.1);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .sidebar-section h3 {
        color: #1e293b;
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

def create_slot_configuration_ui(duration, slab_amount, slot_fees, slot_distribution, currency_symbol):
    """Create UI for slot configuration"""
    st.markdown(f"**🎯 Slot Configuration for {duration}M, {currency_symbol}{slab_amount:,}**")
    
    total_distribution = 0
    for slot in range(1, duration + 1):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fee_pct = st.number_input(
                f"Fee % for Slot {slot}",
                min_value=0.0,
                max_value=20.0,
                value=slot_fees.get(slot, {}).get('fee_pct', 2.0),
                step=0.1,
                key=f"fee_{duration}_{slab_amount}_{slot}"
            )
        
        with col2:
            blocked = st.checkbox(
                f"Block Slot {slot}",
                value=slot_fees.get(slot, {}).get('blocked', False),
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
        ax.bar(df_revenue['Component'], df_revenue['Amount'], color=['#667eea', '#764ba2'])
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
                     color_discrete_sequence=['#667eea', '#764ba2'])
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
        ax.bar(df_grouped.index, df_grouped.values, color='#667eea')
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
        ax.bar(df_grouped.index, df_grouped.values, color='#764ba2')
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
            color_discrete_sequence=['#667eea']
        )
        fig.update_layout(height=400)
        return fig
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        df_grouped = df_forecast.groupby('Month')['Pool Size'].sum()
        ax.plot(df_grouped.index, df_grouped.values, color='#667eea', linewidth=2)
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
    """Create monthly summary from forecast data"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    # Group by month and sum
    monthly_data = []
    for month in range(1, 13):  # 12 months
        month_data = {
            'Month': f"Month {month}",
            'Users Joining This Month': df_forecast['Users'].sum() // 12,
            'Total Revenue': df_forecast['Total Revenue'].sum() // 12,
            'Gross Profit': df_forecast['Gross Profit'].sum() // 12,
            'Total Fees': df_forecast['Total Fees Collected'].sum() // 12,
            'Total NII': df_forecast['Total NII (Lifetime)'].sum() // 12
        }
        monthly_data.append(month_data)
    
    return pd.DataFrame(monthly_data)

def create_yearly_summary(df_monthly):
    """Create yearly summary from monthly data"""
    if df_monthly.empty:
        return pd.DataFrame()
    
    yearly_data = {
        'Year': ['Year 1'],
        'Total Users': [df_monthly['Users Joining This Month'].sum()],
        'Total Revenue': [df_monthly['Total Revenue'].sum()],
        'Gross Profit': [df_monthly['Gross Profit'].sum()],
        'Total Fees': [df_monthly['Total Fees'].sum()],
        'Total NII': [df_monthly['Total NII'].sum()]
    }
    
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
    
    deposit_data = []
    for _, row in df_forecast.iterrows():
        for month in range(1, 13):
            deposit_data.append({
                'Month': f"Month {month}",
                'Duration': row['Duration'],
                'Slab Amount': row['Slab Amount'],
                'Users': row['Users'],
                'Monthly Deposit': row['Slab Amount'],
                'Total Deposits': row['Slab Amount'] * row['Users'],
                'Fee Collected': row['Monthly Fee Collection'],
                'Total Fee': row['Total Fees Collected']
            })
    
    return pd.DataFrame(deposit_data)

def create_default_log(df_forecast):
    """Create default log"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    default_data = []
    for _, row in df_forecast.iterrows():
        for month in range(1, 13):
            default_data.append({
                'Month': f"Month {month}",
                'Duration': row['Duration'],
                'Slab Amount': row['Slab Amount'],
                'Users': row['Users'],
                'Pre-Payout Defaults': row['Pre-Payout Default Loss'],
                'Post-Payout Defaults': row['Post-Payout Default Loss'],
                'Total Defaults': row['Total Default Loss'],
                'Recovery Amount': row['Default Recovery Amount'],
                'Net Default Loss': row['Net Default Loss (After Recovery)']
            })
    
    return pd.DataFrame(default_data)

def create_lifecycle_log(df_forecast):
    """Create lifecycle log"""
    if df_forecast.empty:
        return pd.DataFrame()
    
    lifecycle_data = []
    for _, row in df_forecast.iterrows():
        for month in range(1, 13):
            lifecycle_data.append({
                'Month': f"Month {month}",
                'Duration': row['Duration'],
                'Slab Amount': row['Slab Amount'],
                'Users': row['Users'],
                'New Users': row['Users'] // 12,
                'Rejoining Users': 0,  # Placeholder
                'Churned Users': 0,  # Placeholder
                'Active Users': row['Users'],
                'Pool Size': row['Pool Size']
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
# 🔧 MAIN FORECASTING ENGINE
# =============================================================================

# In the run_forecast function, replace the fee calculation section:

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
        'Pool Size': [],
        'External Capital': [],
        'Total Commitment': [],
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
            
            # Calculate slot-wise fees
            total_fee = 0
            monthly_fee = 0
            
            if fee_collection_mode == "Upfront Fee (Entire Pool)":
                # Calculate upfront fee based on slot distribution
                for slot in range(1, duration + 1):
                    if slot in slot_fees and slot in slot_distribution:
                        slot_fee_pct = slot_fees[slot]['fee_pct']
                        slot_distribution_pct = slot_distribution[slot]
                        if slot_distribution_pct > 0:  # Only if slot is not blocked
                            slot_fee = (slab_amount * duration * (slot_fee_pct / 100) * (slot_distribution_pct / 100))
                            total_fee += slot_fee
            else:
                # Calculate monthly fee based on slot distribution
                for slot in range(1, duration + 1):
                    if slot in slot_fees and slot in slot_distribution:
                        slot_fee_pct = slot_fees[slot]['fee_pct']
                        slot_distribution_pct = slot_distribution[slot]
                        if slot_distribution_pct > 0:  # Only if slot is not blocked
                            slot_monthly_fee = (slab_amount * (slot_fee_pct / 100) * (slot_distribution_pct / 100))
                            monthly_fee += slot_monthly_fee
                total_fee = monthly_fee * duration
            
            # Basic calculations
            total_commitment = slab_amount * duration
            
            # NII calculations
            base_nii = total_commitment * (config['kibor_rate'] + config['spread']) / 100 / 12 * duration
            fee_nii = total_fee * (config['kibor_rate'] + config['spread']) / 100 / 12 * duration
            pool_growth_nii = total_commitment * (config['kibor_rate'] + config['spread']) / 100 / 12 * duration
            total_nii = base_nii + fee_nii + pool_growth_nii
            
            # Default calculations
            pre_payout_default_loss = total_commitment * (config['default_rate'] / 100) * (config['default_pre_pct'] / 100)
            post_payout_default_loss = total_commitment * (config['default_rate'] / 100) * (config['default_post_pct'] / 100)
            total_default_loss = pre_payout_default_loss + post_payout_default_loss
            default_recovery = total_default_loss * (config['recovery_rate'] / 100)
            net_default_loss = total_default_loss - default_recovery
            default_fees = total_default_loss * (config['penalty_pct'] / 100)
            
            # Revenue calculations
            total_revenue = total_fee + total_nii
            total_losses = net_default_loss
            gross_profit = total_revenue - total_losses
            net_profit = gross_profit - default_fees
            
            # Party A/B split
            party_a_share = net_profit * (config['profit_split'] / 100)
            party_b_share = net_profit * ((100 - config['profit_split']) / 100)
            
            # Generate monthly data
            for month in range(1, 13):
                year = 2024 + (month - 1) // 12
                
                # Calculate users for this month
                users_this_month = 100  # Placeholder - should be calculated based on business logic
                
                # Calculate pool size
                pool_size = users_this_month * slab_amount
                
                # Calculate external capital
                external_capital = pool_size * 0.1  # Placeholder - 10% external capital
                
                # Add to scenario data
                scenario_data['Month'].append(month)
                scenario_data['Year'].append(year)
                scenario_data['Duration'].append(duration)
                scenario_data['Slab Amount'].append(slab_amount)
                scenario_data['Users'].append(users_this_month)
                scenario_data['Pool Size'].append(pool_size)
                scenario_data['External Capital'].append(external_capital)
                scenario_data['Total Commitment'].append(total_commitment)
                scenario_data['Fee %'].append(sum([slot_fees.get(slot, {}).get('fee_pct', 0) for slot in range(1, duration + 1)]) / duration)
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
                scenario_data['Total Defaulters'].append(int(users_this_month * config['default_rate'] / 100))
                scenario_data['Total Revenue'].append(total_revenue)
                scenario_data['Total Losses'].append(total_losses)
                scenario_data['Gross Profit'].append(gross_profit)
                scenario_data['Net Profit'].append(net_profit)
                scenario_data['Party A Share'].append(party_a_share)
                scenario_data['Party B Share'].append(party_b_share)
    
    # Convert to DataFrame
    df_forecast = pd.DataFrame(scenario_data)
    
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
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Fee collection mode
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 💳 Fee Collection")
    fee_collection_mode = st.selectbox(
        "Fee Collection Method",
        ["Upfront Fee (Entire Pool)", "Monthly Fee Collection"]
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Market & TAM Configuration
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 🌍 Market & TAM Configuration")
    market_size = st.number_input("Total Addressable Market (TAM)", min_value=0, value=1000000, step=10000, help="Total market size in your currency")
    sam_size = st.number_input("Serviceable Addressable Market (SAM)", min_value=0, value=500000, step=10000, help="Addressable market size")
    som_size = st.number_input("Serviceable Obtainable Market (SOM)", min_value=0, value=50000, step=1000, help="Realistic market capture")
    market_growth_rate = st.number_input("Market Growth Rate (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.1, help="Annual market growth rate")
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
        [3, 6, 9, 12, 18, 24, 36],
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
                        slot_data = []  # <-- Now properly indented under elif
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
    'slot_distribution': slot_distribution
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
        
        # Run forecast
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
            
            # Store market data in session state
            st.session_state['market_size'] = market_size
            st.session_state['sam_size'] = sam_size
            st.session_state['som_size'] = som_size
            st.session_state['market_growth_rate'] = market_growth_rate
            
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
    
    if view_mode == "📊 Dashboard View":
        # Dashboard overview
        create_dashboard_overview(df_monthly_summary, scenario_name, CURRENCY_SYMBOL, CURRENCY_NAME)
        
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
            # Excel export
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_forecast.to_excel(writer, sheet_name='Forecast', index=False)
                if not df_monthly_summary.empty:
                    df_monthly_summary.to_excel(writer, sheet_name='Monthly Summary', index=False)
                if not df_yearly_summary.empty:
                    df_yearly_summary.to_excel(writer, sheet_name='Yearly Summary', index=False)
                if not df_profit_share.empty:
                    df_profit_share.to_excel(writer, sheet_name='Profit Share', index=False)
                if not df_deposit_log.empty:
                    df_deposit_log.to_excel(writer, sheet_name='Deposit Log', index=False)
                if not df_default_log.empty:
                    df_default_log.to_excel(writer, sheet_name='Default Log', index=False)
                if not df_lifecycle_log.empty:
                    df_lifecycle_log.to_excel(writer, sheet_name='Lifecycle Log', index=False)
            excel_data = output.getvalue()
            
            st.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name=f"rosca_forecast_{scenario_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    elif view_mode == "🔧 Detailed Forecast":
        # Detailed forecast table
        st.subheader("📋 Detailed Forecast Results")
        st.dataframe(df_forecast.style.format(precision=0, thousands=","))
        
        # Summary tables
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Monthly Summary")
            st.dataframe(df_monthly_summary)
        
        with col2:
            st.subheader("📈 Yearly Summary")
            st.dataframe(df_yearly_summary)
        
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
    <p>💰 ROSCA Forecast Pro - Advanced Financial Forecasting & Analytics</p>
    <p>Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
