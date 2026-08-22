# Free deployment: Render + Supabase

This setup keeps local development in Docker but deploys the public prototype as:

Browser
  -> Render Static Site (React)
  -> Render Free Web Service (FastAPI)
  -> Supabase Free Postgres

## 1. Put the project on GitHub

Create a GitHub repository and push this project.

Do not commit real secrets.

## 2. Create Supabase database

Create a free Supabase project.

In Supabase, copy a PostgreSQL connection string from the database connection settings.

For this FastAPI app, set Render's `DATABASE_URL` using SQLAlchemy's psycopg prefix:

postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE

If Supabase gives you a URL beginning with `postgresql://`, change only the scheme to:

postgresql+psycopg://

Keep the rest of the connection values unchanged.

## 3. Deploy backend on Render

Option A: use the included `render.yaml` Blueprint.

Option B: create a Web Service manually.

Settings:
- Root Directory: backend
- Runtime: Docker
- Instance: Free
- Health Check Path: /api/health

Environment variables:
- DATABASE_URL = Supabase connection string
- JWT_SECRET = a long random secret
- CORS_ORIGINS = temporary frontend URL after frontend is deployed
- ACCESS_TOKEN_HOURS = 8

Deploy it.

After deployment, note your backend URL, for example:

https://llf-api.onrender.com

Test:

https://llf-api.onrender.com/api/health

It should return JSON with status `ok`.

## 4. Deploy frontend on Render

Create a Static Site.

Settings:
- Root Directory: frontend
- Build Command: npm install && npm run build
- Publish Directory: dist

Environment variable:
- VITE_API_URL = your backend base URL, WITHOUT `/api`

Example:

VITE_API_URL=https://llf-api.onrender.com

Deploy.

Note your frontend URL, for example:

https://llf-dashboard.onrender.com

## 5. Fix backend CORS

Back in the backend Render service, set:

CORS_ORIGINS=https://llf-dashboard.onrender.com

Redeploy the backend.

## 6. Login

Prototype accounts are still:
- admin / admin123
- operator / operator123
- viewer / viewer123

Change them before real plant use.

## 7. Free-tier behavior

Render Free Web Service:
- sleeps after idle time
- may take roughly a minute to wake
- suitable for prototype/testing, not guaranteed production availability

Supabase Free:
- database is persistent within the free project
- free projects may pause after extended inactivity
- no automatic backups on Free

## 8. Local development

From project root:

docker compose up --build

Open:
- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs

You do NOT need to run `npm install` from the project root.
The frontend npm project is under `frontend/`.
