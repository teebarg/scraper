import os
import re
import unicodedata
import uuid

import firebase_admin
import gspread
import requests
from bs4 import BeautifulSoup
from firebase_admin import credentials, storage

FIREBASE_CRED = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
    "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN"),
    "serviceAccountId": os.getenv("FIREBASE_SERVICE_ACCOUNT_ID"),
}


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
        raise Exception(e) from e

    return {
        "id": f"prod_{uuid.uuid4().hex[:24].upper()}",
        "name": product_name,
        "slug": slug,
        "description": product_desc,
        "price": product_price,
        "image_url": image_url,
        "image_name": image_name,
    }


def add_or_update_sheet(product_data: dict) -> None:
    SHEET_ID = os.getenv("SHEET_ID")
    gc = gspread.service_account_from_dict(FIREBASE_CRED)

    # Open the Google Sheet (replace with your sheet ID)
    sht = gc.open_by_key(SHEET_ID).sheet1
    # sht.append_row(
    #     [
    #         product_data["name"],
    #         product_data["slug"],
    #         product_data["description"],
    #         float(product_data["price"]) * 1500,
    #         0,
    #         product_data["image_name"],
    #         4.7,
    #     ]
    # )

    # Find the next available row (get the number of rows)
    next_row = len(sht.get_all_values()) + 1
    print(next_row)

    # Update specific columns (e.g., Name in column 1, Country in column 3)
    sht.update(f'A{next_row}', [[product_data["id"]]])
    sht.update(f'B{next_row}', [[product_data["slug"]]])
    sht.update(f'C{next_row}', [[product_data["name"]]])
    # sht.update(f'D{next_row}', [[product_data["price"]]])
    sht.update(f'E{next_row}', [[product_data["description"]]])
    sht.update(f'F{next_row}', [["published"]])
    sht.update(f'T{next_row}', [["TRUE"]])
    sht.update(f'V{next_row}', [["Default Shipping Profile"]])
    sht.update(f'W{next_row}', [["default"]])
    variant_id = f"variant_{uuid.uuid4().hex[:24].upper()}"
    sht.update(f'X{next_row}', [[variant_id]])
    sht.update(f'AB{next_row}', [["20"]])
    sht.update(f'AC{next_row}', [["FALSE"]])
    sht.update(f'AD{next_row}', [["TRUE"]])
    sht.update(f'AE{next_row}', [["0"]])
    sht.update(f'O{next_row}', [["0"]])


def upload_to_firebase(image_name: str, image_url: str):
    STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")

    try:
        cred = credentials.Certificate(FIREBASE_CRED)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {"storageBucket": STORAGE_BUCKET})

        # Download the image
        response = requests.get(image_url)
        image_content = response.content

        # Upload to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(f"products/{image_name}")
        blob.upload_from_string(image_content, content_type="image/png")

    except Exception as e:
        raise Exception(e) from e
