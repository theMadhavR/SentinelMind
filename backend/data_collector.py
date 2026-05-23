"""
Data collection for user behavior tracking
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import json
from models import UserActivity, BehaviorProfile
import pandas as pd
import numpy as np

class DataCollector:
    """Collects and processes user behavior data"""
    
    def __init__(self):
        self.user_sessions = {}  # In-memory session tracking
    
    def track_login(self, user_id: str, username: str, device: str, 
                   location: str, ip_address: str) -> Dict:
        """Track user login activity"""
        
        # Generate session ID
        session_id = hashlib.md5(
            f"{user_id}{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()[:16]
        
        # Store session info
        self.user_sessions[user_id] = {
            "session_id": session_id,
            "login_time": datetime.utcnow(),
            "device": device,
            "location": location,
            "ip_address": ip_address,
            "action_count": 0,
            "last_action_time": datetime.utcnow()
        }
        
        # Log the activity
        activity_data = {
            "user_id": user_id,
            "username": username,
            "session_id": session_id,
            "action_type": "login",
            "resource": "system",
            "details": {
                "device": device,
                "location": location,
                "ip_address": ip_address,
                "user_agent": "Web Browser"
            },
            "timestamp": datetime.utcnow(),
            "hour_of_day": datetime.utcnow().hour,
            "day_of_week": datetime.utcnow().weekday()
        }
        
        activity_id = UserActivity.create(activity_data)
        activity_data["_id"] = activity_id
        
        # Initialize/update behavior profile
        self._update_behavior_profile(user_id, "login")
        
        return activity_data
    
    def track_action(self, user_id: str, action_type: str, 
                    resource: str, details: Dict = None) -> Dict:
        """Track user action (view, download, edit, delete, etc.)"""
        
        if user_id not in self.user_sessions:
            # Create a session if not exists (for demo purposes)
            self.user_sessions[user_id] = {
                "session_id": hashlib.md5(f"{user_id}{datetime.utcnow()}".encode()).hexdigest()[:16],
                "login_time": datetime.utcnow(),
                "device": "Unknown",
                "location": "Unknown",
                "ip_address": "127.0.0.1",
                "action_count": 0,
                "last_action_time": datetime.utcnow()
            }
        
        # Update session info
        session = self.user_sessions[user_id]
        session["action_count"] += 1
        session["last_action_time"] = datetime.utcnow()
        
        # Calculate session duration
        session_duration = (datetime.utcnow() - session["login_time"]).total_seconds()
        
        # Log the activity
        activity_data = {
            "user_id": user_id,
            "session_id": session["session_id"],
            "action_type": action_type,
            "resource": resource,
            "details": details or {},
            "timestamp": datetime.utcnow(),
            "hour_of_day": datetime.utcnow().hour,
            "day_of_week": datetime.utcnow().weekday(),
            "session_duration": session_duration,
            "action_count_in_session": session["action_count"]
        }
        
        activity_id = UserActivity.create(activity_data)
        activity_data["_id"] = activity_id
        
        # Update behavior profile
        self._update_behavior_profile(user_id, action_type)
        
        return activity_data
    
    def track_logout(self, user_id: str) -> Optional[Dict]:
        """Track user logout"""
        if user_id not in self.user_sessions:
            return None
        
        session = self.user_sessions[user_id]
        session_duration = (datetime.utcnow() - session["login_time"]).total_seconds()
        
        # Log the activity
        activity_data = {
            "user_id": user_id,
            "session_id": session["session_id"],
            "action_type": "logout",
            "resource": "system",
            "details": {
                "session_duration": session_duration,
                "total_actions": session["action_count"],
                "device": session["device"],
                "location": session["location"]
            },
            "timestamp": datetime.utcnow(),
            "hour_of_day": datetime.utcnow().hour,
            "day_of_week": datetime.utcnow().weekday()
        }
        
        activity_id = UserActivity.create(activity_data)
        
        # Remove session
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        # Update behavior profile with session info
        self._update_session_profile(user_id, session_duration, session["action_count"])
        
        return activity_data
    
    def _update_behavior_profile(self, user_id: str, action_type: str):
        """Update user behavior profile"""
        # Get existing profile or create new
        profile = BehaviorProfile.get_profile(user_id) or {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "behavior_pattern": self._initialize_pattern(),
            "action_counts": {},
            "hourly_pattern": {},
            "session_stats": {
                "total_sessions": 0,
                "avg_session_duration": 0,
                "avg_actions_per_session": 0
            }
        }
        
        # Update action counts
        action_counts = profile.get("action_counts", {})
        action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        # Update hourly pattern
        current_hour = datetime.utcnow().hour
        hourly_pattern = profile.get("hourly_pattern", {})
        hourly_pattern[str(current_hour)] = hourly_pattern.get(str(current_hour), 0) + 1
        
        # Update profile
        profile["action_counts"] = action_counts
        profile["hourly_pattern"] = hourly_pattern
        profile["last_updated"] = datetime.utcnow()
        
        # Calculate behavior pattern
        profile["behavior_pattern"] = self._calculate_pattern(profile)
        
        # Save to database
        BehaviorProfile.create_or_update(profile)
    
    def _update_session_profile(self, user_id: str, session_duration: float, action_count: int):
        """Update session statistics in behavior profile"""
        profile = BehaviorProfile.get_profile(user_id)
        if not profile:
            return
        
        session_stats = profile.get("session_stats", {
            "total_sessions": 0,
            "avg_session_duration": 0,
            "avg_actions_per_session": 0
        })
        
        # Update session statistics using moving average
        total_sessions = session_stats["total_sessions"] + 1
        old_avg_duration = session_stats["avg_session_duration"]
        old_avg_actions = session_stats["avg_actions_per_session"]
        
        # Calculate new averages
        new_avg_duration = (old_avg_duration * session_stats["total_sessions"] + session_duration) / total_sessions
        new_avg_actions = (old_avg_actions * session_stats["total_sessions"] + action_count) / total_sessions
        
        session_stats.update({
            "total_sessions": total_sessions,
            "avg_session_duration": new_avg_duration,
            "avg_actions_per_session": new_avg_actions,
            "last_session_duration": session_duration,
            "last_session_actions": action_count
        })
        
        profile["session_stats"] = session_stats
        profile["last_updated"] = datetime.utcnow()
        
        BehaviorProfile.create_or_update(profile)
    
    def _initialize_pattern(self) -> Dict:
        """Initialize behavior pattern"""
        return {
            "login_hours": [],
            "common_actions": [],
            "avg_session_duration": 0,
            "avg_actions_per_hour": 0,
            "action_frequency": {},
            "device_pattern": [],
            "location_pattern": []
        }
    
    def _calculate_pattern(self, profile: Dict) -> Dict:
        """Calculate behavior pattern from profile data"""
        # Analyze hourly pattern
        hourly_pattern = profile.get("hourly_pattern", {})
        if hourly_pattern:
            active_hours = sorted(
                [int(hour) for hour, count in hourly_pattern.items() if count > 0],
                key=lambda x: hourly_pattern.get(str(x), 0),
                reverse=True
            )[:5]  # Top 5 active hours
        else:
            active_hours = []
        
        # Analyze common actions
        action_counts = profile.get("action_counts", {})
        if action_counts:
            common_actions = sorted(
                action_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]  # Top 5 common actions
            common_actions = [action for action, _ in common_actions]
        else:
            common_actions = []
        
        # Calculate action frequency
        total_actions = sum(action_counts.values())
        action_frequency = {
            action: count / total_actions if total_actions > 0 else 0
            for action, count in action_counts.items()
        }
        
        # Get session stats
        session_stats = profile.get("session_stats", {})
        
        return {
            "login_hours": active_hours,
            "common_actions": common_actions,
            "avg_session_duration": session_stats.get("avg_session_duration", 0),
            "avg_actions_per_hour": session_stats.get("avg_actions_per_session", 0) / 24 if session_stats.get("avg_actions_per_session", 0) > 0 else 0,
            "action_frequency": action_frequency,
            "device_pattern": ["Web Browser"],  # Default for now
            "location_pattern": ["Unknown"],    # Default for now
            "pattern_confidence": self._calculate_confidence(profile)
        }
    
    def _calculate_confidence(self, profile: Dict) -> float:
        """Calculate confidence score for behavior pattern"""
        # More data = higher confidence
        total_actions = sum(profile.get("action_counts", {}).values())
        total_sessions = profile.get("session_stats", {}).get("total_sessions", 0)
        
        # Simple confidence calculation
        action_confidence = min(total_actions / 100, 1.0)  # Cap at 100 actions
        session_confidence = min(total_sessions / 10, 1.0)  # Cap at 10 sessions
        
        return (action_confidence * 0.6 + session_confidence * 0.4)
    
    def get_user_behavior_profile(self, user_id: str) -> Dict:
        """Get comprehensive behavior profile for user"""
        # Get from database
        profile = BehaviorProfile.get_profile(user_id)
        
        if not profile:
            return {
                "user_id": user_id,
                "status": "No profile available",
                "confidence": 0,
                "suggestion": "Continue normal activities to build profile"
            }
        
        # Get recent activities
        recent_activities = UserActivity.find_by_user(user_id, limit=20)
        
        # Calculate current session info
        current_session = self.user_sessions.get(user_id, {})
        
        return {
            "profile": profile.get("behavior_pattern", {}),
            "statistics": {
                "total_actions": sum(profile.get("action_counts", {}).values()),
                "total_sessions": profile.get("session_stats", {}).get("total_sessions", 0),
                "avg_session_duration_minutes": round(profile.get("session_stats", {}).get("avg_session_duration", 0) / 60, 2),
                "avg_actions_per_session": round(profile.get("session_stats", {}).get("avg_actions_per_session", 0), 2)
            },
            "current_session": {
                "active": user_id in self.user_sessions,
                "duration_minutes": round((datetime.utcnow() - current_session.get("login_time", datetime.utcnow())).total_seconds() / 60, 2) if current_session else 0,
                "action_count": current_session.get("action_count", 0),
                "device": current_session.get("device", "Unknown")
            },
            "confidence_score": profile.get("behavior_pattern", {}).get("pattern_confidence", 0),
            "recent_activities": recent_activities[:5],  # Last 5 activities
            "last_updated": profile.get("last_updated")
        }
    
    def collect_training_data(self, user_ids: List[str] = None) -> pd.DataFrame:
        """Collect data for ML training"""
        all_activities = []
        
        if user_ids:
            for user_id in user_ids:
                activities = UserActivity.find_by_user(user_id, limit=1000)
                all_activities.extend(activities)
        else:
            # Get all activities (for demo, limit to 5000)
            # In production, use proper pagination
            pass
        
        if not all_activities:
            # Generate sample data for demo
            return self._generate_sample_data()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_activities)
        
        # Feature engineering
        df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day']/24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day']/24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week']/7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week']/7)
        
        # Encode action types
        action_types = df['action_type'].unique()
        for i, action in enumerate(action_types):
            df[f'action_{action}'] = (df['action_type'] == action).astype(int)
        
        # Select features for ML
        features = [
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
            'session_duration', 'action_count_in_session'
        ]
        
        # Add action type features
        for action in action_types:
            if f'action_{action}' in df.columns:
                features.append(f'action_{action}')
        
        return df[features].fillna(0)
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """Generate sample data for demo/testing"""
        np.random.seed(42)
        
        # Generate normal behavior data
        n_samples = 1000
        data = {
            'hour_sin': np.sin(2 * np.pi * np.random.normal(14, 3, n_samples) / 24),
            'hour_cos': np.cos(2 * np.pi * np.random.normal(14, 3, n_samples) / 24),
            'day_sin': np.sin(2 * np.pi * np.random.randint(0, 7, n_samples) / 7),
            'day_cos': np.cos(2 * np.pi * np.random.randint(0, 7, n_samples) / 7),
            'session_duration': np.random.normal(1800, 600, n_samples),  # ~30 min avg
            'action_count_in_session': np.random.poisson(15, n_samples)  # ~15 actions avg
        }
        
        # Add action type features (simulate normal behavior)
        data['action_view'] = np.random.binomial(1, 0.6, n_samples)
        data['action_download'] = np.random.binomial(1, 0.2, n_samples)
        data['action_edit'] = np.random.binomial(1, 0.15, n_samples)
        data['action_delete'] = np.random.binomial(1, 0.05, n_samples)
        
        return pd.DataFrame(data)