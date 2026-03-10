import os
from sqlalchemy import create_engine, inspect

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:KBQZgJVeRSilmYiGSbsjNzJBBRUxmVlh@hopper.proxy.rlwy.net:58682/railway')
engine = create_engine(db_url, future=True)
inspector = inspect(engine)

print('Jobs table columns:')
cols = inspector.get_columns('jobs')
for c in cols:
    print(f'  - {c["name"]}: {c["type"]}')

print('\nTranscripts table check:')
try:
    cols = inspector.get_columns('transcripts')
    print('Transcripts table EXISTS')
    for c in cols:
        print(f'  - {c["name"]}: {c["type"]}')
except Exception as e:
    print(f'Transcripts table NOT found: {e}')
