import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("IKB_USERNAME", "").strip("\"'")
PASSWORD = os.getenv("IKB_PASSWORD", "").strip("\"'")

if not USERNAME or not PASSWORD:
    logging.error("Error: IKB_USERNAME and IKB_PASSWORD environment variables must be set.")
    sys.exit(1)

def run_scraper(date_from: str, date_to: str, filename: str, resolution: str, format_choice: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        # Remove the webdriver flag that WAFs detect
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logging.info("Navigating to login page...")
        page.goto("https://direkt.ikb.at/grid/index.php?page=login")
        
        logging.info("Logging in...")
        page.wait_for_load_state("networkidle")
        # The login form is loaded via AJAX, so wait for the password field to appear
        page.wait_for_selector("input[type='password']", timeout=15000)
        # Fill username - it's the text input right before the password field
        page.fill("input[type='password']", PASSWORD)
        # Username field: find the visible text input in the login form
        page.locator("input[type='text']").last.fill(USERNAME)
        page.click("button[type='submit'], input[type='submit']")

        logging.info("Waiting for dashboard to load...")
        try:
            page.wait_for_url("**/index.php?page=dashboard*", timeout=15000)
        except TimeoutError:
            # Check if we're still on the login page (= wrong credentials)
            if "page=login" in page.url or page.locator("input[type='password']").is_visible():
                logging.error("Error: Login failed. Please check your IKB_USERNAME and IKB_PASSWORD in .env")
                browser.close()
                sys.exit(1)
            logging.warning("Warning: Unexpected page after login, continuing anyway...")

        logging.info("Navigating to Lastprofil/Tageswerte...")
        # Direct navigation instead of clicking
        page.goto("https://direkt.ikb.at/grid/index.php?page=loadprofile")
        page.wait_for_load_state("networkidle")


        logging.info("Selecting Zähler... (Forcing selection via jQuery)")
        try:
            page.evaluate("$('#metCodes').val($('#metCodes option').first().val()).trigger('change');")
        except Exception as e:
            logging.error(f"Could not select Zähler: {e}")

        logging.info(f"Setting timeframe: {date_from} - {date_to}")
        try:
            # The date inputs are readonly, so we use JS (jQuery) to set them and trigger change
            page.evaluate(f"$('#timeRangeFrom').val('{date_from}').trigger('change');")
            page.evaluate(f"$('#timeRangeTo').val('{date_to}').trigger('change');")
        except Exception as e:
            logging.error(f"Could not auto-fill dates: {e}")

        logging.info(f"Setting Auflösung (resolution) to {resolution}...")
        try:
            # Click the label containing the exact resolution text
            page.click(f"label:has-text('{resolution}')", timeout=3000)
        except Exception as e:
            logging.error(f"Could not select {resolution} resolution: {e}")

        logging.info("Clicking 'Aktualisieren' (Update)...")
        try:
            # Exact ID of the update button
            page.click("#updateFlot", timeout=3000)
        except Exception as e:
            logging.error(f"Could not click Aktualisieren: {e}")

        logging.info("Waiting for CSV export button...")
        
        try:
            with page.expect_download(timeout=60000) as download_info:
                try:
                    button_text = "E-Control" if (format_choice == "e-control" and resolution == "15min") else "CSV"
                    if format_choice == "e-control" and resolution != "15min":
                        logging.warning("Warning: E-Control format is only available for 15min resolution. Falling back to standard CSV.")
                    
                    button = page.locator(f"button.export-button:has-text('{button_text}')").first
                    logging.info("Waiting for download button to appear in the export area (up to 30s)...")
                    button.click(timeout=30000)
                    logging.info("Found download button automatically, clicking...")
                except Exception as e:
                    logging.error(f"Auto-click failed: {e}")
                    
            download = download_info.value
            target_filename = ""
            if filename == "":
                target_filename = download.suggested_filename
            else:
                target_filename = filename
            logging.info(f"Download started: {target_filename}")
            download.save_as(target_filename)
            logging.info(f"Successfully saved to: {target_filename}")
            
        except TimeoutError:
            logging.error("Timed out waiting for download. Intervene manually next time!")

        page.wait_for_timeout(3000)
        browser.close()

if __name__ == "__main__":
    yesterday = (datetime.now() - timedelta(1)).strftime("%d.%m.%Y")

    parser = argparse.ArgumentParser(description="Scrape energy data from direkt.ikb.at")
    parser.add_argument("--from", dest="date_from", default=yesterday,
                        help="Start date in DD.MM.YYYY format (default: yesterday)")
    parser.add_argument("--to", dest="date_to", default=yesterday,
                        help="End date in DD.MM.YYYY format (default: yesterday)")
    parser.add_argument("--output", dest="filename", default="",
                        help="Filename for the downloaded CSV (default: Lastprofil_<from>_<to>.csv)")
    parser.add_argument("--resolution", dest="resolution", default="15min",
                        choices=["15min", "Stunde", "Tag", "Woche", "Monat"],
                        help="Data resolution (default: 15min)")
    parser.add_argument("--format", dest="format_choice", default="e-control",
                        choices=["csv", "e-control"],
                        help="Export format (default: e-control)")
    parser.add_argument("--log-level", dest="log_level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Set the logging level (default: INFO)")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Validate date format
    try:
        dt_from = datetime.strptime(args.date_from, "%d.%m.%Y")
        dt_to = datetime.strptime(args.date_to, "%d.%m.%Y")
    except ValueError as e:
        logging.error(f"Error parse date: {e}")
        sys.exit(1)

    # Validate resolution date span compatibility
    if args.resolution in ["Tag", "Woche", "Monat"] and dt_from == dt_to:
        logging.error(f"Error: Resolution '{args.resolution}' is not allowed when --from and --to are the same date.")
        sys.exit(1)

    if args.resolution in ["Woche", "Monat"]:
        # Check if dates fall within the same calendar week
        if dt_from.isocalendar()[:2] == dt_to.isocalendar()[:2]:
            logging.error(f"Error: Resolution '{args.resolution}' requires spanning multiple weeks.")
            sys.exit(1)

    if args.resolution == "Monat":
        if dt_from.year == dt_to.year and dt_from.month == dt_to.month:
            logging.error("Error: Resolution 'Monat' requires spanning multiple months.")
            sys.exit(1)

    if not args.filename:
        iso_from = dt_from.strftime("%Y-%m-%d")
        iso_to = dt_to.strftime("%Y-%m-%d")
        if iso_from == iso_to:
            args.filename = f"ikb_energy_export_{iso_from}.csv"
        else:
            args.filename = f"ikb_energy_export_{iso_from}_{iso_to}.csv"

    run_scraper(args.date_from, args.date_to, args.filename, args.resolution, args.format_choice)
