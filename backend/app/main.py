"""ZQode Internal LLM Gateway Platform — FastAPI entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.bootstrap import run_bootstrap
from app.routers import admin, analytics, auth, gateway, workbench

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("zqode")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await run_bootstrap()
    except Exception:
        log.exception("bootstrap failed; continuing without admin")
    yield


app = FastAPI(
    title="ZQode LLM Gateway",
    description="Internal Enterprise LLM API Gateway Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _envelope(status_code: int, code: str, message: str, details: dict | None = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "message": message,
            "data": {"error_code": code, "details": details or {}},
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return _envelope(
            exc.status_code,
            exc.detail["code"],
            exc.detail.get("message", "Error"),
            exc.detail.get("details"),
        )
    return _envelope(exc.status_code, "HTTP_ERROR", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _envelope(422, "VALIDATION_ERROR", "Request validation failed.", {"errors": exc.errors()})


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(workbench.router)
app.include_router(gateway.router)
app.include_router(analytics.router)
