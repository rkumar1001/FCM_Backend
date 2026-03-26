import logging
import hmac

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import SECRET_KEY, PORT
from app.models import LegacySendOrderRequest
from app.firebase_config import init_firebase, send_push_notification
from app.database import init_db
from app.routes.retell import router as retell_router

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in .env — refusing to start.")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FCM Order Notification Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(retell_router)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup() -> None:
    logger.info("Initializing Firebase Admin SDK …")
    init_firebase()
    logger.info("Initializing SQLite database …")
    init_db()
    logger.info("Service ready on port %s.", PORT)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/send-order")
async def send_order(payload: LegacySendOrderRequest, request: Request):
    logger.info(
        "Incoming /send-order request from %s (deviceToken=%s…)",
        request.client.host if request.client else "unknown",
        payload.deviceToken[:12] if len(payload.deviceToken) > 12 else "***",
    )

    # --- Auth ---------------------------------------------------------------
    if not hmac.compare_digest(payload.secret, SECRET_KEY):
        logger.warning("Unauthorized request — invalid secret.")
        raise HTTPException(status_code=401, detail="Unauthorized")

    # --- Validate -----------------------------------------------------------
    if not payload.deviceToken or not payload.deviceToken.strip():
        raise HTTPException(status_code=400, detail="deviceToken is required")

    # --- Send FCM -----------------------------------------------------------
    try:
        message_id = send_push_notification(
            device_token=payload.deviceToken,
            order_data=payload.orderData,
        )
        return {"success": True, "messageId": message_id}

    except Exception as exc:
        logger.exception("FCM send failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(exc)},
        )
