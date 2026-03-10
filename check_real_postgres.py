from app.db import engine
from sqlalchemy import inspect
inspector = inspect(engine)
cols = inspector.get_columns('users')
print('ACTUAL RAILWAY PostgreSQL COLUMNS:')
for c in cols:
    print(f'  - {c["name"]}: {c["type"]}')
