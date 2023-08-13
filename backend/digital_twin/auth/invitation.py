import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from digital_twin.config.app_config import SMTP_PASSWORD, SMTP_PORT, SMTP_SERVER, SMTP_USER, WEB_DOMAIN


def generate_invitation_token(length=30):
    return secrets.token_urlsafe(length)


def send_user_invitation_email(workspace_name: str, invitee_email: str, token: str) -> None:
    msg = MIMEMultipart()
    msg["Subject"] = f"You're invited to join {workspace_name} workspace"
    msg["From"] = SMTP_USER
    msg["To"] = invitee_email
    # TODO: We'll do proper invitation flow later, for now just send them to the landing page
    # link = f"{WEB_DOMAIN}/accept-invitation?token={token}"
    # body = MIMEText(f"Click the following link to accept your invitation: {link}")
    link = f"{WEB_DOMAIN}"
    body = MIMEText(f"Sign up with your work email here: {link}")
    msg.attach(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        # If credentials fails with gmail, check (You need an app password, not just the basic email password)
        # https://support.google.com/accounts/answer/185833?sjid=8512343437447396151-NA
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)
