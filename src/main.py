import calendar
import datetime
from typing import Optional

from twilio.rest import Client  # type: ignore - stubs totally do exist

from .settings import settings  # Import the settings object


def days_until_end_month():
    d = datetime.date.today()
    end_of_month = datetime.date(
        d.year, d.month, calendar.monthrange(d.year, d.month)[-1]
    )
    end = str(end_of_month).split("-")
    current = str(d).split("-")
    return int(end[2]) - int(current[2])


def send_message(
    phone_number: Optional[str] = None,
    name: Optional[str] = None,
) -> None:
    if not phone_number:
        print(f"Skipping message for {name}: Phone number is missing.")
        return

    # Use settings for credentials and phone number
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    try:
        message = client.messages.create(
            body="Hello {name}, your reminder message here. [This part needs completion]".format(
                name=name if name else "Tenant"
            ),
            from_=settings.TWILIO_PHONE_NUMBER,  # Use settings for from_ number
            to=phone_number,
        )
        print(f"Sent to: {name} | [{message.sid}]")
    except Exception as e:
        print(f"Failed to send message to {name} ({phone_number}): {e}")


def main(spreadsheet: str = "August Rent - Sheet1.csv") -> None:
    with open(spreadsheet, "r") as tenants:
        for _, tenant in enumerate(tenants):
            tenant_info = tenant.split(",")
            if len(tenant_info) > 3 and tenant_info[2] == "FALSE":
                phone_number = tenant_info[3].strip()
                # Pass only necessary parameters
                send_message(name=tenant_info[0], phone_number=phone_number)


main()
