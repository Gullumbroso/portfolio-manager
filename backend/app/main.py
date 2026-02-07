from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import portfolios, transactions, holdings, market_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(title="Portfolio Manager", version="1.0.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolios.router, prefix="/api/portfolios", tags=["portfolios"])
app.include_router(transactions.router, prefix="/api/portfolios", tags=["transactions"])
app.include_router(holdings.router, prefix="/api/portfolios", tags=["holdings"])
app.include_router(market_data.router, prefix="/api/market", tags=["market"])


@app.get("/api/health")
def health_check():
    s = get_settings()
    return {
        "status": "ok",
        "supabase_url_set": bool(s.supabase_url),
        "supabase_key_set": bool(s.supabase_key),
        "finnhub_key_set": bool(s.finnhub_api_key),
    }
