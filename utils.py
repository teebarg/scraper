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
        # Extract product name
        product_name = soup.select_one("h1.product-title")
        product_name = product_name.text.strip() if product_name else "Unknown Product"
        
        # Extract product price
        product_price = soup.select_one("p.actual-price")
        product_price = product_price.text.strip().replace("$", "") if product_price else "0.00"
        
        product_image_url = soup.select_one("div.product-image-wrapper.product-wrapper-inline picture source")
        image_url = product_image_url["srcset"].split(" ")[0] if product_image_url else ""
        
        # Extract product description
        product_desc = soup.select_one("div.product-description-list li")
        product_desc = product_desc.text.strip() if product_desc else "No description available."

        # Extract image URLs from all <li> tags within the preview-and-social-media-icons section
        image_elements = soup.select("div.preview-and-social-media-icons ul li picture img")
        image_urls = [img['src'] for img in image_elements if img.get('src')]
        
        # If no <img> tags are found, fallback to <source> elements
        if not image_urls:
            image_elements = soup.select("div.preview-and-social-media-icons ul li picture source")
            image_urls = [source['srcset'].split(" ")[0] for source in image_elements if source.get('srcset')]
        
        # Generate the slug
        slug = create_slug(product_name)
        image_name = f"{slug}.png"

        # # Use the first image as the main image
        # image_url = image_urls[0] if image_urls else ""

        # Use the first image as the main image and upload it to Firebase
        # image_url = image_urls[0] if image_urls else ""
        image_url = upload_to_firebase(image_url, image_name)

        # Upload all other images and store their Firebase URLs
        product_images = [upload_to_firebase(img, f"{slug}_{i}.png") for i, img in enumerate(image_urls)]
    
    except Exception as e:
        print(f"Error creating product: {e}")
        raise Exception(f"Failed to scrape product due to: {e}") from e

    return {
        "id": f"prod_{uuid.uuid4().hex[:24].upper()}",
        "name": product_name,
        "slug": slug,
        "description": product_desc,
        "price": product_price,
        "image_url": image_url,
        "image_name": image_name,
        "images": "|".join(product_images),
    }


def add_or_update_sheet(product_data: dict) -> None:
    SHEET_ID = os.getenv("SHEET_ID")
    gc = gspread.service_account_from_dict(FIREBASE_CRED)

    # Open the Google Sheet (replace with your sheet ID)
    sht = gc.open_by_key(SHEET_ID).sheet1

    # Find the next available row (get the number of rows)
    next_row = len(sht.get_all_values()) + 1

    # Get all values in the sheet (you can limit columns if needed)
    all_values = sht.get_all_values()

    # Search for the product by slug (assuming slugs are in column C, i.e. index 2)
    # product_row_index = None
    for i, row in enumerate(all_values):
        if len(row) > 1 and row[1] == product_data["name"]:  # Checking slug in column C
            next_row = i + 1  # Add 1 because get_all_values is 0-indexed, but Sheets is 1-indexed
            break

    # Update specific columns (e.g., Name in column 1, Country in column 3)
    sht.update(f'B{next_row}', [[product_data["name"]]])
    sht.update(f'C{next_row}', [[product_data["slug"]]])
    sht.update(f'D{next_row}', [[product_data["description"]]])
    sht.update(f'E{next_row}', [[float(product_data["price"]) * 1500]])
    # sht.update(f'F{next_row}', [[0]])
    sht.update(f'G{next_row}', [[10]])
    sht.update(f'H{next_row}', [[4.8]])
    sht.update(f'I{next_row}', [[product_data["image_url"]]])
    sht.update(f'J{next_row}', [[True]])
    # sht.update(f'K{next_row}', [[""]])
    # sht.update(f'L{next_row}', [[""]])
    sht.update(f'M{next_row}', [[product_data["images"]]])


def upload_to_firebase(image_url: str, image_name: str) -> str:
    STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")

    try:
        cred = credentials.Certificate(FIREBASE_CRED)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {"storageBucket": STORAGE_BUCKET})

        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()  # Ensure image is downloaded successfully

        # Upload to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(f"products/{image_name}")
        blob.upload_from_string(response.content, content_type="image/png")

        # Make the file publicly accessible
        blob.make_public()

        # Return the public URL of the image
        return blob.public_url

    except Exception as e:
        raise Exception(e) from e
    

# Helper to upload image to Firebase
def upload_image_to_firebase(image_url: str, image_name: str) -> str:
    try:
        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()  # Ensure image is downloaded successfully

        # Upload the image to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(f'product_images/{image_name}')
        
        # Upload the image content to Firebase
        blob.upload_from_string(response.content, content_type='image/png')
        
        # Make the file publicly accessible
        blob.make_public()

        # Return the public URL of the image
        return blob.public_url
    except Exception as e:
        raise Exception(f"Failed to upload image to Firebase: {e}") from e
