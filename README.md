# IKB Energy Scraper

This script automates logging into the `direkt.ikb.at` portal and downloading the energy consumption CSV.
It uses Playwright to drive a headed Chromium browser to handle complex PHP viewstates and login flows securely.

## Setup

1. Make sure you have Python installed.
2. Initialize a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ./venv/bin/playwright install chromium
   ```

3. Set up your login credentials. Create a `.env` file in this directory:
   ```env
   IKB_USERNAME=myemail@example.com
   IKB_PASSWORD=mypassword123
   ```
   (Alternatively, you can export these as environment variables in your terminal).

## Running the Scraper

Run the script using python:

```bash
./venv/bin/python scraper.py
```

The script will launch a browser window. It attempts to:
- Navigate to the login page and auto-fill your credentials.
- Wait for you to login and for the dashboard to load.
- Automatically navigate to the `consumptionstatistics` page.
- Look for the `e-control` CSV button and click it to download the file directly to your current folder.

**Note:** Since this runs in headed mode (`headless=False`), you can simply intervene via the browser window if any layout elements have changed and the script asks you to click a button manually.
