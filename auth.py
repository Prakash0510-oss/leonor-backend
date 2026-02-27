import os
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
# 1. Configuration
# ---------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-complex-secret-key-for-leonor")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short life for safety
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Long life for convenience

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# ---------------------------------------------------
# 2. Functions (The "What is it" Section)
# ---------------------------------------------------

def hash_password(password: str) -> str:
    """
    WHAT IS IT: The "Scrambler".
    It takes a clear password like "12345" and turns it into a long 
    random string. You save this string in the DB, never the real password.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    WHAT IS IT: The "Key Matcher".
    When a user logs in, it compares the password they typed with the 
    scrambled string in the DB.
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int) -> str:
    """
    WHAT IS IT: The "Temporary Entry Pass".
    Generates a JWT that lasts 15 minutes. It contains the user's ID
    under the 'sub' (subject) key.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "iat": now, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int, db: Session) -> str:
    """
    WHAT IS IT: The "Permanent Membership Card".
    Generates a random 64-character string and saves it in your 
    database linked to the user.
    """
    token_str = os.urandom(32).hex()
    db_token = models.RefreshToken(
        token=token_str, 
        user_id=user_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_token)
    db.commit()
    return token_str

def rotate_refresh_token(old_token_str: str, db: Session):
    """
    WHAT IS IT: The "Security Alarm".
    It swaps an old refresh token for a new one. If it sees an old 
    token being used twice, it assumes a HACKER is active and 
    immediately logs the user out of all devices for safety.
    """
    token_record = db.query(models.RefreshToken).filter(models.RefreshToken.token == old_token_str).first()
    
    if not token_record:
        raise HTTPException(status_code=401, detail="Session not found")

    # If already used, someone stole the token!
    if token_record.is_used:
        db.query(models.RefreshToken).filter(models.RefreshToken.user_id == token_record.user_id).delete()
        db.commit()
        raise HTTPException(status_code=401, detail="Security breach detected. Please log in again.")

    # Mark as used and give a fresh one
    token_record.is_used = True
    db.commit()
    return create_refresh_token(token_record.user_id, db)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    WHAT IS IT: The "Bouncer".
    This runs before every private API call. It checks if the token 
    is valid and returns the 'User' object so you know who is calling.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub") # Look for 'sub' (standard)
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user