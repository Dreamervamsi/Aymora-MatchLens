import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { WorkflowProvider } from '../context/WorkflowContext';
import ProfileReviewPage from '../pages/ProfileReviewPlaceholder';
import interviewService from '../services/interviewService';
import profileService from '../services/profileService';
import { ApiError } from '../services/apiClient';

vi.mock('../services/interviewService', () => ({
  interviewService: {
    getInterviewState: vi.fn(),
    confirmProfile: vi.fn(),
  },
  default: {
    getInterviewState: vi.fn(),
    confirmProfile: vi.fn(),
  },
}));

vi.mock('../services/profileService', () => ({
  profileService: {
    getProfile: vi.fn(),
  },
  default: {
    getProfile: vi.fn(),
  },
}));

const mockDraftProfile = {
  user_id: 'test_user_123',
  attributes: {
    age: 28,
    gender: 'woman',
    relationship_intent: 'long_term',
    core_values: ['honesty', 'family'],
    interests: ['hiking', 'reading'],
    smoking: 'never',
    drinking: 'socially',
    exercise: 'weekly',
    has_children: false,
    wants_children: 'yes',
    communication_style: 'direct',
    conflict_resolution: 'discuss_immediately',
    contact_frequency: 'daily_check_in',
  },
  expectations: {
    min_age: 26,
    max_age: 35,
    acceptable_genders: ['man'],
    desired_intentions: ['long_term'],
    desired_values: ['honesty', 'kindness'],
    acceptable_smoking: ['never'],
    acceptable_drinking: ['never', 'socially'],
    desired_wants_children: ['yes', 'open'],
    desired_communication_styles: ['direct', 'gentle'],
    desired_conflict_resolutions: ['discuss_immediately'],
  },
  dealbreakers: {
    strict_intention_match: true,
    strict_age_range: true,
    strict_gender_match: true,
    smoking_dealbreaker: true,
    children_dealbreaker: false,
    blocked_user_ids: [],
  },
};

const renderWithProviders = (ui) => {
  return render(
    <WorkflowProvider>
      <BrowserRouter>{ui}</BrowserRouter>
    </WorkflowProvider>
  );
};

