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
   * Submits a user message turn and streams assistant tokens via Server-Sent Events (SSE).
   * POST /api/v1/interview/{session_id}/turn/stream
   */
  processTurnStream: async (sessionId, userMessage, onDelta, onComplete, onError, signal = null) => {
    const baseURL = apiClient.baseURL || (import.meta.env.VITE_API_BASE_URL ? `${import.meta.env.VITE_API_BASE_URL}/api/v1` : 'http://localhost:8000/api/v1');
    const url = `${baseURL}/interview/${sessionId}/turn/stream`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ user_message: userMessage }),
        signal,
      });

      if (!response.ok) {
        let errData;
        try {
          errData = await response.json();
        } catch {
          errData = { detail: `HTTP error ${response.status}` };
        }
        const err = new Error(errData.detail || 'Streaming failed');
        err.status = response.status;
        throw err;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete trailing line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim();
            if (!dataStr) continue;
            try {
              const event = JSON.parse(dataStr);
              if (event.type === 'content_delta') {
                if (onDelta) onDelta(event.delta);
              } else if (event.type === 'turn_complete') {
                if (onComplete) onComplete(event.data);
              }
            } catch (pErr) {
              console.warn('Error parsing SSE event data:', pErr, dataStr);
            }
          }
        }
      }

      if (buffer.trim().startsWith('data:')) {
        const dataStr = buffer.trim().slice(5).trim();
        if (dataStr) {
          try {
            const event = JSON.parse(dataStr);
            if (event.type === 'content_delta') {
              if (onDelta) onDelta(event.delta);
            } else if (event.type === 'turn_complete') {
              if (onComplete) onComplete(event.data);
            }
          } catch (pErr) {
            console.warn('Error parsing final SSE event data:', pErr, dataStr);
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      if (onError) onError(err);
      else throw err;
    }
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
