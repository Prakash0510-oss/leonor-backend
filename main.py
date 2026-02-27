import uvicorn

from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from auth import get_current_user, verify_password, create_access_token
from database import Base, engine, get_db
import models, schemas, crud, game_logic

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize the App
app = FastAPI(title="Leonor Language App")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter() 

@router.get("/profile")
def read_my_profile(current_user: models.User = Depends(get_current_user)):
    return {"email": current_user.email, "name": current_user.name}

# -----------------------
# Request Models
# -----------------------

class LoginRequest(BaseModel):
    email: str
    password: str


print("✅ backend.main started")


# -----------------------
# Routes
# -----------------------

@app.get("/")
def root():
    return {"message": "Hello, Leonor Language App API"}


@app.get("/me", response_model=schemas.UserOut)
def get_current_user_data(current_user: models.User = Depends(get_current_user)):
    return current_user
    

@app.post("/login")
def login(user_data: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, user_data.email)

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=400, detail="Wrong password")

    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}


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


@app.get("/users/{user_id}/practice/due")
def get_daily_review(user_id: int, db: Session = Depends(get_db)):
    due_exercises = crud.get_due_exercises(db, user_id=user_id)

    if not due_exercises:
        return {
            "message": "You're all caught up for today!",
            "exercises": [],
        }

    return {"exercises": due_exercises}


@app.post("/add-xp")
def add_xp(xp: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    current_user.xp += xp
    db.commit()
    db.refresh(current_user)

    return {"xp": current_user.xp}


@app.post("/answer", response_model=schemas.AnswerResponse)
def submit_answer(answer: schemas.AnswerRequest, db: Session = Depends(get_db)):
    try:
        result = game_logic.evaluate_answer(
            db, answer.user_id, answer.exercise_id, answer.user_answer
        )
        return schemas.AnswerResponse(**result)
    except ValueError:
        raise HTTPException(status_code=404, detail="Exercise not found")


# Run directly (optional)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
