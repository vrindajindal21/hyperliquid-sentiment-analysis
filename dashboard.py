import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sentiment_trading_analysis import SentimentTradingAnalyzer
from predictive_model import SentimentPredictiveModel

# Page configuration
st.set_page_config(page_title="PrimeTradeAI: Sentiment Dashboard", layout="wide")

st.title("📊 Hyperliquid Sentiment Trading Dashboard")
st.markdown("""
This dashboard explores the relationship between market sentiment (Fear/Greed) and trader performance 
on the Hyperliquid platform.
""")

# Load data using the existing analyzer
@st.cache_resource
def get_analyzer():
    analyzer = SentimentTradingAnalyzer()
    analyzer.load_data()
    analyzer.create_daily_trader_metrics()
    analyzer.merge_datasets()
    analyzer.create_trader_segments()
    return analyzer

@st.cache_resource
def get_predictive_model():
    model = SentimentPredictiveModel()
    model.load_and_prepare_data()
    model.create_profitability_buckets()
    model.prepare_features()
    model.train_binary_profitability_classifier()
    model.train_profitability_classifier()
    model.train_pnl_regressor()
    model.cluster_traders()
    return model

analyzer = get_analyzer()
merged_data = analyzer.merged_data

# Sidebar for controls
st.sidebar.header("📊 Filter Analysis")
sentiment_options = merged_data['classification'].unique()
selected_sentiment = st.sidebar.multiselect("Select Sentiment Regimes", sentiment_options, default=sentiment_options)
filtered_data = merged_data[merged_data['classification'].isin(selected_sentiment)]

# Metric Row
col1, col2, col3, col4 = st.columns(4)
avg_pnl = filtered_data['daily_pnl'].mean()
avg_vol = filtered_data['daily_volume'].mean()
avg_leverage = filtered_data['leverage_proxy'].mean()
avg_winrate = filtered_data['win_rate'].mean()

col1.metric("Average Daily PnL", f"${avg_pnl:,.2f}")
col2.metric("Average Volume", f"${avg_vol:,.2f}")
col3.metric("Avg Leverage Proxy", f"{avg_leverage:,.2f}")
col4.metric("Average Win Rate", f"{avg_winrate:.1%}")

# Main Visuals
st.header("📈 Sentiment Performance Analysis")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("PnL Distribution by Sentiment")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=filtered_data, x='classification', y='daily_pnl', palette="husl")
    plt.xticks(rotation=45)
    st.pyplot(fig)

with chart_col2:
    st.subheader("Win Rate Comparison")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=filtered_data, x='classification', y='win_rate', ci=None, palette="husl")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Segment Analysis
st.header("👥 Trader Segment Performance")
segment_col1, segment_col2 = st.columns(2)

with segment_col1:
    st.subheader("Performance by Leverage Segment")
    lev_perf = filtered_data.groupby(['leverage_segment', 'classification'])['daily_pnl'].mean().unstack()
    st.bar_chart(lev_perf)

with segment_col2:
    st.subheader("Position Bias by Performance Segment")
    bias_perf = filtered_data.groupby(['performance_segment', 'classification'])['buy_ratio'].mean().unstack()
    st.line_chart(bias_perf)

# Machine Learning Predictions (Optional Expansion)
if st.checkbox("Show Machine Learning Trading Signals (Bonus)"):
    st.header("🤖 ML-Driven Trading Signals")
    model = get_predictive_model()
    signals = model.generate_trading_signals()
    
    selected_account = st.selectbox("Select Account ID:", signals['Account'].unique()[:10])
    account_signals = signals[signals['Account'] == selected_account].head(5)
    st.table(account_signals[['date', 'classification', 'predicted_pnl', 'recommendation']])

# Detailed Insights from Final Report
st.header("🧠 Actionable Findings")
st.markdown("""
- **The Fear Alpha**: Fear periods consistently show **higher average PnL** than Greed periods.
- **Leverage Paradox**: Traders utilize **lower leverage** during Greed days than Fear days.
- **Segmentation**: Winners maintain balanced long/short ratios regardless of sentiment volatility.
""")

st.info("Created for: Primetrade.ai Hiring Team | Candidate: VRINDA JINDAL")
