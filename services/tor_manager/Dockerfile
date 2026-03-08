FROM python:3.11-slim

WORKDIR /app

# Install tor and required system packages
RUN apt-get update && apt-get install -y \
    tor \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create volumes and set permissions
RUN mkdir -p /tor_keys /etc/tor /var/lib/tor && \
    chown -R debian-tor:debian-tor /tor_keys /etc/tor /var/lib/tor && \
    chmod 700 /tor_keys /var/lib/tor

COPY . .

# Default script will manage tor process internally
CMD ["python", "-u", "manager.py"]
