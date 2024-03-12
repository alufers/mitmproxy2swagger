# -*- coding: utf-8 -*-
import json

from testserver import TestServerHandler, launchServerWith


class GenericKeysHandler(TestServerHandler):
    def transform_data(self, raw_data):
        data = json.loads(raw_data)

        data["numeric"]["0000"] = {
            "lorem": "ipsum",
            "dolor": "sit",
            "amet": "consectetur",
        }
        data["uuid"]["123e4567-e89b-12d3-a456-426614174002"] = {
            "lorem": "ipsum",
            "dolor": "sit",
            "amet": "consectetur",
        }
        data["mixed"]["0000"] = {
            "lorem": "ipsum",
            "dolor": "sit",
            "amet": "consectetur",
        }

        # Encode the modified data
        return bytes(json.dumps(data), "utf-8")


if __name__ == "__main__":
    launchServerWith(GenericKeysHandler)
