from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    native_language = Column(String)
    avatar = Column(String, default="default")
    progress = relationship("UserProgress", back_populates="user")

class Language(Base):
    __tablename__ = "languages"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)  
    name = Column(String)

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    language_code = Column(String, index=True) 
    level = Column(Integer, index=True)
    title = Column(String)

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    question_type = Column(String)  
    prompt = Column(String)
    correct_answer = Column(String)
    wrong_answer_1 = Column(String, nullable=True)
    wrong_answer_2 = Column(String, nullable=True)
    wrong_answer_3 = Column(String, nullable=True)
    lesson = relationship("Lesson")

class UserExerciseProgress(Base):
    """Tracks SRS memory data for a specific user and specific exercise"""
    __tablename__ = "user_exercise_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    
    # SM-2 Algorithm Fields
    repetitions = Column(Integer, default=0)
    easiness = Column(Float, default=2.5)  
    interval = Column(Integer, default=0)
    next_review_date = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    exercise = relationship("Exercise")

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    completed = Column(Boolean, default=False)
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    user = relationship("User", back_populates="progress")