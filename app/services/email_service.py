
import html
import resend
from app.core.config import settings


async def send_activation_email(
    recipient_email: str,
    activation_code: str,
) -> None:

    resend.api_key = settings.resend_api_key.get_secret_value()

    safe_code = html.escape(activation_code)

    params: resend.Emails.SendParams = {
        "from": settings.resend_from_email,
        "to": [recipient_email],
        "subject": "Your Shifly activation code",
        "html": f"""
            <h2>Welcome to Shifly!</h2>
            <p>Your employee account has been created.</p>
            <p>Your activation code is:</p>
            <h1>{safe_code}</h1>
            <p>This code expires in 48 hours.</p>
        """,
        "text": (
            "Welcome to Shifly!\n"
            f"Your activation code is: {activation_code}\n"
            "This code expires in 48 hours."
        ),
    }

    await resend.Emails.send_async(params)


async def send_reset_code_email(
    recipient_email: str,
    reset_code: str,
) -> None:

    resend.api_key = settings.resend_api_key.get_secret_value()

    safe_code = html.escape(reset_code)

    params: resend.Emails.SendParams = {
        "from": settings.resend_from_email,
        "to": [recipient_email],
        "subject": "Your Shifly password reset code",
        "html": f"""
            <h2>Password Reset</h2>
            <p>We received a request to reset your Shifly password.</p>
            <p>Your verification code is:</p>
            <h1>{safe_code}</h1>
            <p>This code expires in 10 minutes.</p>
            <p>If you did not request a password reset, you can ignore this email.</p>
        """,
        "text": (
            "Password Reset\n"
            "We received a request to reset your Shifly password.\n"
            f"Your verification code is: {reset_code}\n"
            "This code expires in 10 minutes.\n"
            "If you did not request a password reset, you can ignore this email."
        ),
    }

    await resend.Emails.send_async(params)
