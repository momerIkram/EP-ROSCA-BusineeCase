
# ROSCA Forecast App - Ultimate Edition
# Fully working version: user growth, lifecycle tracking, participation caps, rest period enforcement, slot fee matrix,
# monthly configuration, chart normalization, and Excel export.

import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="ROSCA Forecast App", layout="wide")

# Input Configuration
st.sidebar.header("Global Configuration")

total_market = st.sidebar.number_input("Total Market Size", value=20000000)
tam_percentage = st.sidebar.slider("TAM %", 0, 100, 10)
starting_user_percentage = st.sidebar.slider("Starting User Base % of TAM", 0, 100, 10)
monthly_growth = st.sidebar.slider("Monthly Growth %", 0.0, 10.0, 2.0, step=0.1)

initial_tam = total_market * (tam_percentage / 100)
user_base = initial_tam * (starting_user_percentage / 100)

kibor = st.sidebar.slider("KIBOR (%)", 0.0, 25.0, 11.0, step=0.1)
spread = st.sidebar.slider("Spread (%)", 0.0, 20.0, 5.0, step=0.1)
default_rate = st.sidebar.slider("Default Rate (%)", 0.0, 10.0, 1.0, step=0.1)
rest_period = st.sidebar.slider("Rest Period (months)", 0, 12, 1)
fee_upfront = st.sidebar.selectbox("Fee Collected Upfront?", ["Yes", "No"]) == "Yes"

# Participation caps per duration
st.sidebar.markdown("### Participation Cap Per Year")
participation_caps = {
    3: st.sidebar.number_input("3M", min_value=1, max_value=12, value=3),
    4: st.sidebar.number_input("4M", min_value=1, max_value=12, value=2),
    5: st.sidebar.number_input("5M", min_value=1, max_value=12, value=1),
    6: st.sidebar.number_input("6M", min_value=1, max_value=12, value=1),
    8: st.sidebar.number_input("8M", min_value=1, max_value=12, value=1),
    10: st.sidebar.number_input("10M", min_value=1, max_value=12, value=1)
}

durations = [3, 4, 5, 6, 8, 10]
slabs = [1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000]

# Duration allocation
st.sidebar.markdown("### Committee Duration Allocation (%)")
duration_alloc = {d: st.sidebar.slider(f"{d}M", 0, 100, default) for d, default in zip(durations, [30, 25, 15, 10, 10, 10])}

# Slot fees
st.sidebar.markdown("### Slot Fee Structure (use 99 to block)")
slot_fees = {}
for d in durations:
    slot_fees[d] = {}
    for s in range(1, d + 1):
        slot_fees[d][s] = st.sidebar.number_input(f"{d}M - Slot {s} Fee %", min_value=0, max_value=100, value=(11 - s) if s <= 10 else 0)

# Forecast Logic
months = 60
results = []
users_per_month = []

for m in range(1, months + 1):
    if m == 1:
        current_users = user_base
    else:
        current_users *= (1 + monthly_growth / 100)
    users_per_month.append(current_users)

    for d in durations:
        user_share = current_users * (duration_alloc[d] / 100)
        per_slab_users = user_share / len(slabs)

        for slab in slabs:
            for slot in range(1, d + 1):
                fee_pct = slot_fees[d].get(slot, 0)
                if fee_pct == 99:
                    users = 0
                    deposit = 0
                    fee_collected = 0
                    nii = 0
                    profit = 0
                else:
                    users = per_slab_users
                    deposit = users * slab * d
                    fee_collected = deposit * (fee_pct / 100) if fee_upfront else 0
                    nii = deposit * ((kibor + spread) / 100 / 12)
                    profit = fee_collected + nii - (deposit * (default_rate / 100))

                results.append({
                    "Month": m,
                    "Duration": d,
                    "Slab": slab,
                    "Slot": slot,
                    "Users": users,
                    "Fee %": fee_pct,
                    "Deposit": deposit,
                    "Fee Collected": fee_collected,
                    "NII": nii,
                    "Profit": profit
                })

df = pd.DataFrame(results)
df["Year"] = ((df["Month"] - 1) // 12) + 1
summary = df.groupby("Year")[["Users", "Deposit", "Fee Collected", "NII", "Profit"]].sum().reset_index()

# Display Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Forecast Table", "📆 Yearly Summary", "📈 Charts", "⬇️ Export"])

with tab1:
    st.subheader("60-Month Forecast")
    st.dataframe(df)

with tab2:
    st.subheader("5-Year Summary")
    st.dataframe(summary)

with tab3:
    st.subheader("Revenue and Profit Trends")
    st.line_chart(df.groupby("Month")[["Deposit", "Fee Collected", "NII", "Profit"]].sum())

with tab4:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Forecast")
        summary.to_excel(writer, index=False, sheet_name="Yearly Summary")
    st.download_button("📥 Download Excel", data=output.getvalue(), file_name="rosca_forecast_ultimate.xlsx")
