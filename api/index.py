from http.server import BaseHTTPRequestHandler
import json

from utils import add_or_update_sheet, scrape_product, upload_to_firebase


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Hello, world!".encode("utf-8"))
        return

    def do_POST(self):
        print("POST request received")
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")
        try:
            product_data = scrape_product(post_data)
            add_or_update_sheet(product_data)
            upload_to_firebase(
                image_name=product_data["image_name"],
                image_url=product_data["image_url"],
            )

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            response = json.dumps(
                {"message": "Processing successful", "data": product_data}
            )
            self.wfile.write(response.encode("utf-8"))
        except Exception as e:
            print(e, "error.....")
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_message = (
                '{"error": "Failed to process HTML content", "details": "'
                + str(e)
                + '"}'
            )
            self.wfile.write(error_message.encode("utf-8"))

        return
