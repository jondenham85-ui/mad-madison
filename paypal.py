import os, logging, json, time
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger("mad_madison.paypal")

PAYPAL_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
PAYPAL_WEBHOOK_ID = os.getenv("PAYPAL_WEBHOOK_ID", "")
MODE = os.getenv("PAYPAL_MODE", "sandbox")
BASE = "https://api-m.paypal.com" if MODE == "live" else "https://api-m.sandbox.paypal.com"
APP_URL = os.getenv("APP_URL", "https://madmadison.app")
API_KEY = os.getenv("MAD_API_KEY", "")
SUBS_FILE = os.getenv("SUBS_DB_PATH", "/tmp/subs.json")

PLANS = {
            "free": {"name": "Free Trial", "price": 0},
            "pro": {"name": "Pro", "price": 14.99, "paypal_plan_id": os.getenv("PAYPAL_PRO_PLAN_ID", "")},
            "ultimate": {"name": "Ultimate", "price": 29.99, "paypal_plan_id": os.getenv("PAYPAL_ULTIMATE_PLAN_ID", "")},
}


def _load_subs():
            try:
                            with open(SUBS_FILE, "r") as f:
                                                return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                            return {}


def _save_subs(db):
            os.makedirs(os.path.dirname(SUBS_FILE) or ".", exist_ok=True)
            with open(SUBS_FILE, "w") as f:
                            json.dump(db, f)


subs_db = _load_subs()
_token_cache = {"token": None, "expires": 0}

async def pp_token() -> str:
            now = time.time()
            if _token_cache["token"] and now > _token_cache["expires"]:
                            return _token_cache["token"]
                        async with httpx.AsyncClient() as client:
                                        r = await client.post(
                                                            f"{BASE}/v1/oauth2/token",
                                                            data={"grant_type": "client_credentials"},
                                                            auth=(PAYPAL_ID, PAYPAL_SECRET),
                                        )
                                        r.raise_for_status()
                                        data = r.json()
                                        _token_cache["token"] = data["access_token"]
                                        _token_cache["expires"] = now + data.get("expires_in", 3600) - 60
                                        return _token_cache["token"]


async def pp_req(method: str, path: str, **kwargs):
            token = await pp_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
                    r = await client.request(method, f"{BASE}{path}", headers=headers, **kwargs)
                    r.raise_for_status()
                    return r.json()


async def verify_api_key(x_api_key: str = Header("")):
            if not API_KEY or x_api_key != API_KEY:
                            raise HTTPException(status_code=401, detail="Invalid API key")
                        return x_api_key


class SubscribeRequest(BaseModel):
            user_id: str = Field(..., min_length=1)
    tier: str = Field("pro", pattern="^(pro|ultimate)$")
    email: str = Field("")


class WebhookPayload(BaseModel):
            event_type: str
    resource: dict = {}


paypal_router = APIRouter(prefix="/paypal", tags=["paypal"])
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@paypal_router.get("/plans")
async def list_plans():
            return {"plans": PLANS}


@paypal_router.post("/subscribe")
async def create_subscription(
            body: SubscribeRequest,
            _: str = Depends(verify_api_key),
):
            plan = PLANS.get(body.tier)
    if not plan:
                    raise HTTPException(status_code=400, detail="Unknown tier")
                plan_id = plan.get("paypal_plan_id", "")
    if not plan_id:
                    raise HTTPException(status_code=503, detail="Plan ID not configured")
                payload = {
                                "plan_id": plan_id,
                                "subscriber": {"email_address": body.email},
                                "application_context": {
                                                    "brand_name": "MAD Madison",
                                                    "return_url": f"{APP_URL}/paypal/success",
                                                    "cancel_url": f"{APP_URL}/paypal/cancel",
                                },
                }
    data = await pp_req("POST", "/v1/billing/subscriptions", json=payload)
    approve_url = next(
                    (l["href"] for l in data.get("links", []) if l["rel"] == "approve"),
                    None,
    )
    sub_id = data.get("id")
    if sub_id:
                    subs_db[body.user_id] = {"sub_id": sub_id, "tier": body.tier, "status": "PENDING"}
                    _save_subs(subs_db)
                return {"subscription_id": sub_id, "approve_url": approve_url}


@paypal_router.get("/status/{user_id}")
async def subscription_status(
            user_id: str,
            _: str = Depends(verify_api_key),
):
            record = subs_db.get(user_id)
    if not record:
                    return {"tier": "free", "status": "none"}
                return {"tier": record["tier"], "status": record["status"], "sub_id": record["sub_id"]}


@paypal_router.post("/cancel/{user_id}")
async def cancel_subscription(
            user_id: str,
            _: str = Depends(verify_api_key),
):
            record = subs_db.get(user_id)
    if not record:
                    raise HTTPException(status_code=404, detail="No subscription found")
                await pp_req("POST", f"/v1/billing/subscriptions/{record['sub_id']}/cancel", json={"reason": "User requested"})
    subs_db[user_id]["status"] = "CANCELLED"
    _save_subs(subs_db)
    return {"cancelled": True}


@webhook_router.post("/paypal")
async def paypal_hook(request: Request):
            try:
                            payload = await request.json()
except Exception:
        raise HTTPException(status_code=400, detail="Bad payload")
    event = payload.get("event_type", "")
    resource = payload.get("resource", {})
    sub_id = resource.get("id") or resource.get("billing_agreement_id", "")
    logger.info("PayPal webhook: %s sub=%s", event, sub_id)
    for uid, rec in subs_db.items():
                    if rec.get("sub_id") == sub_id:
                                        if event in ("BILLING.SUBSCRIPTION.ACTIVATED", "PAYMENT.SALE.COMPLETED"):
                                                                subs_db[uid]["status"] = "ACTIVE"
                    elif event in ("BILLING.SUBSCRIPTION.CANCELLED", "BILLING.SUBSCRIPTION.EXPIRED"):
                                            subs_db[uid]["status"] = "CANCELLED"
                                        _save_subs(subs_db)
            break
    return {"received": True}
