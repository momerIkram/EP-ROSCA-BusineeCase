"""
BACHAT ROSCA — Pricing & Risk Model (v2.1)
==========================================
UI redesign: finance-dashboard inspired layout
  - KPI cards with embedded sparklines
  - Semi-circular gauge charts for margin metrics
  - Combo bar+line dual-axis chart
  - Horizontal income statement breakdown (right panel)
  - Auto-generated Smart Insights
  - Card-style chart containers with shadows
  - Two-column overview layout (main | right panel)

Engine is unchanged from v2.1 (slot-conditional defaults,
three-principal NII, two-pass lifecycle, O(M) cumsum).
"""

import dataclasses
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# =============================================================================
# CONSTANTS
# =============================================================================

BACHAT_GREEN       = "#00D084"
BACHAT_GREEN_DARK  = "#00A368"
BACHAT_GREEN_LIGHT = "#E6F9F1"
INK        = "#0F172A"
SLATE_700  = "#334155"
SLATE_500  = "#64748B"
SLATE_300  = "#CBD5E1"
SLATE_200  = "#E2E8F0"
SLATE_100  = "#F1F5F9"
SLATE_50   = "#F8FAFC"
DANGER     = "#DC2626"
WARNING    = "#F59E0B"
INFO       = "#0EA5E9"
PURPLE     = "#8B5CF6"
TEAL       = "#14B8A6"
WHITE      = "#FFFFFF"

PLOTLY_TEMPLATE = "plotly_white"
PLOTLY_COLORWAY = [BACHAT_GREEN, INFO, PURPLE, WARNING, DANGER, TEAL]


# =============================================================================
# CONFIG
# =============================================================================

@dataclass
class BachatConfig:
    """Single source of truth for all model inputs."""
    starting_users: int        = 500
    monthly_growth_rate: float = 8.0
    churn_rate: float          = 5.0
    returning_user_rate: float = 60.0
    rest_period_months: int    = 1
    simulation_months: int     = 60

    durations: List[int]  = field(default_factory=lambda: [6])
    slab_amount: int      = 10_000
    slot_fee_pct: float   = 5.0
    blocked_slots: int    = 1

    kibor_rate: float     = 21.0
    spread: float         = -3.0
    collection_day: int   = 1
    disbursement_day: int = 15

    default_rate: float   = 8.0
    recovery_rate: float  = 30.0
    penalty_pct: float    = 2.0

    profit_split_party_a: float = 60.0


# =============================================================================
# ENGINE  —  pure functions, no Streamlit (unchanged from v2.1)
# =============================================================================

def held_days(deposit_month: int, payout_month: int,
              deposit_day: int, payout_day: int) -> int:
    """30/360 day-count — standard for KIBOR-linked contracts."""
    return max(0, (payout_month - deposit_month) * 30 + (payout_day - deposit_day))


def nii(principal: float, annual_rate_pct: float, days: int) -> float:
    if principal <= 0 or days <= 0:
        return 0.0
    return principal * (annual_rate_pct / 100.0) * (days / 365.0)


def max_debtor_position(duration: int, slot: int, slab: float) -> float:
    return max(0.0, (duration - slot) * slab)


def slot_conditional_default_loss(
    duration: int, blocked: int, slab: float,
    default_rate_pct: float, recovery_rate_pct: float
) -> Tuple[float, float]:
    p = default_rate_pct  / 100.0
    r = recovery_rate_pct / 100.0
    gross = sum(max_debtor_position(duration, s, slab) * p
                for s in range(blocked + 1, duration + 1))
    return gross, gross * (1.0 - r)


def platform_float_capital(duration: int, blocked: int, slab: float) -> float:
    total = 0.0
    for k in range(1, blocked + 1):
        r = duration - k
        total += slab * r * (r + 1) / 2.0
    return total


def base_nii_per_cycle(duration: int, slab: float, annual_rate_pct: float,
                       collection_day: int, disbursement_day: int) -> float:
    """NII on full monthly pool sitting idle between collection and disbursement.
    30/360 convention. Principal = N × M (full pot, all members)."""
    if disbursement_day <= collection_day:
        return 0.0
    return duration * nii(duration * slab, annual_rate_pct,
                          disbursement_day - collection_day)


def float_nii_per_cycle(duration: int, blocked: int, slab: float,
                        annual_rate_pct: float) -> float:
    """NII on platform working-capital float from blocked slots. Different
    principal from base_nii — no double-counting."""
    return platform_float_capital(duration, blocked, slab) * (annual_rate_pct / 100.0) / 12.0


def fee_nii_per_cycle(total_fees: float, duration: int,
                      annual_rate_pct: float) -> float:
    """NII on collected fees held for half the cycle. Different principal."""
    return nii(total_fees, annual_rate_pct, int((duration * 30) / 2))


def user_lifecycle(cfg: BachatConfig, duration: int) -> pd.DataFrame:
    """Two-pass cohort-tracked lifecycle. Pass 2 reads return_schedule[m]
    (written by prior iterations) before processing finish_origin < m, so
    second-generation churn and multi-cycle returns are correct."""
    M    = cfg.simulation_months
    g    = cfg.monthly_growth_rate / 100.0
    churn    = cfg.churn_rate          / 100.0
    ret_rate = cfg.returning_user_rate / 100.0
    rest     = cfg.rest_period_months

    new_users       = np.zeros(M + 1)
    returning_users = np.zeros(M + 1)
    resting_users   = np.zeros(M + 1)
    completed_users = np.zeros(M + 1)
    churned_users   = np.zeros(M + 1)
    active_users    = np.zeros(M + 1)
    return_schedule = np.zeros(M + 2)

    new_users[1] = float(cfg.starting_users)
    cumulative   = float(cfg.starting_users)
    for m in range(2, M + 1):
        cumulative  *= (1.0 + g)
        new_users[m] = max(0.0, cumulative - cumulative / (1.0 + g))

    for m in range(1, M + 1):
        returning_users[m] = return_schedule[m]
        finish_origin = m - duration + 1
        if finish_origin >= 1:
            finishing = new_users[finish_origin] + returning_users[finish_origin]
            churned   = finishing * churn
            survivors = finishing - churned
            completed_users[m] = finishing
            churned_users[m]   = churned
            resting_users[m]   = survivors
            ret_month = m + rest
            if ret_month <= M:
                return_schedule[ret_month] += survivors * ret_rate

    combined  = new_users + returning_users
    cs = np.cumsum(combined)
    for m in range(1, M + 1):
        start = max(1, m - duration + 1)
        active_users[m] = cs[m] - cs[start - 1]

    return pd.DataFrame({
        "month":                 np.arange(1, M + 1),
        "new_users":             new_users[1:].astype(int),
        "returning_users":       returning_users[1:].astype(int),
        "active_users_in_cycle": active_users[1:].astype(int),
        "resting_users":         resting_users[1:].astype(int),
        "completed_users":       completed_users[1:].astype(int),
        "churned_users":         churned_users[1:].astype(int),
    })


