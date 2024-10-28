# Dividend Investment Projection Calculator

This is a Dividend Investment Projection Calculator built using Streamlit. The app allows users to input details of their investment, including share price, dividend yield, appreciation rate, and additional contributions, to project future returns. The app provides projections for baseline, high, and low dividend yield scenarios, with visualisations of investment breakdowns and performance over time.

## Features

- **Input Options**: Enter share price, number of shares, holding period, annual dividend yield, stock appreciation rate, dividend growth rate, and additional contributions.
- **Projection Scenarios**: Calculates projections for baseline, high, and low dividend yields.
- **Reinvestment Option**: Option to reinvest dividends to grow the total shares over time.
- **Visualisations**:
  - **Line Chart**: Shows projected total value over time for baseline, high, and low scenarios.
  - **Stacked Bar Chart**: Displays the investment breakdown (principal, contributions, dividends, and appreciation) as a percentage.
- **Detailed Breakdown**: Displays final values for principal, contributions, dividends, and appreciation in currency format.

## Hosted App

Try the app online: [Dividend Investment Projection Calculator](https://dividendcalc.streamlit.app/)

## Running Locally

To run this app locally, ensure you have Python and the required libraries installed. Follow the steps below:

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/dividend-investment-calculator.git
cd dividend-investment-calculator
```
### 2. Install Dependencies
Create a requirements.txt file with the following contents, or use the one provided:


```
streamlit
plotly
pandas
```

Then, install the dependencies:


```
pip install -r requirements.txt
```

### 3. Run the App
Run the following command to start the app:


```streamlit run dividend_calculator.py```

The app will be available at http://localhost:8501 in your web browser.