import yfinance as yf
import pandas as pd
from nsetools import Nse
import streamlit as st
import plotly.graph_objects as go


def plot_ohlc(df):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"]))
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Close'],
            line=dict(color='red', width=2),
            name='Line Chart'
        )
    )
    return fig



nse = Nse()
stock_codes_nse = list(nse.get_stock_codes(cached=False))

option = st.selectbox("Select stock (NSE)", stock_codes_nse)
if option == "SYMBOL":
    pass
else:
    ticker = yf.Ticker(option + ".NS")
    try:
        st.header("Info")
        st.write(ticker.info)
    except:
        pass

    try:
        st.header("OHLC + Line chart")
        df = ticker.history(period = "max")
        st.plotly_chart(plot_ohlc(df))
    except:
        pass

    try:
        st.header("History metadata")
        st.write(ticker.history_metadata)
    except:
        pass

    # show actions (dividends, splits, capital gains)
    try:
        st.header("Corporate Actions")
        st.write(ticker.actions)
    except:
        pass

    # show dividends
    try:
        st.header("Dividends")
        st.write(ticker.dividends)
    except:
        pass

    # show splits
    try:
        st.header("Splits")
        st.write(ticker.splits)
    except:
        pass

    # show capital gains (for mutual funds & etfs)
    try:
        st.header("Capital gains")
        st.write(ticker.capital_gains)
    except:
        pass

    # show share count
    try:
        st.header("Shares")
        st.write(ticker.shares)
    except:
        pass

    # show financials:
    # - income statement
    try:
        st.header("Annual Income statement")
        st.write(ticker.income_stmt)
    except:
        pass

    try:
        st.header("Quarterly income statement")
        st.write(ticker.quarterly_income_stmt)
    except:
        pass

    # - balance sheet
    try:
        st.header("Annual Balance sheet")
        st.write(ticker.balance_sheet)
    except:
        pass

    try:
        st.header("Quarterly Balance sheet")
        st.write(ticker.quarterly_balance_sheet)
    except:
        pass

    # - cash flow statement
    try:
        st.header("Cash flow statement")
        st.write(ticker.cashflow)
    except:
        pass

    try:
        st.header("Quarterly Cash flow statement")
        st.write(ticker.quarterly_cashflow)
    except:
        pass
    # see `Ticker.get_income_stmt()` for more options

    # show major holders
    try:
        st.header("Major holders")
        st.write(ticker.major_holders)
    except:
        pass

    # show institutional holders
    try:
        st.header("Institutional Holders")
        st.write(ticker.institutional_holders)
    except:
        pass

    # show mutualfund holders
    try:
        st.header("Mutual fund holders")
        st.write(ticker.mutualfund_holders)
    except:
        pass


    # show earnings
    try:
        st.header("Annual Earnings Report")
        st.write(ticker.earnings)
    except:
        pass

    try:
        st.header("Quarterly earnings report")
        st.write(ticker.quarterly_earnings)
    except:
        pass

    # show sustainability
    try:
        st.header("Sustainability review (yfinance)")
        st.write(ticker.sustainability)
    except:
        pass

    # show analysts recommendations
    try:
        st.header("Analyst recommendations")
        st.write(ticker.recommendations)
    except:
        pass

    try:
        st.header("Analyst recommendations summary")
        st.write(ticker.recommendations_summary)
    except:
        pass

    # show analysts other work
    try:
        st.header("Analyst price target")
        st.write(ticker.analyst_price_target)
    except:
        pass

    try:
        st.header("Analyst revenue forecasts")
        st.write(ticker.revenue_forecasts)
    except:
        pass

    try:
        st.header("Analyst earnings forecasts")
        st.write(ticker.earnings_forecasts)
    except:
        pass

    try:
        st.header("Earnings trend by Analysts")
        st.write(ticker.earnings_trend)
    except:
        pass

    # show next event (earnings, etc)
    try:
        st.header("Next events")
        st.write(ticker.calendar)
    except:
        pass

    # Show future and historic earnings dates, returns at most next 4 quarters and last 8 quarters by default. 
    # Note: If more are needed use ticker.get_earnings_dates(limit=XX) with increased limit argument.
    try:
        st.header("Earnigns dates")
        st.write(ticker.earnings_dates)
    except:
        pass

    # show ISIN code - *experimental*
    # ISIN = International Securities Identification Number
    try:
        st.header("ISIN code")
        st.write(ticker.isin)
    except:
        pass

    # show options expirations
    try:
        st.header("Options Expirations")
        st.write(ticker.options)
    except:
        pass

    # show news
    try:
        st.header("News")
        st.write(ticker.news)
    except:
        pass
