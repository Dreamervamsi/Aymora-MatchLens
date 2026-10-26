import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  AlertCircle,
  RefreshCw,
  ArrowRight,
  RotateCcw,
  Inbox,
  CheckCircle,
} from 'lucide-react';
import { Card, Button, Badge } from '../components/ui';
import { useWorkflow } from '../context/WorkflowContext';
import matchService from '../services/matchService';
import profileService from '../services/profileService';
import assessmentService from '../services/assessmentService';
import { isAssessmentPersistedInProfile } from '../utils/assessmentUtils';
import MatchCard from '../components/matches/MatchCard';

/**
 * Real Reciprocal Matches Page replacing MatchesPlaceholder.
 */
export const MatchesPage = () => {
  const { userId, assessmentId } = useWorkflow();

  // Guard & Loading States
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [guardState, setGuardState] = useState({
    missingUserId: false,
    missingProfile: false,
    incompleteAssessment: false,
  });

  // Data States
  const [matches, setMatches] = useState([]);
  const [expandedIndex, setExpandedIndex] = useState(null);

  // Generation counter to protect against stale asynchronous responses
  const activeGenRef = useRef(0);

  const fetchMatches = useCallback(async () => {
    const currentGen = ++activeGenRef.current;
    setLoading(true);
    setError(null);
    setGuardState({
      missingUserId: false,
      missingProfile: false,
      incompleteAssessment: false,
    });

    const activeUserId = userId || sessionStorage.getItem('matchlens_user_id');

    // Guard 1: Missing User ID
    if (!activeUserId) {
      if (currentGen === activeGenRef.current) {
        setGuardState({ missingUserId: true, missingProfile: false, incompleteAssessment: false });
        setLoading(false);
      }
      return;
    }

    // Guard 2: Verify Confirmed Profile Exists
    let profile = null;
    try {
      profile = await profileService.getProfile(activeUserId);
      if (currentGen !== activeGenRef.current) return;

      if (!profile || (profile.user_id && profile.user_id !== activeUserId)) {
        setGuardState({ missingUserId: false, missingProfile: true, incompleteAssessment: false });
        setLoading(false);
        return;
      }
    } catch (err) {
      if (currentGen !== activeGenRef.current) return;
      if (err?.status === 404 || err?.message?.includes('404') || err?.message?.toLowerCase().includes('not found')) {
        setGuardState({ missingUserId: false, missingProfile: true, incompleteAssessment: false });
        setLoading(false);
        return;
      }
      setError(err?.message || 'Failed to verify user profile. Please try again.');
      setLoading(false);
      return;
    }

    // Guard 3: Verify Assessment Completion via Authoritative State
    let isCompleted = false;
    let checkedActiveSession = false;

    // Step 3a: If active assessment ID exists, check backend assessment status
    const activeAssessmentId = assessmentId || sessionStorage.getItem('matchlens_assessment_id');
    if (activeAssessmentId) {
      try {
        const assessmentState = await assessmentService.getAssessmentState(activeAssessmentId);
        if (currentGen !== activeGenRef.current) return;

        // Verify session belongs to active user
        if (assessmentState && (!assessmentState.user_id || assessmentState.user_id === activeUserId)) {
          checkedActiveSession = true;
          if (assessmentState.status === 'completed' || assessmentState.current_stage === 'completed') {
            isCompleted = true;
          } else {
            // Status is active, ready_for_review, etc. -> Incomplete assessment
            isCompleted = false;
          }
        }
      } catch {
        // Ignored; fall back to checking persisted profile responses
      }
    }

    // Step 3b: Fall back to checking profile persistence if no active session was checked
    if (!checkedActiveSession) {
      isCompleted = isAssessmentPersistedInProfile(profile);
    }

    if (!isCompleted) {
      if (currentGen === activeGenRef.current) {
        setGuardState({ missingUserId: false, missingProfile: false, incompleteAssessment: true });
        setLoading(false);
      }
      return;
    }

    // Prerequisites satisfied: Retrieve top matches (top_k=3)
    try {
      const response = await matchService.getMatches(activeUserId, 3);
      if (currentGen !== activeGenRef.current) return;

      const rawMatches = response?.top_matches || (Array.isArray(response) ? response : []);

      // Filter to backend-confirmed eligible matches only
      // Respect both is_eligible boolean and eligibility_status === 'eligible'
      const eligibleMatches = rawMatches.filter((m) => {
        if (!m) return false;
        if (m.is_eligible === false) return false;
        if (m.eligibility_status && m.eligibility_status !== 'eligible') return false;
        return true;
      });

      // Render max 3 eligible recommendations preserving backend rank order
      setMatches(eligibleMatches.slice(0, 3));
    } catch (err) {
      if (currentGen !== activeGenRef.current) return;
      setError(err?.message || 'Failed to calculate reciprocal matches. Please check network or backend server.');
    } finally {
      if (currentGen === activeGenRef.current) {
        setLoading(false);
      }
    }
  }, [userId, assessmentId]);

  useEffect(() => {
    fetchMatches();
  }, [fetchMatches]);

  const handleToggleExpand = (index) => {
    setExpandedIndex((prevIndex) => (prevIndex === index ? null : index));
  };

  // Render Skeleton / Loading State
  if (loading) {
    return (
      <div className="max-w-3xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-16 px-4">
        <div className="w-12 h-12 border-4 border-[#F2C0B6] border-t-[#E07A5F] rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-[#5C627A]">Calculating reciprocal compatibility matches...</p>
      </div>
    );
  }

  // Guard Render 1: Missing User ID
  if (guardState.missingUserId) {
    return (
      <div className="max-w-xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12 px-4">
        <Card className="p-8 text-center w-full shadow-xs">
          <div className="w-14 h-14 rounded-2xl bg-[#FAF6F0] border border-[#E8E3DC] text-[#E07A5F] flex items-center justify-center mx-auto mb-4">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <Badge variant="stone" className="mb-3">
            Onboarding Required
          </Badge>
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">No Active Session</h2>
          <p className="text-sm text-[#5C627A] mb-6 leading-relaxed">
            Please begin conversational onboarding to set up your profile preferences before viewing matches.
          </p>
          <Link to="/">
            <Button variant="primary" icon={ArrowRight}>
              Go to Welcome & Onboarding
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  // Guard Render 2: Missing Confirmed Profile
  if (guardState.missingProfile) {
    return (
      <div className="max-w-xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12 px-4">
        <Card className="p-8 text-center w-full shadow-xs">
          <div className="w-14 h-14 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center mx-auto mb-4">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <Badge variant="rose" className="mb-3">
            Confirmed Profile Required
          </Badge>
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">Complete Profile Review First</h2>
          <p className="text-sm text-[#5C627A] mb-6 leading-relaxed">
            Reciprocal matching requires a confirmed profile with structured relationship traits and partner expectations.
          </p>
          <Link to="/profile/review">
            <Button variant="primary" icon={ArrowRight}>
              Go to Profile Review
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  // Guard Render 3: Incomplete Scenario Assessment
  if (guardState.incompleteAssessment) {
    return (
      <div className="max-w-xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12 px-4">
        <Card className="p-8 text-center w-full shadow-xs">
          <div className="w-14 h-14 rounded-2xl bg-[#FAF6F0] border border-[#E8E3DC] text-[#3D5A80] flex items-center justify-center mx-auto mb-4">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <Badge variant="sky" className="mb-3">
            Scenario Assessment Required
          </Badge>
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">Complete Scenario Assessment</h2>
          <p className="text-sm text-[#5C627A] mb-6 leading-relaxed">
            To generate accurate reciprocal recommendations, you must complete the scenario assessment evaluating self-behavior and partner expectations.
          </p>
          <Link to="/assessment">
            <Button variant="primary" icon={ArrowRight}>
              Go to Scenario Assessment
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  // Network / Server Error State
  if (error) {
    return (
      <div className="max-w-xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12 px-4">
        <Card className="p-8 text-center w-full shadow-xs">
          <div className="w-14 h-14 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">Failed to Load Matches</h2>
          <p className="text-sm text-[#5C627A] mb-6 leading-relaxed">{error}</p>
          <Button variant="primary" icon={RefreshCw} onClick={fetchMatches}>
            Retry Request
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto w-full py-8 px-4 sm:px-6">
      {/* Page Header */}
      <div className="mb-8 text-center sm:text-left">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-2">
          <div>
            <div className="flex items-center justify-center sm:justify-start gap-2 mb-1">
              <h1 className="text-2xl sm:text-3xl font-bold text-[#2B2D42] tracking-tight">
                Your Reciprocal Matches
              </h1>
              <Badge variant="emerald" icon={CheckCircle}>
                Assessment Complete
              </Badge>
            </div>
            <p className="text-sm text-[#5C627A]">
              Recommendations evaluate mutual alignment considering both your preferences and candidates&apos; expectations.
            </p>
          </div>

          <Link to="/assessment">
            <Button variant="ghost" size="sm" icon={RotateCcw}>
              Assessment Review
            </Button>
          </Link>
        </div>
      </div>

      {/* Empty State: No eligible candidates returned */}
      {matches.length === 0 ? (
        <Card className="p-8 md:p-12 text-center border-[#E8E3DC] shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-[#FAF6F0] border border-[#E8E3DC] text-[#8D99AE] flex items-center justify-center mx-auto mb-6">
            <Inbox className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold text-[#2B2D42] mb-2">No Eligible Matches Found</h3>
          <p className="text-sm text-[#5C627A] max-w-md mx-auto mb-8 leading-relaxed">
            There are currently no candidates matching your strict dealbreakers and minimum evidence requirements. You can review your profile criteria to adjust expectations.
          </p>
          <Link to="/profile/review">
            <Button variant="primary" icon={ArrowRight}>
              Review Profile Criteria
            </Button>
          </Link>
        </Card>
      ) : (
        /* Render Up to 3 Ranked Recommendations */
        <div className="space-y-6">
          {matches.map((match, idx) => (
            <MatchCard
              key={match.user_b_id || idx}
              match={match}
              rank={idx + 1}
              isExpanded={expandedIndex === idx}
              onToggleExpand={() => handleToggleExpand(idx)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MatchesPage;
