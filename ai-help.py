

import requests

from config import gemini_api_key

res = requests.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    params={"key": gemini_api_key}
)

print(res.status_code)
print(res.text)
