import requests
import json

from digital_twin.config.app_config import OPENAI_API_KEY
from digital_twin.db.model import DBAPIKeyType, DBSupportedModelType
from digital_twin.db.llm import delete_model_config

base_url = "http://localhost:8080/model"  
# Replace the user_id here
user_id = "ca908470-d13f-476a-8b8f-c96907645860"
key_value = OPENAI_API_KEY  
key_type = DBAPIKeyType.OPENAI_API_KEY.value
headers = {"Content-Type": "application/json"}

model_config = {
    "supported_model_enum": DBSupportedModelType.GPT3_5,
    "temperature": 0.5
}

api_keys = []
model_configs = []
api_id = []
model_config_id = []

# Test store_model_api_key
url = f"{base_url}/api-key/{user_id}"
payload = {"key_type": key_type, "key_value": key_value}
response = requests.post(url, headers=headers, data=json.dumps(payload))
assert response.status_code == 200
api_keys.append(key_type)
api_id.append(response.json()["id"])
print(f"Stored API Key: {key_type}")

# Test get_model_api_key
url = f"{base_url}/api-key/{user_id}?key_type={key_type}"
response = requests.get(url)
assert response.status_code == 200
assert response.json()["key_type"] == key_type
assert response.json()["key_value"] == key_value[-4:]  # it only returns the last 4 characters
print(f"Retrieved API Key: {key_type}")

# Test upsert_model_config_endpoint
url = f"{base_url}/model-config/{user_id}"
response = requests.post(url, headers=headers, data=json.dumps(model_config))
assert response.status_code == 200
model_config_id.append(response.json()["id"])
print(f"Upserted Model Config: {response.json()['id']}")

# Test get_model_config_by_user_endpoint
url = f"{base_url}/model-config/{user_id}"
response = requests.get(url)
assert response.status_code == 200
assert response.json() == model_config  # assuming the response is the same model_config
print(f"Retrieved Model Config: {response.json()}")

# Test delete_model_api_key
url = f"{base_url}/api-key/{user_id}?key_type={key_type}"
response = requests.delete(url)
assert response.status_code == 200
api_keys.remove(key_type)
print(f"Deleted API Key: {key_type}")


# At the end of tests, clean up the test model
for model_id in model_configs:
    delete_model_config(user_id, model_id)
    print(f"Deleted Model Config: {model_id}")

assert len(api_keys) == 0, "All API Keys should be deleted"
assert len(model_configs) == 0, "All Model Configs should be deleted"