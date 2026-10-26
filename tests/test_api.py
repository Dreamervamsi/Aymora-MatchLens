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


@patch("matchlens.ai.extractor.GroqProfileExtractor.extract_full_profile_batch")
@patch("matchlens.ai.extractor.GroqProfileExtractor.extract_from_text")
@patch("matchlens.ai.scenario_extractor.GroqScenarioExtractor.normalize_response")
def test_full_e2e_workflow(mock_normalize, mock_extract, mock_batch_extract, client):
    user_id = "test_user_e2e"

    # Seed another profile so matching produces a result
    from matchlens.models.profile import UserProfile, UserAttributes, PartnerPreferences
    repo = client.app.state.profile_repository
    repo.save_profile(UserProfile(
        user_id="other_match_user",
        attributes=UserAttributes(age=26, gender="woman", relationship_intent="long_term", smoking="never", drinking="socially", wants_children="yes"),
        expectations=PartnerPreferences(min_age=24, max_age=34, acceptable_genders=["man"], desired_intentions=["long_term"]),
    ))

    # 1. Start Interview
    res = client.post("/api/v1/interview/start", json={"user_id": user_id})
    assert res.status_code == 201
    turn_data = res.json()
    session_id = turn_data["session_id"]
    assert session_id is not None

    # 2. Mock Groq interview extraction response providing essential self and partner attributes
    sample_update = ExtractedProfileUpdate(
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
    mock_extract.return_value = sample_update
    mock_batch_extract.return_value = sample_update

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
    scen_data = scen_start_res.json()
    assessment_id = scen_data["assessment_id"]

    # Check GET assessment state returns summary_data structure
    state_res = client.get(f"/api/v1/assessment/{assessment_id}")
    assert state_res.status_code == 200
    assert "summary_data" in state_res.json()

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
    scen_resp = updated_profile["scenarios"][0]
    assert scen_resp["scenario_id"] == "conflict_resolution_01"
    # Verify independence of self behavior and partner expectation
    assert scen_resp["normalized_preference"] == "cool_down_first"
    assert scen_resp["expected_partner_preference"] == "cool_down_first"

    # 9. Get Reciprocal Matches
    matches_res = client.get(f"/api/v1/matches/{user_id}?top_k=3")
    assert matches_res.status_code == 200
    match_data = matches_res.json()
    assert match_data["requesting_user_id"] == user_id
    assert "top_matches" in match_data
    assert len(match_data["top_matches"]) > 0

    # Verify score structures in match response
    top_match = match_data["top_matches"][0]
    assert "mutual_score" in top_match
    assert top_match["mutual_score"] is not None
    assert "directional_a_to_b" in top_match
    assert top_match["directional_a_to_b"]["directional_score"] is not None
    assert "directional_b_to_a" in top_match
    assert top_match["directional_b_to_a"]["directional_score"] is not None
    assert "evidence_coverage" in top_match
    assert "evidence_summary" in top_match
    assert top_match["evidence_summary"] is not None


def test_reconfirm_interview_preserves_scenarios(client):
    user_id = "test_user_reconfirm"

    # Save initial profile directly into repository via interview flow
    start_res = client.post("/api/v1/interview/start", json={"user_id": user_id})
    session1 = start_res.json()["session_id"]

    with patch("matchlens.ai.extractor.GroqProfileExtractor.extract_from_text") as mock_extract:
        mock_extract.return_value = ExtractedProfileUpdate(
            confirmed_self_attributes=PartialUserAttributes(
                age=30,
                gender="man",
                relationship_intent="long_term",
                smoking="never",
                drinking="never",
                wants_children="no",
            ),
            confirmed_partner_preferences=PartialPartnerPreferences(
                min_age=25,
                max_age=35,
                acceptable_genders=["woman"],
                desired_intentions=["long_term"],
            ),
        )
        client.post(f"/api/v1/interview/{session1}/turn", json={"user_message": "info"})
        client.post(f"/api/v1/interview/{session1}/turn", json={"user_message": "/finish"})

    client.post(f"/api/v1/interview/{session1}/confirm")

    # Add scenario assessment
    ass_res = client.post("/api/v1/assessment/start", json={"user_id": user_id, "selected_scenario_ids": ["conflict_resolution_01"]})
    ass_id = ass_res.json()["assessment_id"]
    client.post(f"/api/v1/assessment/{ass_id}/turn", json={"user_response": "cool_down_first"})
    client.post(f"/api/v1/assessment/{ass_id}/turn", json={"user_response": "cool_down_first"})
    client.post(f"/api/v1/assessment/{ass_id}/confirm")

    # Verify scenario was attached
    prof_before = client.get(f"/api/v1/profiles/{user_id}").json()
    assert len(prof_before["scenarios"]) == 1

    # Start a second interview and confirm
    start_res2 = client.post("/api/v1/interview/start", json={"user_id": user_id})
    session2 = start_res2.json()["session_id"]

    with patch("matchlens.ai.extractor.GroqProfileExtractor.extract_from_text") as mock_extract2:
        mock_extract2.return_value = ExtractedProfileUpdate(
            confirmed_self_attributes=PartialUserAttributes(
                age=31,
                gender="man",
                relationship_intent="long_term",
                smoking="never",
                drinking="never",
                wants_children="no",
            ),
            confirmed_partner_preferences=PartialPartnerPreferences(
                min_age=25,
                max_age=35,
                acceptable_genders=["woman"],
                desired_intentions=["long_term"],
            ),
        )
        client.post(f"/api/v1/interview/{session2}/turn", json={"user_message": "updated info"})
        client.post(f"/api/v1/interview/{session2}/turn", json={"user_message": "/finish"})

    confirm2_res = client.post(f"/api/v1/interview/{session2}/confirm")
    assert confirm2_res.status_code == 200
    prof_after = confirm2_res.json()
    # Ensure scenario is preserved after reconfirming interview
    assert len(prof_after["scenarios"]) == 1
    assert prof_after["scenarios"][0]["scenario_id"] == "conflict_resolution_01"


def test_assessment_confirm_requires_ready_for_review(client):
    user_id = "test_user_ready_review"

    # Create profile
    start_res = client.post("/api/v1/interview/start", json={"user_id": user_id})
    s_id = start_res.json()["session_id"]
    with patch("matchlens.ai.extractor.GroqProfileExtractor.extract_from_text") as mock_extract:
        mock_extract.return_value = ExtractedProfileUpdate(
            confirmed_self_attributes=PartialUserAttributes(
                age=25, gender="woman", relationship_intent="long_term", smoking="never", drinking="socially", wants_children="open"
            ),
            confirmed_partner_preferences=PartialPartnerPreferences(
                min_age=22, max_age=32, acceptable_genders=["man"], desired_intentions=["long_term"]
            ),
        )
        client.post(f"/api/v1/interview/{s_id}/turn", json={"user_message": "info"})
        client.post(f"/api/v1/interview/{s_id}/turn", json={"user_message": "/finish"})
    client.post(f"/api/v1/interview/{s_id}/confirm")

    # Start assessment
    ass_res = client.post("/api/v1/assessment/start", json={"user_id": user_id, "selected_scenario_ids": ["conflict_resolution_01"]})
    ass_id = ass_res.json()["assessment_id"]

    # Attempt to confirm immediately when active
    conf_res = client.post(f"/api/v1/assessment/{ass_id}/confirm")
    assert conf_res.status_code == 400


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


@patch("matchlens.ai.extractor.GroqProfileExtractor.extract_from_text")
def test_interview_turn_stream_endpoint(mock_extract, client):
    start_res = client.post("/api/v1/interview/start", json={"user_id": "stream_user"})
    session_id = start_res.json()["session_id"]

    mock_extract.return_value = ExtractedProfileUpdate(
        confirmed_self_attributes=PartialUserAttributes(age=25),
        confirmed_partner_preferences=PartialPartnerPreferences(min_age=20),
    )

    res = client.post(
        f"/api/v1/interview/{session_id}/turn/stream",
        json={"user_message": "I am 25 years old."},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    body = res.text
    assert "content_delta" in body
    assert "turn_complete" in body
