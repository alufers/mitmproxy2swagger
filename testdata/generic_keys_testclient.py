# -*- coding: utf-8 -*-

import json

import requests  # type: ignore

# Sample data
data = {
    "1234": {
        "lorem": "ipsum",
        "dolor": "sit",
        "amet": "consectetur",
    },
    "5678": {
        "lorem": "ipsum",
        "dolor": "sit",
        "amet": "consectetur",
    },
}


url = "http://localhost:8082"
headers = {"Content-Type": "application/json"}
response = requests.post(
    url,
    data=json.dumps(data),
    headers=headers,
    proxies={"http": "http://localhost:8080", "https": "http://localhost:8080"},
)

# Print the response
print(response.status_code)
print(response.headers)

# convert the response data from MessagePack to JSON
data = json.loads(response.content)
print(data)
