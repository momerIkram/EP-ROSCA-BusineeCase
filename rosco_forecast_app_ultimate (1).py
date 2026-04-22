"""
BACHAT KOMMITTEE — Pricing & Risk Model
==========================================
Restores all v1 features dropped in v2, with full validation:

  1. Pre / post-payout default split  (cfg.default_pre_pct / default_post_pct)
  2. Fee collection mode              (Upfront vs Monthly, affects fee-NII timing)
  3. Per-slot granular fee config     (slot_fees_config overrides default slot_fee_pct)
  4. Multi-slab portfolio             (cfg.slab_amounts: List[int])
  5. TAM distribution hierarchy       (duration_share × slab_share → user scaling)
  6. Named scenario analysis          (Base / Optimistic / Pessimistic)
  7. Market analysis                  (TAM / SAM / SOM, market growth rate)
  8. YoY growth rate input            (yoy_growth_rate for P&L projections)
  9. Full validation throughout       (validate_config → errors/warnings in sidebar)

Engine: slot-conditional defaults, three-principal NII, two-pass lifecycle, O(M) cumsum.
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
    """Single source of truth for all model inputs (v3.0)."""
    # ── User growth ────────────────────────────────────────────────────────────
    starting_users: int        = 100_000
    monthly_growth_rate: float = 8.0
    churn_rate: float          = 5.0
    returning_user_rate: float = 60.0
    rest_period_months: int    = 1
    simulation_months: int     = 48

    # ── Portfolio ──────────────────────────────────────────────────────────────
    durations: List[int]       = field(default_factory=lambda: [4, 6])
    slab_amounts: List[int]    = field(default_factory=lambda: [5_000, 10_000])
    slot_fee_pct: float        = 5.0          # default fee; overridden by slot_fees_config
    # Per-duration blocked slots: {duration: n_blocked}.  Falls back to min(1, N-1).
    blocked_slots_config: Dict = field(default_factory=dict)
    fee_collection_mode: str   = "Upfront"    # "Upfront" | "Monthly"

    # Per-slot fee overrides: key = "{duration}_{slot}", value = fee_pct (float)
    slot_fees_config: Dict     = field(default_factory=lambda: {
        "4_3": 8.0, "4_4": 0.0,
        "6_4": 8.0, "6_5": 7.0, "6_6": 0.0,
    })

    # ── Interest / NII ─────────────────────────────────────────────────────────
    kibor_rate: float          = 10.5
    spread: float              = 0.0
    collection_day: int        = 1
    disbursement_day: int      = 15

    # ── Default risk ───────────────────────────────────────────────────────────
    default_rate: float        = 8.0
    recovery_rate: float       = 70.0
    penalty_pct: float         = 10.0
    default_pre_pct: float     = 30.0   # % of defaults occurring BEFORE payout
    default_post_pct: float    = 70.0   # % of defaults occurring AFTER payout

    # ── Profit split ───────────────────────────────────────────────────────────
    profit_split_party_a: float = 90.0

    # ── Market / TAM ───────────────────────────────────────────────────────────
    use_tam: bool              = False
    duration_share: Dict       = field(default_factory=dict)  # {duration: share_pct}
    slab_share: Dict           = field(default_factory=dict)  # {slab: share_pct}
    market_size: int           = 18_000_000
    sam_size: int              = 1_800_000
    som_size: int              = 1_000_000
    market_growth_rate: float  = 15.0

    # ── YoY projection ─────────────────────────────────────────────────────────
    yoy_growth_rate: float     = 10.0


# =============================================================================
# HELPERS
# =============================================================================

def _blocked(cfg: "BachatConfig", duration: int) -> int:
    """Blocked slots for a specific duration.
    Defaults to min(1, duration-1) if not explicitly configured."""
    return cfg.blocked_slots_config.get(duration, min(1, duration - 1))


# =============================================================================
# VALIDATION
# =============================================================================

def validate_config(cfg: BachatConfig) -> Tuple[List[str], List[str]]:
    """Return (errors, warnings). Errors block computation; warnings are advisory."""
    errors: List[str]   = []
    warnings: List[str] = []

    if not cfg.durations:
        errors.append("Select at least one KOMMITTEE duration.")
    if not cfg.slab_amounts:
        errors.append("Select at least one slab amount.")
    for d in cfg.durations:
        b = _blocked(cfg, d)
        if b >= d:
            errors.append(
                f"Blocked slots for {d}M ({b}) must be < {d}. No user slots would remain."
            )
    if cfg.collection_day >= cfg.disbursement_day:
        errors.append(
            f"Collection day ({cfg.collection_day}) must be < disbursement day "
            f"({cfg.disbursement_day}) for positive base NII."
        )
    pre_post_sum = cfg.default_pre_pct + cfg.default_post_pct
    if abs(pre_post_sum - 100.0) > 0.5:
        errors.append(
            f"Pre-payout ({cfg.default_pre_pct:.1f}%) + post-payout "
            f"({cfg.default_post_pct:.1f}%) must sum to 100% (currently {pre_post_sum:.1f}%)."
        )
    if cfg.use_tam:
        d_sum = sum(cfg.duration_share.get(d, 0.0) for d in cfg.durations)
        if abs(d_sum - 100.0) > 0.5:
            errors.append(
                f"Duration shares sum to {d_sum:.1f}% — must equal 100%."
            )
        s_sum = sum(cfg.slab_share.get(s, 0.0) for s in cfg.slab_amounts)
        if abs(s_sum - 100.0) > 0.5:
            errors.append(
                f"Slab shares sum to {s_sum:.1f}% — must equal 100%."
            )
        if cfg.som_size > cfg.sam_size:
            warnings.append("SOM > SAM — SOM cannot exceed addressable market.")
        if cfg.sam_size > cfg.market_size:
            warnings.append("SAM > TAM — SAM cannot exceed total market.")

    net_loss_rate = cfg.default_rate * (1 - cfg.recovery_rate / 100)
    if net_loss_rate > 20:
        warnings.append(
            f"Net expected loss rate is {net_loss_rate:.1f}% — extremely high. "
            "Verify default and recovery assumptions."
        )
    if cfg.kibor_rate + cfg.spread <= 0:
        warnings.append("Effective NII rate is ≤ 0% — no interest income will accrue.")
    if cfg.monthly_growth_rate > 20:
        warnings.append(
            f"Monthly growth rate {cfg.monthly_growth_rate:.1f}% implies "
            f"{cfg.monthly_growth_rate*12:.0f}%+ annual growth — verify this is realistic."
        )

    return errors, warnings


# =============================================================================
# ENGINE  —  pure functions, no Streamlit
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
    """Returns (gross_loss, net_loss). User slots only (blocked+1..N)."""
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
    """NII on full monthly pool between collection and disbursement.
    30/360 convention. Principal = N × M (full pot, all members)."""
    if disbursement_day <= collection_day:
        return 0.0
    return duration * nii(duration * slab, annual_rate_pct,
                          disbursement_day - collection_day)


def float_nii_per_cycle(duration: int, blocked: int, slab: float,
                        annual_rate_pct: float) -> float:
    """NII on platform working-capital float from blocked slots.
    Different principal from base_nii — no double-counting."""
    return platform_float_capital(duration, blocked, slab) * (annual_rate_pct / 100.0) / 12.0


def cycle_fees_and_fee_nii(
    cfg: BachatConfig, duration: int, slab: float, annual_rate_pct: float
) -> Tuple[float, float]:
    """Compute total fees and fee-NII for one cycle, respecting:
      - per-slot fee overrides in cfg.slot_fees_config
      - fee_collection_mode ("Upfront" vs "Monthly")

    Upfront:  fee = pot × fee_pct%;  NII hold = half-cycle (N×30/2 days)
    Monthly:  fee = slab × N × fee_pct%;  NII hold = quarter-cycle (N×30/4 days)
    Note: fee amount is identical in both modes; timing differs → different NII.
    """
    N   = duration
    pot = N * slab
    blocked    = _blocked(cfg, N)
    total_fees = 0.0
    for s in range(blocked + 1, N + 1):
        key     = f"{N}_{s}"
        fee_pct = cfg.slot_fees_config.get(key, cfg.slot_fee_pct)
        # Both modes charge fee_pct on the full pot (numerically equivalent)
        total_fees += pot * (fee_pct / 100.0)

    if cfg.fee_collection_mode == "Upfront":
        hold_days_val = int(N * 30 / 2)   # collected at start, held ~half cycle
    else:
        hold_days_val = int(N * 30 / 4)   # collected monthly, avg ~quarter cycle

    f_nii = nii(total_fees, annual_rate_pct, hold_days_val)
    return total_fees, f_nii


def cycle_default_loss_split(
    cfg: BachatConfig, duration: int, slab: float
) -> Dict:
    """Default loss split into pre-payout and post-payout portions.

    Pre-payout defaults: member stops paying before receiving the pot.
      → Operational loss, immediately affects cash flow.
    Post-payout defaults: member receives pot then stops paying.
      → Credit loss, affects receivables provisioning.
    """
    blocked    = _blocked(cfg, duration)
    gross, net = slot_conditional_default_loss(
        duration, blocked, slab, cfg.default_rate, cfg.recovery_rate)
    penalty  = gross * (cfg.penalty_pct / 100.0)
    pre_net  = net * (cfg.default_pre_pct  / 100.0)
    post_net = net * (cfg.default_post_pct / 100.0)
    return {
        "gross": gross, "net": net,
        "pre_net": pre_net, "post_net": post_net,
        "penalty": penalty,
    }


def user_lifecycle(cfg: BachatConfig, duration: int,
                   scale_factor: float = 1.0) -> pd.DataFrame:
    """Two-pass cohort-tracked lifecycle.
    Pass 1: project new_users growth (geometric).
    Pass 2: forward loop — returning_users[m] is read from return_schedule[m]
            before processing finish_origin < m, so second-generation churn
            and multi-cycle returns are correct.
    Pass 3: O(M) active-users via np.cumsum sliding window.

    scale_factor: applied to starting_users for TAM distribution.
    """
    M        = cfg.simulation_months
    g        = cfg.monthly_growth_rate / 100.0
    churn    = cfg.churn_rate          / 100.0
    ret_rate = cfg.returning_user_rate / 100.0
    rest     = cfg.rest_period_months
    start    = float(cfg.starting_users) * scale_factor

    new_users       = np.zeros(M + 1)
    returning_users = np.zeros(M + 1)
    resting_users   = np.zeros(M + 1)
    completed_users = np.zeros(M + 1)
    churned_users   = np.zeros(M + 1)
    active_users    = np.zeros(M + 1)
    return_schedule = np.zeros(M + 2)

    new_users[1] = start
    cumulative   = start
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

    combined = new_users + returning_users
    cs = np.cumsum(combined)
    for m in range(1, M + 1):
        start_idx = max(1, m - duration + 1)
        active_users[m] = cs[m] - cs[start_idx - 1]

    return pd.DataFrame({
        "month":                 np.arange(1, M + 1),
        "new_users":             new_users[1:].astype(int),
        "returning_users":       returning_users[1:].astype(int),
        "active_users_in_cycle": active_users[1:].astype(int),
        "resting_users":         resting_users[1:].astype(int),
        "completed_users":       completed_users[1:].astype(int),
        "churned_users":         churned_users[1:].astype(int),
    })


def _tam_scale(cfg: BachatConfig, duration: int, slab: int) -> float:
    """Scale factor for this duration×slab combination under TAM distribution.
    Returns 1.0 if use_tam is False."""
    if not cfg.use_tam:
        return 1.0
    n = len(cfg.durations) * len(cfg.slab_amounts)
    d_pct = cfg.duration_share.get(duration, 100.0 / max(1, len(cfg.durations)))
    s_pct = cfg.slab_share.get(slab,     100.0 / max(1, len(cfg.slab_amounts)))
    return (d_pct / 100.0) * (s_pct / 100.0)


def build_forecast(cfg: BachatConfig) -> pd.DataFrame:
    """Monthly forecast across all durations × slab_amounts.
    O(M) via cumsum per combo. All revenue columns are _monthly."""
    rows        = []
    annual_rate = cfg.kibor_rate + cfg.spread
    M           = cfg.simulation_months

    for duration in cfg.durations:
        for slab in cfg.slab_amounts:
            N            = duration
            pot          = N * slab
            scale        = _tam_scale(cfg, duration, slab)
            blocked      = _blocked(cfg, N)
            user_slots   = N - blocked

            cycle_base_nii  = base_nii_per_cycle(
                N, slab, annual_rate, cfg.collection_day, cfg.disbursement_day)
            cycle_float_nii = float_nii_per_cycle(N, blocked, slab, annual_rate)
            cycle_fees, cycle_fee_nii = cycle_fees_and_fee_nii(
                cfg, N, slab, annual_rate)
            def_split       = cycle_default_loss_split(cfg, N, slab)
            net_def         = def_split["net"]
            pre_net         = def_split["pre_net"]
            post_net        = def_split["post_net"]
            cycle_penalty   = def_split["penalty"]
            cycle_float_pkr = platform_float_capital(N, blocked, slab)
            avg_float       = cycle_float_pkr / N if N > 0 else 0.0

            lifecycle = user_lifecycle(cfg, N, scale_factor=scale)
            combined  = (lifecycle["new_users"].values +
                         lifecycle["returning_users"].values).astype(float) / N
            cs_groups = np.concatenate([[0.0], np.cumsum(combined)])

            for m in range(1, M + 1):
                row_lc = lifecycle.iloc[m - 1]
                start  = max(0, m - N)
                gr     = cs_groups[m] - cs_groups[start]
                k      = gr / N

                m_base    = cycle_base_nii   * k
                m_float   = cycle_float_nii  * k
                m_fee_nii = cycle_fee_nii    * k
                m_fees    = cycle_fees       * k
                m_pen     = cycle_penalty    * k
                m_loss    = net_def          * k
                m_pre     = pre_net          * k
                m_post    = post_net         * k
                m_rev     = m_base + m_float + m_fee_nii + m_fees + m_pen
                m_profit  = m_rev - m_loss
                m_a       = m_profit * (cfg.profit_split_party_a / 100.0)

                rows.append({
                    "month": m, "year": ((m - 1) // 12) + 1,
                    "duration": N, "slab_amount": slab,
                    "new_users":       int(row_lc["new_users"]),
                    "returning_users": int(row_lc["returning_users"]),
                    "active_users":    int(row_lc["active_users_in_cycle"]),
                    "churned_users":   int(row_lc["churned_users"]),
                    "groups_started_monthly": (row_lc["new_users"] +
                                               row_lc["returning_users"]) / N,
                    "groups_running_monthly": gr,
                    "pot_disbursed_monthly":          pot * gr,
                    "user_contributions_monthly":     user_slots * slab * gr,
                    "platform_capital_monthly":       blocked * slab * gr,
                    "float_outstanding_monthly":      avg_float * gr,
                    "base_nii_monthly":               m_base,
                    "float_nii_monthly":              m_float,
                    "fee_nii_monthly":                m_fee_nii,
                    "fees_monthly":                   m_fees,
                    "penalty_income_monthly":         m_pen,
                    "pre_payout_loss_monthly":        m_pre,
                    "post_payout_loss_monthly":       m_post,
                    "default_loss_monthly":           m_loss,
                    "total_revenue_monthly":          m_rev,
                    "net_profit_monthly":             m_profit,
                    "party_a_monthly":                m_a,
                    "party_b_monthly":                m_profit - m_a,
                })

    return pd.DataFrame(rows)


def cycle_economics(cfg: BachatConfig, duration: int, slab: int = 0) -> Dict:
    """Per-cycle economics summary for a single duration × slab."""
    if slab == 0:
        slab = cfg.slab_amounts[0] if cfg.slab_amounts else 10_000
    annual_rate = cfg.kibor_rate + cfg.spread
    N           = duration
    pot         = N * slab

    blocked     = _blocked(cfg, N)
    b_nii       = base_nii_per_cycle(N, slab, annual_rate,
                                     cfg.collection_day, cfg.disbursement_day)
    fl_nii      = float_nii_per_cycle(N, blocked, slab, annual_rate)
    fees, f_nii = cycle_fees_and_fee_nii(cfg, N, slab, annual_rate)
    def_split   = cycle_default_loss_split(cfg, N, slab)
    net_def     = def_split["net"]
    penalty     = def_split["penalty"]
    total_rev   = b_nii + fl_nii + fees + f_nii + penalty
    fpm         = platform_float_capital(N, blocked, slab)

    return {
        "duration": N, "slab": slab, "pot": pot,
        "user_slots": N - blocked,
        "base_nii": b_nii, "float_nii": fl_nii,
        "fees": fees, "fee_nii": f_nii,
        "gross_default": def_split["gross"],
        "net_default": net_def,
        "pre_payout_loss": def_split["pre_net"],
        "post_payout_loss": def_split["post_net"],
        "penalty_income": penalty,
        "total_revenue": total_rev,
        "net_profit": total_rev - net_def,
        "float_pkr_months": fpm,
        "avg_float_outstanding": fpm / N if N > 0 else 0.0,
        "blocked_slots": blocked,
        "max_single_default_loss": max(
            (max_debtor_position(N, s, slab)
             for s in range(blocked + 1, N + 1)),
            default=0.0),
    }


def build_slot_table(cfg: BachatConfig, duration: int, slab: int = 0) -> pd.DataFrame:
    if slab == 0:
        slab = cfg.slab_amounts[0] if cfg.slab_amounts else 10_000
    N       = duration
    blocked = _blocked(cfg, N)
    rows    = []
    for slot in range(1, N + 1):
        is_plat  = slot <= blocked
        max_d    = 0.0 if is_plat else max_debtor_position(N, slot, slab)
        exp_loss = (0.0 if is_plat else
                    max_d * (cfg.default_rate / 100.0) * (1 - cfg.recovery_rate / 100.0))
        key      = f"{N}_{slot}"
        fee_pct  = cfg.slot_fees_config.get(key, cfg.slot_fee_pct) if not is_plat else 0.0
        rows.append({
            "Slot":                        slot,
            "Holder":                      "PLATFORM" if is_plat else "USER",
            "Receives Pot (PKR)":          N * slab,
            "Paid Before Receiving (PKR)": (slot - 1) * slab,
            "Max Debtor Position (PKR)":   max_d,
            "Expected Loss (PKR)":         exp_loss,
            "Fee %":                       fee_pct,
            "Fee (PKR)":                   N * slab * (fee_pct / 100.0),
            "Status":                      ("Platform-held (safe)" if is_plat else
                                            ("User: SAFE (last slot)" if slot == N
                                             else "User: AT RISK")),
        })
    return pd.DataFrame(rows)


def build_scenarios(cfg: BachatConfig) -> Dict[str, pd.DataFrame]:
    """Build Base / Optimistic / Pessimistic scenario forecasts."""
    base = build_forecast(cfg)
    opt  = build_forecast(dataclasses.replace(
        cfg,
        default_rate  = cfg.default_rate  * 0.50,
        monthly_growth_rate = cfg.monthly_growth_rate * 1.25,
        recovery_rate = min(100.0, cfg.recovery_rate * 1.20),
    ))
    pess = build_forecast(dataclasses.replace(
        cfg,
        default_rate  = cfg.default_rate  * 2.00,
        monthly_growth_rate = cfg.monthly_growth_rate * 0.60,
        recovery_rate = cfg.recovery_rate * 0.70,
    ))
    return {"Base": base, "Optimistic": opt, "Pessimistic": pess}


def build_yearly_projection(df: pd.DataFrame, cfg: BachatConfig,
                             extra_years: int = 3) -> pd.DataFrame:
    """Actual simulated years + YoY-extrapolated extra years."""
    yearly = (df.groupby("year")
                .agg(revenue=("total_revenue_monthly", "sum"),
                     profit =("net_profit_monthly",    "sum"),
                     loss   =("default_loss_monthly",  "sum"),
                     fees   =("fees_monthly",           "sum"),
                     users  =("active_users",           "max"))
                .reset_index())
    yearly["source"] = "Simulated"

    last_year = int(yearly["year"].max())
    last_row  = yearly.iloc[-1]
    g = cfg.yoy_growth_rate / 100.0
    ext_rows = []
    for i in range(1, extra_years + 1):
        ext_rows.append({
            "year":    last_year + i,
            "revenue": last_row["revenue"] * (1 + g) ** i,
            "profit":  last_row["profit"]  * (1 + g) ** i,
            "loss":    last_row["loss"]    * (1 + g) ** i,
            "fees":    last_row["fees"]    * (1 + g) ** i,
            "users":   int(last_row["users"] * (1 + g) ** i),
            "source":  "Projected",
        })
    return pd.concat([yearly, pd.DataFrame(ext_rows)], ignore_index=True)


# =============================================================================
# UI HELPERS
# =============================================================================

def fmt_pkr(x: float) -> str:
    if pd.isna(x) or x == 0:
        return "—"
    s = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e9:  return f"{s}PKR {x/1e9:.2f}B"
    if x >= 1e6:  return f"{s}PKR {x/1e6:.2f}M"
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

    /* ── Validation banner ───────────────── */
    .val-error {{
        background: #FEF2F2; border: 1px solid {DANGER};
        border-left: 4px solid {DANGER};
        border-radius: 8px; padding: 0.7rem 1rem;
        font-size: 0.82rem; color: {DANGER}; margin-bottom: 0.5rem;
    }}
    .val-warn {{
        background: #FFFBEB; border: 1px solid {WARNING};
        border-left: 4px solid {WARNING};
        border-radius: 8px; padding: 0.7rem 1rem;
        font-size: 0.82rem; color: #92400E; margin-bottom: 0.5rem;
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

    /* ── Metric cards ────────────────────── */
    [data-testid="stMetric"] {{
        background: {WHITE};
        border: 1px solid {SLATE_200};
        border-radius: 12px;
        padding: 0.9rem 1rem;
        box-shadow: 0 1px 4px rgba(15,23,42,0.05);
    }}
    [data-testid="stMetric"] label {{
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: {SLATE_500} !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        color: {INK} !important;
    }}

    /* ── Streamlit chrome ─────────────────── */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header [data-testid="stDecoration"] {{ display: none; }}

    /* ================================================================
       RESPONSIVE — Tablet & Mobile (≤ 768px)
       ================================================================ */
    @media (max-width: 768px) {{
        /* Force sidebar into overlay mode on mobile */
        section[data-testid="stSidebar"] {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            bottom: 0 !important;
            z-index: 999 !important;
            width: 85vw !important;
            min-width: 0 !important;
            max-width: 85vw !important;
            transform: translateX(-100%) !important;
            transition: transform 0.3s ease !important;
            box-shadow: none !important;
        }}
        section[data-testid="stSidebar"][aria-expanded="true"] {{
            transform: translateX(0) !important;
            box-shadow: 4px 0 24px rgba(0,0,0,0.3) !important;
        }}
        /* Ensure main content always gets full width */
        .main,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main {{
            width: 100% !important;
            min-width: 0 !important;
        }}

        .main .block-container {{
            padding-top: 1rem;
            padding-left: 0.6rem;
            padding-right: 0.6rem;
            max-width: 100% !important;
            min-width: 0 !important;
        }}

        /* Hero — stack vertically, allow wrapping */
        .hero {{
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
            padding: 0.9rem 1rem;
            border-radius: 10px;
            border-left-width: 3px;
        }}
        .hero-left h1 {{
            font-size: 1.1rem;
            line-height: 1.3;
            word-break: break-word;
        }}
        .hero-left p {{
            font-size: 0.72rem;
            line-height: 1.4;
            word-break: break-word;
        }}
        .hero-pill {{
            font-size: 0.65rem;
            padding: 0.3rem 0.6rem;
            white-space: normal;
            word-break: break-word;
            line-height: 1.4;
        }}

        /* All column rows — wrap into 2-col grid */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 0.45rem !important;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
            flex: 1 1 calc(50% - 0.45rem) !important;
            min-width: calc(50% - 0.45rem) !important;
            max-width: 100% !important;
            width: auto !important;
        }}

        /* Metric cards — compact */
        [data-testid="stMetric"] {{
            padding: 0.5rem 0.6rem;
            border-radius: 8px;
        }}
        [data-testid="stMetric"] [data-testid="stMetricValue"] {{
            font-size: 0.95rem !important;
        }}
        [data-testid="stMetric"] label {{
            font-size: 0.62rem !important;
        }}

        /* Tabs — horizontal scroll */
        .stTabs [data-baseweb="tab-list"] {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            flex-wrap: nowrap !important;
        }}
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {{ display: none; }}
        .stTabs [data-baseweb="tab"] {{
            padding: 0.45rem 0.65rem;
            font-size: 0.7rem;
            white-space: nowrap;
            flex-shrink: 0;
        }}

        /* Charts */
        [data-testid="stPlotlyChart"] > div {{
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(15,23,42,0.04);
        }}

        /* Section headers */
        .sh {{ font-size: 0.85rem; margin: 1rem 0 0.5rem; }}

        /* Insights panel */
        .insights-panel {{ padding: 0.7rem 0.8rem; border-radius: 10px; }}
        .insights-panel h4 {{ font-size: 0.7rem; }}
        .insight-item {{ font-size: 0.74rem; padding: 0.4rem 0; }}

        /* Sidebar sections */
        .sb-section {{ margin: 0.4rem 0.4rem; padding: 0.6rem 0.65rem 0.45rem; }}
        .sb-summary {{ margin: 0.4rem 0.4rem 0; padding: 0.55rem 0.65rem; }}

        /* Audit / verdict */
        .audit-box {{ font-size: 0.78rem; padding: 0.7rem 0.9rem; }}
        .verdict {{ font-size: 0.72rem; padding: 0.3rem 0.7rem; }}
    }}

    /* ================================================================
       RESPONSIVE — Small phone (≤ 480px)
       ================================================================ */
    @media (max-width: 480px) {{
        .main .block-container {{
            padding-left: 0.35rem;
            padding-right: 0.35rem;
        }}

        /* Single-column stack for metrics */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }}

        .hero-left h1 {{ font-size: 0.95rem; }}
        .hero-pill {{ font-size: 0.6rem; }}

        .stTabs [data-baseweb="tab"] {{
            padding: 0.35rem 0.5rem;
            font-size: 0.65rem;
        }}

        .sb-brand {{ padding: 0.8rem 0.7rem 0.6rem; }}
        .sb-brand-name {{ font-size: 0.88rem; }}
    }}
    </style>
    """, unsafe_allow_html=True)


