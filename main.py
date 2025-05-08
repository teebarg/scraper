from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import time
import json

from dotenv import load_dotenv
load_dotenv()

from utils import scrape_product, add_or_update_sheet

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return PlainTextResponse("Hello, world!")


@app.post("/")
async def process_product(request: Request):
    start_time = time.time()
    try:
        body = await request.body()
        html_content = body.decode("utf-8")

        scrape_start = time.time()
        product_data = scrape_product(html_content)
        print(f"Scraping took: {time.time() - scrape_start:.2f} seconds")

        sheet_start = time.time()
        add_or_update_sheet(product_data)
        print(f"Sheet update took: {time.time() - sheet_start:.2f} seconds")

        response = {
            "message": "Processing successful",
            "data": product_data
        }

        return JSONResponse(content=response)

    except Exception as e:
        print("Error:", e)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process HTML content: {str(e)}"
        )
    finally:
        print(f"Total request time: {time.time() - start_time:.2f} seconds")
