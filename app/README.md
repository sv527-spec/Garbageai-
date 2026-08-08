# Habit Board

A habit + class-attendance tracker that installs like a real app and stores
all data on your device (no server, no account).

## What's inside
- `index.html`, `style.css`, `app.js` — the app
- `manifest.json`, `service-worker.js` — makes it installable and offline-capable
- `icons/` — app icons

## Step 1 — Put it online (needed once, for installing + APK)
Phones only let you "install" or turn a site into an APK if it's served over
`https://`, not opened as a local file. Pick whichever is easiest:

**Netlify Drop (fastest, no account needed)**
1. Go to https://app.netlify.com/drop
2. Drag the whole unzipped folder onto the page
3. You'll get a live URL like `https://random-name.netlify.app`

**GitHub Pages**
1. Create a new GitHub repo, upload these files
2. Repo Settings → Pages → deploy from the main branch
3. Your URL will be `https://yourusername.github.io/reponame`

**Vercel**
1. https://vercel.com/new → drag and drop the folder → Deploy

## Step 2 — Install it on your phone (PWA — works today)
1. Open your live URL in Chrome (Android) or Safari (iPhone)
2. Android Chrome: menu (⋮) → **Add to Home screen** / **Install app**
3. iPhone Safari: Share icon → **Add to Home Screen**
4. It now opens full-screen with its own icon, and works offline. Your data
   is saved in the browser's local storage on that device.

## Step 3 (optional) — Turn it into a real, installable APK
1. Go to https://www.pwabuilder.com/
2. Paste your live URL (from Step 1) and click **Start**
3. Once it scans your manifest, go to the **Android** package option
4. Click **Generate** — it builds a signed APK/AAB for you to download
5. Transfer the `.apk` to your phone and open it to install (you may need to
   allow "install unknown apps" for your file manager/browser in Android
   settings — this is normal for anything not from the Play Store)

This gives you a real `.apk` file without needing Android Studio.

## Notes on data & reminders
- All habits, check-ins, classes, and attendance are stored in the browser's
  local storage on that specific device/browser. Nothing is synced to a
  server, so use **Settings → Export backup** occasionally, especially
  before clearing browser data or switching phones. **Import backup**
  restores it.
- Reminders (bell icon on a habit) use two modes:
  - **Notification** — a real browser/OS notification. Needs permission
    (Settings → Allow) and, on Android, the PWA installed; it fires even if
    the app isn't in the foreground once installed, but the phone must be on
    and the app not force-closed.
  - **Alarm** — plays a sound and shows a full-screen alert while the app is
    open. It won't ring if the app is fully closed — true background alarms
    need a native app with special OS permissions, which a web app can't get.
- Theme defaults to matte black; switch to light in Settings → Appearance.
