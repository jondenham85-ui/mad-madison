import os, uuid
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from paypal import router as paypal_router, webhook_router

app = FastAPI(title="MAD Madison", description="AI Business Assistant by Donkey MAD LLC", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(paypal_router)
app.include_router(webhook_router)

@app.get("/")
async def root():
    return {"service": "MAD Madison", "version": "1.0.0", "type": "AI Business Assistant", "status": "running", "by": "Donkey MAD LLC"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mad-madison", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/ready")
async def ready():
    return {"status": "ready", "service": "mad-madison"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
