
import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="ROSCA Forecast App v3", layout="wide")

# Sidebar Input_Config
st.sidebar.header("Global Configuration")
initial_tam = st.sidebar.number_input("Initial TAM", value=200000)
kibor = st.sidebar.slider("KIBOR (%)", 0.0, 25.0, 11.0, step=0.1)
spread = st.sidebar.slider("Spread (%)", 0.0, 20.0, 5.0, step=0.1)
default_rate = st.sidebar.slider("Default Rate (%)", 0.0, 10.0, 1.0, step=0.1)
rest_period = st.sidebar.number_input("Rest Period (months)", min_value=0, max_value=12, value=1)
fee_upfront = st.sidebar.selectbox("Fee Collected Upfront?", ["Yes", "No"]) == "Yes"

# Year-wise growth rate
st.sidebar.markdown("### Yearly Monthly Growth Rates (%)")
growth_rates = [
    st.sidebar.slider(f"Year {i+1}", 0.0, 10.0, default, step=0.1)
    for i, default in enumerate([2.0, 1.8, 1.5, 1.2, 1.0])
]

# Duration allocation (% of TAM)
st.sidebar.markdown("### Committee Duration Allocation (%)")
durations = [3, 4, 5, 6, 8, 10]
duration_allocation = {d: st.sidebar.slider(f"{d}M", 0, 100, v, step=5) for d, v in zip(durations, [30, 25, 15, 10, 10, 10])}

# Slot Fee % (common)
st.sidebar.markdown("### Slot Fee Structure")
slot_fees = {i: st.sidebar.number_input(f"Slot {i} Fee %", min_value=0, max_value=100, value=11 - i) for i in range(1, 11)}

# Base parameters
slabs = [1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000]
participation_caps = {3: 3, 4: 2, 5: 1, 6: 1, 8: 1, 10: 1}
months = 60

# Initialize forecast list
forecast = []

# Compute monthly growth factor
monthly_growth_factors = []
for i in range(months):
    year_idx = min(i // 12, 4)
    rate = growth_rates[year_idx] / 100
    monthly_growth_factors.append((1 + rate) ** (i % 12))

# Forecast model
for month in range(1, months + 1):
    month_idx = month - 1
    tam = initial_tam * monthly_growth_factors[month_idx]
    for d in durations:
        users_by_duration = tam * (duration_allocation[d] / 100)
        per_slab = users_by_duration / len(slabs)
        for slab in slabs:
            for slot in range(1, d + 1):
                fee_pct = slot_fees[slot] / 100
                deposit = per_slab * slab * d
                fee_collected = deposit * fee_pct if fee_upfront else 0
                nii = deposit * ((kibor + spread) / 100 / 12)
                profit = fee_collected + nii - (deposit * (default_rate / 100))
                forecast.append({
                    "Month": month,
                    "Duration": d,
                    "Slab": slab,
                    "Slot": slot,
                    "Users": per_slab,
                    "Deposit": deposit,
                    "Fee %": fee_pct,
                    "Fee Collected": fee_collected,
                    "NII": nii,
                    "Profit": profit
                })

df = pd.DataFrame(forecast)
df["Year"] = ((df["Month"] - 1) // 12) + 1

# Yearly summary
summary = df.groupby("Year")[["Users", "Deposit", "Fee Collected", "NII", "Profit"]].sum().reset_index()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Forecast", "📆 Yearly Summary", "📈 Charts", "⬇️ Export"])

with tab1:
    st.subheader("60-Month Forecast")
    st.dataframe(df)

with tab2:
    st.subheader("5-Year Summary")
    st.dataframe(summary)

with tab3:
    st.subheader("Trends")
    st.line_chart(df.groupby("Month")[["Deposit", "Fee Collected", "NII", "Profit"]].sum())

with tab4:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Forecast")
        summary.to_excel(writer, index=False, sheet_name="Yearly Summary")
    st.download_button("📥 Download Excel", data=output.getvalue(), file_name="rosca_forecast_v3.xlsx")
