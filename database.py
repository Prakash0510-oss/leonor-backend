import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# ---------------------------------------------------
# 1. Setup & Environment
# ---------------------------------------------------
load_dotenv()

# Setup logging to see what's happening behind the scenes
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to local sqlite if no env is found
    DATABASE_URL = "sqlite:///./leonor.db"
    print("⚠️ DATABASE_URL not found, falling back to local SQLite.")

# FIX: SQLAlchemy 1.4+ requires "postgresql://" but some providers give "postgres://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ---------------------------------------------------
# 2. Advanced Connection Logic
# ---------------------------------------------------
connect_args = {}

if "postgresql" in DATABASE_URL:
    # Production settings for cloud databases (Render/AWS/Heroku)
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 30,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
elif "sqlite" in DATABASE_URL:
    # Required for SQLite to work with FastAPI's multi-threading
    connect_args = {"check_same_thread": False}

# ---------------------------------------------------
# 3. The Engine (The "Brain")
# ---------------------------------------------------
# pool_pre_ping: Checks if connection is alive before every request
# pool_recycle: Prevents "Connection Timed Out" by refreshing every 10 mins
# pool_size / max_overflow: Manage how many concurrent users you can handle
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=600,
    pool_size=10,
    max_overflow=20
)

# ---------------------------------------------------
# 4. Session & Base
# ---------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

Base = declarative_base()

# ---------------------------------------------------
# 5. The Dependency (FastAPI standard)
# ---------------------------------------------------

def get_db():
    """
    Creates a new database session for a single request, 
    and ensures it is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()