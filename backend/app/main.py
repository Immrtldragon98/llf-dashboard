from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import CORS_ORIGINS
from app.db.init import init_db
from app.api import auth, equipment, records, reports, admin

init_db()

app=FastAPI(title="LLF Dashboard API",version="0.7.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(equipment.router)
app.include_router(records.router)
app.include_router(reports.router)
app.include_router(admin.router)

@app.get("/api/health")
def health():
    return {"status":"ok","architecture":"modular"}
