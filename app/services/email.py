from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from jinja2 import Environment, BaseLoader
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Email templates
VERIFICATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Verify Your Email - The Ultimate API</title>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #1f1f1f; color: #ffffff; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #3ac062; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #2a2a2a; padding: 30px; border-radius: 0 0 8px 8px; }
        .button { display: inline-block; background: #3ac062; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; }
        .footer { text-align: center; margin-top: 20px; color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; color: white;">Welcome to The Ultimate API!</h1>
        </div>
        <div class="content">
            <h2>Verify Your Email Address</h2>
            <p>Hello {{ username }},</p>
            <p>Thank you for registering with The Ultimate API! To complete your registration and start using our powerful Roblox audio downloading service, please verify your email address.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ verification_url }}" class="button">Verify Email Address</a>
            </div>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background: #1f1f1f; padding: 10px; border-radius: 4px;">{{ verification_url }}</p>
            
            <p><strong>This verification link will expire in 24 hours.</strong></p>
            
            <p>If you didn't create an account with us, please ignore this email.</p>
            
            <p>Best regards,<br>The Ultimate API Team</p>
        </div>
        <div class="footer">
            <p>© 2024 The Ultimate API. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

PASSWORD_RESET_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Reset Your Password - The Ultimate API</title>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #1f1f1f; color: #ffffff; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #3ac062; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #2a2a2a; padding: 30px; border-radius: 0 0 8px 8px; }
        .button { display: inline-block; background: #3ac062; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; }
        .footer { text-align: center; margin-top: 20px; color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; color: white;">Reset Your Password</h1>
        </div>
        <div class="content">
            <h2>Password Reset Request</h2>
            <p>Hello {{ username }},</p>
            <p>We received a request to reset your password for your Ultimate API account. If you made this request, click the button below to reset your password:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ reset_url }}" class="button">Reset Password</a>
            </div>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background: #1f1f1f; padding: 10px; border-radius: 4px;">{{ reset_url }}</p>
            
            <p><strong>This reset link will expire in 1 hour.</strong></p>
            
            <p>If you didn't request a password reset, please ignore this email. Your password will not be changed.</p>
            
            <p>Best regards,<br>The Ultimate API Team</p>
        </div>
        <div class="footer">
            <p>© 2024 The Ultimate API. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