def _sb_section(icon: str, title: str, color: str = BACHAT_GREEN):
    st.sidebar.markdown(f"""
    <div class="sb-section-title">
        <span class="sb-section-icon"
              style="background:{color}22; color:{color};">{icon}</span>
        {title}
    </div>""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar() -> BachatConfig:
    cfg = BachatConfig()

    # ── Brand header ─────────────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div class="sb-brand">
        <div class="sb-brand-name">◉ Bachat KOMMITTEE</div>
        <div class="sb-brand-sub">Pricing &amp; Risk Model</div>
        <span class="sb-brand-pill">v3.0</span>
    </div>""", unsafe_allow_html=True)

    # ── Portfolio (Durations + Slabs) ─────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("📦", "PORTFOLIO", BACHAT_GREEN)

    chosen_dur = st.sidebar.multiselect(
        "KOMMITTEE Durations (months)",
        [3, 4, 5, 6, 7, 8, 9, 10, 11, 12], default=[4, 6],
        help="Select one or more cycle lengths to model simultaneously")
    if not chosen_dur:
        st.sidebar.error("Select at least one duration.")
        chosen_dur = [4, 6]
    cfg.durations = sorted(chosen_dur)

    SLAB_OPTIONS = [5_000, 10_000, 15_000, 20_000, 25_000, 30_000, 50_000, 100_000]
    chosen_slabs = st.sidebar.multiselect(
        "Monthly Contribution Slabs (PKR)",
        SLAB_OPTIONS,
        default=[5_000, 10_000],
        format_func=lambda x: f"PKR {x:,}",
        help="Each slab is modelled as a separate portfolio segment")
    if not chosen_slabs:
        st.sidebar.error("Select at least one slab amount.")
        chosen_slabs = [5_000]
    cfg.slab_amounts = sorted(chosen_slabs)

    st.sidebar.caption("Platform-Blocked Slots per Duration")
    blocked_cfg: Dict = {}
    _blocked_defaults = {4: 2, 6: 3}
    for dur in cfg.durations:
        max_b = dur - 1
        default_b = _blocked_defaults.get(dur, max(1, dur // 2))
        blocked_cfg[dur] = st.sidebar.slider(
            f"Blocked slots — {dur}M KOMMITTEE",
            0, max(1, max_b), min(default_b, max_b),
            key=f"blocked_{dur}",
            help=f"For {dur}-month KOMMITTEE: slots the platform occupies to capture float. "
                 f"Max = {max_b} (must leave at least 1 user slot).")
    cfg.blocked_slots_config = blocked_cfg

    cfg.fee_collection_mode = st.sidebar.radio(
        "Fee Collection Mode",
        ["Upfront", "Monthly"],
        horizontal=True,
        help="Upfront: full fee at start (higher fee-NII). "
             "Monthly: fee spread over cycle (lower fee-NII).")


    # Per-slot fee override expander
    _default_slot_fees = {
        "4_3": 8.0, "4_4": 0.0,
        "6_4": 8.0, "6_5": 7.0, "6_6": 0.0,
    }
    with st.sidebar.expander("⚙ Per-Slot Fee Overrides (optional)"):
        st.caption("Override the default fee for any specific Duration × Slot. "
                   "Leave blank to use the default above.")
        slot_fees: Dict = {}
        for dur in cfg.durations:
            b_dur = cfg.blocked_slots_config.get(dur, min(1, dur - 1))
            st.markdown(f"**{dur}-Month KOMMITTEE** ({b_dur} blocked, {dur - b_dur} user slots)")
            cols = st.columns(3)
            for idx, slot in enumerate(range(b_dur + 1, dur + 1)):
                with cols[idx % 3]:
                    key = f"{dur}_{slot}"
                    default_val = _default_slot_fees.get(key, cfg.slot_fee_pct)
                    val = st.number_input(
                        f"Slot {slot} fee %",
                        min_value=0.0, max_value=50.0,
                        value=default_val, step=0.5,
                        key=f"sfee_{dur}_{slot}")
                    slot_fees[key] = val
        cfg.slot_fees_config = slot_fees
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── User Growth ───────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("👥", "USER GROWTH", INFO)

    cfg.starting_users = st.sidebar.number_input(
        "Starting Users (Month 1)",
        min_value=10, max_value=10_000_000, value=100_000, step=1_000,
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
        help="Months a user sits out between KOMMITTEE cycles")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── Float / NII ───────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("🏦", "FLOAT / NII", PURPLE)

    cfg.kibor_rate = st.sidebar.slider(
        "KIBOR Rate %", 5.0, 30.0, 10.5, 0.25,
        help="Pakistan benchmark interest rate for NII calculations")
    cfg.spread = st.sidebar.slider(
        "Spread vs KIBOR %", -10.0, 5.0, 0.0, 0.25,
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
        "Recovery Rate %", 0.0, 100.0, 70.0, 5.0,
        help="% of defaulted exposure recovered through collections or collateral")
    cfg.penalty_pct = st.sidebar.slider(
        "Penalty % on Defaults", 0.0, 20.0, 10.0, 0.5,
        help="Additional fee charged on the defaulted principal — becomes platform income")

    st.sidebar.caption("Pre/Post Payout Default Split — must sum to 100%")
    col_pre, col_post = st.sidebar.columns(2)
    cfg.default_pre_pct  = col_pre.number_input(
        "Pre-Payout %", 0.0, 100.0, 30.0, 5.0,
        help="Defaults BEFORE user receives pot (operational loss)")
    cfg.default_post_pct = col_post.number_input(
        "Post-Payout %", 0.0, 100.0, 70.0, 5.0,
        help="Defaults AFTER user receives pot (credit loss)")
    pre_post_sum = cfg.default_pre_pct + cfg.default_post_pct
    if abs(pre_post_sum - 100.0) > 0.5:
        st.sidebar.error(f"Pre + Post = {pre_post_sum:.1f}% ≠ 100%")

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
        "Party A Share %", 0.0, 100.0, 90.0, 1.0,
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

    # ── Market / TAM ──────────────────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("🌍", "MARKET / TAM", WARNING)

    cfg.use_tam = st.sidebar.toggle(
        "Enable TAM Distribution",
        value=False,
        help="Scale users per duration×slab by their market share percentages")

    if cfg.use_tam:
        st.sidebar.caption("Duration shares (must sum to 100%)")
        d_shares: Dict = {}
        even_d = 100.0 / len(cfg.durations)
        for dur in cfg.durations:
            d_shares[dur] = st.sidebar.slider(
                f"{dur}M share %", 0.0, 100.0, even_d, 1.0,
                key=f"dshare_{dur}")
        cfg.duration_share = d_shares
        d_sum = sum(d_shares.values())
        if abs(d_sum - 100.0) > 0.5:
            st.sidebar.error(f"Duration shares sum to {d_sum:.1f}% (need 100%)")

        st.sidebar.caption("Slab shares (must sum to 100%)")
        s_shares: Dict = {}
        even_s = 100.0 / len(cfg.slab_amounts)
        for slab in cfg.slab_amounts:
            s_shares[slab] = st.sidebar.slider(
                f"PKR {slab:,} share %", 0.0, 100.0, even_s, 1.0,
                key=f"sshare_{slab}")
        cfg.slab_share = s_shares
        s_sum = sum(s_shares.values())
        if abs(s_sum - 100.0) > 0.5:
            st.sidebar.error(f"Slab shares sum to {s_sum:.1f}% (need 100%)")

    _tam_options = [i * 1_000_000 for i in range(1, 101)]
    cfg.market_size = st.sidebar.select_slider(
        "TAM (total KOMMITTEE users)", options=_tam_options, value=18_000_000,
        format_func=lambda x: f"{x:,}",
        help="Total addressable market — all KOMMITTEE participants in Pakistan")
    _sam_options = [i * 100_000 for i in range(1, 501)]
    cfg.sam_size = st.sidebar.select_slider(
        "SAM (serviceable)", options=_sam_options, value=1_800_000,
        format_func=lambda x: f"{x:,}",
        help="Serviceable addressable market — users reachable by your platform")
    _som_options = [i * 50_000 for i in range(1, 201)]
    cfg.som_size = st.sidebar.select_slider(
        "SOM (obtainable)", options=_som_options, value=1_000_000,
        format_func=lambda x: f"{x:,}",
        help="Serviceable obtainable market — realistic near-term capture")
    cfg.market_growth_rate = st.sidebar.slider(
        "Market Growth Rate % p.a.", 0.0, 50.0, 15.0, 1.0,
        help="Annual growth of the total KOMMITTEE market in Pakistan")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── Simulation Horizon & YoY ──────────────────────────────────────────────
    st.sidebar.markdown('<div class="sb-section">', unsafe_allow_html=True)
    _sb_section("📅", "HORIZON & PROJECTIONS", SLATE_500)

    cfg.simulation_months = st.sidebar.selectbox(
        "Forecast Length",
        [12, 24, 36, 48, 60],
        index=3,
        format_func=lambda x: f"{x} months  ({x//12} year{'s' if x//12>1 else ''})",
        help="Total number of months to simulate")
    cfg.yoy_growth_rate = st.sidebar.slider(
        "YoY Projection Growth %", 0.0, 50.0, 10.0, 1.0,
        help="Annual growth rate used to project P&L beyond the simulation window")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # ── Live Config Summary ───────────────────────────────────────────────────
    min_pot = min(cfg.durations) * min(cfg.slab_amounts)
    slabs_str = ", ".join(f"PKR {s:,}" for s in cfg.slab_amounts)
    blocked_str = "  ".join(
        f"{d}M:{cfg.blocked_slots_config.get(d, min(1,d-1))}b"
        for d in cfg.durations)
    st.sidebar.markdown(f"""
    <div class="sb-summary">
        <div class="sb-summary-title">◉ Active Configuration</div>
        <div class="sb-summary-row">
            <span>Duration(s)</span>
            <b>{", ".join(f"{d}M" for d in cfg.durations)}</b>
        </div>
        <div class="sb-summary-row">
            <span>Blocked Slots</span>
            <b style="font-size:0.72rem">{blocked_str}</b>
        </div>
        <div class="sb-summary-row">
            <span>Slab(s)</span>
            <b>{slabs_str}</b>
        </div>
        <div class="sb-summary-row">
            <span>Min Pot</span>
            <b>PKR {min_pot:,}</b>
        </div>
        <div class="sb-summary-row">
            <span>Effective Rate</span>
            <b>{cfg.kibor_rate + cfg.spread:.2f}%</b>
        </div>
        <div class="sb-summary-row">
            <span>Fee Mode</span>
            <b>{cfg.fee_collection_mode}</b>
        </div>
        <div class="sb-summary-row">
            <span>Net Loss Rate</span>
            <b>{cfg.default_rate * (1 - cfg.recovery_rate/100):.1f}%</b>
        </div>
        <div class="sb-summary-row">
            <span>Pre / Post Default</span>
            <b>{cfg.default_pre_pct:.0f}% / {cfg.default_post_pct:.0f}%</b>
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
        f"per cycle via {eco['blocked_slots']} blocked slot(s), earning "
        f"<b>{fmt_pkr(eco['float_nii'])}</b> NII/cycle at {annual_rate:.1f}%."
    )

    # 4 — breakeven default rate
    slab0 = cfg.slab_amounts[0]
    for r in range(0, 51):
        c2 = dataclasses.replace(cfg, default_rate=float(r))
        if cycle_economics(c2, cfg.durations[0], slab0)["net_profit"] < 0:
            safety = r - cfg.default_rate
            insights.append(
                f"Breakeven default rate: <b>{r}%</b>. "
                f"Current {cfg.default_rate:.0f}% leaves a "
                f"<b>{safety:.0f} ppt safety margin</b>."
            )
            break

    # 5 — default split
    total_pre  = df["pre_payout_loss_monthly"].sum()
    total_post = df["post_payout_loss_monthly"].sum()
    total_loss = total_pre + total_post
    total_rev  = df["total_revenue_monthly"].sum()
    loss_pct   = total_loss / total_rev * 100 if total_rev else 0
    insights.append(
        f"Default losses consume <b>{loss_pct:.1f}%</b> of revenue "
        f"({fmt_pkr(total_loss)}): "
        f"<b>{fmt_pkr(total_pre)}</b> pre-payout (operational) + "
        f"<b>{fmt_pkr(total_post)}</b> post-payout (credit)."
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
# VIZ HELPERS
# =============================================================================

_CFG_STATIC = {"displayModeBar": False}


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


def _sh(text: str):
    st.markdown(f'<div class="sh">{text}</div>', unsafe_allow_html=True)


# =============================================================================
# CHART FUNCTIONS
# =============================================================================

def _fmt_short(x: float, is_currency: bool = True) -> str:
    """Compact human-readable format for sparkline annotations."""
    if x == 0:
        return "0"
    s = "-" if x < 0 else ""
    x = abs(x)
    if is_currency:
        if x >= 1e9:  return f"{s}PKR {x/1e9:.1f}B"
        if x >= 1e6:  return f"{s}PKR {x/1e6:.1f}M"
        if x >= 1e3:  return f"{s}PKR {x/1e3:.0f}k"
        return f"{s}PKR {x:,.0f}"
    if x >= 1e6:  return f"{s}{x/1e6:.2f}M"
    if x >= 1e3:  return f"{s}{x/1e3:.1f}k"
    return f"{s}{x:,.0f}"


def chart_kpi_sparklines(agg: pd.DataFrame) -> go.Figure:
    """4-panel sparkline cards — each shows a title, formatted value, delta %, and area chart."""
    metrics = [
        ("total_revenue_monthly", "Monthly Revenue", BACHAT_GREEN, True),
        ("net_profit_monthly",    "Net Profit",      INFO,         True),
        ("active_users",          "Active Users",    PURPLE,       False),
        ("default_loss_monthly",  "Default Loss",    DANGER,       True),
    ]

    fig = make_subplots(
        rows=1, cols=4,
        horizontal_spacing=0.06,
    )

    annotations = []
    for col_idx, (col, label, color, is_currency) in enumerate(metrics, 1):
        y = agg[col].values if col in agg.columns else np.zeros(len(agg))
        latest = y[-1] if len(y) else 0
        prev   = y[-2] if len(y) > 1 else latest
        delta  = ((latest - prev) / prev * 100) if prev != 0 else 0
        headline = _fmt_short(latest, is_currency)
        delta_sign = "+" if delta >= 0 else ""
        delta_color = (BACHAT_GREEN if col != "default_loss_monthly" else DANGER) if delta >= 0 else (DANGER if col != "default_loss_monthly" else BACHAT_GREEN)

        fig.add_trace(go.Scatter(
            x=agg["month"], y=y, mode="lines",
            line=dict(color=color, width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor=_hex_rgba(color, 0.10),
            showlegend=False,
            hovertemplate=f"<b>{label}</b><br>"
                          "Month %{x}<br>"
                          f"Value: %{{y:,.0f}}<extra></extra>",
        ), row=1, col=col_idx)

        x_ref = f"x{col_idx} domain" if col_idx > 1 else "x domain"
        y_ref = f"y{col_idx} domain" if col_idx > 1 else "y domain"
        annotations.append(dict(
            text=f"<b style='color:{SLATE_500};font-size:11px'>{label}</b>",
            x=0.02, y=1.18, xref=x_ref, yref=y_ref,
            showarrow=False, xanchor="left", font=dict(size=11),
        ))
        annotations.append(dict(
            text=f"<b style='color:{INK};font-size:17px'>{headline}</b>"
                 f"  <span style='color:{delta_color};font-size:11px'>{delta_sign}{delta:.1f}%</span>",
            x=0.02, y=1.02, xref=x_ref, yref=y_ref,
            showarrow=False, xanchor="left", font=dict(size=17),
        ))

    for ax_key in list(fig.layout.to_plotly_json()):
        if ax_key.startswith("xaxis") or ax_key.startswith("yaxis"):
            fig.layout[ax_key].update(showgrid=False, showticklabels=False,
                                      zeroline=False, showline=False)

    fig.update_layout(
        height=180, margin=dict(l=8, r=8, t=60, b=8),
        template=PLOTLY_TEMPLATE, paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        showlegend=False,
        annotations=annotations,
    )
    return fig


def chart_revenue_combo(agg: pd.DataFrame) -> go.Figure:
    """Combo bar+line: stacked revenue components + net profit line."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    components = [
        ("fees_monthly",           "Fees",         BACHAT_GREEN),
        ("base_nii_monthly",       "Base NII",     INFO),
        ("float_nii_monthly",      "Float NII",    PURPLE),
        ("fee_nii_monthly",        "Fee NII",      TEAL),
        ("penalty_income_monthly", "Penalty",      WARNING),
    ]
    for col, name, color in components:
        if col in agg.columns:
            fig.add_trace(go.Bar(x=agg["month"], y=agg[col], name=name,
                                 marker_color=color, opacity=0.85), secondary_y=False)
    fig.add_trace(
        go.Scatter(x=agg["month"], y=agg["net_profit_monthly"],
                   name="Net Profit", mode="lines",
                   line=dict(color=DANGER, width=2.5, dash="solid"),
                   showlegend=True),
        secondary_y=True,
    )
    fig.update_layout(barmode="stack", height=400,
                      margin=dict(l=16, r=16, t=48, b=36),
                      template=PLOTLY_TEMPLATE, paper_bgcolor=WHITE, plot_bgcolor=WHITE,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                  xanchor="right", x=1.0, font=dict(size=11)),
                      hovermode="x unified")
    fig.update_yaxes(title_text="Revenue (PKR)", secondary_y=False,
                     gridcolor=SLATE_100)
    fig.update_yaxes(title_text="Net Profit (PKR)", secondary_y=True,
                     gridcolor=SLATE_100)
    fig.update_layout(title=dict(
        text="Revenue Components vs Net Profit",
        font=dict(size=14, color=INK), x=0.0, xanchor="left"))
    return fig


def chart_deposits_cumulative(agg: pd.DataFrame) -> go.Figure:
    """Stacked area: cumulative user deposits + platform capital vs total pot turnover."""
    contrib = agg["user_contributions_monthly"].values if "user_contributions_monthly" in agg.columns else np.zeros(len(agg))
    plat = agg["platform_capital_monthly"].values if "platform_capital_monthly" in agg.columns else np.zeros(len(agg))
    disbursed = agg["pot_disbursed_monthly"].values if "pot_disbursed_monthly" in agg.columns else np.zeros(len(agg))

    cum_user = np.cumsum(contrib)
    cum_plat = np.cumsum(plat)
    cum_dis  = np.cumsum(disbursed)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=agg["month"], y=cum_dis, name="Total Pot Turnover",
        mode="lines", line=dict(color=PURPLE, width=2.5, shape="spline"),
        fill="tozeroy", fillcolor=_hex_rgba(PURPLE, 0.08),
        hovertemplate="Month %{x}<br>Pot Turnover: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=agg["month"], y=cum_user, name="User Deposits",
        mode="lines", line=dict(color=BACHAT_GREEN, width=2.5, shape="spline"),
        fill="tozeroy", fillcolor=_hex_rgba(BACHAT_GREEN, 0.12),
        hovertemplate="Month %{x}<br>User Deposits: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=agg["month"], y=cum_plat, name="Platform Capital",
        mode="lines", line=dict(color=WARNING, width=2, dash="dash", shape="spline"),
        hovertemplate="Month %{x}<br>Platform Capital: %{y:,.0f}<extra></extra>",
    ))
    return _theme(fig, "Cumulative Deposits vs Pot Turnover", height=380)


