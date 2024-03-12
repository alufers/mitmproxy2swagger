# -*- coding: utf-8 -*-
import msgpack
from testserver import TestServerHandler, launchServerWith


class MessagePackHandler(TestServerHandler):
    def transform_data(self, raw_data):
        data = msgpack.unpackb(raw_data, raw=False)

        # Add a new field to the data
        data["new_field"] = "Added Field"

        # Encode the modified data as MessagePack
        return msgpack.packb(data, use_bin_type=True)


if __name__ == "__main__":
    launchServerWith(MessagePackHandler)
