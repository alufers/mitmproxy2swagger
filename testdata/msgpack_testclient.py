# -*- coding: utf-8 -*-

import msgpack
from testclient import testclient

# Sample MessagePack data
msgpack_data = {"field1": "value1", "field2": "value2"}

testclient(
    "application/msgpack",
    lambda: msgpack.packb(msgpack_data),
    lambda content: msgpack.unpackb(content),
)
