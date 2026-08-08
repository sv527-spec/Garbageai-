# Deployment Guide

How to get this platform online. Three parts need hosting — the **frontend** (Next.js), the **backend**
(FastAPI), and the **database** (PostgreSQL) — plus one wrinkle for the **ESP32 bins** (see section 5).

---

## 1. Recommended setup

| Piece | Host | Cost |
|---|---|---|
| Frontend (Next.js) | **Vercel** | Free on Hobby *for non-commercial use*; $20/user/mo Pro if this becomes a real product |
| Backend (FastAPI) | **Render** or **Railway** | Render free tier works for demos; ~$7/mo Starter for always-on |
| Database (PostgreSQL) | **Neon** | Free tier: 0.5 GB storage, no 30-day expiry |
| Scan images | **Cloudinary** free tier | Free up to ~25 GB bandwidth/mo |

**Why this split:** Vercel is built by the Next.js team so the frontend deploy is effectively zero-config.
FastAPI needs a long-running container, which Render/Railway do well and Vercel does not. Neon is the
pick for the database over Render's own free Postgres because **Render's free database is deleted 30 days
after creation** — fine for a demo, fatal if you forget. Neon's free tier doesn't expire.

**Important licensing note:** Vercel's Hobby plan is restricted to personal, non-commercial use. For a
college project or demo you're fine. The moment this earns money or is used by an organization, you need
Pro ($20/user/mo) or you're in breach of their terms.

### Cheapest realistic monthly cost
- **Demo / college project:** ₹0 — Vercel Hobby + Render free + Neon free. Caveat: Render's free backend
  sleeps after 15 minutes idle and takes ~1 minute to wake, so the first scan after a pause is slow.
- **Always-on small production:** roughly $7–13/mo (~₹600–1,100) for a Render Starter backend + a paid
  database tier once you outgrow 0.5 GB.

---

## 2. Deploy the database (Neon) — do this first

1. Sign up at neon.tech, create a project (pick the region closest to your users — Singapore or Mumbai
   for India).
2. Copy the connection string. It looks like:
   `postgresql://user:password@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`
3. Keep it handy — this is your `DATABASE_URL` for the backend.

---

## 3. Deploy the backend (Render)

1. Push this repo to GitHub.
2. On Render: **New → Web Service**, connect the repo, set **Root Directory** to `backend`.
3. Render auto-detects the Dockerfile. If you'd rather skip Docker, set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `alembic upgrade head && python -m app.seed_data && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables (Render dashboard → Environment):

   ```
   DATABASE_URL      = <your Neon connection string>
   JWT_SECRET_KEY    = <run: openssl rand -hex 32>
   ESP32_SHARED_SECRET = <run: openssl rand -hex 32>
   CORS_ORIGINS      = https://your-frontend.vercel.app
   ```

   Do **not** reuse the values from `.env.example` — those are placeholders and are public in your repo.
5. Deploy. Once live, confirm `https://your-backend.onrender.com/health` returns `{"status":"ok"}` and
   that `https://your-backend.onrender.com/docs` shows the interactive API documentation.

The start command runs migrations and seeds the 18 materials + CO2 factors automatically on first boot.
The seed script is idempotent (it skips rows that already exist), so redeploys are safe.

---

## 4. Deploy the frontend (Vercel)

1. On Vercel: **Add New → Project**, import the same GitHub repo.
2. Set **Root Directory** to `frontend`. Framework preset auto-detects as Next.js.
3. Add environment variables:

   ```
   NEXT_PUBLIC_API_BASE_URL = https://your-backend.onrender.com/api/v1
   NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = <optional, for the map view>
   ```
4. Deploy.
5. **Go back to Render** and update `CORS_ORIGINS` to your real Vercel URL, then redeploy the backend.
   Skipping this is the single most common cause of "the site loads but nothing works" — the browser
   silently blocks the API calls.

---

## 5. The ESP32 problem you need to know about

**This changes once you host in the cloud.** The current firmware design has the backend *push* commands
to the bin's local IP address (e.g. `192.168.1.50`). That works when the backend runs on your laptop on
the same Wi-Fi. It will **not** work once the backend is on Render, because your bin sits behind a home
or campus router (NAT) and has no public address — the cloud simply cannot reach into your local network.

Three ways to solve it, easiest first:

**Option A — Bin polls the backend (implemented, recommended).**
The bin asks "any commands for me?" every couple of seconds instead of waiting to be told. Outbound
requests pass through NAT fine, so no router configuration is needed. The backend endpoint for this is
`GET /api/v1/esp32/{device_uid}/pending-command` — already added. The firmware change needed is described
in `esp32-firmware/README.md` under "Cloud polling mode".

**Option B — MQTT broker.** Run an MQTT broker (HiveMQ Cloud has a free tier); the bin subscribes to its
own topic and the backend publishes to it. This is the properly scalable answer for many bins, with lower
latency than polling, but it's another moving part to operate.

**Option C — Phone as gateway over BLE.** The app talks to the cloud, then relays the command to the bin
over Bluetooth. Already spec'd in `esp32-firmware/ble_fallback.md`. Best for rural sites with no Wi-Fi
at all.

For a single bin demo, use Option A. It needs no extra infrastructure.

---

## 6. Before you call it production

- [ ] **Rotate every secret.** `JWT_SECRET_KEY` and `ESP32_SHARED_SECRET` must be long random values set
      only in the host's environment panel — never committed.
- [ ] **Confirm `.env` is gitignored** (it is, in this repo) and that no real credentials ever got committed.
      If one did, rotate it — deleting the commit is not enough.
- [ ] **Verify the CO2 factors.** The seeded numbers are compiled from published EPA/CPCB tables and are
      reasonable for a demo, but check them against your own sources before publishing environmental
      claims to real users. They're admin-editable by design for exactly this reason.
- [ ] **Replace the baseline classifier.** The shipped heuristic classifier is honest scaffolding, not an
      accurate model. Real users will notice. Train and swap in a proper model (ARCHITECTURE.md §6)
      before anyone relies on the output.
- [ ] **Set up backups.** Neon has point-in-time restore on paid tiers; on free, export periodically
      with `pg_dump`.
- [ ] **Add error monitoring.** Sentry has a free tier and takes about ten minutes to wire into both apps.
- [ ] **Restrict your Google Maps API key** to your Vercel domain in Google Cloud Console, otherwise
      someone else can run up your bill with your key.

---

## 7. Alternative: one-box deploy

If you'd rather run everything on a single server (a ₹400–800/mo VPS from DigitalOcean, Hetzner, or an
Indian provider), the included `docker-compose.yml` already wires up all three services. On the VPS:

```bash
git clone <your-repo> && cd smart-waste-platform
cp backend/.env.example backend/.env      # then edit with real secrets
cp frontend/.env.example frontend/.env.local
docker compose up -d --build
```

Then put Caddy or nginx in front for HTTPS. This is more setup and more maintenance than the managed
option, but it's predictable in cost, keeps everything in one place, and sidesteps the NAT problem
entirely if the server lives on the same network as your bins.
