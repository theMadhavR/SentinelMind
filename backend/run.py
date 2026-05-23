#!/usr/bin/env python3
"""
Simple runner script for the Adaptive Cybersecurity System
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pymongo',
        'sklearn',
        'pandas',
        'numpy'
    ]
    
    print("Checking dependencies...")
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"✗ {package}")
    
    return missing

def setup_environment():
    """Setup environment variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("\nCreating .env file with default values...")
        env_content = """# Adaptive Cybersecurity System Environment Variables
MONGO_URI=mongodb://localhost:27017
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("Created .env file")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed. Using default environment variables.")

def start_backend():
    """Start the FastAPI backend server"""
    print("\n" + "="*60)
    print("Starting Adaptive Cybersecurity System Backend")
    print("="*60)
    
    # Check if MongoDB is running
    try:
        from pymongo import MongoClient
        client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
        client.server_info()
        print("✓ MongoDB connection successful")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        print("\nPlease make sure MongoDB is running:")
        print("  On Windows: Run 'mongod' from command prompt")
        print("  Or install MongoDB as a service")
        print("\nYou can install MongoDB from: https://www.mongodb.com/try/download/community")
        return False
    
    # Initialize database
    print("\nInitializing database...")
    try:
        # Import after path is set
        from models import User
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
    
    # Train ML model if not exists
    model_path = Path("isolation_forest.pkl")
    if not model_path.exists():
        print("\nTraining ML model (first time setup)...")
        try:
            # Import and run training
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml_training'))
            
            # Create a simple training script
            print("Generating and training ML model...")
            
            # Import necessary modules
            import pandas as pd
            import numpy as np
            from sklearn.ensemble import IsolationForest
            import joblib
            
            # Generate sample data
            np.random.seed(42)
            n_samples = 1000
            data = pd.DataFrame({
                'hour_sin': np.sin(2 * np.pi * np.random.normal(14, 3, n_samples) / 24),
                'hour_cos': np.cos(2 * np.pi * np.random.normal(14, 3, n_samples) / 24),
                'day_sin': np.sin(2 * np.pi * np.random.randint(0, 7, n_samples) / 7),
                'day_cos': np.cos(2 * np.pi * np.random.randint(0, 7, n_samples) / 7),
                'session_duration': np.random.normal(1800, 600, n_samples),
                'action_count_in_session': np.random.poisson(15, n_samples),
                'action_view': np.random.binomial(1, 0.6, n_samples),
                'action_download': np.random.binomial(1, 0.2, n_samples),
                'action_edit': np.random.binomial(1, 0.15, n_samples),
                'action_delete': np.random.binomial(1, 0.05, n_samples)
            })
            
            # Train model
            model = IsolationForest(
                n_estimators=100,
                contamination=0.1,
                random_state=42
            )
            model.fit(data)
            
            # Save model
            joblib.dump(model, 'isolation_forest.pkl')
            print("✓ ML model trained and saved successfully")
            
        except Exception as e:
            print(f"✗ ML model training failed: {e}")
            print("Continuing with rule-based detection only...")
    
    # Start the server
    print("\n" + "="*60)
    print("Starting server on http://localhost:8000")
    print("="*60)
    print("\nAvailable endpoints:")
    print("  • http://localhost:8000/docs - API Documentation")
    print("  • http://localhost:8000/health - Health Check")
    print("\nPress Ctrl+C to stop the server")
    print("="*60)
    
    # Import and run the app
    try:
        from app import app
        import uvicorn
        
        # Run with auto-reload for development
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["backend"]
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        raise
    
    return True

def main():
    """Main entry point"""
    print("Adaptive Cybersecurity System - Setup & Launch")
    print("="*60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("\nInstall them using:")
        print(f"  pip install {' '.join(missing)}")
        install = input("\nDo you want to install missing packages? (y/n): ")
        if install.lower() == 'y':
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
                print("\nPackages installed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\nFailed to install packages: {e}")
                print("Please install them manually and try again.")
                sys.exit(1)
        else:
            print("Cannot continue without required packages")
            sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Start backend
    try:
        start_backend()
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\nError starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()