"""
Real-time anomaly detection system
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from models import UserActivity, BehaviorProfile, SecurityAlert
from ml_model import BehaviorAnomalyDetector, prepare_features_from_activity
import json

class AnomalyDetector:
    """Real-time anomaly detection and alerting system"""
    
    def __init__(self):
        self.ml_detector = BehaviorAnomalyDetector("isolation_forest.pkl")
        self.user_risk_scores = {}  # Cache for user risk scores
        self.alert_history = []     # In-memory alert history
        self.load_model()
    
    def load_model(self):
        """Load ML model if available"""
        try:
            if not self.ml_detector.load_model():
                print("Note: No trained ML model found. Using rule-based detection only.")
        except Exception as e:
            print(f"Note: Could not load ML model ({type(e).__name__}). Using rule-based detection only.")
    
    def check_anomaly(self, user_id: str) -> float:
        """
        Check for anomalies in user behavior
        Returns anomaly probability (0-1)
        """
        try:
            # Get recent activities
            recent_activities = UserActivity.get_recent_activities(user_id, hours=24)
            
            if not recent_activities:
                return 0.0  # No data, no anomaly
            
            # Calculate anomaly scores using multiple methods
            rule_score = self._rule_based_detection(user_id, recent_activities)
            ml_score = self._ml_based_detection(user_id, recent_activities)
            
            # Combine scores (weighted average)
            final_score = (rule_score * 0.4 + ml_score * 0.6)
            
            # Store in cache
            self.user_risk_scores[user_id] = {
                'score': final_score,
                'timestamp': datetime.utcnow(),
                'rule_score': rule_score,
                'ml_score': ml_score
            }
            
            # Create alert if threshold exceeded
            if final_score > 0.7:
                self._create_alert(user_id, final_score, recent_activities)
            
            return final_score
            
        except Exception as e:
            print(f"Error checking anomaly for user {user_id}: {e}")
            return 0.0
    
    def _rule_based_detection(self, user_id: str, activities: List[Dict]) -> float:
        """Rule-based anomaly detection"""
        score = 0.0
        reasons = []
        
        if not activities:
            return score
        
        # Get user behavior profile
        profile = BehaviorProfile.get_profile(user_id)
        
        # Rule 1: Unusual login time
        current_hour = datetime.utcnow().hour
        if profile and 'behavior_pattern' in profile:
            normal_hours = profile['behavior_pattern'].get('login_hours', [])
            if normal_hours and current_hour not in normal_hours:
                # Outside normal hours
                hour_diff = min([abs(current_hour - h) for h in normal_hours])
                if hour_diff > 4:  # More than 4 hours difference
                    score += 0.3
                    reasons.append(f"Unusual login time: {current_hour}:00")
        
        # Rule 2: High frequency of actions
        last_hour_activities = [
            a for a in activities 
            if a['timestamp'] > datetime.utcnow() - timedelta(hours=1)
        ]
        
        if len(last_hour_activities) > 50:  # More than 50 actions per hour
            score += min(0.4, len(last_hour_activities) / 200)
            reasons.append(f"High action frequency: {len(last_hour_activities)} actions/hour")
        
        # Rule 3: Unusual action types
        action_counts = {}
        for activity in activities[:100]:  # Check last 100 activities
            action_type = activity.get('action_type', 'unknown')
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        total_actions = sum(action_counts.values())
        if total_actions > 0:
            # Check for rare actions
            for action_type, count in action_counts.items():
                frequency = count / total_actions
                if action_type in ['delete', 'admin', 'config'] and frequency > 0.1:
                    score += 0.2
                    reasons.append(f"Unusual frequency of {action_type} actions")
        
        # Rule 4: Very short or very long sessions
        for activity in activities:
            if activity.get('action_type') == 'logout':
                session_duration = activity.get('details', {}).get('session_duration', 0)
                if session_duration < 60:  # Less than 1 minute
                    score += 0.15
                    reasons.append("Very short session detected")
                elif session_duration > 36000:  # More than 10 hours
                    score += 0.15
                    reasons.append("Very long session detected")
        
        # Rule 5: Rapid succession of critical actions
        critical_actions = ['delete', 'edit', 'download']
        critical_count = 0
        last_time = None
        
        for activity in sorted(activities, key=lambda x: x['timestamp']):
            if activity.get('action_type') in critical_actions:
                if last_time:
                    time_diff = (activity['timestamp'] - last_time).total_seconds()
                    if time_diff < 30:  # Less than 30 seconds between critical actions
                        critical_count += 1
                last_time = activity['timestamp']
        
        if critical_count > 3:
            score += min(0.3, critical_count * 0.1)
            reasons.append(f"Rapid critical actions: {critical_count} in short period")
        
        # Cap score at 1.0
        final_score = min(score, 1.0)
        
        # Store detection details
        if reasons and final_score > 0.3:
            self._log_detection(user_id, 'rule_based', final_score, reasons)
        
        return final_score
    
    def _ml_based_detection(self, user_id: str, activities: List[Dict]) -> float:
        """ML-based anomaly detection"""
        if not self.ml_detector.is_trained:
            return 0.0
        
        try:
            # Use the most recent activity for ML prediction
            if not activities:
                return 0.0
            
            latest_activity = activities[0]
            features = prepare_features_from_activity(latest_activity)
            
            # Get prediction - returns tuple (anomaly_probability, risk_level, result_dict)
            anomaly_probability, risk_level, result_dict = self.ml_detector.predict(features)
            
            # Adjust based on historical consistency
            if len(activities) > 10:
                # Check if this is part of a pattern
                recent_scores = []
                for activity in activities[:10]:
                    try:
                        act_features = prepare_features_from_activity(activity)
                        act_prob, _, _ = self.ml_detector.predict(act_features)
                        recent_scores.append(act_prob)
                    except:
                        continue
                
                if recent_scores:
                    avg_recent = np.mean(recent_scores)
                    # If consistently anomalous, increase score
                    if avg_recent > 0.6 and anomaly_probability > 0.5:
                        anomaly_probability = min(1.0, anomaly_probability * 1.2)
            
            # Log if anomaly detected
            if anomaly_probability > 0.7:
                self._log_detection(
                    user_id, 
                    'ml_based', 
                    anomaly_probability,
                    [f"ML anomaly score: {anomaly_probability:.2f}"]
                )
            
            return anomaly_probability
            
        except Exception as e:
            print(f"ML detection error for user {user_id}: {e}")
            return 0.0
    
    def _create_alert(self, user_id: str, score: float, activities: List[Dict]):
        """Create security alert"""
        # Determine severity
        if score > 0.9:
            severity = "High"
            alert_type = "Critical Anomaly"
        elif score > 0.7:
            severity = "Medium"
            alert_type = "Suspicious Behavior"
        else:
            severity = "Low"
            alert_type = "Unusual Activity"
        
        # Get recent activity summary
        recent_summary = []
        for activity in activities[:5]:
            recent_summary.append({
                'action': activity.get('action_type'),
                'time': activity.get('timestamp').isoformat() if activity.get('timestamp') else None,
                'resource': activity.get('resource')
            })
        
        # Create alert data
        alert_data = {
            "user_id": user_id,
            "alert_type": alert_type,
            "severity": severity,
            "anomaly_score": score,
            "description": f"Anomaly detected with score: {score:.2f}",
            "detection_method": "Combined (Rules + ML)",
            "recent_activities": recent_summary,
            "status": "active",
            "created_at": datetime.utcnow(),
            "recommended_action": self._get_recommended_action(score)
        }
        
        # Save to database
        alert_id = SecurityAlert.create(alert_data)
        
        # Store in memory cache
        self.alert_history.append({
            "alert_id": alert_id,
            "user_id": user_id,
            "score": score,
            "timestamp": datetime.utcnow(),
            "severity": severity
        })
        
        # Keep only last 100 alerts in memory
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        print(f"Alert created for user {user_id}: {alert_type} (Score: {score:.2f})")
    
    def _get_recommended_action(self, score: float) -> str:
        """Get recommended action based on anomaly score"""
        if score > 0.9:
            return "Immediate session termination and administrator notification"
        elif score > 0.7:
            return "Enhanced monitoring and user verification required"
        elif score > 0.5:
            return "Monitor user activity and check for pattern changes"
        else:
            return "No action required - continue monitoring"
    
    def _log_detection(self, user_id: str, method: str, score: float, reasons: List[str]):
        """Log detection details for analysis"""
        log_entry = {
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "detection_method": method,
            "score": score,
            "reasons": reasons,
            "action_taken": "alert_created" if score > 0.7 else "logged_only"
        }
        
        # In production, save to database
        # For now, just print
        if score > 0.5:
            print(f"[ANOMALY DETECTED] User: {user_id}, Method: {method}, Score: {score:.2f}")
            for reason in reasons:
                print(f"  - {reason}")
    
    def get_user_anomaly_score(self, user_id: str) -> float:
        """Get cached anomaly score for user"""
        if user_id in self.user_risk_scores:
            cache_entry = self.user_risk_scores[user_id]
            # Check if cache is fresh (last 5 minutes)
            if datetime.utcnow() - cache_entry['timestamp'] < timedelta(minutes=5):
                return cache_entry['score']
        
        # If no cache or stale, calculate new score
        return self.check_anomaly(user_id)
    
    def get_user_risk_profile(self, user_id: str) -> Dict:
        """Get comprehensive risk profile for user"""
        score = self.get_user_anomaly_score(user_id)
        
        # Get recent alerts
        recent_alerts = SecurityAlert.find_by_user(user_id, limit=5)
        
        # Get behavior statistics
        recent_activities = UserActivity.get_recent_activities(user_id, hours=24)
        
        # Calculate statistics
        stats = {
            "total_actions_24h": len(recent_activities),
            "unique_resources": len(set(a.get('resource', '') for a in recent_activities)),
            "action_types": {},
            "peak_hour": None
        }
        
        # Count action types
        for activity in recent_activities:
            action_type = activity.get('action_type', 'unknown')
            stats["action_types"][action_type] = stats["action_types"].get(action_type, 0) + 1
        
        # Find peak activity hour
        if recent_activities:
            hour_counts = {}
            for activity in recent_activities:
                hour = activity.get('timestamp').hour if activity.get('timestamp') else 0
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            if hour_counts:
                stats["peak_hour"] = max(hour_counts.items(), key=lambda x: x[1])[0]
        
        # Determine risk level
        if score > 0.8:
            risk_level = "CRITICAL"
            color = "red"
        elif score > 0.6:
            risk_level = "HIGH"
            color = "orange"
        elif score > 0.4:
            risk_level = "MEDIUM"
            color = "yellow"
        elif score > 0.2:
            risk_level = "LOW"
            color = "blue"
        else:
            risk_level = "NORMAL"
            color = "green"
        
        return {
            "user_id": user_id,
            "current_score": score,
            "risk_level": risk_level,
            "risk_color": color,
            "last_updated": datetime.utcnow().isoformat(),
            "recent_alerts": recent_alerts,
            "activity_stats": stats,
            "recommendations": self._get_user_recommendations(score, stats)
        }
    
    def _get_user_recommendations(self, score: float, stats: Dict) -> List[str]:
        """Get personalized recommendations based on risk profile"""
        recommendations = []
        
        if score > 0.7:
            recommendations.append("Immediate review of recent activities required")
            recommendations.append("Consider temporary access restrictions")
        
        if stats.get("total_actions_24h", 0) > 100:
            recommendations.append("High activity volume detected - verify legitimate use")
        
        if 'delete' in stats.get("action_types", {}) and stats["action_types"]['delete'] > 5:
            recommendations.append("Multiple delete operations - review data integrity")
        
        if not recommendations and score > 0.4:
            recommendations.append("Continue monitoring for pattern changes")
        
        if not recommendations:
            recommendations.append("Normal behavior pattern detected")
        
        return recommendations
    
    def get_system_analytics(self) -> Dict:
        """Get system-wide analytics"""
        # Count active alerts by severity
        all_alerts = []
        # In production, query database
        # For demo, use in-memory cache
        
        high_risk_users = [
            user_id for user_id, data in self.user_risk_scores.items()
            if data['score'] > 0.7
        ]
        
        return {
            "total_monitored_users": len(self.user_risk_scores),
            "high_risk_users": len(high_risk_users),
            "total_alerts_24h": len(self.alert_history),
            "avg_anomaly_score": np.mean([d['score'] for d in self.user_risk_scores.values()]) 
                                if self.user_risk_scores else 0,
            "ml_model_status": "active" if self.ml_detector.is_trained else "inactive",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def simulate_attack(self, user_id: str, attack_type: str) -> Dict:
        """Simulate different types of attacks for testing"""
        simulation_results = {
            "attack_type": attack_type,
            "timestamp": datetime.utcnow().isoformat(),
            "activities_simulated": [],
            "final_score": 0.0,
            "alerts_triggered": []
        }
        
        # Simulate based on attack type
        if attack_type == "insider_threat":
            # Simulate unusual working hours and excessive downloads
            activities = []
            # Late night login
            activities.append({
                "action_type": "login",
                "hour_of_day": 2,  # 2 AM
                "session_duration": 7200,  # 2 hours
                "action_count_in_session": 1
            })
            # Multiple downloads
            for i in range(20):
                activities.append({
                    "action_type": "download",
                    "hour_of_day": 3,
                    "session_duration": 7200 + i*300,
                    "action_count_in_session": i+2
                })
            
            simulation_results["activities_simulated"] = activities
            
            # Calculate anomaly score
            rule_score = 0.8  # High due to unusual time
            ml_score = 0.7    # ML would detect pattern
            final_score = (rule_score * 0.4 + ml_score * 0.6)
            
        elif attack_type == "credential_stuffing":
            # Rapid login attempts
            activities = []
            for i in range(15):
                activities.append({
                    "action_type": "login",
                    "hour_of_day": datetime.utcnow().hour,
                    "session_duration": 60,  # Very short sessions
                    "action_count_in_session": 1
                })
            
            simulation_results["activities_simulated"] = activities
            final_score = 0.9  # Very high probability
            
        elif attack_type == "data_exfiltration":
            # Large number of view/download actions
            activities = []
            for i in range(100):
                activities.append({
                    "action_type": "download" if i % 5 == 0 else "view",
                    "hour_of_day": datetime.utcnow().hour,
                    "session_duration": 18000,  # 5 hours
                    "action_count_in_session": i+1
                })
            
            simulation_results["activities_simulated"] = activities
            final_score = 0.85
        
        else:
            final_score = 0.0
        
        simulation_results["final_score"] = final_score
        
        # Trigger alert if score is high
        if final_score > 0.7:
            alert_type = "HIGH" if final_score > 0.8 else "MEDIUM"
            simulation_results["alerts_triggered"].append({
                "severity": alert_type,
                "message": f"Simulated {attack_type} detected with score {final_score:.2f}"
            })
        
        return simulation_results