# Getting Your App Online — The Simple Version

No experience assumed. Follow these in order. Budget about 1–2 hours the first time.

---

## First, understand what you're doing

Your app is three separate pieces, and each needs its own home on the internet:

1. **The database** — the filing cabinet. Stores users, scans, materials.
2. **The backend** — the brain. Does the AI classification and the maths.
3. **The frontend** — the face. The website people actually look at.

You'll put each one on a different free service, then tell them how to find each other.
That last part — introducing them to each other — is where most people get stuck, so I've called it
out clearly at each step.

**Order matters.** Database first (the backend needs its address), then backend, then frontend.

---

## Step 0: Put your code on GitHub

Everything else reads your code *from* GitHub, so this has to happen first.

1. Make a free account at **github.com** if you don't have one.
2. Download and install **GitHub Desktop** (desktop.github.com). It's the version with buttons instead
   of typed commands — much easier to start with.
3. Unzip the project folder I gave you somewhere sensible, like your Documents folder.
4. Open GitHub Desktop → **File → Add Local Repository** → choose your `smart-waste-platform` folder.
   - If it says it's not a repository, click the **"create a repository"** link it offers.
5. Give it a name, and choose **Private** (your project, your call — but private is the safer default).
6. Click **Publish repository**.

✅ **Check it worked:** go to github.com, and your project files should be sitting there.

> ⚠️ Before publishing, make sure there's no file called exactly `.env` in the `backend` folder — only
> `.env.example`. The `.env` file holds passwords and must never go on GitHub. (I've already set the
> project up to ignore it, so you should be fine — just worth a glance.)

---

## Step 1: The database (Neon)

This is your filing cabinet. Free, and it doesn't expire.

1. Go to **neon.tech** → sign up (you can use your GitHub account).
2. Create a new project. Name it anything. For **region**, pick **Singapore** or **Mumbai** — closest to
   India means faster for your users.
3. When it finishes, it shows you a **connection string**. It looks like this:

   ```
   postgresql://neondb_owner:AbC123xyz@ep-cool-name-123.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```

4. **Copy it and paste it somewhere safe** (a notes file). You need it in the next step.

✅ **Check it worked:** you have that long `postgresql://...` line saved.

> This string is a password. Don't put it in a screenshot, a WhatsApp message, or your code.

---

## Step 2: The backend (Render)

This is the brain.

1. Go to **render.com** → sign up with GitHub.
2. Click **New** → **Web Service**.
3. Connect your GitHub and pick your `smart-waste-platform` repository.
4. Fill in the settings:
   - **Name:** anything, e.g. `smartwaste-backend`
   - **Root Directory:** type `backend` ← **easy to miss, and nothing works without it**
   - **Runtime/Language:** it should detect **Docker** automatically. Let it.
   - **Instance Type:** **Free**
5. Find the **Environment Variables** section and add these four:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | the long `postgresql://...` string from Step 1 |
   | `JWT_SECRET_KEY` | a long random jumble of letters and numbers (see below) |
   | `ESP32_SHARED_SECRET` | a *different* long random jumble |
   | `CORS_ORIGINS` | leave as `http://localhost:3000` for now — you'll fix this in Step 4 |

   **For the random jumbles:** search "random password generator", set the length to 40+, and generate
   two different ones. These are what stop strangers logging in as your users, so don't use `password123`
   and don't reuse the same one for both.

6. Click **Create Web Service** and wait. First build takes 5–10 minutes. Watching the log scroll is normal.

✅ **Check it worked:** Render gives you a web address like `https://smartwaste-backend.onrender.com`.
Open it with `/health` on the end:

```
https://smartwaste-backend.onrender.com/health
```

You should see `{"status":"ok"}`. **Copy your backend address into your notes file.**

Now try `/docs` on the end instead — you'll get a full interactive list of everything your app can do.
That page is genuinely useful later for testing.

**If it fails:** click the **Logs** tab and read the last red lines. 90% of the time it's either the Root
Directory not set to `backend`, or a typo in the `DATABASE_URL`.

---

## Step 3: The frontend (Vercel)

This is the face — the actual website.

