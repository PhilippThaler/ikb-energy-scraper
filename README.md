# IKB Energy Scraper

[🇩🇪 Deutsche Version (README_DE.md)](README_DE.md)

This script automates logging into the `direkt.ikb.at` portal and downloading your smart meter energy consumption data in CSV format. 
It uses Playwright to drive a headless Chromium browser, utilizing stealth techniques (like custom User-Agents) to bypass Web Application Firewalls (WAF) that might otherwise block automated access.

> [!CAUTION]
> **Disclaimer:** This tool is intended for **personal use only**. Automated scraping of web portals may be against the terms of service of your utility provider. Use this responsibly and at your own risk.

## Setup

### Option 1: Using Docker (Recommended)

1. Ensure you have Docker installed on your system.
2. Build the Docker image:
   ```bash
   # Optional: Build it yourself, or just use the pre-built GHCR image below
   git clone https://github.com/philippthaler/ikb-energy-scraper.git
   cd ikb-energy-scraper
   docker build -t ikb-scraper .
   ```
3. Set up your login credentials. Create a `.env` file in this directory:
   ```env
   IKB_USERNAME=myemail@example.com
   IKB_PASSWORD=mypassword123
   ```
4. Look at the `docker-compose.yml` file. You have two options for credentials:

   **Option A: Plaintext (Easy)**
   ```yaml
   environment:
     IKB_USERNAME: myemail@example.com
     IKB_PASSWORD: mypassword123
   ```

   **Option B: Docker Secrets (Recommended)**
   ```yaml
   environment:
     IKB_USERNAME_FILE: /run/secrets/ikb_username
     IKB_PASSWORD_FILE: /run/secrets/ikb_password
   secrets:
     - ikb_username
     - ikb_password
   # And define the files in the top-level secrets block
   ```
5. Start the daemon using Docker Compose. It will automatically download the resulting CSV files into a `data/` folder on your host machine every day at 01:00 AM:
   ```bash
   mkdir -p data
   sudo chown -R $(id -u):$(id -g) data/ # Ensure correct permissions
   docker-compose up -d
   ```
   *To view logs: `docker-compose logs -f`*

6. **Alternative: Run once using `docker run`:**
   ```bash
   docker run --rm \
     -v ./data:/data \
     -e IKB_USERNAME="meine_email@beispiel.at" \
     -e IKB_PASSWORD="mein_passwort123" \
     ghcr.io/philippthaler/ikb-energy-scraper:latest \
     --from 01.01.2026 --to 28.03.2026 --output test.csv
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

### Running with Docker (Directly)

If you aren't using Docker Compose, you can pass arguments directly to the image:

```bash
# Run for a specific date range once
docker run --rm --env-file .env -v ./data:/data ghcr.io/philippthaler/ikb-energy-scraper:latest --from 01.01.2026 --to 28.03.2026

# Run as a background daemon
docker run -d --name ikb-scraper --restart unless-stopped --env-file .env -v ./data:/data ghcr.io/philippthaler/ikb-energy-scraper:latest --schedule 01:00

# Run with Docker Secrets (best practice)
docker run --rm \
  -v ./data:/data \
  -v ./secrets/username.txt:/run/secrets/ikb_username:ro \
  -v ./secrets/password.txt:/run/secrets/ikb_password:ro \
  -e IKB_USERNAME_FILE=/run/secrets/ikb_username \
  -e IKB_PASSWORD_FILE=/run/secrets/ikb_password \
  ghcr.io/philippthaler/ikb-energy-scraper:latest
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
