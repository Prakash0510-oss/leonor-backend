import uvicorn
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import Base, engine, get_db
from . import models, schemas, crud, game_logic

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize the App FIRST
app = FastAPI(title="Leonor Language App")

# 1. This is the security guard letting your React Native app inside!

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Define the shape of the data the frontend is sending
class LoginRequest(BaseModel):
    email: str
    password: str

print("✅ backend.main started")

# 3. The actual "catcher" for the fetch request
@app.post("/login")
def login(user_data: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, user_data.email)

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if user.password != user_data.password:
        raise HTTPException(status_code=400, detail="Wrong password")

    return {
        "message": "Login successful",
        "user_id": user.id
    }


@app.get("/")
def root():
    return {"message": "Hello, Leonor Language App API"}

@app.post("/users/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.get("/lessons/{language_code}", response_model=list[schemas.LessonOut])
def list_lessons(language_code: str, db: Session = Depends(get_db)):
    lessons = crud.get_lessons_for_language(db, language_code)
    return lessons

@app.get("/lesson/{lesson_id}/exercises", response_model=list[schemas.ExerciseOut])
def list_exercises(lesson_id: int, db: Session = Depends(get_db)):
    return crud.get_exercises_for_lesson(db, lesson_id)

# --- New Practice Route ---
@app.get("/users/{user_id}/practice/due")
def get_daily_review(user_id: int, db: Session = Depends(get_db)):
    due_exercises = crud.get_due_exercises(db, user_id=user_id)
    
    if not due_exercises:
        return {
            "message": "You're all caught up for today!", 
            "exercises": []
        }
        
    return {"exercises": due_exercises}

@app.post("/answer", response_model=schemas.AnswerResponse)
def submit_answer(answer: schemas.AnswerRequest, db: Session = Depends(get_db)):
    try:
        result = game_logic.evaluate_answer(
            db, answer.user_id, answer.exercise_id, answer.user_answer
        )
        return schemas.AnswerResponse(**result)
    except ValueError:
        raise HTTPException(status_code=404, detail="Exercise not found")


