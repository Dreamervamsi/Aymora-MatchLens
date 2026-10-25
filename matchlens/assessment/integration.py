import logging
from copy import deepcopy
from typing import List, Optional, Set

from matchlens.models.profile import UserProfile
from matchlens.models.scenario import ScenarioCatalog, ScenarioResponse

logger = logging.getLogger(__name__)


def attach_scenario_responses(
    profile: UserProfile,
    new_responses: List[ScenarioResponse],
    replace_existing: bool = False,
) -> UserProfile:
    """
    Attaches confirmed ScenarioResponse objects to an existing UserProfile without mutating the original profile.

    Requirements:
    - Preserves all existing attributes, expectations, dealbreakers, and weights.
    - Validates scenario IDs and options against ScenarioCatalog.
    - Prevents duplicate scenario IDs (unless replace_existing=True).
    - Returns a newly validated UserProfile.

    Args:
        profile: The original UserProfile.
        new_responses: List of canonical ScenarioResponse objects to attach.
        replace_existing: If True, existing scenario responses with matching scenario_ids will be overwritten.
                          If False, raises ValueError if a duplicate scenario_id is encountered.

    Returns:
        A new UserProfile containing the attached scenario responses.
    """
    if not new_responses:
        return deepcopy(profile)

    # Validate each new response against ScenarioCatalog
    for resp in new_responses:
        defn = ScenarioCatalog.get_definition(resp.scenario_id)
        if not defn:
            raise ValueError(f"Scenario ID '{resp.scenario_id}' is unknown and not found in ScenarioCatalog.")

        if resp.target_dimension != defn.target_dimension:
            raise ValueError(
                f"Scenario '{resp.scenario_id}' target dimension '{resp.target_dimension}' "
                f"does not match catalog dimension '{defn.target_dimension}'."
            )

        norm_pref = resp.normalized_preference.strip().lower() if resp.normalized_preference else ""
        if norm_pref not in defn.allowed_options:
            raise ValueError(
                f"Option '{resp.normalized_preference}' is invalid for scenario '{resp.scenario_id}'. "
                f"Allowed options: {defn.allowed_options}."
            )

        if resp.expected_partner_preference:
            exp_pref = resp.expected_partner_preference.strip().lower()
            if exp_pref not in defn.allowed_options:
                raise ValueError(
                    f"Expected partner option '{resp.expected_partner_preference}' is invalid for scenario '{resp.scenario_id}'. "
                    f"Allowed options: {defn.allowed_options}."
                )

    # Deep-copy existing profile to avoid mutating the original
    updated_profile_dict = profile.model_dump()
    existing_scenarios = [ScenarioResponse.model_validate(s) for s in updated_profile_dict.get("scenarios", [])]

    # Map existing scenarios by scenario_id
    scenarios_map = {s.scenario_id: s for s in existing_scenarios}

    # Process new responses
    for resp in new_responses:
        if resp.scenario_id in scenarios_map:
            if not replace_existing:
                raise ValueError(
                    f"Duplicate scenario_id '{resp.scenario_id}' found in profile. "
                    "Set replace_existing=True to overwrite existing scenario responses."
                )
            logger.info(f"Replacing existing scenario response for '{resp.scenario_id}'.")
            scenarios_map[resp.scenario_id] = resp
        else:
            scenarios_map[resp.scenario_id] = resp

    # Update scenario list in profile dictionary and validate newly constructed UserProfile
    updated_profile_dict["scenarios"] = [s.model_dump() for s in scenarios_map.values()]
    new_profile = UserProfile.model_validate(updated_profile_dict)

    return new_profile
