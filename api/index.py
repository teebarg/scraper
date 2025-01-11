from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import time
import asyncio

from utils import scrape_product, add_or_update_sheet

async def homepage(request):
    return PlainTextResponse("Hello, world!")

async def process_product(request):
    print("POST request received")
    start_time = time.time()

    try:
        # Get request body
        post_data = await request.body()
        post_data = post_data.decode("utf-8")

        # Process the product asynchronously
        scrape_start = time.time()
        product_data = await scrape_product(post_data)
        print(f"Scraping took: {time.time() - scrape_start:.2f} seconds")

        # Update sheet asynchronously
        sheet_start = time.time()
        await add_or_update_sheet(product_data)
        print(f"Sheet update took: {time.time() - sheet_start:.2f} seconds")

        print(f"Total request time: {time.time() - start_time:.2f} seconds")
        return JSONResponse({
            "message": "Processing successful",
            "data": product_data
        })

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({
            "error": "Failed to process HTML content",
            "details": str(e)
        }, status_code=400)

# Route configuration
routes = [
    Route("/", homepage, methods=["GET"]),
    Route("/api", process_product, methods=["POST"])
]

# Middleware configuration
middleware = [
    Middleware(CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"])
]

# Create Starlette application
app = Starlette(
    debug=True,
    routes=routes,
    middleware=middleware
)
