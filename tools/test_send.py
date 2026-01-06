from dotenv import load_dotenv
import os, sys
load_dotenv()

# Ensure project root is on sys.path so `app` package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.utils.send_email import send_email, EmailError

recipient = os.getenv("CONTACT_TO_EMAIL") or os.getenv("CONTACT_TO") or os.getenv("OWNER_EMAIL") or "devtest@example.com"
print("Using recipient:", recipient)
try:
    send_email(
        to_address=recipient,
        subject="EchoScript test email",
        body_text="This is a test sent from test_send.py",
    )
    print("SEND_OK")
except EmailError as e:
    print("EMAIL_ERROR:", str(e))
except Exception as e:
    print("UNEXPECTED_ERROR:", str(e))
