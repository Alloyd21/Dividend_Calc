import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import altair as alt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class DividendCalculator:
    def __init__(self):
        self.setup_page_config()
        self.setup_styles()
        
    def setup_page_config(self):
        st.set_page_config(layout="wide")
        
    def setup_styles(self):
        st.markdown("""
            <style>
            .stNumberInput, .stSelectbox, .stRadio { margin-bottom: 20px; }
            .css-1d391kg { padding-bottom: 30px; }
            </style>
        """, unsafe_allow_html=True)
        
    def get_user_inputs(self) -> Tuple[Dict, float, int]:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            share_price = st.number_input("Share Price ($)", min_value=0.01, value=13.73)
            
            # Initialize session state if not already done
            if 'initialized' not in st.session_state:
                st.session_state.num_shares = 145.66
                st.session_state.principal_value = share_price * 145.66
                st.session_state.last_modified = 'shares'
                st.session_state.previous_share_price = share_price
                st.session_state.initialized = True
            
            # Create columns for share count and principal value
            share_col, principal_col = st.columns(2)
            
            # Update function for number of shares
            def update_principal():
                if st.session_state.num_shares != st.session_state.principal_value / share_price:
                    st.session_state.principal_value = share_price * st.session_state.num_shares
                    st.session_state.last_modified = 'shares'
            
            # Update function for principal value
            def update_shares():
                if st.session_state.principal_value != st.session_state.num_shares * share_price:
                    st.session_state.num_shares = st.session_state.principal_value / share_price
                    st.session_state.last_modified = 'principal'
            
            # Create the input fields without default values
            with share_col:
                num_shares = st.number_input(
                    "Number of Shares",
                    min_value=0.0,
                    key='num_shares',
                    on_change=update_principal
                )
            
            with principal_col:
                principal_value = st.number_input(
                    "Principal Value ($)",
                    min_value=0.0,
                    key='principal_value',
                    on_change=update_shares
                )
            
            # Update values based on share price changes
            if st.session_state.previous_share_price != share_price:
                if st.session_state.last_modified == 'shares':
                    st.session_state.principal_value = share_price * st.session_state.num_shares
                else:
                    st.session_state.num_shares = st.session_state.principal_value / share_price
                st.session_state.previous_share_price = share_price
            
            # Add dividend payment frequency radio buttons
            dividend_frequency = st.radio(
                "Dividend Payment Frequency",
                ["Monthly", "Quarterly", "Annually"],
                index=1  # Default to Quarterly
            )
            
            # Rest of the inputs
            inputs = {
                'share_price': share_price,
                'num_shares': st.session_state.num_shares,
                'holding_period': st.slider("Investment Period (Years)", min_value=1, max_value=30, value=15),
                'annual_dividend_yield': st.number_input("Annual Dividend Yield (%)", min_value=0.0, max_value=100.0, value=6.5),
                'stock_appreciation': st.number_input("Stock Appreciation Rate (%)", min_value=0.0, max_value=100.0, value=5.0),
                'dividend_growth_rate': st.number_input("Estimated Dividend Growth Rate (%)", min_value=0.0, max_value=100.0, value=2.0),
                'additional_contribution': st.number_input("Annual Contribution ($)", min_value=0, step=1000, value=2000),
                'contribution_frequency': st.selectbox("Contribution Frequency", ["Monthly", "Quarterly", "Annually"]),
                'dividend_frequency': dividend_frequency,
                'reinvest_dividends': st.radio("Reinvest Dividends?", ["Yes", "No"]) == "Yes"
            }
            
        return inputs, col2, inputs['holding_period']

    
    def calculate_monthly_rates(self, inputs: Dict) -> Tuple[float, float, float, Dict[str, float]]:
        contribution_multiplier = {"Monthly": 12, "Quarterly": 4, "Annually": 1}[inputs['contribution_frequency']]
        monthly_contribution = inputs['additional_contribution'] / contribution_multiplier
        monthly_stock_appreciation = (1 + inputs['stock_appreciation'] / 100) ** (1/12) - 1
        monthly_dividend_growth = (1 + inputs['dividend_growth_rate'] / 100) ** (1/12) - 1
        
        # Adjust dividend yields based on payment frequency
        dividend_payments_per_year = {
            "Monthly": 12,
            "Quarterly": 4,
            "Annually": 1
        }[inputs['dividend_frequency']]
        
        base_yield = inputs['annual_dividend_yield'] / dividend_payments_per_year / 100
        
        monthly_dividend_yields = {
            "Baseline": base_yield,
            "High": base_yield * 1.15,  # 15% higher
            "Low": base_yield * 0.85    # 15% lower
        }
        
        return monthly_contribution, monthly_stock_appreciation, monthly_dividend_growth, monthly_dividend_yields, dividend_payments_per_year

    
    def project_investment(self, inputs: Dict, monthly_rates: Tuple) -> Tuple[Dict[str, List[float]], float, float, float, float]:
        monthly_contribution, monthly_stock_appreciation, monthly_dividend_growth, monthly_dividend_yields, dividend_payments_per_year = monthly_rates
        projection_data = {"Baseline": [], "High": [], "Low": []}
        months_between_payments = 12 // dividend_payments_per_year
        
        for label, initial_yield in monthly_dividend_yields.items():
            total_shares = inputs['num_shares']
            total_value = start_value = inputs['share_price'] * inputs['num_shares']
            adj_dividend_yield = initial_yield
            adj_share_price = inputs['share_price']
            
            for month in range(inputs['holding_period'] * 12):
                if month > 0:
                    adj_dividend_yield *= (1 + monthly_dividend_growth)
                
                # Only pay dividends on the correct months based on frequency
                if month % months_between_payments == 0:
                    monthly_dividend = total_value * adj_dividend_yield
                    if inputs['reinvest_dividends']:
                        total_shares += monthly_dividend / adj_share_price
                
                contribution_multiplier = {"Monthly": 12, "Quarterly": 4, "Annually": 1}[inputs['contribution_frequency']]
                if (month + 1) % (12 / contribution_multiplier) == 0:
                    total_shares += monthly_contribution / adj_share_price
                
                adj_share_price *= (1 + monthly_stock_appreciation)
                total_value = total_shares * adj_share_price
                projection_data[label].append(total_value)
        
        final_principal = start_value
        final_contributions = inputs['additional_contribution'] * inputs['holding_period']
        
        # Adjust dividend calculation based on payment frequency
        dividend_months = [i for i in range(len(projection_data["Baseline"])) if i % months_between_payments == 0]
        final_dividends = sum(projection_data["Baseline"][i] * monthly_dividend_yields["Baseline"] for i in dividend_months)
        
        final_appreciation = projection_data["Baseline"][-1] - final_principal - final_contributions - final_dividends
        
        return projection_data, final_principal, final_contributions, final_dividends, final_appreciation

    
    def create_projection_dataframe(self, projection_data: Dict[str, List[float]], holding_period: int, 
                                  initial_share_price: float, monthly_stock_appreciation: float) -> pd.DataFrame:
        date_range = [datetime.today() + timedelta(days=30 * i) for i in range(holding_period * 12)]
        
        # Calculate share price over time
        share_prices = []
        current_share_price = initial_share_price
        for _ in range(holding_period * 12):
            share_prices.append(current_share_price)
            current_share_price *= (1 + monthly_stock_appreciation)
        
        return pd.DataFrame({
            "Date": date_range,
            "Share Price": share_prices,
            "Baseline": projection_data["Baseline"],
            "High": projection_data["High"],
            "Low": projection_data["Low"]
        }).set_index("Date")
    
    def create_altair_chart(self, df_projection: pd.DataFrame) -> alt.Chart:
        df_melted = df_projection.reset_index().melt(
            id_vars=['Date'],
            value_vars=['Baseline', 'High', 'Low'],
            var_name='Scenario',
            value_name='Value'
        )
        
        hover = alt.selection_point(
            fields=['Date'],
            nearest=True,
            on='mouseover',
            empty='none',
            clear='mouseout'
        )
        
        base = alt.Chart(df_melted).encode(
            x=alt.X('Date:T', axis=alt.Axis(title='Date', format='%Y-%m')),
            y=alt.Y('Value:Q', 
                   axis=alt.Axis(title='Portfolio Value ($)', format=',.0f'),
                   scale=alt.Scale(zero=False)),
            color=alt.Color('Scenario:N', 
                          scale=alt.Scale(
                              domain=['Baseline', 'High', 'Low'],
                              range=['#4361EE', '#7209B7', '#F72585']
                          ))
        )
        
        lines = base.mark_line().encode(
            opacity=alt.condition(hover, alt.value(1), alt.value(0.5))
        )
        
        points = base.mark_circle(size=100).encode(
            opacity=alt.condition(hover, alt.value(1), alt.value(0))
        ).add_params(hover)
        
        tooltips = alt.layer(
            lines,
            points,
            base.mark_rule(color='gray').encode(
                x='Date:T'
            ).transform_filter(hover),
            base.mark_text(align='left', dx=5, dy=-5).encode(
                text=alt.Text('Value:Q', format='$,.0f'),
                opacity=alt.condition(hover, alt.value(1), alt.value(0))
            )
        )
        
        chart = tooltips.properties(
            width='container',
            height=500
        ).configure_axis(
            grid=True,
            gridOpacity=0.2
        ).configure_view(
            strokeWidth=0
        )
        
        return chart
    
    def calculate_yearly_dividends(self, projection_data: List[float], monthly_dividend_yields: Dict[str, float], 
                                 dividend_frequency: str) -> List[float]:
        """Calculate yearly dividend income from monthly projections."""
        months_between_payments = {
            "Monthly": 1,
            "Quarterly": 3,
            "Annually": 12
        }[dividend_frequency]
        
        yearly_dividends = []
        for year in range(len(projection_data) // 12):
            year_start = year * 12
            year_end = (year + 1) * 12
            year_values = projection_data[year_start:year_end]
            
            # Only count dividend payments on the correct months
            dividend_months = [i % 12 for i in range(year_start, year_end) if i % months_between_payments == 0]
            year_total = sum(year_values[i] * monthly_dividend_yields['Baseline'] for i in dividend_months)
            yearly_dividends.append(year_total)
        
        return yearly_dividends

    def create_dividend_income_chart(self, projection_data: Dict[str, List[float]], monthly_dividend_yields: Dict[str, float],
                                   dividend_frequency: str) -> alt.Chart:
        """Create an Altair bar chart showing yearly dividend income."""
        yearly_dividends = self.calculate_yearly_dividends(
            projection_data["Baseline"], 
            monthly_dividend_yields,
            dividend_frequency
        )
        
        df_dividends = pd.DataFrame({
            'YearNum': range(1, len(yearly_dividends) + 1),
            'Year': [f"Year {i}" for i in range(1, len(yearly_dividends) + 1)],
            'Dividend': yearly_dividends
        })
        
        hover = alt.selection_point(
            fields=['Year'],
            nearest=True,
            on='mouseover',
            empty='none',
            clear='mouseout'
        )
        
        base = alt.Chart(df_dividends).encode(
            x=alt.X('Year:N', 
                    axis=alt.Axis(
                        labelAngle=-45,
                        title=None
                    ),
                    sort=df_dividends['Year'].tolist()
            ),
            y=alt.Y('Dividend:Q',
                    axis=alt.Axis(
                        title='Dividend Income ($)',
                        format='$,.0f',
                        grid=True,
                        gridOpacity=0.2
                    ))
        )
        
        bars = base.mark_bar(color='#7209B7').encode(
            opacity=alt.condition(hover, alt.value(1), alt.value(0.8))
        )
        
        text = base.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,
            fontSize=12
        ).encode(
            text=alt.Text('Dividend:Q', format='$,.0f'),
            opacity=alt.condition(hover, alt.value(1), alt.value(0))
        )
        
        chart = alt.layer(bars, text).add_params(hover).properties(
            title=alt.TitleParams(
                text='Yearly Dividend Income',
                anchor='middle',
                fontSize=16,
                dy=-10
            ),
            width='container',
            height=450
        ).configure_axis(
            grid=True,
            gridOpacity=0.2
        ).configure_view(
            strokeWidth=0
        )
        
        return chart
    
    def create_portfolio_composition_chart(self, values: Tuple[float, float, float, float]) -> go.Figure:
        final_principal, final_contributions, final_dividends, final_appreciation = values
        total_investment = sum(values)
        
        percentages = [v/total_investment * 100 for v in values]
        colors = ['#4361EE', '#3A0CA3', '#7209B7', '#F72585']
        names = ['Principal', 'Contributions', 'Dividends', 'Appreciation']
        
        fig = go.Figure()
        
        for i, (name, pct, value, color) in enumerate(zip(names, percentages, values, colors)):
            fig.add_trace(go.Bar(
                name=name,
                x=[pct],
                y=["Portfolio Composition"],
                orientation='h',
                marker=dict(color=color),
                text=f"{name}: ${value:,.0f} ({pct:.1f}%)",
                textposition='inside',
                textfont=dict(size=14, color='white'),
                hoverinfo='skip'
            ))
            
        fig.update_layout(
            barmode='stack',
            showlegend=True,
            height=200,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                bgcolor='rgba(0,0,0,0)'
            ),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig
    
    def display_results(self, col2, df_projection: pd.DataFrame, values: Tuple[float, float, float, float],
                       monthly_dividend_yields: Dict[str, float], share_price: float, dividend_frequency: str):
        final_principal, final_contributions, final_dividends, final_appreciation = values
        total_return = final_dividends + final_appreciation
        
        with col2:
            st.subheader(f"Capital Growth: ${total_return:,.2f}")
            
            col3, col4 = st.columns(2)
            col3.markdown(f"<p style='font-size:20px'><strong>Principal:</strong> ${final_principal:,.2f}</p>", unsafe_allow_html=True)
            col3.markdown(f"<p style='font-size:20px'><strong>Contributions:</strong> ${final_contributions:,.2f}</p>", unsafe_allow_html=True)
            col4.markdown(f"<p style='font-size:20px'><strong>Dividends:</strong> ${final_dividends:,.2f}</p>", unsafe_allow_html=True)
            col4.markdown(f"<p style='font-size:20px'><strong>Appreciation:</strong> ${final_appreciation:,.2f}</p>", unsafe_allow_html=True)
            
            chart = self.create_altair_chart(df_projection)
            st.altair_chart(chart, use_container_width=True)
            
            st.subheader(f"Final Projected Total Value: ${df_projection['Baseline'].iloc[-1]:,.2f}")
            
            # Portfolio composition chart
            fig_portfolio = self.create_portfolio_composition_chart(values)
            st.plotly_chart(fig_portfolio, use_container_width=True, config={'displayModeBar': False})
            
            # Yearly dividend income chart
            dividend_chart = self.create_dividend_income_chart(
                {"Baseline": df_projection["Baseline"].tolist()}, 
                monthly_dividend_yields,
                dividend_frequency
            )
            st.altair_chart(dividend_chart, use_container_width=True)
            
            # Updated to match the new method signature
            self.display_detailed_table(df_projection, monthly_dividend_yields, dividend_frequency)
    
    
    
    def display_detailed_table(self, df_projection: pd.DataFrame, monthly_dividend_yields: Dict[str, float], 
                             dividend_frequency: str):
        date_range = df_projection.index
        months_between_payments = {"Monthly": 1, "Quarterly": 3, "Annually": 12}[dividend_frequency]
        
        # Calculate dividend income based on frequency
        monthly_dividends = []
        for i, value in enumerate(df_projection["Baseline"]):
            if i % months_between_payments == 0:
                monthly_dividends.append(value * monthly_dividend_yields['Baseline'])
            else:
                monthly_dividends.append(0)
        
        df = pd.DataFrame({
            "Date": date_range,
            "Share Price": [f"${price:,.2f}" for price in df_projection["Share Price"]],
            "Total Value": [f"${value:,.2f}" for value in df_projection["Baseline"]],
            "Dividend Income": [f"${value:,.2f}" for value in monthly_dividends],
        })
        st.dataframe(df.set_index("Date"), use_container_width=True, hide_index=False)
    
    def run(self):
        st.title("Dividend Investment Projection")
        
        # Get user inputs
        inputs, col2, holding_period = self.get_user_inputs()
        
        # Calculate monthly rates
        monthly_rates = self.calculate_monthly_rates(inputs)
        
        # Project investment
        projection_data, *values = self.project_investment(inputs, monthly_rates)
        
        # Create projection dataframe with share price progression
        df_projection = self.create_projection_dataframe(
            projection_data, 
            holding_period,
            inputs['share_price'],
            monthly_rates[1]  # monthly_stock_appreciation
        )
        
        # Display results
        self.display_results(
            col2, 
            df_projection, 
            values, 
            monthly_rates[3], 
            inputs['share_price'],
            inputs['dividend_frequency']
        )

if __name__ == "__main__":
    calculator = DividendCalculator()
    calculator.run()