# Product Scraper and Processor

This project consists of a Chrome extension and a FastAPI backend for scraping product information from web pages and processing it. The scraped data is stored in a Google Sheet and product images are uploaded to Firebase Storage.

## Components

1. Chrome Extension: Captures the HTML of the current page and sends it to the backend.
2. FastAPI Backend: Processes the HTML, extracts product information, updates a Google Sheet, and uploads images to Firebase.

## Setup

### Prerequisites

- Python 3.9+
- Google Cloud project with Sheets API enabled
- Firebase project
- Docker (for containerized deployment)

### Chrome Extension Setup

1. Navigate to `chrome://extensions/` in your Chrome browser.
2. Enable "Developer mode" in the top right corner.
3. Click "Load unpacked" and select the `chrome_extension` directory.

### Backend Setup

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/product-scraper.git
   cd product-scraper
   ```

2. Create a `.env` file in the project root with the following contents:

   ```
   GOOGLE_SHEETS_CREDENTIALS_PATH=/app/google_sheets_credentials.json
   GOOGLE_SHEETS_ID=your_google_sheet_id
   FIREBASE_CREDENTIALS_PATH=/app/firebase_credentials.json
   FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
   ```

3. Place your Google Sheets and Firebase credential files in the project root directory.

4. Build and run the Docker container:

   ```
   docker build -t product-scraper .
   docker run -p 8000:8000 --env-file .env product-scraper
   ```

## Usage

1. Navigate to a product page in your Chrome browser.
2. Click on the extension icon and then click "Capture HTML".
3. The extension will send the HTML to the backend for processing.
4. Check your Google Sheet and Firebase Storage for the updated information.

## Development

To run the backend locally for development:

1. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Run the FastAPI server:

   ```
   uvicorn main:app --reload
   ```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
