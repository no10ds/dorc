{% if rapid_enabled %}
import os

from rapid import Rapid
from rapid import RapidAuth

rapid_url = os.getenv("RAPID_URL")
rapid_client_key = os.getenv("RAPID_CLIENT_KEY")
rapid_client_secret = os.getenv("RAPID_CLIENT_SECRET")

rapid = Rapid(auth=RapidAuth(rapid_client_key, rapid_client_secret, url=rapid_url))
{% endif %}


def handler(event, context):
    print("HELLO WORLD")

    return {"statusCode": 200, "body": "Hello World"}
