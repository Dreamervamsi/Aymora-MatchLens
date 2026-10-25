"""
Main FastAPI application entrypoint for MatchLens.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from matchlens.ai.exceptions import GroqError
from matchlens.api.config import settings
from matchlens.api.repository import ProfileRepository
from matchlens.api.routers import assessment, health, interview, matches, profiles
from matchlens.interview.orchestrator import InterviewOrchestrator
from matchlens.assessment.orchestrator import ScenarioAssessmentOrchestrator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Instantiates shared singletons for interview, assessment, and profile storage.
    """
    logger.info("Initializing MatchLens API shared services...")
    app.state.profile_repository = ProfileRepository()
    app.state.interview_orchestrator = InterviewOrchestrator()
    app.state.assessment_orchestrator = ScenarioAssessmentOrchestrator()
    yield
    logger.info("Shutting down MatchLens API shared services...")


app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Register API Routers under /api/v1
app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(interview.router, prefix=settings.api_v1_prefix)
app.include_router(assessment.router, prefix=settings.api_v1_prefix)
app.include_router(profiles.router, prefix=settings.api_v1_prefix)
app.include_router(matches.router, prefix=settings.api_v1_prefix)


# Centralized Exception Handlers

@app.exception_handler(GroqError)
async def handle_groq_exception(request: Request, exc: GroqError) -> JSONResponse:
    logger.error(f"Groq AI service error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "AI processing service is temporarily unavailable. Please try again."},
    )


@app.exception_handler(ValueError)
async def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
    msg = str(exc)
    status_code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_400_BAD_REQUEST
    return JSONResponse(
        status_code=status_code,
        content={"detail": msg},
    )


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred."},
    )
