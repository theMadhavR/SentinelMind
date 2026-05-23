"""
Authentication and authorization handlers
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from models import User

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-cybersecurity-system-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing - using argon2 for better security and no 72-byte limit
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthHandler:
    """Authentication handler"""
    
    def encode_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def encode_token(self, user_id: str) -> str:
        """Create JWT token"""
        payload = {
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "sub": user_id
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def decode_token(self, token: str) -> Optional[str]:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
        """Get current user from token"""
        token = credentials.credentials
        user_id = self.decode_token(token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = User.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return {
            "user_id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }

# Create instance
auth_handler = AuthHandler()

# Dependency for protected routes
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Dependency to get current user"""
    return auth_handler.get_current_user(credentials)