def build_forecast(cfg: BachatConfig) -> pd.DataFrame:
    """O(M) monthly forecast across all durations. All columns are _monthly."""
    rows = []
    annual_rate = cfg.kibor_rate + cfg.spread
    M = cfg.simulation_months

    for duration in cfg.durations:
        slab = cfg.slab_amount
        N    = duration
        pot  = N * slab
        user_slots = N - cfg.blocked_slots

        cycle_base_nii  = base_nii_per_cycle(N, slab, annual_rate,
                                             cfg.collection_day, cfg.disbursement_day)
        cycle_float_nii = float_nii_per_cycle(N, cfg.blocked_slots, slab, annual_rate)
        cycle_fees      = user_slots * pot * (cfg.slot_fee_pct / 100.0)
        cycle_fee_nii   = fee_nii_per_cycle(cycle_fees, N, annual_rate)
        gross_def, net_def = slot_conditional_default_loss(
            N, cfg.blocked_slots, slab, cfg.default_rate, cfg.recovery_rate)
        cycle_penalty   = gross_def * (cfg.penalty_pct / 100.0)
        cycle_float_pkr = platform_float_capital(N, cfg.blocked_slots, slab)
        avg_float       = cycle_float_pkr / N if N > 0 else 0.0

        lifecycle = user_lifecycle(cfg, N)
        combined  = (lifecycle["new_users"].values +
                     lifecycle["returning_users"].values).astype(float) / N
        cs_groups = np.concatenate([[0.0], np.cumsum(combined)])

        for m in range(1, M + 1):
            row_lc = lifecycle.iloc[m - 1]
            start  = max(0, m - N)
            gr     = cs_groups[m] - cs_groups[start]
            k      = gr / N

            m_base   = cycle_base_nii  * k
            m_float  = cycle_float_nii * k
            m_fee_nii= cycle_fee_nii   * k
            m_fees   = cycle_fees      * k
            m_pen    = cycle_penalty   * k
            m_loss   = net_def         * k
            m_rev    = m_base + m_float + m_fee_nii + m_fees + m_pen
            m_profit = m_rev - m_loss
            m_a      = m_profit * (cfg.profit_split_party_a / 100.0)

            rows.append({
                "month": m, "year": ((m - 1) // 12) + 1,
                "duration": N, "slab_amount": slab,
                "new_users":       int(row_lc["new_users"]),
                "returning_users": int(row_lc["returning_users"]),
                "active_users":    int(row_lc["active_users_in_cycle"]),
                "churned_users":   int(row_lc["churned_users"]),
                "groups_started_monthly": (row_lc["new_users"] + row_lc["returning_users"]) / N,
                "groups_running_monthly": gr,
                "pot_disbursed_monthly":      pot   * gr,
                "user_contributions_monthly": N * slab * gr,
                "float_outstanding_monthly":  avg_float * gr,
                "base_nii_monthly":       m_base,
                "float_nii_monthly":      m_float,
                "fee_nii_monthly":        m_fee_nii,
                "fees_monthly":           m_fees,
                "penalty_income_monthly": m_pen,
                "default_loss_monthly":   m_loss,
                "total_revenue_monthly":  m_rev,
                "net_profit_monthly":     m_profit,
                "party_a_monthly":        m_a,
                "party_b_monthly":        m_profit - m_a,
            })

    return pd.DataFrame(rows)


def cycle_economics(cfg: BachatConfig, duration: int) -> Dict:
    slab, N     = cfg.slab_amount, duration
    annual_rate = cfg.kibor_rate + cfg.spread
    pot         = N * slab
    user_slots  = N - cfg.blocked_slots
    b_nii  = base_nii_per_cycle(N, slab, annual_rate, cfg.collection_day, cfg.disbursement_day)
    fl_nii = float_nii_per_cycle(N, cfg.blocked_slots, slab, annual_rate)
    fees   = user_slots * pot * (cfg.slot_fee_pct / 100.0)
    f_nii  = fee_nii_per_cycle(fees, N, annual_rate)
    gross_def, net_def = slot_conditional_default_loss(
        N, cfg.blocked_slots, slab, cfg.default_rate, cfg.recovery_rate)
    penalty   = gross_def * (cfg.penalty_pct / 100.0)
    total_rev = b_nii + fl_nii + fees + f_nii + penalty
    fpm       = platform_float_capital(N, cfg.blocked_slots, slab)
    return {
        "duration": N, "pot": pot, "user_slots": user_slots,
        "base_nii": b_nii, "float_nii": fl_nii, "fees": fees, "fee_nii": f_nii,
        "gross_default": gross_def, "net_default": net_def,
        "penalty_income": penalty, "total_revenue": total_rev,
        "net_profit": total_rev - net_def,
        "float_pkr_months": fpm,
        "avg_float_outstanding": fpm / N if N > 0 else 0.0,
        "max_single_default_loss": max(
            (max_debtor_position(N, s, slab) for s in range(cfg.blocked_slots + 1, N + 1)),
            default=0.0),
    }


def build_slot_table(cfg: BachatConfig, duration: int) -> pd.DataFrame:
    slab, N = cfg.slab_amount, duration
    rows = []
    for slot in range(1, N + 1):
        is_plat = slot <= cfg.blocked_slots
        max_d   = 0.0 if is_plat else max_debtor_position(N, slot, slab)
        exp_loss = (0.0 if is_plat else
                    max_d * (cfg.default_rate / 100.0) * (1 - cfg.recovery_rate / 100.0))
        rows.append({
            "Slot": slot,
            "Holder": "PLATFORM" if is_plat else "USER",
            "Receives Pot (PKR)": N * slab,
            "Paid Before Receiving (PKR)": (slot - 1) * slab,
            "Max Debtor Position (PKR)": max_d,
            "Expected Loss (PKR)": exp_loss,
            "Status": ("Platform-held (safe)" if is_plat
                       else ("User: SAFE (last slot)" if slot == N else "User: AT RISK")),
        })
    return pd.DataFrame(rows)


# =============================================================================
# UI HELPERS
# =============================================================================

def fmt_pkr(x: float) -> str:
    if pd.isna(x) or x == 0:
        return "—"
    s = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e7:  return f"{s}PKR {x/1e7:.2f} Cr"
    if x >= 1e5:  return f"{s}PKR {x/1e5:.2f} L"
    if x >= 1e3:  return f"{s}PKR {x/1e3:.1f}k"
    return f"{s}PKR {x:,.0f}"


def _hex_rgba(hex_color: str, alpha: float = 0.18) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _agg_monthly(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = [c for c in df.columns
                if c not in ("month", "year", "duration", "slab_amount")]
    return df.groupby("month")[num_cols].sum().reset_index()


def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, sans-serif;
        color: {INK};
    }}
    .main .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1480px;
    }}

    /* ── Hero ─────────────────────────────── */
    .hero {{
        background: {WHITE};
        border: 1px solid {SLATE_200};
        border-left: 5px solid {BACHAT_GREEN};
        border-radius: 14px;
        padding: 1.4rem 2rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .hero-left h1 {{
        font-size: 1.65rem; font-weight: 800;
        margin: 0; color: {INK}; letter-spacing: -0.025em;
    }}
    .hero-left p {{
        margin: 0.2rem 0 0 0; color: {SLATE_500}; font-size: 0.9rem;
    }}
    .hero-pill {{
        background: {BACHAT_GREEN_LIGHT};
        border: 1px solid {BACHAT_GREEN};
        color: {BACHAT_GREEN_DARK};
        font-size: 0.78rem; font-weight: 600;
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        white-space: nowrap;
    }}

    /* ── KPI / Chart cards ────────────────── */
    [data-testid="stPlotlyChart"] > div {{
        border: 1px solid {SLATE_200};
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(15,23,42,0.06);
        background: {WHITE};
    }}

    /* ── Section headers ──────────────────── */
    .sh {{
        font-size: 1rem; font-weight: 700; color: {INK};
        margin: 1.6rem 0 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid {BACHAT_GREEN};
        display: inline-block;
    }}

    /* ── Verdict pill ─────────────────────── */
    .verdict {{
        display: inline-flex; align-items: center; gap: 0.4rem;
        padding: 0.45rem 1rem; border-radius: 999px;
        font-size: 0.82rem; font-weight: 700; margin-bottom: 1rem;
    }}
    .verdict-good {{ background:{BACHAT_GREEN_LIGHT}; color:{BACHAT_GREEN_DARK}; border:1.5px solid {BACHAT_GREEN}; }}
    .verdict-bad  {{ background:#FEE2E2; color:{DANGER};          border:1.5px solid {DANGER}; }}
    .verdict-warn {{ background:#FEF3C7; color:#92400E;           border:1.5px solid {WARNING}; }}

    /* ── Right panel ──────────────────────── */
    .insights-panel {{
        background: {SLATE_50};
        border: 1px solid {SLATE_200};
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        margin-top: 0.5rem;
    }}
    .insights-panel h4 {{
        font-size: 0.82rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.06em;
        color: {SLATE_500}; margin: 0 0 0.9rem;
    }}
    .insight-item {{
        font-size: 0.83rem; line-height: 1.55; color: {SLATE_700};
        padding: 0.6rem 0; border-bottom: 1px solid {SLATE_200};
    }}
    .insight-item:last-child {{ border-bottom: none; }}
    .insight-item b {{ color: {INK}; }}

    /* ── Audit note box ───────────────────── */
    .audit-box {{
        background: {SLATE_50};
        border: 1px solid {SLATE_200};
        border-left: 3px solid {INFO};
        border-radius: 8px;
        padding: 1rem 1.25rem;
        font-size: 0.87rem; line-height: 1.65;
        color: {SLATE_700};
    }}

    /* ── Sidebar shell ────────────────────── */
    section[data-testid="stSidebar"] {{
        background: {WHITE};
        border-right: 1px solid {SLATE_200};
        padding-bottom: 2rem;
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 0 !important;
    }}

    /* ── Sidebar brand header ─────────────── */
    .sb-brand {{
        background: linear-gradient(135deg, {INK} 0%, {SLATE_700} 100%);
        padding: 1.2rem 1.1rem 1rem;
        margin: 0 0 0.5rem 0;
    }}
    .sb-brand-name {{
        font-size: 1.05rem; font-weight: 800;
        color: {WHITE}; letter-spacing: -0.01em;
        line-height: 1.2; margin: 0;
    }}
    .sb-brand-sub {{
        font-size: 0.72rem; color: rgba(255,255,255,0.55);
        margin: 0.2rem 0 0; letter-spacing: 0.04em;
        text-transform: uppercase;
    }}
    .sb-brand-pill {{
        display: inline-block;
        background: {BACHAT_GREEN};
        color: {INK};
        font-size: 0.65rem; font-weight: 700;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        margin-top: 0.55rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }}

    /* ── Sidebar section cards ─────────────── */
    .sb-section {{
        background: {SLATE_50};
        border: 1px solid {SLATE_200};
        border-radius: 10px;
        padding: 0.85rem 0.9rem 0.6rem;
        margin: 0.6rem 0.7rem;
    }}
    .sb-section-title {{
        display: flex; align-items: center; gap: 0.45rem;
        font-size: 0.7rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.07em;
        color: {SLATE_500};
        margin: 0 0 0.65rem;
        padding-bottom: 0.45rem;
        border-bottom: 1px solid {SLATE_200};
    }}
    .sb-section-icon {{
        width: 18px; height: 18px;
        border-radius: 5px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 0.72rem;
        flex-shrink: 0;
    }}

    /* ── Sidebar label override ────────────── */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stNumberInput label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label {{
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: {SLATE_700} !important;
        margin-bottom: 0.15rem !important;
    }}

    /* ── Slider track color ────────────────── */
    section[data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"] {{
        background: {BACHAT_GREEN} !important;
        border-color: {BACHAT_GREEN} !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="slider"] div[style*="background"] {{
        background: {BACHAT_GREEN} !important;
    }}

    /* ── Input borders ─────────────────────── */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] [data-baseweb="select"] div {{
        border-color: {SLATE_200} !important;
        border-radius: 7px !important;
        font-size: 0.82rem !important;
    }}
    section[data-testid="stSidebar"] input:focus {{
        border-color: {BACHAT_GREEN} !important;
        box-shadow: 0 0 0 2px {BACHAT_GREEN_LIGHT} !important;
    }}

    /* ── Config summary card ───────────────── */
    .sb-summary {{
        background: {BACHAT_GREEN_LIGHT};
        border: 1px solid {BACHAT_GREEN};
        border-radius: 10px;
        padding: 0.8rem 0.9rem;
        margin: 0.6rem 0.7rem 0;
    }}
    .sb-summary-title {{
        font-size: 0.68rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.07em;
        color: {BACHAT_GREEN_DARK}; margin: 0 0 0.6rem;
    }}
    .sb-summary-row {{
        display: flex; justify-content: space-between;
        align-items: center;
        font-size: 0.76rem;
        color: {SLATE_700};
        padding: 0.2rem 0;
        border-bottom: 1px solid rgba(0,160,80,0.15);
    }}
    .sb-summary-row:last-child {{ border-bottom: none; }}
    .sb-summary-row b {{ color: {INK}; font-weight: 700; }}

    /* ── Tabs ─────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0; border-bottom: 2px solid {SLATE_200};
        background: {WHITE};
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 0.7rem 1.4rem; font-weight: 600;
        font-size: 0.88rem; color: {SLATE_500};
        border-radius: 0; border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }}
    .stTabs [aria-selected="true"] {{
        color: {BACHAT_GREEN_DARK} !important;
        border-bottom-color: {BACHAT_GREEN} !important;
    }}

    /* ── Dataframes ───────────────────────── */
    .stDataFrame {{ border: 1px solid {SLATE_200}; border-radius: 10px; }}

    /* ── Streamlit chrome ─────────────────── */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)


def _sb_section(icon: str, title: str, color: str = BACHAT_GREEN):
    """Render a section card header inside the sidebar."""
    st.sidebar.markdown(f"""
    <div class="sb-section-title">
        <span class="sb-section-icon"
              style="background:{color}22; color:{color};">{icon}</span>
        {title}
    </div>""", unsafe_allow_html=True)


def render_sidebar() -> BachatConfig:
    cfg = BachatConfig()

    # ── Brand header ─────────────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div class="sb-brand">
        <div class="sb-brand-name">◉ Bachat ROSCA</div>
        <div class="sb-brand-sub">Pricing &amp; Risk Model</div>
        <span class="sb-brand-pill">v2.1</span>
    </div>""", unsafe_allow_html=True)

    # ── Product ───────────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("📦", "PRODUCT", BACHAT_GREEN)

    chosen = st.sidebar.multiselect(
        "ROSCA Durations (months)",
        [3, 4, 5, 6, 7, 8, 9, 10, 11, 12], default=[6],
        help="Select one or more cycle lengths to model simultaneously")
    if not chosen:
        st.sidebar.error("Select at least one duration.")
        st.stop()
    cfg.durations = sorted(chosen)

    cfg.slab_amount = st.sidebar.number_input(
        "Monthly Contribution (PKR)",
        min_value=1_000, max_value=500_000, value=10_000, step=1_000,
        help="Fixed amount each member contributes per month")

    max_b = min(cfg.durations) - 1
    cfg.blocked_slots = st.sidebar.slider(
        "Platform-Blocked Slots", 0, max(1, max_b), min(1, max_b),
        help="Early slots the platform takes to capture working-capital float")

    cfg.slot_fee_pct = st.sidebar.slider(
        "Slot Fee % of Pot", 0.0, 15.0, 5.0, 0.5,
        help="Fee charged to user slot-winners as % of the full pot")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── User Growth ───────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("👥", "USER GROWTH", INFO)

    cfg.starting_users = st.sidebar.number_input(
        "Starting Users (Month 1)",
        min_value=10, max_value=100_000, value=500, step=50,
        help="Number of users who join in the very first month")
    cfg.monthly_growth_rate = st.sidebar.slider(
        "Monthly Growth %", 0.0, 30.0, 8.0, 0.5,
        help="Month-on-month % growth of the new-user base")
    cfg.churn_rate = st.sidebar.slider(
        "Churn % per Cycle", 0.0, 50.0, 5.0, 0.5,
        help="% of completers who leave permanently after a cycle ends")
    cfg.returning_user_rate = st.sidebar.slider(
        "Returning User Rate %", 0.0, 100.0, 60.0, 1.0,
        help="% of non-churned completers who re-join after their rest period")
    cfg.rest_period_months = st.sidebar.slider(
        "Rest Period (months)", 0, 6, 1,
        help="Months a user sits out between ROSCA cycles")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── Float / NII ───────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("🏦", "FLOAT / NII", PURPLE)

    cfg.kibor_rate = st.sidebar.slider(
        "KIBOR Rate %", 5.0, 30.0, 21.0, 0.25,
        help="Pakistan benchmark interest rate for NII calculations")
    cfg.spread = st.sidebar.slider(
        "Spread vs KIBOR %", -10.0, 5.0, -3.0, 0.25,
        help="Placement rate relative to KIBOR (negative = below benchmark)")

    annual_rate = cfg.kibor_rate + cfg.spread
    rate_color  = BACHAT_GREEN_DARK if annual_rate >= 10 else WARNING
    st.sidebar.markdown(f"""
    <div style="background:{WHITE}; border:1px solid {SLATE_200};
                border-left:3px solid {rate_color};
                border-radius:6px; padding:0.45rem 0.7rem; margin-top:0.3rem;
                font-size:0.78rem; color:{SLATE_700};">
        Effective rate:&nbsp;
        <b style="color:{rate_color}; font-size:0.92rem;">{annual_rate:.2f}%</b>
        &nbsp;(KIBOR {cfg.kibor_rate:.2f}% {cfg.spread:+.2f}%)
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.sidebar.columns(2)
    cfg.collection_day   = col1.number_input(
        "Collection Day", 1, 28, 1, 1,
        help="Day of month when monthly deposits are collected")
    cfg.disbursement_day = col2.number_input(
        "Disbursement Day", 1, 28, 15, 1,
        help="Day of month when the pot is paid to the slot winner")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── Default Risk ──────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("⚠️", "DEFAULT RISK", DANGER)

    cfg.default_rate = st.sidebar.slider(
        "User Default Rate %", 0.0, 30.0, 8.0, 0.5,
        help="% of user-held slots where the member stops paying after receiving the pot")
    cfg.recovery_rate = st.sidebar.slider(
        "Recovery Rate %", 0.0, 100.0, 30.0, 5.0,
        help="% of defaulted exposure recovered through collections or collateral")
    cfg.penalty_pct = st.sidebar.slider(
        "Penalty % on Defaults", 0.0, 10.0, 2.0, 0.5,
        help="Additional fee charged on the defaulted principal — becomes platform income")

    net_exp_pct = cfg.default_rate * (1 - cfg.recovery_rate / 100)
    exp_color   = BACHAT_GREEN_DARK if net_exp_pct < 5 else (WARNING if net_exp_pct < 12 else DANGER)
    st.sidebar.markdown(f"""
    <div style="background:{WHITE}; border:1px solid {SLATE_200};
                border-left:3px solid {exp_color};
                border-radius:6px; padding:0.45rem 0.7rem; margin-top:0.3rem;
                font-size:0.78rem; color:{SLATE_700};">
        Net expected loss rate:&nbsp;
        <b style="color:{exp_color}; font-size:0.92rem;">{net_exp_pct:.1f}%</b>
        &nbsp;({cfg.default_rate:.1f}% × {100-cfg.recovery_rate:.0f}% unrecovered)
    </div>""", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── Profit Split ──────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("🤝", "PROFIT SPLIT", TEAL)

    cfg.profit_split_party_a = st.sidebar.slider(
        "Party A Share %", 0.0, 100.0, 60.0, 1.0,
        help="Platform/operator share of net profit")
    b_share = 100 - cfg.profit_split_party_a
    st.sidebar.markdown(f"""
    <div style="background:{WHITE}; border:1px solid {SLATE_200};
                border-radius:6px; overflow:hidden; margin-top:0.35rem;">
        <div style="display:flex; height:20px; font-size:0.68rem;
                    font-weight:700; line-height:20px;">
            <div style="width:{cfg.profit_split_party_a:.0f}%;
                        background:{BACHAT_GREEN}; color:{INK};
                        text-align:center; white-space:nowrap;
                        overflow:hidden; padding:0 4px;">
                A&nbsp;{cfg.profit_split_party_a:.0f}%
            </div>
            <div style="width:{b_share:.0f}%;
                        background:{INFO}; color:{WHITE};
                        text-align:center; white-space:nowrap;
                        overflow:hidden; padding:0 4px;">
                B&nbsp;{b_share:.0f}%
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── Simulation Horizon ────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("📅", "SIMULATION HORIZON", SLATE_500)

    cfg.simulation_months = st.sidebar.selectbox(
        "Forecast Length",
        [12, 24, 36, 48, 60],
        index=4,
        format_func=lambda x: f"{x} months  ({x//12} year{'s' if x//12>1 else ''})",
        help="Total number of months to simulate")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── Live Config Summary ───────────────────────────────────────────────────
    pot = min(cfg.durations) * cfg.slab_amount
    st.sidebar.markdown(f"""
    <div class="sb-summary">
        <div class="sb-summary-title">◉ Active Configuration</div>
        <div class="sb-summary-row">
            <span>Duration(s)</span>
            <b>{", ".join(f"{d}M" for d in cfg.durations)}</b>
        </div>
        <div class="sb-summary-row">
            <span>Pot (shortest)</span>
            <b>PKR {pot:,}</b>
        </div>
        <div class="sb-summary-row">
            <span>Effective Rate</span>
            <b>{cfg.kibor_rate + cfg.spread:.2f}%</b>
        </div>
        <div class="sb-summary-row">
            <span>Blocked Slots</span>
            <b>{cfg.blocked_slots} of {min(cfg.durations)}</b>
        </div>
        <div class="sb-summary-row">
            <span>Net Loss Rate</span>
            <b>{cfg.default_rate * (1 - cfg.recovery_rate/100):.1f}%</b>
        </div>
        <div class="sb-summary-row">
            <span>Horizon</span>
            <b>{cfg.simulation_months} months</b>
        </div>
    </div>""", unsafe_allow_html=True)

    return cfg


# =============================================================================
# SMART INSIGHTS
# =============================================================================

def generate_insights(cfg: BachatConfig, df: pd.DataFrame) -> List[str]:
    agg    = _agg_monthly(df)
    yearly = df.groupby("year").agg(
        revenue=("total_revenue_monthly", "sum"),
        profit =("net_profit_monthly",    "sum"),
    ).reset_index()

    eco         = cycle_economics(cfg, cfg.durations[0])
    annual_rate = cfg.kibor_rate + cfg.spread
    insights    = []

    # 1 — peak profit month
    peak_idx = agg["net_profit_monthly"].idxmax()
    peak_m   = int(agg.loc[peak_idx, "month"])
    peak_v   = agg.loc[peak_idx, "net_profit_monthly"]
    insights.append(
        f"Peak monthly profit of <b>{fmt_pkr(peak_v)}</b> reached in "
        f"Month {peak_m} (Year {((peak_m-1)//12)+1})."
    )

    # 2 — Y1 → Y2 revenue growth
    if len(yearly) >= 2:
        y1 = yearly.loc[yearly["year"]==1, "revenue"].values[0]
        y2 = yearly.loc[yearly["year"]==2, "revenue"].values[0]
        g  = (y2 - y1) / y1 * 100 if y1 else 0
        insights.append(
            f"Revenue grows <b>{g:+.1f}%</b> from Year 1 to Year 2 "
            f"({fmt_pkr(y1)} → {fmt_pkr(y2)})."
        )

    # 3 — float capture
    insights.append(
        f"Platform captures <b>{fmt_pkr(eco['avg_float_outstanding'])}</b> avg float "
        f"per cycle via {cfg.blocked_slots} blocked slot(s), earning "
        f"<b>{fmt_pkr(eco['float_nii'])}</b> NII/cycle at {annual_rate:.1f}%."
    )

    # 4 — breakeven default rate
    for r in range(0, 51):
        c2 = dataclasses.replace(cfg, default_rate=float(r))
        if cycle_economics(c2, cfg.durations[0])["net_profit"] < 0:
            safety = r - cfg.default_rate
            insights.append(
                f"Breakeven default rate: <b>{r}%</b>. "
                f"Current {cfg.default_rate:.0f}% leaves a "
                f"<b>{safety:.0f} ppt safety margin</b>."
            )
            break

    # 5 — default share of revenue
    total_loss = df["default_loss_monthly"].sum()
    total_rev  = df["total_revenue_monthly"].sum()
    loss_pct   = total_loss / total_rev * 100 if total_rev else 0
    insights.append(
        f"Default losses consume <b>{loss_pct:.1f}%</b> of total revenue "
        f"({fmt_pkr(total_loss)} of {fmt_pkr(total_rev)})."
    )

    # 6 — returning-user share
    total_ret = df["returning_users"].sum()
    total_new = df["new_users"].sum()
    total_all = total_new + total_ret
    if total_all > 0:
        ret_pct = total_ret / total_all * 100
        insights.append(
            f"Returning users are <b>{ret_pct:.0f}%</b> of total activity "
            f"({total_ret:,} of {total_all:,}) — "
            f"driven by {cfg.returning_user_rate:.0f}% return rate."
        )

    return insights


# =============================================================================
# VIZ
# =============================================================================

def _theme(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=INK, family="Inter"),
                   x=0.0, xanchor="left", pad=dict(b=8)),
        template=PLOTLY_TEMPLATE,
        font=dict(family="Inter", size=12, color=SLATE_700),
        colorway=PLOTLY_COLORWAY,
        height=height,
        margin=dict(l=16, r=16, t=48, b=36),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        xaxis=dict(gridcolor=SLATE_100, linecolor=SLATE_200, zeroline=False),
        yaxis=dict(gridcolor=SLATE_100, linecolor=SLATE_200, zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1.0, font=dict(size=11)),
        hovermode="x unified",
    )
    return fig


# ── KPI card with sparkline (text annotations + sparkline trace) ─────────────

def chart_kpi(label: str, value_str: str, sub: str,
              data: np.ndarray, color: str,
              delta_str: str = "", height: int = 155) -> go.Figure:
    """Full KPI card as a single Plotly figure.
    Sparkline occupies the bottom 38% of the y-axis range;
    metric text floats above via annotations — no double rendering."""
    y  = list(data) if data is not None and len(data) > 0 else [0, 0]
    x  = list(range(len(y)))
    lo, hi = min(y), max(y)
    span   = (hi - lo) if hi != lo else 1.0
    # Scale so data sits in [0, 0.38]; text lives in [0.42, 1]
    ys = [(v - lo) / span * 0.38 for v in y]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=ys, mode="lines",
        line=dict(color=color, width=2.5),
        fill="tozeroy", fillcolor=_hex_rgba(color, 0.18),
        hoverinfo="skip",
    ))

    # Metric label
    fig.add_annotation(
        text=label, xref="paper", yref="paper",
        x=0.05, y=0.98, xanchor="left", yanchor="top", showarrow=False,
        font=dict(size=10, color=SLATE_500, family="Inter"),
    )
    # Main value
    fig.add_annotation(
        text=f"<b>{value_str}</b>", xref="paper", yref="paper",
        x=0.05, y=0.83, xanchor="left", yanchor="top", showarrow=False,
        font=dict(size=20, color=INK, family="Inter"),
    )
    # Sub-label
    if sub:
        fig.add_annotation(
            text=sub, xref="paper", yref="paper",
            x=0.05, y=0.61, xanchor="left", yanchor="top", showarrow=False,
            font=dict(size=10, color=SLATE_500, family="Inter"),
        )
    # Delta badge (top-right)
    if delta_str:
        dc = BACHAT_GREEN_DARK if delta_str.startswith("+") else DANGER
        fig.add_annotation(
            text=f"<b>{delta_str}</b>", xref="paper", yref="paper",
            x=0.97, y=0.98, xanchor="right", yanchor="top", showarrow=False,
            font=dict(size=11, color=dc, family="Inter"),
        )

    fig.update_layout(
        height=height,
        margin=dict(l=14, r=14, t=14, b=8),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True, range=[0, 1.05]),
        showlegend=False,
    )
    return fig


# ── Gauge ─────────────────────────────────────────────────────────────────────

def chart_gauge(value: float, title: str, max_val: float = 100.0,
                suffix: str = "%", color: str = BACHAT_GREEN) -> go.Figure:
    """Semi-circular gauge with colour-banded background."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": suffix, "font": {"size": 30, "color": INK, "family": "Inter"},
                "valueformat": ".1f"},
        title={"text": title,
               "font": {"size": 12, "color": SLATE_500, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, max_val], "tickwidth": 1,
                     "tickcolor": SLATE_300, "tickfont": {"size": 9}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": WHITE, "borderwidth": 0,
            "steps": [
                {"range": [0,           max_val * 0.33], "color": "#FEE2E2"},
                {"range": [max_val*0.33, max_val * 0.66], "color": "#FEF3C7"},
                {"range": [max_val*0.66, max_val],        "color": BACHAT_GREEN_LIGHT},
            ],
            "threshold": {"line": {"color": INK, "width": 2.5},
                          "thickness": 0.85, "value": value},
        },
    ))
    fig.update_layout(
        height=210,
        margin=dict(l=24, r=24, t=30, b=10),
        paper_bgcolor=WHITE,
        font=dict(family="Inter"),
    )
    return fig


# ── Combo: stacked revenue bars + dual-axis profit margin line ────────────────

def chart_combo(df: pd.DataFrame) -> go.Figure:
    d     = _agg_monthly(df)
    total = d["total_revenue_monthly"].replace(0, np.nan)
    margin = d["net_profit_monthly"] / total * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    components = [
        ("Slot Fees",  "fees_monthly",           BACHAT_GREEN),
        ("Base NII",   "base_nii_monthly",        INFO),
        ("Float NII",  "float_nii_monthly",       PURPLE),
        ("Fee NII",    "fee_nii_monthly",         TEAL),
        ("Penalty",    "penalty_income_monthly",  WARNING),
    ]
    for name, col, clr in components:
        fig.add_trace(go.Bar(x=d["month"], y=d[col], name=name,
                             marker_color=clr, marker_opacity=0.88),
                      secondary_y=False)

    fig.add_trace(go.Scatter(
        x=d["month"], y=margin,
        mode="lines+markers", name="Profit Margin %",
        line=dict(color=INK, width=2.5),
        marker=dict(size=4, color=INK),
    ), secondary_y=True)

    fig.update_layout(
        barmode="stack", height=390,
        margin=dict(l=16, r=16, t=50, b=36),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        font=dict(family="Inter", size=12, color=SLATE_700),
        legend=dict(orientation="h", y=1.04, x=1.0,
                    xanchor="right", font=dict(size=10)),
        hovermode="x unified",
        title=dict(text="Monthly Revenue Composition & Profit Margin",
                   font=dict(size=14, color=INK), x=0),
        xaxis=dict(title="Month", gridcolor=SLATE_100, linecolor=SLATE_200),
    )
    fig.update_yaxes(title_text="Revenue (PKR)", secondary_y=False,
                     gridcolor=SLATE_100, linecolor=SLATE_200)
    fig.update_yaxes(title_text="Profit Margin %", secondary_y=True,
                     ticksuffix="%", showgrid=False)
    return fig


# ── Horizontal income statement (right panel) ─────────────────────────────────

def chart_income_h(df: pd.DataFrame) -> go.Figure:
    total_rev = df["total_revenue_monthly"].sum()
    items = [
        ("Revenue",     "total_revenue_monthly",  BACHAT_GREEN),
        ("Slot Fees",   "fees_monthly",            INFO),
        ("Base NII",    "base_nii_monthly",        PURPLE),
        ("Float NII",   "float_nii_monthly",       TEAL),
        ("Fee NII",     "fee_nii_monthly",         "#A78BFA"),
        ("Penalty",     "penalty_income_monthly",  WARNING),
        ("Default Loss","default_loss_monthly",    DANGER),
        ("Net Profit",  "net_profit_monthly",      INK),
    ]
    labels = [i[0] for i in items]
    values = [df[i[1]].sum() for i in items]
    colors = [i[2] for i in items]
    pcts   = [abs(v) / total_rev * 100 if total_rev else 0 for v in values]

    fig = go.Figure(go.Bar(
        y=labels, x=pcts,
        orientation="h",
        marker_color=colors,
        text=[fmt_pkr(v) for v in values],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(size=10, color=WHITE, family="Inter"),
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=42, b=10),
        paper_bgcolor=WHITE, plot_bgcolor=SLATE_50,
        xaxis=dict(visible=False, fixedrange=True, range=[0, 115]),
        yaxis=dict(autorange="reversed",
                   tickfont=dict(size=11, color=SLATE_700, family="Inter"),
                   gridcolor=SLATE_200),
        showlegend=False,
        title=dict(text="Income Statement", font=dict(size=13, color=INK,
                                                      family="Inter"), x=0),
    )
    return fig


# ── P&L line chart ────────────────────────────────────────────────────────────

def chart_pnl(df: pd.DataFrame) -> go.Figure:
    d = _agg_monthly(df)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["month"], y=d["total_revenue_monthly"],
                             mode="lines", name="Revenue",
                             line=dict(color=BACHAT_GREEN, width=2.5)))
    fig.add_trace(go.Scatter(x=d["month"], y=d["default_loss_monthly"],
                             mode="lines", name="Default Loss",
                             line=dict(color=DANGER, width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=d["month"], y=d["net_profit_monthly"],
                             mode="lines", name="Net Profit",
                             line=dict(color=INK, width=3),
                             fill="tozeroy",
                             fillcolor=_hex_rgba(BACHAT_GREEN, 0.08)))
    return _theme(fig, "Revenue vs Default Loss vs Net Profit", height=390)


# ── User lifecycle ────────────────────────────────────────────────────────────

def chart_users(df: pd.DataFrame) -> go.Figure:
    d = _agg_monthly(df)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["month"], y=d["active_users"],
                             mode="lines", name="Active",
                             line=dict(color=BACHAT_GREEN, width=3),
                             fill="tozeroy",
                             fillcolor=_hex_rgba(BACHAT_GREEN, 0.1)))
    fig.add_trace(go.Scatter(x=d["month"], y=d["new_users"],
                             mode="lines", name="New",
                             line=dict(color=INFO, width=2)))
    fig.add_trace(go.Scatter(x=d["month"], y=d["returning_users"],
                             mode="lines", name="Returning",
                             line=dict(color=PURPLE, width=2)))
    return _theme(fig, "User Lifecycle", height=360)


