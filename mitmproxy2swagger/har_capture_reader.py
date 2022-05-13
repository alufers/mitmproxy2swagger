import os
from tokenize import Number
import json_stream
# a heuristic to determine if a fileis a har archive
def har_archive_heuristic(file_path: str) -> Number:
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

class HarCaptureReader:
    def __init__(self, file_path: str):
        self.file_path = file_path
    def captured_requests(self) -> Iterator[HarFlowWrapper]:
        with open(self.file_path, 'r') as f:
        data = json_stream.load(f)
        for entry in data['log']['entries']:
            yield HarFlowWrapper(entry.persistent())

