import apiClient from './apiClient';

/**
 * Service module for Profile repository endpoints.
 * Endpoint prefix: /api/v1/profiles
 */
export const profileService = {
  /**
   * Retrieves a confirmed UserProfile by user_id.
   * GET /api/v1/profiles/{user_id}
   */
  getProfile: async (userId) => {
    return apiClient.get(`/profiles/${userId}`);
  },

  /**
   * Directly updates or saves a UserProfile.
   * PUT /api/v1/profiles/{user_id}
   */
  updateProfile: async (userId, profileData) => {
    return apiClient.put(`/profiles/${userId}`, profileData);
  },
};

export default profileService;