# ── Float outstanding ─────────────────────────────────────────────────────────

def chart_float(df: pd.DataFrame) -> go.Figure:
    d = _agg_monthly(df)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["month"], y=d["float_outstanding_monthly"],
                             mode="lines", name="Float",
                             line=dict(color=PURPLE, width=3),
                             fill="tozeroy",
                             fillcolor=_hex_rgba(PURPLE, 0.12)))
    return _theme(fig, "Platform Float Capital Outstanding", height=310)


# ── Slot risk ─────────────────────────────────────────────────────────────────

def chart_slot_risk(slot_df: pd.DataFrame) -> go.Figure:
    colors = [
        BACHAT_GREEN if h == "PLATFORM"
        else (DANGER if "AT RISK" in s else BACHAT_GREEN_DARK)
        for h, s in zip(slot_df["Holder"], slot_df["Status"])
    ]
    fig = go.Figure(go.Bar(
        x=[f"Slot {s}" for s in slot_df["Slot"]],
        y=slot_df["Max Debtor Position (PKR)"],
        marker_color=colors,
        text=[fmt_pkr(v) for v in slot_df["Max Debtor Position (PKR)"]],
        textposition="outside", textfont=dict(size=11),
    ))
    return _theme(fig, "Per-Slot Maximum Default Exposure", height=360)


