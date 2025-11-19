import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from api.utils.logger import logger

load_dotenv()


SMTP_HOST = os.getenv("MAIL_HOST")
SMTP_PORT = int(os.getenv("MAIL_PORT", 465))
SMTP_USERNAME = os.getenv("MAIL_USERNAME")
SMTP_PASSWORD = os.getenv("MAIL_PASSWORD")
SMTP_SENDER_EMAIL = os.getenv("MAIL_FROM_ADDRESS")
SMTP_ENCRYPTION = os.getenv("MAIL_ENCRYPTION", "SSL").upper()

async def send_email(to_email: str, subject: str, body: str):
    """
    Sends an email using the configured SMTP server.
    """
    
    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_SENDER_EMAIL]):
        return

    msg = MIMEMultipart()
    msg['From'] = SMTP_SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Port 465 uses implicit SSL (use_tls=True)
        # Port 587 uses explicit TLS (STARTTLS)
        use_tls = SMTP_PORT == 465 or SMTP_ENCRYPTION == "SSL"
        
        
        async with aiosmtplib.SMTP(
            hostname=SMTP_HOST, 
            port=SMTP_PORT, 
            use_tls=use_tls
        ) as server:
            
            if not use_tls and SMTP_ENCRYPTION == "TLS":
                
                await server.starttls()
            
            
            await server.login(SMTP_USERNAME, SMTP_PASSWORD)
            
            
            await server.send_message(msg)
            
        logger.info(f"Email successfully sent to: {to_email}")
    except Exception as e:
        import traceback
        traceback.print_exc()