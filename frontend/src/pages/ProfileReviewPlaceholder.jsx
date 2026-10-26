import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight,
  RotateCcw,
  Sparkles,
  Shield,
  Heart,
  User,
  Sliders,
  RefreshCw,
  Info
} from 'lucide-react';
import { Card, Button, Badge } from '../components/ui';
import { useWorkflow } from '../context/WorkflowContext';
import interviewService from '../services/interviewService';
import profileService from '../services/profileService';

/**
 * Helper to convert snake_case keys or internal values to Title Case.
 */
const formatLabel = (key) => {
  if (!key) return '';
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

/**
 * Formats values into clean readable strings.
 * Distinguishes null/undefined (Not specified), boolean, array (empty vs non-empty), and string/number.
 */
const formatValue = (val) => {
  if (val === null || val === undefined) {
    return <span className="text-[#A0A4B8] italic">Not specified</span>;
  }
  if (typeof val === 'boolean') {
    return val ? (
      <Badge variant="success">Yes</Badge>
    ) : (
      <Badge variant="stone">No</Badge>
    );
  }
  if (Array.isArray(val)) {
    if (val.length === 0) {
      return <span className="text-[#A0A4B8] italic">Unrestricted / Open</span>;
    }
    return (
      <div className="flex flex-wrap gap-1.5 mt-1">
        {val.map((item, idx) => (
          <Badge key={idx} variant="rose">
            {formatLabel(String(item))}
          </Badge>
        ))}
      </div>
    );
  }
  return <span className="font-medium text-[#2B2D42]">{formatLabel(String(val))}</span>;
};

/**
 * Reusable Card container for Profile sections.
 */
export const ProfileSection = ({ title, icon: Icon, children, description }) => (
  <Card className="p-6 md:p-8 mb-6 transition-all duration-200 hover:border-[#F2C0B6]">
    <div className="flex items-start gap-4 mb-4">
      {Icon && (
        <div className="w-10 h-10 rounded-xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center shrink-0">
          <Icon className="w-5 h-5" />
        </div>
      )}
      <div>
        <h3 className="text-lg font-bold text-[#2B2D42] tracking-tight">{title}</h3>
        {description && <p className="text-xs text-[#5C627A] mt-0.5">{description}</p>}
      </div>
    </div>
    <div className="space-y-3.5 pt-2 border-t border-[#E8E3DC]/60">{children}</div>
  </Card>
);

/**
 * Single field row component with optional inline editing.
 */
export const ProfileField = ({ label, value, onSave, options, isBoolean, isArray, isNumber }) => {
  const [editing, setEditing] = useState(false);
  const [editVal, setEditVal] = useState('');

  const handleStartEdit = () => {
    if (isArray) {
      setEditVal(Array.isArray(value) ? value.join(', ') : '');
    } else if (isBoolean) {
      setEditVal(value ? 'true' : 'false');
    } else {
      setEditVal(value !== null && value !== undefined ? String(value) : '');
    }
    setEditing(true);
  };

  const handleSave = () => {
    if (!onSave) return;
    if (isBoolean) {
      onSave(editVal === 'true');
    } else if (isNumber) {
      const num = parseInt(editVal, 10);
      onSave(isNaN(num) ? null : num);
    } else if (isArray) {
      const arr = editVal.split(',').map((s) => s.trim()).filter(Boolean);
      onSave(arr);
    } else {
      onSave(editVal.trim() || null);
    }
    setEditing(false);
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between py-2 gap-2 border-b border-[#FAF6F0] last:border-0">
      <span className="text-xs font-semibold text-[#5C627A] uppercase tracking-wider">{label}</span>
      <div className="flex items-center gap-2">
        {editing ? (
          <div className="flex items-center gap-2 w-full sm:w-auto">
            {options ? (
              <select
                value={editVal}
                onChange={(e) => setEditVal(e.target.value)}
                className="text-xs p-1.5 border border-[#E8E3DC] rounded-lg bg-white focus:outline-none focus:border-[#E07A5F]"
              >
                <option value="">Not specified</option>
                {options.map((opt) => (
                  <option key={opt} value={opt}>{formatLabel(opt)}</option>
                ))}
              </select>
            ) : isBoolean ? (
              <select
                value={editVal}
                onChange={(e) => setEditVal(e.target.value)}
                className="text-xs p-1.5 border border-[#E8E3DC] rounded-lg bg-white focus:outline-none focus:border-[#E07A5F]"
              >
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            ) : (
              <input
                type={isNumber ? "number" : "text"}
                value={editVal}
                onChange={(e) => setEditVal(e.target.value)}
                className="text-xs p-1.5 border border-[#E8E3DC] rounded-lg bg-white focus:outline-none focus:border-[#E07A5F] w-48"
                placeholder={isArray ? "Comma separated values" : "Enter value"}
              />
            )}
            <button
              onClick={handleSave}
              className="text-xs px-2.5 py-1 bg-[#E07A5F] text-white font-semibold rounded-lg hover:bg-[#D0694E] transition-colors"
            >
              Done
            </button>
            <button
              onClick={() => setEditing(false)}
              className="text-xs px-2.5 py-1 bg-[#FAF6F0] text-[#5C627A] rounded-lg hover:bg-[#E8E3DC]"
            >
              Cancel
            </button>
          </div>
        ) : (
          <>
            <div className="text-sm text-[#2B2D42] text-left sm:text-right">{formatValue(value)}</div>
            {onSave && (
              <button
                onClick={handleStartEdit}
                className="text-xs text-[#E07A5F] hover:text-[#C85A3F] font-medium ml-2 px-2 py-0.5 rounded hover:bg-[#FDF0ED] transition-colors"
              >
                Edit
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
};

/**
 * Formats explicit preference lists.
 */
export const PreferenceList = ({ items }) => {
  if (items === null || items === undefined) {
    return <span className="text-[#A0A4B8] italic">Not specified</span>;
  }
  if (Array.isArray(items) && items.length === 0) {
    return <span className="text-[#A0A4B8] italic">Unrestricted / Open</span>;
  }
  if (Array.isArray(items)) {
    return (
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, idx) => (
          <Badge key={idx} variant="rose">
            {formatLabel(String(item))}
          </Badge>
        ))}
      </div>
    );
  }
  return <span className="font-medium text-[#2B2D42]">{formatLabel(String(items))}</span>;
};

/**
 * Header status badge & indicator using valid Badge variants (rose, stone, success, neutral).
 */
export const ReviewStatus = ({ status, isConfirmed }) => {
  if (isConfirmed) {
    return (
      <Badge variant="success" className="py-1 px-3 text-xs gap-1.5">
        <CheckCircle className="w-3.5 h-3.5" />
        Confirmed Profile
      </Badge>
    );
  }
  if (status === 'ready_for_review') {
    return (
      <Badge variant="rose" className="py-1 px-3 text-xs gap-1.5">
        <Sparkles className="w-3.5 h-3.5" />
        Ready for Review
      </Badge>
    );
  }
  if (status === 'awaiting_confirmation') {
    return (
      <Badge variant="rose" className="py-1 px-3 text-xs gap-1.5">
        <Clock className="w-3.5 h-3.5" />
        Awaiting Clarification
      </Badge>
    );
  }
  return (
    <Badge variant="stone" className="py-1 px-3 text-xs gap-1.5">
      <Clock className="w-3.5 h-3.5" />
      Interview In Progress
    </Badge>
  );
};

export const ProfileReviewPage = () => {
  const navigate = useNavigate();
  const { sessionId: contextSessionId, userId: contextUserId } = useWorkflow();

  const sessionId = contextSessionId || sessionStorage.getItem('matchlens_interview_session_id') || '';
  const userId = contextUserId || sessionStorage.getItem('matchlens_user_id') || '';

  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [rechecking, setRechecking] = useState(false);
  const [error, setError] = useState(null);
  const [uncertainError, setUncertainError] = useState(null);
  const [sessionState, setSessionState] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [isConfirmed, setIsConfirmed] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setUncertainError(null);

    try {
      let activeSession = null;

      // 1. Check interview state if sessionId exists
      if (sessionId) {
        try {
          activeSession = await interviewService.getInterviewState(sessionId);
          setSessionState(activeSession);
        } catch (err) {
          // Ignore 404 silently as session may have expired/been cleared
          if (err?.status !== 404 && err?.status !== 0) {
            console.warn('Error retrieving interview session:', err);
          }
        }
      }

      // 2. Check repository for an existing confirmed profile
      let confirmedProfile = null;
      let profileError = null;
      if (userId) {
        try {
          const res = await profileService.getProfile(userId);
          // Verify confirmed profile belongs to current userId
          if (res && (!res.user_id || res.user_id === userId)) {
            confirmedProfile = res;
          }
        } catch (err) {
          profileError = err;
          if (err?.status !== 404) {
            console.warn('Error retrieving confirmed profile:', err);
          }
        }
      }

      // Handle backend 500 or network status 0 errors during profile/session retrieval
      if (profileError && profileError.status >= 500) {
        setError('Server error while checking confirmed profile state. Please try again or recheck status.');
        return;
      }

      // 3. Evaluate state precedence with strict authoritative checks
      if (confirmedProfile) {
        // Authoritative persisted confirmed profile found
        setIsConfirmed(true);
        setProfileData(confirmedProfile);
      } else if (activeSession && activeSession.status === 'ready_for_review') {
        setIsConfirmed(false);
        setProfileData(activeSession.draft_profile || null);
      } else if (activeSession && activeSession.status === 'awaiting_confirmation') {
        setIsConfirmed(false);
        setProfileData(activeSession.draft_profile || null);
      } else if (activeSession && activeSession.status === 'active') {
        setSessionState(activeSession);
        setProfileData(activeSession.draft_profile || null);
        setIsConfirmed(false);
      } else if (activeSession && activeSession.status === 'completed') {
        // Interview reports completed, but confirmed profile could not be retrieved from repository
        setError('Interview completed, but confirmed profile record could not be loaded. Please recheck status.');
      } else {
        // Session missing, 404, or unhandled status
        setError('No active profile review or interview session found. Please start or continue an interview.');
      }
    } catch (err) {
      console.error('Failed to load profile review:', err);
      setError(err?.message || 'An error occurred while loading your profile data.');
    } finally {
      setLoading(false);
    }
  }, [sessionId, userId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Status recheck action after ambiguous confirmation error or failure
  const handleRecheckStatus = async () => {
    setRechecking(true);
    setUncertainError(null);
    try {
      if (userId) {
        const saved = await profileService.getProfile(userId);
        if (saved && (!saved.user_id || saved.user_id === userId)) {
          setProfileData(saved);
          setIsConfirmed(true);
          setError(null);
          return;
        }
      }
      setUncertainError('Profile persistence is not yet confirmed on the server. You can re-try confirmation.');
    } catch {
      setUncertainError('Failed to verify profile status. Please try rechecking again.');
    } finally {
      setRechecking(false);
    }
  };

  // Handler for explicit confirmation
  const handleConfirmProfile = async () => {
    if (confirming || !sessionId) return;
    setConfirming(true);
    setError(null);
    setUncertainError(null);

    try {
      // POST /api/v1/interview/{session_id}/confirm
      const response = await interviewService.confirmProfile(sessionId);

      // Re-verify authoritative persisted profile from profileService
      let persistedProfile = null;
      if (userId) {
        try {
          persistedProfile = await profileService.getProfile(userId);
        } catch {
          // Failure to verify persistence
        }
      }

      if (persistedProfile && (!persistedProfile.user_id || persistedProfile.user_id === userId)) {
        setProfileData(persistedProfile);
        setIsConfirmed(true);
      } else if (response && response.user_id === userId) {
        setProfileData(response);
        setIsConfirmed(true);
      } else {
        // Confirmation POST returned but persistence verification failed
        setUncertainError('Confirmation requested, but server persistence could not be verified. Please recheck status.');
      }
    } catch (err) {
      console.error('Profile confirmation error:', err);

      // Handle ambiguous failure (network failure status 0, 408, timeout, 5xx) by rechecking backend state
      const isAmbiguousError =
        err?.status === 0 ||
        err?.status === 408 ||
        err?.code === 'ECONNABORTED' ||
        err?.message?.includes('timeout') ||
        (err?.status && err.status >= 500);

      if (isAmbiguousError && userId) {
        try {
          const checkSaved = await profileService.getProfile(userId);
          if (checkSaved && (!checkSaved.user_id || checkSaved.user_id === userId)) {
            setProfileData(checkSaved);
            setIsConfirmed(true);
            setError(null);
            return;
          }
        } catch {
          // Recheck failed
        }
        setUncertainError('A network or server error occurred during confirmation. Recheck status to see if it succeeded.');
        return;
      }

      const detail = err?.message || 'Failed to confirm profile. Please try again.';
      setError(detail);
    } finally {
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-16">
        <div className="w-12 h-12 border-4 border-[#F2C0B6] border-t-[#E07A5F] rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-[#5C627A]">Loading draft profile review...</p>
      </div>
    );
  }

  // Session missing / expired state
  if (error && !profileData) {
    return (
      <div className="max-w-xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12">
        <Card className="p-8 text-center w-full">
          <div className="w-14 h-14 rounded-2xl bg-[#FAF6F0] border border-[#E8E3DC] text-[#E07A5F] flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">Interview Session Required</h2>
          <p className="text-sm text-[#5C627A] mb-6 leading-relaxed">{error}</p>
          <div className="flex flex-col sm:flex-row justify-center gap-3">
            <Button variant="secondary" icon={RefreshCw} onClick={loadData} disabled={rechecking}>
              Recheck Status
            </Button>
            <Link to="/interview">
              <Button variant="primary" icon={ArrowRight}>
                Go to Interview Onboarding
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Active interview in progress state (not ready for review yet)
  if (sessionState && sessionState.status === 'active' && !isConfirmed) {
    return (
      <div className="max-w-xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12">
        <Card className="p-8 text-center w-full">
          <div className="w-14 h-14 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center mx-auto mb-4">
            <Clock className="w-7 h-7" />
          </div>
          <Badge variant="rose" className="mb-3">
            Interview In Progress
          </Badge>
          <h2 className="text-xl font-bold text-[#2B2D42] mb-2">Interview Not Yet Completed</h2>
          <p className="text-sm text-[#5C627A] mb-6 leading-relaxed">
            Your conversational interview is currently in progress. Please complete the remaining questions to generate your review-ready draft profile.
          </p>
          <Link to="/interview">
            <Button variant="primary" icon={ArrowRight}>
              Continue Interview
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  const attributes = profileData?.attributes || {};
  const expectations = profileData?.expectations || {};
  const dealbreakers = profileData?.dealbreakers || {};

  const updateAttribute = (field, val) => {
    setProfileData((prev) => {
      const updated = {
        ...prev,
        attributes: {
          ...(prev?.attributes || {}),
          [field]: val,
        },
      };
      if (userId) {
        profileService.updateProfile(userId, updated).catch((err) => console.warn('Field auto-save failed:', err));
      }
      return updated;
    });
  };

  const updateExpectation = (field, val) => {
    setProfileData((prev) => {
      const updated = {
        ...prev,
        expectations: {
          ...(prev?.expectations || {}),
          [field]: val,
        },
      };
      if (userId) {
        profileService.updateProfile(userId, updated).catch((err) => console.warn('Field auto-save failed:', err));
      }
      return updated;
    });
  };

  const updateDealbreaker = (field, val) => {
    setProfileData((prev) => {
      const updated = {
        ...prev,
        dealbreakers: {
          ...(prev?.dealbreakers || {}),
          [field]: val,
        },
      };
      if (userId) {
        profileService.updateProfile(userId, updated).catch((err) => console.warn('Field auto-save failed:', err));
      }
      return updated;
    });
  };

  return (
    <div className="max-w-3xl mx-auto w-full py-8 px-4 sm:px-6">
      {/* Top Banner & Header */}
      <div className="mb-8 text-center sm:text-left flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center justify-center sm:justify-start gap-2.5 mb-2">
            <ReviewStatus status={sessionState?.status} isConfirmed={isConfirmed} />
            <span className="text-xs text-[#A0A4B8]">ID: {userId?.substring(0, 12)}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#2B2D42] tracking-tight">
            Profile Review & Confirmation
          </h1>
          <p className="text-sm text-[#5C627A] mt-1">
            {isConfirmed
              ? 'Your profile is finalized and saved in the MatchLens system.'
              : 'Please review your extracted traits and partner expectations before finalizing.'}
          </p>
        </div>

        {isConfirmed ? (
          <Button
            variant="primary"
            icon={ArrowRight}
            onClick={() => navigate('/assessment')}
            className="shrink-0"
          >
            Continue to Scenario Assessment
          </Button>
        ) : (
          <Button
            variant="primary"
            icon={CheckCircle}
            onClick={handleConfirmProfile}
            disabled={confirming || (sessionState?.status !== 'ready_for_review' && !profileData)}
            className="shrink-0 shadow-sm"
          >
            {confirming ? 'Confirming Profile...' : 'Confirm My Profile'}
          </Button>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-[#FDF0ED] border border-[#F2C0B6] rounded-xl text-xs text-[#E07A5F] flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="ghost" size="sm" icon={RefreshCw} onClick={handleRecheckStatus} disabled={rechecking}>
            Recheck
          </Button>
        </div>
      )}

      {uncertainError && (
        <div className="mb-6 p-4 bg-[#FAF6F0] border border-[#E8E3DC] rounded-xl text-xs text-[#5C627A] flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Info className="w-5 h-5 text-[#E07A5F] shrink-0" />
            <span>{uncertainError}</span>
          </div>
          <Button variant="secondary" size="sm" icon={RefreshCw} onClick={handleRecheckStatus} disabled={rechecking}>
            {rechecking ? 'Checking...' : 'Recheck Status'}
          </Button>
        </div>
      )}

      {/* Section 1: About You */}
      <ProfileSection
        title="About You"
        icon={User}
        description="Your self-reported personal characteristics and lifestyle habits"
      >
        <ProfileField label="Age" value={attributes.age} isNumber onSave={(v) => updateAttribute('age', v)} />
        <ProfileField label="Gender" value={attributes.gender} options={['man', 'woman', 'non-binary']} onSave={(v) => updateAttribute('gender', v)} />
        <ProfileField label="Relationship Intent" value={attributes.relationship_intent} options={['long_term', 'marriage', 'casual', 'friendship']} onSave={(v) => updateAttribute('relationship_intent', v)} />
        <ProfileField label="Core Values" value={attributes.core_values} isArray onSave={(v) => updateAttribute('core_values', v)} />
        <ProfileField label="Interests" value={attributes.interests} isArray onSave={(v) => updateAttribute('interests', v)} />
        <ProfileField label="Smoking" value={attributes.smoking} options={['never', 'socially', 'regularly']} onSave={(v) => updateAttribute('smoking', v)} />
        <ProfileField label="Drinking" value={attributes.drinking} options={['never', 'socially', 'regularly']} onSave={(v) => updateAttribute('drinking', v)} />
        <ProfileField label="Exercise" value={attributes.exercise} options={['daily', 'weekly', 'rarely', 'never']} onSave={(v) => updateAttribute('exercise', v)} />
        <ProfileField label="Has Children" value={attributes.has_children} isBoolean onSave={(v) => updateAttribute('has_children', v)} />
        <ProfileField label="Wants Children" value={attributes.wants_children} options={['yes', 'no', 'open', 'maybe']} onSave={(v) => updateAttribute('wants_children', v)} />
        <ProfileField label="Communication Style" value={attributes.communication_style} options={['direct', 'gentle', 'expressive', 'analytical']} onSave={(v) => updateAttribute('communication_style', v)} />
        <ProfileField label="Conflict Resolution" value={attributes.conflict_resolution} options={['discuss_immediately', 'cool_down_first', 'written_first']} onSave={(v) => updateAttribute('conflict_resolution', v)} />
        <ProfileField label="Contact Frequency" value={attributes.contact_frequency} options={['frequent', 'daily_check_in', 'as_needed']} onSave={(v) => updateAttribute('contact_frequency', v)} />
      </ProfileSection>

      {/* Section 2: Your Ideal Partner */}
      <ProfileSection
        title="Your Ideal Partner"
        icon={Heart}
        description="Independently captured expectations for a prospective partner"
      >
        <ProfileField label="Min Age Preference" value={expectations.min_age} isNumber onSave={(v) => updateExpectation('min_age', v)} />
        <ProfileField label="Max Age Preference" value={expectations.max_age} isNumber onSave={(v) => updateExpectation('max_age', v)} />
        <ProfileField label="Acceptable Genders" value={expectations.acceptable_genders} isArray onSave={(v) => updateExpectation('acceptable_genders', v)} />
        <ProfileField label="Desired Intentions" value={expectations.desired_intentions} isArray onSave={(v) => updateExpectation('desired_intentions', v)} />
        <ProfileField label="Desired Core Values" value={expectations.desired_values} isArray onSave={(v) => updateExpectation('desired_values', v)} />
        <ProfileField label="Acceptable Smoking" value={expectations.acceptable_smoking} isArray onSave={(v) => updateExpectation('acceptable_smoking', v)} />
        <ProfileField label="Acceptable Drinking" value={expectations.acceptable_drinking} isArray onSave={(v) => updateExpectation('acceptable_drinking', v)} />
        <ProfileField label="Desired Children Views" value={expectations.desired_wants_children} isArray onSave={(v) => updateExpectation('desired_wants_children', v)} />
        <ProfileField label="Communication Expectations" value={expectations.desired_communication_styles} isArray onSave={(v) => updateExpectation('desired_communication_styles', v)} />
        <ProfileField label="Conflict Resolution Preference" value={expectations.desired_conflict_resolutions} isArray onSave={(v) => updateExpectation('desired_conflict_resolutions', v)} />
      </ProfileSection>

      {/* Section 3: Dealbreakers */}
      <ProfileSection
        title="Dealbreakers & Mandatory Rules"
        icon={Shield}
        description="Strict eligibility constraints used for match filtering"
      >
        <ProfileField label="Strict Intention Match Required" value={dealbreakers.strict_intention_match} isBoolean onSave={(v) => updateDealbreaker('strict_intention_match', v)} />
        <ProfileField label="Strict Age Range Required" value={dealbreakers.strict_age_range} isBoolean onSave={(v) => updateDealbreaker('strict_age_range', v)} />
        <ProfileField label="Strict Gender Match Required" value={dealbreakers.strict_gender_match} isBoolean onSave={(v) => updateDealbreaker('strict_gender_match', v)} />
        <ProfileField label="Smoking Dealbreaker" value={dealbreakers.smoking_dealbreaker} isBoolean onSave={(v) => updateDealbreaker('smoking_dealbreaker', v)} />
        <ProfileField label="Children Dealbreaker" value={dealbreakers.children_dealbreaker} isBoolean onSave={(v) => updateDealbreaker('children_dealbreaker', v)} />
      </ProfileSection>

      {/* Section 4: Profile Review Status */}
      <ProfileSection
        title="Review Status"
        icon={Sliders}
        description="Data completeness according to the backend match engine"
      >
        <div className="p-4 bg-[#FAF6F0] rounded-xl border border-[#E8E3DC] text-xs text-[#5C627A] space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-[#2B2D42]">Confirmation Status:</span>
            <span className="font-medium">{isConfirmed ? 'Confirmed & Saved' : 'Draft Ready for Review'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-semibold text-[#2B2D42]">Session Status:</span>
            <span className="font-medium">{sessionState?.status || (isConfirmed ? 'completed' : 'unknown')}</span>
          </div>
        </div>
      </ProfileSection>

      {/* Editing Tip Notice */}
      <div className="mt-8 p-6 bg-[#FAF6F0] rounded-2xl border border-[#E8E3DC] text-center">
        <h4 className="text-sm font-bold text-[#2B2D42] mb-1">Direct Field Editing</h4>
        <p className="text-xs text-[#5C627A] max-w-lg mx-auto mb-2 leading-relaxed">
          Click <span className="font-semibold text-[#E07A5F]">Edit</span> next to any field above to modify your traits or preferences directly without making any AI calls!
        </p>
      </div>

      {/* Bottom CTA Action Bar */}
      <div className="mt-8 pt-6 border-t border-[#E8E3DC] flex flex-col sm:flex-row items-center justify-between gap-4">
        <Link to="/">
          <Button variant="ghost" icon={RotateCcw}>
            Welcome Page
          </Button>
        </Link>

        {isConfirmed ? (
          <Button
            variant="primary"
            icon={ArrowRight}
            onClick={() => navigate('/assessment')}
            className="w-full sm:w-auto"
          >
            Continue to Scenario Assessment
          </Button>
        ) : (
          <Button
            variant="primary"
            icon={CheckCircle}
            onClick={handleConfirmProfile}
            disabled={confirming || sessionState?.status !== 'ready_for_review'}
            className="w-full sm:w-auto shadow-md"
          >
            {confirming ? 'Confirming Profile...' : 'Confirm My Profile'}
          </Button>
        )}
      </div>
    </div>
  );
};

export default ProfileReviewPage;
