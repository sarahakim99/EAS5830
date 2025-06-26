import requests
import json

PINATA_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiIzMTJmZTU0MS1kMTRkLTRiY2UtYWUyZi01ZDRlNGYyOGM1NzgiLCJlbWFpbCI6InNhcmFoYWtpbTk5QGhvdG1haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6IjNjMmRkZTQ1NDk1MDY2MzMwNjRjIiwic2NvcGVkS2V5U2VjcmV0IjoiNGJjYzM3NjFkNGU3OTQ2MjQ5MWMyMWUzMzdkMDU2YWVhNWQ4MjU5NzQ5MGMyMzY1OThjNTZhMjJhOWNiNGQ0NCIsImV4cCI6MTc4MjQ2NjUwM30.j3DZmuHmUgg3V1oyGA1jukOXNpQGjKqhm3yT4yY3OGQ"

def pin_to_ipfs(data):
    assert isinstance(data, dict), "pin_to_ipfs expects a dictionary"
    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "Authorization": f"Bearer {PINATA_JWT}",
        "Content-Type": "application/json"
    }
    payload = {
        "pinataContent": data
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    res_json = response.json()
    return res_json["IpfsHash"]  # This is the CID

def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), "get_from_ipfs expects a string CID"
    # Use a public IPFS gateway to fetch the JSON
    url = f"https://gateway.pinata.cloud/ipfs/{cid}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    assert isinstance(data, dict), "get_from_ipfs should return a dict"
    return data
