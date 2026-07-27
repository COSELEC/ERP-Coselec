import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from sqlalchemy import text

def add_columns():
    db = SessionLocal()
    try:
        # Add project_id
        query = text("""
            ALTER TABLE purchase_orders 
            ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL;
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
