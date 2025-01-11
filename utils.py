import os
import re
import unicodedata
import uuid
import time
import concurrent.futures
from typing import List, Tuple
import aiohttp
import asyncio
from gspread_asyncio import AsyncioGspreadClientManager

import firebase_admin
import gspread
import requests
from bs4 import BeautifulSoup
from firebase_admin import credentials, storage
from rembg import remove
from PIL import Image
import io
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

# FIREBASE_CRED = {
#     "type": "service_account",
#     "project_id": os.getenv("FIREBASE_PROJECT_ID"),
#     "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
#     "private_key": os.getenv("FIREBASE_PRIVATE_KEY"),
#     "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
#     "client_id": os.getenv("FIREBASE_CLIENT_ID"),
#     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#     "token_uri": "https://oauth2.googleapis.com/token",
#     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#     "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
#     "universe_domain": "googleapis.com",
#     "serviceAccountId": os.getenv("FIREBASE_SERVICE_ACCOUNT_ID"),
# }

# Config will be read from environment variables and/or ".env" files.
config = Config(".env")

DEBUG = config('DEBUG', cast=bool, default=False)
# DATABASE_URL = config('DATABASE_URL')
FIREBASE_PROJECT_ID = config('FIREBASE_PROJECT_ID')
FIREBASE_PRIVATE_KEY_ID = config('FIREBASE_PRIVATE_KEY_ID')
FIREBASE_PRIVATE_KEY = config('FIREBASE_PRIVATE_KEY')
FIREBASE_CLIENT_EMAIL = config('FIREBASE_CLIENT_EMAIL')
FIREBASE_CLIENT_ID = config('FIREBASE_CLIENT_ID')
FIREBASE_CLIENT_CERT_URL = config('FIREBASE_CLIENT_CERT_URL')
FIREBASE_SERVICE_ACCOUNT_ID = config('FIREBASE_SERVICE_ACCOUNT_ID')

STORAGE_BUCKET = config('STORAGE_BUCKET')
SHEET_ID = config('SHEET_ID')
# SECRET_KEY = config('SECRET_KEY', cast=Secret)
# ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=CommaSeparatedStrings)

FIREBASE_CRED = {
    "type": "service_account",
    "project_id": FIREBASE_PROJECT_ID,
    "private_key_id": FIREBASE_PRIVATE_KEY_ID,
    "private_key": FIREBASE_PRIVATE_KEY,
    "client_email": FIREBASE_CLIENT_EMAIL,
    "client_id": FIREBASE_CLIENT_ID,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": FIREBASE_CLIENT_CERT_URL,
    "universe_domain": "googleapis.com",
    "serviceAccountId": FIREBASE_SERVICE_ACCOUNT_ID,
}

print(FIREBASE_CRED)
print(FIREBASE_PROJECT_ID)

def create_slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = text.strip("-")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text


async def scrape_product_async(html_content) -> dict[str, str]:
    soup = BeautifulSoup(html_content, "html.parser")

    try:
        # Extract product name
        product_name = soup.select_one("h1.product-title")
        product_name = product_name.text.strip() if product_name else "Unknown Product"

        # Extract product price
        product_price = soup.select_one("p.actual-price")
        product_price = product_price.text.strip().replace("$", "") if product_price else "0.00"

        # Extract main product image
        product_image_url = soup.select_one("div.product-image-wrapper.product-wrapper-inline picture source")
        image_url = product_image_url["srcset"].split(" ")[0] if product_image_url else ""

        # Extract product description
        product_desc = soup.select_one("div.product-description-list li")
        product_desc = product_desc.text.strip() if product_desc else "No description available."

        # Extract image URLs - with error checking
        image_elements = soup.select("div.preview-and-social-media-icons ul li picture img")
        image_urls = []
        for img in image_elements:
            if img.get('src'):  # Check if src attribute exists
                image_urls.append(img['src'])

        # If no <img> tags are found, try <source> elements
        if not image_urls:
            image_elements = soup.select("div.preview-and-social-media-icons ul li picture source")
            for source in image_elements:
                if source.get('srcset'):  # Check if srcset attribute exists
                    image_urls.append(source['srcset'].split(" ")[0])

        # Generate the slug
        slug = create_slug(product_name)
        image_name = f"{slug}.png"

        # Convert image uploads to async
        upload_start = time.time()
        image_uploads = []

        if image_url:
            image_uploads.append((image_url, image_name))

        for i, img in enumerate(image_urls[:5]):
            if img:
                image_uploads.append((img, f"{slug}-{i}.png"))

        all_uploaded_urls = await parallel_image_upload_async(image_uploads) if image_uploads else []
        print(f"All image uploads took: {time.time() - upload_start:.2f} seconds")

        # First URL is the main image, rest are additional
        image_url = all_uploaded_urls[0] if all_uploaded_urls else ""
        product_images = all_uploaded_urls[1:] if len(all_uploaded_urls) > 1 else []

    except Exception as e:
        print(f"Error creating product: {e}")
        raise

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


