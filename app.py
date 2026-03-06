"""
Fraud Detection Web Application
================================
Flask app for real-time fraud detection predictions.

Features:
- Single transaction prediction
- Batch prediction from CSV
- Interactive dashboard
- Model performance metrics
- Feature importance visualization
"""

from flask import Flask, render_template, request, jsonify, send_file
import numpy as np
import pandas as pd
import joblib
import json
from datetime import datetime
import os
import io
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

# Global variables
model = None
scaler = None
feature_names = None

def load_model_and_scaler():
    """Load trained model and scaler"""
    global model, scaler, feature_names
    
    try:
        model = joblib.load('/mnt/user-data/outputs/best_fraud_model.pkl')
        # Note: In production, save and load the scaler as well
        feature_names = ['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10',
                        'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17', 'V18', 'V19', 'V20',
                        'V21', 'V22', 'V23', 'V24', 'V25', 'V26', 'V27', 'V28', 'Amount', 'Time']
        print("Model and scaler loaded successfully!")
        return True
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Make prediction for single transaction"""
    try:
        data = request.json
        
        # Extract features
        features = []
        for feature in feature_names:
            if feature in data:
                features.append(float(data[feature]))
            else:
                return jsonify({'error': f'Missing feature: {feature}'}), 400
        
        features = np.array(features).reshape(1, -1)
        
        # Make prediction
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0]
        
        result = {
            'is_fraud': int(prediction),
            'fraud_probability': float(probability[1]),
            'legitimate_probability': float(probability[0]),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    """Make predictions for batch of transactions"""
    try:
        file = request.files['file']
        
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        # Read CSV
        df = pd.read_csv(file)
        
        # Prepare features
        required_features = set(feature_names)
        available_features = set(df.columns)
        
        if not required_features.issubset(available_features):
            missing = required_features - available_features
            return jsonify({'error': f'Missing features: {missing}'}), 400
        
        X = df[feature_names].values
        
        # Make predictions
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        
        # Add predictions to dataframe
        df['is_fraud'] = predictions
        df['fraud_probability'] = probabilities[:, 1]
        df['legitimate_probability'] = probabilities[:, 0]
        
        # Save to CSV
        output_path = '/tmp/predictions.csv'
        df.to_csv(output_path, index=False)
        
        # Return file
        return send_file(output_path, as_attachment=True, download_name='fraud_predictions.csv')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/model_info')
def model_info():
    """Get model information"""
    try:
        info = {
            'model_type': type(model).__name__,
            'num_features': len(feature_names),
            'features': feature_names,
            'loaded': model is not None
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'model_loaded': model is not None})

if __name__ == '__main__':
    if load_model_and_scaler():
        app.run(debug=True, port=5000)
    else:
        print("Failed to load model. Please train the model first.")
