import sentry_sdk
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import connect, disconnect
from core.errors import register_error_handlers
from core.logging import logger, setup_logging
from core.middleware import RequestLoggingMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration


from core.rate_limit import (
    limiter,
    rate_limit_exceeded_handler,
    SlowAPIMiddleware,
    RateLimitExceeded,
)


# ---------------------------------------------------------------------------
# Lifespan — runs on startup and shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting up Aap ki Rasoi API")
    await connect()
    logger.info("Database pool connected")
    yield
    # Shutdown
    await disconnect()
    logger.info("Shutting down Aap ki Rasoi API")

# Must init before FastAPI app — FastApiIntegration patches request handling at import time
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.2,
    release=settings.git_commit_sha,
    environment=settings.environment,
)



# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Aap ki Rasoi API",
    version="1.0.0",
    lifespan=lifespan,
)


# Rate limiter state attached to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware)


# ---------------------------------------------------------------------------
# CORS — origins loaded from environment variable, never wildcard
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
register_error_handlers(app)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from routers import (  # noqa: E402 — routers must come after app is created
    health,
    menu,
    delivery,
    orders,
    reservations,
    catering,
    internal,
)

app.include_router(health.router)
app.include_router(menu.router)
app.include_router(delivery.router)
app.include_router(orders.router)
app.include_router(reservations.router)
app.include_router(catering.router)
app.include_router(internal.router)


# ---------------------------------------------------------------------------
# Root — quick sanity check
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Aap ki Rasoi API is running"}
