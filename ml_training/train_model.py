"""
Training script for behavior anomaly detection model
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import json
from datetime import datetime
from backend.data_collector import DataCollector
from backend.ml_model import train_model, BehaviorAnomalyDetector

def generate_training_data():
    """Generate comprehensive training data"""
    print("Generating training data...")
    
    # Initialize data collector
    collector = DataCollector()
    
    # Generate normal behavior data
    normal_data = collector._generate_sample_data()
    
    # Generate anomalous behavior data (20% contamination)
    n_anomalous = len(normal_data) // 5
    
    anomalous_data = pd.DataFrame({
        'hour_sin': np.sin(2 * np.pi * np.random.uniform(0, 6, n_anomalous) / 24),  # Night hours
        'hour_cos': np.cos(2 * np.pi * np.random.uniform(0, 6, n_anomalous) / 24),
        'day_sin': np.sin(2 * np.pi * np.random.choice([5, 6], n_anomalous) / 7),  # Weekend
        'day_cos': np.cos(2 * np.pi * np.random.choice([5, 6], n_anomalous) / 7),
        'session_duration': np.random.uniform(10, 300, n_anomalous),  # Very short sessions
        'action_count_in_session': np.random.poisson(50, n_anomalous),  # High action count
        'action_view': np.random.binomial(1, 0.3, n_anomalous),
        'action_download': np.random.binomial(1, 0.5, n_anomalous),  # High download rate
        'action_edit': np.random.binomial(1, 0.4, n_anomalous),
        'action_delete': np.random.binomial(1, 0.3, n_anomalous)  # High delete rate
    })
    
    # Combine data
    combined_data = pd.concat([normal_data, anomalous_data], ignore_index=True)
    
    # Shuffle the data
    combined_data = combined_data.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"Generated {len(normal_data)} normal samples and {len(anomalous_data)} anomalous samples")
    print(f"Total training samples: {len(combined_data)}")
    
    return combined_data

def evaluate_model(detector: BehaviorAnomalyDetector, test_data: pd.DataFrame):
    """Evaluate model performance"""
    print("\nEvaluating model...")
    
    # Split data (first 80% normal, last 20% anomalous for testing)
    split_idx = int(len(test_data) * 0.8)
    normal_test = test_data[:split_idx]
    anomalous_test = test_data[split_idx:]
    
    # Test on normal data
    normal_scores = []
    for _, row in normal_test.iterrows():
        features = row.to_dict()
        score, _, _ = detector.predict(features)
        normal_scores.append(score)
    
    # Test on anomalous data
    anomalous_scores = []
    for _, row in anomalous_test.iterrows():
        features = row.to_dict()
        score, _, _ = detector.predict(features)
        anomalous_scores.append(score)
    
    # Calculate metrics
    normal_mean = np.mean(normal_scores)
    normal_std = np.std(normal_scores)
    anomalous_mean = np.mean(anomalous_scores)
    anomalous_std = np.std(anomalous_scores)
    
    # Calculate separation (higher is better)
    separation = (anomalous_mean - normal_mean) / (normal_std + anomalous_std)
    
    print(f"Normal data - Mean score: {normal_mean:.3f}, Std: {normal_std:.3f}")
    print(f"Anomalous data - Mean score: {anomalous_mean:.3f}, Std: {anomalous_std:.3f}")
    print(f"Separation score: {separation:.3f}")
    
    # Calculate detection rate at different thresholds
    thresholds = [0.3, 0.5, 0.7, 0.9]
    for threshold in thresholds:
        normal_detected = sum(1 for s in normal_scores if s > threshold)
        anomalous_detected = sum(1 for s in anomalous_scores if s > threshold)
        
        false_positive_rate = normal_detected / len(normal_scores)
        true_positive_rate = anomalous_detected / len(anomalous_scores)
        
        print(f"\nThreshold {threshold}:")
        print(f"  False Positive Rate: {false_positive_rate:.3f}")
        print(f"  True Positive Rate: {true_positive_rate:.3f}")
    
    return {
        "normal_mean": float(normal_mean),
        "normal_std": float(normal_std),
        "anomalous_mean": float(anomalous_mean),
        "anomalous_std": float(anomalous_std),
        "separation": float(separation),
        "evaluation_time": datetime.utcnow().isoformat()
    }

def save_training_report(model_info: dict, evaluation_results: dict):
    """Save training report"""
    report = {
        "training_info": model_info,
        "evaluation_results": evaluation_results,
        "training_time": datetime.utcnow().isoformat(),
        "model_details": {
            "algorithm": "Isolation Forest",
            "contamination": 0.1,
            "n_estimators": 100,
            "features_used": model_info.get("features", [])
        }
    }
    
    report_path = os.path.join(os.path.dirname(__file__), "training_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nTraining report saved to: {report_path}")
    return report

def main():
    """Main training function"""
    print("=" * 60)
    print("BEHAVIOR ANOMALY DETECTION MODEL TRAINING")
    print("=" * 60)
    
    # Step 1: Generate training data
    training_data = generate_training_data()
    
    # Step 2: Train the model
    print("\nTraining model...")
    detector = BehaviorAnomalyDetector()
    detector.train(training_data, contamination=0.1)
    
    # Step 3: Get model info
    model_info = detector.get_model_info()
    print(f"\nModel trained successfully!")
    print(f"Features: {len(model_info['features'])}")
    print(f"Threshold - Low: {model_info['thresholds']['low']:.3f}")
    print(f"Threshold - High: {model_info['thresholds']['high']:.3f}")
    
    # Step 4: Evaluate model
    evaluation_results = evaluate_model(detector, training_data)
    
    # Step 5: Save report
    report = save_training_report(model_info, evaluation_results)
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    # Test with sample predictions
    print("\nSample predictions:")
    print("-" * 40)
    
    # Normal behavior sample
    normal_sample = {
        'hour_sin': np.sin(2 * np.pi * 14 / 24),  # 2 PM
        'hour_cos': np.cos(2 * np.pi * 14 / 24),
        'day_sin': np.sin(2 * np.pi * 2 / 7),  # Tuesday
        'day_cos': np.cos(2 * np.pi * 2 / 7),
        'session_duration': 1800,  # 30 minutes
        'action_count_in_session': 15,
        'action_view': 1,
        'action_download': 0,
        'action_edit': 0,
        'action_delete': 0
    }
    
    score, risk, details = detector.predict(normal_sample)
    print(f"Normal behavior sample:")
    print(f"  Score: {score:.3f}, Risk: {risk}")
    
    # Anomalous behavior sample
    anomalous_sample = {
        'hour_sin': np.sin(2 * np.pi * 3 / 24),  # 3 AM
        'hour_cos': np.cos(2 * np.pi * 3 / 24),
        'day_sin': np.sin(2 * np.pi * 6 / 7),  # Sunday
        'day_cos': np.cos(2 * np.pi * 6 / 7),
        'session_duration': 60,  # 1 minute
        'action_count_in_session': 100,
        'action_view': 0,
        'action_download': 1,
        'action_edit': 0,
        'action_delete': 1
    }
    
    score, risk, details = detector.predict(anomalous_sample)
    print(f"\nAnomalous behavior sample:")
    print(f"  Score: {score:.3f}, Risk: {risk}")
    
    return detector

if __name__ == "__main__":
    main()