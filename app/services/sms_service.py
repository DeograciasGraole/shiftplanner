
import httpx

from app.core.config import settings


async def send_activation_sms(
    phone_number: str,
    activation_code: str,
) -> None:

    url = (
        f"{settings.infobip_base_url.rstrip('/')}"
        "/sms/3/messages"
    )

    headers = {
        "Authorization": (
            f"App {settings.infobip_api_key.get_secret_value()}"
        ),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "messages": [
            {
                "sender": settings.infobip_sender,
                "destinations": [
                    {"to": phone_number}
                ],
                "content": {
                    "text": (
                        f"Welcome to Shifly! "
                        f"Your activation code is: {activation_code}. "
                        "It expires in 48 hours."
                    )
                },
            }
        ]
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

        response.raise_for_status()
