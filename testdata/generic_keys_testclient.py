# -*- coding: utf-8 -*-

import json

from testclient import testclient

# Sample data
data = {
    "numeric": {
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
    },
    "uuid": {
        "123e4567-e89b-12d3-a456-426614174000": {
            "lorem": "ipsum",
            "dolor": "sit",
            "amet": "consectetur",
        },
        "123e4567-e89b-12d3-a456-426614174001": {
            "lorem": "ipsum",
            "dolor": "sit",
            "amet": "consectetur",
        },
    },
    "mixed": {
        "1234": {
            "lorem": "ipsum",
            "dolor": "sit",
            "amet": "consectetur",
        },
        "123e4567-e89b-12d3-a456-426614174000": {
            "lorem": "ipsum",
            "dolor": "sit",
            "amet": "consectetur",
        },
    },
}

testclient(
    "application/json",
    lambda: json.dumps(data),
    lambda content: json.loads(content),
)
