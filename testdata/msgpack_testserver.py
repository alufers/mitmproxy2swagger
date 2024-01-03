# -*- coding: utf-8 -*-
import http.server
import socketserver

import msgpack


class MessagePackHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        raw_data = self.rfile.read(content_length)

        try:
            # Decode received MessagePack data

            print(raw_data)
            data = msgpack.unpackb(raw_data, raw=False)

            # Add a new field to the data
            data["new_field"] = "Added Field"

            # Encode the modified data as MessagePack
            modified_data = msgpack.packb(data, use_bin_type=True)

            # Send the response
            self.send_response(200)
            self.send_header("Content-type", "application/msgpack")
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

    with socketserver.TCPServer(("", PORT), MessagePackHandler) as httpd:
        print(f"Serving on port {PORT}")
        httpd.serve_forever()
