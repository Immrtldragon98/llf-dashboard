import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://llf:llf_dev_password@db:5432/llf")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
ACCESS_TOKEN_HOURS = int(os.getenv("ACCESS_TOKEN_HOURS", "8"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
