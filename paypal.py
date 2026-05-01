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
SUBS_FILE = os.getenv("SUBS_DB_PATH", "/data/subs.json")

PLANS = {
        "free": {"name": "Free Trial", "price": 0, "features": ["5 AI tasks/day", "Basic business tools", "Email support"]},
        "pro": {"name": "Pro", "price": 14.99, "paypal_plan_id": os.getenv("PAYPAL_PRO_PLAN_ID", ""), "features": ["Unlimited AI tasks", "Business automation", "Priority support", "Custom workflows"]},
        "ultimate": {"name": "Ultimate", "price": 29.99, "paypal_plan_id": os.getenv("PAYPAL_ULTIMATE_PLAN_ID", ""), "features": ["Everything in Pro", "Multi-business management", "API access", "Dedicated support", "Advanced analytics"]},
}

# --- Persistent JSON storage (survives restarts) ---
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

# --- Cached PayPal OAuth token ---
_token_cache = {"token": None, "expires": 0}

async def pp_token():
        if _token_cache["token"] and time.time() > _token_cache["expires"]:
                    return _token_cache["token"]
                async with httpx.AsyncClient() as c:
                            r = await c.post(f"{BASE}/v1/oauth2/token", data={"grant_type": "client_credentials"}, auth=(PAYPAL_ID, PAYPAL_SECRET))
                            r.raise_for_status()
                            data = r.json()
                            _token_cache["token"] = data["access_token"]
                            _token_cache["expires"] = time.time() + data.get("expires_in", 3600) - 60
                            return _token_cache["token"]

async def pp_req(method, path, data=None):
        token = await pp_token()
    async with httpx.AsyncClient() as c:
                r = await c.request(method, f"{BASE}{path}", json=data, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
                r.raise_for_status()
                return r.json() if r.content else {}

# --- API key auth ---
async def verify_api_key(x_api_key: str = Header(None)):
        if API_KEY and x_api_key != API_KEY:
                    raise HTTPException(401, "Invalid or missing API key")

class SubCreate(BaseModel):
        plan: str = Field(..., pattern="^(pro|ultimate)$")
    return_url: str = None
    cancel_url: str = None

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"], dependencies=[Depends(verify_api_key)])

@router.get("/plans")
async def list_plans():
        return {"plans": PLANS}

@router.get("/me")
async def my_sub(user_id: str = "anonymous"):
        sub = subs_db.get(user_id, {"plan": "free", "status": "active"})
    return {"subscription": sub}

@router.post("/create")
async def create_sub(body: SubCreate, user_id: str = "anonymous"):
        plan = PLANS.get(body.plan)
    if not plan or not plan.get("paypal_plan_id"):
                raise HTTPException(400, "Invalid plan")
            ret_url = body.return_url or f"{APP_URL}/success"
    can_url = body.cancel_url or f"{APP_URL}/cancel"
    result = await pp_req("POST", "/v1/billing/subscriptions", {"plan_id": plan["paypal_plan_id"], "application_context": {"brand_name": "MAD Madison AI Assistant", "shipping_preference": "NO_SHIPPING", "user_action": "SUBSCRIBE_NOW", "return_url": ret_url, "cancel_url": can_url}})
    sid = result.get("id")
    url = next((l["href"] for l in result.get("links", []) if l["rel"] == "approve"), None)
    subs_db[user_id] = {"plan": body.plan, "status": "pending", "paypal_id": sid, "created": datetime.now(timezone.utc).isoformat()}
    _save_subs(subs_db)
    return {"subscription_id": sid, "approve_url": url}

@router.post("/cancel")
async def cancel_sub(user_id: str = "anonymous"):
        sub = subs_db.get(user_id)
        if not sub or sub.get("status") != "active":
                    raise HTTPException(404, "No active subscription")
                await pp_req("POST", f"/v1/billing/subscriptions/{sub['paypal_id']}/cancel", {"reason": "User requested"})
    sub["status"] = "cancelled"
    _save_subs(subs_db)
    return {"status": "cancelled"}

# --- Webhook with PayPal signature verification ---
webhook_router = APIRouter(tags=["webhooks"])

async def _verify_webhook(request: Request, body_bytes: bytes):
        if not PAYPAL_WEBHOOK_ID:
                    logger.warning("PAYPAL_WEBHOOK_ID not set - skipping signature verification")
                    return True
                headers = request.headers
    token = await pp_token()
    verify_payload = {
                "auth_algo": headers.get("paypal-auth-algo", ""),
                "cert_url": headers.get("paypal-cert-url", ""),
                "transmission_id": headers.get("paypal-transmission-id", ""),
                "transmission_sig": headers.get("paypal-transmission-sig", ""),
                "transmission_time": headers.get("paypal-transmission-time", ""),
                "webhook_id": PAYPAL_WEBHOOK_ID,
                "webhook_event": json.loads(body_bytes),
    }
    async with httpx.AsyncClient() as c:
                r = await c.post(f"{BASE}/v1/notifications/verify-webhook-signature", json=verify_payload, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
                r.raise_for_status()
                return r.json().get("verification_status") == "SUCCESS"

@webhook_router.post("/api/v1/webhooks/paypal")
async def paypal_hook(request: Request):
        body_bytes = await request.body()
    if not await _verify_webhook(request, body_bytes):
                raise HTTPException(401, "Webhook signature verification failed")
            body = json.loads(body_bytes)
    event = body.get("event_type", "")
    rid = body.get("resource", {}).get("id", "")
    logger.info(f"PayPal webhook: {event} sub={rid}")
    uid = next((u for u, s in subs_db.items() if s.get("paypal_id") == rid), None)
    if uid:
                if "ACTIVATED" in event: subs_db[uid]["status"] = "active"
    elif "CANCELLED" in event: subs_db[uid]["status"] = "cancelled"
elif "SUSPENDED" in event: subs_db[uid]["status"] = "suspended"
elif "EXPIRED" in event: subs_db[uid]["status"] = "expired"; subs_db[uid]["plan"] = "free"
elif "PAYMENT.SALE" in event: subs_db[uid]["last_payment"] = datetime.now(timezone.utc).isoformat()
        _save_subs(subs_db)
    return {"received": True}
