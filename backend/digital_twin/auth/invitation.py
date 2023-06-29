import smtplib
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


from digital_twin.config.app_config import (
    SMTP_SERVER, 
    SMTP_PORT, 
    SMTP_USER,
    SMTP_PASSWORD,
    WEB_DOMAIN,
)


def generate_invitation_token(length=30):
    return secrets.token_urlsafe(length)

def send_user_invitation_email(workspace_name: str, invitee_email: str, token: str) -> None:
    msg = MIMEMultipart()
    msg["Subject"] = f"You're invited to join {workspace_name} workspace"
    msg["From"] = SMTP_USER
    msg["To"] = invitee_email

    link = f"{WEB_DOMAIN}/accept-invitation?token={token}"

    body = MIMEText(f"Click the following link to accept your invitation: {link}")
    msg.attach(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        # If credentials fails with gmail, check (You need an app password, not just the basic email password)
        # https://support.google.com/accounts/answer/185833?sjid=8512343437447396151-NA
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)