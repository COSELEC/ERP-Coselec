import sys
sys.path.append('.')
from app.core.database.session import engine
from sqlalchemy import text

enum_values = [
    'IT_EQUIPMENT', 'IT_ACCESS', 'IT_INCIDENT',
    'FACILITY_MAINTENANCE', 'FACILITY_BADGE', 'FACILITY_SUPPLIES',
    'FUEL', 'DOCUMENT', 'OTHER'
]

with engine.execution_options(isolation_level='AUTOCOMMIT').connect() as conn:
    for val in enum_values:
        try:
            conn.execute(text(f"ALTER TYPE requesttype ADD VALUE '{val}'"))
            print(f'Added {val}')
        except Exception as e:
            print(f'Skipped {val} or failed')
