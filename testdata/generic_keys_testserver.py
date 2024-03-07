# -*- coding: utf-8 -*-
import http.server
import json
import socketserver


class GenericKeysHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        raw_data = self.rfile.read(content_length)

        try:
            # Decode received data

            print(raw_data)
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
            modified_data = bytes(json.dumps(data), "utf-8")

            # Send the response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", len(modified_data))
            self.end_headers()
            self.wfile.write(modified_data)

        except Exception as e:
            print(f"Error processing request: {str(e)}")
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error processing request: {str(e)}".encode())


if __name__ == "__main__":
    PORT = 8082

    with socketserver.TCPServer(("", PORT), GenericKeysHandler) as httpd:
        print(f"Serving on port {PORT}")
        httpd.serve_forever()
