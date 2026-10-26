import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { WorkflowProvider } from '../context/WorkflowContext';
import { AssessmentPage } from '../pages/AssessmentPage';
import assessmentService from '../services/assessmentService';
import profileService from '../services/profileService';
import { ApiError } from '../services/apiClient';

vi.mock('../services/assessmentService', () => ({
  assessmentService: {
    startAssessment: vi.fn(),
    submitTurn: vi.fn(),
    correctResponse: vi.fn(),
    getAssessmentState: vi.fn(),
    confirmAssessment: vi.fn(),
  },
  default: {
    startAssessment: vi.fn(),
    submitTurn: vi.fn(),
    correctResponse: vi.fn(),
    getAssessmentState: vi.fn(),
    confirmAssessment: vi.fn(),
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

const renderWithProviders = (ui, initialUserId = 'test_user_123') => {
  if (initialUserId) {
    sessionStorage.setItem('matchlens_user_id', initialUserId);
  }
  return render(
    <WorkflowProvider initialUserId={initialUserId}>
      <BrowserRouter>{ui}</BrowserRouter>
    </WorkflowProvider>
  );
};

const mockConfirmedProfile = {
  user_id: 'test_user_123',
  attributes: { age: 28, gender: 'woman', relationship_intent: 'long_term' },
  expectations: { min_age: 25, max_age: 35 },
  dealbreakers: {},
};

const mockScenarioDefinition = {
  scenario_id: 'conflict_resolution_01',
  target_dimension: 'communication_preferences',
  title: 'Handling disagreement after a stressful day',
  description: 'A major disagreement arises at the end of a long, stressful workday.',
  self_prompt: 'What would you most likely do in this situation?',
  partner_prompt: 'What would you prefer or be comfortable with your partner doing?',
  allowed_options: ['discuss_immediately', 'cool_down_first', 'written_first', 'defer_to_partner'],
  option_descriptions: {
    discuss_immediately: 'Talk through the issue immediately to clear the air.',
    cool_down_first: 'Take time alone to process before discussing.',
    written_first: 'Express thoughts in a text or letter before talking.',
    defer_to_partner: 'Let partner take the lead on when and how to resolve.',
  },
};

const mockInitialTurn = {
  assessment_id: 'assess_001',
  status: 'active',
  current_stage: 'self_behavior',
  current_scenario_id: 'conflict_resolution_01',
  scenario_definition: mockScenarioDefinition,
  prompt_text: 'Scenario 1/3: Handling disagreement',
  allowed_options: ['discuss_immediately', 'cool_down_first', 'written_first', 'defer_to_partner'],
  unresolved_clarification: null,
  progress: {
    current_scenario_index: 0,
    total_scenarios: 3,
    completed_scenario_ids: [],
    current_stage: 'self_behavior',
    percentage: 0.0,
  },
  summary_data: null,
};

describe('AssessmentPage Component — Phase 7.4 Requirements', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    sessionStorage.clear();
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
  });

  it('1. Assessment page requires a confirmed profile', async () => {
    sessionStorage.setItem('matchlens_user_id', 'user_no_profile');
    profileService.getProfile.mockImplementation((id) => {
      if (id === 'user_no_profile') {
        return Promise.reject(new ApiError('Not found', 404));
      }
      return Promise.resolve(mockConfirmedProfile);
    });

    renderWithProviders(<AssessmentPage />, 'user_no_profile');

    await waitFor(() => {
      expect(screen.getByText('Complete Profile Review First')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Go to Profile Review' })).toBeInTheDocument();
    });
    expect(assessmentService.startAssessment).not.toHaveBeenCalled();
  });

  it('2. Starting an assessment creates one session', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.startAssessment.mockResolvedValueOnce(mockInitialTurn);

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Ready to Begin Assessment')).toBeInTheDocument();
    });

    const startBtn = screen.getByRole('button', { name: 'Start Assessment' });
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(assessmentService.startAssessment).toHaveBeenCalledTimes(1);
      expect(assessmentService.startAssessment).toHaveBeenCalledWith('test_user_123', null, null);
      expect(screen.getByText('Handling disagreement after a stressful day')).toBeInTheDocument();
    });
  });

  it('3. Existing assessment is restored after refresh', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_existing');

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce({
      ...mockInitialTurn,
      assessment_id: 'assess_existing',
    });

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(assessmentService.getAssessmentState).toHaveBeenCalledWith('assess_existing');
      expect(screen.getByText('Handling disagreement after a stressful day')).toBeInTheDocument();
    });
  });

  it('4. Expired assessment requires explicit restart', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_expired');

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockRejectedValueOnce(new ApiError('Assessment session not found', 404));

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText(/Stored assessment session has expired/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Start New Assessment' })).toBeInTheDocument();
    });

    expect(assessmentService.startAssessment).not.toHaveBeenCalled();

    assessmentService.startAssessment.mockResolvedValueOnce(mockInitialTurn);
    fireEvent.click(screen.getByRole('button', { name: 'Start New Assessment' }));

    await waitFor(() => {
      expect(assessmentService.startAssessment).toHaveBeenCalledTimes(1);
    });
  });

  it('5. Scenario content renders correctly', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce(mockInitialTurn);

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Handling disagreement after a stressful day')).toBeInTheDocument();
      expect(screen.getByText('Perspective A — Your Behavior')).toBeInTheDocument();
      expect(screen.getByText('Discuss Immediately')).toBeInTheDocument();
      expect(screen.getByText('Cool Down First')).toBeInTheDocument();
    });
  });

  it('6. Self-response submission', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce(mockInitialTurn);

    const partnerStageTurn = {
      ...mockInitialTurn,
      current_stage: 'partner_expectation',
      progress: { ...mockInitialTurn.progress, percentage: 16.7 },
    };
    assessmentService.submitTurn.mockResolvedValueOnce(partnerStageTurn);

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Perspective A — Your Behavior')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Discuss Immediately'));
    fireEvent.click(screen.getByRole('button', { name: 'Submit Choice & Proceed' }));

    await waitFor(() => {
      expect(assessmentService.submitTurn).toHaveBeenCalledWith('assess_001', 'discuss_immediately');
      expect(screen.getByText('Perspective B — Your Ideal Partner')).toBeInTheDocument();
    });
  });

  it('7. Partner-response submission', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const partnerTurnState = {
      ...mockInitialTurn,
      current_stage: 'partner_expectation',
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce(partnerTurnState);

    const nextScenarioTurn = {
      ...mockInitialTurn,
      current_stage: 'self_behavior',
      current_scenario_id: 'social_energy_01',
      progress: { current_scenario_index: 1, total_scenarios: 3, percentage: 33.3 },
    };
    assessmentService.submitTurn.mockResolvedValueOnce(nextScenarioTurn);

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Perspective B — Your Ideal Partner')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Cool Down First'));
    fireEvent.click(screen.getByRole('button', { name: 'Submit Choice & Proceed' }));

    await waitFor(() => {
      expect(assessmentService.submitTurn).toHaveBeenCalledWith('assess_001', 'cool_down_first');
    });
  });

  it('8. Different self and partner choices remain independent', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce(mockInitialTurn);

    // Turn 1: self_behavior -> 'discuss_immediately'
    assessmentService.submitTurn.mockResolvedValueOnce({
      ...mockInitialTurn,
      current_stage: 'partner_expectation',
    });

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Perspective A — Your Behavior')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Discuss Immediately'));
    fireEvent.click(screen.getByRole('button', { name: 'Submit Choice & Proceed' }));

    await waitFor(() => {
      expect(assessmentService.submitTurn).toHaveBeenLastCalledWith('assess_001', 'discuss_immediately');
    });

    // Turn 2: partner_expectation -> 'cool_down_first' (distinct option)
    assessmentService.submitTurn.mockResolvedValueOnce({
      ...mockInitialTurn,
      current_scenario_index: 1,
      current_stage: 'self_behavior',
    });

    fireEvent.click(screen.getByText('Cool Down First'));
    fireEvent.click(screen.getByRole('button', { name: 'Submit Choice & Proceed' }));

    await waitFor(() => {
      expect(assessmentService.submitTurn).toHaveBeenLastCalledWith('assess_001', 'cool_down_first');
    });
  });

  it('9. Duplicate submission prevention', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce(mockInitialTurn);

    let resolveTurn;
    assessmentService.submitTurn.mockImplementationOnce(() => {
      return new Promise((resolve) => {
        resolveTurn = resolve;
      });
    });

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Discuss Immediately')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Discuss Immediately'));
    const submitBtn = screen.getByRole('button', { name: 'Submit Choice & Proceed' });

    fireEvent.click(submitBtn);
    fireEvent.click(submitBtn);

    expect(assessmentService.submitTurn).toHaveBeenCalledTimes(1);

    resolveTurn(mockInitialTurn);
  });

  it('10. Backend clarification handling', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const clarificationTurn = {
      ...mockInitialTurn,
      unresolved_clarification: {
        scenario_id: 'conflict_resolution_01',
        stage: 'self_behavior',
        raw_input: 'i like talking right away',
        proposed_option: 'discuss_immediately',
        confidence: 0.6,
        reasoning: 'Matches immediate discussion',
        clarification_prompt: 'Did you mean "discuss_immediately"?',
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce(clarificationTurn);

    assessmentService.submitTurn.mockResolvedValueOnce({
      ...mockInitialTurn,
      current_stage: 'partner_expectation',
      unresolved_clarification: null,
    });

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Clarification Required')).toBeInTheDocument();
      expect(screen.getByText('Did you mean "discuss_immediately"?')).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole('button', { name: /Yes, I meant "discuss immediately"/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(assessmentService.submitTurn).toHaveBeenCalledWith('assess_001', 'yes');
    });
  });

  it('11. Partial scenario completion', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const partialProgressTurn = {
      ...mockInitialTurn,
      current_stage: 'partner_expectation',
      progress: {
        current_scenario_index: 0,
        total_scenarios: 3,
        completed_scenario_ids: [],
        current_stage: 'partner_expectation',
        percentage: 16.7,
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce(partialProgressTurn);

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('17% Completed')).toBeInTheDocument();
      expect(screen.getByText('• Part B: Ideal Partner')).toBeInTheDocument();
    });
  });

  it('12. Correct progress tracking', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const halfProgressTurn = {
      ...mockInitialTurn,
      current_scenario_index: 1,
      current_stage: 'partner_expectation',
      progress: {
        current_scenario_index: 1,
        total_scenarios: 3,
        completed_scenario_ids: ['conflict_resolution_01'],
        current_stage: 'partner_expectation',
        percentage: 50.0,
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce(halfProgressTurn);

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('50% Completed')).toBeInTheDocument();
      expect(screen.getByText('Scenario 2 of 3')).toBeInTheDocument();
    });
  });

  it('13. Assessment ready-for-review state', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const reviewTurn = {
      assessment_id: 'assess_001',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01', 'social_energy_01', 'financial_planning_01'],
      progress: { current_scenario_index: 3, total_scenarios: 3, completed_scenario_ids: ['conflict_resolution_01', 'social_energy_01', 'financial_planning_01'], percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
        social_energy_01: { self_response: 'stay_home_quiet', partner_expectation: 'small_group_gathering' },
        financial_planning_01: { self_response: 'balanced_spending', partner_expectation: 'balanced_spending' },
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByText('Review Your Assessment')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Confirm My Assessment' })).toBeInTheDocument();
    });
  });

  it('14. Review of all three scenarios', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const reviewTurn = {
      assessment_id: 'assess_001',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01', 'social_energy_01', 'financial_planning_01'],
      progress: { current_scenario_index: 3, total_scenarios: 3, percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
        social_energy_01: { self_response: 'stay_home_quiet', partner_expectation: 'small_group_gathering' },
        financial_planning_01: { self_response: 'balanced_spending', partner_expectation: 'balanced_spending' },
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByText('Handling disagreement after a stressful day')).toBeInTheDocument();
      expect(screen.getByText('Weekend downtime preferences')).toBeInTheDocument();
      expect(screen.getByText('Approach to joint budgeting and major expenses')).toBeInTheDocument();
    });
  });

  it('15. Correction of self-response without modifying partner-response', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const reviewTurn = {
      assessment_id: 'assess_001',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01'],
      progress: { percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);

    assessmentService.correctResponse.mockResolvedValueOnce({
      ...reviewTurn,
      summary_data: {
        conflict_resolution_01: { self_response: 'cool_down_first', partner_expectation: 'cool_down_first' },
      },
    });

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByText('Discuss Immediately')).toBeInTheDocument();
    });

    const correctBtns = screen.getAllByText('Correct');
    fireEvent.click(correctBtns[0]); // Correct self behavior

    const input = screen.getByPlaceholderText('Type option, e.g. discuss_immediately');
    fireEvent.change(input, { target: { value: 'cool_down_first' } });

    const saveBtn = screen.getByRole('button', { name: 'Save' });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(assessmentService.correctResponse).toHaveBeenCalledWith(
        'assess_001',
        'conflict_resolution_01',
        'self_behavior',
        'cool_down_first'
      );
    });
  });

  it('16. Correction of partner-response without modifying self-response', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const reviewTurn = {
      assessment_id: 'assess_001',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01'],
      progress: { percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);

    assessmentService.correctResponse.mockResolvedValueOnce({
      ...reviewTurn,
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'written_first' },
      },
    });

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByText('Cool Down First')).toBeInTheDocument();
    });

    const correctBtns = screen.getAllByText('Correct');
    fireEvent.click(correctBtns[1]); // Correct partner expectation

    const input = screen.getByPlaceholderText('Type option, e.g. cool_down_first');
    fireEvent.change(input, { target: { value: 'written_first' } });

    const saveBtn = screen.getByRole('button', { name: 'Save' });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(assessmentService.correctResponse).toHaveBeenCalledWith(
        'assess_001',
        'conflict_resolution_01',
        'partner_expectation',
        'written_first'
      );
    });
  });

  it('17. No automatic assessment confirmation', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const reviewTurn = {
      assessment_id: 'assess_001',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01'],
      progress: { percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByText('Review Your Assessment')).toBeInTheDocument();
    });

    // Verify confirm API was NOT called automatically
    expect(assessmentService.confirmAssessment).not.toHaveBeenCalled();
  });

  it('18. Explicit confirmation success', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const reviewTurn = {
      assessment_id: 'assess_001',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01'],
      progress: { percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);
    assessmentService.confirmAssessment.mockResolvedValueOnce({
      ...mockConfirmedProfile,
      scenario_responses: [{ scenario_id: 'conflict_resolution_01' }],
    });

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Confirm My Assessment' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Confirm My Assessment' }));

    await waitFor(() => {
      expect(assessmentService.confirmAssessment).toHaveBeenCalledWith('assess_001');
      expect(screen.getByText('Scenario Assessment Confirmed!')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Discover My Matches' })).toBeInTheDocument();
    });
  });

  it('19. Confirmation failure or timeout recovery', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_timeout');

    const reviewTurn = {
      assessment_id: 'assess_timeout',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01'],
      progress: { percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);

    // Confirmation API times out
    assessmentService.confirmAssessment.mockRejectedValueOnce(new ApiError('Request timed out', 408));
    // Recheck profile finds attached scenario responses
    profileService.getProfile.mockImplementation(() => {
      return Promise.resolve({
        ...mockConfirmedProfile,
        scenario_responses: [{ scenario_id: 'conflict_resolution_01' }],
      });
    });

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Confirm My Assessment' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Confirm My Assessment' }));

    await waitFor(() => {
      expect(profileService.getProfile).toHaveBeenCalledWith('test_user_123');
      expect(screen.getByText('Scenario Assessment Confirmed!')).toBeInTheDocument();
    });
  });

  it('20. Already-completed assessment handling', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_done');

    const completedTurn = {
      assessment_id: 'assess_done',
      status: 'completed',
      current_stage: 'completed',
      selected_scenario_ids: ['conflict_resolution_01'],
      progress: { percentage: 100.0 },
    };

    profileService.getProfile.mockResolvedValue({
      ...mockConfirmedProfile,
      scenario_responses: [{ scenario_id: 'conflict_resolution_01' }],
    });
    assessmentService.getAssessmentState.mockResolvedValue(completedTurn);

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByText('Scenario Assessment Confirmed!')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Discover My Matches' })).toBeInTheDocument();
    });

    expect(assessmentService.confirmAssessment).not.toHaveBeenCalled();
  });

  it('21. Navigation to /matches only after authoritative completion', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const completedTurn = {
      assessment_id: 'assess_001',
      status: 'completed',
      current_stage: 'completed',
      progress: { percentage: 100.0 },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(completedTurn);

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      const matchBtn = screen.getByRole('button', { name: 'Discover My Matches' });
      expect(matchBtn).toBeInTheDocument();
    });
  });

  it('22. Late responses from old sessions do not overwrite the current assessment', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_old');

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);

    let oldResolve;
    assessmentService.getAssessmentState.mockImplementationOnce((id) => {
      if (id === 'assess_old') {
        return new Promise((resolve) => {
          oldResolve = resolve;
        });
      }
      return Promise.reject(new ApiError('Not found', 404));
    });

    assessmentService.startAssessment.mockResolvedValueOnce({
      ...mockInitialTurn,
      assessment_id: 'assess_brand_new',
      scenario_definition: {
        ...mockScenarioDefinition,
        title: 'Brand New Session Scenario',
      },
    });

    renderWithProviders(<AssessmentPage />);

    // Wait for old assessment restore attempt to be pending, then start new assessment
    await waitFor(() => {
      expect(assessmentService.getAssessmentState).toHaveBeenCalledWith('assess_old');
    });

    const startBtn = screen.getByRole('button', { name: 'Start Assessment' });
    fireEvent.click(startBtn);

    // Resolve old request late
    if (oldResolve) {
      oldResolve({
        ...mockInitialTurn,
        assessment_id: 'assess_old',
        scenario_definition: {
          ...mockScenarioDefinition,
          title: 'OLD STALE SESSION',
        },
      });
    }

    await waitFor(() => {
      expect(assessmentService.startAssessment).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Brand New Session Scenario')).toBeInTheDocument();
      expect(screen.queryByText('OLD STALE SESSION')).not.toBeInTheDocument();
    });
  });

  it('23. Confirmation POST succeeds but persisted responses are unavailable', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const reviewTurn = {
      assessment_id: 'assess_001',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01'],
      progress: { percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);
    assessmentService.confirmAssessment.mockResolvedValueOnce({
      user_id: 'test_user_123',
      scenario_responses: [],
    });

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Confirm My Assessment' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Confirm My Assessment' }));

    await waitFor(() => {
      expect(screen.queryByText('Scenario Assessment Confirmed!')).not.toBeInTheDocument();
      expect(screen.getByText(/persisted scenario responses for this assessment could not be verified/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Recheck Status' })).toBeInTheDocument();
    });
  });

  it('24. Existing unrelated scenario responses do not count as confirmation of the current assessment', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const reviewTurn = {
      assessment_id: 'assess_001',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01'],
      progress: { percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
      },
    };

    profileService.getProfile.mockResolvedValue({
      ...mockConfirmedProfile,
      scenario_responses: [{ scenario_id: 'unrelated_scenario_99' }],
    });
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);
    assessmentService.confirmAssessment.mockRejectedValueOnce(new ApiError('Server error', 500));

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Confirm My Assessment' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Confirm My Assessment' }));

    await waitFor(() => {
      expect(screen.queryByText('Scenario Assessment Confirmed!')).not.toBeInTheDocument();
      expect(screen.getByText(/network or server error occurred during confirmation/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Recheck Status' })).toBeInTheDocument();
    });
  });

  it('25. Correction failure retains the editor and entered value', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const reviewTurn = {
      assessment_id: 'assess_001',
      status: 'ready_for_review',
      current_stage: 'review',
      selected_scenario_ids: ['conflict_resolution_01'],
      progress: { percentage: 100.0 },
      summary_data: {
        conflict_resolution_01: { self_response: 'discuss_immediately', partner_expectation: 'cool_down_first' },
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValue(reviewTurn);
    assessmentService.correctResponse.mockRejectedValueOnce(new ApiError('Invalid response choice', 400));

    renderWithProviders(<AssessmentPage />, 'test_user_123');

    await waitFor(() => {
      expect(screen.getByText('Discuss Immediately')).toBeInTheDocument();
    });

    const correctBtns = screen.getAllByText('Correct');
    fireEvent.click(correctBtns[0]);

    const input = screen.getByPlaceholderText('Type option, e.g. discuss_immediately');
    fireEvent.change(input, { target: { value: 'invalid_choice' } });

    const saveBtn = screen.getByRole('button', { name: 'Save' });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Type option, e.g. discuss_immediately')).toBeInTheDocument();
      expect(screen.getByDisplayValue('invalid_choice')).toBeInTheDocument();
      expect(screen.getAllByText('Invalid response choice').length).toBeGreaterThan(0);
    });
  });

  it('26. Assessment restoration returns 500 error and allows retry', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_500');

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockRejectedValueOnce(new ApiError('Internal Server Error', 500));

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Assessment Restoration Failure')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Retry Restoration' })).toBeInTheDocument();
      expect(screen.queryByText('Ready to Begin Assessment')).not.toBeInTheDocument();
    });

    assessmentService.getAssessmentState.mockResolvedValueOnce(mockInitialTurn);
    fireEvent.click(screen.getByRole('button', { name: 'Retry Restoration' }));

    await waitFor(() => {
      expect(screen.getByText('Handling disagreement after a stressful day')).toBeInTheDocument();
    });
  });

  it('27. Assessment restoration times out', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_timeout');

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockRejectedValueOnce(new ApiError('Request timed out', 408));

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Assessment Restoration Failure')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Retry Restoration' })).toBeInTheDocument();
    });
  });

  it('28. Clarification safety with null proposed_option', async () => {
    sessionStorage.setItem('matchlens_user_id', 'test_user_123');
    sessionStorage.setItem('matchlens_assessment_id', 'assess_001');

    const clarificationTurn = {
      ...mockInitialTurn,
      unresolved_clarification: {
        scenario_id: 'conflict_resolution_01',
        stage: 'self_behavior',
        raw_input: 'maybe both or neither',
        proposed_option: null,
        clarification_prompt: 'Please rephrase your choice more specifically.',
      },
    };

    profileService.getProfile.mockResolvedValue(mockConfirmedProfile);
    assessmentService.getAssessmentState.mockResolvedValueOnce(clarificationTurn);

    renderWithProviders(<AssessmentPage />);

    await waitFor(() => {
      expect(screen.getByText('Please rephrase your choice more specifically.')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Yes, that is correct' })).toBeInTheDocument();
    });
  });
});
