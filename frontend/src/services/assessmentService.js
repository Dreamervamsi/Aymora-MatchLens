import apiClient from './apiClient';

/**
 * Service module for Scenario Assessment endpoints.
 * Endpoint prefix: /api/v1/assessment
 */
export const assessmentService = {
  /**
   * Initializes a scenario assessment for a user.
   * POST /api/v1/assessment/start
   */
  startAssessment: async (userId, selectedScenarioIds = null, assessmentId = null) => {
    return apiClient.post('/assessment/start', {
      user_id: userId,
      ...(selectedScenarioIds ? { selected_scenario_ids: selectedScenarioIds } : {}),
      ...(assessmentId ? { assessment_id: assessmentId } : {}),
    });
  },

  /**
   * Submits user response for active scenario stage.
   * POST /api/v1/assessment/{assessment_id}/turn
   */
  submitTurn: async (assessmentId, userResponse) => {
    return apiClient.post(`/assessment/${assessmentId}/turn`, {
      user_response: userResponse,
    });
  },

  /**
   * Corrects a self or partner response during assessment review.
   * POST /api/v1/assessment/{assessment_id}/correct
   */
  correctResponse: async (assessmentId, scenarioId, target, newValue) => {
    return apiClient.post(`/assessment/${assessmentId}/correct`, {
      scenario_id: scenarioId,
      target: target, // 'self_behavior' or 'partner_expectation'
      new_value: newValue,
    });
  },

  /**
   * Retrieves assessment session status and summary progress.
   * GET /api/v1/assessment/{assessment_id}
   */
  getAssessmentState: async (assessmentId) => {
    return apiClient.get(`/assessment/${assessmentId}`);
  },

  /**
   * Confirms assessment and attaches canonical responses to profile.
   * POST /api/v1/assessment/{assessment_id}/confirm
   */
  confirmAssessment: async (assessmentId) => {
    return apiClient.post(`/assessment/${assessmentId}/confirm`);
  },
};

export default assessmentService;
