# -*- coding: utf-8 -*-
import http.server
import socketserver
from typing import Type


class TestServerHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        raw_data = self.rfile.read(content_length)

        try:
            # Decode received data

            print(raw_data)
            modified_data = self.transform_data(raw_data)

            # Send the response
            self.send_response(200)
            self.send_header("Content-type", self.headers["Content-type"])
            self.send_header("Content-length", len(modified_data))
            self.end_headers()
            self.wfile.write(modified_data)

        except Exception as e:
            print(f"Error processing request: {str(e)}")
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error processing request: {str(e)}".encode())

    def transform_data(self, raw_data):
        raise NotImplementedError("Subclasses must implement this method")


def launchServerWith(handler: Type[TestServerHandler]):
    PORT = 8082
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving on port {PORT}")
        httpd.serve_forever()
