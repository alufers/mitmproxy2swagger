import os
import json_stream
from typing import Iterator


# a heuristic to determine if a fileis a har archive
def har_archive_heuristic(file_path: str) -> int:
    val = 0
    # if has the har extension
    if file_path.endswith('.har'):
        val += 15
    # read the first 2048 bytes
    with open(file_path, 'rb') as f:
        data = f.read(2048)
        # if file contains only ascii characters
        if data.decode('utf-8', 'ignore').isprintable() is True:
            val += 40
        # if first character is a '{'
        if data[0] == '{':
            val += 15
        # if it contains the word '"WebInspector"'
        if b'"WebInspector"' in data:
            val += 15
        # if it contains the word '"entries"'
        if b'"entries"' in data:
            val += 15
        # if it contains the word '"version"'
        if b'"version"' in data:
            val += 15
    return val


class HarFlowWrapper:
    def __init__(self, flow: dict):
        self.flow = flow

    def get_url(self):
        return self.flow['request']['url']

    def get_method(self):
        return self.flow['request']['method']

    def get_request_headers(self):
        headers = {}
        for kv in self.flow['request']['headers']:
            k = kv['name']
            v = kv['value']
            # create list on key if it does not exist
            headers[k] = headers.get(k, [])
            headers[k].append(v)

    def get_request_body(self):
        if 'request' in self.flow and 'postData' in self.flow['request'] and 'text' in self.flow['request']['postData']:
            return self.flow['request']['postData']['text']
        return None

    def get_response_status_code(self):
        return self.flow['response']['status']

    def get_response_reason(self):
        return self.flow['response']['statusText']

    def get_response_headers(self):
        headers = {}
        for kv in self.flow['response']['headers']:
            k = kv['name']
            v = kv['value']
            # create list on key if it does not exist
            headers[k] = headers.get(k, [])
            headers[k].append(v)
        return headers

    def get_response_body(self):
        if 'response' in self.flow and 'content' in self.flow['response'] and 'text' in self.flow['response']['content']:
            return self.flow['response']['content']['text']
        return None


class HarCaptureReader:
    def __init__(self, file_path: str, progress_callback=None):
        self.file_path = file_path
        self.progress_callback = progress_callback

    def captured_requests(self) -> Iterator[HarFlowWrapper]:
        har_file_size = os.path.getsize(self.file_path)
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json_stream.load(f)
            for entry in data['log']['entries'].persistent():
                if self.progress_callback:
                    self.progress_callback(f.tell() / har_file_size)
                yield HarFlowWrapper(entry)
