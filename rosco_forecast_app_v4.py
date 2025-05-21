
import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="ROSCA Forecast App v4", layout="wide")

# Sidebar Inputs - Editable Configuration
st.sidebar.title("Input Configuration")

initial_tam = st.sidebar.number_input("Initial TAM", value=200000)
rest_period = st.sidebar.number_input("Rest Period (months)", min_value=0, max_value=12, value=1)
kibor = st.sidebar.slider("KIBOR (%)", 0.0, 25.0, 11.0, step=0.1)
spread = st.sidebar.slider("Spread (%)", 0.0, 20.0, 5.0, step=0.1)
default_rate = st.sidebar.slider("Default Rate (%)", 0.0, 10.0, 1.0, step=0.1)
fee_upfront = st.sidebar.selectbox("Fee Collected Upfront?", ["Yes", "No"]) == "Yes"

st.sidebar.markdown("### Yearly Monthly Growth Rates (%)")
growth_rates = [
    st.sidebar.slider(f"Year {i+1}", 0.0, 10.0, default, step=0.1)
    for i, default in enumerate([2.0, 1.8, 1.5, 1.2, 1.0])
]

st.sidebar.markdown("### Participation Cap Per Year by Duration")
participation_caps = {
    3: st.sidebar.number_input("3M", min_value=1, max_value=12, value=3),
    4: st.sidebar.number_input("4M", min_value=1, max_value=12, value=2),
    5: st.sidebar.number_input("5M", min_value=1, max_value=12, value=1),
    6: st.sidebar.number_input("6M", min_value=1, max_value=12, value=1),
    8: st.sidebar.number_input("8M", min_value=1, max_value=12, value=1),
    10: st.sidebar.number_input("10M", min_value=1, max_value=12, value=1)
}

st.sidebar.markdown("### Committee Duration Allocation (%)")
durations = [3, 4, 5, 6, 8, 10]
duration_alloc = {d: st.sidebar.slider(f"{d}M", 0, 100, default) for d, default in zip(durations, [30, 25, 15, 10, 10, 10])}

st.sidebar.markdown("### Slot Blocking and Fee Matrix (Use 99 to block)")
slot_fee = {}
for d in durations:
    slot_fee[d] = {}
    for s in range(1, d + 1):
        slot_fee[d][s] = st.sidebar.number_input(f"{d}M - Slot {s} Fee %", min_value=0, max_value=100, value=(11 - s) if s <= 10 else 0)

# Static Values
slabs = [1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000]
months = 60
users_db = {}

# Forecast Logic
results = []
for m in range(1, months + 1):
    year_idx = (m - 1) // 12
    monthly_growth = growth_rates[year_idx] / 100
    tam = initial_tam * ((1 + monthly_growth) ** ((m - 1) % 12))

    for d in durations:
        duration_users = tam * (duration_alloc[d] / 100)
        users_per_slab = duration_users / len(slabs)

        for slab in slabs:
            for slot in range(1, d + 1):
                fee_pct = slot_fee[d].get(slot, 0)
                if fee_pct == 99:
                    users = 0
                    deposit = 0
                    fee_collected = 0
                    nii = 0
                    profit = 0
                else:
                    users = users_per_slab
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

# UI Tabs
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
    st.download_button("📥 Download Excel", data=output.getvalue(), file_name="rosca_forecast_v4.xlsx")
