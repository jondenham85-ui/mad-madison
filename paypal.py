import os, logging, json, time
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger("mad_madison.paypal")
PAYPAL_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
MODE = os.getenv("PAYPAL_MODE", "sandbox")
BASE = "https://api-m.paypal.com" if MODE == "live" else "https://api-m.sandbox.paypal.com"
APP_URL = os.getenv("APP_URL", "htps://mad-madison-production.up.railway.app")
API_KEY = os.getenv("MAD_API_KEY", "")
SUBS_FILE = os.getenv("SUBS_DB_PATH", "/tmp/subs.json")
PLANS_FILE = "/tmp/pp_plans.json"
_token_cache = {"token": None, "expires": 0}
subs_db = {}
_plans_cache = {}


def _load_subs():
  try:
    with open(SUBS_FILE, "r") as f:
      return json.load(f)
  except Exception:
    return {}


def _save_subs(db):
  os.makedirs(os.path.dirname(SUBS_FILE) or ".", exist_ok=True)
  with open(SUBS_FILE, "w") as f:
    json.dump(db, f)


def _load_plans():
  try:
    with open(PLANS_FILE, "r") as f:
      return json.load(f)
  except Exception:
    return {}


def _save_plans(p):
  with open(PLANS_FILE, "w") as f:
    json.dump(p, f)


subs_db = _load_subs()
_plans_cache = _load_plans()


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


async def ensure_plans():
  global _plans_cache
  if _plans_cache.get("pro") and _plans_cache.get("ultimate"):
    return _plans_cache
    product = await pp_req("POST", "/v1/catalogs/products", {"name": "MAD Madison AI", "type": "SERVICE", "category": "SOFTWARE"})
    pid = product["id"]
    pro = await pp_req("POST", "/v1/billing/plans", {"product_id": pid, "name": "Pro", "billing_cycles": [{"frequency": {"interval_unit": "MONTH", "interval_count": 1}, "tenure_type": "REGULAR", "sequence": 1, "total_cycles": 0, "pricing_scheme": {"fixed_price": {"value": "14.99", "currency_code": "USD"}}}], "payment_preferences": {"auto_bill_outstanding": True, "payment_failure_threshold": 3}})
    ultimate = await pp_req("POST", "/v1/billing/plans", {"product_id": pid, "name": "Ultimate", "billing_cycles": [{"frequency": {"interval_unit": "MONTH", "interval_count": 1}, "tenure_type": "REGULAR", "sequence": 1, "total_cycles": 0, "pricing_scheme": {"fixed_price": {"value": "29.99", "currency_code": "USD"}}}], "payment_preferences": {"auto_bill_outstanding": True, "payment_failure_threshold": 3}})
    _plans_cache = {"pro": pro["id"], "ultimate": ultimate["id"], "product": pid}
    _save_plans(_plans_cache)
    return _plans_cache


PLANS_META = {"free": {"name": "Free Trial", "price": 0}, "pro": {"name": "Pro", "price": 14.99}, "ultimate": {"name": "Ultimate", "price": 29.99}}


async def verify_api_key(x_api_key: str = Header(None)):
  if API_KEY and x_api_key != API_KEY:
    raise HTTPException(401, "Invalid or missing API key")


class SubCreate(BaseModel):
  plan: str = Field(..., pattern="^(pro|ultimate)$")
  return_url: str = None
  cancel_url: str = None


router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"], dependencies=[Depends(verify_api_key)])
webhook_router = APIRouter(tags=["webhooks"])


@router.get("/plans")
async def list_plans():
  plans = await ensure_plans()
  return {"plans": {k: {**v, "paypal_plan_id": plans.get(k, "")} for k, v in PLANS_META.items()}}


@router.get("/me")
async def my_sub(user_id: str = "anonymous"):
  return {"subscription": subs_db.get(user_id, {"plan": "free", "status": "active"})}


@router.post("/create")
async def create_sub(body: SubCreate, user_id: str = "anonymous"):
  plans = await ensure_plans()
  plan_id = plans.get(body.plan)
  if not plan_id:
    raise HTTPException(400, "Plan not available")
    result = await pp_req("POST", "/v1/billing/subscriptions", {"plan_id": plan_id, "application_context": {"brand_name": "MAD Madison", "shipping_preference": "NO_SHIPPING", "user_action": "SUBSCRIBE_NOW", "return_url": body.return_url or f"{APP_URL}/success", "cancel_url": body.cancel_url or f"{APP_URL}/cancel"}})
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


@webhook_router.post("/api/v1/webhooks/paypal")
async def paypal_hook(request: Request):
  body = json.loads(await request.body())
  event = body.get("event_type", "")
  rid = body.get("resource", {}).get("id", "")
  uid = next((u for u, s in subs_db.items() if s.get("paypal_id") == rid), None)
  if uid:
    if "ACTIVATED" in event: subs_db[uid]["status"] = "active"
  elif "CANCELLED" in event: subs_db[uid]["status"] = "cancelled"
elif "SUSPENDED" in event: subs_db[uid]["status"] = "suspended"
elif "PAYMENT.SALE" in event: subs_db[uid]["last_payment"] = datetime.now(timezone.utc).isoformat()
_save_subs(subs_db)
return {"received": True}
