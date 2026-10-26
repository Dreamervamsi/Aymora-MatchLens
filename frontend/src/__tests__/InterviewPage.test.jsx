import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { WorkflowProvider } from '../context/WorkflowContext';
import { InterviewPage } from '../pages/InterviewPage';
import { interviewService } from '../services/interviewService';

// Mock interviewService methods
vi.mock('../services/interviewService', () => ({
  interviewService: {
    getInterviewState: vi.fn(),
    startInterview: vi.fn(),
    processTurn: vi.fn(),
    confirmProfile: vi.fn(),
  },
}));

const renderWithProviders = (ui) => {
  return render(
    <WorkflowProvider>
      <BrowserRouter>{ui}</BrowserRouter>
    </WorkflowProvider>
  );
};

describe('InterviewPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it('starts a new interview when no active session exists', async () => {
    interviewService.startInterview.mockResolvedValueOnce({
      session_id: 'test_session_123',
      assistant_message: 'Welcome to MatchLens! Tell me about yourself.',
      interview_status: 'active',
      current_topic: 'basic_and_intention',
      progress: { percentage: 0, completed_topics: [] },
      pending_confirmations: [],
    });

    renderWithProviders(<InterviewPage />);

    expect(screen.getByText('Initializing session...')).toBeInTheDocument();

    await waitFor(() => {
      expect(interviewService.startInterview).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(
        screen.getByText('Welcome to MatchLens! Tell me about yourself.')
      ).toBeInTheDocument();
    });
  });

  it('allows entering and submitting messages normally after Start Fresh completes', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'old_session_111');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'old_session_111',
      status: 'active',
      current_topic: 'basic_and_intention',
      turn_count: 2,
      progress: { percentage: 20, completed_topics: [] },
      conversation_history: [
        { role: 'assistant', content: 'Old intro message', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    interviewService.startInterview.mockResolvedValueOnce({
      session_id: 'brand_new_session_222',
      assistant_message: 'New session started. What is your age?',
      interview_status: 'active',
      current_topic: 'basic_and_intention',
      progress: { percentage: 0, completed_topics: [] },
      pending_confirmations: [],
    });

    interviewService.processTurn.mockResolvedValueOnce({
      session_id: 'brand_new_session_222',
      assistant_message: 'Thanks! What are your goals?',
      interview_status: 'active',
      current_topic: 'basic_and_intention',
      progress: { percentage: 10, completed_topics: [] },
      newly_extracted_fields: ['attributes.age'],
      pending_confirmations: [],
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Old intro message')).toBeInTheDocument();
    });

    const startFreshBtn = screen.getByRole('button', { name: /start fresh/i });
    fireEvent.click(startFreshBtn);

    await waitFor(() => {
      expect(screen.getByText('New session started. What is your age?')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Type your response... (Press Enter to send)');
    fireEvent.change(input, { target: { value: 'I am 25 years old' } });

    const sendBtn = screen.getByRole('button', { name: '' });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(interviewService.processTurn).toHaveBeenCalledWith('brand_new_session_222', 'I am 25 years old');
      expect(screen.getByText('Thanks! What are your goals?')).toBeInTheDocument();
    });
  });

  it('handles multiple identical user messages and targets retry to specific failed message ID', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_dup_msg');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_dup_msg',
      status: 'active',
      current_topic: 'basic_and_intention',
      turn_count: 1,
      progress: { percentage: 10, completed_topics: [] },
      conversation_history: [
        { role: 'assistant', content: 'Tell me about yourself', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    interviewService.processTurn
      .mockResolvedValueOnce({
        session_id: 'sess_dup_msg',
        assistant_message: 'Got first message',
        interview_status: 'active',
        current_topic: 'basic_and_intention',
        progress: { percentage: 15, completed_topics: [] },
        newly_extracted_fields: [],
        pending_confirmations: [],
      })
      .mockRejectedValueOnce(new Error('Second send failed'))
      .mockResolvedValueOnce({
        session_id: 'sess_dup_msg',
        assistant_message: 'Retried second message success',
        interview_status: 'active',
        current_topic: 'basic_and_intention',
        progress: { percentage: 20, completed_topics: [] },
        newly_extracted_fields: [],
        pending_confirmations: [],
      });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Tell me about yourself')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Type your response... (Press Enter to send)');
    const sendBtn = screen.getByRole('button', { name: '' });

    // First send: "Hello"
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText('Got first message')).toBeInTheDocument();
    });

    // Second send: "Hello" (identical text)
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText('Failed to send.')).toBeInTheDocument();
    });

    const retryBtn = screen.getByText('Retry');
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByText('Retried second message success')).toBeInTheDocument();
    });
  });

  it('renders neutral system notice when restoring session without conversation history', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_no_hist');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_no_hist',
      status: 'active',
      current_topic: 'lifestyle',
      turn_count: 3,
      progress: { percentage: 30, completed_topics: [] },
      conversation_history: [],
      pending_confirmations: [],
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Session restored. Detailed past conversation turns are unavailable.')).toBeInTheDocument();
    });
  });

  it('sends user turn message and renders returned assistant response', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_turn_test');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_turn_test',
      status: 'active',
      current_topic: 'basic_and_intention',
      turn_count: 1,
      progress: { percentage: 10, completed_topics: [] },
      conversation_history: [
        { role: 'assistant', content: 'What is your age and gender?', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    interviewService.processTurn.mockResolvedValueOnce({
      session_id: 'sess_turn_test',
      assistant_message: 'Great, thank you! What are your core values in a relationship?',
      interview_status: 'active',
      current_topic: 'core_values',
      progress: { percentage: 20, completed_topics: ['basic_and_intention'] },
      newly_extracted_fields: ['attributes.age'],
      pending_confirmations: [],
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('What is your age and gender?')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Type your response... (Press Enter to send)');
    fireEvent.change(input, { target: { value: 'I am 28 years old.' } });

    const submitBtn = screen.getByRole('button', { name: '' }); // Send icon button
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(interviewService.processTurn).toHaveBeenCalledWith('sess_turn_test', 'I am 28 years old.');
    });

    await waitFor(() => {
      expect(
        screen.getByText('Great, thank you! What are your core values in a relationship?')
      ).toBeInTheDocument();
    });
  });

  it('displays Review My Profile CTA overlay when ready_for_review status is returned', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_review');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_review',
      status: 'ready_for_review',
      current_topic: 'dealbreakers',
      turn_count: 12,
      progress: { percentage: 100, completed_topics: ['basic_and_intention', 'core_values', 'lifestyle', 'communication', 'partner_expectations', 'dealbreakers'] },
      conversation_history: [
        { role: 'assistant', content: 'Your draft profile is ready for review!', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Draft Profile Ready!').textContent).toBe('Draft Profile Ready!');
      expect(screen.getByRole('button', { name: 'Review My Profile' })).toBeInTheDocument();
    });
  });

  it('retains draft and shows explicit retry action when turn submission fails', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_fail_test');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_fail_test',
      status: 'active',
      current_topic: 'basic_and_intention',
      turn_count: 1,
      progress: { percentage: 10, completed_topics: [] },
      conversation_history: [
        { role: 'assistant', content: 'What is your age and gender?', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    interviewService.processTurn.mockRejectedValueOnce(new Error('Network error'));

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('What is your age and gender?')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Type your response... (Press Enter to send)');
    fireEvent.change(input, { target: { value: 'My name is Alex' } });

    const submitBtn = screen.getByRole('button', { name: '' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Failed to send.')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
      expect(input.value).toBe('My name is Alex');
    });
  });

  it('allows retrying without accidental duplicate submission', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_retry_test');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_retry_test',
      status: 'active',
      current_topic: 'basic_and_intention',
      turn_count: 1,
      progress: { percentage: 10, completed_topics: [] },
      conversation_history: [
        { role: 'assistant', content: 'What is your age?', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    interviewService.processTurn
      .mockRejectedValueOnce(new Error('Temporary error'))
      .mockResolvedValueOnce({
        session_id: 'sess_retry_test',
        assistant_message: 'Got it, you are 30.',
        interview_status: 'active',
        current_topic: 'core_values',
        progress: { percentage: 20, completed_topics: [] },
        newly_extracted_fields: ['attributes.age'],
        pending_confirmations: [],
      });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('What is your age?')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Type your response... (Press Enter to send)');
    fireEvent.change(input, { target: { value: 'I am 30' } });

    const submitBtn = screen.getByRole('button', { name: '' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Failed to send.')).toBeInTheDocument();
    });

    const retryBtn = screen.getByText('Retry');
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(interviewService.processTurn).toHaveBeenCalledTimes(2);
      expect(screen.getByText('Got it, you are 30.')).toBeInTheDocument();
    });
  });

  it('creates a new session rather than restoring the old one on Start Fresh', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'old_session_999');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'old_session_999',
      status: 'active',
      current_topic: 'lifestyle',
      turn_count: 4,
      progress: { percentage: 40, completed_topics: [] },
      conversation_history: [
        { role: 'assistant', content: 'Old question', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    interviewService.startInterview.mockResolvedValueOnce({
      session_id: 'brand_new_session_000',
      assistant_message: 'Fresh start interview message.',
      interview_status: 'active',
      current_topic: 'basic_and_intention',
      progress: { percentage: 0, completed_topics: [] },
      pending_confirmations: [],
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Old question')).toBeInTheDocument();
    });

    const startFreshBtn = screen.getByRole('button', { name: /start fresh/i });
    fireEvent.click(startFreshBtn);

    await waitFor(() => {
      expect(interviewService.startInterview).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Fresh start interview message.')).toBeInTheDocument();
      expect(sessionStorage.getItem('matchlens_interview_session_id')).toBe('brand_new_session_000');
    });
  });

  it('prevents late responses from an old session from overwriting a restarted session', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'old_sess');

    let resolveGetState;
    interviewService.getInterviewState.mockImplementationOnce(() => {
      return new Promise((resolve) => {
        resolveGetState = resolve;
      });
    });

    interviewService.startInterview.mockResolvedValueOnce({
      session_id: 'new_sess',
      assistant_message: 'New Session Welcome',
      interview_status: 'active',
      current_topic: 'basic_and_intention',
      progress: { percentage: 0, completed_topics: [] },
      pending_confirmations: [],
    });

    renderWithProviders(<InterviewPage />);

    // Perform Start Fresh while old getInterviewState is pending
    const startFreshBtn = screen.getByRole('button', { name: /start fresh/i });
    fireEvent.click(startFreshBtn);

    // Resolve old getInterviewState late
    resolveGetState({
      session_id: 'old_sess',
      status: 'active',
      current_topic: 'lifestyle',
      turn_count: 5,
      progress: { percentage: 50, completed_topics: [] },
      conversation_history: [
        { role: 'assistant', content: 'STALE OLD SESSION CONTENT', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    await waitFor(() => {
      expect(screen.getByText('New Session Welcome')).toBeInTheDocument();
      expect(screen.queryByText('STALE OLD SESSION CONTENT')).not.toBeInTheDocument();
    });
  });

  it('shows explicit session expired state when session is missing/404 and requires explicit start', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'expired_sess');

    interviewService.getInterviewState.mockRejectedValueOnce({
      status: 404,
      message: 'Interview session not found',
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Session Expired or Not Found')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Start New Interview' })).toBeInTheDocument();
    });

    expect(interviewService.startInterview).not.toHaveBeenCalled();

    const startNewBtn = screen.getByRole('button', { name: 'Start New Interview' });
    interviewService.startInterview.mockResolvedValueOnce({
      session_id: 'fresh_session_after_expiry',
      assistant_message: 'Welcome to your new session!',
      interview_status: 'active',
      current_topic: 'basic_and_intention',
      progress: { percentage: 0, completed_topics: [] },
      pending_confirmations: [],
    });

    fireEvent.click(startNewBtn);

    await waitFor(() => {
      expect(interviewService.startInterview).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Welcome to your new session!')).toBeInTheDocument();
    });
  });

  it('ensures pending confirmations remain actionable after refresh and historical ones are read-only', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'conf_sess');

    const pendingConf = {
      field_name: 'smoking',
      target_category: 'self_attributes',
      proposed_value: 'Socially',
      reasoning: 'You mentioned smoking with friends.',
      clarification_question: 'Do you smoke socially?',
    };

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'conf_sess',
      status: 'awaiting_confirmation',
      current_topic: 'lifestyle',
      turn_count: 2,
      progress: { percentage: 20, completed_topics: [] },
      conversation_history: [
        {
          role: 'assistant',
          content: 'Historical prompt',
          pendingConfirmations: [pendingConf],
        },
        {
          role: 'assistant',
          content: 'Active confirmation prompt',
          pendingConfirmations: [pendingConf],
        },
      ],
      pending_confirmations: [pendingConf],
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Active confirmation prompt')).toBeInTheDocument();
    });

    // Check buttons are present ONLY for the active confirmation
    const confirmBtns = screen.getAllByRole('button', { name: 'Yes, Confirm' });
    expect(confirmBtns.length).toBe(1);

    expect(screen.getByText('Confirmation recorded')).toBeInTheDocument();
  });

  it('allows user to provide a correction when rejection is selected', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'reject_sess');

    const pendingConf = {
      field_name: 'smoking',
      target_category: 'self_attributes',
      proposed_value: 'Regularly',
      reasoning: 'Inferred smoking habits.',
      clarification_question: 'Do you smoke regularly?',
    };

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'reject_sess',
      status: 'awaiting_confirmation',
      current_topic: 'lifestyle',
      turn_count: 2,
      progress: { percentage: 20, completed_topics: [] },
      conversation_history: [
        {
          role: 'assistant',
          content: 'Do you smoke regularly?',
          pendingConfirmations: [pendingConf],
        },
      ],
      pending_confirmations: [pendingConf],
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Do you smoke regularly?')).toBeInTheDocument();
    });

    const rejectBtn = screen.getByRole('button', { name: 'No, Correct' });
    fireEvent.click(rejectBtn);

    await waitFor(() => {
      expect(screen.getByText(/Providing correction for/)).toBeInTheDocument();
      const input = screen.getByPlaceholderText('Type your response... (Press Enter to send)');
      expect(input.value).toBe('No, actually for smoking: ');
    });
  });

  it('prevents double-clicking Send from submitting twice', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_double_send');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_double_send',
      status: 'active',
      current_topic: 'basic_and_intention',
      turn_count: 1,
      progress: { percentage: 10, completed_topics: [] },
      conversation_history: [
        { role: 'assistant', content: 'Hello', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    let resolveTurn;
    interviewService.processTurn.mockImplementationOnce(() => {
      return new Promise((resolve) => {
        resolveTurn = resolve;
      });
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Type your response... (Press Enter to send)');
    fireEvent.change(input, { target: { value: 'Single submission test' } });

    const submitBtn = screen.getByRole('button', { name: '' });
    fireEvent.click(submitBtn);
    fireEvent.click(submitBtn);

    expect(interviewService.processTurn).toHaveBeenCalledTimes(1);

    resolveTurn({
      session_id: 'sess_double_send',
      assistant_message: 'Response',
      interview_status: 'active',
      current_topic: 'basic_and_intention',
      progress: { percentage: 15, completed_topics: [] },
      newly_extracted_fields: [],
      pending_confirmations: [],
    });
  });

  it('ensures ready-for-review state does not automatically confirm the profile', async () => {
    sessionStorage.setItem('matchlens_interview_session_id', 'sess_ready');

    interviewService.getInterviewState.mockResolvedValueOnce({
      session_id: 'sess_ready',
      status: 'ready_for_review',
      current_topic: 'dealbreakers',
      turn_count: 10,
      progress: { percentage: 100, completed_topics: [] },
      conversation_history: [
        { role: 'assistant', content: 'Ready for review', timestamp: '2026-03-30T10:00:00Z' },
      ],
      pending_confirmations: [],
    });

    renderWithProviders(<InterviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Draft Profile Ready!')).toBeInTheDocument();
    });

    // Verify profile confirm API was NOT called automatically
    expect(interviewService.confirmProfile).not.toHaveBeenCalled();
  });
});
