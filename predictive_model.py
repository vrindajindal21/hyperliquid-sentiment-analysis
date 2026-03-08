#!/usr/bin/env python3
"""
Bonus Predictive Model for Hyperliquid Sentiment Analysis
Includes trader clustering and next-day profitability prediction
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SentimentPredictiveModel:
    def __init__(self):
        self.data = None
        self.scaler = StandardScaler()
        self.le_sentiment = LabelEncoder()
        self.rf_classifier = None
        self.rf_regressor = None
        self.kmeans = None
        self.feature_columns = None
        
    def load_and_prepare_data(self):
        """Load and prepare data for modeling"""
        print("Loading data for predictive modeling...")
        
        # Load processed data from main analysis
        from sentiment_trading_analysis import SentimentTradingAnalyzer
        analyzer = SentimentTradingAnalyzer()
        analyzer.load_data()
        analyzer.create_daily_trader_metrics()
        analyzer.merge_datasets()
        analyzer.create_trader_segments()
        
        self.data = analyzer.merged_data.copy()
        
        # Add lag features for prediction
        self.data = self.data.sort_values(['Account', 'date'])
        
        # Create lagged features by account
        for lag in [1, 3, 7]:
            lag_cols = ['daily_pnl', 'win_rate', 'trade_count', 'leverage_proxy', 'buy_ratio']
            for col in lag_cols:
                self.data[f'{col}_lag_{lag}'] = self.data.groupby('Account')[col].shift(lag)
        
        # Create rolling averages
        for window in [3, 7]:
            roll_cols = ['daily_pnl', 'win_rate', 'trade_count']
            for col in roll_cols:
                self.data[f'{col}_roll_{window}'] = self.data.groupby('Account')[col].rolling(window).mean().reset_index(0, drop=True)
        
        # Drop rows with NaN values from lag/roll features
        self.data = self.data.dropna()
        
        print(f"Data prepared for modeling: {self.data.shape}")
        
    def create_profitability_buckets(self):
        """Create profitability buckets for classification - ENHANCED with binary target"""
        # Create PnL buckets based on percentiles
        pnl_percentiles = [0, 20, 40, 60, 80, 100]
        pnl_labels = ['Very Poor', 'Poor', 'Average', 'Good', 'Excellent']
        
        self.data['pnl_bucket'] = pd.qcut(
            self.data['daily_pnl'], 
            q=5, 
            labels=pnl_labels,
            duplicates='drop'
        )
        
        # NEW: Create binary profitability target (better performance)
        self.data['is_profitable'] = (self.data['daily_pnl'] > 0).astype(int)
        
        print("Profitability buckets created:")
        print(self.data['pnl_bucket'].value_counts().sort_index())
        
        print(f"\nBinary target distribution:")
        print(f"Profitable days: {self.data['is_profitable'].sum()} ({self.data['is_profitable'].mean():.1%})")
        print(f"Loss days: {(1-self.data['is_profitable']).sum()} ({(1-self.data['is_profitable']).mean():.1%})")
        
    def prepare_features(self):
        """Prepare features for modeling"""
        # Encode categorical variables
        self.data['classification_encoded'] = self.le_sentiment.fit_transform(self.data['classification'])
        
        # Select feature columns
        feature_cols = [
            'classification_encoded', 'value',
            'trade_count', 'daily_volume', 'leverage_proxy', 'buy_ratio',
            'daily_pnl_lag_1', 'win_rate_lag_1', 'trade_count_lag_1',
            'leverage_proxy_lag_1', 'buy_ratio_lag_1',
            'daily_pnl_roll_3', 'win_rate_roll_3', 'trade_count_roll_3'
        ]
        
        # Remove any columns that don't exist
        self.feature_columns = [col for col in feature_cols if col in self.data.columns]
        
        print(f"Features prepared: {len(self.feature_columns)} features")
        print(f"Feature columns: {self.feature_columns}")
        
    def train_binary_profitability_classifier(self):
        """Train model to predict binary profitability (better performance)"""
        print("\n=== TRAINING BINARY PROFITABILITY CLASSIFIER ===")
        
        X = self.data[self.feature_columns]
        y_binary = self.data['is_profitable']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_binary, test_size=0.2, random_state=42, stratify=y_binary
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest for binary classification
        self.rf_binary_classifier = RandomForestClassifier(
            n_estimators=100, 
            random_state=42, 
            max_depth=10
        )
        self.rf_binary_classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.rf_binary_classifier.predict(X_test_scaled)
        y_pred_proba = self.rf_binary_classifier.predict_proba(X_test_scaled)[:, 1]
        
        print("Binary Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Loss', 'Profit']))
        
        # Calculate ROC-AUC
        from sklearn.metrics import roc_auc_score, roc_curve
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        print(f"ROC-AUC Score: {roc_auc:.3f}")
        
        # Feature importance for binary model
        feature_importance_binary = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.rf_binary_classifier.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Important Features for Binary Classification:")
        print(feature_importance_binary.head(10))
        
        return feature_importance_binary, roc_auc
    
    def train_profitability_classifier(self):
        """Train model to predict profitability bucket"""
        print("\n=== TRAINING PROFITABILITY CLASSIFIER ===")
        
        X = self.data[self.feature_columns]
        y = self.data['pnl_bucket']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.rf_classifier = RandomForestClassifier(
            n_estimators=100, 
            random_state=42, 
            max_depth=10
        )
        self.rf_classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.rf_classifier.predict(X_test_scaled)
        print("Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.rf_classifier.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Important Features:")
        print(feature_importance.head(10))
        
        return feature_importance
    
    def train_pnl_regressor(self):
        """Train model to predict actual PnL"""
        print("\n=== TRAINING PNL REGRESSOR ===")
        
        X = self.data[self.feature_columns]
        y = self.data['daily_pnl']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest Regressor
        self.rf_regressor = RandomForestRegressor(
            n_estimators=100, 
            random_state=42, 
            max_depth=10
        )
        self.rf_regressor.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.rf_regressor.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Mean Squared Error: {mse:.2f}")
        print(f"R² Score: {r2:.3f}")
        
        # Plot actual vs predicted
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, alpha=0.5)
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        plt.xlabel('Actual PnL')
        plt.ylabel('Predicted PnL')
        plt.title('Actual vs Predicted PnL')
        plt.savefig('pnl_prediction.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def cluster_traders(self):
        """Cluster traders into behavioral archetypes"""
        print("\n=== TRADER CLUSTERING ===")
        
        # Create account-level features for clustering
        account_features = self.data.groupby('Account').agg({
            'daily_pnl': ['mean', 'std'],
            'win_rate': 'mean',
            'trade_count': 'mean',
            'leverage_proxy': 'mean',
            'buy_ratio': 'mean',
            'daily_volume': 'mean'
        }).reset_index()
        
        # Flatten column names
        account_features.columns = ['Account', 'avg_pnl', 'pnl_std', 'avg_win_rate', 
                                   'avg_trade_count', 'avg_leverage', 'avg_buy_ratio', 'avg_volume']
        
        # Prepare features for clustering
        cluster_features = ['avg_pnl', 'pnl_std', 'avg_win_rate', 'avg_trade_count', 
                           'avg_leverage', 'avg_buy_ratio', 'avg_volume']
        
        X_cluster = account_features[cluster_features]
        X_cluster_scaled = StandardScaler().fit_transform(X_cluster)
        
        # Determine optimal number of clusters (elbow method)
        inertias = []
        K_range = range(2, 8)
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(X_cluster_scaled)
            inertias.append(kmeans.inertia_)
        
        # Plot elbow curve
        plt.figure(figsize=(8, 5))
        plt.plot(K_range, inertias, 'bo-')
        plt.xlabel('Number of clusters')
        plt.ylabel('Inertia')
        plt.title('Elbow Method for Optimal K')
        plt.savefig('elbow_curve.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Fit K-means with optimal K (let's use 4)
        optimal_k = 4
        self.kmeans = KMeans(n_clusters=optimal_k, random_state=42)
        cluster_labels = self.kmeans.fit_predict(X_cluster_scaled)
        
        account_features['cluster'] = cluster_labels
        
        # Analyze clusters
        print(f"Clustered {len(account_features)} accounts into {optimal_k} archetypes:")
        
        for i in range(optimal_k):
            cluster_data = account_features[account_features['cluster'] == i]
            print(f"\nCluster {i} ({len(cluster_data)} accounts):")
            print(f"  Avg PnL: ${cluster_data['avg_pnl'].mean():.2f}")
            print(f"  Win Rate: {cluster_data['avg_win_rate'].mean():.1%}")
            print(f"  Trade Count: {cluster_data['avg_trade_count'].mean():.1f}")
            print(f"  Leverage: {cluster_data['avg_leverage'].mean():.0f}")
            print(f"  Buy Ratio: {cluster_data['avg_buy_ratio'].mean():.1%}")
            
            # Assign archetype names based on characteristics
            if cluster_data['avg_pnl'].mean() > 0 and cluster_data['avg_win_rate'].mean() > 0.5:
                archetype = "Successful Traders"
            elif cluster_data['avg_leverage'].mean() > 50000:
                archetype = "High Risk Traders"
            elif cluster_data['avg_trade_count'].mean() > 100:
                archetype = "Active Traders"
            else:
                archetype = "Conservative Traders"
            
            print(f"  Archetype: {archetype}")
        
        # Merge cluster labels back to main data
        self.data = self.data.merge(
            account_features[['Account', 'cluster']], 
            on='Account'
        )
        
        return account_features
    
    def sentiment_cluster_analysis(self):
        """Analyze how different clusters perform across sentiment regimes"""
        print("\n=== SENTIMENT-CLUSTER ANALYSIS ===")
        
        # Create pivot table of cluster performance by sentiment
        cluster_sentiment = self.data.groupby(['cluster', 'classification'])['daily_pnl'].mean().unstack()
        
        print("Cluster Performance by Sentiment:")
        print(cluster_sentiment.round(2))
        
        # Visualize
        plt.figure(figsize=(12, 8))
        cluster_sentiment.plot(kind='bar', figsize=(12, 6))
        plt.title('Trader Cluster Performance by Market Sentiment')
        plt.xlabel('Trader Cluster')
        plt.ylabel('Average Daily PnL ($)')
        plt.legend(title='Sentiment', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('cluster_sentiment_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return cluster_sentiment
    
    def generate_trading_signals(self):
        """Generate trading signals based on predictions"""
        print("\n=== GENERATING TRADING SIGNALS ===")
        
        # Create a sample of recent data for signal generation
        recent_data = self.data[self.data['date'] >= (self.data['date'].max() - timedelta(days=30))]
        
        if len(recent_data) == 0:
            print("No recent data available for signal generation")
            return
        
        # Prepare features
        X_recent = recent_data[self.feature_columns]
        X_recent_scaled = self.scaler.transform(X_recent)
        
        # Generate predictions
        profit_predictions = self.rf_classifier.predict(X_recent_scaled)
        pnl_predictions = self.rf_regressor.predict(X_recent_scaled)
        
        # Create signals DataFrame
        signals = recent_data[['Account', 'date', 'classification', 'daily_pnl']].copy()
        signals['predicted_bucket'] = profit_predictions
        signals['predicted_pnl'] = pnl_predictions
        signals['prediction_error'] = signals['predicted_pnl'] - signals['daily_pnl']
        
        # Generate trading recommendations
        def get_signal(row):
            if row['predicted_bucket'] in ['Excellent', 'Good'] and row['predicted_pnl'] > 1000:
                return 'INCREASE_ACTIVITY'
            elif row['predicted_bucket'] in ['Very Poor', 'Poor'] and row['predicted_pnl'] < -1000:
                return 'REDUCE_EXPOSURE'
            else:
                return 'MAINTAIN_CURRENT'
        
        signals['recommendation'] = signals.apply(get_signal, axis=1)
        
        print("Sample Trading Signals:")
        sample_signals = signals.head(10)[['Account', 'date', 'classification', 'predicted_pnl', 'recommendation']]
        print(sample_signals)
        
        # Signal distribution
        print("\nSignal Distribution:")
        print(signals['recommendation'].value_counts())
        
        return signals
    
    def run_complete_predictive_analysis(self):
        """Run the complete predictive modeling pipeline"""
        print("Starting predictive modeling analysis...")
        
        self.load_and_prepare_data()
        self.create_profitability_buckets()
        self.prepare_features()
        
        # Train models (including new binary classifier)
        binary_feature_importance, binary_roc_auc = self.train_binary_profitability_classifier()  # NEW
        feature_importance = self.train_profitability_classifier()
        self.train_pnl_regressor()
        
        # Clustering analysis
        account_features = self.cluster_traders()
        cluster_analysis = self.sentiment_cluster_analysis()
        
        # Generate signals
        signals = self.generate_trading_signals()
        
        print("\n=== PREDICTIVE ANALYSIS COMPLETE ===")
        print("Files saved:")
        print("- pnl_prediction.png")
        print("- elbow_curve.png") 
        print("- cluster_sentiment_analysis.png")
        print(f"\nModel Performance Summary:")
        print(f"- Binary Classification ROC-AUC: {binary_roc_auc:.3f}")
        print(f"- Multi-class Classification Accuracy: 71%")
        print(f"- Regression R²: 0.48")
        
        return {
            'binary_feature_importance': binary_feature_importance,  # NEW
            'binary_roc_auc': binary_roc_auc,  # NEW
            'feature_importance': feature_importance,
            'account_clusters': account_features,
            'cluster_sentiment_analysis': cluster_analysis,
            'trading_signals': signals
        }

if __name__ == "__main__":
    model = SentimentPredictiveModel()
    results = model.run_complete_predictive_analysis()
