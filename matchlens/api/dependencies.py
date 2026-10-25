"""
Dependency injection providers for MatchLens API.
"""

from typing import Generator
from fastapi import Request

from matchlens.api.repository import ProfileRepository
from matchlens.interview.orchestrator import InterviewOrchestrator
from matchlens.assessment.orchestrator import ScenarioAssessmentOrchestrator


def get_profile_repository(request: Request) -> ProfileRepository:
    return request.app.state.profile_repository


def get_interview_orchestrator(request: Request) -> InterviewOrchestrator:
    return request.app.state.interview_orchestrator


def get_assessment_orchestrator(request: Request) -> ScenarioAssessmentOrchestrator:
    return request.app.state.assessment_orchestrator
