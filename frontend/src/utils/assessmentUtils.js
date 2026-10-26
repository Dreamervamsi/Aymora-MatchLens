/**
 * Utility functions for verifying scenario assessment state and profile persistence.
 */

/**
 * Checks whether scenario assessment responses are authoritatively persisted in a user's confirmed profile.
 *
 * @param {Object} profile - User profile object returned from profileService.getProfile()
 * @param {Object} [currentAssessmentData] - Optional active/completed assessment data object
 * @returns {boolean} True if valid assessment responses exist in the profile matching expected criteria.
 */
export const isAssessmentPersistedInProfile = (profile, currentAssessmentData = null) => {
  if (!profile) return false;

  const responses = Array.isArray(profile.scenario_responses)
    ? profile.scenario_responses
    : Array.isArray(profile.scenarios)
    ? profile.scenarios
    : null;

  if (!responses || responses.length === 0) return false;

  // Determine expected scenario IDs if assessment data is supplied
  const expectedIds = currentAssessmentData?.selected_scenario_ids?.length
    ? currentAssessmentData.selected_scenario_ids
    : currentAssessmentData?.summary_data
    ? Object.keys(currentAssessmentData.summary_data)
    : [];

  // If specific assessment scenarios are expected, verify every expected ID is present
  if (expectedIds.length > 0) {
    const allExpectedPresent = expectedIds.every((expectedId) => {
      const matchingResponses = responses.filter(
        (r) => r && (r.scenario_id === expectedId || r.id === expectedId)
      );
      if (matchingResponses.length === 0) return false;

      // Compare self-behavior and partner-expectation values where summary_data allows
      const summary = currentAssessmentData?.summary_data?.[expectedId];
      if (summary) {
        if (summary.self_response) {
          const matchesSelf = matchingResponses.some(
            (r) =>
              r.normalized_preference === summary.self_response ||
              r.self_response === summary.self_response ||
              r.raw_answer === summary.self_response
          );
          if (!matchesSelf) return false;
        }

        if (summary.partner_expectation) {
          const matchesPartner = matchingResponses.some(
            (r) =>
              r.expected_partner_preference === summary.partner_expectation ||
              r.partner_expectation === summary.partner_expectation
          );
          if (!matchesPartner) return false;
        }
      }

      return true;
    });

    return allExpectedPresent;
  }

  // General check (no specific assessment data provided): check that valid structured responses exist
  return responses.every((r) => Boolean(r && (r.scenario_id || r.id)));
};

export default {
  isAssessmentPersistedInProfile,
};
