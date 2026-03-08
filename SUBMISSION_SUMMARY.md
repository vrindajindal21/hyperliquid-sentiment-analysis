# PrimeTradeAI: Sentiment Trading Analysis - Project Summary

## 📑 Overview
This project analyzes the relationship between **Bitcoin Fear/Greed Sentiment** and **Hyperliquid Trading Behavior**. Using a dataset of over **211,000 trades** across 32 accounts (2023-2025), we identify how market psychology impacts risk-taking and profitability.

## 🛠️ Methodology
1.  **Data Preparation**: Aggregated raw trade-level data into daily metrics per account (PnL, Volume, Win Rate, Leverage).
2.  **Sentiment Mapping**: Merged trader metrics with the Bitcoin Fear/Greed Index on synchronized timestamps.
3.  **Statistical Analysis**: Performed Fear vs. Greed performance comparisons using T-tests and boxplot distributions to identify behavioral anomalies.
4.  **Trader Segmentation**: Clustered accounts into 4 archetypes (Successful, High Risk, Active, Conservative) to analyze how different segments react to sentiment.
5.  **Predictive Modeling**: Developed Random Forest models to predict next-day profitability (ROC-AUC: 0.956) and generate trading signals.

## 🧠 Key Insights
*   **The Fear Alpha**: Fear periods outperform Greed by **25.1%** in average daily PnL ($5,185 vs $4,144), despite lower overall participation.
*   **Leverage Paradox**: Traders utilize **39% LESS leverage** during Greed periods, suggesting a cautious bias or defensive positioning during market peaks.
*   **Volume & Participation**: Extreme Fear drives significantly higher trading volume (2.1x) compared to Greed, fueled by emotional liquidation and dip-buying behavior.
*   **Predictive Power**: Behavioral features (lagged PnL, leverage) combined with sentiment value serve as strong predictors for future trader success.

## 📈 Strategy Recommendations
1.  **Sentiment-Based Position Sizing**: Reduce exposure by 30% during Greed periods for high-leverage accounts to mitigate the lower risk-adjusted returns observed.
2.  **Dynamic Long/Short Balance**: Maintain a balanced (45-55%) long ratio during extreme sentiment periods to reduce directional risk from emotional bias.
3.  **Fear-Period Allocation**: Increase capital allocation by 25% during Fear periods for consistent performers to capitalize on higher structural profitability.
4.  **Sentiment-Triggered Stop Losses**: Tighten stops by 25% during Greed periods to protect against the higher probability of reversals and lower win rates.

---
**Author**: PrimeTradeAI Team / USER
**Files**: `sentiment_trading_analysis.py`, `predictive_model.py`, `FINAL_REPORT.md`
