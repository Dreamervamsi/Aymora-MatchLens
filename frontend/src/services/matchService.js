import apiClient from './apiClient';

/**
 * Service module for Reciprocal Matching endpoints.
 * Endpoint prefix: /api/v1/matches
 */
export const matchService = {
  /**
   * Retrieves top reciprocal match recommendations for a confirmed user profile.
   * GET /api/v1/matches/{user_id}?top_k={topK}
   */
  getMatches: async (userId, topK = 3) => {
    return apiClient.get(`/matches/${userId}?top_k=${topK}`);
  },
};

export default matchService;
