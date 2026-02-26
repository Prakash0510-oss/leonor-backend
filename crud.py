from datetime import datetime
from sqlalchemy.orm import Session
from .auth import hash_password
from models import User

import models, schemas, crud, game_logic

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    
    db_user = models.User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        native_language=user.native_language,
        
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_lessons_for_language(db: Session, language_code: str):
    return (
        db.query(models.Lesson)
        .filter(models.Lesson.language_code == language_code)
        .order_by(models.Lesson.level)
        .all()
    )

def get_exercises_for_lesson(db: Session, lesson_id: int):
    return (
        db.query(models.Exercise)
        .filter(models.Exercise.lesson_id == lesson_id)
        .all()
    )

def get_exercise(db: Session, exercise_id: int):
    return (
        db.query(models.Exercise)
        .filter(models.Exercise.id == exercise_id)
        .first()
    )

def get_or_create_progress(db: Session, user_id: int, lesson_id: int):
    progress = (
        db.query(models.UserProgress)
        .filter(
            models.UserProgress.user_id == user_id,
            models.UserProgress.lesson_id == lesson_id,
        )
        .first()
    )
    if not progress:
        progress = models.UserProgress(
            user_id=user_id, lesson_id=lesson_id, completed=False, xp=0, streak=0
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress

def update_progress_on_answer(db: Session, progress: models.UserProgress, correct: bool):
    if correct:
        progress.xp += 10
        progress.streak += 1
    else:
        progress.streak = 0
    db.commit()
    db.refresh(progress)
    return progress

# --- SRS Database Functions ---

def get_or_create_exercise_progress(db: Session, user_id: int, exercise_id: int):
    """Fetches or creates the memory tracking data for a specific exercise."""
    progress = db.query(models.UserExerciseProgress).filter(
        models.UserExerciseProgress.user_id == user_id,
        models.UserExerciseProgress.exercise_id == exercise_id
    ).first()
    
    if not progress:
        progress = models.UserExerciseProgress(user_id=user_id, exercise_id=exercise_id)
        db.add(progress)
        db.commit()
        db.refresh(progress)
        
    return progress

def get_due_exercises(db: Session, user_id: int, limit: int = 10):
    """Fetches exercises that the user is scheduled to review today."""
    today = datetime.utcnow()
    
    due_exercises = (
        db.query(models.Exercise)
        .join(models.UserExerciseProgress, models.Exercise.id == models.UserExerciseProgress.exercise_id)
        .filter(
            models.UserExerciseProgress.user_id == user_id,
            models.UserExerciseProgress.next_review_date <= today
        )
        .limit(limit)
        .all()
    )
    
    return due_exercises

