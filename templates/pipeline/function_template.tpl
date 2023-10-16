{% if rapid_enabled %}
import os

from rapid import Rapid
from rapid import RapidAuth

rapid = Rapid(auth=RapidAuth())
{% endif %}


def handler(event, context):
    print("HELLO WORLD")

    return {"statusCode": 200, "body": "Hello World"}
