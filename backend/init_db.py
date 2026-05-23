#!/usr/bin/env python3
"""
Database initialization script for Adaptive Cybersecurity System
Creates demo users and sample data
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import User, users_collection, db
from auth import AuthHandler

def init_database():
    """Initialize database with demo users"""
    print("=" * 60)
    print("Initializing Adaptive Cybersecurity Database")
    print("=" * 60)
    
    auth_handler = AuthHandler()
    
    # Check if demo user already exists
    existing_user = User.find_by_username("demo")
    if existing_user:
        print("\n✓ Demo user already exists")
        print(f"  Username: demo")
        print(f"  Email: {existing_user.get('email', 'demo@example.com')}")
        print(f"  User ID: {existing_user.get('_id')}")
        return
    
    # Create demo user
    print("\nCreating demo user...")
    demo_password = "demo123"
    hashed_password = auth_handler.encode_password(demo_password)
    
    demo_user_data = {
        "username": "demo",
        "email": "demo@example.com",
        "password_hash": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "role": "user"
    }
    
    try:
        result = users_collection.insert_one(demo_user_data)
        print("✓ Demo user created successfully")
        print(f"  Username: demo")
        print(f"  Password: {demo_password}")
        print(f"  Email: demo@example.com")
        print(f"  User ID: {result.inserted_id}")
        
        # Create admin user
        print("\nCreating admin user...")
        admin_password = "admin123"
        hashed_admin_password = auth_handler.encode_password(admin_password)
        
        admin_user_data = {
            "username": "admin",
            "email": "admin@example.com",
            "password_hash": hashed_admin_password,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "role": "admin"
        }
        
        result = users_collection.insert_one(admin_user_data)
        print("✓ Admin user created successfully")
        print(f"  Username: admin")
        print(f"  Password: {admin_password}")
        print(f"  Email: admin@example.com")
        print(f"  User ID: {result.inserted_id}")
        
    except Exception as e:
        print(f"✗ Error creating users: {e}")
        return
    
    print("\n" + "=" * 60)
    print("Database initialization completed!")
    print("=" * 60)
    print("\nYou can now login with:")
    print("  - Username: demo, Password: demo123")
    print("  - Username: admin, Password: admin123")
    print("=" * 60)

if __name__ == "__main__":
    try:
        # Test MongoDB connection
        from pymongo import MongoClient
        MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        client = MongoClient(MONGO_URI)
        client.server_info()
        print("✓ MongoDB connection successful\n")
        
        init_database()
    except Exception as e:
        print(f"\n✗ MongoDB connection failed: {e}")
        print("\nPlease make sure MongoDB is running:")
        print("  On Windows: Run 'mongod' from command prompt")
        print("  Or install MongoDB as a service")
        sys.exit(1)
