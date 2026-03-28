FROM python:3.12-slim

WORKDIR /app

# 1. Zuerst Python-Pakete installieren (macht den 'playwright' Befehl verfügbar)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Playwright holt sich selbst die exakt passenden apt-Pakete für Debian
RUN playwright install-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY scraper.py .

# 3. Berechtigungen und User (Dein perfekter Block)
RUN groupadd -g 1000 scraper && \
    useradd -m -u 1000 -g 1000 -s /bin/bash scraper && \
    mkdir -p /data && \
    chown -R scraper:scraper /data

USER scraper
RUN playwright install chromium

VOLUME /data
WORKDIR /data

ENTRYPOINT ["python", "/app/scraper.py"]