async def upload_to_firebase_async(image_url: str, image_name: str) -> str:
    # STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")
    storage_bucket = STORAGE_BUCKET
    print("storage_bucket")
    print(storage_bucket)

    try:
        # Initialize Firebase (remains sync as it's one-time)
        cred = credentials.Certificate(FIREBASE_CRED)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})

        # Download the image asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                response.raise_for_status()
                image_data = await response.read()

        # Process image (remove background) - remains sync as it's CPU-bound
        input_image = Image.open(io.BytesIO(image_data))
        output_image = remove(input_image)

        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # Upload to Firebase (remains sync as Firebase SDK is not async)
        bucket = storage.bucket()
        blob = bucket.blob(f"products/{image_name}")
        blob.upload_from_string(img_byte_arr, content_type="image/png")
        blob.make_public()

        return blob.public_url

    except Exception as e:
        print(f"Firebase upload error for {image_name}: {str(e)}")
        raise


# Helper to upload image to Firebase
async def upload_image_to_firebase(image_url: str, image_name: str) -> str:
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


def batch_update_sheet(sheet, updates: List[Tuple[str, list]]) -> None:
    """Perform batch updates to Google Sheet"""
    try:
        # Convert updates list to batch request format
        batch_updates = {
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {
                    'range': update[0],  # Cell range (e.g., 'B46')
                    'values': update[1]   # Values to update
                }
                for update in updates
            ]
        }

        # Perform the batch update
        sheet.batch_update(batch_updates)

    except Exception as e:
        print(f"Batch update error: {str(e)}")
        raise


async def parallel_image_upload_async(image_urls: List[Tuple[str, str]]) -> List[str]:
    """Upload multiple images in parallel using asyncio"""
    tasks = []
    for idx, (url, name) in enumerate(image_urls):
        task = asyncio.create_task(upload_to_firebase_async(url, name))
        tasks.append((idx, task))

    uploaded_urls = {}
    for idx, task in tasks:
        try:
            result = await task
            uploaded_urls[idx] = result
        except Exception as e:
            print(f"Failed to upload image {idx}: {str(e)}")
            uploaded_urls[idx] = ""

    return [uploaded_urls[i] for i in range(len(image_urls))]


async def add_or_update_sheet_async(product_data: dict) -> None:
    """Async version of sheet updates"""
    try:
        # SHEET_ID = os.getenv("SHEET_ID")
        sheet_id = SHEET_ID
        print("sheet_id")
        print(sheet_id)

        # Create async credentials
        agcm = AsyncioGspreadClientManager(lambda: FIREBASE_CRED)
        agc = await agcm.authorize()

        # Open spreadsheet
        spreadsheet = await agc.open_by_key(sheet_id)
        sheet = await spreadsheet.get_worksheet(0)

        # Get all values
        all_values = await sheet.get_all_values()
        next_row = len(all_values) + 1

        # Search for existing product
        for i, row in enumerate(all_values):
            if len(row) > 1 and row[1] == product_data["name"]:
                next_row = i + 1
                break

        # Ensure price is a string and convert to float
        try:
            price = float(str(product_data["price"]).replace('$', '').strip()) * 1500
        except (ValueError, TypeError):
            price = 0.0
            print(f"Warning: Could not convert price {product_data['price']} to float")

        # Ensure images is a string
        images = product_data.get("images", "")
        if isinstance(images, list):
            images = "|".join(str(img) for img in images)

        # Prepare row data
        row_data = [
            "",  # Column A is empty
            str(product_data.get("name", "")),
            str(product_data.get("slug", "")),
            str(product_data.get("description", "")),
            price,
            0,  # Column F is empty
            10,
            4.8,
            str(product_data.get("image_url", "")),
            True,
            "",  # Column K is empty
            "",  # Column L is empty
            "",  # Column M is empty
            images
        ]

        # Update sheet
        await sheet.update(f'A{next_row}:M{next_row}', [row_data])

    except Exception as e:
        print(f"Error updating sheet: {e}")
        raise
