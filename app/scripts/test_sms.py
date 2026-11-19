
import asyncio

from app.services.sms_service import send_activation_sms


async def main():
    await send_activation_sms(
        phone_number="+905XXXXXXXXX",
        activation_code="123456",
    )

    print("SMS request sent successfully!")

if __name__ == "__main__":
    asyncio.run(main())