# ── Blocking sensitivity ──────────────────────────────────────────────────────

def chart_blocking_sensitivity(cfg: BachatConfig, duration: int) -> go.Figure:
    blocks_range = list(range(0, duration))
    profits, exposures, floats = [], [], []
    for k in blocks_range:
        c2  = dataclasses.replace(cfg, blocked_slots=k, durations=[duration])
        eco = cycle_economics(c2, duration)
        profits.append(eco["net_profit"])
        exposures.append(eco["net_default"])
        floats.append(eco["avg_float_outstanding"])

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=blocks_range, y=profits, name="Net Profit / cycle",
                         marker_color=BACHAT_GREEN, marker_opacity=0.85),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=blocks_range, y=exposures,
                             name="Expected Default Loss",
                             line=dict(color=DANGER, width=3),
                             mode="lines+markers"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=blocks_range, y=floats,
                             name="Avg Float Outstanding",
                             line=dict(color=PURPLE, width=2.5, dash="dot"),
                             mode="lines+markers"),
                  secondary_y=True)
    fig.update_xaxes(title_text="Number of Blocked Slots")
    fig.update_yaxes(title_text="Profit / Loss (PKR)", secondary_y=False)
    fig.update_yaxes(title_text="Float (PKR)", secondary_y=True, showgrid=False)
    fig.update_layout(
        height=400, barmode="overlay",
        margin=dict(l=16, r=16, t=50, b=36),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        font=dict(family="Inter", size=12, color=SLATE_700),
        legend=dict(orientation="h", y=1.04, x=1.0, xanchor="right",
                    font=dict(size=10)),
        title=dict(text=f"Blocking Strategy Sensitivity — {duration}-month ROSCA",
                   font=dict(size=14, color=INK), x=0),
        hovermode="x unified",
    )
    return fig


