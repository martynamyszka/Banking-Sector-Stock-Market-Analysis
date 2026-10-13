import pandas as pd
import yfinance as yf
import numpy as np
import datetime as dt

# 1. PARAMETERS
tickers = ['HSBC', 'JPM', 'BARC.L']
end_date = dt.datetime.today()
start_date = end_date - dt.timedelta(days=5 * 365)

all_dfs = []

# 2. LOOP THROUGH EACH TICKER (Why? I use a loop to process each ticker individually to avoid MultiIndex alignment issues and calendar mismatches between different
# stock exchanges (e.g., US vs. UK). This ensures calculations like rolling averages are strictly accurate before merging the data
for ticker in tickers:

    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)

    df = df[['Close']].copy()
    df = df.reset_index()

    # Stripping timezone information to ensure perfect date alignment between US and UK exchanges.
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)

    df.rename(columns={'Close': 'Price'}, inplace=True)
    df['Ticker'] = ticker

# 3. CALCULATE METRICS
    df['Prev_Price'] = df['Price'].shift(1)
    df['Log_Return'] = np.log(df['Price'] / df['Prev_Price'])

    df['MA_30_Days'] = df['Price'].rolling(window=30).mean()
    df['MA_200_Days'] = df['Price'].rolling(window=200).mean()

    df['Volatility_30D'] = df['Log_Return'].rolling(window=30).std() * np.sqrt(252)

# 4. CLEAN DATA
    df = df.dropna().reset_index(drop=True)

# 5. CUMULATIVE RETURN
    df['Cumulative_Return'] = np.exp(df['Log_Return'].cumsum()) - 1

    df = df.drop(columns=['Prev_Price'])

    all_dfs.append(df)

# 6. GLUE EVERYTHING TOGETHER
final_df = pd.concat(all_dfs, ignore_index=True)

# 7. BUSINESS INSIGHTS
print("QUICK BUSINESS INSIGHTS")
summary = final_df.groupby('Ticker').agg(
    Total_Return=('Cumulative_Return', 'last'),
    Avg_Volatility=('Volatility_30D', 'mean')
)

for ticker in summary.index:
    tot_ret = summary.loc[ticker, 'Total_Return'] * 100
    avg_vol = summary.loc[ticker, 'Avg_Volatility'] * 100
    print(f"{ticker} -> Total Return: {tot_ret:5.2f}% | Avg Risk (Volatility): {avg_vol:5.2f}%")

best_return_ticker = summary['Total_Return'].idxmax()
most_risky_ticker = summary['Avg_Volatility'].idxmax()

print("AUTOMATED CONCLUSIONS")
print(f"HIGHEST RETURN: {best_return_ticker} (Yielding {summary.loc[best_return_ticker, 'Total_Return'] * 100:.2f}%)")
print(f"HIGHEST RISK:   {most_risky_ticker} (Volatility of {summary.loc[most_risky_ticker, 'Avg_Volatility'] * 100:.2f}%)")

print("CORRELATION MATRIX (RISK DIVERSIFICATION)")
returns_wide = final_df.pivot(index='Date', columns='Ticker', values='Log_Return')
correlation_matrix = returns_wide.corr()
print(correlation_matrix.round(2))

# 8. EXPORT TO CSV
stocks_analysis = 'banking_stocks_analysis.csv'
final_df.to_csv(stocks_analysis, index=False)
print(f"Data successfully cleaned and exported to {stocks_analysis}")