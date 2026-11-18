import asyncio
from contextlib import asynccontextmanager, suppress

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from backend.ai import ai_mode  # noqa: E402  (after load_dotenv so AI_MODE is read from .env)
from backend.db import init_db  # noqa: E402
from backend.routers import inbox, intake, mock_erp, model, orders, rules, stock  # noqa: E402
from backend.services.orders.crm_worker import crm_sync_worker, worker_enabled  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables once upon application boot
    init_db()
    worker = asyncio.create_task(crm_sync_worker()) if worker_enabled() else None
    yield
    if worker:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker


app = FastAPI(title="OneOrder", version="0.1.0", lifespan=lifespan)
app.include_router(intake.router)
app.include_router(orders.router)
app.include_router(model.router)
app.include_router(stock.router)
app.include_router(mock_erp.router)
app.include_router(inbox.router)
app.include_router(rules.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "ai_mode": ai_mode()}
