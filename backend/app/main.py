from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings
from app.api.v1 import auth, users, scans, materials, recycling_centers, leaderboard, market_prices, esp32, admin

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Smart Waste Management & Recycling Platform API",
    description="AI waste classification, CO2/earnings estimation, recycling centers, leaderboard, ESP32 bins.",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(scans.router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(materials.router, prefix="/api/v1/materials", tags=["materials"])
app.include_router(recycling_centers.router, prefix="/api/v1/recycling-centers", tags=["recycling-centers"])
app.include_router(leaderboard.router, prefix="/api/v1/leaderboard", tags=["leaderboard"])
app.include_router(market_prices.router, prefix="/api/v1/market-prices", tags=["market-prices"])
app.include_router(esp32.router, prefix="/api/v1/esp32", tags=["esp32"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
