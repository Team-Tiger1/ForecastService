from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

<<<<<<< HEAD
# Load environment variables
load_dotenv()

# Load database credentials from environment varibles
DB_USER = os.getenv("DB_USER")
=======
load_dotenv()

DB_USER = os.getenv("DB_USER")

>>>>>>> 2199e9c1f5f61fc99eb47626b9746022efb58fda
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

<<<<<<< HEAD
# Construct database URL
=======
>>>>>>> 2199e9c1f5f61fc99eb47626b9746022efb58fda
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
<<<<<<< HEAD
    """
    Creates a new database session and ensures it closes after.
    """
=======
>>>>>>> 2199e9c1f5f61fc99eb47626b9746022efb58fda
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()