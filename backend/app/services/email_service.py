import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")


def send_otp_email(to_email: str, otp_code: str, name: str) -> bool:
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'PaisaTrack - Email Verification Code'
        msg['From'] = GMAIL_USER
        msg['To'] = to_email

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #333; }}
                .container {{ max-width: 400px; padding: 20px; }}
                .code {{ font-size: 24px; font-weight: bold; margin: 24px 0; letter-spacing: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <p>Hello {name},</p>
                <p>Your verification code for PaisaTrack is:</p>
                <div class="code">{otp_code}</div>
                <p>This code expires in 10 minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
        </body>
        </html>
        """

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
