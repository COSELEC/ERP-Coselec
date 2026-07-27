import sys
import os

# Append the project root to sys.path so 'app' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

enum_values = ['PENDING_MANAGER', 'PENDING_FINANCE', 'PENDING_HR', 'PENDING_IT']

with engine.execution_options(isolation_level='AUTOCOMMIT').connect() as conn:
    for val in enum_values:
        try:
            conn.execute(text(f"ALTER TYPE requeststatus ADD VALUE '{val}'"))
            print(f"Added {val}")
        except Exception as e:
            print(f"Skipped {val} or failed: {e}")
