# Using Ghost Bullet

## Prerequisites
- Docker
- Docker Compose

## Quick Start
1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Build and start the services:
   ```bash
   docker compose up -d --build
   ```
3. Open your browser and navigate to `http://localhost:8008` to access the Ghost Bullet dashboard.

## Dashboard Usage
- **Add a Site**: Click "Create New Site", provide an internal host/port (e.g., `my_app_container:80`), and an optional vanity prefix (e.g., `ghost`).
- **Deploy**: Once created, click "Deploy". The Tor Manager will spin up the necessary `torrc` and reload the Tor service.
- **Vanity Addresses**: If a vanity prefix is provided, the vanity worker will pick it up and generate the matching key, updating the DB when complete.
