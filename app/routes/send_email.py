import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "support@echoscriptai.com")

def send_email(to: str, subject: str, content: str):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to,
        subject=subject,
        plain_text_content=content
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(message)
