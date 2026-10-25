import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Loader2, AlertCircle, Compass } from 'lucide-react';
import { useWorkflow } from '../context/WorkflowContext';
import { interviewService } from '../services/interviewService';
import {
  ChatMessage,
  ChatComposer,
  InterviewProgress,
  InterviewHeader,
} from '../components/interview';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

/**
 * Conversational AI Onboarding Interview Page.
 * Handles persistent session recovery, turn-by-turn processing, StrictMode deduplication,
 * and auto-scrolling chat history.
 */
export const InterviewPage = () => {
  const navigate = useNavigate();
  const { userId, sessionId, setSessionId, resetWorkflow } = useWorkflow();

  const [messages, setMessages] = useState([]);
  const [draftMessage, setDraftMessage] = useState('');
  const [status, setStatus] = useState('active');
  const [currentTopic, setCurrentTopic] = useState('basic_and_intention');
  const [progressPct, setProgressPct] = useState(0);
  const [completedTopics, setCompletedTopics] = useState([]);
  const [turnCount, setTurnCount] = useState(0);
  const [pendingConfirmations, setPendingConfirmations] = useState([]);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [rejectionTarget, setRejectionTarget] = useState(null);

  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);
  const isMountedRef = useRef(false);
  const activeSessionIdRef = useRef(sessionId);
  const activeRequestIdRef = useRef(0);

  useEffect(() => {
    activeSessionIdRef.current = sessionId;
  }, [sessionId]);

  // Auto-scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Session Initialization & Recovery
  const initSession = useCallback(async (forcedSessionId = undefined) => {
    setIsInitializing(true);
    setError(null);
    setSessionExpired(false);

    const targetSessionId = forcedSessionId !== undefined ? forcedSessionId : sessionId;

    try {
      if (targetSessionId) {
        // Attempt session recovery via GET /api/v1/interview/{sessionId}
        try {
          const stateData = await interviewService.getInterviewState(targetSessionId);
          
          // Guard against out-of-order session responses
          if (activeSessionIdRef.current && targetSessionId !== activeSessionIdRef.current) {
            return;
          }

          setStatus(stateData.status);
          setCurrentTopic(stateData.current_topic);
          setTurnCount(stateData.turn_count || 0);
          setPendingConfirmations(stateData.pending_confirmations || []);

          if (stateData.progress) {
            setProgressPct(stateData.progress.percentage || 0);
            setCompletedTopics(stateData.progress.completed_topics || []);
          }

          // Restore conversation history if provided by backend
          if (stateData.conversation_history && stateData.conversation_history.length > 0) {
            const restoredConfs = stateData.pending_confirmations || [];
            const lastAssistantIdx = stateData.conversation_history.findLastIndex((m) => m.role === 'assistant');

            setMessages(
              stateData.conversation_history.map((msg, idx) => ({
                id: `hist_${idx}`,
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp,
                pendingConfirmations: msg.pendingConfirmations || (idx === lastAssistantIdx && restoredConfs.length > 0 ? restoredConfs : []),
              }))
            );
          } else {
            // Show neutral recovery notice instead of inventing an assistant message
            setMessages([
              {
                id: 'res_notice',
                role: 'assistant',
                content: 'Session restored. How can I help you continue your interview?',
                timestamp: new Date().toISOString(),
              },
            ]);
          }
          setIsInitializing(false);
          return;
        } catch (recoverErr) {
          // If 404/not found or expired, do NOT auto-start a new session. Show session-expired state.
          if (recoverErr.status === 404 || (recoverErr.message && recoverErr.message.includes('not found'))) {
            setSessionId(null);
            setSessionExpired(true);
            setIsInitializing(false);
            return;
          } else {
            throw recoverErr;
          }
        }
      }

      // No active session or forced start: Start new interview
      const startRes = await interviewService.startInterview(userId);
      
      // Guard against stale response
      setSessionId(startRes.session_id);
      activeSessionIdRef.current = startRes.session_id;

      setStatus(startRes.interview_status || 'active');
      setCurrentTopic(startRes.current_topic || 'basic_and_intention');
      setTurnCount(1);
      setPendingConfirmations(startRes.pending_confirmations || []);

      if (startRes.progress) {
        setProgressPct(startRes.progress.percentage || 0);
        setCompletedTopics(startRes.progress.completed_topics || []);
      }

      setMessages([
        {
          id: 'init_1',
          role: 'assistant',
          content: startRes.assistant_message,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      setError(err.message || 'Failed to initialize interview session.');
    } finally {
      setIsInitializing(false);
    }
  }, [userId, sessionId, setSessionId]);

  // Mount effect with React StrictMode guard
  useEffect(() => {
    if (!isMountedRef.current) {
      isMountedRef.current = true;
      initSession();
    }
  }, [initSession]);

  // Handle user turn submission
  const handleSendMessage = async (userText, isRetry = false) => {
    if (!userText.trim() || isLoading) return;
    const currentSessionId = activeSessionIdRef.current;
    if (!currentSessionId) return;

    const requestId = ++activeRequestIdRef.current;

    setError(null);
    setIsLoading(true);

    const userMsgId = `user_${Date.now()}`;
    const newMsg = {
      id: userMsgId,
      role: 'user',
      content: userText,
      timestamp: new Date().toISOString(),
      status: 'pending',
    };

    // If not retrying an existing message, add user message to list and clear composer draft
    if (!isRetry) {
      setMessages((prev) => [...prev, newMsg]);
      setDraftMessage('');
    } else {
      // Mark failed message as sending again
      setMessages((prev) =>
        prev.map((msg) => (msg.id === userMsgId || msg.status === 'failed' ? { ...msg, status: 'pending' } : msg))
      );
    }

    try {
      const turnRes = await interviewService.processTurn(currentSessionId, userText);

      // Guard against responses from old/stale sessions or outdated requests
      if (activeSessionIdRef.current !== currentSessionId || activeRequestIdRef.current !== requestId) {
        return;
      }

      // Mark user message as delivered
      setMessages((prev) =>
        prev.map((msg) => (msg.content === userText && msg.status === 'pending' ? { ...msg, status: 'delivered' } : msg))
      );

      setStatus(turnRes.interview_status);
      setCurrentTopic(turnRes.current_topic);
      setTurnCount((prev) => prev + 1);
      setPendingConfirmations(turnRes.pending_confirmations || []);
      setRejectionTarget(null);

      if (turnRes.progress) {
        setProgressPct(turnRes.progress.percentage || 0);
        setCompletedTopics(turnRes.progress.completed_topics || []);
      }

      const assistantMsg = {
        id: `asst_${Date.now()}`,
        role: 'assistant',
        content: turnRes.assistant_message,
        timestamp: new Date().toISOString(),
        newlyExtracted: turnRes.newly_extracted_fields || [],
        pendingConfirmations: turnRes.pending_confirmations || [],
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      if (activeSessionIdRef.current !== currentSessionId || activeRequestIdRef.current !== requestId) {
        return;
      }

      // Ambiguous network failure check: try to recover state before blindly marking failed
      if (err.status === 0 || err.status === 408) {
        try {
          const recoveredState = await interviewService.getInterviewState(currentSessionId);
          // Check if server turn_count actually advanced
          if (recoveredState.turn_count > turnCount) {
            setStatus(recoveredState.status);
            setCurrentTopic(recoveredState.current_topic);
            setTurnCount(recoveredState.turn_count);
            setPendingConfirmations(recoveredState.pending_confirmations || []);
            if (recoveredState.progress) {
              setProgressPct(recoveredState.progress.percentage || 0);
              setCompletedTopics(recoveredState.progress.completed_topics || []);
            }
            if (recoveredState.conversation_history && recoveredState.conversation_history.length > 0) {
              setMessages(
                recoveredState.conversation_history.map((msg, idx) => ({
                  id: `hist_${idx}`,
                  role: msg.role,
                  content: msg.content,
                  timestamp: msg.timestamp,
                }))
              );
            }
            setIsLoading(false);
            return;
          }
        } catch {
          // Fall through to mark failed
        }
      }

      // Mark user message as failed and keep draft for resubmission/retry
      setMessages((prev) =>
        prev.map((msg) => (msg.content === userText && msg.status === 'pending' ? { ...msg, status: 'failed' } : msg))
      );
      setDraftMessage(userText);
      setError(err.message || 'Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle early finish trigger
  const handleEarlyFinish = async () => {
    await handleSendMessage('/finish');
  };

  // Handle fresh restart (Genuinely new session without setTimeout closures)
  const handleStartFresh = async () => {
    if (isLoading) return;
    setIsLoading(true);
    resetWorkflow();
    setSessionId(null);
    setMessages([]);
    setStatus('active');
    setCurrentTopic('basic_and_intention');
    setProgressPct(0);
    setCompletedTopics([]);
    setTurnCount(0);
    setPendingConfirmations([]);
    setSessionExpired(false);
    setError(null);
    setDraftMessage('');
    setRejectionTarget(null);

    // Call initSession with forced null sessionId to start fresh
    await initSession(null);
  };

  const isFinished = status === 'ready_for_review' || status === 'completed';

  return (
    <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
      {/* Top Section Progress Bar */}
      <InterviewProgress
        percentage={progressPct}
        currentTopic={currentTopic}
        completedTopics={completedTopics}
      />

      {/* Main Chat Container Card */}
      <Card className="flex-1 flex flex-col min-h-[500px] max-h-[70vh] p-4 sm:p-6 shadow-xs relative overflow-hidden">
        {/* Header Bar */}
        <InterviewHeader
          status={status}
          turnCount={turnCount}
          onEarlyFinish={handleEarlyFinish}
          onStartNewSession={handleStartFresh}
          isFinished={isFinished}
        />

        {/* Conversation Message Scroll Window */}
        <div className="flex-1 overflow-y-auto px-1 py-2 space-y-4">
          {sessionExpired ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 text-[#5C627A]">
              <AlertCircle className="w-8 h-8 text-[#E07A5F] mb-3" />
              <h3 className="text-base font-bold text-[#2B2D42] mb-1">Session Expired or Not Found</h3>
              <p className="text-xs text-[#5C627A] mb-4 max-w-sm">
                Your previous interview session is no longer active. You can start a new interview session below.
              </p>
              <Button variant="primary" size="md" onClick={handleStartFresh}>
                Start New Interview
              </Button>
            </div>
          ) : isInitializing ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 text-[#5C627A]">
              <Loader2 className="w-8 h-8 animate-spin text-[#E07A5F] mb-3" />
              <p className="text-sm font-medium">Initializing session...</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 text-[#5C627A]">
              <Compass className="w-8 h-8 text-[#E07A5F] mb-3" />
              <p className="text-sm font-medium">Your interview is ready to begin.</p>
            </div>
          ) : (
            messages.map((msg, index) => {
              // Find if this is the latest assistant message with pending confirmations from active backend state
              const isLatestAssistantWithConfirmation =
                msg.role === 'assistant' &&
                msg.pendingConfirmations &&
                msg.pendingConfirmations.length > 0 &&
                pendingConfirmations.length > 0 &&
                index === messages.findLastIndex((m) => m.role === 'assistant' && m.pendingConfirmations && m.pendingConfirmations.length > 0);

              return (
                <div key={msg.id || index} className="flex flex-col">
                  <ChatMessage
                    role={msg.role}
                    content={msg.content}
                    timestamp={msg.timestamp}
                    newlyExtracted={msg.newlyExtracted}
                    pendingConfirmations={msg.pendingConfirmations}
                    onConfirmClick={handleSendMessage}
                    onRejectClick={(conf) => {
                      setRejectionTarget(conf);
                      setDraftMessage(`No, actually for ${conf.field_name}: `);
                    }}
                    isInteractive={isLatestAssistantWithConfirmation && !isFinished}
                    isLoading={isLoading}
                  />
                  {msg.status === 'failed' && (
                    <div className="self-end text-xs text-red-500 mt-1 flex items-center gap-2">
                      <span>Failed to send.</span>
                      <button
                        onClick={() => handleSendMessage(msg.content, true)}
                        className="font-semibold underline hover:text-red-700 cursor-pointer"
                      >
                        Retry
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}

          {/* Thinking Pulse Indicator */}
          {isLoading && (
            <div className="flex gap-3 my-3">
              <div className="w-8 h-8 rounded-xl bg-[#FAF6F0] text-[#E07A5F] border border-[#E8E3DC] flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 animate-pulse" />
              </div>
              <div className="bg-white border border-[#E8E3DC] px-4 py-3 rounded-2xl rounded-tl-xs shadow-2xs text-xs text-[#5C627A] flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#E07A5F]" />
                <span>MatchLens is processing your response...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-600 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-500 font-semibold hover:underline cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Ready For Review Completion Overlay */}
        {isFinished ? (
          <div className="mt-4 p-5 bg-[#FDF0ED] border border-[#F2C0B6] rounded-2xl text-center flex flex-col items-center">
            <h3 className="text-base font-bold text-[#2B2D42] mb-1">
              {status === 'completed' ? 'Profile Confirmed!' : 'Draft Profile Ready!'}
            </h3>
            <p className="text-xs text-[#5C627A] mb-4 max-w-md">
              {status === 'completed'
                ? 'Your interview responses are finalized. You can review your confirmed profile.'
                : "You've provided sufficient details for your draft profile. Click below to review and verify your preferences."}
            </p>
            <Button
              variant="primary"
              size="md"
              onClick={() => navigate('/profile/review')}
              className="px-6 py-2.5"
            >
              Review My Profile
            </Button>
          </div>
        ) : (
          /* Fixed Message Composer */
          <div className="mt-4 pt-2">
            {rejectionTarget && (
              <div className="mb-2 p-2 bg-[#FAF6F0] border border-[#F2C0B6] rounded-xl text-xs text-[#5C627A] flex items-center justify-between">
                <span>
                  Providing correction for <strong className="text-[#2B2D42]">{rejectionTarget.field_name}</strong>
                </span>
                <button
                  onClick={() => {
                    setRejectionTarget(null);
                    setDraftMessage('');
                  }}
                  className="text-xs text-[#E07A5F] hover:underline font-semibold"
                >
                  Cancel
                </button>
              </div>
            )}
            <ChatComposer
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              disabled={isInitializing || isFinished || sessionExpired}
              initialValue={draftMessage}
              placeholder="Type your response... (Press Enter to send)"
            />
          </div>
        )}
      </Card>
    </div>
  );
};

export default InterviewPage;
