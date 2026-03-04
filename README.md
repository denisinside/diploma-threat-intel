# diploma-threat-intel

Threat intelligence platform: CVE vulnerabilities and credential leaks (combo lists) from Telegram channels.

## Services

- **api-gateway** — REST API, auth, leaks management
- **leak-scraper** — Telegram combo file collector (watcher / full-sync)
- **combo-parser** — RabbitMQ consumer, parses leak files → Elasticsearch
- **cve-parser** — CVE ingestion
- **frontend** — React + TypeScript UI (Tactical / Palantir style)

## Quick Start

```bash
docker-compose up -d   # MongoDB, ES, Redis, RabbitMQ
```

Run API gateway:

```bash
cd services/api-gateway
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Run frontend:

```bash
cd services/frontend
npm install
npm run dev
```

