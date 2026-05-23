"""
Machine Learning model for behavior anomaly detection
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib
import os
from datetime import datetime
import json
from typing import Dict, List, Tuple, Any

from data_collector import DataCollector

class BehaviorAnomalyDetector:
    """Isolation Forest based anomaly detector"""
    
    def __init__(self, model_path: str = "isolation_forest.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.pca = None
        self.feature_names = []
        self.is_trained = False
        
    def train(self, data: pd.DataFrame, contamination: float = 0.1):
        """Train the Isolation Forest model"""
        if data.empty or len(data) < 10:
            raise ValueError("Insufficient data for training")
        
        # Prepare features
        X = data.values
        self.feature_names = list(data.columns)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Optional: Apply PCA for dimensionality reduction
        if X.shape[1] > 10:
            n_components = min(10, X.shape[1])
            self.pca = PCA(n_components=n_components)
            X_processed = self.pca.fit_transform(X_scaled)
        else:
            X_processed = X_scaled
        
        # Train Isolation Forest
        self.model = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=contamination,
            max_features=1.0,
            bootstrap=False,
            n_jobs=-1,
            random_state=42,
            verbose=0
        )
        
        self.model.fit(X_processed)
        self.is_trained = True
        
        # Save model
        self.save_model()
        
        # Calculate threshold (75th percentile of anomaly scores)
        scores = self.model.decision_function(X_processed)
        self.threshold_low = np.percentile(scores, 75)  # 75% of normal data
        self.threshold_high = np.percentile(scores, 90)  # 90% of normal data
        
        print(f"Model trained with {len(data)} samples")
        print(f"Features: {self.feature_names}")
        print(f"Thresholds - Low: {self.threshold_low:.3f}, High: {self.threshold_high:.3f}")
        
        return self
    
    def predict(self, features: Dict) -> Tuple[float, str, Dict]:
        """Predict anomaly score for given features"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Convert features to array in correct order
        feature_vector = []
        for feature_name in self.feature_names:
            if feature_name in features:
                feature_vector.append(features[feature_name])
            else:
                feature_vector.append(0)  # Default value for missing features
        
        X = np.array([feature_vector])
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Apply PCA if used
        if self.pca:
            X_processed = self.pca.transform(X_scaled)
        else:
            X_processed = X_scaled
        
        # Get anomaly score (higher = more normal, lower = more anomalous)
        anomaly_score = self.model.decision_function(X_processed)[0]
        
        # Convert to anomaly probability (0 = normal, 1 = anomalous)
        # Isolation Forest returns negative scores for anomalies
        # We normalize to 0-1 where 1 is highly anomalous
        anomaly_probability = 1 / (1 + np.exp(anomaly_score))
        
        # Determine risk level
        if anomaly_score < self.threshold_high:
            risk_level = "HIGH"
            alert = True
        elif anomaly_score < self.threshold_low:
            risk_level = "MEDIUM"
            alert = True
        else:
            risk_level = "LOW"
            alert = False
        
        # Feature contributions (simplified)
        feature_contributions = {}
        if len(self.feature_names) == len(feature_vector):
            for i, (name, value) in enumerate(zip(self.feature_names, feature_vector)):
                # Simple heuristic: features far from mean are suspicious
                mean_val = self.scaler.mean_[i] if i < len(self.scaler.mean_) else 0
                std_val = np.sqrt(self.scaler.var_[i]) if i < len(self.scaler.var_) else 1
                if std_val > 0:
                    z_score = abs((value - mean_val) / std_val)
                    if z_score > 2:  # More than 2 std deviations
                        feature_contributions[name] = {
                            "value": value,
                            "mean": mean_val,
                            "z_score": z_score,
                            "contribution": "high" if z_score > 3 else "medium"
                        }
        
        result = {
            "anomaly_score": float(anomaly_score),
            "anomaly_probability": float(anomaly_probability),
            "risk_level": risk_level,
            "alert": alert,
            "threshold_low": float(self.threshold_low),
            "threshold_high": float(self.threshold_high),
            "feature_contributions": feature_contributions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return anomaly_probability, risk_level, result
    
    def save_model(self):
        """Save model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'pca': self.pca,
            'feature_names': self.feature_names,
            'threshold_low': getattr(self, 'threshold_low', -0.1),
            'threshold_high': getattr(self, 'threshold_high', -0.05),
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, self.model_path)
        print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load model from disk"""
        if os.path.exists(self.model_path):
            try:
                model_data = joblib.load(self.model_path)
                
                # Validate that model_data is a dictionary with expected keys
                if not isinstance(model_data, dict):
                    print(f"Warning: Model file is corrupted (not a dict). Starting fresh.")
                    return False
                
                # Validate all required keys exist
                required_keys = ['model', 'scaler', 'feature_names', 'is_trained']
                missing_keys = [k for k in required_keys if k not in model_data]
                if missing_keys:
                    print(f"Warning: Model file missing keys: {missing_keys}. Starting fresh.")
                    return False
                
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.pca = model_data.get('pca', None)
                self.feature_names = model_data['feature_names']
                self.threshold_low = model_data.get('threshold_low', -0.1)
                self.threshold_high = model_data.get('threshold_high', -0.05)
                self.is_trained = model_data['is_trained']
                print(f"Model loaded from {self.model_path}")
                return True
            except Exception as e:
                print(f"Warning: Could not load model file: {e}. Starting fresh.")
                return False
        return False
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            "is_trained": self.is_trained,
            "feature_count": len(self.feature_names),
            "features": self.feature_names,
            "thresholds": {
                "low": float(self.threshold_low) if hasattr(self, 'threshold_low') else None,
                "high": float(self.threshold_high) if hasattr(self, 'threshold_high') else None
            },
            "model_type": "Isolation Forest",
            "last_trained": datetime.fromtimestamp(os.path.getmtime(self.model_path)).isoformat() 
                          if os.path.exists(self.model_path) else None
        }