def chart_deposits_monthly(agg: pd.DataFrame) -> go.Figure:
    """Stacked bar: user deposits + platform capital, with pot turnover line."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    contrib = agg["user_contributions_monthly"] if "user_contributions_monthly" in agg.columns else pd.Series(np.zeros(len(agg)))
    plat = agg["platform_capital_monthly"] if "platform_capital_monthly" in agg.columns else pd.Series(np.zeros(len(agg)))
    disbursed = agg["pot_disbursed_monthly"] if "pot_disbursed_monthly" in agg.columns else pd.Series(np.zeros(len(agg)))

    fig.add_trace(go.Bar(
        x=agg["month"], y=contrib, name="User Deposits",
        marker_color=BACHAT_GREEN, opacity=0.85,
        hovertemplate="Month %{x}<br>User Deposits: %{y:,.0f}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=agg["month"], y=plat, name="Platform Capital",
        marker_color=WARNING, opacity=0.70,
        hovertemplate="Month %{x}<br>Platform Capital: %{y:,.0f}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=agg["month"], y=disbursed, name="Pot Turnover",
        mode="lines",
        line=dict(color=PURPLE, width=2.5),
        hovertemplate="Month %{x}<br>Pot Turnover: %{y:,.0f}<extra></extra>",
    ), secondary_y=True)
    fig.update_layout(
        barmode="stack", height=400,
        margin=dict(l=16, r=16, t=48, b=36),
        template=PLOTLY_TEMPLATE, paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1.0, font=dict(size=11)),
        hovermode="x unified",
        title=dict(text="Monthly Deposits & Platform Capital",
                   font=dict(size=14, color=INK), x=0.0, xanchor="left"),
    )
    fig.update_yaxes(title_text="Amount (PKR)", secondary_y=False, gridcolor=SLATE_100)
    fig.update_yaxes(title_text="Pot Turnover (PKR)", secondary_y=True, gridcolor=SLATE_100)
    return fig


def chart_float_timeline(agg: pd.DataFrame) -> go.Figure:
    """Area chart of platform float outstanding over time."""
    flt = agg["float_outstanding_monthly"] if "float_outstanding_monthly" in agg.columns else pd.Series(np.zeros(len(agg)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=agg["month"], y=flt, name="Float Outstanding",
        mode="lines", line=dict(color=TEAL, width=2.5, shape="spline"),
        fill="tozeroy", fillcolor=_hex_rgba(TEAL, 0.12),
        hovertemplate="Month %{x}<br>Float: %{y:,.0f}<extra></extra>",
    ))
    return _theme(fig, "Platform Float Outstanding", height=320)


def chart_profit_gauge(cfg: BachatConfig) -> go.Figure:
    """Four horizontal gauge indicators: margin, loss, profit/user, float ROI."""
    eco      = cycle_economics(cfg, cfg.durations[0])
    margin   = eco["net_profit"] / eco["total_revenue"] * 100 if eco["total_revenue"] else 0
    loss_pct = eco["net_default"] / eco["total_revenue"] * 100 if eco["total_revenue"] else 0
    profit_per_user = eco["net_profit"] / eco["user_slots"] if eco["user_slots"] else 0
    float_roi = (eco["net_profit"] / eco["avg_float_outstanding"] * 100
                 if eco["avg_float_outstanding"] else 0)

    m_color = BACHAT_GREEN if margin > 30 else (WARNING if margin > 0 else DANGER)
    l_color = BACHAT_GREEN if loss_pct < 8 else (WARNING if loss_pct < 20 else DANGER)

    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "indicator"}] * 2] * 2,
        horizontal_spacing=0.12,
        vertical_spacing=0.25,
    )

    indicators = [
        ("Net Margin",     round(margin, 1),         "%",  m_color, [-20, 80],  0,   1, 1),
        ("Loss / Revenue", round(loss_pct, 1),       "%",  l_color, [0, 50],   20,   1, 2),
        ("Profit / User",  round(profit_per_user, 0), "",  INFO,    [0, max(profit_per_user * 2, 1000)], None, 2, 1),
        ("Float ROI",      round(float_roi, 1),      "%",  PURPLE,  [0, max(float_roi * 2, 100)], None, 2, 2),
    ]

    for title, val, suffix, color, axis_range, threshold, row, col in indicators:
        gauge_cfg = {
            "axis": {"range": axis_range,
                     "tickfont": {"size": 10, "color": SLATE_300},
                     "dtick": (axis_range[1] - axis_range[0]) / 4},
            "bar": {"color": color, "thickness": 0.6},
            "bgcolor": SLATE_100,
            "borderwidth": 0,
            "shape": "bullet",
        }
        if threshold is not None:
            gauge_cfg["threshold"] = {
                "line": {"color": SLATE_500, "width": 2},
                "thickness": 0.85, "value": threshold,
            }
            gauge_cfg["steps"] = [
                {"range": [axis_range[0], threshold], "color": _hex_rgba(color, 0.08)},
                {"range": [threshold, axis_range[1]], "color": _hex_rgba(SLATE_300, 0.10)},
            ]

        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=val,
            title={"text": f"<b>{title}</b>",
                   "font": {"size": 13, "color": SLATE_500, "family": "Inter"}},
            number={"suffix": suffix,
                    "font": {"size": 26, "color": color, "family": "Inter"},
                    "valueformat": ",.1f" if suffix == "%" else ",.0f"},
            gauge=gauge_cfg,
        ), row=row, col=col)

    fig.update_layout(
        height=260, margin=dict(l=24, r=24, t=28, b=16),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
    )
    return fig


def chart_income_statement(eco: Dict) -> go.Figure:
    """Horizontal waterfall-style income statement."""
    labels = ["Fees", "Base NII", "Float NII", "Fee NII", "Penalty",
              "Gross Revenue", "Default Loss", "Net Profit"]
    values = [eco["fees"], eco["base_nii"], eco["float_nii"],
              eco["fee_nii"], eco["penalty_income"],
              eco["total_revenue"], -eco["net_default"],
              eco["net_profit"]]
    colors = [BACHAT_GREEN, INFO, PURPLE, TEAL, WARNING,
              BACHAT_GREEN_DARK, DANGER,
              BACHAT_GREEN if eco["net_profit"] >= 0 else DANGER]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors, text=[fmt_pkr(v) for v in values],
        textposition="outside", textfont=dict(size=11),
    ))
    fig.update_layout(
        height=340, margin=dict(l=8, r=60, t=32, b=8),
        template=PLOTLY_TEMPLATE, paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        xaxis=dict(showgrid=True, gridcolor=SLATE_100, zeroline=True,
                   zerolinecolor=SLATE_300),
        yaxis=dict(autorange="reversed"),
        title=dict(text="Cycle Income Statement (per group)",
                   font=dict(size=13, color=INK), x=0.0),
    )
    return fig


def chart_default_split(agg: pd.DataFrame) -> go.Figure:
    """Stacked bar: pre vs post payout default loss over time."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["month"], y=agg.get("pre_payout_loss_monthly", 0),
        name="Pre-Payout (Operational)", marker_color=WARNING))
    fig.add_trace(go.Bar(
        x=agg["month"], y=agg.get("post_payout_loss_monthly", 0),
        name="Post-Payout (Credit)", marker_color=DANGER))
    fig.update_layout(barmode="stack")
    return _theme(fig, "Default Loss: Pre vs Post Payout", height=380)


