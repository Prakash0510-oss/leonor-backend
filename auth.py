import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import get_db

# ---------------------------------------------------
# 1. Configuration & Security Setup
# ---------------------------------------------------
# NEVER hardcode these in production. Use .env files.
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-complex-secret-key-for-leonor")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Use Argon2 if possible, otherwise Bcrypt is the standard
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This tells FastAPI where to look for the "Login" endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# ---------------------------------------------------
# 2. Password & Token Utilities
# ---------------------------------------------------

def hash_password(password: str) -> str:
    """Returns the hashed version of a plain text password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the provided password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a secure JWT token with an expiration timestamp."""
    to_encode = data.copy()
    
    # Python 3.12+ uses timezone-aware UTC
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ---------------------------------------------------
# 3. Authentication Dependency
# ---------------------------------------------------



def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Decodes the JWT, validates the user_id, and fetches the user from the DB.
    Use this as a dependency in your routes: (user = Depends(get_current_user))
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 1. Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. Extract the user_id (the 'sub' claim is standard for subject)
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception

    # 3. Fetch user from Database
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
        
    # 4. (Optional) Check if user is active
    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User account is deactivated"
        )

    return user