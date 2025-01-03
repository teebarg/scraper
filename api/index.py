from http.server import BaseHTTPRequestHandler
import json
import time

from utils import add_or_update_sheet, scrape_product


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Hello, world!".encode("utf-8"))
        return

    def do_POST(self):
        print("POST request received")
        start_time = time.time()

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")

        try:
            scrape_start = time.time()
            product_data = scrape_product(post_data)
            print(f"Scraping took: {time.time() - scrape_start:.2f} seconds")

            sheet_start = time.time()
            add_or_update_sheet(product_data)
            print(f"Sheet update took: {time.time() - sheet_start:.2f} seconds")

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

        print(f"Total request time: {time.time() - start_time:.2f} seconds")
        return
