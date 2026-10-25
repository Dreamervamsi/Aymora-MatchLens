import apiClient from './apiClient';

/**
 * Service module for Interview onboarding endpoints.
 * Endpoint prefix: /api/v1/interview
 */
export const interviewService = {
  /**
   * Initializes a new conversational interview session.
   * POST /api/v1/interview/start
   */
  startInterview: async (userId, sessionId = null) => {
    return apiClient.post('/interview/start', {
      user_id: userId,
      ...(sessionId ? { session_id: sessionId } : {}),
    });
  },

  /**
   * Submits a user message turn in an ongoing interview session.
   * POST /api/v1/interview/{session_id}/turn
   */
  processTurn: async (sessionId, userMessage) => {
    return apiClient.post(`/interview/${sessionId}/turn`, {
      user_message: userMessage,
    });
  },

  /**
   * Retrieves interview state and draft profile.
   * GET /api/v1/interview/{session_id}
   */
  getInterviewState: async (sessionId) => {
    return apiClient.get(`/interview/${sessionId}`);
  },

  /**
   * Finalizes and confirms draft interview profile into repository.
   * POST /api/v1/interview/{session_id}/confirm
   */
  confirmProfile: async (sessionId) => {
    return apiClient.post(`/interview/${sessionId}/confirm`);
  },
};

export default interviewService;
