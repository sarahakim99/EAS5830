import requests
import json


INFURA_PROJECT_ID = "def845368e8e47529180a15c63d275dc"
INFURA_PROJECT_SECRET = "vlxz8rT+r4FYb/JDC8cZNddHGRff10WIeV4pGOG7cMkDwz5IigLqRg"
INFURA_API_URL = "https://ipfs.infura.io:5001"

def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary"
    # Convert dict to JSON and encode as bytes
    json_bytes = json.dumps(data).encode('utf-8')
    files = {'file': ('data.json', json_bytes)}
    # Auth required for Infura
    response = requests.post(
        INFURA_API_URL + "/api/v0/add",
        files=files,
        auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET)
    )
    response.raise_for_status()
    res_json = response.json()
    cid = res_json["Hash"]
    return cid

def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), f"get_from_ipfs accepts a cid in the form of a string"
    # Infura's /cat endpoint only supports POST, not GET
    params = {'arg': cid}
    response = requests.post(
        INFURA_API_URL + "/api/v0/cat",
        params=params,
        auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET)
    )
    response.raise_for_status()
    data = json.loads(response.text)
    assert isinstance(data, dict), f"get_from_ipfs should return a dict"
    return data
