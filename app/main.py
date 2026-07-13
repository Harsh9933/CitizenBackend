from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.auth.routes import router as auth_router
from app.core.database import get_db
from app.processing_service.routes import router as processing_router
from app.query_service.routes import router as query_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Civic Issue Reporting System",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/db", tags=["Test"])
async def testing(db: AsyncSession = Depends(get_db)):
    url = db.get_bind().url.render_as_string(hide_password=False)

    return url

# Include routers
app.include_router(auth_router)
app.include_router(processing_router)
app.include_router(query_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Civic Issue Reporting System API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}