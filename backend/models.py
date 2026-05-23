"""
Database models for MongoDB
"""
from pymongo import MongoClient
from datetime import datetime
from typing import Optional, List, Dict, Any
import os
from bson import ObjectId

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "cybersecurity_db"

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Collections
users_collection = db["users"]
activities_collection = db["user_activities"]
alerts_collection = db["security_alerts"]
behavior_profiles_collection = db["behavior_profiles"]

class User:
    """User model"""
    
    @staticmethod
    def create_indexes():
        """Create indexes for performance"""
        users_collection.create_index("username", unique=True)
        users_collection.create_index("email", unique=True)
        activities_collection.create_index([("user_id", 1), ("timestamp", -1)])
        alerts_collection.create_index([("user_id", 1), ("created_at", -1)])
    
    @staticmethod
    def find_by_username(username: str) -> Optional[Dict]:
        """Find user by username"""
        return users_collection.find_one({"username": username})
    
    @staticmethod
    def find_by_id(user_id: str) -> Optional[Dict]:
        """Find user by ID"""
        return users_collection.find_one({"_id": ObjectId(user_id)})
    
    @staticmethod
    def create(user_data: Dict) -> str:
        """Create a new user"""
        result = users_collection.insert_one(user_data)
        return str(result.inserted_id)
    
    def save(self):
        """Save user to database"""
        user_dict = self.__dict__.copy()
        # Remove _id if it's None to avoid errors
        if '_id' in user_dict and user_dict['_id'] is None:
            del user_dict['_id']
        
        if hasattr(self, '_id') and self._id:
            users_collection.update_one({"_id": self._id}, {"$set": user_dict})
        else:
            result = users_collection.insert_one(user_dict)
            self._id = result.inserted_id
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class UserActivity:
    """User activity logging model"""
    
    @staticmethod
    def create(activity_data: Dict) -> str:
        """Create a new activity log"""
        result = activities_collection.insert_one(activity_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_user(user_id: str, limit: int = 100) -> List[Dict]:
        """Find activities by user"""
        activities = activities_collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)
        return list(activities)
    
    @staticmethod
    def get_recent_activities(user_id: str, hours: int = 24) -> List[Dict]:
        """Get recent activities within specified hours"""
        from datetime import datetime, timedelta
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        activities = activities_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": time_threshold}
        }).sort("timestamp", -1)
        
        return list(activities)
    
    @staticmethod
    def get_user_stats(user_id: str) -> Dict:
        """Get user activity statistics"""
        # Total actions
        total_actions = activities_collection.count_documents({"user_id": user_id})
        
        # Actions today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_actions = activities_collection.count_documents({
            "user_id": user_id,
            "timestamp": {"$gte": today_start}
        })
        
        # Action types distribution
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        action_distribution = list(activities_collection.aggregate(pipeline))
        
        # Average session duration
        login_activities = list(activities_collection.find({
            "user_id": user_id,
            "action_type": "login"
        }).sort("timestamp", -1).limit(10))
        
        avg_session_duration = 0
        if login_activities:
            sessions = []
            for login in login_activities:
                logout = activities_collection.find_one({
                    "user_id": user_id,
                    "action_type": "logout",
                    "timestamp": {"$gt": login['timestamp']}
                })
                if logout:
                    session_duration = (logout['timestamp'] - login['timestamp']).total_seconds()
                    sessions.append(session_duration)
            
            if sessions:
                avg_session_duration = sum(sessions) / len(sessions)
        
        return {
            "total_actions": total_actions,
            "today_actions": today_actions,
            "action_distribution": action_distribution,
            "avg_session_duration": avg_session_duration
        }

class SecurityAlert:
    """Security alert model"""
    
    SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]
    
    @staticmethod
    def create(alert_data: Dict) -> str:
        """Create a new security alert"""
        result = alerts_collection.insert_one(alert_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_user(user_id: str, limit: int = 20) -> List[Dict]:
        """Find alerts by user"""
        alerts = alerts_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)
        return list(alerts)
    
    @staticmethod
    def find_active_alerts(user_id: str) -> List[Dict]:
        """Find active alerts for user"""
        alerts = alerts_collection.find({
            "user_id": user_id,
            "status": "active"
        }).sort("created_at", -1)
        return list(alerts)
    
    @staticmethod
    def update_alert(alert_id: str, updates: Dict) -> bool:
        """Update an alert"""
        result = alerts_collection.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    @staticmethod
    def get_alert_stats(user_id: str) -> Dict:
        """Get alert statistics for user"""
        # Count by severity
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
        ]
        severity_counts = list(alerts_collection.aggregate(pipeline))
        
        # Count active alerts
        active_count = alerts_collection.count_documents({
            "user_id": user_id,
            "status": "active"
        })
        
        # Recent alerts (last 7 days)
        week_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = week_ago.replace(day=week_ago.day-7)
        
        recent_count = alerts_collection.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": week_ago}
        })
        
        return {
            "severity_distribution": severity_counts,
            "active_alerts": active_count,
            "recent_alerts": recent_count
        }

class BehaviorProfile:
    """User behavior profile model"""
    
    @staticmethod
    def create_or_update(profile_data: Dict) -> str:
        """Create or update behavior profile"""
        user_id = profile_data["user_id"]
        
        # Check if profile exists
        existing = behavior_profiles_collection.find_one({"user_id": user_id})
        
        if existing:
            # Update existing profile
            behavior_profiles_collection.update_one(
                {"user_id": user_id},
                {"$set": profile_data}
            )
            return str(existing["_id"])
        else:
            # Create new profile
            result = behavior_profiles_collection.insert_one(profile_data)
            return str(result.inserted_id)
    
    @staticmethod
    def get_profile(user_id: str) -> Optional[Dict]:
        """Get behavior profile for user"""
        return behavior_profiles_collection.find_one({"user_id": user_id})
    
    @staticmethod
    def update_behavior_pattern(user_id: str, new_pattern: Dict):
        """Update behavior pattern for user"""
        behavior_profiles_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "behavior_pattern": new_pattern,
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    @staticmethod
    def get_all_profiles() -> List[Dict]:
        """Get all behavior profiles"""
        return list(behavior_profiles_collection.find())

# Initialize indexes on startup
User.create_indexes()