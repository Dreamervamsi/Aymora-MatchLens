"""
Comprehensive integration and API endpoint tests for MatchLens Phase 6 FastAPI backend.
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from matchlens.ai.models import ExtractedProfileUpdate, PartialUserAttributes, PartialPartnerPreferences
from matchlens.api.app import app
from matchlens.models.profile import UserProfile


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "v1"


def test_openapi_docs(client):
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()


@patch("matchlens.ai.extractor.GroqProfileExtractor.extract_from_text")
@patch("matchlens.ai.scenario_extractor.GroqScenarioExtractor.normalize_response")
def test_full_e2e_workflow(mock_normalize, mock_extract, client):
    user_id = "test_user_e2e"

    # 1. Start Interview
    res = client.post("/api/v1/interview/start", json={"user_id": user_id})
    assert res.status_code == 201
    turn_data = res.json()
    session_id = turn_data["session_id"]
    assert session_id is not None

    # 2. Mock Groq interview extraction response providing essential self and partner attributes
    mock_extract.return_value = ExtractedProfileUpdate(
        confirmed_self_attributes=PartialUserAttributes(
            age=28,
            gender="man",
            relationship_intent="long_term",
            core_values=["honesty", "family", "ambition"],
            smoking="never",
            drinking="socially",
            wants_children="yes",
        ),
        confirmed_partner_preferences=PartialPartnerPreferences(
            min_age=22,
            max_age=32,
            acceptable_genders=["woman"],
            desired_intentions=["long_term"],
            desired_values=["honesty", "family"],
            acceptable_smoking=["never"],
            acceptable_drinking=["socially", "never"],
            desired_wants_children=["yes"],
        ),
    )

    turn_res1 = client.post(
        f"/api/v1/interview/{session_id}/turn",
        json={"user_message": "I am 28, male, looking for a long term relationship with a female aged 22-32."},
    )
    assert turn_res1.status_code == 200

    turn_res2 = client.post(
        f"/api/v1/interview/{session_id}/turn",
        json={"user_message": "/finish"},
    )
    assert turn_res2.status_code == 200
    turn_json = turn_res2.json()
    assert turn_json["is_ready_for_review"] is True

    # 3. Confirm Interview Profile
    confirm_res = client.post(f"/api/v1/interview/{session_id}/confirm")
    assert confirm_res.status_code == 200
    profile_data = confirm_res.json()
    assert profile_data["user_id"] == user_id
    assert profile_data["attributes"]["age"] == 28

    # 4. Verify profile in repository
    prof_res = client.get(f"/api/v1/profiles/{user_id}")
    assert prof_res.status_code == 200

    # 5. Start Scenario Assessment
    scen_start_res = client.post(
        "/api/v1/assessment/start",
        json={"user_id": user_id, "selected_scenario_ids": ["conflict_resolution_01"]},
    )
    assert scen_start_res.status_code == 201
    scen_data = scen_start_res.status_code == 201
    assessment_id = scen_start_res.json()["assessment_id"]

    # 6. Submit self behavior response
    turn1 = client.post(
        f"/api/v1/assessment/{assessment_id}/turn",
        json={"user_response": "cool_down_first"},
    )
    assert turn1.status_code == 200

    # 7. Submit partner expectation response
    turn2 = client.post(
        f"/api/v1/assessment/{assessment_id}/turn",
        json={"user_response": "cool_down_first"},
    )
    assert turn2.status_code == 200
    assert turn2.json()["status"] == "ready_for_review"

    # 8. Confirm assessment
    confirm_scen_res = client.post(f"/api/v1/assessment/{assessment_id}/confirm")
    assert confirm_scen_res.status_code == 200
    updated_profile = confirm_scen_res.json()
    assert len(updated_profile["scenarios"]) == 1
    assert updated_profile["scenarios"][0]["scenario_id"] == "conflict_resolution_01"

    # 9. Get Reciprocal Matches
    matches_res = client.get(f"/api/v1/matches/{user_id}?top_k=3")
    assert matches_res.status_code == 200
    match_data = matches_res.json()
    assert match_data["requesting_user_id"] == user_id
    assert "top_matches" in match_data
    assert len(match_data["top_matches"]) > 0


def test_missing_and_invalid_ids(client):
    # Non-existent profile
    res = client.get("/api/v1/profiles/non_existent_id")
    assert res.status_code == 404

    # Non-existent interview turn
    res = client.post("/api/v1/interview/invalid_session_id/turn", json={"user_message": "hello"})
    assert res.status_code == 404

    # Non-existent assessment turn
    res = client.post("/api/v1/assessment/invalid_assessment_id/turn", json={"user_response": "hello"})
    assert res.status_code == 404


def test_premature_interview_confirm(client):
    start_res = client.post("/api/v1/interview/start", json={"user_id": "incomplete_user"})
    session_id = start_res.json()["session_id"]

    # Confirm before ready
    confirm_res = client.post(f"/api/v1/interview/{session_id}/confirm")
    assert confirm_res.status_code == 400
    assert "ready_for_review" in confirm_res.json()["detail"].lower()