1. Go to **vercel.com** → sign up with GitHub.
2. Click **Add New** → **Project** → import the same repository.
3. Settings:
   - **Root Directory:** click Edit and choose `frontend` ← **again, easy to miss**
   - Framework should auto-detect as **Next.js**. Leave it.
4. Open **Environment Variables** and add one:

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_BASE_URL` | your Render address + `/api/v1` |

   So it looks like: `https://smartwaste-backend.onrender.com/api/v1`

   (Note the `/api/v1` on the end. It matters.)

5. Click **Deploy** and wait 2–3 minutes.

✅ **Check it worked:** Vercel gives you an address like `https://smart-waste-platform.vercel.app`.
Open it — you should see your landing page. **Save this address in your notes too.**

---

## Step 4: Introduce them to each other ⚠️ DON'T SKIP

Right now your website loads but **nothing will work** — you can't log in, scans will fail. That's
expected. Your backend doesn't yet trust your website, so browsers are blocking them from talking.

Fix it:

1. Go back to **Render** → your backend → **Environment**.
2. Find `CORS_ORIGINS` and change it to your Vercel address, exactly as Vercel shows it:

   ```
   https://smart-waste-platform.vercel.app
   ```

   No slash on the end. No `/api/v1`. Just the plain address.
3. Save. Render redeploys automatically — wait for it to finish.

✅ **Check it worked:** open your Vercel site, create an account, and log in. If you land on the
dashboard, all three pieces are talking. **Your app is live.**

---

## Step 5: Try a real scan

Open your site on your **phone** (that's what it's designed for), log in, go to Scan, and photograph
something.

You'll get back a material, a weight, CO₂ saved, and an earnings estimate.

**Be aware:** the answer will often be wrong. The AI in there right now is a placeholder that guesses
from colour and texture — it's real working plumbing, not a real trained model. Everything around it
(the maths, the money, the CO₂, the database) is correct; only the identification step is a stand-in.
Replacing it is the biggest remaining job, and it needs a labelled dataset of waste photos.

Please don't demo it as finished AI — if someone tests it with three objects, they'll notice.

---

## Step 6: Your smart bin

Your ESP32 bin needs one change before it'll work with the hosted version.

The reason: right now the backend tries to contact your bin directly. That worked when everything ran
on your laptop on the same Wi-Fi. Now the backend lives on the internet and your bin sits behind your
router — the internet can't reach into your home network to find it. So instead, the **bin has to ask
the backend** "anything for me?" every couple of seconds. Asking outward works fine.

The code to paste into your firmware is in `esp32-firmware/README.md` under **"Cloud polling mode"**.
You'll also need to change `BACKEND_HOST` in the firmware to your Render address, and set
`SHARED_SECRET` to the exact same value you put in `ESP32_SHARED_SECRET` on Render.

**Strong suggestion:** get the bin working on your laptop first (using Docker, see `README.md`) before
trying it against the hosted version. If you do both at once and it fails, you won't know whether the
problem is the wiring, the firmware, or the hosting.

---

## Things that will confuse you (they confuse everyone)

**"The first visit takes a minute to load."**
Normal on Render's free plan. It puts your backend to sleep after 15 minutes of no traffic, and waking
it up is slow. Pay $7/month for the Starter plan and it stays awake. Worth doing before a demo — set it
up the day before, not five minutes before.

**"I changed the code but the site looks the same."**
Push your changes to GitHub (GitHub Desktop → Commit → Push). Render and Vercel redeploy automatically
when GitHub changes, not when your laptop changes.

**"Login says something about CORS / network error."**
Step 4. The address in `CORS_ORIGINS` must match your site exactly — check for a stray `/` on the end.

**"Everything broke and I don't know why."**
Read the **Logs** tab (Render) or **Deployments → the failed one** (Vercel). The actual error is in there
in plain English near the bottom. Paste it to me and I'll tell you what it means.

---

## One legal note

Vercel's free plan is for **personal, non-commercial** projects only. A college project or portfolio
piece is completely fine. If this ever starts making money or gets adopted by an organisation, you need
their paid plan ($20/month) — otherwise you're breaking their terms and they can take your site down.

---

## What this costs

- **Right now, as a demo:** ₹0. All three services free.
- **If you want it always-on and fast:** about $7/month (~₹600) for Render's Starter plan. That's the
  single upgrade that makes the most difference.