def chart_user_waterfall(agg: pd.DataFrame) -> go.Figure:
    """Area chart: new, returning, active users over time."""
    fig = go.Figure()
    for col, name, color in [
        ("active_users",    "Active",    BACHAT_GREEN),
        ("new_users",       "New",       INFO),
        ("returning_users", "Returning", PURPLE),
        ("churned_users",   "Churned",   DANGER),
    ]:
        if col in agg.columns:
            fig.add_trace(go.Scatter(
                x=agg["month"], y=agg[col], name=name, mode="lines",
                line=dict(color=color, width=2),
                fill="tozeroy" if col == "active_users" else "none",
                fillcolor=_hex_rgba(color, 0.08)))
    return _theme(fig, "User Lifecycle", height=380)


def chart_scenario_comparison(scenarios: Dict[str, pd.DataFrame]) -> go.Figure:
    """Line chart comparing net profit across Base/Optimistic/Pessimistic."""
    colors = {"Base": INFO, "Optimistic": BACHAT_GREEN, "Pessimistic": DANGER}
    fig = go.Figure()
    for name, df in scenarios.items():
        agg = _agg_monthly(df)
        fig.add_trace(go.Scatter(
            x=agg["month"], y=agg["net_profit_monthly"],
            name=name, mode="lines",
            line=dict(color=colors.get(name, SLATE_500), width=2.5,
                      dash="solid" if name == "Base" else
                           "dot" if name == "Optimistic" else "dash")))
    fig.add_hline(y=0, line=dict(color=SLATE_300, width=1, dash="dot"))
    return _theme(fig, "Scenario Comparison — Monthly Net Profit", height=400)


