import requests
import json


projectId = "def845368e8e47529180a15c63d275dc"
projectSecret = "vlxz8rT+r4FYb/JDC8cZNddHGRff10WIeV4pGOG7cMkDwz5IigLqRg"
endpoint = "https://ipfs.infura.io:5001"

def pin_to_ipfs(data):
    assert isinstance(data, dict), "pin_to_ipfs expects a dictionary"
    # Convert dict to JSON and encode as bytes
    json_bytes = json.dumps(data).encode('utf-8')
    files = {'file': ('data.json', json_bytes)}
    response = requests.post(endpoint + "/api/v0/add", files=files, auth=(projectId, projectSecret))
    response.raise_for_status()
    # Parse the response to get the hash (CID)
    res_json = response.json()
    cid = res_json["Hash"]
    return cid

def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), "get_from_ipfs expects a string CID"
    params = {"arg": cid}
    response = requests.post(endpoint + "/api/v0/cat", params=params, auth=(projectId, projectSecret))
    response.raise_for_status()
    data = json.loads(response.text)
    assert isinstance(data, dict), "get_from_ipfs should return a dict"
    return data

# Example usage:
if __name__ == "__main__":
    test_dict = {"hello": "world", "number": 42}
    cid = pin_to_ipfs(test_dict)
    print("Pinned CID:", cid)
    fetched = get_from_ipfs(cid)
    print("Fetched from IPFS:", fetched)
