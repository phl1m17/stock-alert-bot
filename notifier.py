import os
from twilio.rest import Client

def send_text(message: str):
    account_sid = os.getenv("TWILIO_SID")
    auth_token = os.getenv("TWILIO_TOKEN")
    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_=os.getenv("TWILIO_FROM"),
        to=os.getenv("TWILIO_TO")
    )