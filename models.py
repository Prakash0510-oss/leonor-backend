from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from database import Base

# ---------------------------------------------------
# 1. User Account & Global Stats
# ---------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    native_language = Column(String, default="en")
    avatar = Column(String, default="default_avatar.png")
    xp = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    exercise_history = relationship("UserExerciseProgress", back_populates="user")

# ---------------------------------------------------
# 2. Content Structure (Lessons & Exercises)
# ---------------------------------------------------
class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    language_code = Column(String, index=True) # e.g., 'es', 'fr'
    level = Column(Integer, index=True, default=1) # e.g., Level 1, 2, 3
    title = Column(String, nullable=False)
    
    exercises = relationship("Exercise", back_populates="lesson")

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    
    question_type = Column(String) # 'multiple_choice', 'translation', 'listening'
    prompt = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    # Storing distractors as nullable for flexible exercise types
    wrong_answer_1 = Column(String, nullable=True)
    wrong_answer_2 = Column(String, nullable=True)
    
    lesson = relationship("Lesson", back_populates="exercises")

# ---------------------------------------------------
# 3. Tracking & Algorithms (SRS)
# ---------------------------------------------------
class UserExerciseProgress(Base):
    """Tracks SRS (Spaced Repetition) for specific words/phrases"""
    __tablename__ = "user_exercise_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    
    # SM-2 Algorithm Fields
    repetitions = Column(Integer, default=0)
    easiness = Column(Float, default=2.5)  
    interval = Column(Integer, default=0)
    next_review_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="exercise_history")
    exercise = relationship("Exercise")

class UserProgress(Base):
    """Tracks overall lesson completion and streaks"""
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="progress")