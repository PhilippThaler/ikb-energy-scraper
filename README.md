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
4. Create a `docker-compose.yml` file (or use the one provided in this repo):
   ```yaml
   services:
     scraper:
       build: .
       image: ikb-scraper
       container_name: ikb-scraper
       restart: unless-stopped
       env_file:
         - .env
       volumes:
         - ./data:/data
       # Run in daemon mode, scraping every day at 01:00 AM
       command: ["--schedule", "01:00", "--log-level", "INFO"]
   ```
5. Start the daemon using Docker Compose. It will automatically download the resulting CSV files into a `data/` folder on your host machine every day at 01:00 AM:
   ```bash
   mkdir -p data
   sudo chown -R $(id -u):$(id -g) data/ # Ensure correct permissions
   docker-compose up -d
   ```
   *To view logs: `docker-compose logs -f`*

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

You can customize the date range, the data resolution, and the output filename using CLI flags:

```bash
# Default: yesterday's data
./venv/bin/python scraper.py

# Custom date range
./venv/bin/python scraper.py --from 01.03.2026 --to 27.03.2026

# Just a specific day
./venv/bin/python scraper.py --from 15.03.2026 --to 15.03.2026

# Custom output file
./venv/bin/python scraper.py --from 15.03.2026 --to 15.03.2026 --output custom_file.csv

# Custom resolution
./venv/bin/python scraper.py --resolution Monat --from 01.01.2026 --to 28.03.2026

# Export format
./venv/bin/python scraper.py --format csv

# Daemon mode
./venv/bin/python scraper.py --schedule 01:00
```

*(If using Docker without compose, simply append these arguments to the `docker run` command).*

### Resolutions
Use `--resolution` to choose your data granularity. Available options: `15min` (default), `Stunde`, `Tag`, `Woche`, `Monat`.
**Note:** The script enforces date compatibility based on your chosen resolution:
- You cannot use `Tag`, `Woche`, or `Monat` if `--from` and `--to` are the same date.
- You cannot use `Woche` or `Monat` if `--from` and `--to` fall within the **same calendar week**.
- You cannot use `Monat` if `--from` and `--to` fall within the **same month**.

### Export Formats
Use `--format` to choose your preferred export type. Available options: `e-control` (default), `csv`.
**Note:** `e-control` is solely available for the `15min` resolution. If you attempt to use it with any other resolution, it will automatically fall back to downloading standard `csv`.

### Date Formats and Output Naming
* Input dates for `--from` and `--to` **must** be in `DD.MM.YYYY` format.
* If no `--output` flag is specified, the script automatically generates chronologically sortable filenames using ISO 8601 formatting, for example: `ikb_energy_export_2026-03-27.csv` or `ikb_energy_export_2026-03-01_2026-03-27.csv`.
