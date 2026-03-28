# IKB Energy Scraper

[🇬🇧 English version (README.md)](README.md)

Dieses Skript automatisiert die Anmeldung im `direkt.ikb.at`-Portal und lädt Ihre Smart Meter Energieverbrauchsdaten im CSV-Format herunter.
Es verwendet Playwright, um einen headless Chromium-Browser zu steuern, und nutzt Stealth-Techniken (wie benutzerdefinierte User-Agents), um Web Application Firewalls (WAF) zu umgehen.

> [!CAUTION]
> **Haftungsausschluss:** Dieses Tool ist nur für den **persönlichen Gebrauch** bestimmt. Das automatisierte Scraping von Webportalen kann gegen die Nutzungsbedingungen Ihres Energieversorgers verstoßen. Die Nutzung erfolgt auf eigene Verantwortung.

## Einrichtung

### Option 1: Mit Docker (Empfohlen)

1. Stellen Sie sicher, dass Docker auf Ihrem System installiert ist.
2. Erstellen Sie das Docker-Image (optional, falls Sie nicht das fertige Image von GHCR nutzen):
   ```bash
   git clone https://github.com/philippthaler/ikb-energy-scraper.git
   cd ikb-energy-scraper
   docker build -t ikb-scraper .
   ```
3. Richten Sie Ihre Zugangsdaten ein. Erstellen Sie eine `.env`-Datei in diesem Verzeichnis:
   ```env
   IKB_USERNAME=meine_email@beispiel.at
   IKB_PASSWORD=mein_passwort123
   ```
4. Erstellen Sie eine `docker-compose.yml`-Datei (oder verwenden Sie die in diesem Repo vorhandene):
   ```yaml
   services:
     ikb-energy-scraper:
       container_name: ikb-energy-scraper
       image: ghcr.io/philippthaler/ikb-energy-scraper:latest
       restart: unless-stopped
       # env_file: .env
       environment:
         IKB_USERNAME: meine_email@beispiel.at
         IKB_PASSWORD: mein_passwort123
       volumes:
         - ./data:/data
       # Führt das Skript im Daemon-Modus aus, täglicher Abruf um 01:00 Uhr
       command: ["--schedule", "01:00", "--log-level", "INFO"]
   ```
5. Starten Sie den Daemon mit Docker Compose. Die CSV-Dateien werden automatisch jeden Tag um 01:00 Uhr im Ordner `data/` gespeichert:
   ```bash
   mkdir -p data
   sudo chown -R $(id -u):$(id -g) data/ # Berechtigungen sicherstellen
   docker-compose up -d
   ```
   *Logs anzeigen: `docker-compose logs -f`*

6. **Alternative: Einmalige Ausführung mit `docker run`:**
   ```bash
   docker run --rm \
     -v ./data:/data \
     -e IKB_USERNAME="meine_email@beispiel.at" \
     -e IKB_PASSWORD="mein_passwort123" \
     ghcr.io/philippthaler/ikb-energy-scraper:latest \
     --from 01.01.2026 --to 28.03.2026 --output test.csv
   ```

### Option 2: Direkt mit Python

1. Stellen Sie sicher, dass Python installiert ist.
2. Initialisieren Sie eine virtuelle Umgebung und installieren Sie die Abhängigkeiten:
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ./venv/bin/playwright install chromium
   ```
3. Richten Sie Ihre Zugangsdaten ein (`.env`-Datei erstellen, siehe oben).
4. Starten Sie das Skript:
   ```bash
   ./venv/bin/python scraper.py
   ```

## Nutzung und CLI-Argumente

Standardmäßig lädt das Skript das Lastprofil für **gestern** mit einer **15-Minuten-Auflösung** im E-Control-CSV-Format herunter.

Sie können den Zeitraum, die Auflösung und den Dateinamen über CLI-Flags anpassen:

```bash
# Standard: Daten von gestern
./venv/bin/python scraper.py

# Benutzerdefinierter Zeitraum
./venv/bin/python scraper.py --from 01.03.2026 --to 27.03.2026

# Nur ein bestimmter Tag
./venv/bin/python scraper.py --from 15.03.2026 --to 15.03.2026

# Eigener Dateiname
./venv/bin/python scraper.py --from 15.03.2026 --to 15.03.2026 --output meine_daten.csv

# Andere Auflösung
./venv/bin/python scraper.py --resolution Monat --from 01.01.2026 --to 28.03.2026

# Anderes Export-Format
./venv/bin/python scraper.py --format csv

# Daemon-Modus (geplante Ausführung)
./venv/bin/python scraper.py --schedule 01:00
```

### Directe Ausführung mit Docker

Wenn Sie Docker Compose nicht verwenden, können Sie Argumente direkt an das Image übergeben:

```bash
# Einmalige Ausführung für einen bestimmten Zeitraum
docker run --rm --env-file .env -v ./data:/data ghcr.io/philippthaler/ikb-energy-scraper:latest --from 01.01.2026 --to 28.03.2026

# Als Hintergrund-Daemon starten
docker run -d --name ikb-scraper --restart unless-stopped --env-file .env -v ./data:/data ghcr.io/philippthaler/ikb-energy-scraper:latest --schedule 01:00
```

*(Bei Verwendung von Docker ohne Compose hängen Sie diese Argumente einfach an den `docker run`-Befehl an).*

### Auflösungen
Verwenden Sie `--resolution`, um die Datengranularität zu wählen. Verfügbare Optionen: `15min` (Standard), `Stunde`, `Tag`, `Woche`, `Monat`.
**Hinweis:** Das Skript prüft die Kompatibilität des Zeitraums:
- `Tag`, `Woche` oder `Monat` sind nicht erlaubt, wenn Start- und Enddatum identisch sind.
- `Woche` oder `Monat` sind nicht erlaubt, wenn beide Daten in derselben Kalenderwoche liegen.
- `Monat` ist nicht erlaubt, wenn beide Daten im selben Monat liegen.

### Export-Formate
Verwenden Sie `--format`, um den Exporttyp zu wählen. Verfügbare Optionen: `e-control` (Standard), `csv`.
**Hinweis:** `e-control` ist nur für die `15min`-Auflösung verfügbar. Bei anderen Auflösungen wird automatisch das Standard-`csv` verwendet.

### Datumsformate und Benennung
* Daten für `--from` und `--to` **müssen** im Format `TT.MM.JJJJ` vorliegen.
* Ohne `--output` generiert das Skript automatisch chronologisch sortierbare Dateinamen im ISO 8601 Format, z.B.: `ikb_energy_export_2026-03-27.csv`.
