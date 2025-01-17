import os
import re
import unicodedata
import uuid
import time
import concurrent.futures
from typing import List, Tuple

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

        # Prepare all image uploads (main + additional)
        upload_start = time.time()
        image_uploads = []

        # Only add main image if URL exists
        if image_url:
            image_uploads.append((image_url, image_name))

        # Add additional images
        for i, img in enumerate(image_urls[:5]):  # Limit to 5 additional images
            if img:  # Only add if URL is not empty
                image_uploads.append((img, f"{slug}-{i}.png"))

        # Upload all images in parallel
        all_uploaded_urls = parallel_image_upload(image_uploads) if image_uploads else []
        print(f"All image uploads took: {time.time() - upload_start:.2f} seconds")

        # First URL is the main image, rest are additional
        image_url = all_uploaded_urls[0] if all_uploaded_urls else ""
        product_images = all_uploaded_urls[1:] if len(all_uploaded_urls) > 1 else []

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
    """Update Google Sheet with product data"""
    try:
        SHEET_ID = os.getenv("SHEET_ID")
        gc = gspread.service_account_from_dict(FIREBASE_CRED)
        sht = gc.open_by_key(SHEET_ID).sheet1

        # Find the next available row
        all_values = sht.get_all_values()
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

        # Update the entire row at once
        sht.update(f'A{next_row}:M{next_row}', [row_data])

    except Exception as e:
        print(f"Error updating sheet: {e}")
        raise


def upload_to_firebase(image_url: str, image_name: str) -> str:
    STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")

    try:
        # Initialize Firebase if not already initialized
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
        print(f"Firebase upload error for {image_name}: {str(e)}")
        raise Exception(f"Failed to upload {image_name}: {str(e)}") from e


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


def parallel_image_upload(image_urls: List[Tuple[str, str]]) -> List[str]:
    """Upload multiple images in parallel"""
    uploaded_urls = {}  # Changed to dict to maintain mapping

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(upload_to_firebase, url, name): (url, name, idx)  # Added index
            for idx, (url, name) in enumerate(image_urls)
        }

        for future in concurrent.futures.as_completed(future_to_url):
            url, name, idx = future_to_url[future]
            try:
                result = future.result()
                uploaded_urls[idx] = result  # Store with index as key
            except Exception as e:
                print(f"Failed to upload {name}: {str(e)}")
                uploaded_urls[idx] = ""  # Store empty string for failed uploads

    # Convert back to ordered list
    ordered_urls = [uploaded_urls[i] for i in range(len(image_urls))]
    return ordered_urls
