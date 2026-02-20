from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    native_language: str

class UserCreate(UserBase):
    pass

class UserOut(UserBase):
    id: int
    avatar: str
    class Config:
        orm_mode = True

# --- Lesson & Exercise Schemas ---
class ExerciseOut(BaseModel):
    id: int
    question_type: str
    prompt: str
    # We don't send the correct answer to the frontend initially to prevent cheating!
    wrong_answer_1: Optional[str] = None
    wrong_answer_2: Optional[str] = None
    wrong_answer_3: Optional[str] = None

    class Config:
        orm_mode = True

class LessonOut(BaseModel):
    id: int
    title: str
    level: int
    exercises: List[ExerciseOut] = []
    class Config:
        orm_mode = True

# --- Game Logic Schemas ---
class AnswerRequest(BaseModel):
    user_id: int
    exercise_id: int
    user_answer: str

class SRSData(BaseModel):
    next_review: str
    interval_days: int

class AnswerResponse(BaseModel):
    correct: bool
    xp_awarded: int
    new_streak: int
    explanation: str
    srs_data: Optional[SRSData] = None  # New field for the algorithm