# -*- coding: utf-8 -*-

import msgpack
import requests  # type: ignore

# Sample MessagePack data
msgpack_data = {"field1": "value1", "field2": "value2"}


url = "http://localhost:8082"
headers = {"Content-Type": "application/msgpack"}
response = requests.post(
    url,
    data=msgpack.packb(msgpack_data, use_bin_type=True),
    headers=headers,
    proxies={"http": "http://localhost:8080", "https": "http://localhost:8080"},
)

# Print the response
print(response.status_code)
print(response.headers)

# convert the response data from MessagePack to JSON
data = msgpack.unpackb(response.content, raw=False)
print(data)
