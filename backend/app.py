"""
Main FastAPI Application for Adaptive Cybersecurity System
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import os
from typing import Optional

# Import our modules
from auth import AuthHandler, get_current_user
from models import User, UserActivity, SecurityAlert
from data_collector import DataCollector
from anomaly_detector import AnomalyDetector
from ml_model import train_model, predict_anomaly

app = FastAPI(title="Adaptive Cybersecurity System", version="1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
auth_handler = AuthHandler()
data_collector = DataCollector()
anomaly_detector = AnomalyDetector()

# Models for API
class UserRegister(BaseModel):
    username: str
    password: str
    email: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserAction(BaseModel):
    action_type: str  # "view", "download", "edit", "delete"
    resource: str
    details: Optional[dict] = {}

# Routes
@app.get("/")
async def root():
    return {
        "message": "Adaptive Cybersecurity API",
        "status": "running",
        "endpoints": ["/login", "/register", "/predict"]
    }

@app.post("/register")
async def register(user: UserRegister):
    """Register a new user"""
    # Check if user exists
    if User.find_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user
    hashed_password = auth_handler.encode_password(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        is_active=True,
        created_at=datetime.utcnow()
    )
    new_user.save()
    
    return {"message": "User created successfully", "user_id": str(new_user._id)}

@app.post("/login")
async def login(user: UserLogin):
    """User login endpoint"""
    # Find user
    db_user = User.find_by_username(user.username)
    if not db_user or not auth_handler.verify_password(user.password, db_user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Track login activity
    login_activity = data_collector.track_login(
        user_id=str(db_user['_id']),
        username=user.username,
        device="Web Browser",  # In real app, extract from request
        location="Unknown",
        ip_address="127.0.0.1"
    )
    
    # Generate token
    token = auth_handler.encode_token(str(db_user['_id']))
    
    return {
        "token": token,
        "user_id": str(db_user['_id']),
        "username": user.username,
        "login_id": str(login_activity['_id'])
    }

@app.post("/action")
async def perform_action(
    action: UserAction,
    current_user: dict = Depends(get_current_user)
):
    """Track user actions"""
    user_id = current_user['user_id']
    
    # Track the action
    activity = data_collector.track_action(
        user_id=user_id,
        action_type=action.action_type,
        resource=action.resource,
        details=action.details
    )
    
    # Check for anomalies
    anomaly_score = anomaly_detector.check_anomaly(user_id)
    
    # If anomaly detected, create alert
    if anomaly_score > 0.7:
        alert = SecurityAlert.create(
            user_id=user_id,
            alert_type="Suspicious Behavior",
            severity="Medium" if anomaly_score < 0.9 else "High",
            description=f"Anomaly detected with score: {anomaly_score:.2f}",
            anomaly_score=anomaly_score,
            status="active"
        )
        
        # If high risk, force logout
        if anomaly_score > 0.9:
            return {
                "action_logged": True,
                "anomaly_detected": True,
                "anomaly_score": anomaly_score,
                "alert": "High risk detected. Session terminated.",
                "force_logout": True
            }
    
    return {
        "action_logged": True,
        "anomaly_detected": anomaly_score > 0.7,
        "anomaly_score": anomaly_score,
        "force_logout": False
    }

@app.get("/user/behavior")
async def get_user_behavior(current_user: dict = Depends(get_current_user)):
    """Get user behavior profile"""
    user_id = current_user['user_id']
    behavior = data_collector.get_user_behavior_profile(user_id)
    return behavior

@app.get("/security/alerts")
async def get_security_alerts(current_user: dict = Depends(get_current_user)):
    """Get security alerts for the user"""
    user_id = current_user['user_id']
    alerts = SecurityAlert.find_by_user(user_id, limit=10)
    return {"alerts": alerts}

@app.post("/train/model")
async def train_behavior_model():
    """Train the behavior model (admin endpoint)"""
    try:
        train_model()
        return {"message": "Model trained successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    user_id = current_user['user_id']
    
    # Get user activities
    activities = UserActivity.find_by_user(user_id, limit=50)
    
    # Calculate stats
    total_actions = len(activities)
    today_actions = len([a for a in activities if a['timestamp'].date() == datetime.utcnow().date()])
    
    # Get anomaly score
    anomaly_score = anomaly_detector.get_user_anomaly_score(user_id)
    
    # Get alerts
    alerts = SecurityAlert.find_by_user(user_id, limit=5)
    
    return {
        "user_id": user_id,
        "total_actions": total_actions,
        "today_actions": today_actions,
        "anomaly_score": anomaly_score,
        "recent_alerts": alerts,
        "risk_level": "Low" if anomaly_score < 0.5 else "Medium" if anomaly_score < 0.8 else "High"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)