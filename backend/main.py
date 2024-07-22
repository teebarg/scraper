from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import settings
from core.logging import logger
from utils import add_or_update_sheet, scrape_product, upload_to_firebase

app = FastAPI(title=settings.PROJECT_NAME, openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    # allow_origins=[
    #     str(origin).rstrip("/")
    #     for origin in settings.BACKEND_CORS_ORIGINS
    # ],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HTMLContent(BaseModel):
    html: str


# Root path
@app.get("/api/")
async def root():
    return {"message": "Hello World!!!"}


@app.get("/api/health-check")
async def health_check():
    return {"message": "Server is running"}


@app.post("/api/process_html")
async def process_html(content: HTMLContent):
    try:
        product_data = scrape_product(content.html)
        add_or_update_sheet(product_data)
        upload_to_firebase(
            image_name=product_data["image_name"], image_url=product_data["image_url"]
        )

        return {"message": "Processing successful", "data": product_data}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e)) from e
