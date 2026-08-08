# Smart Waste Management & Recycling Platform — System Architecture

## 1. Purpose & Scope

This document is the engineering blueprint for the platform: a mobile-first web app that identifies
waste from a photo, estimates its weight/value/CO2 impact, connects users to recycling centers, talks
to ESP32-controlled smart bins, and gamifies recycling. It targets users across India, with regional
language support prioritizing the North-East.

This repo ships a **working, runnable scaffold**: real auth, real database schema, real API contracts,
a real (swappable) AI classification service, a real frontend, and real ESP32 firmware. The waste
classifier ships with a heuristic/color-histogram baseline model behind a clean interface — swap in a
trained YOLOv8/v11 or EfficientNet checkpoint without touching any other layer (see `services/ai_classifier.py`).

## 2. Why this stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind | SSR for fast first paint on low-end Android, file-based routing, huge ecosystem, built-in image optimization for camera uploads, easy PWA/offline story via `next-pwa`. |
| Backend | FastAPI (Python) | Async I/O suits camera-upload + AI-inference workloads, native Pydantic validation, auto-generated OpenAPI docs (needed for a system this API-heavy), same language as the AI/ML stack (PyTorch/OpenCV) so the classifier can live in-process or as a sidecar without a language boundary. |
| Database | PostgreSQL | Relational integrity for users/roles/transactions/leaderboards; PostGIS extension available later for real geo-queries on recycling centers. |
| Auth | JWT (access + refresh) with role claims | Stateless, scales horizontally, easy to verify on both API and (future) ESP32 gateway. |
| AI | PyTorch + OpenCV, ONNX Runtime for inference | Standard for vision models; ONNX export lets the model run fast on modest servers or even on-device later. |
| IoT link | ESP32 over Wi-Fi (HTTP) primary, BLE fallback | Wi-Fi HTTP is simplest to secure and debug; BLE is added for offline/no-router deployments (rural collection points). |
| Storage | S3-compatible (AWS S3 or Cloudinary) | Scan images and certificates need durable object storage, not the DB. |
| Deployment | Docker + docker-compose locally; Railway/Render + Vercel in production; GitHub Actions CI | Cheap to start, easy to scale piece by piece. |

## 3. High-level architecture

```
                         ┌─────────────────────────┐
                         │   Next.js Frontend       │
                         │ (Web, installable PWA)   │
                         └────────────┬─────────────┘
                                      │ HTTPS/JSON (JWT)
                                      ▼
                         ┌─────────────────────────┐
                         │   FastAPI Backend        │
                         │  - Auth & RBAC           │
                         │  - Scans/Materials API   │
                         │  - CO2/Earnings calc     │
                         │  - Leaderboard           │
                         │  - Recycling centers     │
                         │  - ESP32 bridge (REST)   │
                         └──┬───────────┬───────────┘
                            │           │
                 ┌──────────▼──┐   ┌────▼─────────┐
                 │ AI Inference │   │ PostgreSQL    │
                 │ Service      │   │ (users, scans,│
                 │ (in-process, │   │ centers, etc.)│
                 │ swappable)   │   └───────────────┘
                 └──────────────┘
                            │
                            │ Wi-Fi HTTP / BLE
                            ▼
                 ┌───────────────────────┐
                 │  ESP32 Smart Bin       │
                 │  - Servo compartments  │
                 │  - Load cell (weight)  │
                 │  - Ultrasonic (fill)   │
                 │  - Status → backend    │
                 └───────────────────────┘
```

## 4. Database schema (PostgreSQL)

Core tables (full DDL lives in `docs/schema.sql`, ORM models in `backend/app/models/`):

- **users** — id, email, phone, password_hash, full_name, role (worker/supervisor/user/admin), district,
  state, language_pref, created_at.
- **materials** — id, code (e.g. `PET`, `GLASS`), category (`plastic`/`glass`/`metal`/`paper`/`organic`/`ewaste`/`textile`),
  polymer_type (nullable, plastics only), biodegradable (bool), recyclable (bool), reusable (bool),
  description, disposal_instructions, recycling_instructions, base_price_per_kg.
- **co2_factors** — material_id (FK), co2_saved_recycle_per_kg, co2_saved_reuse_per_kg, energy_saved_per_kg_kwh,
  landfill_volume_reduced_per_kg_l, tree_equivalent_per_kg, source_note (for transparency).
- **scans** — id, user_id (FK), material_id (FK), image_url, confidence_score, estimated_weight_kg,
  weight_source (`vision`/`load_cell`), weight_confidence, co2_saved_kg, earnings_estimate, device_id
  (nullable, ESP32 that processed it), status, created_at.
- **market_prices** — id, category, price_per_kg, currency, updated_by (FK admin), updated_at, source
  (`admin`/`external_api`).
- **recycling_centers** — id, name, address, lat, lng, phone, operating_hours (JSONB), accepted_materials
  (array of material codes), rating, verified.
- **leaderboard_entries** — materialized/rollup table: user_id, period (`daily`/`monthly`/`alltime`),
  district, state, total_weight_kg, total_co2_kg, total_earnings, streak_days, rank.
- **achievements** / **user_achievements** — badge catalog + earned records.
- **esp32_devices** — id, device_uid, owner_id (FK, supervisor/admin), location, last_seen, firmware_version.
- **collections** (supervisor workflow) — worker_id, area, assigned_by, status, scheduled_for.

Roles are enforced both at the DB level (role enum) and API level (dependency-injected RBAC guards).

