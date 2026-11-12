# Oracle Cloud Always Free — TradePilot API setup

Forever-free backend host for FastAPI + worker + Postgres. Frontend stays on Vercel.

**Always Free shapes to use**
- Preferred: `VM.Standard.A1.Flex` (Ampere ARM) — e.g. **2 OCPU / 12 GB** (within free quota)
- Fallback: `VM.Standard.E2.1.Micro` (x86) — 1/8 OCPU, 1 GB (tight for Postgres)

Do **not** pick paid shapes. Stay in **Home Region** Always Free.

---

## 1) Create the free account

1. Open [https://www.oracle.com/cloud/free/](https://www.oracle.com/cloud/free/)
2. Sign up (card may be required for identity; Always Free is not a trial if you stay on free shapes)
3. Pick a home region close to India (e.g. Mumbai / Hyderabad if offered)
4. Wait until the tenancy is fully provisioned

---

## 2) Networking (one-time)

In **OCI Console → Networking → Virtual Cloud Networks**:

1. **Start VCN Wizard** → **Create VCN with Internet Connectivity**
2. Name: `tradepilot-vcn`
3. Note the **public subnet**

**Security List** (or NSG) ingress for the public subnet:

| Source | Protocol | Ports | Why |
|--------|----------|-------|-----|
| `0.0.0.0/0` | TCP | 22 | SSH (optionally lock to your IP later) |
| `0.0.0.0/0` | TCP | 80 | HTTP → HTTPS redirect |
| `0.0.0.0/0` | TCP | 443 | Public API HTTPS |

Do **not** expose Postgres `5432` publicly.

---

## 3) Create the Always Free VM

**Compute → Instances → Create Instance**

- Name: `tradepilot-api`
- Image: **Ubuntu 22.04** (or Oracle Linux 8)
- Shape: **Ampere** `VM.Standard.A1.Flex` — 2 OCPU, 12 GB RAM (Always Free Eligible)
- Networking: public subnet, **assign public IPv4**
- SSH keys: paste your public key (`~/.ssh/id_rsa.pub` / `id_ed25519.pub`)
- Boot volume: default is fine

Create → copy the **Public IP**.

```bash
ssh -i YOUR_KEY ubuntu@PUBLIC_IP
# Oracle Linux images often use: opc@PUBLIC_IP
```

---

## 4) Install Docker on the VM

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
docker version
```

Or run the repo script after cloning: `bash scripts/oracle_bootstrap.sh`

---

## 5) Put the code on the VM

**Option A — git clone** (if the repo is on GitHub):

```bash
cd ~
git clone YOUR_REPO_URL tradepilot
cd tradepilot
```

**Option B — upload from your PC** (PowerShell):

```powershell
scp -i YOUR_KEY -r "C:\Users\shyam\Downloads\trading bots\*" ubuntu@PUBLIC_IP:~/tradepilot/
```

---

## 6) Configure secrets

```bash
cd ~/tradepilot
cp .env.example .env
nano .env
```

Set at least:

```env
TRADEPILOT_ENV=production
POSTGRES_PASSWORD=use-a-long-random-password
TRADEPILOT_CORS_ORIGINS=https://tradepilot-ai-demo.vercel.app
TELEGRAM_BOT_TOKEN=
MARKET_DATA_PROVIDER=unconfigured
MARKET_DATA_MODE=delayed
API_PORT=8000
```

`DATABASE_URL` is built inside `docker-compose.prod.yaml` — you do not need to hand-edit it for Compose.

---

## 7) Apply migrations + start stack

```bash
cd ~/tradepilot
docker compose -f docker-compose.prod.yaml up -d --build

# Wait for healthy, then apply SQL migrations
docker compose -f docker-compose.prod.yaml exec -T postgres \
  psql -U tradepilot -d tradepilot < migrations/0001_init.sql
docker compose -f docker-compose.prod.yaml exec -T postgres \
  psql -U tradepilot -d tradepilot < migrations/0002_app_runtime.sql

curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ready
```

Useful commands:

```bash
docker compose -f docker-compose.prod.yaml ps
docker compose -f docker-compose.prod.yaml logs -f api
docker compose -f docker-compose.prod.yaml logs -f worker
```

---

## 8) HTTPS with Caddy (free Let’s Encrypt)

Point a domain (or free subdomain) **A record** → VM public IP, e.g. `api.yourdomain.com`.

```bash
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update
sudo apt-get install -y caddy
```

`/etc/caddy/Caddyfile`:

```caddy
api.yourdomain.com {
    reverse_proxy 127.0.0.1:8000
}
```

```bash
sudo systemctl reload caddy
curl -fsS https://api.yourdomain.com/ready
```

**No domain yet?** Temporary (HTTP only, not ideal for cookies):

```bash
curl -fsS http://PUBLIC_IP:8000/ready
```

Open OCI security list TCP **8000** only while testing, then prefer HTTPS on 443.

---

## 9) Connect the Vercel frontend

In Vercel project → Settings → Environment Variables (Production):

```text
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

Redeploy the web app. Confirm API `.env` has:

```env
TRADEPILOT_CORS_ORIGINS=https://tradepilot-ai-demo.vercel.app
```

(Include every Vercel production origin you use, comma-separated, no trailing slash.)

---

## 10) Backup (free, on-box)

From your PC (PowerShell), after SSH config works:

```powershell
ssh ubuntu@PUBLIC_IP "cd ~/tradepilot && docker compose -f docker-compose.prod.yaml exec -T postgres pg_dump -U tradepilot tradepilot" > tradepilot-backup.sql
```

Restore drill: see `scripts/backup_restore.sh` / `docs/runbooks.md`.

---

## Capacity notes (Always Free)

| Resource | Guidance |
|----------|----------|
| API + worker + Postgres | Fits comfortably on A1.Flex 2 OCPU / 12 GB |
| E2.1.Micro (1 GB) | Prefer SQLite (`TRADEPILOT_DB_PATH`) instead of Postgres |
| Cold starts | None — VM stays on |
| Cost | ₹0 if shapes stay Always Free Eligible |

---

## Checklist before beta testers

- [ ] `/ready` returns OK over **HTTPS**
- [ ] Vercel `NEXT_PUBLIC_API_URL` set + redeployed
- [ ] CORS origin matches Vercel URL
- [ ] Postgres volume persists across `compose down` / `up`
- [ ] Backup dump file created once
- [ ] Telegram token only if you want alerts live
- [ ] Still: licensed NSE data + legal review are separate (not hosting)
