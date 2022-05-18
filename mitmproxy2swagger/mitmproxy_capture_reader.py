from typing import Iterator
from mitmproxy import io as iom, http
from mitmproxy.exceptions import FlowReadException
import os


def mitmproxy_dump_file_huristic(file_path: str) -> int:
    val = 0
    if 'flow' in file_path:
        val += 1
    if 'mitmproxy' in file_path:
        val += 1
    # read the first 2048 bytes
    with open(file_path, 'rb') as f:
        data = f.read(2048)
        # if file contains non-ascii characters
        if data.decode('utf-8', 'ignore').isprintable() is False:
            val += 50
        # if first character of the byte array is a digit
        if str(data[0]).isdigit() is True:
            val += 5
        # if it contains the word status_code
        if b'status_code' in data:
            val += 5
        if b'regular' in data:
            val += 10
    return val


class MitmproxyFlowWrapper:
    def __init__(self, flow: http.HTTPFlow):
        self.flow = flow

    def get_url(self):
        return self.flow.request.url

    def get_method(self):
        return self.flow.request.method

    def get_request_headers(self):
        headers = {}
        for k, v in self.flow.request.headers.items(multi=True):
            # create list on key if it does not exist
            headers[k] = headers.get(k, [])
            headers[k].append(v)
        return headers

    def get_request_body(self):
        return self.flow.request.content

    def get_response_status_code(self):
        return self.flow.response.status_code

    def get_response_reason(self):
        return self.flow.response.reason

    def get_response_headers(self):
        headers = {}
        for k, v in self.flow.response.headers.items(multi=True):
            # create list on key if it does not exist
            headers[k] = headers.get(k, [])
            headers[k].append(v)
        return headers

    def get_response_body(self):
        return self.flow.response.content


class MitmproxyCaptureReader:
    def __init__(self, file_path, progress_callback=None):
        self.file_path = file_path
        self.progress_callback = progress_callback

    def captured_requests(self) -> Iterator[MitmproxyFlowWrapper]:
        with open(self.file_path, 'rb') as logfile:
            logfile_size = os.path.getsize(self.file_path)
            freader = iom.FlowReader(logfile)
            try:
                for f in freader.stream():
                    if self.progress_callback:
                        self.progress_callback(logfile.tell() / logfile_size)
                    if isinstance(f, http.HTTPFlow):
                        if f.response is None:
                            print("[warn] flow without response: {}".format(f.request.url))
                            continue
                        yield MitmproxyFlowWrapper(f)
            except FlowReadException as e:
                print(f"Flow file corrupted: {e}")
