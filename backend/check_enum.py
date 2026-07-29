import asyncio
from sqlalchemy import text
from app.core.database import SessionLocal

def check_enum():
    db = SessionLocal()
    try:
        res = db.execute(text("SELECT enumlabel FROM pg_enum WHERE enumtypid = 'purchaseorderstatus'::regtype;"))
        for r in res:
            print(f"ENUM VALUE: {r[0]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_enum()