describe('ProfileReviewPage Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    sessionStorage.clear();
  });

  it('1. loads a review-ready draft profile when active session is in ready_for_review status', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_review_123');
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_review_123',
      user_id: 'test_user_123',
      status: 'ready_for_review',
      draft_profile: mockDraftProfile,
    });
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      expect(interviewService.getInterviewState).toHaveBeenCalledWith('sess_review_123');
    });

    await waitFor(() => {
      expect(screen.getByText('Ready for Review')).toBeInTheDocument();
      expect(screen.getAllByRole('button', { name: 'Confirm My Profile' })[0]).toBeInTheDocument();
    });
  });

  it('2. renders self-attributes, partner expectations, and dealbreakers accurately with correct badges', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_review_123');
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_review_123',
      user_id: 'test_user_123',
      status: 'ready_for_review',
      draft_profile: mockDraftProfile,
    });
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      // Self-attributes
      expect(screen.getByText('About You')).toBeInTheDocument();
      expect(screen.getByText('28')).toBeInTheDocument();
      expect(screen.getAllByText('Woman')[0]).toBeInTheDocument();

      // Partner preferences
      expect(screen.getByText('Your Ideal Partner')).toBeInTheDocument();
      expect(screen.getByText('26 - 35 Years Old')).toBeInTheDocument();

      // Dealbreakers
      expect(screen.getByText('Dealbreakers & Mandatory Rules')).toBeInTheDocument();
    });
  });

  it('3. distinguishes missing, empty, unknown, and unrestricted preference values', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_partial');
    sessionStorage.setItem('matchlens_user_id', 'test_user_partial');

    const partialProfile = {
      ...mockDraftProfile,
      attributes: {
        ...mockDraftProfile.attributes,
        smoking: null, // missing -> Not specified
        has_children: false, // boolean false -> No
      },
      expectations: {
        ...mockDraftProfile.expectations,
        acceptable_smoking: [], // empty array -> Unrestricted / Open
      },
    };

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_partial',
      user_id: 'test_user_partial',
      status: 'ready_for_review',
      draft_profile: partialProfile,
    });
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Not specified')).toBeInTheDocument();
      expect(screen.getByText('Unrestricted / Open')).toBeInTheDocument();
      expect(screen.getAllByText('No')[0]).toBeInTheDocument();
    });
  });

  it('4. displays limitation warning for profile editing', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_review_123');
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_review_123',
      status: 'ready_for_review',
      draft_profile: mockDraftProfile,
    });
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Need to modify profile details?')).toBeInTheDocument();
      expect(
        screen.getByText(/Direct field editing during profile review is currently unsupported/i)
      ).toBeInTheDocument();
    });
  });

  it('5. handles confirmation POST success and verifies persistence', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_confirm_test');
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_confirm_test',
      status: 'ready_for_review',
      draft_profile: mockDraftProfile,
    });
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    interviewService.confirmProfile.mockResolvedValueOnce({
      ...mockDraftProfile,
    });

    profileService.getProfile.mockResolvedValueOnce({
      ...mockDraftProfile,
    });

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: 'Confirm My Profile' })[0]).toBeInTheDocument();
    });

    const confirmBtn = screen.getAllByRole('button', { name: 'Confirm My Profile' })[0];
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(interviewService.confirmProfile).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Confirmed Profile')).toBeInTheDocument();
      expect(screen.getAllByRole('button', { name: 'Continue to Scenario Assessment' })[0]).toBeInTheDocument();
    });
  });

  it('6. handles confirmation POST success but persistence verification failure safely', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_confirm_test');
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_confirm_test',
      status: 'ready_for_review',
      draft_profile: mockDraftProfile,
    });
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    interviewService.confirmProfile.mockResolvedValueOnce(null);
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: 'Confirm My Profile' })[0]).toBeInTheDocument();
    });

    const confirmBtn = screen.getAllByRole('button', { name: 'Confirm My Profile' })[0];
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(/Confirmation requested, but server persistence could not be verified/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Recheck Status' })).toBeInTheDocument();
    });
  });

  it('7. handles interview completed status when confirmed profile is missing', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_completed');
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_completed',
      status: 'completed',
      draft_profile: mockDraftProfile,
    });
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/Interview completed, but confirmed profile record could not be loaded/i)).toBeInTheDocument();
    });
  });

  it('8. ignores confirmed profile belonging to a different user ID', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_wrong_user');
    sessionStorage.setItem('matchlens_user_id', 'user_a');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_wrong_user',
      status: 'ready_for_review',
      draft_profile: { ...mockDraftProfile, user_id: 'user_a' },
    });
    // getProfile returns profile for user_b instead of user_a
    profileService.getProfile.mockResolvedValueOnce({ ...mockDraftProfile, user_id: 'user_b' });

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      // Should treat profile as unconfirmed for user_a and show ready_for_review
      expect(screen.getByText('Ready for Review')).toBeInTheDocument();
    });
  });

  it('9. handles network failure / ambiguous timeout after confirmation by rechecking backend state', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'timeout_sess');
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'timeout_sess',
      status: 'ready_for_review',
      draft_profile: mockDraftProfile,
    });
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    interviewService.confirmProfile.mockRejectedValueOnce(new ApiError('Request timed out', 408));
    profileService.getProfile.mockResolvedValueOnce({ ...mockDraftProfile, user_id: 'test_user_123' });

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: 'Confirm My Profile' })[0]).toBeInTheDocument();
    });

    const confirmBtn = screen.getAllByRole('button', { name: 'Confirm My Profile' })[0];
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(profileService.getProfile).toHaveBeenCalledWith('test_user_123');
      expect(screen.getByText('Confirmed Profile')).toBeInTheDocument();
    });
  });

  it('10. handles backend 500 error during initial profile load accurately', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_500');
    sessionStorage.setItem('matchlens_user_id', 'test_user_500');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_500',
      status: 'ready_for_review',
      draft_profile: mockDraftProfile,
    });
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Internal Server Error', 500));

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/Server error while checking confirmed profile state/i)).toBeInTheDocument();
    });
  });

  it('11. navigates to /assessment only after explicit confirmation or when profile is already confirmed', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_confirmed');

    profileService.getProfile.mockResolvedValueOnce({ ...mockDraftProfile, user_id: 'test_user_confirmed' });

    renderWithProviders(<ProfileReviewPage />);

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: 'Continue to Scenario Assessment' })[0]).toBeInTheDocument();
    });
  });
});
