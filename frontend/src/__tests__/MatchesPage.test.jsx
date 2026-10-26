import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { WorkflowProvider, useWorkflow } from '../context/WorkflowContext';
import { MatchesPage } from '../pages/MatchesPage';
import matchService from '../services/matchService';
import profileService from '../services/profileService';
import assessmentService from '../services/assessmentService';
import { ApiError } from '../services/apiClient';

vi.mock('../services/matchService', () => ({
  matchService: {
    getMatches: vi.fn(),
  },
  default: {
    getMatches: vi.fn(),
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

vi.mock('../services/assessmentService', () => ({
  assessmentService: {
    getAssessmentState: vi.fn(),
  },
  default: {
    getAssessmentState: vi.fn(),
  },
}));

const renderWithProviders = (initialUserId = 'alex_101') => {
  if (initialUserId) {
    sessionStorage.setItem('matchlens_user_id', initialUserId);
  } else {
    sessionStorage.removeItem('matchlens_user_id');
  }
  return render(
    <WorkflowProvider initialUserId={initialUserId}>
      <BrowserRouter>
        <MatchesPage />
      </BrowserRouter>
    </WorkflowProvider>
  );
};

// Fixture matching confirmed profile with completed scenario assessment
const mockConfirmedProfileWithAssessment = {
  user_id: 'alex_101',
  attributes: { age: 29, gender: 'man', relationship_intent: 'long_term' },
  expectations: { min_age: 24, max_age: 34 },
  scenario_responses: [
    {
      scenario_id: 'conflict_resolution_01',
      target_dimension: 'communication_preferences',
      normalized_preference: 'cool_down_first',
      expected_partner_preference: 'cool_down_first',
    },
    {
      scenario_id: 'social_energy_01',
      target_dimension: 'lifestyle_compatibility',
      normalized_preference: 'small_group_gathering',
      expected_partner_preference: 'small_group_gathering',
    },
  ],
};

// Realistic Backend Match Result Fixtures
const mockMatchTaylor = {
  user_a_id: 'alex_101',
  user_b_id: 'taylor_202',
  display_name: 'Taylor',
  eligibility_status: 'eligible',
  is_eligible: true,
  ineligibility_reasons: [],
  mutual_score: 87.5,
  directional_a_to_b: {
    evaluator_id: 'alex_101',
    candidate_id: 'taylor_202',
    directional_score: 90.0,
    total_active_weight: 1.0,
    evidence_coverage: 100.0,
    dimension_scores: {
      core_values: { dimension_name: 'core_values', score: 92.0, has_sufficient_data: true },
      relationship_intentions: { dimension_name: 'relationship_intentions', score: 100.0, has_sufficient_data: true },
      lifestyle_compatibility: { dimension_name: 'lifestyle_compatibility', score: 85.0, has_sufficient_data: true },
      communication_preferences: { dimension_name: 'communication_preferences', score: 80.0, has_sufficient_data: true },
      shared_interests: { dimension_name: 'shared_interests', score: 75.0, has_sufficient_data: true },
    },
  },
  directional_b_to_a: {
    evaluator_id: 'taylor_202',
    candidate_id: 'alex_101',
    directional_score: 85.0,
    total_active_weight: 1.0,
    evidence_coverage: 100.0,
    dimension_scores: {
      core_values: { dimension_name: 'core_values', score: 90.0, has_sufficient_data: true },
      relationship_intentions: { dimension_name: 'relationship_intentions', score: 100.0, has_sufficient_data: true },
      lifestyle_compatibility: { dimension_name: 'lifestyle_compatibility', score: 80.0, has_sufficient_data: true },
      communication_preferences: { dimension_name: 'communication_preferences', score: 80.0, has_sufficient_data: true },
      shared_interests: { dimension_name: 'shared_interests', score: 70.0, has_sufficient_data: true },
    },
  },
  evidence_coverage: 100.0,
  is_low_coverage: false,
  evidence_summary: {
    strengths: ['Shared commitment to honesty and family', 'Aligned cool-down conflict resolution style'],
    potential_differences: ['Slight variation in daily exercise routines'],
    scenario_highlights: ['Both prefer small group gatherings over large parties'],
    missing_data_warnings: [],
    structured_evidence: [],
  },
};

const mockMatchJordan = {
  user_a_id: 'alex_101',
  user_b_id: 'jordan_303',
  display_name: 'Jordan',
  eligibility_status: 'eligible',
  is_eligible: true,
  ineligibility_reasons: [],
  mutual_score: 72.0,
  directional_a_to_b: {
    evaluator_id: 'alex_101',
    candidate_id: 'jordan_303',
    directional_score: 75.0,
    total_active_weight: 1.0,
    evidence_coverage: 80.0,
    dimension_scores: {
      core_values: { dimension_name: 'core_values', score: 80.0, has_sufficient_data: true },
      relationship_intentions: { dimension_name: 'relationship_intentions', score: 100.0, has_sufficient_data: true },
      lifestyle_compatibility: { dimension_name: 'lifestyle_compatibility', score: 60.0, has_sufficient_data: true },
      communication_preferences: { dimension_name: 'communication_preferences', score: 50.0, has_sufficient_data: true },
      shared_interests: { dimension_name: 'shared_interests', score: null, has_sufficient_data: false },
    },
  },
  directional_b_to_a: {
    evaluator_id: 'jordan_303',
    candidate_id: 'alex_101',
    directional_score: 69.0,
    total_active_weight: 1.0,
    evidence_coverage: 80.0,
    dimension_scores: {
      core_values: { dimension_name: 'core_values', score: 75.0, has_sufficient_data: true },
      relationship_intentions: { dimension_name: 'relationship_intentions', score: 100.0, has_sufficient_data: true },
      lifestyle_compatibility: { dimension_name: 'lifestyle_compatibility', score: 60.0, has_sufficient_data: true },
      communication_preferences: { dimension_name: 'communication_preferences', score: 45.0, has_sufficient_data: true },
      shared_interests: { dimension_name: 'shared_interests', score: null, has_sufficient_data: false },
    },
  },
  evidence_coverage: 80.0,
  is_low_coverage: false,
  evidence_summary: {
    strengths: ['Aligned long-term intention'],
    potential_differences: ['Divergent conflict resolution approach'],
    scenario_highlights: [],
    missing_data_warnings: ['Insufficient data on shared interests'],
    structured_evidence: [],
  },
};

const mockMatchMorgan = {
  user_a_id: 'alex_101',
  user_b_id: 'morgan_505',
  display_name: 'Morgan',
  eligibility_status: 'eligible',
  is_eligible: true,
  ineligibility_reasons: [],
  mutual_score: 61.0,
  directional_a_to_b: {
    evaluator_id: 'alex_101',
    candidate_id: 'morgan_505',
    directional_score: 65.0,
    total_active_weight: 0.5,
    evidence_coverage: 40.0,
    dimension_scores: {},
  },
  directional_b_to_a: {
    evaluator_id: 'morgan_505',
    candidate_id: 'alex_101',
    directional_score: 57.0,
    total_active_weight: 0.5,
    evidence_coverage: 40.0,
    dimension_scores: {},
  },
  evidence_coverage: 40.0,
  is_low_coverage: true,
  evidence_summary: {
    strengths: [],
    potential_differences: [],
    scenario_highlights: [],
    missing_data_warnings: ['Missing core values, lifestyle, and communication data'],
    structured_evidence: [],
  },
};

const mockMatchesResponse = {
  requesting_user_id: 'alex_101',
  top_matches: [mockMatchTaylor, mockMatchJordan, mockMatchMorgan],
  ranking_metadata: {
    total_candidates: 4,
    eligible_candidates: 3,
    pending_information_candidates: 1,
    filtered_for_coverage: 0,
    returned_count: 3,
  },
};

// Helper component for test 16 context switching
const ContextSwitcher = ({ userId }) => {
  const { setUserId } = useWorkflow();
  return (
    <button onClick={() => setUserId(userId)}>
      Switch to {userId}
    </button>
  );
};

describe('MatchesPage Component — Phase 7.5 Reciprocal Match Discovery Suite', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    sessionStorage.clear();
    sessionStorage.setItem('matchlens_user_id', 'alex_101');
    profileService.getProfile.mockResolvedValue(mockConfirmedProfileWithAssessment);
  });

  it('1. Confirmed user with completed assessment sees returned matches', async () => {
    matchService.getMatches.mockResolvedValueOnce(mockMatchesResponse);

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('Your Reciprocal Matches')).toBeInTheDocument();
      expect(screen.getByText('Taylor')).toBeInTheDocument();
      expect(screen.getByText('Jordan')).toBeInTheDocument();
      expect(screen.getByText('Morgan')).toBeInTheDocument();
    });
  });

  it('2. Match API called with correct user ID and top_k=3', async () => {
    matchService.getMatches.mockResolvedValueOnce(mockMatchesResponse);

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(matchService.getMatches).toHaveBeenCalledTimes(1);
      expect(matchService.getMatches).toHaveBeenCalledWith('alex_101', 3);
    });
  });

  it('3. Backend returns three matches', async () => {
    matchService.getMatches.mockResolvedValueOnce(mockMatchesResponse);

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getAllByText(/#[1-3]/).length).toBe(3);
      expect(screen.getByText('#1')).toBeInTheDocument();
      expect(screen.getByText('#2')).toBeInTheDocument();
      expect(screen.getByText('#3')).toBeInTheDocument();
    });
  });

  it('4. Backend returns one match', async () => {
    matchService.getMatches.mockResolvedValueOnce({
      requesting_user_id: 'alex_101',
      top_matches: [mockMatchTaylor],
      ranking_metadata: { total_candidates: 4, returned_count: 1 },
    });

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('Taylor')).toBeInTheDocument();
      expect(screen.queryByText('Jordan')).not.toBeInTheDocument();
    });
  });

  it('5. Backend returns zero matches', async () => {
    matchService.getMatches.mockResolvedValueOnce({
      requesting_user_id: 'alex_101',
      top_matches: [],
      ranking_metadata: { total_candidates: 4, returned_count: 0 },
    });

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('No Eligible Matches Found')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Review Profile Criteria' })).toBeInTheDocument();
    });
  });

  it('6. Correct ordering based on backend ranking', async () => {
    matchService.getMatches.mockResolvedValueOnce(mockMatchesResponse);

    renderWithProviders('alex_101');

    await waitFor(() => {
      const rankBadges = screen.getAllByText(/#[1-3]/);
      expect(rankBadges[0]).toHaveTextContent('#1');
      expect(rankBadges[1]).toHaveTextContent('#2');
      expect(rankBadges[2]).toHaveTextContent('#3');
      expect(screen.getByText('Taylor')).toBeInTheDocument();
    });
  });

  it('7. Reciprocal and directional scores render correctly', async () => {
    matchService.getMatches.mockResolvedValueOnce({
      requesting_user_id: 'alex_101',
      top_matches: [mockMatchTaylor],
    });

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getAllByText('88%').length).toBeGreaterThan(0);
      expect(screen.getByText('90%')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
    });
  });

  it('8. Evidence coverage is separate from compatibility', async () => {
    matchService.getMatches.mockResolvedValueOnce({
      requesting_user_id: 'alex_101',
      top_matches: [mockMatchTaylor],
    });

    renderWithProviders('alex_101');

    const detailBtn = await screen.findByRole('button', { name: /View Compatibility Details for Taylor/i });
    fireEvent.click(detailBtn);

    await waitFor(() => {
      expect(screen.getByText(/Evidence coverage shows how much information was available/i)).toBeInTheDocument();
      expect(screen.getByText('High Coverage')).toBeInTheDocument();
    });
  });

  it('9. Missing optional fields do not crash the page', async () => {
    const minimalMatch = {
      user_a_id: 'alex_101',
      user_b_id: 'minimal_candidate',
      mutual_score: 50.0,
      directional_a_to_b: null,
      directional_b_to_a: null,
      evidence_coverage: null, // Null coverage
      is_low_coverage: false,
      evidence_summary: null,
    };

    matchService.getMatches.mockResolvedValueOnce({
      requesting_user_id: 'alex_101',
      top_matches: [minimalMatch],
    });

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('Candidate 1')).toBeInTheDocument();
      expect(screen.getAllByText('50%').length).toBeGreaterThan(0);
    });

    const detailBtn = screen.getByRole('button', { name: /View Compatibility Details for Candidate 1/i });
    fireEvent.click(detailBtn);

    await waitFor(() => {
      expect(screen.getByText('Evidence unavailable')).toBeInTheDocument();
      expect(screen.getAllByText(/Not enough evidence/i).length).toBeGreaterThan(0);
    });
  });

  it('10. Match details expand and collapse', async () => {
    matchService.getMatches.mockResolvedValueOnce({
      requesting_user_id: 'alex_101',
      top_matches: [mockMatchTaylor],
    });

    renderWithProviders('alex_101');

    const detailBtn = await screen.findByRole('button', { name: /View Compatibility Details for Taylor/i });

    // Expand
    fireEvent.click(detailBtn);
    await waitFor(() => {
      expect(screen.getByText('Compatibility Dimensions')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Hide Compatibility Details for Taylor/i })).toBeInTheDocument();
    });

    // Collapse
    const hideBtn = screen.getByRole('button', { name: /Hide Compatibility Details for Taylor/i });
    fireEvent.click(hideBtn);
    await waitFor(() => {
      expect(screen.queryByText('Compatibility Dimensions')).not.toBeInTheDocument();
    });
  });

  it('11. Missing user ID prevents API request', async () => {
    sessionStorage.removeItem('matchlens_user_id');

    renderWithProviders(null);

    await waitFor(() => {
      expect(screen.getByText('No Active Session')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Go to Welcome & Onboarding' })).toBeInTheDocument();
    });

    expect(matchService.getMatches).not.toHaveBeenCalled();
  });

  it('12. Missing confirmed profile redirects or displays recovery', async () => {
    profileService.getProfile.mockRejectedValueOnce(new ApiError('Not found', 404));

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('Complete Profile Review First')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Go to Profile Review' })).toBeInTheDocument();
    });

    expect(matchService.getMatches).not.toHaveBeenCalled();
  });

  it('13. Incomplete assessment prevents results', async () => {
    profileService.getProfile.mockResolvedValueOnce({
      user_id: 'alex_101',
      attributes: { age: 29 },
      scenario_responses: [], // Empty assessment
    });

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('Complete Scenario Assessment')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Go to Scenario Assessment' })).toBeInTheDocument();
    });

    expect(matchService.getMatches).not.toHaveBeenCalled();
  });

  it('14. API failure displays retry', async () => {
    matchService.getMatches.mockRejectedValueOnce(new ApiError('Internal Server Error', 500));

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('Failed to Load Matches')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Retry Request' })).toBeInTheDocument();
    });
  });

  it('15. Retry performs a new request', async () => {
    matchService.getMatches.mockRejectedValueOnce(new ApiError('Internal Server Error', 500));

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Retry Request' })).toBeInTheDocument();
    });

    matchService.getMatches.mockResolvedValueOnce(mockMatchesResponse);
    fireEvent.click(screen.getByRole('button', { name: 'Retry Request' }));

    await waitFor(() => {
      expect(matchService.getMatches).toHaveBeenCalledTimes(2);
      expect(screen.getByText('Taylor')).toBeInTheDocument();
    });
  });

  it('16. Stale requests do not overwrite results after workflow context user change', async () => {
    let oldUserResolve;

    profileService.getProfile.mockImplementation((user) => {
      return Promise.resolve({
        ...mockConfirmedProfileWithAssessment,
        user_id: user,
      });
    });

    // User A's match request will hang
    matchService.getMatches.mockImplementation((user) => {
      if (user === 'user_A') {
        return new Promise((resolve) => {
          oldUserResolve = resolve;
        });
      }
      if (user === 'user_B') {
        return Promise.resolve({
          requesting_user_id: 'user_B',
          top_matches: [{ ...mockMatchTaylor, user_b_id: 'candidate_for_B', display_name: 'Candidate B Match' }],
        });
      }
      return Promise.reject(new Error('Unexpected user'));
    });

    render(
      <WorkflowProvider initialUserId="user_A">
        <BrowserRouter>
          <ContextSwitcher userId="user_B" />
          <MatchesPage />
        </BrowserRouter>
      </WorkflowProvider>
    );

    // Verify initial request for user_A was initiated
    await waitFor(() => {
      expect(matchService.getMatches).toHaveBeenCalledWith('user_A', 3);
    });

    // Trigger workflow user context switch to user_B
    fireEvent.click(screen.getByText('Switch to user_B'));

    // Verify user_B's match renders
    await waitFor(() => {
      expect(matchService.getMatches).toHaveBeenCalledWith('user_B', 3);
      expect(screen.getByText('Candidate B Match')).toBeInTheDocument();
    });

    // Resolve User A's hanging request late
    oldUserResolve({
      requesting_user_id: 'user_A',
      top_matches: [{ ...mockMatchTaylor, user_b_id: 'candidate_for_A', display_name: 'Candidate A Match' }],
    });

    // Verify User A's result NEVER replaces User B's result
    await waitFor(() => {
      expect(screen.getByText('Candidate B Match')).toBeInTheDocument();
      expect(screen.queryByText('Candidate A Match')).not.toBeInTheDocument();
    });
  });

  it('17. No invented candidate data is displayed', async () => {
    matchService.getMatches.mockResolvedValueOnce({
      requesting_user_id: 'alex_101',
      top_matches: [mockMatchTaylor],
    });

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('Taylor')).toBeInTheDocument();
      // Verify no fictitious bios, profile pictures, or fabricated swipe metrics exist
      expect(screen.queryByAltText(/profile photo/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/swipe/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/superlike/i)).not.toBeInTheDocument();
    });
  });

  it('18. Eligibility safety: explicitly filters out ineligible or pending candidates', async () => {
    const ineligibleMatch = {
      ...mockMatchJordan,
      user_b_id: 'ineligible_404',
      display_name: 'Ineligible Person',
      is_eligible: false,
      eligibility_status: 'ineligible',
    };

    const pendingMatch = {
      ...mockMatchMorgan,
      user_b_id: 'pending_505',
      display_name: 'Pending Person',
      is_eligible: true,
      eligibility_status: 'pending_information',
    };

    matchService.getMatches.mockResolvedValueOnce({
      requesting_user_id: 'alex_101',
      top_matches: [mockMatchTaylor, ineligibleMatch, pendingMatch],
    });

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('Taylor')).toBeInTheDocument();
      expect(screen.queryByText('Ineligible Person')).not.toBeInTheDocument();
      expect(screen.queryByText('Pending Person')).not.toBeInTheDocument();
    });
  });

  it('19. Assessment completion verification check via active assessment session', async () => {
    sessionStorage.setItem('matchlens_assessment_id', 'active_assess_101');

    // Active assessment state on backend is still 'ready_for_review' (not completed)
    assessmentService.getAssessmentState.mockResolvedValueOnce({
      assessment_id: 'active_assess_101',
      user_id: 'alex_101',
      status: 'ready_for_review',
      current_stage: 'review',
    });

    renderWithProviders('alex_101');

    await waitFor(() => {
      expect(screen.getByText('Complete Scenario Assessment')).toBeInTheDocument();
    });

    expect(matchService.getMatches).not.toHaveBeenCalled();
  });
});
