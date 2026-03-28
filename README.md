# IKB Energy Scraper

This script automates logging into the `direkt.ikb.at` portal and downloading your smart meter energy consumption data in CSV format. 
It uses Playwright to drive a headless Chromium browser, utilizing stealth techniques (like custom User-Agents) to bypass Web Application Firewalls (WAF) that might otherwise block automated access.

## Setup

### Option 1: Using Docker (Recommended)

1. Ensure you have Docker installed on your system.
2. Build the Docker image:
   ```bash
   docker build -t ikb-scraper .
   ```
3. Set up your login credentials. Create a `.env` file in this directory:
   ```env
   IKB_USERNAME=myemail@example.com
   IKB_PASSWORD=mypassword123
   ```
4. Run the scraper. It will save the resulting CSV file into a `data/` folder on your host machine:
   ```bash
   mkdir -p data
   sudo chown -R $(id -u):$(id -g) data/ # Ensure correct permissions
   docker run --env-file .env -v ./data:/data ikb-scraper
   ```

### Option 2: Using Python directly

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
4. Run the scraper:
   ```bash
   ./venv/bin/python scraper.py
   ```

## Usage and CLI Arguments

By default, the script will download the energy consumption profile for **yesterday** at a **15-minute resolution** in the E-Control CSV format. 

You can customize the date range and the output filename using CLI flags:

```bash
# Default: yesterday's data
./venv/bin/python scraper.py

# Custom date range
./venv/bin/python scraper.py --from 01.03.2026 --to 27.03.2026

# Just a specific day
./venv/bin/python scraper.py --from 15.03.2026 --to 15.03.2026

# Custom output file
./venv/bin/python scraper.py --from 15.03.2026 --to 15.03.2026 --output custom_file.csv
```

*(If using Docker, simply append these arguments to the `docker run` command).*

### Date Formats and Output Naming
* Input dates for `--from` and `--to` **must** be in `DD.MM.YYYY` format.
* If no `--output` flag is specified, the script automatically generates chronologically sortable filenames using ISO 8601 formatting, for example: `ikb_energy_export_2026-03-27.csv` or `ikb_energy_export_2026-03-01_2026-03-27.csv`.
