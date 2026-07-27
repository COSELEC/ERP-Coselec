import sys
import os

# Add the project root to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from sqlalchemy import text

def fix_pending_states():
    db = SessionLocal()
    try:
        # PostgreSQL enum type name is usually the lowercase class name: requeststatus
        query = text("""
            UPDATE requests 
            SET status = 'PENDING' 
            WHERE status IN ('PENDING_MANAGER', 'PENDING_HR', 'PENDING_IT', 'PENDING_FINANCE');
        """)
        result = db.execute(query)
        db.commit()
        print(f"Updated {result.rowcount} requests to 'PENDING'.")
        
        # We also need to update request_history records to avoid breaking history
        query_history_old = text("""
            UPDATE request_history 
            SET old_status = 'PENDING' 
            WHERE old_status IN ('PENDING_MANAGER', 'PENDING_HR', 'PENDING_IT', 'PENDING_FINANCE');
        """)
        res_hist_old = db.execute(query_history_old)
        
        query_history_new = text("""
            UPDATE request_history 
            SET new_status = 'PENDING' 
            WHERE new_status IN ('PENDING_MANAGER', 'PENDING_HR', 'PENDING_IT', 'PENDING_FINANCE');
        """)
        res_hist_new = db.execute(query_history_new)
        db.commit()
        print(f"Updated {res_hist_old.rowcount + res_hist_new.rowcount} history records.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_pending_states()
