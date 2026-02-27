from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models


def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    if db.query(models.Lesson).first():
        print("Already seeded")
        db.close()
        return

    langs = [
        ("en", "English"),
        ("es", "Spanish"),
        ("ja", "Japanese"),
        ("ru", "Russian"),
        ("hi", "Hindi"),
        ("ko", "Korean"),
    ]
    for code, name in langs:
        db.add(models.Language(code=code, name=name))

    lesson1 = models.Lesson(language_code="es", level=1, title="Greetings 1")
    db.add(lesson1)
    db.commit()
    db.refresh(lesson1)

    ex1 = models.Exercise(
        lesson_id=lesson1.id,
        question_type="mcq",
        prompt="How do you say 'Hello' in Spanish?",
        correct_answer="Hola",
        wrong_answer_1="Adiós",
        wrong_answer_2="Gracias",
        wrong_answer_3="Buenos días",
    )
    ex2 = models.Exercise(
        lesson_id=lesson1.id,
        question_type="mcq",
        prompt="How do you say 'Thank you' in Spanish?",
        correct_answer="Gracias",
        wrong_answer_1="Por favor",
        wrong_answer_2="Hola",
        wrong_answer_3="Adiós",
    )
    db.add_all([ex1, ex2])
    db.commit()
    db.close()
    print("Seeded sample data")


if __name__ == "__main__":
    seed()
