from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import paypal, swap
app = FastAPI()
app.include_router(paypal.router)
app.include_router(paypal.webhook_router)
app.include_router(swap.router)
@app.get("/health")
def health():
    return {"status": "healthy", "service": "mad-madison"}
@app.get("/success")
def success():
    return FileResponse("static/success.html")
@app.get("/cancel")
def cancel_page():
    return FileResponse("static/cancel.html")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