def chart_scenario_revenue(scenarios: Dict[str, pd.DataFrame]) -> go.Figure:
    """Bar chart of total revenue per scenario per year."""
    colors = {"Base": INFO, "Optimistic": BACHAT_GREEN, "Pessimistic": DANGER}
    fig = go.Figure()
    for name, df in scenarios.items():
        yearly = df.groupby("year")["total_revenue_monthly"].sum().reset_index()
        fig.add_trace(go.Bar(
            x=yearly["year"], y=yearly["total_revenue_monthly"],
            name=name, marker_color=colors.get(name, SLATE_500)))
    fig.update_layout(barmode="group")
    return _theme(fig, "Annual Revenue by Scenario", height=380)


def chart_market_funnel(cfg: BachatConfig, df: pd.DataFrame) -> go.Figure:
    """TAM / SAM / SOM funnel with simulated user penetration."""
    sim_users = int(df["active_users"].max()) if "active_users" in df.columns else 0
    fig = go.Figure(go.Funnel(
        y=["TAM", "SAM", "SOM", "Simulated Peak"],
        x=[cfg.market_size, cfg.sam_size, cfg.som_size, sim_users],
        textinfo="value+percent initial",
        marker=dict(color=[SLATE_300, INFO, BACHAT_GREEN, BACHAT_GREEN_DARK]),
        connector=dict(line=dict(color=SLATE_200, width=1)),
    ))
    fig.update_layout(height=340, margin=dict(l=16, r=16, t=48, b=8),
                      paper_bgcolor=WHITE, plot_bgcolor=WHITE,
                      title=dict(text="Market Penetration Funnel",
                                 font=dict(size=14, color=INK), x=0.0))
    return fig


def chart_market_growth(cfg: BachatConfig) -> go.Figure:
    """Projected TAM/SAM/SOM growth over 5 years."""
    years = list(range(1, 6))
    g     = cfg.market_growth_rate / 100.0
    fig   = go.Figure()
    for name, base, color in [
        ("TAM", cfg.market_size, SLATE_300),
        ("SAM", cfg.sam_size,    INFO),
        ("SOM", cfg.som_size,    BACHAT_GREEN),
    ]:
        vals = [base * (1 + g) ** (y - 1) for y in years]
        fig.add_trace(go.Scatter(x=years, y=vals, name=name, mode="lines+markers",
                                 line=dict(color=color, width=2.5)))
    return _theme(fig, f"Market Size Projection ({cfg.market_growth_rate:.0f}% p.a.)",
                  height=340)


