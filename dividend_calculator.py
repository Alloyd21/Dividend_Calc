import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.markdown("""
    <style>
    /* Add spacing between inputs */
    .stNumberInput, .stSelectbox, .stRadio {
        margin-bottom: 20px;
    }
    /* Add padding at the bottom of the left column */
    .css-1d391kg {
        padding-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Dividend Investment Projection Calculator")

col1, col2 = st.columns([1, 3])

with col1:
    share_price = st.number_input("Share Price ($)", min_value=0.01, value=13.73)
    num_shares = st.number_input("Number of Shares", min_value=0.0, value=145.66)
    holding_period = st.slider("Investment Period (Years)", min_value=1, max_value=30, value=10)
    annual_dividend_yield = st.number_input("Annual Dividend Yield (%)", min_value=0.0, max_value=100.0, value=6.5)
    stock_appreciation = st.number_input("Stock Appreciation Rate (%)", min_value=0.0, max_value=100.0, value=5.0)
    dividend_growth_rate = st.number_input("Estimated Dividend Growth Rate (%)", min_value=0.0, max_value=100.0, value=2.0)
    

    additional_contribution = st.number_input("Annual Contribution ($)", min_value=0, step=1000, value=2000)
    contribution_frequency = st.selectbox("Contribution Frequency", ["Monthly", "Quarterly", "Annually"])
    reinvest_dividends = st.radio("Reinvest Dividends?", ["Yes", "No"]) == "Yes"

contribution_multiplier = {"Monthly": 12, "Quarterly": 4, "Annually": 1}[contribution_frequency]
monthly_contribution = additional_contribution / contribution_multiplier
monthly_stock_appreciation = (1 + stock_appreciation / 100) ** (1 / 12) - 1
monthly_dividend_growth = (1 + dividend_growth_rate / 100) ** (1 / 12) - 1

monthly_dividend_yields = {
    "Baseline": (annual_dividend_yield / 12) / 100,
    "High": ((annual_dividend_yield + 1.5) / 12) / 100,
    "Low": ((annual_dividend_yield - 1.5) / 12) / 100
}

projection_data = {"Baseline": [], "High": [], "Low": []}

for label, initial_yield in monthly_dividend_yields.items():
    total_shares = num_shares
    total_value = start_value = share_price * num_shares
    adj_dividend_yield = initial_yield  
    adj_share_price = share_price

    for month in range(holding_period * 12):
        if month > 0:
            adj_dividend_yield *= (1 + monthly_dividend_growth)
        monthly_dividend = total_value * adj_dividend_yield
        if reinvest_dividends:
            total_shares += monthly_dividend / adj_share_price
        if (month + 1) % (12 / contribution_multiplier) == 0:
            new_shares_from_contribution = monthly_contribution / adj_share_price
            total_shares += new_shares_from_contribution
        adj_share_price *= (1 + monthly_stock_appreciation)
        total_value = total_shares * adj_share_price
        projection_data[label].append(total_value)
date_range = [datetime.today() + timedelta(days=30 * i) for i in range(holding_period * 12)]
df_projection = pd.DataFrame({
    "Date": date_range,
    "Baseline": projection_data["Baseline"],
    "High": projection_data["High"],
    "Low": projection_data["Low"]
}).set_index("Date")

final_principal = start_value
final_contributions = additional_contribution * holding_period
final_dividends = sum(projection_data["Baseline"]) * monthly_dividend_yields["Baseline"]
final_appreciation = df_projection["Baseline"].iloc[-1] - final_principal - final_contributions - final_dividends

total_investment = final_principal + final_contributions + final_dividends + final_appreciation
principal_pct = (final_principal / total_investment) * 100
contributions_pct = (final_contributions / total_investment) * 100
dividends_pct = (final_dividends / total_investment) * 100
appreciation_pct = (final_appreciation / total_investment) * 100


with col2:
    st.subheader(f"Final Projected Total Value (Baseline): ${df_projection['Baseline'].iloc[-1]:,.2f}")

    col3, col4 = st.columns(2)
    col3.markdown(f"<p style='font-size:20px'><strong>Principal:</strong> ${final_principal:,.2f}</p>", unsafe_allow_html=True)
    col3.markdown(f"<p style='font-size:20px'><strong>Contributions:</strong> ${final_contributions:,.2f}</p>", unsafe_allow_html=True)
    col4.markdown(f"<p style='font-size:20px'><strong>Dividends:</strong> ${final_dividends:,.2f}</p>", unsafe_allow_html=True)
    col4.markdown(f"<p style='font-size:20px'><strong>Appreciation:</strong> ${final_appreciation:,.2f}</p>", unsafe_allow_html=True)

    st.line_chart(df_projection, height=500)

    fig = go.Figure(data=[
        go.Bar(
            name="Principal",
            x=[principal_pct],
            y=["Investment Breakdown"],
            orientation='h',
            marker=dict(color='#1f77b4'),
               text=f"Principal: ${final_principal:,.2f} ({principal_pct:.2f}%)", 
            textposition='inside'
        ),
        go.Bar(
            name="Contributions",
            x=[contributions_pct],
            y=["Investment Breakdown"],
            orientation='h',
            marker=dict(color='#ff7f0e'),
            text=f"Contributions: ${final_contributions:,.2f} ({contributions_pct:.2f}%)",
            textposition='inside'
        ),
        go.Bar(
            name="Dividends",
            x=[dividends_pct],
            y=["Investment Breakdown"],
            orientation='h',
            marker=dict(color='#2ca02c'),
            text=f"Dividends: ${final_dividends:,.2f} ({dividends_pct:.2f}%)", 
            textposition='inside'
        ),
        go.Bar(
            name="Appreciation",
            x=[appreciation_pct],
            y=["Investment Breakdown"],
            orientation='h',
            marker=dict(color='#d62728'),
            text=f"Appreciation: ${final_appreciation:,.2f} ({appreciation_pct:.2f}%)", 
            textposition='inside'
        )
    ])

    fig.update_layout(
        barmode='stack',
        showlegend=True,
        height=325
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

df_projection["Total Shares"] = df_projection["Baseline"] 
df = pd.DataFrame({
    "Date": date_range,
    "Share Price": [f"${share_price:,.2f}" for _ in date_range],
    "Total Value": [f"${value:,.2f}" for value in df_projection["Baseline"]],
    "Dividend Income": [f"${value * monthly_dividend_yields['Baseline']:,.2f}" for value in df_projection["Baseline"]],
})

st.dataframe(df.set_index("Date"), use_container_width=True, hide_index=False)
