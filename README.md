# Product Scraper and Processor

This project consists of a Chrome extension and a Python Serverless for scraping product information from web pages and processing it. The scraped data is stored in a Google Sheet and product images are uploaded to Supabase Storage.

## Components

1. Chrome Extension: Captures the HTML of the current page and sends it to the backend.
2. Vercel Python Serverless: Processes the HTML, extracts product information, updates a Google Sheet, and uploads images to Supabase.

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
   git clone https://github.com/teebarg/scraper.git
   cd scraper
   ```

2. Create a `.env` file in the project root with the following contents:

   ```
   FIREBASE_PRIVATE_KEY_ID=private_key_id
   FIREBASE_PRIVATE_KEY=private_key
   FIREBASE_CLIENT_EMAIL=client_email
   FIREBASE_CLIENT_ID=client_id
   FIREBASE_CLIENT_CERT_URL=client_x509_cert_url
   FIREBASE_SERVICE_ACCOUNT_ID=serviceAccountId

   SHEET_ID="sheet_id"

   SUPABASE_URL="supabase_url"
   SUPABASE_KEY="supabase_key"
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
   uv sync
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

2. Run the development server:

   ```
   uvicorn main:app --reload
   ```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
