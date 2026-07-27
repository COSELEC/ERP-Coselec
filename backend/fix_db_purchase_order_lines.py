import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from sqlalchemy import text

def add_columns():
    db = SessionLocal()
    try:
        # Add designation to purchase_order_lines
        query = text("""
            ALTER TABLE purchase_order_lines 
            ADD COLUMN IF NOT EXISTS designation VARCHAR(255);
        """)
        db.execute(query)
        db.commit()
        print("Columns added successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_columns()
