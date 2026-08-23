# Deploy Veritas to Vercel + Render + Supabase

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Backend       │     │   Database      │
│   (Vercel)      │────▶│   (Render)      │────▶│   (Supabase)    │
│   React + Vite  │     │   FastAPI       │     │   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Quick Start (5 minutes)

### 1. Supabase (Database)

Your project: **`jddyiqdllaytbhopjmch`**

1. Go to [supabase.com](https://supabase.com) → your project
2. **Settings → Database → Connection string → URI**
4. Copy: `postgresql://postgres:[DB_PASSWORD]@db.jddyiqdllaytbhopjmch.supabase.co:5432/postgres`
5. **Settings → API** and copy:
   - **Project URL**: `https://jddyiqdllaytbhopjmch.supabase.co`
   - **service_role key** (secret): `sb_secret_...`
6. Run migrations in SQL Editor (see `SUPABASE_SETUP.md`)

### 2. Render (Backend)

1. Fork this repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render will detect `render.yaml` and create web service
5. Add environment variables in Render Dashboard:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql://postgres.jddyiqdllaytbhopjmch:[DB_PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres` |
| `SUPABASE_URL` | `https://jddyiqdllaytbhopjmch.supabase.co` |
| `SUPABASE_SERVICE_KEY` | `sb_secret_...` (from Supabase API settings) |
| `JWT_SECRET_KEY` | Auto-generated (or `openssl rand -base64 32`) |
| `CORS_ORIGINS` | `https://your-app.vercel.app` |
| `LOG_LEVEL` | `INFO` |

6. Wait for deploy, note the URL: `https://veritas-backend.onrender.com`

### 3. Vercel (Frontend)

1. Go to [vercel.com](https://vercel.com) → Add New → Project
2. Import your GitHub repo
3. Configure:
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Add Environment Variable:
   - `VITE_API_BASE` = `https://veritas-backend.onrender.com`
5. Deploy!

## GitHub Actions (Automatic CI/CD)

The `.github/workflows/ci-cd.yml` handles:

- ✅ Backend tests (with PostgreSQL)
- ✅ Frontend lint + build
- ✅ Docker image builds (GHCR)
- ✅ Auto-deploy to Render on merge to main
- ✅ Auto-deploy to Vercel on merge to main

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `VERCEL_TOKEN` | From Vercel Account Settings → Tokens |
| `VERCEL_ORG_ID` | From Vercel Project Settings |
| `VERCEL_PROJECT_ID` | From Vercel Project Settings |
| `RENDER_API_KEY` | From Render Account Settings → API Keys |
| `RENDER_BACKEND_SERVICE_ID` | From Render Service Settings → ID |
| `VITE_API_BASE` | Your Render backend URL |

## Environment Variables Reference

### Backend (Render)

```env
# Required
DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=sb_secret_xxx  # Service role key (secret!)
JWT_SECRET_KEY=xxx  # 32+ bytes base64
CORS_ORIGINS=https://your-app.vercel.app

# Optional
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
LOG_LEVEL=INFO
NVIDIA_API_KEY=xxx
OPENAI_API_KEY=xxx
SEARCH_API_KEY=xxx
```

### Frontend (Vercel)

```env
VITE_API_BASE=https://your-backend.onrender.com
```

## Post-Deployment Checklist

- [ ] Backend health check: `https://your-backend.onrender.com/api/health`
- [ ] Frontend loads: `https://your-app.vercel.app`
- [ ] Login/register works
- [ ] Demo pipeline runs: Click "Run demo pipeline" in UI
- [ ] File upload works (PDF, CSV, images)
- [ ] CORS configured correctly (no console errors)
- [ ] Database migrations applied
- [ ] SSL/TLS working on both domains

## Troubleshooting

### CORS Errors
- Verify `CORS_ORIGINS` in Render includes your Vercel URL exactly
- Check no trailing slashes: `https://app.vercel.app` not `https://app.vercel.app/`

### Database Connection Failed
- Verify Supabase connection string format
- Check Supabase allows connections from Render IPs (Settings → Database → Connection pooling)
- Try pooled connection string (port 6543) for serverless

### Build Failures
- Check Node.js version (20+) in Vercel settings
- Check Python version (3.11+) in Render settings
- Verify all dependencies in `requirements.txt` and `package.json`

### Slow First Request (Render Free Tier)
- Render spins down after 15 min inactivity
- First request takes ~30s to spin up
- Upgrade to Starter plan for always-on

## Cost Estimate (Monthly)

| Service | Tier | Cost |
|---------|------|------|
| Vercel | Hobby | Free |
| Render | Starter | $7/mo |
| Supabase | Pro | $25/mo |
| **Total** | | **~$32/mo** |

Free tiers available for all (with limitations).

## Custom Domains

### Vercel
1. Project Settings → Domains → Add
2. Configure DNS records as instructed

### Render
1. Service Settings → Custom Domains → Add
2. Configure DNS records as instructed

## Scaling

| Component | Scaling |
|-----------|---------|
| Frontend | Vercel Edge (automatic) |
| Backend | Render: increase plan, add instances |
| Database | Supabase: upgrade plan, enable read replicas |

## Security

- [ ] Rotate `JWT_SECRET_KEY` quarterly
- [ ] Enable Supabase RLS policies
- [ ] Set up Supabase Auth (if needed)
- [ ] Configure Render WAF (paid plans)
- [ ] Enable Vercel Firewall rules