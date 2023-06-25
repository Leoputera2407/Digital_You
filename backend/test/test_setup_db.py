import requests
import json

from digital_twin.db.connectors.google_drive import upsert_db_google_app_cred
from digital_twin.utils.clients import get_supabase_client
from digital_twin.server.model import GoogleAppWebCredentials, GoogleAppCredentials

supabase = get_supabase_client()
BUCKET_NAME = "Access Token Bucket"
BUCKET_SOURCE = "localhost_google_app_credentials.json"
destination ="./localhost_google_app_credentials.json"
"""
with open(destination, 'wb+') as f:
  res = supabase.storage.from_(BUCKET_NAME).download(BUCKET_SOURCE)
  f.write(res)
"""

with open(destination, 'r') as f:
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
app_credentials = GoogleAppCredentials(**credentials['web'])
res = upsert_db_google_app_cred(app_credentials.dict())

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