class EmailService:
    """Email service for handling verification and password reset emails"""
    
    def __init__(self):
        self.fastmail = FastMail(conf)
        self.serializer = URLSafeTimedSerializer(settings.EMAIL_VERIFICATION_SECRET)
        self.jinja_env = Environment(loader=BaseLoader())
    
    def generate_verification_token(self, email: str) -> str:
        """Generate email verification token"""
        return self.serializer.dumps(email, salt='email-verify')
    
    def generate_password_reset_token(self, email: str) -> str:
        """Generate password reset token"""
        return self.serializer.dumps(email, salt='password-reset')
    
    def verify_verification_token(self, token: str, max_age: int = 86400) -> str:
        """Verify email verification token and return email"""
        try:
            return self.serializer.loads(
                token, 
                salt='email-verify', 
                max_age=max_age
            )
        except Exception as e:
            logger.error("Failed to verify email token", error=str(e))
            raise ValueError("Invalid or expired verification token")
    
    def verify_password_reset_token(self, token: str, max_age: int = 3600) -> str:
        """Verify password reset token and return email"""
        try:
            return self.serializer.loads(
                token, 
                salt='password-reset', 
                max_age=max_age
            )
        except Exception as e:
            logger.error("Failed to verify reset token", error=str(e))
            raise ValueError("Invalid or expired reset token")
    
    async def send_verification_email(self, email: EmailStr, username: str, token: str):
        """Send email verification email"""
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            
            template = self.jinja_env.from_string(VERIFICATION_EMAIL_TEMPLATE)
            html_content = template.render(
                username=username,
                verification_url=verification_url
            )
            
            message = MessageSchema(
                subject="Verify Your Email - The Ultimate API",
                recipients=[email],
                body=html_content,
                subtype=MessageType.html
            )
            
            await self.fastmail.send_message(message)
            logger.info("Verification email sent", email=email, username=username)
            
        except Exception as e:
            logger.error("Failed to send verification email", email=email, error=str(e))
            raise ValueError(f"Failed to send verification email: {str(e)}")
    
    async def send_password_reset_email(self, email: EmailStr, username: str, token: str):
        """Send password reset email"""
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            template = self.jinja_env.from_string(PASSWORD_RESET_EMAIL_TEMPLATE)
            html_content = template.render(
                username=username,
                reset_url=reset_url
            )
            
            message = MessageSchema(
                subject="Reset Your Password - The Ultimate API",
                recipients=[email],
                body=html_content,
                subtype=MessageType.html
            )
            
            await self.fastmail.send_message(message)
            logger.info("Password reset email sent", email=email, username=username)
            
        except Exception as e:
            logger.error("Failed to send password reset email", email=email, error=str(e))
            raise ValueError(f"Failed to send password reset email: {str(e)}")
    
    async def send_welcome_email(self, email: EmailStr, username: str):
        """Send welcome email after successful verification"""
        try:
            welcome_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome to The Ultimate API!</title>
                <style>
                    body { font-family: 'Inter', sans-serif; background-color: #1f1f1f; color: #ffffff; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #3ac062; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
                    .content { background: #2a2a2a; padding: 30px; border-radius: 0 0 8px 8px; }
                    .feature { background: #1f1f1f; padding: 15px; margin: 10px 0; border-radius: 6px; }
                    .footer { text-align: center; margin-top: 20px; color: #888; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0; color: white;">🎉 Welcome to The Ultimate API!</h1>
                    </div>
                    <div class="content">
                        <h2>Your account is now verified!</h2>
                        <p>Hello {{ username }},</p>
                        <p>Congratulations! Your email has been successfully verified and your Ultimate API account is now fully activated.</p>
                        
                        <h3>🚀 What you can do now:</h3>
                        <div class="feature">
                            <strong>🎵 Download Roblox Audio:</strong> Access any public Roblox audio file instantly
                        </div>
                        <div class="feature">
                            <strong>🔑 Generate API Keys:</strong> Create API keys for your Discord bots and applications
                        </div>
                        <div class="feature">
                            <strong>📊 Track Your Usage:</strong> Monitor your downloads and API usage with detailed analytics
                        </div>
                        <div class="feature">
                            <strong>⚡ High Performance:</strong> Enjoy lightning-fast downloads with our optimized infrastructure
                        </div>
                        
                        <h3>🎯 Getting Started:</h3>
                        <ol>
                            <li>Login to your account at <a href="{{ frontend_url }}/login" style="color: #3ac062;">{{ frontend_url }}/login</a></li>
                            <li>Generate your first API key in the dashboard</li>
                            <li>Check out our documentation for integration examples</li>
                            <li>Start downloading audio files!</li>
                        </ol>
                        
                        <p>Your daily limit: <strong>1,000 downloads</strong> (upgrade to Premium for 10,000+ downloads)</p>
                        
                        <p>If you have any questions, feel free to reach out to our support team.</p>
                        
                        <p>Happy downloading!<br>The Ultimate API Team</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 The Ultimate API. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            template = self.jinja_env.from_string(welcome_template)
            html_content = template.render(
                username=username,
                frontend_url=settings.FRONTEND_URL
            )
            
            message = MessageSchema(
                subject="🎉 Welcome to The Ultimate API - Account Verified!",
                recipients=[email],
                body=html_content,
                subtype=MessageType.html
            )
            
            await self.fastmail.send_message(message)
            logger.info("Welcome email sent", email=email, username=username)
            
        except Exception as e:
            logger.error("Failed to send welcome email", email=email, error=str(e))
            # Don't raise here as this is not critical