def chart_yoy_projection(proj: pd.DataFrame) -> go.Figure:
    """Bar + line: actual vs projected revenue and profit YoY."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    sim  = proj[proj["source"] == "Simulated"]
    ext  = proj[proj["source"] == "Projected"]

    fig.add_trace(go.Bar(x=sim["year"], y=sim["revenue"],
                         name="Revenue (Simulated)", marker_color=BACHAT_GREEN,
                         opacity=0.85), secondary_y=False)
    fig.add_trace(go.Bar(x=ext["year"], y=ext["revenue"],
                         name="Revenue (Projected)", marker_color=BACHAT_GREEN,
                         opacity=0.45, marker_pattern_shape="/"), secondary_y=False)
    fig.add_trace(go.Scatter(x=proj["year"], y=proj["profit"],
                             name="Net Profit", mode="lines+markers",
                             line=dict(color=INFO, width=2.5)), secondary_y=True)
    fig.update_layout(barmode="group", height=380,
                      margin=dict(l=16, r=16, t=48, b=36),
                      template=PLOTLY_TEMPLATE, paper_bgcolor=WHITE, plot_bgcolor=WHITE,
                      hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                  xanchor="right", x=1.0),
                      title=dict(text="YoY Revenue & Profit (Simulated + Projected)",
                                 font=dict(size=14, color=INK), x=0.0))
    fig.update_yaxes(title_text="Revenue (PKR)", secondary_y=False,
                     gridcolor=SLATE_100)
    fig.update_yaxes(title_text="Net Profit (PKR)", secondary_y=True)
    return fig


def chart_profit_split_area(agg: pd.DataFrame) -> go.Figure:
    """Stacked area: Party A vs Party B net profit share over time."""
    party_a = agg["party_a_monthly"]
    party_b = agg["party_b_monthly"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=agg["month"], y=party_a,
        name="Party A (Platform)", mode="lines",
        line=dict(color=BACHAT_GREEN, width=0),
        fill="tozeroy", fillcolor=_hex_rgba(BACHAT_GREEN, 0.55),
        stackgroup="split",
    ))
    fig.add_trace(go.Scatter(
        x=agg["month"], y=party_b,
        name="Party B (Investors)", mode="lines",
        line=dict(color=INFO, width=0),
        fill="tonexty", fillcolor=_hex_rgba(INFO, 0.45),
        stackgroup="split",
    ))
    # Net profit line on top
    fig.add_trace(go.Scatter(
        x=agg["month"], y=agg["net_profit_monthly"],
        name="Net Profit (total)", mode="lines",
        line=dict(color=INK, width=2, dash="dot"),
    ))
    return _theme(fig, "Party A vs Party B — Monthly Profit Split", height=360)


def chart_profit_split_donut(party_a: float, party_b: float,
                              pct_a: float) -> go.Figure:
    """Donut focused purely on profit split between the two parties."""
    pct_b = 100 - pct_a
    colors = [BACHAT_GREEN, INFO]
    fig = go.Figure(go.Pie(
        labels=[f"Party A  ({pct_a:.0f}%)", f"Party B  ({pct_b:.0f}%)"],
        values=[max(0, party_a), max(0, party_b)],
        hole=0.62,
        marker=dict(colors=colors,
                    line=dict(color=WHITE, width=3)),
        textinfo="label+value",
        texttemplate="%{label}<br><b>%{value:,.0f}</b>",
        textfont=dict(size=11, color=INK),
        insidetextorientation="horizontal",
        pull=[0.04, 0],
        direction="clockwise",
        sort=False,
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=8, r=8, t=40, b=8),
        paper_bgcolor=WHITE,
        showlegend=False,
        title=dict(text="Cumulative Profit Split",
                   font=dict(size=13, color=INK), x=0.5, xanchor="center"),
        annotations=[dict(
            text=f"<b>{pct_a:.0f}% / {pct_b:.0f}%</b>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=INK, family="Inter"),
        )],
    )
    return fig


def chart_profit_split_yearly(df: pd.DataFrame, cfg: BachatConfig) -> go.Figure:
    """Grouped bar — Party A vs B profit per year."""
    yearly = df.groupby("year").agg(
        party_a=("party_a_monthly", "sum"),
        party_b=("party_b_monthly", "sum"),
    ).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=yearly["year"], y=yearly["party_a"],
        name=f"Party A ({cfg.profit_split_party_a:.0f}%)",
        marker_color=BACHAT_GREEN,
        text=[fmt_pkr(v) for v in yearly["party_a"]],
        textposition="outside", textfont=dict(size=10),
    ))
    fig.add_trace(go.Bar(
        x=yearly["year"], y=yearly["party_b"],
        name=f"Party B ({100-cfg.profit_split_party_a:.0f}%)",
        marker_color=INFO,
        text=[fmt_pkr(v) for v in yearly["party_b"]],
        textposition="outside", textfont=dict(size=10),
    ))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Year", tickmode="linear")
    fig.update_yaxes(title_text="Profit (PKR)")
    return _theme(fig, "Annual Profit by Party", height=360)


# =============================================================================
# TAB FUNCTIONS
# =============================================================================

def tab_overview(cfg: BachatConfig, df: pd.DataFrame):
    agg      = _agg_monthly(df)
    eco      = cycle_economics(cfg, cfg.durations[0])
    insights = generate_insights(cfg, df)

    # ── Headline metrics row ─────────────────────────────────────────────────
    total_rev   = agg["total_revenue_monthly"].sum() if "total_revenue_monthly" in agg.columns else 0
    total_profit = agg["net_profit_monthly"].sum() if "net_profit_monthly" in agg.columns else 0
    peak_users  = agg["active_users"].max() if "active_users" in agg.columns else 0
    total_loss  = agg["default_loss_monthly"].sum() if "default_loss_monthly" in agg.columns else 0
    margin_pct  = (total_profit / total_rev * 100) if total_rev else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Revenue",   fmt_pkr(total_rev))
    k2.metric("Net Profit",      fmt_pkr(total_profit))
    k3.metric("Net Margin",      f"{margin_pct:.1f}%")
    k4.metric("Peak Users",      f"{peak_users:,.0f}")
    k5.metric("Default Losses",  fmt_pkr(total_loss))

    st.markdown("")

    # ── Trend sparklines + Bullet gauges ─────────────────────────────────────
    st.plotly_chart(chart_kpi_sparklines(agg),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_1")

    # ── Combo chart + insights panel ─────────────────────────────────────────
    main_col, right_col = st.columns([2, 1])
    with main_col:
        st.plotly_chart(chart_revenue_combo(agg),
                        use_container_width=True, config=_CFG_STATIC,
                        key="_pc_3")
    with right_col:
        items_html = "".join(
            f'<div class="insight-item">{ins}</div>' for ins in insights
        )
        st.markdown(f"""
        <div class="insights-panel">
            <h4>Smart Insights</h4>
            {items_html}
        </div>""", unsafe_allow_html=True)

    # ── Income statement ─────────────────────────────────────────────────────
    _sh("Cycle Income Statement")
    st.plotly_chart(chart_income_statement(eco),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_4")


def tab_deposits(cfg: BachatConfig, df: pd.DataFrame):
    agg = _agg_monthly(df)

    contrib   = agg["user_contributions_monthly"] if "user_contributions_monthly" in agg.columns else pd.Series(np.zeros(len(agg)))
    disbursed = agg["pot_disbursed_monthly"] if "pot_disbursed_monthly" in agg.columns else pd.Series(np.zeros(len(agg)))
    plat_cap  = agg["platform_capital_monthly"] if "platform_capital_monthly" in agg.columns else pd.Series(np.zeros(len(agg)))
    flt       = agg["float_outstanding_monthly"] if "float_outstanding_monthly" in agg.columns else pd.Series(np.zeros(len(agg)))
    users     = agg["active_users"] if "active_users" in agg.columns else pd.Series(np.ones(len(agg)))

    total_dep     = contrib.sum()
    total_dis     = disbursed.sum()
    total_plat    = plat_cap.sum()
    pool_balance  = (contrib.cumsum().iloc[-1] - disbursed.cumsum().iloc[-1]) if len(agg) else 0
    peak_flt      = flt.max()
    avg_per_user  = total_dep / users.sum() if users.sum() > 0 else 0

    # ── Headline metrics ─────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("User Deposits",       fmt_pkr(total_dep))
    k2.metric("Pot Turnover",        fmt_pkr(total_dis))
    k3.metric("Platform Capital",    fmt_pkr(total_plat))
    k4.metric("Peak Float",          fmt_pkr(peak_flt))
    k5.metric("Avg Deposit / User",  fmt_pkr(avg_per_user))

    st.markdown("")

    # ── Cumulative deposits vs disbursements ─────────────────────────────────
    st.plotly_chart(chart_deposits_cumulative(agg),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_dep_1")

    # ── Monthly flows + right panel ──────────────────────────────────────────
    left_col, right_col = st.columns([2, 1])
    with left_col:
        st.plotly_chart(chart_deposits_monthly(agg),
                        use_container_width=True, config=_CFG_STATIC,
                        key="_dep_2")
    with right_col:
        latest_net = (contrib.iloc[-1] - disbursed.iloc[-1]) if len(agg) else 0
        net_color = BACHAT_GREEN if latest_net >= 0 else DANGER
        net_arrow = "▲" if latest_net >= 0 else "▼"
        plat_share = (total_plat / total_dis * 100) if total_dis else 0
        st.markdown(f"""
        <div style="background:{WHITE}; border:1px solid {SLATE_200};
                    border-radius:14px; padding:1.5rem; text-align:center;
                    margin-top:1rem;">
            <div style="font-size:0.75rem; font-weight:600; color:{SLATE_500};
                        text-transform:uppercase; letter-spacing:0.05em;
                        margin-bottom:0.6rem;">Latest Month Net Flow</div>
            <div style="font-size:2rem; font-weight:800; color:{net_color};
                        letter-spacing:-0.02em;">
                {net_arrow} {fmt_pkr(abs(latest_net))}
            </div>
            <div style="font-size:0.78rem; color:{SLATE_500}; margin-top:0.5rem;
                        line-height:1.5;">
                User deposits minus total pot payouts.<br>
                Gap = platform's blocked-slot capital.
            </div>
        </div>""", unsafe_allow_html=True)

        velocity = contrib.iloc[-1] / (total_dep / len(agg)) * 100 if len(agg) and total_dep else 100
        st.markdown(f"""
        <div style="background:{SLATE_50}; border:1px solid {SLATE_200};
                    border-radius:14px; padding:1rem 1.2rem; margin-top:0.8rem;">
            <div style="font-size:0.7rem; font-weight:700; color:{SLATE_500};
                        text-transform:uppercase; letter-spacing:0.05em;
                        margin-bottom:0.5rem;">Quick Stats</div>
            <div style="display:flex; justify-content:space-between;
                        font-size:0.82rem; padding:0.3rem 0;
                        border-bottom:1px solid {SLATE_200};">
                <span style="color:{SLATE_500};">Platform Capital Share</span>
                <b style="color:{INK};">{plat_share:.1f}%</b>
            </div>
            <div style="display:flex; justify-content:space-between;
                        font-size:0.82rem; padding:0.3rem 0;
                        border-bottom:1px solid {SLATE_200};">
                <span style="color:{SLATE_500};">Deposit Velocity</span>
                <b style="color:{INK};">{velocity:.0f}% of avg</b>
            </div>
            <div style="display:flex; justify-content:space-between;
                        font-size:0.82rem; padding:0.3rem 0;">
                <span style="color:{SLATE_500};">Peak Float</span>
                <b style="color:{INK};">{fmt_pkr(peak_flt)}</b>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Float outstanding ────────────────────────────────────────────────────
    _sh("Platform Float")
    st.plotly_chart(chart_float_timeline(agg),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_dep_3")


def tab_risk(cfg: BachatConfig, df: pd.DataFrame):
    _sh("Default Loss — Pre vs Post Payout")
    st.caption(
        "Pre-payout: member stops paying before receiving the pot (operational loss). "
        "Post-payout: member receives pot then defaults (credit loss / receivable)."
    )
    agg = _agg_monthly(df)
    st.plotly_chart(chart_default_split(agg),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_5")

    # KPI strip
    c1, c2, c3, c4 = st.columns(4)
    total_pre  = df["pre_payout_loss_monthly"].sum()
    total_post = df["post_payout_loss_monthly"].sum()
    total_loss = total_pre + total_post
    total_rev  = df["total_revenue_monthly"].sum()
    c1.metric("Total Default Loss",    fmt_pkr(total_loss))
    c2.metric("Pre-Payout (Ops)",      fmt_pkr(total_pre),
              f"{cfg.default_pre_pct:.0f}% of loss")
    c3.metric("Post-Payout (Credit)",  fmt_pkr(total_post),
              f"{cfg.default_post_pct:.0f}% of loss")
    c4.metric("Loss / Revenue",
              f"{total_loss/total_rev*100:.1f}%" if total_rev else "—")

    _sh("Slot-by-Slot Exposure Table")
    for dur in cfg.durations:
        for slab in cfg.slab_amounts:
            eco = cycle_economics(cfg, dur, slab)
            verdict_cls = ("verdict-good" if eco["net_profit"] > 0 else "verdict-bad")
            st.markdown(
                f'<span class="verdict {verdict_cls}">'
                f'{dur}M / PKR {slab:,} — Net profit per cycle: '
                f'{fmt_pkr(eco["net_profit"])}'
                f'</span>', unsafe_allow_html=True
            )
            st.dataframe(build_slot_table(cfg, dur, slab),
                         use_container_width=True, hide_index=True)

    _sh("Audit Trail")
    st.markdown("""
    <div class="audit-box">
    <b>Slot-conditional default loss</b>: only user-held slots (blocked+1 … N)
    contribute to expected loss. Slot <i>s</i> exposure = (N−s)×M, so early
    slot recipients are highest-risk.<br><br>
    <b>Pre/post-payout split</b>: pre-payout defaults reduce platform cash flow
    (no pot was paid so the exposure is the un-recovered contributions); post-payout
    defaults create a receivable on the member who received the pot.
    Both are included in the cycle net loss.
    </div>""", unsafe_allow_html=True)


def tab_revenue(cfg: BachatConfig, df: pd.DataFrame):
    _sh("Revenue Components Over Time")
    agg = _agg_monthly(df)
    st.plotly_chart(chart_revenue_combo(agg),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_6")

    _sh("NII Breakdown")
    annual_rate = cfg.kibor_rate + cfg.spread
    rows_eco = []
    for dur in cfg.durations:
        for slab in cfg.slab_amounts:
            eco = cycle_economics(cfg, dur, slab)
            rows_eco.append({
                "Duration": f"{dur}M",
                "Slab (PKR)": f"{slab:,}",
                "Fee Mode": cfg.fee_collection_mode,
                "Base NII": fmt_pkr(eco["base_nii"]),
                "Float NII": fmt_pkr(eco["float_nii"]),
                "Fee NII": fmt_pkr(eco["fee_nii"]),
                "Total Fees": fmt_pkr(eco["fees"]),
                "Penalty": fmt_pkr(eco["penalty_income"]),
                "Total Rev": fmt_pkr(eco["total_revenue"]),
                "Net Profit": fmt_pkr(eco["net_profit"]),
            })
    st.dataframe(pd.DataFrame(rows_eco), use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div class="audit-box">
    <b>Three principals, no double-counting:</b><br>
    • <b>Base NII</b>: full monthly pool (N×M) × {annual_rate:.2f}% × (disbursement_day − collection_day)/365.<br>
    • <b>Float NII</b>: working-capital blocked in platform slots — entirely different principal.<br>
    • <b>Fee NII</b>: collected fees held for {'half' if cfg.fee_collection_mode == 'Upfront' else 'a quarter of'} the cycle
      ({cfg.fee_collection_mode} mode → {'N×30/2' if cfg.fee_collection_mode == 'Upfront' else 'N×30/4'} day hold).
    </div>""", unsafe_allow_html=True)


def tab_users(cfg: BachatConfig, df: pd.DataFrame):
    _sh("User Lifecycle")
    agg = _agg_monthly(df)
    st.plotly_chart(chart_user_waterfall(agg),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_7")

    # MoM growth metrics
    _sh("Month-on-Month & Year-on-Year Metrics")
    yearly = df.groupby("year").agg(
        active_users=("active_users", "max"),
        revenue     =("total_revenue_monthly", "sum"),
        profit      =("net_profit_monthly",     "sum"),
    ).reset_index()
    yearly["users_yoy_%"]   = yearly["active_users"].pct_change() * 100
    yearly["revenue_yoy_%"] = yearly["revenue"].pct_change()       * 100
    yearly["profit_yoy_%"]  = yearly["profit"].pct_change()        * 100
    st.dataframe(yearly.round(1), use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div class="audit-box">
    <b>Two-pass lifecycle:</b> returning_users[m] is resolved from return_schedule[m]
    <em>before</em> processing finish_origin &lt; m — ensuring second-generation churn
    and multi-cycle return rates compound correctly.<br><br>
    Growth rate: <b>{cfg.monthly_growth_rate:.1f}%/mo</b> |
    Churn: <b>{cfg.churn_rate:.1f}%</b> |
    Return rate: <b>{cfg.returning_user_rate:.1f}%</b> |
    Rest: <b>{cfg.rest_period_months} month(s)</b>
    </div>""", unsafe_allow_html=True)


def tab_pnl(cfg: BachatConfig, df: pd.DataFrame):
    _sh("Profit & Loss — Yearly Summary with Projections")
    proj = build_yearly_projection(df, cfg, extra_years=3)
    st.plotly_chart(chart_yoy_projection(proj),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_8")

    st.caption(f"Simulated years use model output. Projected years apply "
               f"{cfg.yoy_growth_rate:.0f}% YoY growth to the last simulated year.")
    st.dataframe(proj.assign(
        revenue=proj["revenue"].map(fmt_pkr),
        profit =proj["profit"].map(fmt_pkr),
        loss   =proj["loss"].map(fmt_pkr),
        fees   =proj["fees"].map(fmt_pkr),
    ), use_container_width=True, hide_index=True)

    _sh("Monthly P&L Breakdown")
    agg = _agg_monthly(df)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=agg["month"], y=agg["total_revenue_monthly"],
                             name="Revenue", mode="lines",
                             line=dict(color=BACHAT_GREEN, width=2.5)))
    fig.add_trace(go.Scatter(x=agg["month"], y=agg["net_profit_monthly"],
                             name="Net Profit", mode="lines",
                             line=dict(color=INFO, width=2.5)))
    fig.add_trace(go.Scatter(x=agg["month"], y=agg["default_loss_monthly"],
                             name="Default Loss", mode="lines",
                             line=dict(color=DANGER, width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=agg["month"], y=agg["party_a_monthly"],
                             name="Party A", mode="lines",
                             line=dict(color=PURPLE, width=2, dash="dot")))
    st.plotly_chart(_theme(fig, "P&L Over Time", height=400),
                    use_container_width=True, config=_CFG_STATIC,
                    key="pnl_monthly_breakdown")

    # ── Profit Split ─────────────────────────────────────────────────────────
    total_fees    = df["fees_monthly"].sum()
    total_b_nii   = df["base_nii_monthly"].sum()
    total_fl_nii  = df["float_nii_monthly"].sum()
    total_fee_nii = df["fee_nii_monthly"].sum()
    total_pen     = df["penalty_income_monthly"].sum()
    total_loss    = df["default_loss_monthly"].sum()
    total_profit  = df["net_profit_monthly"].sum()
    party_a_total = df["party_a_monthly"].sum()
    party_b_total = total_profit - party_a_total
    pct_a         = cfg.profit_split_party_a
    pct_b         = 100 - pct_a
    total_rev     = total_fees + total_b_nii + total_fl_nii + total_fee_nii + total_pen

    _sh("Profit Split — Party A vs Party B")

    # ── KPI strip ────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Revenue",   fmt_pkr(total_rev))
    k2.metric("Total Net Profit", fmt_pkr(total_profit),
              f"{total_profit/total_rev*100:.1f}% margin" if total_rev else None)
    k3.metric("Default Loss",    fmt_pkr(total_loss),
              f"−{total_loss/total_rev*100:.1f}% of rev" if total_rev else None)
    k4.metric(f"Party A  ({pct_a:.0f}%)", fmt_pkr(party_a_total),
              "Platform / Operator")
    k5.metric(f"Party B  ({pct_b:.0f}%)", fmt_pkr(party_b_total),
              "Investors / Partners")
    k6.metric("A : B Ratio",
              f"{party_a_total/party_b_total:.1f}x" if party_b_total else "∞")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Donut  +  Stacked area  (side by side) ────────────────────────────────
    col_donut, col_area = st.columns([1, 2])
    with col_donut:
        st.plotly_chart(
            chart_profit_split_donut(party_a_total, party_b_total, pct_a),
            use_container_width=True, config=_CFG_STATIC,
            key="pnl_split_donut")
        # Labelled breakdown under donut
        st.markdown(f"""
        <div style="background:{BACHAT_GREEN_LIGHT}; border:1px solid {BACHAT_GREEN};
                    border-radius:10px; padding:0.85rem 1rem; margin-top:0.5rem;">
            <div style="font-size:0.68rem; font-weight:700; text-transform:uppercase;
                        letter-spacing:0.06em; color:{BACHAT_GREEN_DARK}; margin-bottom:0.6rem;">
                Profit Allocation
            </div>
            <div style="display:flex; justify-content:space-between;
                        font-size:0.82rem; padding:0.3rem 0;
                        border-bottom:1px solid rgba(0,160,80,0.2);">
                <span style="color:{SLATE_700};">
                    <b style="color:{BACHAT_GREEN};">●</b>&nbsp;
                    Party A (Platform)&nbsp;&nbsp;<span style="color:{SLATE_500};">{pct_a:.0f}%</span>
                </span>
                <b style="color:{INK};">{fmt_pkr(party_a_total)}</b>
            </div>
            <div style="display:flex; justify-content:space-between;
                        font-size:0.82rem; padding:0.3rem 0;">
                <span style="color:{SLATE_700};">
                    <b style="color:{INFO};">●</b>&nbsp;
                    Party B (Investors)&nbsp;&nbsp;<span style="color:{SLATE_500};">{pct_b:.0f}%</span>
                </span>
                <b style="color:{INK};">{fmt_pkr(party_b_total)}</b>
            </div>
        </div>""", unsafe_allow_html=True)

    with col_area:
        st.plotly_chart(
            chart_profit_split_area(agg),
            use_container_width=True, config=_CFG_STATIC,
            key="pnl_split_area")

    # ── Annual grouped bar ────────────────────────────────────────────────────
    st.plotly_chart(
        chart_profit_split_yearly(df, cfg),
        use_container_width=True, config=_CFG_STATIC,
        key="pnl_split_yearly")

    # ── Yearly breakdown table ────────────────────────────────────────────────
    _sh("Year-by-Year Profit Allocation")
    yt = df.groupby("year").agg(
        revenue       =("total_revenue_monthly",   "sum"),
        net_profit    =("net_profit_monthly",       "sum"),
        default_loss  =("default_loss_monthly",     "sum"),
        party_a       =("party_a_monthly",          "sum"),
        party_b       =("party_b_monthly",          "sum"),
    ).reset_index()
    yt["margin_%"]     = (yt["net_profit"] / yt["revenue"] * 100).round(1)
    yt["A_pct_check"]  = (yt["party_a"]   / yt["net_profit"] * 100).round(1)

    display_yt = yt.copy()
    display_yt["revenue"]      = yt["revenue"].map(fmt_pkr)
    display_yt["net_profit"]   = yt["net_profit"].map(fmt_pkr)
    display_yt["default_loss"] = yt["default_loss"].map(fmt_pkr)
    display_yt["party_a"]      = yt["party_a"].map(fmt_pkr)
    display_yt["party_b"]      = yt["party_b"].map(fmt_pkr)
    display_yt["margin_%"]     = yt["margin_%"].astype(str) + "%"
    display_yt["A_pct_check"]  = yt["A_pct_check"].astype(str) + "%"
    display_yt.columns = ["Year", "Revenue", "Net Profit", "Default Loss",
                          f"Party A ({pct_a:.0f}%)", f"Party B ({pct_b:.0f}%)",
                          "Net Margin", "A's Actual %"]
    st.dataframe(display_yt, use_container_width=True, hide_index=True)

    # ── Revenue allocation donut ──────────────────────────────────────────────
    _sh("Cumulative Revenue Allocation")
    fig_rev = go.Figure(go.Pie(
        labels=["Fees", "Base NII", "Float NII", "Fee NII",
                "Penalty", "Default Loss", "Net Profit"],
        values=[total_fees, total_b_nii, total_fl_nii, total_fee_nii,
                total_pen, total_loss, max(0, total_profit)],
        hole=0.5,
        marker=dict(colors=[BACHAT_GREEN, INFO, PURPLE, TEAL,
                             WARNING, DANGER, BACHAT_GREEN_DARK]),
        textinfo="label+percent",
        textfont=dict(size=11),
    ))
    fig_rev.update_layout(
        height=340, margin=dict(l=8, r=8, t=40, b=8),
        paper_bgcolor=WHITE,
        title=dict(text="Revenue Waterfall — Where Does Each Rupee Go?",
                   font=dict(size=13, color=INK), x=0.0),
    )
    st.plotly_chart(fig_rev, use_container_width=True, config=_CFG_STATIC,
                    key="pnl_rev_alloc_donut")


def tab_scenarios(cfg: BachatConfig):
    _sh("Scenario Analysis — Base / Optimistic / Pessimistic")
    st.caption(
        "Optimistic: default rate ×0.5, growth ×1.25, recovery ×1.2. "
        "Pessimistic: default rate ×2.0, growth ×0.6, recovery ×0.7."
    )
    scenarios = build_scenarios(cfg)

    st.plotly_chart(chart_scenario_comparison(scenarios),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_11")
    st.plotly_chart(chart_scenario_revenue(scenarios),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_12")

    _sh("Scenario Summary Table")
    summary_rows = []
    for name, sdf in scenarios.items():
        total_rev    = sdf["total_revenue_monthly"].sum()
        total_profit = sdf["net_profit_monthly"].sum()
        total_loss   = sdf["default_loss_monthly"].sum()
        peak_users   = int(sdf["active_users"].max())
        summary_rows.append({
            "Scenario":       name,
            "Total Revenue":  fmt_pkr(total_rev),
            "Total Profit":   fmt_pkr(total_profit),
            "Total Loss":     fmt_pkr(total_loss),
            "Loss / Rev %":   f"{total_loss/total_rev*100:.1f}%" if total_rev else "—",
            "Peak Active Users": f"{peak_users:,}",
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="audit-box">
    <b>Scenario assumptions are multiplicative adjustments on the current config.</b>
    They are not separate parameter sets — the Base scenario is your exact sidebar
    configuration. Use this tab to stress-test model resilience to economic shocks.
    </div>""", unsafe_allow_html=True)


def tab_market(cfg: BachatConfig, df: pd.DataFrame):
    _sh("Market Opportunity — TAM / SAM / SOM")

    agg = _agg_monthly(df)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_market_funnel(cfg, agg),
                        use_container_width=True, config=_CFG_STATIC,
                        key="_pc_13")
    with c2:
        st.plotly_chart(chart_market_growth(cfg),
                        use_container_width=True, config=_CFG_STATIC,
                        key="_pc_14")

    # Penetration metrics
    _sh("Penetration Metrics")
    sim_peak    = int(agg["active_users"].max())
    som_pct     = sim_peak / cfg.som_size  * 100 if cfg.som_size  else 0
    sam_pct     = sim_peak / cfg.sam_size  * 100 if cfg.sam_size  else 0
    tam_pct     = sim_peak / cfg.market_size * 100 if cfg.market_size else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TAM",           f"{cfg.market_size:,}")
    col2.metric("SAM",           f"{cfg.sam_size:,}",
                f"{cfg.sam_size/cfg.market_size*100:.1f}% of TAM")
    col3.metric("SOM",           f"{cfg.som_size:,}",
                f"{cfg.som_size/cfg.sam_size*100:.1f}% of SAM" if cfg.sam_size else "—")
    col4.metric("Simulated Peak", f"{sim_peak:,}",
                f"{som_pct:.1f}% of SOM")

    _sh("TAM Distribution Config")
    if cfg.use_tam:
        st.success("TAM distribution is ENABLED — users are scaled by duration × slab shares.")
        share_rows = []
        for dur in cfg.durations:
            for slab in cfg.slab_amounts:
                d_pct = cfg.duration_share.get(dur, 100.0/len(cfg.durations))
                s_pct = cfg.slab_share.get(slab, 100.0/len(cfg.slab_amounts))
                share_rows.append({
                    "Duration": f"{dur}M",
                    "Slab": f"PKR {slab:,}",
                    "Duration Share %": f"{d_pct:.1f}%",
                    "Slab Share %": f"{s_pct:.1f}%",
                    "Combined Scale": f"{d_pct*s_pct/100:.2f}%",
                })
        st.dataframe(pd.DataFrame(share_rows), use_container_width=True, hide_index=True)
    else:
        st.info("TAM distribution is DISABLED. Enable it in the sidebar to scale users "
                "by duration × slab market shares.")

    st.markdown(f"""
    <div class="audit-box">
    <b>Market growth projection</b> uses {cfg.market_growth_rate:.0f}% p.a. compounded
    on the current TAM/SAM/SOM inputs.<br><br>
    <b>Penetration benchmark:</b> simulated peak active users ({sim_peak:,}) represents
    <b>{tam_pct:.3f}%</b> of TAM, <b>{sam_pct:.2f}%</b> of SAM,
    <b>{som_pct:.1f}%</b> of SOM.
    </div>""", unsafe_allow_html=True)


def tab_sensitivity(cfg: BachatConfig):
    _sh("Default Rate Sensitivity")
    st.caption("Net profit per cycle vs default rate. Zero-crossing = breakeven.")

    slab0 = cfg.slab_amounts[0]
    rates = np.arange(0, 31, 1)
    fig   = go.Figure()
    for dur, color in zip([3, 6, 9, 12], PLOTLY_COLORWAY):
        profits = [cycle_economics(
            dataclasses.replace(cfg, default_rate=float(r), durations=[dur]),
            dur, slab0)["net_profit"] for r in rates]
        fig.add_trace(go.Scatter(x=rates, y=profits, mode="lines",
                                 name=f"{dur}M", line=dict(color=color, width=2.5)))
    fig.add_hline(y=0, line=dict(color=SLATE_500, width=1.5, dash="dash"))
    fig.add_vline(x=cfg.default_rate, line=dict(color=WARNING, width=2, dash="dot"),
                  annotation_text=f"Current: {cfg.default_rate:.0f}%",
                  annotation_font=dict(size=11, color=WARNING))
    fig.update_xaxes(title_text="User Default Rate (%)")
    fig.update_yaxes(title_text="Net Profit per Cycle (PKR)")
    st.plotly_chart(_theme(fig, "Profit per Cycle vs Default Rate", height=400),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_15")

    _sh("Fee Sensitivity")
    st.caption("How net profit responds to fee % at different blocking levels.")
    fees_range  = np.arange(0, 16, 0.5)
    primary_dur = cfg.durations[0]
    fig2        = go.Figure()
    for blocks, color in zip(range(0, min(4, primary_dur)), PLOTLY_COLORWAY):
        profits = [cycle_economics(
            dataclasses.replace(cfg, slot_fee_pct=float(f),
                                blocked_slots_config={primary_dur: blocks},
                                durations=[primary_dur],
                                slot_fees_config={}),
            primary_dur, slab0)["net_profit"] for f in fees_range]
        fig2.add_trace(go.Scatter(x=fees_range, y=profits, mode="lines",
                                  name=f"{blocks} blocked",
                                  line=dict(color=color, width=2.5)))
    fig2.add_hline(y=0, line=dict(color=SLATE_500, width=1.5, dash="dash"))
    fig2.add_vline(x=cfg.slot_fee_pct, line=dict(color=WARNING, width=2, dash="dot"),
                   annotation_text=f"Current: {cfg.slot_fee_pct:.1f}%",
                   annotation_font=dict(size=11, color=WARNING))
    fig2.update_xaxes(title_text="Slot Fee % of Pot")
    fig2.update_yaxes(title_text="Net Profit per Cycle (PKR)")
    st.plotly_chart(_theme(fig2, f"Profit vs Fee — {primary_dur}M KOMMITTEE", height=400),
                    use_container_width=True, config=_CFG_STATIC,
                    key="_pc_16")

    _sh("Fee Mode Impact")
    st.caption("NII earned on collected fees: Upfront (half-cycle hold) vs Monthly (quarter-cycle hold).")
    mode_data = []
    for dur in cfg.durations:
        for slab in cfg.slab_amounts:
            eco_up  = cycle_economics(
                dataclasses.replace(cfg, fee_collection_mode="Upfront"), dur, slab)
            eco_mo  = cycle_economics(
                dataclasses.replace(cfg, fee_collection_mode="Monthly"), dur, slab)
            mode_data.append({
                "Duration": f"{dur}M",
                "Slab": f"PKR {slab:,}",
                "Fee NII — Upfront": fmt_pkr(eco_up["fee_nii"]),
                "Fee NII — Monthly": fmt_pkr(eco_mo["fee_nii"]),
                "Difference": fmt_pkr(eco_up["fee_nii"] - eco_mo["fee_nii"]),
            })
    st.dataframe(pd.DataFrame(mode_data), use_container_width=True, hide_index=True)


def tab_raw(df: pd.DataFrame):
    _sh("Raw Forecast Data")
    st.caption("All revenue/cost columns are suffixed _monthly. "
               "pre_payout_loss_monthly + post_payout_loss_monthly = default_loss_monthly.")
    st.dataframe(df, use_container_width=True, height=480)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download as CSV", csv,
                       "bachat_forecast_v3.csv", "text/csv")


# =============================================================================
# MAIN
# =============================================================================

def main():
    st.set_page_config(
        page_title="Bachat KOMMITTEE — Pricing & Risk",
        page_icon="◉",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()

    cfg = render_sidebar()

    # ── Validation gate ───────────────────────────────────────────────────────
    errors, warnings = validate_config(cfg)
    if errors:
        for err in errors:
            st.markdown(f'<div class="val-error">🚫 {err}</div>',
                        unsafe_allow_html=True)
        st.stop()
    for warn in warnings:
        st.markdown(f'<div class="val-warn">⚠ {warn}</div>',
                    unsafe_allow_html=True)

    df = build_forecast(cfg)

    annual_rate = cfg.kibor_rate + cfg.spread
    slabs_str   = " · ".join(f"PKR {s:,}/mo" for s in cfg.slab_amounts)
    st.markdown(f"""
    <div class="hero">
        <div class="hero-left">
            <h1>Bachat KOMMITTEE — Pricing &amp; Risk</h1>
            <p>Slot-conditional defaults · three-principal NII ·
               two-pass lifecycle · {cfg.simulation_months}-month horizon ·
               {cfg.fee_collection_mode} fees</p>
        </div>
        <div class="hero-pill">
            KIBOR {cfg.kibor_rate:.2f}% + Spread {cfg.spread:+.2f}%
            = <b>{annual_rate:.2f}%</b> &nbsp;|&nbsp;
            {", ".join(f"{d}M" for d in cfg.durations)} &nbsp;|&nbsp;
            {slabs_str}
        </div>
    </div>""", unsafe_allow_html=True)

    tabs = st.tabs([
        "📊 Overview",
        "💵 Deposits",
        "⚠️ Risk & Slots",
        "💰 Revenue & NII",
        "👥 Users",
        "📈 P&L",
        "🎭 Scenarios",
        "🌍 Market",
        "🔬 Sensitivity",
        "🗂 Raw Data",
    ])

    with tabs[0]: tab_overview(cfg, df)
    with tabs[1]: tab_deposits(cfg, df)
    with tabs[2]: tab_risk(cfg, df)
    with tabs[3]: tab_revenue(cfg, df)
    with tabs[4]: tab_users(cfg, df)
    with tabs[5]: tab_pnl(cfg, df)
    with tabs[6]: tab_scenarios(cfg)
    with tabs[7]: tab_market(cfg, df)
    with tabs[8]: tab_sensitivity(cfg)
    with tabs[9]: tab_raw(df)


if __name__ == "__main__":
    main()
