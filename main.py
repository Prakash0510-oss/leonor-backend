import uvicorn
from fastapi import FastAPI, Depends, HTTPException, APIRouter, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Security imports from your auth.py
from auth import (
    get_current_user, 
    verify_password, 
    create_access_token, 
    create_refresh_token, 
    rotate_refresh_token,
    hash_password
)
from database import Base, engine, get_db
import models, schemas, crud, game_logic

# 1. Database Initialization
Base.metadata.create_all(bind=engine)

# 2. App Initialization
app = FastAPI(title="Leonor Language App")

# 3. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Request Models
# -----------------------

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

# -----------------------
# Authentication Routes
# -----------------------

@app.post("/login")
def login(user_data: LoginRequest, db: Session = Depends(get_db)):
    """Logs the user in and returns both Access and Refresh tokens."""
    user = crud.get_user_by_email(db, user_data.email)

    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password"
        )

    # The Safest Way: Short-lived Access Token + Database-backed Refresh Token
    access_token = create_access_token(user_id=user.id)
    refresh_token = create_refresh_token(user_id=user.id, db=db)

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/refresh")
def refresh_session(data: RefreshRequest, db: Session = Depends(get_db)):
    """Exchanges an old refresh token for a brand new pair (Rotation)."""
    # This checks for reuse/hacks and returns a NEW random string
    new_refresh_token_str = rotate_refresh_token(data.refresh_token, db)
    
    # Get the user_id from the record we just updated/created
    token_record = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == new_refresh_token_str
    ).first()
    
    new_access_token = create_access_token(user_id=token_record.user_id)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer"
    }

@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Hashes password and creates a new user account."""
    hashed_pw = hash_password(user.password)

    db_user = models.User(
        username=user.username,
        email=user.email,
        password=hashed_pw
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "User created successfully"}

# -----------------------
# Protected User Routes
# -----------------------

@app.get("/me", response_model=schemas.UserOut)
def get_current_user_data(current_user: models.User = Depends(get_current_user)):
    """Returns full data for the currently logged-in user."""
    return current_user

@app.get("/profile")
def read_my_profile(current_user: models.User = Depends(get_current_user)):
    """Returns simple profile info (fixed 'name' to 'username')."""
    return {"email": current_user.email, "username": current_user.username}

@app.post("/add-xp")
def add_xp(xp: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Safely adds XP to the authenticated user's account."""
    current_user.xp += xp
    db.commit()
    db.refresh(current_user)
    return {"xp": current_user.xp}

# -----------------------
# Lesson & Game Routes
# -----------------------

@app.get("/lessons/{language_code}", response_model=list[schemas.LessonOut])
def list_lessons(language_code: str, db: Session = Depends(get_db)):
    return crud.get_lessons_for_language(db, language_code)

@app.get("/lesson/{lesson_id}/exercises", response_model=list[schemas.ExerciseOut])
def list_exercises(lesson_id: int, db: Session = Depends(get_db)):
    return crud.get_exercises_for_lesson(db, lesson_id)

@app.post("/answer", response_model=schemas.AnswerResponse)
def submit_answer(answer: schemas.AnswerRequest, db: Session = Depends(get_db)):
    try:
        result = game_logic.evaluate_answer(
            db, answer.user_id, answer.exercise_id, answer.user_answer
        )
        return schemas.AnswerResponse(**result)
    except ValueError:
        raise HTTPException(status_code=404, detail="Exercise not found")

# -----------------------
# App Entry Point
# -----------------------

if __name__ == "__main__":
    print("✅ Leonor Backend (Safest Version) is starting...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)