# Global detector instance
detector = BehaviorAnomalyDetector()

def prepare_features_from_activity(activity: Dict) -> Dict:
    """Prepare features from user activity for ML model"""
    features = {}
    
    # Time-based features
    hour = activity.get('hour_of_day', datetime.utcnow().hour)
    features['hour_sin'] = np.sin(2 * np.pi * hour / 24)
    features['hour_cos'] = np.cos(2 * np.pi * hour / 24)
    
    day = activity.get('day_of_week', datetime.utcnow().weekday())
    features['day_sin'] = np.sin(2 * np.pi * day / 7)
    features['day_cos'] = np.cos(2 * np.pi * day / 7)
    
    # Session features
    features['session_duration'] = activity.get('session_duration', 0)
    features['action_count_in_session'] = activity.get('action_count_in_session', 1)
    
    # Action type features
    action_type = activity.get('action_type', 'view')
    for action in ['view', 'download', 'edit', 'delete', 'login', 'logout']:
        features[f'action_{action}'] = 1 if action_type == action else 0
    
    return features

def train_model():
    """Train the behavior anomaly detection model"""
    print("Starting model training...")
    
    # Collect training data
    data_collector = DataCollector()
    training_data = data_collector.collect_training_data()
    
    if training_data.empty:
        print("Warning: No training data available. Using sample data.")
        training_data = data_collector._generate_sample_data()
    
    print(f"Training data shape: {training_data.shape}")
    
    # Train the model
    global detector
    detector.train(training_data, contamination=0.1)
    
    # Test the model
    test_sample = training_data.iloc[0].to_dict()
    score, risk, details = detector.predict(test_sample)
    
    print(f"Test prediction - Score: {score:.3f}, Risk: {risk}")
    print("Model training completed successfully!")
    
    return detector.get_model_info()

def predict_anomaly(features: Dict) -> Dict:
    """Predict anomaly for given features"""
    global detector
    
    # Load model if not loaded
    if not detector.is_trained:
        if not detector.load_model():
            raise ValueError("Model not trained. Please train the model first.")
    
    try:
        score, risk, details = detector.predict(features)
        return details
    except Exception as e:
        print(f"Prediction error: {e}")
        # Return default safe response
        return {
            "anomaly_score": 0.0,
            "anomaly_probability": 0.0,
            "risk_level": "LOW",
            "alert": False,
            "error": str(e)
        }

def get_model_status() -> Dict:
    """Get current model status"""
    global detector
    return detector.get_model_info() if detector else {"status": "not_initialized"}