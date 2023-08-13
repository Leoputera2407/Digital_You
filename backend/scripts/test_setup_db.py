import json

import requests

from digital_twin.config.app_config import POSTGRES_DB, POSTGRES_HOST
from digital_twin.db.connectors.google_drive import async_upsert_db_google_app_cred
from digital_twin.db.engine import get_async_session
from digital_twin.server.model import GoogleAppCredentials, GoogleAppWebCredentials

print(POSTGRES_DB, POSTGRES_HOST)

BUCKET_NAME = "Access Token Bucket"
BUCKET_SOURCE = "localhost_google_app_credentials.json"
# destination ="./localhost_google_app_credentials.json"
destination = "./localhost_google_app_credentials.json"
"""
with open(destination, 'wb+') as f:
  res = supabase.storage.from_(BUCKET_NAME).download(BUCKET_SOURCE)
  f.write(res)
"""

with open(destination, "r") as f:
    credentials = json.load(f)


# Now push the app_credential to the database, remember to change the redirect_uri to your
# frontend "url/connectors/google-drive/auth/callback"
"""
app_credentials = GoogleAppWebCredentials(**credentials)
response = requests.put(
    url="http://localhost:8080/connector/admin/google-drive/app-credential",
    headers={"Content-Type": "application/json"},
    json=app_credentials.dict()  # Converting Pydantic model to dict
)

# We can now handle the response
if response.status_code == 200:
    print("Successfully saved Google App Credentials")
else:
    print(f"Error occurred: {response.text}")
"""
app_credentials = GoogleAppCredentials(**credentials["web"])
db_session = get_async_session()


async def upsert_db_google_app_cred():
    return await async_upsert_db_google_app_cred(app_credentials.dict(), db_session)


# You should run your coroutine inside an event loop
async def main():
    res = await upsert_db_google_app_cred()
    print("pushed cred to db")
    return


import asyncio

asyncio.run(main())
"""
# URL of your API
url = "http://localhost:8080/connector/google-drive/app-credential"

# Send the GET request
response = requests.get(url)

# Handle the response
if response.status_code == 200:
    print("Google App Credentials exist.")
    print(f"Client ID: {response.json()['client_id']}")
elif response.status_code == 404:
    print("Google App Credentials not found.")
else:
    print(f"Unexpected status code received: {response.status_code}. Response text: {response.text}")
"""
