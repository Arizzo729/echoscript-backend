import os
from dotenv import load_dotenv
load_dotenv()
keys = [
    'RESEND_API_KEY',
    'SMTP_HOST','SMTP_PORT','SMTP_USER','SMTP_PASS','SMTP_FROM',
    'CONTACT_DEV_SAVE','CONTACT_DEV_LOG','CONTACT_TO_EMAIL','CONTACT_TO','OWNER_EMAIL'
]
for k in keys:
    v = os.getenv(k)
    print(f"{k} => {repr(v)}")
