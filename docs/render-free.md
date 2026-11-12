# Render free setup (TradePilot API)

Forever-free path: **Render Free web service** + **Neon Free Postgres** + **Vercel** frontend.

| Piece | Host | Cost |
|-------|------|------|
| API + Telegram worker | Render Free web service | $0 (sleeps after ~15 min idle) |
| Postgres | Neon Free | $0 (permanent free plan; not Render’s 30-day DB) |
| Web UI | Vercel | $0 (already live) |

Do **not** create Render Free Postgres — it expires in 30 days.

---

## 0) Push this repo to GitHub

Render deploys from Git. From your PC (PowerShell), in the project folder:

```powershell
cd "C:\Users\shyam\Downloads\trading bots"
git init
git add .
git commit -m "TradePilot API ready for Render free deploy"
# Create an empty private repo on GitHub named tradepilot, then:
gh repo create tradepilot --private --source=. --remote=origin --push
```

Or create the repo in the GitHub UI and:

```powershell
git remote add origin https://github.com/YOUR_USER/tradepilot.git
git branch -M main
git push -u origin main
```

---

## 1) Neon Free Postgres (CLI — preferred)

From the repo (already linked to project `super-forest-37801309`):

```powershell
neon login
neon deploy
```

That writes gitignored `.env.local` (pooled `DATABASE_URL`, unpooled URL, Auth/Realtime/S3 keys).  
**Never paste those values into chat or commit them.**

For Render, copy **only** the pooled `DATABASE_URL` from `.env.local` into the Render dashboard env.

App schema for sessions/outbox is created automatically on API boot (`postgres_store`).

---

## 2) Deploy on Render

1. Open [https://dashboard.render.com](https://dashboard.render.com) → sign up (GitHub login)
2. **New → Blueprint**
3. Connect the `tradepilot` GitHub repo
4. Render reads `render.yaml` → one free web service `tradepilot-api`
5. When prompted for sync:false secrets, set:

| Key | Value |
|-----|--------|
| `DATABASE_URL` | Neon pooled URL — copy from local `.env.local` after `neon deploy` (do not paste into chat) |
| `TRADEPILOT_CORS_ORIGINS` | `https://tradepilot-ai-demo.vercel.app` |
| `TELEGRAM_BOT_TOKEN` | leave empty until you have a bot |
| `SENTRY_DSN` | leave empty |

6. Apply / create → wait for the first deploy (Docker build)
7. Open the service URL → check:

```text
https://YOUR-SERVICE.onrender.com/health
https://YOUR-SERVICE.onrender.com/ready
```

`/ready` must succeed (DB reachable). First hit after idle can take ~1 minute (cold start).

---

## 3) Manual deploy (if you skip Blueprint)

**New → Web Service** → connect repo → settings:

- Runtime: **Docker**
- Dockerfile path: `./Dockerfile`
- Docker command: `sh scripts/render_start.sh`
- Instance type: **Free**
- Health check path: `/ready`

Same env vars as the table above.

---

## 4) Connect Vercel frontend

Vercel project → Settings → Environment Variables → Production:

```text
NEXT_PUBLIC_API_URL=https://YOUR-SERVICE.onrender.com
```

Redeploy the web app. CORS must list that Vercel origin on the API (`TRADEPILOT_CORS_ORIGINS`).

---

## 5) What the free service runs

`scripts/render_start.sh` starts:

1. Telegram worker in the background  
2. Uvicorn API on Render’s `$PORT`

Paid Render Background Workers are not used, so cost stays $0.

---

## Limits to expect

- Sleep after ~15 minutes with no traffic; next request cold-starts (~1 min)
- 512 MB RAM on free web
- Neon free: storage/CU-hour caps; compute can scale to zero when idle
- Ephemeral disk — never store DB files on the Render instance; use Neon only

---

## After deploy checklist

- [ ] `GET /ready` returns OK
- [ ] Vercel `NEXT_PUBLIC_API_URL` set + redeployed
- [ ] Sign-up / login works from the live demo
- [ ] Optional: set `TELEGRAM_BOT_TOKEN` and redeploy for alerts
