"""
Simple script to create demo user - Working Version
"""
import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from pymongo import MongoClient
    import bcrypt
    from datetime import datetime
    
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017")
    db = client["cybersecurity_db"]
    users_collection = db["users"]
    
    # Check if demo user exists
    existing = users_collection.find_one({"username": "demo"})
    if existing:
        print("Demo user already exists!")
        print(f"Username: demo")
        print(f"User ID: {existing['_id']}")
    else:
        # Create password hash using bcrypt directly
        password = "demo123".encode('utf-8')
        pwd_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_data = {
            "username": "demo",
            "email": "demo@example.com",
            "password_hash": pwd_hash,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "role": "user"
        }
        
        result = users_collection.insert_one(user_data)
        print("✓ Demo user created!")
        print(f"Username: demo")
        print(f"Password: demo123")
        print(f"User ID: {result.inserted_id}")
    
    # Check if admin user exists
    existing_admin = users_collection.find_one({"username": "admin"})
    if existing_admin:
        print("\nAdmin user already exists!")
        print(f"Username: admin")
        print(f"User ID: {existing_admin['_id']}")
    else:
        # Create admin user
        admin_password = "admin123".encode('utf-8')
        admin_hash = bcrypt.hashpw(admin_password, bcrypt.gensalt()).decode('utf-8')
        
        admin_data = {
            "username": "admin",
            "email": "admin@example.com",
            "password_hash": admin_hash,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "role": "admin"
        }
        
        result = users_collection.insert_one(admin_data)
        print("\n✓ Admin user created!")
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"User ID: {result.inserted_id}")
    
    print("\n" + "=" * 50)
    print("You can now login with:")
    print("  Username: demo, Password: demo123")
    print("  Username: admin, Password: admin123")
    print("=" * 50)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
