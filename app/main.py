from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from app.api import webhook, auth, invoices, onboarding, vendors

app = FastAPI(title="GST Guard", description="WhatsApp-first GST ITC Recovery Agent")

app.include_router(webhook.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(invoices.router, prefix="/api")
app.include_router(onboarding.router, prefix="/api")
app.include_router(vendors.router, prefix="/api")

@app.get("/")
def read_root():
    return FileResponse("frontend/index.html")

@app.get("/health")
def health_check():
    return {"status": "ok"}
