import requests
import json
import random
import time 

from digital_twin.config.app_config import APP_HOST, APP_PORT
from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import InputType
from digital_twin.db.model import IndexingStatus
from digital_twin.utils.clients import get_supabase_client

base_url = f"http://{APP_HOST}:{APP_PORT}/connector" 
# Please adjust to the correct USER_ID
supabase_user_id = "134c22cc-e810-4050-a60a-f7076f747c48"

headers = {"Content-Type": "application/json"}

def random_name_gen() -> str:
    return f"Test_connector_{random.randint(0, 100000)}"

def random_source() -> str:
    return random.choice([source.value for source in DocumentSource])

def random_input_type() -> str:
    return random.choice([input_type.value for input_type in InputType])


def generate_random_index_attempts(connector_credential_pairs: list[tuple[int, int]]) -> list[int]:
    client = get_supabase_client()
    index_ids = []
    statuses = [status.value for status in IndexingStatus]
    for connector_id, credential_id in connector_credential_pairs:
        for status in statuses:
            # Insert a random number of index attempts for each status
            for _ in range(random.randint(1, 3)):
                data = {
                    'connector_id': connector_id,
                    'credential_id': credential_id,
                    'status': status
                }
                response = client.table('index_attempt').insert(data).execute()
                print(response)
                index_ids.append(response.data[0]['id'])
                
                # Wait for 10 seconds
                time.sleep(random.randint(0,3))
    return index_ids

def delete_index_attempts(index_ids: list[int]):
    client = get_supabase_client()
    for index_id in index_ids:
        response = client.table('index_attempt').delete().eq('id', index_id).execute()
        print(response)


fixed_updated_status = random_source()
connector_ids = []
credential_ids = []
index_attempt_ids = []
associated_connect_credentials = []

url = f"{base_url}/create?supabase_user_id={supabase_user_id}"
payload = {
    "name": random_name_gen(),
    "user_id": supabase_user_id,
    "source": random_source(),  # Replace with your DocumentSource Enum value
    "input_type": random_input_type(),  # Replace with your InputType Enum value
    "connector_specific_config": {"key": "value"},  # Replace with your specific configuration
    "refresh_freq": 300,  # Replace with your refresh frequency
    "disabled": False,
}
response = requests.post(url, headers=headers, data=json.dumps(payload))
connector_id = response.json()['id']
connector_ids.append(connector_id)
print(f"Created connector with ID: {connector_id}")

url = f"{base_url}/create?supabase_user_id={supabase_user_id}"
payload = {
    "name": random_name_gen(),
    "user_id": supabase_user_id,
    "source": random_source(),  # Replace with your DocumentSource Enum value
    "input_type": random_input_type(),  # Replace with your InputType Enum value
    "connector_specific_config": {"key": "value"},  # Replace with your specific configuration
    "refresh_freq": 300,  # Replace with your refresh frequency
    "disabled": False,
}
response = requests.post(url, headers=headers, data=json.dumps(payload))
connector_id_2 = response.json()['id']
connector_ids.append(connector_id_2)
print(f"Created connector with ID: {connector_id_2}")

url = f"{base_url}/{connector_id}"
params = {"supabase_user_id": supabase_user_id}
response = requests.get(url, headers=headers, params=params)
print("Get connector by ID response: ", response.json())

url = f"{base_url}/{connector_id_2}"
params = {"supabase_user_id": supabase_user_id}
response = requests.get(url, headers=headers, params=params)
print("Get connector by ID response: ", response.json())

url = f"{base_url}/{connector_id}"
params = {"supabase_user_id": supabase_user_id}
payload = {
    "name": random_name_gen(),
    "user_id": supabase_user_id,
    "source": fixed_updated_status,  
    "input_type": "poll",  # Replace with your InputType Enum value
    "connector_specific_config": {"key": "new_value"},  # Replace with your specific configuration
    "refresh_freq": 600,  # Replace with your refresh frequency
    "disabled": False,
}
response = requests.patch(url, headers=headers, params=params, data=json.dumps(payload))
print("Update connector response: ", response.json())

url = f"{base_url}/credential?supabase_user_id={supabase_user_id}"

payload = {
    "credential_json": {"credential_key": "credential_value"},
    "public_doc": False,
}
response = requests.post(url, headers=headers, data=json.dumps(payload))
response_json = response.json()
credential_id = response_json['id']
credential_ids.append(credential_id)
print(f"Created credential with ID: {credential_id}")


# 4. Create a new credential
url = f"{base_url}/credential?supabase_user_id={supabase_user_id}"

payload = {
    "credential_json": {"credential_key": "credential_value"},
    "public_doc": False,
}
response = requests.post(url, headers=headers, data=json.dumps(payload))
response_json = response.json()
credential_id_2 = response_json['id']
credential_ids.append(credential_id_2)
print(f"Created credential with ID: {credential_id_2}")

# 5. Get the credential by ID
url = f"{base_url}/credential/{credential_id}?supabase_user_id={supabase_user_id}"
response = requests.get(url, headers=headers)
print("Get credential by ID response: ", response.json())

# 6. Associate the credential with the connector
url = f"{base_url}/{connector_id}/credential/{credential_id}"
params = {"supabase_user_id": supabase_user_id}
response = requests.put(url, headers=headers, params=params)
associated_connect_credentials.append((connector_id, credential_id))
print("Associate credential to connector response: ", response.json())


# 6. Associate the credential with the connector
url = f"{base_url}/{connector_id_2}/credential/{credential_id_2}"
params = {"supabase_user_id": supabase_user_id}
response = requests.put(url, headers=headers, params=params)
associated_connect_credentials.append((connector_id_2, credential_id_2))
print("Associate credential to connector response: ", response.json())


# Call the /latest-index-attempt endpoint
response = requests.get(f"{base_url}/latest-index-attempt", params={"supabase_user_id": supabase_user_id})
latest_index_attempts = response.json()
print(json.dumps(latest_index_attempts, indent=2))


index_attempt_ids.extend(generate_random_index_attempts(associated_connect_credentials))

response = requests.get(f"{base_url}/latest-index-attempt/{fixed_updated_status}", params={"supabase_user_id": supabase_user_id})
latest_index_attempts_for_source = response.json()
print(json.dumps(latest_index_attempts_for_source, indent=2))

response = requests.get(f"{base_url}/indexing-status", params={"supabase_user_id": supabase_user_id})
connector_indexing_status = response.json()
print(json.dumps(connector_indexing_status, indent=2))

response = requests.get(f"{base_url}/list", params={"supabase_user_id": supabase_user_id})
connectors = response.json()
print(json.dumps(connectors, indent=2))

# Disassociate the credential from the connector
for connector_id, credential_id in associated_connect_credentials:
    url = f"{base_url}/{connector_id}/credential/{credential_id}"
    params = {"supabase_user_id": supabase_user_id}
    response = requests.delete(url, headers=headers, params=params)
    print("Dissociate credential from connector response: ", response.json())

# Delete IndexAttempts
delete_index_attempts(index_attempt_ids)


# Delete the credential
for credential_id in credential_ids:
    url = f"{base_url}/credential/{credential_id}"
    params = {"supabase_user_id": supabase_user_id}
    response = requests.delete(url, headers=headers, params=params)
    print("Delete credential response: ", response.json())

# Delete the connector
for connector_id in connector_ids:
    url = f"{base_url}/{connector_id}"
    params = {"supabase_user_id": supabase_user_id}
    response = requests.delete(url, headers=headers, params=params)
    print("Delete connector response: ", response.json())