## 5. API design

REST, versioned under `/api/v1`, documented automatically via FastAPI's OpenAPI/Swagger UI at `/docs`.
Key resource groups:

- `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`
- `GET/PATCH /users/me`, `GET /users/{id}` (admin/supervisor scoped)
- `POST /scans` (multipart image upload → classification → weight/CO2/earnings response), `GET /scans`,
  `GET /scans/{id}`
- `GET /materials`, `GET /materials/{code}`
- `GET /recycling-centers?lat=&lng=&radius=&material=`
- `GET /leaderboard?period=&scope=district|state|national`
- `GET/PUT /market-prices` (admin write, public read)
- `POST /esp32/{device_id}/command`, `POST /esp32/{device_id}/status` (device → backend heartbeat),
  `WS /esp32/{device_id}/stream` (optional live status)
- `GET/POST /admin/...` (users, centers, CO2 factors, model versions)

Every response that carries a monetary or environmental figure includes the calculation inputs
(emission factor used, price used, weight source) so the UI can show "how we got this number" —
a transparency requirement from the spec.

## 6. AI classification pipeline

1. Client uploads image (or ESP32 camera module posts one later).
2. `services/ai_classifier.py` exposes `classify(image_bytes) -> ClassificationResult`. The shipped
   implementation is a **deterministic, explainable baseline** (color/texture heuristics + a small
   scikit-image feature pipeline) so the whole system works end-to-end without a GPU or training data.
3. To go to production accuracy: train a YOLOv8/v11 classification or detection head on a labeled waste
   dataset (TrashNet, TACO, or your own North-East-India-collected set), export to ONNX, and drop it
   behind the same `classify()` interface — no other file changes.
4. Weight estimation follows the same pattern: `services/weight_estimator.py` uses reference-object
   scaling by default, and reads `load_cell_grams` instead whenever an ESP32 payload includes it.
5. CO2/energy/landfill factors are stored in `co2_factors` (admin-editable) rather than hardcoded, per
   the spec's "transparent, publicly sourced factors" requirement — seeded from published EPA/CPCB
   recycling emission-factor tables (cite sources in the `source_note` column).

## 7. Multi-language architecture

`next-intl` with one JSON message catalog per locale in `frontend/messages/`. Shipped locales:
`en`, `hi` fully translated as the reference pair; `as` (Assamese), `bn` (Bengali), `ne` (Nepali),
`lus` (Mizo), `lep` (Lepcha), `njz`/`nag` (Nagamese) are scaffolded with English fallback strings and
a translation TODO list — adding a language is: drop a new `messages/<locale>.json`, add it to
`i18n/config.ts`. No code changes needed elsewhere.

## 8. ESP32 integration

- **Transport**: Wi-Fi HTTP is the default (simplest, most reliable for fixed bins with router access).
  BLE (via a phone-as-gateway pattern) is implemented as a fallback for sites without Wi-Fi.
- **Flow**: app classifies waste → app (or backend) sends `{category, device_id}` to
  `POST /esp32/{device_id}/command` → backend forwards to the bin over its registered channel → ESP32
  unlocks/opens the matching servo compartment, keeps others locked → auto-closes after a timeout or an
  ultrasonic-confirmed "item deposited" event → posts a status update back.
- **Extensibility**: firmware is written with a `SensorModule` interface so load cells, ultrasonic fill
  sensors, RFID readers, and a camera module can be added as independent modules without touching the
  core command-dispatch loop.

## 9. Security

- Passwords hashed with bcrypt (via `passlib`).
- JWT access tokens short-lived (15 min) + rotating refresh tokens.
- RBAC dependency guards on every mutating endpoint.
- Rate limiting on `/auth/*` and `/scans` (slowapi).
- Image uploads validated (MIME sniffing + size cap) before hitting the classifier.
- ESP32 devices authenticate with a per-device shared secret (HMAC-signed requests), not a shared API key.
- All secrets via environment variables, never committed (`.env.example` provided, `.env` gitignored).

## 10. Folder structure

```
smart-waste-platform/
├── ARCHITECTURE.md
├── docker-compose.yml
├── .github/workflows/ci.yml
├── docs/schema.sql
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/        # config, security, database
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── api/v1/        # routers
│   │   ├── services/      # AI classifier, CO2 calc, weight estimator, ESP32 bridge
│   │   └── tests/
│   ├── alembic/            # migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                # Next.js App Router pages
│   ├── components/
│   ├── lib/                 # API client, auth context
│   ├── messages/             # i18n JSON per locale
│   ├── package.json
│   └── Dockerfile
└── esp32-firmware/
    └── smart_bin/smart_bin.ino
```

## 11. Build order (what's implemented in this scaffold vs. next steps)

Implemented now: DB models + migrations, JWT auth + RBAC, scans/materials/CO2/earnings pipeline end to
end with the baseline classifier, recycling centers CRUD + read API, leaderboard rollup endpoint,
market price admin endpoints, ESP32 command/status REST contract + working firmware, i18n-ready frontend
with landing/auth/scan/dashboard/leaderboard/recycling-center pages, Docker Compose for local dev, CI
pipeline for lint+test.

Deliberately left as documented next steps (too large for one pass, and dependent on your data/hardware):
training a production-accuracy vision model on a real labeled dataset, full translations for the six
non-reference languages, Google Maps JS SDK wiring (needs your API key), payment/payout rails for
converting "earnings estimate" into real payouts, and production TLS/secrets setup on your chosen host.
