from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from services.mongodb import create_indexes
from routes.upload import router as upload_router
from routes.invoices import router as invoices_router
from routes.review import router as review_router
from routes.export import router as export_router
from routes.analytics import router as analytics_router
from routes.po import router as po_router

app = FastAPI(
    title="InvoiceIQ API v2",
    description="AI-powered invoice processing — LangGraph + Gemini 2.5 Flash",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(invoices_router)
app.include_router(review_router)
app.include_router(export_router)
app.include_router(analytics_router)
app.include_router(po_router)


@app.on_event("startup")
async def startup():
    await create_indexes()
    print("🚀 InvoiceIQ v2 API started")
    print(f"   Docs: http://localhost:8000/docs")


@app.get("/")
async def root():
    return {"app": "InvoiceIQ", "version": "2.0.0", "status": "running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
