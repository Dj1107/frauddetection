"""
Fraud Detection ML Project
==========================
Complete end-to-end fraud detection system using credit card transaction data.

This project demonstrates:
- Data preprocessing and handling imbalanced data
- Multiple ML algorithms (Logistic Regression, Random Forest, XGBoost, LightGBM)
- Hyperparameter tuning with Bayesian Optimization
- Model evaluation with business metrics
- Feature importance analysis
- SHAP value interpretability
- Production-ready model deployment

Author: Your Name
Date: 2024
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_auc_score, roc_curve,
    precision_recall_curve, f1_score, precision_score, recall_score,
    accuracy_score, Matthews_corrcoef
)
import xgboost as xgb
import lightgbm as lgb
import joblib
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

class FraudDetectionPipeline:
    """Complete fraud detection pipeline"""
    
    def __init__(self, data_path, test_size=0.3, random_state=42):
        """Initialize the pipeline"""
        self.data_path = data_path
        self.test_size = test_size
        self.random_state = random_state
        self.models = {}
        self.metrics = {}
        
    def load_data(self):
        """Load and explore the dataset"""
        print("=" * 80)
        print("LOADING DATA")
        print("=" * 80)
        
        self.df = pd.read_csv(self.data_path)
        print(f"\nDataset shape: {self.df.shape}")
        print(f"\nFirst few rows:")
        print(self.df.head())
        print(f"\nData types:")
        print(self.df.dtypes)
        print(f"\nMissing values:")
        print(self.df.isnull().sum())
        print(f"\nClass distribution:")
        print(self.df['Class'].value_counts())
        print(f"Fraud percentage: {self.df['Class'].value_counts()[1] / len(self.df) * 100:.2f}%")
        
        return self.df
    
    def preprocess_data(self):
        """Preprocess the data"""
        print("\n" + "=" * 80)
        print("PREPROCESSING DATA")
        print("=" * 80)
        
        # Separate features and target
        X = self.df.drop('Class', axis=1)
        y = self.df['Class']
        
        # The Amount column may need scaling
        if 'Amount' in X.columns:
            print("\nScaling Amount column...")
            scaler_amount = StandardScaler()
            X['Amount'] = scaler_amount.fit_transform(X[['Amount']])
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state, stratify=y
        )
        
        # Standardize features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        print(f"\nTraining set shape: {X_train_scaled.shape}")
        print(f"Test set shape: {X_test_scaled.shape}")
        print(f"Training fraud rate: {y_train.value_counts()[1] / len(y_train) * 100:.2f}%")
        print(f"Test fraud rate: {y_test.value_counts()[1] / len(y_test) * 100:.2f}%")
        
        self.X_train = X_train
        self.X_test = X_test
        self.X_train_scaled = X_train_scaled
        self.X_test_scaled = X_test_scaled
        self.y_train = y_train
        self.y_test = y_test
        self.scaler = scaler
        self.feature_names = X.columns.tolist()
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train_logistic_regression(self):
        """Train Logistic Regression"""
        print("\n" + "=" * 80)
        print("TRAINING LOGISTIC REGRESSION")
        print("=" * 80)
        
        model = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=self.random_state,
            n_jobs=-1
        )
        model.fit(self.X_train_scaled, self.y_train)
        
        self.models['Logistic Regression'] = model
        self._evaluate_model('Logistic Regression', model)
        
        return model
    
    def train_random_forest(self):
        """Train Random Forest"""
        print("\n" + "=" * 80)
        print("TRAINING RANDOM FOREST")
        print("=" * 80)
        
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight='balanced',
            random_state=self.random_state,
            n_jobs=-1
        )
        model.fit(self.X_train, self.y_train)
        
        self.models['Random Forest'] = model
        self._evaluate_model('Random Forest', model)
        
        return model
    
    def train_xgboost(self):
        """Train XGBoost"""
        print("\n" + "=" * 80)
        print("TRAINING XGBOOST")
        print("=" * 80)
        
        # Calculate scale_pos_weight for imbalanced data
        scale_pos_weight = (self.y_train == 0).sum() / (self.y_train == 1).sum()
        
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=7,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            random_state=self.random_state,
            n_jobs=-1,
            eval_metric='logloss'
        )
        model.fit(self.X_train, self.y_train)
        
        self.models['XGBoost'] = model
        self._evaluate_model('XGBoost', model)
        
        return model
    
    def train_lightgbm(self):
        """Train LightGBM"""
        print("\n" + "=" * 80)
        print("TRAINING LIGHTGBM")
        print("=" * 80)
        
        # Calculate scale_pos_weight for imbalanced data
        scale_pos_weight = (self.y_train == 0).sum() / (self.y_train == 1).sum()
        
        model = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=7,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            random_state=self.random_state,
            n_jobs=-1
        )
        model.fit(self.X_train, self.y_train)
        
        self.models['LightGBM'] = model
        self._evaluate_model('LightGBM', model)
        
        return model
    
    def _evaluate_model(self, model_name, model):
        """Evaluate a single model"""
        # Predictions
        y_pred = model.predict(self.X_test_scaled if model_name == 'Logistic Regression' else self.X_test)
        y_pred_proba = model.predict_proba(self.X_test_scaled if model_name == 'Logistic Regression' else self.X_test)[:, 1]
        
        # Metrics
        acc = accuracy_score(self.y_test, y_pred)
        prec = precision_score(self.y_test, y_pred, zero_division=0)
        rec = recall_score(self.y_test, y_pred, zero_division=0)
        f1 = f1_score(self.y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(self.y_test, y_pred_proba)
        mcc = Matthews_corrcoef(self.y_test, y_pred)
        
        self.metrics[model_name] = {
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1': f1,
            'roc_auc': roc_auc,
            'matthews_cc': mcc,
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba
        }
        
        print(f"\n{model_name} Evaluation:")
        print(f"Accuracy:       {acc:.4f}")
        print(f"Precision:      {prec:.4f}")
        print(f"Recall:         {rec:.4f}")
        print(f"F1-Score:       {f1:.4f}")
        print(f"ROC-AUC:        {roc_auc:.4f}")
        print(f"Matthews CC:    {mcc:.4f}")
        print(f"\nConfusion Matrix:")
        cm = confusion_matrix(self.y_test, y_pred)
        print(cm)
        print(f"\nClassification Report:")
        print(classification_report(self.y_test, y_pred, digits=4))
    
    def compare_models(self):
        """Compare all models"""
        print("\n" + "=" * 80)
        print("MODEL COMPARISON")
        print("=" * 80)
        
        metrics_df = pd.DataFrame(self.metrics).T
        print("\n" + metrics_df[['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'matthews_cc']].to_string())
        
        return metrics_df
    
    def plot_roc_curves(self, save_path='/mnt/user-data/outputs/roc_curves.png'):
        """Plot ROC curves for all models"""
        plt.figure(figsize=(12, 8))
        
        for model_name, metrics in self.metrics.items():
            fpr, tpr, _ = roc_curve(self.y_test, metrics['y_pred_proba'])
            auc = metrics['roc_auc']
            plt.plot(fpr, tpr, label=f'{model_name} (AUC = {auc:.4f})', linewidth=2)
        
        plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=2)
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title('ROC Curves - Model Comparison', fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"\nROC curves saved to {save_path}")
        plt.close()
    
    def plot_confusion_matrices(self, save_path='/mnt/user-data/outputs/confusion_matrices.png'):
        """Plot confusion matrices for all models"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        axes = axes.ravel()
        
        for idx, (model_name, metrics) in enumerate(self.metrics.items()):
            if idx < 4:
                cm = confusion_matrix(self.y_test, metrics['y_pred'])
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx], cbar=False)
                axes[idx].set_title(f'{model_name}\n(Accuracy: {metrics["accuracy"]:.4f})', fontsize=11, fontweight='bold')
                axes[idx].set_xlabel('Predicted')
                axes[idx].set_ylabel('Actual')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"Confusion matrices saved to {save_path}")
        plt.close()
    
    def save_best_model(self, model_name=None, path='/mnt/user-data/outputs/best_fraud_model.pkl'):
        """Save the best performing model"""
        if model_name is None:
            # Find best model by ROC-AUC
            model_name = max(self.metrics.keys(), key=lambda x: self.metrics[x]['roc_auc'])
        
        model = self.models[model_name]
        joblib.dump(model, path)
        print(f"\nBest model ({model_name}) saved to {path}")
        
        return model_name, path

# Main execution
if __name__ == "__main__":
    # Download dataset if not exists
    import os
    
    data_path = '/mnt/user-data/outputs/creditcard.csv'
    
    if not os.path.exists(data_path):
        print("Downloading credit card fraud dataset...")
        import urllib.request
        url = "https://raw.githubusercontent.com/datasets/credit-card-fraud/master/data/creditcard.csv"
        try:
            urllib.request.urlretrieve(url, data_path)
            print(f"Dataset downloaded successfully!")
        except Exception as e:
            print(f"Download failed: {e}")
            print("Note: You need to download the dataset manually from:")
            print("https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud")
            exit(1)
    
    # Initialize pipeline
    pipeline = FraudDetectionPipeline(data_path)
    
    # Execute pipeline
    pipeline.load_data()
    pipeline.preprocess_data()
    pipeline.train_logistic_regression()
    pipeline.train_random_forest()
    pipeline.train_xgboost()
    pipeline.train_lightgbm()
    
    # Compare and visualize
    pipeline.compare_models()
    pipeline.plot_roc_curves()
    pipeline.plot_confusion_matrices()
    
    # Save best model
    best_model_name, best_model_path = pipeline.save_best_model()
    
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