# ── Duration comparison ───────────────────────────────────────────────────────

def chart_duration_comparison(df: pd.DataFrame) -> go.Figure:
    s = df.groupby("duration").agg(
        revenue=("total_revenue_monthly", "sum"),
        profit =("net_profit_monthly",    "sum"),
    ).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=s["duration"].astype(str) + "M",
                         y=s["revenue"], name="Revenue",
                         marker_color=BACHAT_GREEN, marker_opacity=0.85))
    fig.add_trace(go.Bar(x=s["duration"].astype(str) + "M",
                         y=s["profit"],  name="Net Profit",
                         marker_color=INFO, marker_opacity=0.85))
    fig.update_layout(barmode="group")
    return _theme(fig, "Revenue & Net Profit by Duration", height=320)


# =============================================================================
# TABS
# =============================================================================

_CFG_STATIC = {"displayModeBar": False, "staticPlot": False,
               "scrollZoom": False}


def _sh(text: str):
    st.markdown(f'<div class="sh">{text}</div>', unsafe_allow_html=True)


def tab_overview(cfg: BachatConfig, df: pd.DataFrame):
    agg         = _agg_monthly(df)
    eco         = cycle_economics(cfg, cfg.durations[0])
    total_rev   = df["total_revenue_monthly"].sum()
    total_profit= df["net_profit_monthly"].sum()
    total_users = df["new_users"].sum() + df["returning_users"].sum()
    avg_active  = agg["active_users"].mean()

    # YoY delta for KPI deltas (last year vs year 1)
    def _yr_delta(col):
        yr_max = df["year"].max()
        y1  = df[df["year"]==1][col].sum()
        yn  = df[df["year"]==yr_max][col].sum()
        d   = (yn - y1) / y1 * 100 if y1 else 0
        return f"{d:+.1f}%" if yr_max > 1 else ""

    # Verdict
    verdict_cls  = "verdict-good" if eco["net_profit"] >= 0 else "verdict-bad"
    verdict_text = ("✓ PROFITABLE · MANAGEABLE RISK" if eco["net_profit"] >= 0
                    else "✗ UNPROFITABLE · ADJUST PARAMETERS")
    st.markdown(f'<div class="verdict {verdict_cls}">{verdict_text}</div>',
                unsafe_allow_html=True)

    # ── Layout: left (3) | right (1) ─────────────────────────────────────────
    left, right = st.columns([3.2, 1.0], gap="medium")

    with left:
        # ── Row 1: KPI sparkline cards ────────────────────────────────────
        k1, k2, k3, k4 = st.columns(4, gap="small")
        with k1:
            st.plotly_chart(
                chart_kpi("TOTAL REVENUE", fmt_pkr(total_rev),
                          f"Over {cfg.simulation_months} months",
                          agg["total_revenue_monthly"].values, BACHAT_GREEN,
                          _yr_delta("total_revenue_monthly")),
                use_container_width=True, config=_CFG_STATIC)
        with k2:
            tone = "+" if total_profit >= 0 else ""
            margin = total_profit / total_rev * 100 if total_rev else 0
            st.plotly_chart(
                chart_kpi("NET PROFIT", fmt_pkr(total_profit),
                          f"Margin: {margin:.1f}%",
                          agg["net_profit_monthly"].values,
                          BACHAT_GREEN if total_profit >= 0 else DANGER,
                          _yr_delta("net_profit_monthly")),
                use_container_width=True, config=_CFG_STATIC)
        with k3:
            st.plotly_chart(
                chart_kpi("AVG ACTIVE USERS", f"{avg_active:,.0f}",
                          f"Total joined: {total_users:,}",
                          agg["active_users"].values, INFO,
                          _yr_delta("new_users")),
                use_container_width=True, config=_CFG_STATIC)
        with k4:
            total_float = df["float_outstanding_monthly"].sum()
            st.plotly_chart(
                chart_kpi("FLOAT CAPTURED", fmt_pkr(total_float),
                          f"{cfg.blocked_slots} blocked slot(s)",
                          agg["float_outstanding_monthly"].values, PURPLE,
                          ""),
                use_container_width=True, config=_CFG_STATIC)

        # ── Row 2: gauge metrics ──────────────────────────────────────────
        _sh("Key Ratios")
        g1, g2, g3 = st.columns(3, gap="small")
        with g1:
            pm = total_profit / total_rev * 100 if total_rev else 0
            st.plotly_chart(chart_gauge(pm, "Net Profit Margin", 60, "%",
                                        BACHAT_GREEN if pm >= 0 else DANGER),
                            use_container_width=True, config=_CFG_STATIC)
        with g2:
            total_fees = df["fees_monthly"].sum()
            fee_yield  = total_fees / df["user_contributions_monthly"].sum() * 100 \
                         if df["user_contributions_monthly"].sum() else 0
            st.plotly_chart(chart_gauge(fee_yield, "Fee Yield %", 15, "%", INFO),
                            use_container_width=True, config=_CFG_STATIC)
        with g3:
            total_loss = df["default_loss_monthly"].sum()
            def_impact = total_loss / total_rev * 100 if total_rev else 0
            st.plotly_chart(chart_gauge(def_impact, "Default Impact on Revenue",
                                        30, "%", DANGER),
                            use_container_width=True, config=_CFG_STATIC)

        # ── Duration comparison (multi-duration only) ─────────────────────
        if len(cfg.durations) > 1:
            _sh("By Duration")
            st.plotly_chart(chart_duration_comparison(df),
                            use_container_width=True, config=_CFG_STATIC)

        # ── Combo chart ───────────────────────────────────────────────────
        _sh("Monthly Revenue & Profit Margin")
        st.plotly_chart(chart_combo(df),
                        use_container_width=True, config=_CFG_STATIC)

    # ── Right panel ───────────────────────────────────────────────────────
    with right:
        st.markdown(f"""
        <div style="background:{SLATE_50}; border:1px solid {SLATE_200};
                    border-radius:10px; padding:0.7rem 0.9rem; margin-bottom:0.8rem;
                    font-size:0.8rem; color:{SLATE_500};">
            <b style="color:{INK};">Showing data for:</b><br>
            Last {cfg.simulation_months} months
            across {len(cfg.durations)} duration(s) —
            {", ".join(f"{d}M" for d in cfg.durations)}
        </div>""", unsafe_allow_html=True)

        st.plotly_chart(chart_income_h(df),
                        use_container_width=True, config=_CFG_STATIC)

        # Smart Insights
        st.markdown(f"""
        <div class="insights-panel">
            <h4>💡 Smart Insights</h4>""", unsafe_allow_html=True)
        for ins in generate_insights(cfg, df):
            st.markdown(f'<div class="insight-item">{ins}</div>',
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def tab_risk(cfg: BachatConfig, df: pd.DataFrame):
    _sh("Slot-Level Risk Decomposition")
    st.caption(
        "Platform-held slots are safe by construction. User exposure = "
        "(N − slot) × monthly contribution. Last slot is always safe."
    )

    for dur in cfg.durations:
        header = f"{dur}-month ROSCA"
        with (st.expander(header, expanded=True) if len(cfg.durations) > 1
              else st.container()):
            eco     = cycle_economics(cfg, dur)
            slot_df = build_slot_table(cfg, dur)

            left, right = st.columns([1.6, 1.0], gap="medium")
            with left:
                st.plotly_chart(chart_slot_risk(slot_df),
                                use_container_width=True, config=_CFG_STATIC)
            with right:
                k1, k2 = st.columns(2, gap="small")
                with k1:
                    st.plotly_chart(
                        chart_kpi("POT PER GROUP", fmt_pkr(eco["pot"]),
                                  f"{dur} × {fmt_pkr(cfg.slab_amount)}",
                                  [], BACHAT_GREEN),
                        use_container_width=True, config=_CFG_STATIC)
                    st.plotly_chart(
                        chart_kpi("MAX SINGLE DEFAULT",
                                  fmt_pkr(eco["max_single_default_loss"]),
                                  "Worst-case exposure", [], DANGER),
                        use_container_width=True, config=_CFG_STATIC)
                with k2:
                    st.plotly_chart(
                        chart_kpi("NET DEFAULT LOSS",
                                  fmt_pkr(eco["net_default"]),
                                  f"After {cfg.recovery_rate:.0f}% recovery",
                                  [], WARNING),
                        use_container_width=True, config=_CFG_STATIC)
                    st.plotly_chart(
                        chart_kpi("PENALTY INCOME",
                                  fmt_pkr(eco["penalty_income"]),
                                  f"{cfg.penalty_pct:.1f}% on defaulted",
                                  [], TEAL),
                        use_container_width=True, config=_CFG_STATIC)

            display_df = slot_df.copy()
            for col in ["Receives Pot (PKR)", "Paid Before Receiving (PKR)",
                        "Max Debtor Position (PKR)", "Expected Loss (PKR)"]:
                display_df[col] = display_df[col].apply(fmt_pkr)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    _sh("Blocking Strategy Sensitivity")
    st.caption(
        "Net profit, default exposure, and float vs blocked-slot count. "
        "Sweet spot is usually 1–2 blocked slots."
    )
    st.plotly_chart(chart_blocking_sensitivity(cfg, cfg.durations[0]),
                    use_container_width=True, config=_CFG_STATIC)


def tab_revenue(cfg: BachatConfig, df: pd.DataFrame):
    agg = _agg_monthly(df)

    _sh("Revenue Composition")
    st.caption(
        "Five sources, three distinct NII principals — no double-counting. "
        "Slot Fees are the headline; each NII type earns on a different balance."
    )

    left, right = st.columns([2.2, 1.0], gap="medium")

    with left:
        # Stacked area revenue
        fig = go.Figure()
        components = [
            ("Slot Fees",  "fees_monthly",          BACHAT_GREEN),
            ("Base NII",   "base_nii_monthly",       INFO),
            ("Float NII",  "float_nii_monthly",      PURPLE),
            ("Fee NII",    "fee_nii_monthly",        TEAL),
            ("Penalty",    "penalty_income_monthly", WARNING),
        ]
        for name, col, clr in components:
            fig.add_trace(go.Bar(x=agg["month"], y=agg[col], name=name,
                                 marker_color=clr, marker_opacity=0.88))
        fig.update_layout(barmode="stack")
        _theme(fig, "Monthly Revenue Stack", height=360)
        st.plotly_chart(fig, use_container_width=True, config=_CFG_STATIC)

    with right:
        eco     = cycle_economics(cfg, cfg.durations[0])
        annual  = cfg.kibor_rate + cfg.spread
        per_cyc = [
            ("Slot Fees",  eco["fees"],         BACHAT_GREEN),
            ("Base NII",   eco["base_nii"],      INFO),
            ("Float NII",  eco["float_nii"],     PURPLE),
            ("Fee NII",    eco["fee_nii"],       TEAL),
            ("Penalty",    eco["penalty_income"],WARNING),
            ("Net Profit", eco["net_profit"],    INK),
        ]
        labels = [i[0] for i in per_cyc]
        values = [i[1] for i in per_cyc]
        colors = [i[2] for i in per_cyc]
        pcts   = [v / eco["total_revenue"] * 100 if eco["total_revenue"] else 0
                  for v in values]

        fig2 = go.Figure(go.Bar(
            y=labels, x=[abs(p) for p in pcts], orientation="h",
            marker_color=colors,
            text=[fmt_pkr(v) for v in values],
            textposition="inside", insidetextanchor="start",
            textfont=dict(size=10, color=WHITE),
        ))
        fig2.update_layout(
            height=310,
            margin=dict(l=10, r=10, t=42, b=10),
            paper_bgcolor=WHITE, plot_bgcolor=SLATE_50,
            xaxis=dict(visible=False, fixedrange=True),
            yaxis=dict(autorange="reversed",
                       tickfont=dict(size=11, color=SLATE_700)),
            showlegend=False,
            title=dict(text="Per-Cycle Breakdown",
                       font=dict(size=13, color=INK), x=0),
        )
        st.plotly_chart(fig2, use_container_width=True, config=_CFG_STATIC)

    _sh("NII Methodology — Audit Note")
    idle = max(0, cfg.disbursement_day - cfg.collection_day)
    st.markdown(f"""
    <div class="audit-box">
    <b>Base NII</b> — Full pot ({cfg.durations[0]} × PKR {cfg.slab_amount:,}) sits idle
    for {idle} days/month (collection day {cfg.collection_day} →
    disbursement day {cfg.disbursement_day}). 30/360 convention.
    Rate = {annual:.2f}% (KIBOR + spread).<br><br>
    <b>Float NII</b> — When the platform takes the first {cfg.blocked_slots} slot(s),
    it holds other members' contributions as working capital.
    Principal = PKR-months of float × monthly rate.
    <em>Entirely different principal from Base NII.</em><br><br>
    <b>Fee NII</b> — Collected fees sit for ~{cfg.durations[0]*15} days on average
    (half-cycle). Computed only on the fee principal.
    <em>No overlap with either above.</em><br><br>
    <b>Total NII = Base + Float + Fee, zero overlap.</b>
    The v1 model applied the same principal to all three — corrected here.
    </div>""", unsafe_allow_html=True)


def tab_users(cfg: BachatConfig, df: pd.DataFrame):
    agg = _agg_monthly(df)

    total_new  = df["new_users"].sum()
    total_ret  = df["returning_users"].sum()
    total_all  = total_new + total_ret
    total_chur = df["churned_users"].sum()
    avg_active = agg["active_users"].mean()

    _sh("User Lifecycle Overview")
    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        st.plotly_chart(
            chart_kpi("NEW USERS", f"{total_new:,}",
                      f"{cfg.monthly_growth_rate:.1f}% monthly growth",
                      agg["new_users"].values, BACHAT_GREEN),
            use_container_width=True, config=_CFG_STATIC)
    with k2:
        ret_pct = total_ret / total_all * 100 if total_all else 0
        st.plotly_chart(
            chart_kpi("RETURNING", f"{total_ret:,}",
                      f"{ret_pct:.0f}% of total activity",
                      agg["returning_users"].values, PURPLE),
            use_container_width=True, config=_CFG_STATIC)
    with k3:
        st.plotly_chart(
            chart_kpi("CHURNED", f"{total_chur:,}",
                      f"{cfg.churn_rate:.0f}% per cycle",
                      agg["churned_users"].values, DANGER),
            use_container_width=True, config=_CFG_STATIC)
    with k4:
        st.plotly_chart(
            chart_kpi("AVG ACTIVE", f"{avg_active:,.0f}",
                      "Users in-cycle per month",
                      agg["active_users"].values, INFO),
            use_container_width=True, config=_CFG_STATIC)

    left, right = st.columns([2, 1], gap="medium")
    with left:
        st.plotly_chart(chart_users(df),
                        use_container_width=True, config=_CFG_STATIC)
    with right:
        st.plotly_chart(chart_float(df),
                        use_container_width=True, config=_CFG_STATIC)

    _sh("Monthly Detail")
    show = agg[["month", "new_users", "returning_users",
                "active_users", "churned_users",
                "groups_running_monthly"]].copy()
    show.insert(1, "year", ((show["month"] - 1) // 12 + 1))
    show["groups_running_monthly"] = show["groups_running_monthly"].round(1)
    st.dataframe(show, use_container_width=True, hide_index=True, height=380)


def tab_pnl(cfg: BachatConfig, df: pd.DataFrame):
    yearly = df.groupby("year").agg(
        new_users   =("new_users",             "sum"),
        revenue     =("total_revenue_monthly",  "sum"),
        def_loss    =("default_loss_monthly",   "sum"),
        net_profit  =("net_profit_monthly",     "sum"),
        party_a     =("party_a_monthly",        "sum"),
        party_b     =("party_b_monthly",        "sum"),
    ).reset_index()

    a_lbl = f"Party A ({cfg.profit_split_party_a:.0f}%)"
    b_lbl = f"Party B ({100-cfg.profit_split_party_a:.0f}%)"
    yearly.columns = ["Year", "New Users", "Revenue",
                      "Default Loss", "Net Profit", a_lbl, b_lbl]

    # KPI row for totals
    _sh("5-Year Summary")
    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        st.plotly_chart(
            chart_kpi("5-YR REVENUE", fmt_pkr(yearly["Revenue"].sum()),
                      f"{len(yearly)} years",
                      yearly["Revenue"].values, BACHAT_GREEN),
            use_container_width=True, config=_CFG_STATIC)
    with k2:
        st.plotly_chart(
            chart_kpi("5-YR NET PROFIT", fmt_pkr(yearly["Net Profit"].sum()),
                      f"Margin: {yearly['Net Profit'].sum()/yearly['Revenue'].sum()*100:.1f}%",
                      yearly["Net Profit"].values,
                      BACHAT_GREEN if yearly["Net Profit"].sum() >= 0 else DANGER),
            use_container_width=True, config=_CFG_STATIC)
    with k3:
        st.plotly_chart(
            chart_kpi(a_lbl.upper(), fmt_pkr(yearly[a_lbl].sum()),
                      "Platform share", yearly[a_lbl].values, INFO),
            use_container_width=True, config=_CFG_STATIC)
    with k4:
        st.plotly_chart(
            chart_kpi(b_lbl.upper(), fmt_pkr(yearly[b_lbl].sum()),
                      "Partner share", yearly[b_lbl].values, PURPLE),
            use_container_width=True, config=_CFG_STATIC)

    left, right = st.columns([2, 1], gap="medium")

    with left:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=yearly["Year"], y=yearly["Revenue"],
                             name="Revenue", marker_color=BACHAT_GREEN,
                             marker_opacity=0.85))
        fig.add_trace(go.Bar(x=yearly["Year"], y=-yearly["Default Loss"],
                             name="Default Loss", marker_color=DANGER,
                             marker_opacity=0.85))
        fig.add_trace(go.Scatter(x=yearly["Year"], y=yearly["Net Profit"],
                                 name="Net Profit", mode="lines+markers",
                                 line=dict(color=INK, width=3),
                                 marker=dict(size=10, color=INK)))
        fig.update_layout(barmode="relative")
        st.plotly_chart(_theme(fig, "Annual P&L", height=360),
                        use_container_width=True, config=_CFG_STATIC)

    with right:
        display = yearly.copy()
        for col in display.columns[2:]:
            display[col] = display[col].apply(
                lambda x: fmt_pkr(x) if isinstance(x, float) else f"{x:,}")
        st.dataframe(display, use_container_width=True, hide_index=True)

        # Profit split donut
        total_a = yearly[a_lbl].sum()
        total_b = yearly[b_lbl].sum()
        fig_d = go.Figure(go.Pie(
            labels=[a_lbl, b_lbl],
            values=[max(0, total_a), max(0, total_b)],
            hole=0.55,
            marker_colors=[BACHAT_GREEN, INFO],
            textinfo="percent+label",
            textfont=dict(size=11, family="Inter"),
        ))
        fig_d.update_layout(
            height=240, margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor=WHITE,
            title=dict(text="Profit Split", font=dict(size=13, color=INK), x=0),
            showlegend=False,
        )
        st.plotly_chart(fig_d, use_container_width=True, config=_CFG_STATIC)


def tab_sensitivity(cfg: BachatConfig):
    _sh("Default Rate Sensitivity")
    st.caption("Net profit per cycle vs default rate. Zero-crossing = breakeven.")

    rates = np.arange(0, 31, 1)
    fig = go.Figure()
    for dur, color in zip([3, 6, 9, 12], PLOTLY_COLORWAY):
        profits = [cycle_economics(
            dataclasses.replace(cfg, default_rate=float(r), durations=[dur]), dur
        )["net_profit"] for r in rates]
        fig.add_trace(go.Scatter(x=rates, y=profits, mode="lines",
                                 name=f"{dur}M", line=dict(color=color, width=2.5)))
    fig.add_hline(y=0, line=dict(color=SLATE_500, width=1.5, dash="dash"))
    fig.add_vline(x=cfg.default_rate, line=dict(color=WARNING, width=2, dash="dot"),
                  annotation_text=f"Current: {cfg.default_rate:.0f}%",
                  annotation_font=dict(size=11, color=WARNING))
    fig.update_xaxes(title_text="User Default Rate (%)")
    fig.update_yaxes(title_text="Net Profit per Cycle (PKR)")
    st.plotly_chart(_theme(fig, "Profit per Cycle vs Default Rate", height=400),
                    use_container_width=True, config=_CFG_STATIC)

    _sh("Fee Sensitivity")
    st.caption("How net profit responds to fee % at different blocking levels.")
    fees_range  = np.arange(0, 16, 0.5)
    primary_dur = cfg.durations[0]
    fig2 = go.Figure()
    for blocks, color in zip(range(0, min(4, primary_dur)), PLOTLY_COLORWAY):
        profits = [cycle_economics(
            dataclasses.replace(cfg, slot_fee_pct=float(f),
                                blocked_slots=blocks, durations=[primary_dur]),
            primary_dur)["net_profit"] for f in fees_range]
        fig2.add_trace(go.Scatter(x=fees_range, y=profits, mode="lines",
                                  name=f"{blocks} blocked",
                                  line=dict(color=color, width=2.5)))
    fig2.add_hline(y=0, line=dict(color=SLATE_500, width=1.5, dash="dash"))
    fig2.add_vline(x=cfg.slot_fee_pct, line=dict(color=WARNING, width=2, dash="dot"),
                   annotation_text=f"Current: {cfg.slot_fee_pct:.1f}%",
                   annotation_font=dict(size=11, color=WARNING))
    fig2.update_xaxes(title_text="Slot Fee % of Pot")
    fig2.update_yaxes(title_text="Net Profit per Cycle (PKR)")
    st.plotly_chart(_theme(fig2, f"Profit vs Fee — {primary_dur}M ROSCA", height=400),
                    use_container_width=True, config=_CFG_STATIC)


def tab_raw(df: pd.DataFrame):
    _sh("Raw Forecast Data")
    st.caption("All revenue/cost columns are suffixed _monthly — "
               "no mixing with cycle-lifetime values.")
    st.dataframe(df, use_container_width=True, height=480)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download as CSV", csv,
                       "bachat_forecast.csv", "text/csv")


