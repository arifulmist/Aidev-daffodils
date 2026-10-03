from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import init_db
from backend.api.complaints import router as complaints_router
from backend.api.investigations import router as investigations_router
from backend.api.transactions import router as transactions_router
from backend.api.cases import router as cases_router
from backend.api.metrics import router as metrics_router
from backend.api.demo import router as demo_router
from backend.api.alerts import router as alerts_router

# Initialize database schema
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Transaction Dispute Investigator for upay Operations & Service Intelligence (Hackathon 2026)"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(investigations_router)
app.include_router(complaints_router)
app.include_router(transactions_router)
app.include_router(cases_router)
app.include_router(metrics_router)
app.include_router(demo_router)
app.include_router(alerts_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "models_loaded": True
    }

@app.get("/api/supabase/status")
def supabase_status():
    from backend.services.supabase_service import supabase_service
    return supabase_service.check_health()

dist_path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if dist_path.exists() and (dist_path / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "system": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "operational",
            "endpoints": {
                "investigations": "/api/investigations/run",
                "complaints": "/api/complaints",
                "transactions": "/api/transactions",
                "cases": "/api/cases",
                "metrics": "/api/metrics",
                "demo": "/api/demo/cases",
                "docs": "/docs"
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
