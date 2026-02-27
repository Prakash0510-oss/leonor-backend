from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import crud

def calculate_sm2(quality: int, repetitions: int, easiness: float, interval: int):
    """The core math for the spaced repetition algorithm."""
    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * easiness)
        repetitions += 1
    else:
        repetitions = 0
        interval = 1

    easiness += 0.1 - (5.0 - quality) * (0.08 + (5.0 - quality) * 0.02)
    easiness = max(1.3, easiness)

    next_review_date = datetime.utcnow() + timedelta(days=interval)
    return repetitions, easiness, interval, next_review_date


def evaluate_answer(db: Session, user_id: int, exercise_id: int, user_answer: str, quality: int = None):
    exercise = crud.get_exercise(db, exercise_id)
    if not exercise:
        raise ValueError("Exercise not found")

    correct = user_answer.strip().lower() == exercise.correct_answer.strip().lower()

    # --- Spaced Repetition Logic ---
    if quality is None:
        quality = 4 if correct else 0

    exercise_progress = crud.get_or_create_exercise_progress(db, user_id, exercise_id)

    new_rep, new_ease, new_int, next_date = calculate_sm2(
        quality=quality,
        repetitions=exercise_progress.repetitions,
        easiness=exercise_progress.easiness,
        interval=exercise_progress.interval
    )

    exercise_progress.repetitions = new_rep
    exercise_progress.easiness = new_ease
    exercise_progress.interval = new_int
    exercise_progress.next_review_date = next_date
    db.commit()

    # --- Lesson Progress Logic ---
    lesson_id = exercise.lesson_id
    progress = crud.get_or_create_progress(db, user_id, lesson_id)
    progress = crud.update_progress_on_answer(db, progress, correct)

    explanation = (
        "Nice! You got it right." if correct else f"Correct answer is: {exercise.correct_answer}"
    )

    if progress.xp >= 50:
        progress.completed = True
        db.commit()
        db.refresh(progress)

    return {
        "correct": correct,
        "xp_awarded": 10 if correct else 0,
        "new_streak": progress.streak,
        "explanation": explanation,
        "srs_data": {
            "next_review": next_date.isoformat(),
            "interval_days": new_int
        }
    }