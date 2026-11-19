
from app.services.email_service import send_activation_email, send_reset_code_email


async def send_activation_notification(
    email: str,
    activation_code: str,
) -> None:

    await send_activation_email(
        recipient_email=email,
        activation_code=activation_code,
    )


async def send_reset_code_notification(
    email: str,
    reset_code: str,
) -> None:
    await send_reset_code_email(
        recipient_email=email,
        reset_code=reset_code,
    )