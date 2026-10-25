/**
 * Core Native Fetch API Client.
 * Handles base URL configuration, request timeouts, JSON body serialization,
 * FastAPI error parsing, and network error handling.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_V1_PREFIX = '/api/v1';

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Standardized HTTP request wrapper.
 */
async function request(endpoint, options = {}) {
  const {
    method = 'GET',
    body = null,
    headers = {},
    timeout = 15000, // 15s default request timeout
    ...customConfig
  } = options;

  const url = `${BASE_URL}${API_V1_PREFIX}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const config = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    signal: controller.signal,
    ...customConfig,
  };

  if (body !== null && body !== undefined) {
    config.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  try {
    const response = await fetch(url, config);
    clearTimeout(timeoutId);

    let responseData = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      responseData = await response.json();
    } else {
      responseData = await response.text();
    }

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

      if (responseData && typeof responseData === 'object') {
        if (typeof responseData.detail === 'string') {
          errorMessage = responseData.detail;
        } else if (Array.isArray(responseData.detail)) {
          // Parse FastAPI Pydantic validation error array
          errorMessage = responseData.detail
            .map((err) => `${err.loc ? err.loc.join('.') : 'field'}: ${err.msg}`)
            .join(' | ');
        }
      }

      throw new ApiError(errorMessage, response.status, responseData);
    }

    return responseData;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error.name === 'AbortError') {
      throw new ApiError('Request timed out after 15 seconds. Please try again.', 408);
    }

    throw new ApiError(
      error.message || 'Unable to connect to MatchLens backend. Please check your network connection.',
      0
    );
  }
}

export const apiClient = {
  get: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'POST', body }),
  patch: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'PATCH', body }),
};

export default apiClient;
