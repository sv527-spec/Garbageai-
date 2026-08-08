# Smart Waste Management & Recycling Platform

AI-powered waste identification, CO2/earnings estimation, recycling-center locator, and ESP32 smart-bin
integration. See `ARCHITECTURE.md` for the full system design and rationale.

## Hosting / going live

- **New to deployment?** Read `HOSTING-SIMPLE.md` — plain-language, click-by-click.
- **Comfortable with deployment?** Read `DEPLOYMENT.md` — the condensed technical version.

## Quick start (local dev)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

- Backend API + docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Run without Docker

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

## ESP32 firmware

See `esp32-firmware/smart_bin/smart_bin.ino` and `esp32-firmware/README.md` for wiring + flashing.

## Repo layout

See "Folder structure" in `ARCHITECTURE.md`.