# =============================================================================
# MAIN
# =============================================================================

def main():
    st.set_page_config(
        page_title="Bachat ROSCA — Pricing & Risk",
        page_icon="◉",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()

    cfg = render_sidebar()
    df  = build_forecast(cfg)

    annual_rate = cfg.kibor_rate + cfg.spread
    st.markdown(f"""
    <div class="hero">
        <div class="hero-left">
            <h1>Bachat ROSCA — Pricing &amp; Risk</h1>
            <p>Slot-conditional defaults · three-principal NII ·
               two-pass lifecycle · {cfg.simulation_months}-month horizon</p>
        </div>
        <div class="hero-pill">
            KIBOR {cfg.kibor_rate:.2f}% + Spread {cfg.spread:+.2f}%
            = <b>{annual_rate:.2f}%</b> &nbsp;|&nbsp;
            {", ".join(f"{d}M" for d in cfg.durations)} &nbsp;|&nbsp;
            PKR {cfg.slab_amount:,}/mo
        </div>
    </div>""", unsafe_allow_html=True)

    tabs = st.tabs(["📊 Overview", "⚠️ Risk & Slots",
                    "💰 Revenue & NII", "👥 Users",
                    "📈 P&L", "🔬 Sensitivity", "🗂 Raw Data"])

    with tabs[0]: tab_overview(cfg, df)
    with tabs[1]: tab_risk(cfg, df)
    with tabs[2]: tab_revenue(cfg, df)
    with tabs[3]: tab_users(cfg, df)
    with tabs[4]: tab_pnl(cfg, df)
    with tabs[5]: tab_sensitivity(cfg)
    with tabs[6]: tab_raw(df)


if __name__ == "__main__":
    main()
