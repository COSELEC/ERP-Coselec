import asyncio
from sqlalchemy import text
from app.core.database import SessionLocal

def fix_enum():
    db = SessionLocal()
    try:
        db.execute(text("ALTER TYPE purchaseorderstatus ADD VALUE IF NOT EXISTS 'APPROVED';"))
        db.commit()
        print("Enum updated successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_enum()
