import os
from sqlalchemy import create_engine, inspect

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:KBQZgJVeRSilmYiGSbsjNzJBBRUxmVlh@hopper.proxy.rlwy.net:58682/railway')
engine = create_engine(db_url, future=True)
inspector = inspect(engine)

print('Tables in database:')
for table in inspector.get_table_names():
    print(f'  - {table}')
