
# ROSCA Forecast App - v6
# Fully integrated with lifecycle tracking, growth, slot blocking, participation caps, rejoining logic, export, and chart scaling

import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="ROSCA Forecast App", layout="wide")
st.title("ROSCA Forecast App - v6")

# Global Parameters
st.sidebar.header("Configuration")
total_market = st.sidebar.number_input("Total Market", value=20000000)
tam_percent = st.sidebar.slider("TAM %", 0, 100, 10)
starting_user_percent = st.sidebar.slider("Starting User % of TAM", 0, 100, 10)
monthly_growth = st.sidebar.slider("Monthly Growth %", 0.0, 10.0, 2.0)

initial_tam = total_market * (tam_percent / 100)
user_base = initial_tam * (starting_user_percent / 100)

kibor = st.sidebar.slider("KIBOR (%)", 0.0, 25.0, 11.0)
spread = st.sidebar.slider("Spread (%)", 0.0, 20.0, 5.0)
default_rate = st.sidebar.slider("Default Rate (%)", 0.0, 10.0, 1.0)
rest_period = st.sidebar.slider("Rest Period (months)", 0, 12, 1)
fee_upfront = st.sidebar.radio("Fee Collected Upfront?", ["Yes", "No"]) == "Yes"

# Participation Caps
st.sidebar.markdown("### Participation Cap Per Year")
participation_caps = {d: st.sidebar.number_input(f"{d}M", 1, 12, default) for d, default in zip([3, 4, 5, 6, 8, 10], [3, 2, 1, 1, 1, 1])}
durations = [3, 4, 5, 6, 8, 10]
slabs = [1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000]

# Duration Allocation
st.sidebar.markdown("### Committee Duration Allocation (%)")
duration_alloc = {d: st.sidebar.slider(f"{d}M", 0, 100, v) for d, v in zip(durations, [30, 25, 15, 10, 10, 10])}
assert sum(duration_alloc.values()) == 100, "Allocation must sum to 100%"

# Slot Fee Matrix
st.sidebar.markdown("### Slot Fee Structure (Use 99 to block)")
slot_fees = {d: {s: st.sidebar.number_input(f"{d}M - Slot {s} Fee %", 0, 100, max(0, 11 - s)) for s in range(1, d + 1)} for d in durations}

# Forecast Engine
months = 60
results, user_pool, rejoining_track = [], user_base, [0]*months

for m in range(1, months + 1):
    new_users = user_pool if m == 1 else user_pool * (1 + monthly_growth / 100)
    rejoining = rejoining_track[m-1] if m-1 < len(rejoining_track) else 0
    total_users = new_users + rejoining

    for d in durations:
        if duration_alloc[d] == 0:
            continue

        users_by_duration = total_users * (duration_alloc[d] / 100)
        per_slab_users = users_by_duration / len(slabs)

        if (m + d + rest_period) < months:
            rejoining_track[m + d + rest_period] += users_by_duration

        for slab in slabs:
            for slot in range(1, d + 1):
                fee = slot_fees[d][slot]
                if fee == 99:
                    deposit, fee_collected, nii, profit, users = 0, 0, 0, 0, 0
                else:
                    users = per_slab_users
                    deposit = users * slab * d
                    fee_collected = deposit * (fee / 100) if fee_upfront else 0
                    nii = deposit * ((kibor + spread) / 100 / 12)
                    profit = fee_collected + nii - (deposit * default_rate / 100)

                results.append({
                    "Month": m, "Year": (m - 1) // 12 + 1, "Duration": d, "Slab": slab, "Slot": slot,
                    "Users": users, "Fee %": fee, "Deposit": deposit,
                    "Fee Collected": fee_collected, "NII": nii, "Profit": profit,
                    "Rejoining Customers": rejoining if slot == 1 and slab == slabs[0] else 0
                })

    user_pool = total_users

# DataFrame and Summary
df = pd.DataFrame(results)
summary = df.groupby("Year")[["Users", "Deposit", "Fee Collected", "NII", "Profit"]].sum().reset_index()

# UI Display
tab1, tab2, tab3, tab4 = st.tabs(["Forecast", "Summary", "Charts", "Export"])
with tab1: st.dataframe(df)
with tab2: st.dataframe(summary)
with tab3: st.line_chart(df.groupby("Month")[["Fee Collected", "NII", "Profit"]].sum())
with tab4:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Forecast", index=False)
        summary.to_excel(writer, sheet_name="Summary", index=False)
    st.download_button("Download Excel", buffer.getvalue(), "rosca_forecast_v6.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
