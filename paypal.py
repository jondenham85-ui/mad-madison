import os, logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger("mad_madison.paypal")
PAYPAL_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
MODE = os.getenv("PAYPAL_MODE", "sandbox")
BASE = "https://api-m.paypal.com" if MODE == "live" else "https://api-m.sandbox.paypal.com"

PLANS = {
    "free": {"name": "Free", "price": 0, "features": ["5 swaps/day", "Standard quality"]},
    "pro": {"name": "Pro", "price": 9.99, "paypal_plan_id": os.getenv("PAYPAL_PRO_PLAN_ID", ""), "features": ["Unlimited swaps", "HD quality", "No watermark"]},
    "ultimate": {"name": "Ultimate", "price": 19.99, "paypal_plan_id": os.getenv("PAYPAL_ULTIMATE_PLAN_ID", ""), "features": ["Everything in Pro", "4K video", "API access", "Analytics"]},
}
subs_db = {}
router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])

async def pp_token():
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/v1/oauth2/token", data={"grant_type": "client_credentials"}, auth=(PAYPAL_ID, PAYPAL_SECRET))
        r.raise_for_status()
        return r.json()["access_token"]

async def pp_req(method, path, data=None):
    token = await pp_token()
    async with httpx.AsyncClient() as c:
        r = await c.request(method, f"{BASE}{path}", json=data, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        r.raise_for_status()
        return r.json() if r.content else {}

class SubCreate(BaseModel):
    plan: str = Field(..., pattern="^(pro|ultimate)$")
    return_url: str = "https://madfaceshift.com/success"
    cancel_url: str = "https://madfaceshift.com/cancel"

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
    result = await pp_req("POST", "/v1/billing/subscriptions", {"plan_id": plan["paypal_plan_id"], "application_context": {"brand_name": "MAD Madison", "shipping_preference": "NO_SHIPPING", "user_action": "SUBSCRIBE_NOW", "return_url": body.return_url, "cancel_url": body.cancel_url}})
    sid = result.get("id")
    url = next((l["href"] for l in result.get("links", []) if l["rel"] == "approve"), None)
    subs_db[user_id] = {"plan": body.plan, "status": "pending", "paypal_id": sid, "created": datetime.now(timezone.utc).isoformat()}
    return {"subscription_id": sid, "approve_url": url}

@router.post("/cancel")
async def cancel_sub(user_id: str = "anonymous"):
    sub = subs_db.get(user_id)
    if not sub or sub.get("status") != "active":
        raise HTTPException(404, "No active subscription")
    await pp_req("POST", f"/v1/billing/subscriptions/{sub['paypal_id']}/cancel", {"reason": "User requested"})
    sub["status"] = "cancelled"
    return {"status": "cancelled"}

webhook_router = APIRouter(tags=["webhooks"])

@webhook_router.post("/api/v1/webhooks/paypal")
async def paypal_hook(request: Request):
    body = await request.json()
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
    return {"received": True}
