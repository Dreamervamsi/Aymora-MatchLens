import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AlertCircle, RefreshCw, ArrowRight, RotateCcw, ShieldAlert, Layers } from 'lucide-react';
import { Card, Button, Badge } from '../components/ui';
import { useWorkflow } from '../context/WorkflowContext';
import assessmentService from '../services/assessmentService';
import profileService from '../services/profileService';
import {
  AssessmentHeader,
  ScenarioProgress,
  ScenarioCard,
  ScenarioResponseForm,
  ScenarioReview,
  AssessmentCompletion,
} from '../components/assessment';

import { isAssessmentPersistedInProfile } from '../utils/assessmentUtils';

export const AssessmentPage = () => {
  const navigate = useNavigate();
  const { userId, assessmentId, setAssessmentId } = useWorkflow();

  // Component State
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [rechecking, setRechecking] = useState(false);
  const [correctingState, setCorrectingState] = useState({});

  const [hasConfirmedProfile, setHasConfirmedProfile] = useState(false);
  const [profileCheckFailed, setProfileCheckFailed] = useState(false);
  const [restorationFailed, setRestorationFailed] = useState(false);
  const [error, setError] = useState(null);
  const [uncertainError, setUncertainError] = useState(null);

  // Turn / State Data
  const [assessmentData, setAssessmentData] = useState(null);

  // Generation counter to protect against stale asynchronous responses
  const activeGenRef = useRef(0);

  // 1. Verify eligibility and initialize/restore session on mount
  const initializeAssessment = useCallback(async () => {
    const currentGen = ++activeGenRef.current;
    setLoading(true);
    setError(null);
    setUncertainError(null);
    setProfileCheckFailed(false);
    setRestorationFailed(false);

    // Read current user ID directly from sessionStorage fallback if context is initializing
    const activeUserId = userId || sessionStorage.getItem('matchlens_user_id');

    if (!activeUserId) {
      if (currentGen === activeGenRef.current) {
        setError('Missing user identifier. Please return to onboarding.');
        setLoading(false);
      }
      return;
    }

    // Step A: Verify confirmed profile exists
    try {
      const profile = await profileService.getProfile(activeUserId);
      if (currentGen === activeGenRef.current) {
        if (!profile || (profile.user_id && profile.user_id !== activeUserId)) {
          setHasConfirmedProfile(false);
        } else {
          setHasConfirmedProfile(true);
        }
      }
    } catch (err) {
      if (currentGen !== activeGenRef.current) return;
      // In unit test mocks or API errors, handle missing profile / 404
      if (err?.status === 404 || err?.message?.includes('404') || err?.message?.toLowerCase().includes('not found')) {
        setHasConfirmedProfile(false);
        setLoading(false);
        return;
      }
      // Server error (500+) during profile check
      setProfileCheckFailed(true);
      setError('Failed to verify confirmed profile. Please check your network or server state.');
      setLoading(false);
      return;
    }

    // Step B: If stored assessmentId exists, attempt to restore it
    const activeAssessmentId = assessmentId || sessionStorage.getItem('matchlens_assessment_id');
    if (activeAssessmentId) {
      try {
        const stateRes = await assessmentService.getAssessmentState(activeAssessmentId);
        if (currentGen === activeGenRef.current) {
          setAssessmentData(stateRes);
          setLoading(false);
          return;
        }
      } catch (err) {
        if (currentGen !== activeGenRef.current) return;
        if (err?.status === 404 || err?.message?.includes('404')) {
          // Session expired or unknown on backend
          setError('Stored assessment session has expired or is invalid. Please start a new assessment.');
          setLoading(false);
          return;
        }
        // Server / Network error during restoration (500, timeout)
        setRestorationFailed(true);
        setError(err?.message || 'Failed to restore assessment session due to a network or server error.');
        setLoading(false);
        return;
      }
    }

    // Step C: No assessmentId, default to ready-to-start state
    if (currentGen === activeGenRef.current) {
      setLoading(false);
    }
  }, [userId, assessmentId]);

  useEffect(() => {
    initializeAssessment();
  }, [initializeAssessment]);

  // Action: Explicit Start Assessment
  const handleStartAssessment = async () => {
    if (submitting) return;
    const currentGen = ++activeGenRef.current;
    setSubmitting(true);
    setError(null);

    try {
      const activeUserId = userId || sessionStorage.getItem('matchlens_user_id');
      const turnRes = await assessmentService.startAssessment(activeUserId, null, null);
      if (currentGen === activeGenRef.current) {
        setAssessmentData(turnRes);
        setAssessmentId(turnRes.assessment_id);
      }
    } catch (err) {
      if (currentGen === activeGenRef.current) {
        setError(err?.message || 'Failed to start scenario assessment.');
      }
    } finally {
      if (currentGen === activeGenRef.current) {
        setSubmitting(false);
      }
    }
  };

  // Action: Submit Response Turn
  const handleSubmitTurn = async (userResponseText) => {
    if (submitting || !assessmentData?.assessment_id) return;
    const currentGen = activeGenRef.current;
    setSubmitting(true);
    setError(null);

    try {
      const turnRes = await assessmentService.submitTurn(assessmentData.assessment_id, userResponseText);
      if (currentGen === activeGenRef.current) {
        setAssessmentData(turnRes);
      }
    } catch (err) {
      if (currentGen === activeGenRef.current) {
        setError(err?.message || 'Failed to submit scenario response. Please try again.');
      }
    } finally {
      if (currentGen === activeGenRef.current) {
        setSubmitting(false);
      }
    }
  };

  // Action: Correct Response
  const handleCorrectResponse = async (scenarioId, target, newValue) => {
    if (!assessmentData?.assessment_id) {
      return { success: false, error: 'No active assessment session.' };
    }
    const currentGen = activeGenRef.current;
    const key = `${scenarioId}_${target}`;
    setCorrectingState((prev) => ({ ...prev, [key]: true, [scenarioId]: true }));
    setError(null);

    try {
      const turnRes = await assessmentService.correctResponse(
        assessmentData.assessment_id,
        scenarioId,
        target,
        newValue
      );
      if (currentGen === activeGenRef.current) {
        setAssessmentData(turnRes);
      }
      return { success: true, data: turnRes };
    } catch (err) {
      const errMsg = err?.message || `Failed to correct ${target} for scenario ${scenarioId}.`;
      if (currentGen === activeGenRef.current) {
        setError(errMsg);
      }
      return { success: false, error: errMsg };
    } finally {
      if (currentGen === activeGenRef.current) {
        setCorrectingState((prev) => ({ ...prev, [key]: false, [scenarioId]: false }));
      }
    }
  };

  // Action: Status Recheck for ambiguous network failure
  const handleRecheckStatus = async () => {
    if (!assessmentData?.assessment_id) return;
    setRechecking(true);
    setUncertainError(null);
    const activeUserId = userId || sessionStorage.getItem('matchlens_user_id');

    try {
      // Re-fetch assessment state from backend
      const stateRes = await assessmentService.getAssessmentState(assessmentData.assessment_id);
      let profile = null;
      try {
        profile = await profileService.getProfile(activeUserId);
      } catch {
        // Profile fetch failed
      }

      if (stateRes?.status === 'completed' || isAssessmentPersistedInProfile(profile, assessmentData)) {
        setAssessmentData({
          ...stateRes,
          status: 'completed',
          current_stage: 'completed',
        });
        setError(null);
      } else {
        setAssessmentData(stateRes);
        setUncertainError('Backend state rechecked, but assessment is not confirmed yet. Please try confirming again.');
      }
    } catch {
      setUncertainError('Failed to verify backend status. Please try rechecking again.');
    } finally {
      setRechecking(false);
    }
  };

  // Action: Confirm Assessment
  const handleConfirmAssessment = async () => {
    if (confirming || !assessmentData?.assessment_id) return;
    const currentGen = activeGenRef.current;
    setConfirming(true);
    setError(null);
    setUncertainError(null);

    const activeUserId = userId || sessionStorage.getItem('matchlens_user_id');

    try {
      // POST /api/v1/assessment/{assessment_id}/confirm
      const confirmRes = await assessmentService.confirmAssessment(assessmentData.assessment_id);

      if (currentGen !== activeGenRef.current) return;

      // Authoritative verification: inspect actual confirmed profile or re-fetch profile
      let profile = (confirmRes && confirmRes.user_id === activeUserId && Array.isArray(confirmRes.scenario_responses))
        ? confirmRes
        : null;

      if (!profile) {
        try {
          profile = await profileService.getProfile(activeUserId);
        } catch {
          // Profile check failed
        }
      }

      if (isAssessmentPersistedInProfile(profile, assessmentData)) {
        setAssessmentData((prev) => ({
          ...prev,
          status: 'completed',
          current_stage: 'completed',
        }));
        setError(null);
      } else {
        setUncertainError(
          'Confirmation POST succeeded, but persisted scenario responses for this assessment could not be verified in your profile. Please recheck status.'
        );
      }
    } catch {
      if (currentGen !== activeGenRef.current) return;

      // Ambiguous error recovery check
      try {
        const profile = await profileService.getProfile(activeUserId);
        if (isAssessmentPersistedInProfile(profile, assessmentData)) {
          setAssessmentData((prev) => ({
            ...prev,
            status: 'completed',
            current_stage: 'completed',
          }));
          setError(null);
          return;
        }
      } catch {
        // Check failed
      }

      setUncertainError('A network or server error occurred during confirmation. Recheck status to verify.');
    } finally {
      if (currentGen === activeGenRef.current) {
        setConfirming(false);
      }
    }
  };

  // Render Loading State
  if (loading) {
    return (
      <div className="max-w-3xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-16">
        <div className="w-12 h-12 border-4 border-[#F2C0B6] border-t-[#E07A5F] rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-[#5C627A]">Loading scenario assessment...</p>
      </div>
    );
  }

  // Render Missing Confirmed Profile Guard
  if (!hasConfirmedProfile && !profileCheckFailed) {
    return (
      <div className="max-w-xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12">
        <Card className="p-8 text-center w-full shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center mx-auto mb-4">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <Badge variant="rose" className="mb-3">
            Confirmed Profile Required
          </Badge>
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">Complete Profile Review First</h2>
          <p className="text-sm text-[#5C627A] mb-6 leading-relaxed">
            Scenario assessment evaluates relationship choices for reciprocal matching. You must complete conversational onboarding and explicitly confirm your profile traits first.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-3">
            <Link to="/profile/review">
              <Button variant="primary" icon={ArrowRight}>
                Go to Profile Review
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Render Expired Session or Startup Error
  if (error && !assessmentData) {
    return (
      <div className="max-w-xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12">
        <Card className="p-8 text-center w-full shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-[#FAF6F0] border border-[#E8E3DC] text-[#E07A5F] flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">
            {restorationFailed ? 'Assessment Restoration Failure' : 'Assessment Session Notice'}
          </h2>
          <p className="text-sm text-[#5C627A] mb-6 leading-relaxed">{error}</p>
          <div className="flex flex-col sm:flex-row justify-center gap-3">
            {restorationFailed && (
              <Button
                variant="primary"
                icon={RefreshCw}
                onClick={initializeAssessment}
                disabled={loading}
              >
                Retry Restoration
              </Button>
            )}
            <Button
              variant={restorationFailed ? 'secondary' : 'primary'}
              icon={restorationFailed ? undefined : RefreshCw}
              onClick={handleStartAssessment}
              disabled={submitting}
            >
              {submitting ? 'Starting New Assessment...' : 'Start New Assessment'}
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Render Ready to Start State (no active assessment session created yet)
  if (!assessmentData) {
    return (
      <div className="max-w-2xl mx-auto w-full py-8 px-4 sm:px-6">
        <AssessmentHeader status="active" currentStage="start" userId={userId} />

        <Card className="p-8 md:p-10 text-center border-[#E8E3DC] shadow-sm">
          <div className="w-16 h-16 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center mx-auto mb-6">
            <Layers className="w-8 h-8" />
          </div>

          <h2 className="text-2xl font-bold text-[#2B2D42] mb-3 tracking-tight">
            Ready to Begin Assessment
          </h2>

          <p className="text-sm text-[#5C627A] max-w-md mx-auto mb-8 leading-relaxed">
            You will evaluate 3 core relationship decision scenarios. For each scenario, you will answer from two perspectives: your own behavior and your ideal partner.
          </p>

          <Button
            variant="primary"
            icon={ArrowRight}
            onClick={handleStartAssessment}
            disabled={submitting}
            className="py-3.5 px-8 shadow-md text-base"
          >
            {submitting ? 'Starting Assessment...' : 'Start Assessment'}
          </Button>
        </Card>
      </div>
    );
  }

  // Authoritative status & stage fields
  const status = assessmentData.status;
  const currentStage = assessmentData.current_stage;
  const isCompleted = status === 'completed' || currentStage === 'completed';
  const isReview = status === 'ready_for_review' || currentStage === 'review';

  return (
    <div className="max-w-3xl mx-auto w-full py-8 px-4 sm:px-6">
      <AssessmentHeader status={status} currentStage={currentStage} userId={userId} />

      {/* Persistent Error Banner */}
      {error && (
        <div className="mb-6 p-4 bg-[#FDF0ED] border border-[#F2C0B6] rounded-xl text-xs text-[#E07A5F] flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {uncertainError && (
        <div className="mb-6 p-4 bg-[#FAF6F0] border border-[#E8E3DC] rounded-xl text-xs text-[#5C627A] flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-[#E07A5F] shrink-0" />
            <span>{uncertainError}</span>
          </div>
          <Button variant="secondary" size="sm" icon={RefreshCw} onClick={handleRecheckStatus} disabled={rechecking}>
            {rechecking ? 'Checking...' : 'Recheck Status'}
          </Button>
        </div>
      )}

      {/* Progress Bar (Visible in active & review stages) */}
      {!isCompleted && (
        <ScenarioProgress progress={assessmentData.progress} currentStage={currentStage} />
      )}

      {/* Completed State View */}
      {isCompleted ? (
        <AssessmentCompletion onNavigateToMatches={() => navigate('/matches')} />
      ) : isReview ? (
        /* Review Screen */
        <ScenarioReview
          summaryData={assessmentData.summary_data || {}}
          selectedScenarioIds={assessmentData.selected_scenario_ids || []}
          confirming={confirming}
          onConfirmAssessment={handleConfirmAssessment}
          onCorrectResponse={handleCorrectResponse}
          correctingState={correctingState}
          isAlreadyCompleted={isCompleted}
          onNavigateToMatches={() => navigate('/matches')}
        />
      ) : (
        /* Active Scenario Question Stage */
        <>
          <ScenarioCard
            scenarioDefinition={assessmentData.scenario_definition}
            currentStage={currentStage}
          />

          <ScenarioResponseForm
            allowedOptions={assessmentData.allowed_options || []}
            optionDescriptions={assessmentData.scenario_definition?.option_descriptions || {}}
            unresolvedClarification={assessmentData.unresolved_clarification}
            submitting={submitting}
            onSubmitTurn={handleSubmitTurn}
          />
        </>
      )}

      {/* Navigation Footer */}
      <div className="mt-8 pt-6 border-t border-[#E8E3DC] flex items-center justify-between">
        <Link to="/profile/review">
          <Button variant="ghost" icon={RotateCcw}>
            Profile Review
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default AssessmentPage;
