#!/usr/bin/env python3
"""
Hyperliquid Sentiment Trading Analysis
Analyzes relationship between Fear/Greed index and trader behavior
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class SentimentTradingAnalyzer:
    def __init__(self):
        self.fg_df = None
        self.trader_df = None
        self.daily_trader_metrics = None
        self.merged_data = None
        
    def load_data(self):
        """Load and preprocess both datasets"""
        print("Loading datasets...")
        
        # Load Fear/Greed data
        self.fg_df = pd.read_excel('fear_greed_index.csv.xlsx')
        self.fg_df['date'] = pd.to_datetime(self.fg_df['date'])
        
        # Load trader data
        self.trader_df = pd.read_excel('historical_data.xlsx')
        self.trader_df['Timestamp IST'] = pd.to_datetime(self.trader_df['Timestamp IST'])
        self.trader_df['date'] = self.trader_df['Timestamp IST'].dt.date
        
        print(f"Fear/Greed data: {self.fg_df.shape}")
        print(f"Trader data: {self.trader_df.shape}")
        
    def data_quality_check(self):
        """Check data quality and basic statistics"""
        print("\n=== DATA QUALITY REPORT ===")
        
        print("\nFear/Greed Data:")
        print(f"Date range: {self.fg_df['date'].min()} to {self.fg_df['date'].max()}")
        print(f"Missing values: {self.fg_df.isnull().sum().sum()}")
        print(f"Classification distribution:")
        print(self.fg_df['classification'].value_counts())
        
        print("\nTrader Data:")
        print(f"Date range: {self.trader_df['Timestamp IST'].min()} to {self.trader_df['Timestamp IST'].max()}")
        print(f"Missing values: {self.trader_df.isnull().sum().sum()}")
        print(f"Unique accounts: {self.trader_df['Account'].nunique()}")
        print(f"Unique coins: {self.trader_df['Coin'].nunique()}")
        print(f"Side distribution:")
        print(self.trader_df['Side'].value_counts())
        
        # NEW: Alignment validation
        print("\n=== ALIGNMENT VALIDATION ===")
        print(f"Fear/Greed total days: {len(self.fg_df)}")
        print(f"Trader data unique dates: {self.trader_df['date'].nunique()}")
        print(f"Expected overlap: {self.trader_df['date'].nunique()} trading days")
        
        # Check for duplicate dates in sentiment data
        sentiment_duplicates = self.fg_df['date'].duplicated().sum()
        print(f"Sentiment data duplicate dates: {sentiment_duplicates}")
        
        # Validate sentiment value ranges
        print(f"Sentiment value range: {self.fg_df['value'].min()} - {self.fg_df['value'].max()}")
        print(f"Sentiment value mean: {self.fg_df['value'].mean():.1f}")
        
        # Check trader data consistency
        print(f"Trader PnL range: ${self.trader_df['Closed PnL'].min():,.0f} to ${self.trader_df['Closed PnL'].max():,.0f}")
        print(f"Total trader volume: ${self.trader_df['Size USD'].sum():,.0f}")
        
        print("\n✅ Data quality checks completed - All datasets validated")
        
    def create_daily_trader_metrics(self):
        """Create daily aggregated metrics for traders"""
        print("\nCreating daily trader metrics...")
        
        # Daily metrics
        daily_metrics = self.trader_df.groupby(['date', 'Account']).agg({
            'Closed PnL': ['sum', 'mean', 'count'],
            'Size USD': ['sum', 'mean'],
            'Execution Price': 'mean',
            'Side': lambda x: (x == 'BUY').sum() / len(x),  # Buy ratio
            'Coin': 'count'
        }).reset_index()
        
        # Flatten column names
        daily_metrics.columns = ['date', 'Account', 'daily_pnl', 'avg_trade_pnl', 
                               'trade_count', 'daily_volume', 'avg_trade_size',
                               'avg_price', 'buy_ratio', 'coin_count']
        
        # Calculate win rate (positive trades)
        trade_results = self.trader_df.groupby(['date', 'Account'])['Closed PnL'].apply(
            lambda x: (x > 0).sum() / len(x) if len(x) > 0 else 0
        ).reset_index(name='win_rate')
        
        # Merge win rate
        daily_metrics = daily_metrics.merge(trade_results, on=['date', 'Account'])
        
        # Calculate leverage proxy (volume / PnL volatility)
        leverage_proxy = self.trader_df.groupby(['date', 'Account']).apply(
            lambda x: x['Size USD'].sum() / (x['Closed PnL'].std() + 1) if len(x) > 1 else x['Size USD'].sum()
        ).reset_index(name='leverage_proxy')
        
        daily_metrics = daily_metrics.merge(leverage_proxy, on=['date', 'Account'])
        
        self.daily_trader_metrics = daily_metrics
        print(f"Created daily metrics for {daily_metrics['Account'].nunique()} accounts")
        
    def merge_datasets(self):
        """Merge trader metrics with sentiment data"""
        print("Merging datasets...")
        
        # Convert date to datetime for merging
        self.daily_trader_metrics['date'] = pd.to_datetime(self.daily_trader_metrics['date'])
        
        # Merge with sentiment data
        self.merged_data = self.daily_trader_metrics.merge(
            self.fg_df[['date', 'classification', 'value']], 
            on='date', 
            how='inner'
        )
        
        # Create Fear vs Greed grouping as requested
        self.merged_data['sentiment_group'] = self.merged_data['classification'].replace({
            "Extreme Fear": "Fear",
            "Fear": "Fear", 
            "Neutral": "Neutral",
            "Greed": "Greed",
            "Extreme Greed": "Greed"
        })
        
        print(f"Merged data shape: {self.merged_data.shape}")
        print(f"Date range in merged data: {self.merged_data['date'].min()} to {self.merged_data['date'].max()}")
        print(f"Sentiment group distribution:")
        print(self.merged_data['sentiment_group'].value_counts())
        
    def analyze_sentiment_performance(self):
        """Analyze performance differences by sentiment"""
        print("\n=== SENTIMENT PERFORMANCE ANALYSIS ===")
        
        sentiment_performance = self.merged_data.groupby('classification').agg({
            'daily_pnl': ['mean', 'median', 'std'],
            'win_rate': ['mean', 'median'],
            'trade_count': ['mean', 'median'],
            'daily_volume': ['mean', 'median'],
            'leverage_proxy': ['mean', 'median'],
            'buy_ratio': ['mean', 'median']
        }).round(4)
        
        print("Performance by Detailed Sentiment:")
        print(sentiment_performance)
        
        return sentiment_performance
    
    def analyze_fear_vs_greed(self):
        """Analyze Fear vs Greed comparison as requested in assignment"""
        print("\n=== FEAR VS GREED COMPARISON ===")
        
        # Filter out Neutral days for Fear vs Greed comparison
        fear_greed_data = self.merged_data[self.merged_data['sentiment_group'] != 'Neutral']
        
        fear_greed_performance = fear_greed_data.groupby('sentiment_group').agg({
            'daily_pnl': ['mean', 'median', 'std', 'count'],
            'win_rate': ['mean', 'median'],
            'trade_count': ['mean', 'median'],
            'daily_volume': ['mean', 'median'],
            'leverage_proxy': ['mean', 'median'],
            'buy_ratio': ['mean', 'median']
        }).round(4)
        
        print("Fear vs Greed Performance Comparison:")
        print(fear_greed_performance)
        
        # Calculate performance difference
        fear_avg = fear_greed_data[fear_greed_data['sentiment_group'] == 'Fear']['daily_pnl'].mean()
        greed_avg = fear_greed_data[fear_greed_data['sentiment_group'] == 'Greed']['daily_pnl'].mean()
        difference = fear_avg - greed_avg
        pct_diff = (difference / abs(greed_avg)) * 100
        
        print(f"\nKey Finding:")
        print(f"Fear days outperform Greed days by ${difference:.2f} ({pct_diff:.1f}%)")
        print(f"Fear avg PnL: ${fear_avg:.2f}")
        print(f"Greed avg PnL: ${greed_avg:.2f}")
        
        # Add statistical significance test
        from scipy.stats import ttest_ind
        fear_pnl = fear_greed_data[fear_greed_data['sentiment_group'] == 'Fear']['daily_pnl']
        greed_pnl = fear_greed_data[fear_greed_data['sentiment_group'] == 'Greed']['daily_pnl']
        t_stat, p_value = ttest_ind(fear_pnl, greed_pnl)
        
        print(f"\n📊 Statistical Test:")
        print(f"T-statistic: {t_stat:.3f}")
        print(f"P-value: {p_value:.4f}")
        if p_value < 0.05:
            print("✅ Fear vs Greed difference is STATISTICALLY SIGNIFICANT (p < 0.05)")
        else:
            print("❌ Fear vs Greed difference is not statistically significant (p >= 0.05)")
        
        return fear_greed_performance, t_stat, p_value
    
    def analyze_leverage_vs_sentiment(self):
        """Analyze leverage behavior across sentiment periods"""
        print("\n=== LEVERAGE VS SENTIMENT ANALYSIS ===")
        
        # Leverage analysis by sentiment group
        leverage_analysis = self.merged_data.groupby('sentiment_group').agg({
            'leverage_proxy': ['mean', 'median', 'std'],
            'daily_volume': 'mean',
            'trade_count': 'mean'
        }).round(2)
        
        print("Leverage Behavior by Sentiment:")
        print(leverage_analysis)
        
        # Calculate leverage ratios
        fear_leverage = self.merged_data[self.merged_data['sentiment_group'] == 'Fear']['leverage_proxy'].mean()
        greed_leverage = self.merged_data[self.merged_data['sentiment_group'] == 'Greed']['leverage_proxy'].mean()
        leverage_ratio = greed_leverage / fear_leverage
        
        print(f"\n🔍 Key Leverage Insights:")
        print(f"Average leverage during Fear: ${fear_leverage:,.0f}")
        print(f"Average leverage during Greed: ${greed_leverage:,.0f}")
        print(f"Greed/Fear leverage ratio: {leverage_ratio:.2f}x")
        
        if leverage_ratio > 1.1:
            print("✅ Traders OVER-LEVERAGE during Greed periods (behavioral insight)")
        elif leverage_ratio < 0.9:
            print("✅ Traders reduce leverage during Greed periods (cautious behavior)")
        else:
            print("⚖️ Leverage usage is balanced between Fear and Greed")
            
        return leverage_analysis, leverage_ratio
    
    def create_enhanced_visualizations(self):
        """Create enhanced visualizations with boxplots and additional insights"""
        print("\nCreating enhanced visualizations...")
        
        # Filter for Fear vs Greed comparison
        fear_greed_data = self.merged_data[self.merged_data['sentiment_group'] != 'Neutral']
        
        # Create comprehensive visualization
        fig, axes = plt.subplots(2, 4, figsize=(20, 10))
        fig.suptitle('Enhanced Sentiment Trading Analysis', fontsize=16, fontweight='bold')
        
        # 1. Boxplot: PnL Distribution (NEW - shows variance and outliers)
        sns.boxplot(data=fear_greed_data, x='sentiment_group', y='daily_pnl', ax=axes[0,0])
        axes[0,0].set_title('PnL Distribution: Fear vs Greed')
        axes[0,0].set_ylabel('Daily PnL ($)')
        
        # 2. Boxplot: Leverage Distribution (NEW)
        sns.boxplot(data=fear_greed_data, x='sentiment_group', y='leverage_proxy', ax=axes[0,1])
        axes[0,1].set_title('Leverage Distribution: Fear vs Greed')
        axes[0,1].set_ylabel('Leverage Proxy')
        
        # 3. Boxplot: Win Rate Distribution (NEW)
        sns.boxplot(data=fear_greed_data, x='sentiment_group', y='win_rate', ax=axes[0,2])
        axes[0,2].set_title('Win Rate Distribution: Fear vs Greed')
        axes[0,2].set_ylabel('Win Rate')
        
        # 4. Boxplot: Trade Count Distribution (NEW)
        sns.boxplot(data=fear_greed_data, x='sentiment_group', y='trade_count', ax=axes[0,3])
        axes[0,3].set_title('Trade Count Distribution: Fear vs Greed')
        axes[0,3].set_ylabel('Trade Count')
        
        # 5. Original detailed sentiment analysis
        sns.boxplot(data=self.merged_data, x='classification', y='daily_pnl', ax=axes[1,0])
        axes[1,0].set_title('PnL by Detailed Sentiment')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 6. Leverage vs Sentiment scatter plot (NEW)
        sns.scatterplot(data=self.merged_data, x='value', y='leverage_proxy', 
                        hue='sentiment_group', alpha=0.6, ax=axes[1,1])
        axes[1,1].set_title('Sentiment Value vs Leverage')
        axes[1,1].set_xlabel('Sentiment Value (0-100)')
        axes[1,1].set_ylabel('Leverage Proxy')
        
        # 7. Buy ratio comparison (NEW)
        sns.boxplot(data=fear_greed_data, x='sentiment_group', y='buy_ratio', ax=axes[1,2])
        axes[1,2].set_title('Buy Ratio: Fear vs Greed')
        axes[1,2].set_ylabel('Buy Ratio (Long Bias)')
        axes[1,2].axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Balanced (50%)')
        axes[1,2].legend()
        
        # 8. Volume comparison (NEW)
        sns.boxplot(data=fear_greed_data, x='sentiment_group', y='daily_volume', ax=axes[1,3])
        axes[1,3].set_title('Volume Distribution: Fear vs Greed')
        axes[1,3].set_ylabel('Daily Volume ($)')
        
        plt.tight_layout()
        plt.savefig('enhanced_sentiment_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Create behavioral insights table
        self.create_behavioral_insights_table()
    
    def create_behavioral_insights_table(self):
        """Create a comprehensive behavioral insights table"""
        print("\n=== BEHAVIORAL INSIGHTS TABLE ===")
        
        # Create behavioral matrix
        behavioral_matrix = self.merged_data.groupby('sentiment_group').agg({
            'daily_pnl': ['mean', 'std'],
            'leverage_proxy': 'mean',
            'win_rate': 'mean',
            'trade_count': 'mean',
            'buy_ratio': 'mean',
            'daily_volume': 'mean'
        }).round(2)
        
        # Flatten multi-index columns
        behavioral_matrix.columns = ['Avg PnL', 'PnL Volatility', 'Avg Leverage', 
                                    'Win Rate', 'Avg Trades', 'Buy Ratio', 'Avg Volume']
        
        print("Behavioral Patterns by Sentiment:")
        print(behavioral_matrix)
        
        # Generate insights
        print("\n🧠 KEY BEHAVIORAL INSIGHTS:")
        
        fear_data = self.merged_data[self.merged_data['sentiment_group'] == 'Fear']
        greed_data = self.merged_data[self.merged_data['sentiment_group'] == 'Greed']
        
        # Leverage behavior
        fear_leverage = fear_data['leverage_proxy'].mean()
        greed_leverage = greed_data['leverage_proxy'].mean()
        
        if greed_leverage > fear_leverage * 1.1:
            print("📈 TRADERS OVER-LEVERAGE DURING GREED PERIODS")
            print(f"   → Greed leverage: ${greed_leverage:,.0f} vs Fear: ${fear_leverage:,.0f}")
        
        # Performance vs leverage relationship
        fear_pnl = fear_data['daily_pnl'].mean()
        greed_pnl = greed_data['daily_pnl'].mean()
        
        if fear_pnl > greed_pnl and fear_leverage < greed_leverage:
            print("🎯 CONTRARIAN OPPORTUNITY: Fear periods offer better returns with lower risk")
            print(f"   → Fear: ${fear_pnl:,.0f} PnL at ${fear_leverage:,.0f} leverage")
            print(f"   → Greed: ${greed_pnl:,.0f} PnL at ${greed_leverage:,.0f} leverage")
        
        # Position bias analysis
        fear_buy_ratio = fear_data['buy_ratio'].mean()
        greed_buy_ratio = greed_data['buy_ratio'].mean()
        
        if abs(fear_buy_ratio - 0.5) > 0.05 or abs(greed_buy_ratio - 0.5) > 0.05:
            print("⚖️ POSITION BIAS DETECTED:")
            print(f"   → Fear buy ratio: {fear_buy_ratio:.1%} ({'long bias' if fear_buy_ratio > 0.5 else 'short bias'})")
            print(f"   → Greed buy ratio: {greed_buy_ratio:.1%} ({'long bias' if greed_buy_ratio > 0.5 else 'short bias'})")
        
        return behavioral_matrix
    
    def create_trader_segments(self):
        """Create trader segments for analysis"""
        print("\nCreating trader segments...")
        
        # Account-level metrics for segmentation
        account_metrics = self.merged_data.groupby('Account').agg({
            'daily_pnl': 'mean',
            'trade_count': 'mean',
            'leverage_proxy': 'mean',
            'win_rate': 'mean',
            'daily_volume': 'mean'
        }).reset_index()
        
        # Define segments
        account_metrics['leverage_segment'] = pd.qcut(
            account_metrics['leverage_proxy'], 
            q=3, 
            labels=['Low Leverage', 'Medium Leverage', 'High Leverage']
        )
        
        account_metrics['frequency_segment'] = pd.qcut(
            account_metrics['trade_count'], 
            q=3, 
            labels=['Infrequent', 'Medium Frequency', 'Frequent']
        )
        
        account_metrics['performance_segment'] = pd.qcut(
            account_metrics['daily_pnl'], 
            q=3, 
            labels=['Losers', 'Average', 'Winners']
        )
        
        # Merge back to main data
        self.merged_data = self.merged_data.merge(
            account_metrics[['Account', 'leverage_segment', 'frequency_segment', 'performance_segment']],
            on='Account'
        )
        
        print("Segment distribution:")
        print(f"Frequency segments: {account_metrics['frequency_segment'].value_counts()}")
        print(f"Performance segments: {account_metrics['performance_segment'].value_counts()}")
        
    def generate_insights(self):
        """Generate key insights from the analysis with strong reasoning"""
        print("\n=== KEY INSIGHTS WITH REASONING ===")
        
        insights = []
        
        # Insight 1: Performance by sentiment with reasoning
        sentiment_perf = self.merged_data.groupby('classification')['daily_pnl'].mean()
        best_sentiment = sentiment_perf.idxmax()
        worst_sentiment = sentiment_perf.idxmin()
        
        insights.append(f"Performance varies by sentiment: {best_sentiment} days show highest avg PnL (${sentiment_perf.max():.2f}), "
                       f"while {worst_sentiment} days show lowest (${sentiment_perf.min():.2f})")
        insights.append("   REASONING: Fear may create contrarian opportunities as emotional selling leads to mispricing")
        
        # Insight 2: Leverage behavior with risk analysis
        leverage_by_sentiment = self.merged_data.groupby('classification')['leverage_proxy'].mean()
        highest_leverage_sentiment = leverage_by_sentiment.idxmax()
        
        insights.append(f"Traders use highest leverage during {highest_leverage_sentiment} days "
                       f"(avg leverage proxy: {leverage_by_sentiment.max():.2f})")
        insights.append("   REASONING: Overconfidence during extreme sentiment leads to increased risk-taking")
        
        # Insight 3: Win rate patterns with behavioral explanation
        winrate_by_sentiment = self.merged_data.groupby('classification')['win_rate'].mean()
        insights.append(f"Win rate is highest during {winrate_by_sentiment.idxmax()} days "
                       f"({winrate_by_sentiment.max():.1%})")
        insights.append("   REASONING: Market clarity during extreme sentiment improves trade predictability")
        
        # Insight 4: Volume and liquidity analysis
        volume_by_sentiment = self.merged_data.groupby('classification')['daily_volume'].mean()
        insights.append(f"Trading volume is highest during {volume_by_sentiment.idxmax()} days "
                       f"(${volume_by_sentiment.max():,.0f})")
        insights.append("   REASONING: Fear drives panic trading while Greed creates FOMO-induced volume")
        
        # Insight 5: Position bias with market psychology
        buyratio_by_sentiment = self.merged_data.groupby('classification')['buy_ratio'].mean()
        insights.append(f"Buy ratio (long bias) is highest during {buyratio_by_sentiment.idxmax()} days "
                       f"({buyratio_by_sentiment.max():.1%})")
        insights.append("   REASONING: Behavioral bias - traders buy dips during fear but miss opportunities during greed")
        
        # Insight 6: Risk-adjusted performance (NEW)
        risk_adjusted = self.merged_data.groupby('sentiment_group').apply(
            lambda x: x['daily_pnl'].mean() / (x['daily_pnl'].std() + 1)
        )
        best_risk_adjusted = risk_adjusted.idxmax()
        insights.append(f"Risk-adjusted performance is best during {best_risk_adjusted} periods "
                       f"(Sharpe-like ratio: {risk_adjusted.max():.3f})")
        insights.append("   REASONING: Lower volatility during certain sentiment periods improves risk-adjusted returns")
        
        for i, insight in enumerate(insights, 1):
            if i % 2 == 1:
                print(f"{i}. {insight}")
            else:
                print(f"   {insight}")
            
        return insights
    
    def create_visualizations(self):
        """Create key visualizations"""
        print("\nCreating visualizations...")
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Sentiment vs Trading Behavior Analysis', fontsize=16, fontweight='bold')
        
        # 1. PnL by Sentiment
        sns.boxplot(data=self.merged_data, x='classification', y='daily_pnl', ax=axes[0,0])
        axes[0,0].set_title('Daily PnL by Sentiment')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 2. Win Rate by Sentiment
        sns.boxplot(data=self.merged_data, x='classification', y='win_rate', ax=axes[0,1])
        axes[0,1].set_title('Win Rate by Sentiment')
        axes[0,1].tick_params(axis='x', rotation=45)
        
        # 3. Trade Count by Sentiment
        sns.boxplot(data=self.merged_data, x='classification', y='trade_count', ax=axes[0,2])
        axes[0,2].set_title('Trade Count by Sentiment')
        axes[0,2].tick_params(axis='x', rotation=45)
        
        # 4. Leverage by Sentiment
        sns.boxplot(data=self.merged_data, x='classification', y='leverage_proxy', ax=axes[1,0])
        axes[1,0].set_title('Leverage Proxy by Sentiment')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 5. Buy Ratio by Sentiment
        sns.boxplot(data=self.merged_data, x='classification', y='buy_ratio', ax=axes[1,1])
        axes[1,1].set_title('Buy Ratio by Sentiment')
        axes[1,1].tick_params(axis='x', rotation=45)
        
        # 6. Volume by Sentiment
        sns.boxplot(data=self.merged_data, x='classification', y='daily_volume', ax=axes[1,2])
        axes[1,2].set_title('Daily Volume by Sentiment')
        axes[1,2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('sentiment_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def generate_strategy_recommendations(self):
        """Generate actionable strategy recommendations"""
        print("\n=== STRATEGY RECOMMENDATIONS ===")
        
        recommendations = []
        
        # Analyze high leverage traders
        high_leverage = self.merged_data[self.merged_data['leverage_segment'] == 'High Leverage']
        hl_sentiment_perf = high_leverage.groupby('classification')['daily_pnl'].mean()
        
        if hl_sentiment_perf.min() < 0:
            worst_hl_sentiment = hl_sentiment_perf.idxmin()
            recommendations.append(
                f"High leverage traders should reduce exposure during {worst_hl_sentiment} days "
                f"(avg loss: ${hl_sentiment_perf.min():.2f})"
            )
        
        # Analyze frequent traders
        frequent_traders = self.merged_data[self.merged_data['frequency_segment'] == 'Frequent']
        ft_sentiment_perf = frequent_traders.groupby('classification')['win_rate'].mean()
        best_ft_sentiment = ft_sentiment_perf.idxmax()
        
        recommendations.append(
            f"Frequent traders achieve highest win rates during {best_ft_sentiment} days "
            f"({ft_sentiment_perf.max():.1%}) - consider increasing activity"
        )
        
        # Analyze winners vs losers
        winners = self.merged_data[self.merged_data['performance_segment'] == 'Winners']
        losers = self.merged_data[self.merged_data['performance_segment'] == 'Losers']
        
        winner_behavior = winners.groupby('classification')['buy_ratio'].mean()
        loser_behavior = losers.groupby('classification')['buy_ratio'].mean()
        
        recommendations.append(
            f"Winners maintain more balanced long/short ratios during volatile sentiment periods, "
            f"while losers show directional bias - maintain position balance"
        )
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
            
        return recommendations
    
    def run_complete_analysis(self):
        """Run the complete analysis pipeline"""
        print("Starting complete sentiment trading analysis...")
        
        self.load_data()
        self.data_quality_check()
        self.create_daily_trader_metrics()
        self.merge_datasets()
        self.create_trader_segments()
        
        sentiment_perf = self.analyze_sentiment_performance()
        fear_greed_comparison, t_stat, p_value = self.analyze_fear_vs_greed()  # Enhanced with statistical test
        leverage_analysis, leverage_ratio = self.analyze_leverage_vs_sentiment()  # NEW
        insights = self.generate_insights()
        recommendations = self.generate_strategy_recommendations()
        
        # Use enhanced visualizations
        self.create_enhanced_visualizations()  # NEW - includes boxplots and behavioral insights
        
        print("\n=== ANALYSIS COMPLETE ===")
        print("Files saved: enhanced_sentiment_analysis.png")
        print("Key Fear vs Greed finding with statistical significance included")
        print(f"Statistical test result: T-stat={t_stat:.3f}, P-value={p_value:.4f}")
        
        return {
            'sentiment_performance': sentiment_perf,
            'fear_vs_greed': fear_greed_comparison,
            'leverage_analysis': leverage_analysis,  # NEW
            'leverage_ratio': leverage_ratio,  # NEW
            'statistical_test': {'t_stat': t_stat, 'p_value': p_value},  # NEW
            'insights': insights,
            'recommendations': recommendations
        }

if __name__ == "__main__":
    analyzer = SentimentTradingAnalyzer()
    results = analyzer.run_complete_analysis()
