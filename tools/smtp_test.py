import os
from dotenv import load_dotenv
import smtplib, ssl
from email.message import EmailMessage

load_dotenv()

HOST = os.getenv('SMTP_HOST')
PORT = int(os.getenv('SMTP_PORT', '587'))
USER = os.getenv('SMTP_USER')
PWD = os.getenv('SMTP_PASS')
FROM = os.getenv('SMTP_FROM', USER or 'noreply@example.com')
TO = os.getenv('CONTACT_TO_EMAIL') or os.getenv('CONTACT_TO') or os.getenv('OWNER_EMAIL') or 'devtest@example.com'

print('HOST=', HOST)
print('PORT=', PORT)
print('USER=', USER)
print('FROM=', FROM)
print('TO=', TO)

msg = EmailMessage()
msg['From'] = FROM
msg['To'] = TO
msg['Subject'] = 'SMTP test from smtp_test.py'
msg.set_content('This is a test')

try:
    context = ssl.create_default_context()
    with smtplib.SMTP(HOST, PORT, timeout=20) as s:
        s.set_debuglevel(1)
        s.ehlo()
        s.starttls(context=context)
        s.ehlo()
        s.login(USER, PWD)
        s.send_message(msg)
    print('SENT_OK')
except Exception as e:
    print('SMTP_ERROR:', repr(e))
