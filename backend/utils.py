import os
import re
import unicodedata

import firebase_admin
import gspread
import requests
from bs4 import BeautifulSoup
from firebase_admin import credentials, storage

from core.config import settings
from core.logging import logger


def create_slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = text.strip("-")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text


def scrape_product(html_content) -> dict[str, str]:
    soup = BeautifulSoup(html_content, "html.parser")

    try:
        product_name = soup.select_one("h1.product-title").text.strip()
        product_price = soup.select_one("p.actual-price").text.strip().replace("$", "")
        product_image_url = soup.select_one(
            "div.product-image-wrapper.product-wrapper-inline picture source"
        )["srcset"]
        product_desc = soup.select_one("div.product-description-list li").text.strip()

        image_url = product_image_url.split(" ")[0]
        slug = create_slug(product_name)
        image_name = f"{slug}.png"

    except Exception as e:
        logger.error(e)
        raise Exception(e) from e

    return {
        "name": product_name,
        "slug": slug,
        "description": product_desc,
        "price": product_price,
        "image_url": image_url,
        "image_name": image_name,
    }


def add_or_update_sheet(product_data: dict) -> None:
    gc = gspread.service_account_from_dict(settings.FIREBASE_CRED)

    # Open the Google Sheet (replace with your sheet ID)
    sht = gc.open_by_key(settings.SHEET_ID).sheet1

    sht.append_row(
        [
            product_data["name"],
            product_data["slug"],
            product_data["description"],
            float(product_data["price"]) * 1500,
            0,
            product_data["image_name"],
            4.7,
        ]
    )


def upload_to_firebase(image_name: str, image_url: str):
    try:
        cred = credentials.Certificate(settings.FIREBASE_CRED)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                cred, {"storageBucket": settings.STORAGE_BUCKET}
            )

        # Download the image
        response = requests.get(image_url)
        with open(image_name, "wb") as f:
            f.write(response.content)

        # Upload to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(f"products/{image_name}")
        blob.upload_from_filename(image_name)

        # Clean up the local file
        os.remove(image_name)
    except Exception as e:
        logger.error(e)
        raise Exception(e) from e
