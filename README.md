# LLF Dashboard V0.8 — Free Deployment Ready

Scalable LLF prototype for Continuous Properzi 15 Tbh.

## Stack
- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL
- Local environment: Docker Compose
- Free cloud prototype: Render + Supabase

## V0.8 changes
- Fixed `passlib` / `bcrypt` compatibility by pinning `bcrypt==4.0.1`.
- Backend now respects cloud `PORT`.
- Frontend API base URL comes from `VITE_API_URL`.
- CORS comes from `CORS_ORIGINS`.
- Added `.env.example` files.
- Added Render Blueprint (`render.yaml`).
- Added backend health check.
- Added free deployment guide.
- Kept V0.7 modular backend architecture and normalized database design.

## Local run

```powershell
docker compose up --build
```

Frontend:
http://localhost:5173

Backend docs:
http://localhost:8000/docs

## Free deployment

Read:
`DEPLOY_FREE.md`

Recommended prototype deployment:
- Render Static Site — frontend
- Render Free Web Service — FastAPI
- Supabase Free — PostgreSQL

## Important

The included accounts are development accounts only:
- admin / admin123
- operator / operator123
- viewer / viewer123

Do not use these credentials for real plant data.
