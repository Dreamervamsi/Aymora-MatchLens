import React, { createContext, useContext, useState, useEffect } from 'react';

/**
 * Lightweight Workflow Context for storing active workflow session identifiers.
 * Persists non-sensitive state (userId, sessionId, assessmentId) in sessionStorage across page refreshes.
 */
const WorkflowContext = createContext(null);

const SESSION_KEYS = {
  USER_ID: 'matchlens_user_id',
  SESSION_ID: 'matchlens_interview_session_id',
  ASSESSMENT_ID: 'matchlens_assessment_id',
};

// Helper to generate a default lightweight user ID if none exists
const generateDefaultUserId = () => {
  return `user_${Math.random().toString(36).substring(2, 9)}`;
};

export const WorkflowProvider = ({ children }) => {
  const [userId, setUserIdState] = useState(() => {
    return sessionStorage.getItem(SESSION_KEYS.USER_ID) || generateDefaultUserId();
  });

  const [sessionId, setSessionIdState] = useState(() => {
    return sessionStorage.getItem(SESSION_KEYS.SESSION_ID) || null;
  });

  const [assessmentId, setAssessmentIdState] = useState(() => {
    return sessionStorage.getItem(SESSION_KEYS.ASSESSMENT_ID) || null;
  });

  // Sync to sessionStorage on changes
  useEffect(() => {
    if (userId) {
      sessionStorage.setItem(SESSION_KEYS.USER_ID, userId);
    }
  }, [userId]);

  useEffect(() => {
    if (sessionId) {
      sessionStorage.setItem(SESSION_KEYS.SESSION_ID, sessionId);
    } else {
      sessionStorage.removeItem(SESSION_KEYS.SESSION_ID);
    }
  }, [sessionId]);

  useEffect(() => {
    if (assessmentId) {
      sessionStorage.setItem(SESSION_KEYS.ASSESSMENT_ID, assessmentId);
    } else {
      sessionStorage.removeItem(SESSION_KEYS.ASSESSMENT_ID);
    }
  }, [assessmentId]);

  const setUserId = (newUserId) => {
    setUserIdState(newUserId);
  };

  const setSessionId = (newSessionId) => {
    setSessionIdState(newSessionId);
  };

  const setAssessmentId = (newAssessmentId) => {
    setAssessmentIdState(newAssessmentId);
  };

  const resetWorkflow = () => {
    setSessionIdState(null);
    setAssessmentIdState(null);
    sessionStorage.removeItem(SESSION_KEYS.SESSION_ID);
    sessionStorage.removeItem(SESSION_KEYS.ASSESSMENT_ID);
  };

  const value = {
    userId,
    sessionId,
    assessmentId,
    setUserId,
    setSessionId,
    setAssessmentId,
    resetWorkflow,
  };

  return (
    <WorkflowContext.Provider value={value}>
      {children}
    </WorkflowContext.Provider>
  );
};

export const useWorkflow = () => {
  const context = useContext(WorkflowContext);
  if (!context) {
    throw new Error('useWorkflow must be used within a WorkflowProvider');
  }
  return context;
};

export default WorkflowContext;
