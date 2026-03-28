import argparse
import os
import sys
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("IKB_USERNAME", "").strip("\"'")
PASSWORD = os.getenv("IKB_PASSWORD", "").strip("\"'")

if not USERNAME or not PASSWORD:
    print("Error: IKB_USERNAME and IKB_PASSWORD environment variables must be set.")
    sys.exit(1)

def run_scraper(date_from: str, date_to: str, filename: str):
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

        print("Navigating to login page...")
        page.goto("https://direkt.ikb.at/grid/index.php?page=login")
        
        print("Logging in...")
        page.wait_for_load_state("networkidle")
        # The login form is loaded via AJAX, so wait for the password field to appear
        page.wait_for_selector("input[type='password']", timeout=15000)
        # Fill username - it's the text input right before the password field
        page.fill("input[type='password']", PASSWORD)
        # Username field: find the visible text input in the login form
        page.locator("input[type='text']").last.fill(USERNAME)
        page.click("button[type='submit'], input[type='submit']")

        print("Waiting for dashboard to load...")
        try:
            page.wait_for_url("**/index.php?page=dashboard*", timeout=15000)
        except TimeoutError:
            # Check if we're still on the login page (= wrong credentials)
            if "page=login" in page.url or page.locator("input[type='password']").is_visible():
                print("Error: Login failed. Please check your IKB_USERNAME and IKB_PASSWORD in .env")
                browser.close()
                sys.exit(1)
            print("Warning: Unexpected page after login, continuing anyway...")

        print("Navigating to Lastprofil/Tageswerte...")
        # Direct navigation instead of clicking
        page.goto("https://direkt.ikb.at/grid/index.php?page=loadprofile")
        page.wait_for_load_state("networkidle")


        print("Selecting Zähler... (Forcing selection via jQuery)")
        try:
            page.evaluate("$('#metCodes').val($('#metCodes option').first().val()).trigger('change');")
        except Exception as e:
            print(f"Could not select Zähler: {e}")

        print(f"Setting timeframe: {date_from} - {date_to}")
        try:
            # The date inputs are readonly, so we use JS (jQuery) to set them and trigger change
            page.evaluate(f"$('#timeRangeFrom').val('{date_from}').trigger('change');")
            page.evaluate(f"$('#timeRangeTo').val('{date_to}').trigger('change');")
        except Exception as e:
            print(f"Could not auto-fill dates: {e}")

        print("Setting Auflösung (resolution) to 15min...")
        try:
            # It's a radio button label with for='ResOpt1'
            page.click("label[for='ResOpt1']", timeout=3000)
        except Exception as e:
            print(f"Could not select 15min resolution: {e}")

        print("Clicking 'Aktualisieren' (Update)...")
        try:
            # Exact ID of the update button
            page.click("#updateFlot", timeout=3000)
        except Exception as e:
            print(f"Could not click Aktualisieren: {e}")

        print("\nWaiting for CSV export button...")
        
        try:
            with page.expect_download(timeout=60000) as download_info:
                try:
                    button = page.locator("button.export-button:has-text('E-Control')").first
                    print("Waiting for download button to appear in the export area (up to 30s)...")
                    button.click(timeout=30000)
                    print("Found download button automatically, clicking...")
                except Exception as e:
                    print(f"Auto-click failed: {e}")
                    
            download = download_info.value
            target_filename = ""
            if filename == "":
                target_filename = download.suggested_filename
            else:
                target_filename = filename
            print(f"\nDownload started: {target_filename}")
            download.save_as(target_filename)
            print(f"Successfully saved to: {target_filename}")
            
        except TimeoutError:
            print("\nTimed out waiting for download. Intervene manually next time!")

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
    args = parser.parse_args()

    # Validate date format
    for label, val in [("--from", args.date_from), ("--to", args.date_to)]:
        try:
            datetime.strptime(val, "%d.%m.%Y")
        except ValueError:
            print(f"Error: {label} date '{val}' is not in DD.MM.YYYY format")
            sys.exit(1)

    if not args.filename:
        iso_from = datetime.strptime(args.date_from, "%d.%m.%Y").strftime("%Y-%m-%d")
        iso_to = datetime.strptime(args.date_to, "%d.%m.%Y").strftime("%Y-%m-%d")
        if iso_from == iso_to:
            args.filename = f"ikb_energy_export_{iso_from}.csv"
        else:
            args.filename = f"ikb_energy_export_{iso_from}_{iso_to}.csv"

    run_scraper(args.date_from, args.date_to, args.filename)
