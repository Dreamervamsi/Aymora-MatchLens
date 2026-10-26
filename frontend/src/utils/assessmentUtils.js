/**
 * Utility functions for strictly verifying scenario assessment state and profile persistence.
 */

// Canonical MVP scenario IDs defined in backend ScenarioCatalog
export const CANONICAL_MVP_SCENARIO_IDS = [
  'conflict_resolution_01',
  'social_energy_01',
  'financial_planning_01',
];

/**
 * Checks whether scenario assessment responses are strictly and authoritatively persisted in a user's confirmed profile.
 *
 * Rules & Requirements:
 * 1. Profile must exist and belong to expectedUserId (if expectedUserId is supplied).
 * 2. Profile must contain persisted scenario responses array.
 * 3. Every expected scenario must have persisted entries for BOTH self behavior AND partner expectation.
 * 4. Never accepts responses.some(...) or partial responses as proof of completion.
 * 5. Does not treat a single or partial scenario response as a completed assessment.
 * 6. Does not treat an assessment ID stored in sessionStorage as proof of completion.
 *
 * @param {Object} profile - User profile object returned from profileService.getProfile()
 * @param {Object} [currentAssessmentData] - Optional active/completed assessment state response from backend
 * @param {string} [expectedUserId] - Optional expected user ID to verify profile ownership
 * @returns {boolean} True if all required scenarios have persisted self and partner preferences in the profile.
 */
export const isAssessmentPersistedInProfile = (
  profile,
  currentAssessmentData = null,
  expectedUserId = null
) => {
  if (!profile || typeof profile !== 'object') return false;

  // 1. Verify user ownership if expectedUserId is provided
  if (expectedUserId && profile.user_id && profile.user_id !== expectedUserId) {
    return false;
  }

  // Also check ownership against currentAssessmentData if provided
  if (
    currentAssessmentData?.user_id &&
    profile.user_id &&
    currentAssessmentData.user_id !== profile.user_id
  ) {
    return false;
  }

  const responses = Array.isArray(profile.scenario_responses)
    ? profile.scenario_responses
    : Array.isArray(profile.scenarios)
    ? profile.scenarios
    : null;

  if (!responses || responses.length === 0) return false;

  // 2. Determine required scenario IDs
  let expectedIds = [];

  if (Array.isArray(currentAssessmentData?.selected_scenario_ids) && currentAssessmentData.selected_scenario_ids.length > 0) {
    expectedIds = currentAssessmentData.selected_scenario_ids;
  } else if (currentAssessmentData?.summary_data && Object.keys(currentAssessmentData.summary_data).length > 0) {
    expectedIds = Object.keys(currentAssessmentData.summary_data);
  } else {
    // Default to the complete MVP scenario set
    expectedIds = CANONICAL_MVP_SCENARIO_IDS;
  }

  if (!expectedIds || expectedIds.length === 0) return false;

  // 3. Strict Verification: EVERY required scenario ID must have BOTH self_behavior AND partner_expectation persisted
  const allRequiredComplete = expectedIds.every((scenarioId) => {
    // Filter matching responses for this scenario ID
    const matching = responses.filter(
      (r) => r && (r.scenario_id === scenarioId || r.id === scenarioId)
    );

    if (matching.length === 0) return false;

    // Check for self behavior preference presence across canonical fields
    const hasSelfBehavior = matching.some((r) => {
      const val = r.normalized_preference || r.self_response || r.raw_answer;
      return typeof val === 'string' && val.trim().length > 0;
    });

    // Check for partner expectation preference presence across canonical fields
    const hasPartnerExpectation = matching.some((r) => {
      const val = r.expected_partner_preference || r.partner_expectation;
      return typeof val === 'string' && val.trim().length > 0;
    });

    if (!hasSelfBehavior || !hasPartnerExpectation) {
      return false;
    }

    // If currentAssessmentData contains summary_data, cross-check specific values
    const summary = currentAssessmentData?.summary_data?.[scenarioId];
    if (summary) {
      if (summary.self_response) {
        const matchesSelf = matching.some(
          (r) =>
            r.normalized_preference === summary.self_response ||
            r.self_response === summary.self_response ||
            (r.raw_answer && r.raw_answer.includes(summary.self_response))
        );
        if (!matchesSelf) return false;
      }

      if (summary.partner_expectation) {
        const matchesPartner = matching.some(
          (r) =>
            r.expected_partner_preference === summary.partner_expectation ||
            r.partner_expectation === summary.partner_expectation ||
            (r.raw_answer && r.raw_answer.includes(summary.partner_expectation))
        );
        if (!matchesPartner) return false;
      }
    }

    return true;
  });

  return allRequiredComplete;
};

export default {
  CANONICAL_MVP_SCENARIO_IDS,
  isAssessmentPersistedInProfile,
};
