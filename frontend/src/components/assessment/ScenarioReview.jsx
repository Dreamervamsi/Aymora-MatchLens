import React, { useState } from 'react';
import { User, Heart, CheckCircle, Edit3 } from 'lucide-react';
import { Card, Button, Badge } from '../ui';

const KNOWN_TITLE_MAP = {
  conflict_resolution_01: 'Handling disagreement after a stressful day',
  social_energy_01: 'Weekend downtime preferences',
  financial_planning_01: 'Approach to joint budgeting and major expenses',
};

const formatOptionLabel = (str) => {
  if (!str) return 'Not answered';
  return str.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

export const ScenarioReview = ({
  summaryData = {},
  selectedScenarioIds = [],
  confirming,
  onConfirmAssessment,
  onCorrectResponse,
  correctingState = {},
  isAlreadyCompleted = false,
  onNavigateToMatches,
}) => {
  const [editingKey, setEditingKey] = useState(null); // `${scenarioId}_${target}`
  const [editValue, setEditValue] = useState('');
  const [correctionError, setCorrectionError] = useState(null);

  const scenarioIds = selectedScenarioIds.length > 0 ? selectedScenarioIds : Object.keys(summaryData);

  const handleStartCorrection = (scenarioId, target, currentValue) => {
    setEditingKey(`${scenarioId}_${target}`);
    setEditValue(currentValue || '');
    setCorrectionError(null);
  };

  const handleSaveCorrection = async (scenarioId, target) => {
    if (!editValue.trim()) return;
    const isCorrectingThis = correctingState[`${scenarioId}_${target}`] || correctingState[scenarioId];
    if (isCorrectingThis) return;

    setCorrectionError(null);
    const result = await onCorrectResponse(scenarioId, target, editValue.trim());

    if (result && result.success === false) {
      setCorrectionError(result.error || 'Correction failed.');
    } else {
      setEditingKey(null);
      setEditValue('');
      setCorrectionError(null);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6 md:p-8 border-[#F2C0B6] bg-[#FDF0ED]/30 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center shrink-0">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <Badge variant="rose" className="mb-2">
              All Scenarios Answered
            </Badge>
            <h2 className="text-xl font-bold text-[#2B2D42] tracking-tight">
              Review Your Assessment
            </h2>
            <p className="text-sm text-[#5C627A] mt-1 leading-relaxed">
              Compare your personal behavior against your ideal partner expectations for each scenario before final confirmation.
            </p>
          </div>
        </div>
      </Card>

      {/* Scenario Responses Comparison Cards */}
      {scenarioIds.map((sid, idx) => {
        const scenarioResponses = summaryData[sid] || {};
        const title = KNOWN_TITLE_MAP[sid] || `Scenario ${idx + 1}: ${sid}`;
        const selfResp = scenarioResponses.self_response;
        const partnerResp = scenarioResponses.partner_expectation;

        const isEditingSelf = editingKey === `${sid}_self_behavior`;
        const isEditingPartner = editingKey === `${sid}_partner_expectation`;
        const isCorrectingSelf = correctingState[`${sid}_self_behavior`] || (isEditingSelf && correctingState[sid]);
        const isCorrectingPartner = correctingState[`${sid}_partner_expectation`] || (isEditingPartner && correctingState[sid]);

        return (
          <Card key={sid} className="p-6 md:p-8 border-[#E8E3DC] shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-[#E8E3DC]/60 mb-6">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-[#E07A5F]">
                  Scenario {idx + 1}
                </span>
                <h3 className="text-lg font-bold text-[#2B2D42]">{title}</h3>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              {/* Self Behavior Column */}
              <div className="p-4 rounded-2xl border border-[#F2C0B6] bg-[#FDF0ED]/40">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-[#E07A5F]" />
                    <span className="text-xs font-bold uppercase tracking-wider text-[#2B2D42]">
                      Your Behavior
                    </span>
                  </div>
                  {!isAlreadyCompleted && !isEditingSelf && (
                    <button
                      type="button"
                      onClick={() => handleStartCorrection(sid, 'self_behavior', selfResp)}
                      className="text-xs font-semibold text-[#E07A5F] hover:underline flex items-center gap-1"
                    >
                      <Edit3 className="w-3 h-3" /> Correct
                    </button>
                  )}
                </div>

                {isEditingSelf ? (
                  <div className="space-y-2 mt-2">
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      placeholder="Type option, e.g. discuss_immediately"
                      className="w-full px-3 py-2 rounded-xl border border-[#E8E3DC] text-xs focus:outline-none focus:ring-2 focus:ring-[#E07A5F]"
                    />
                    {correctionError && (
                      <p className="text-xs text-[#E07A5F]">{correctionError}</p>
                    )}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleSaveCorrection(sid, 'self_behavior')}
                        disabled={isCorrectingSelf}
                      >
                        {isCorrectingSelf ? 'Saving...' : 'Save'}
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => {
                          setEditingKey(null);
                          setCorrectionError(null);
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm font-semibold text-[#2B2D42]">
                    {formatOptionLabel(selfResp)}
                  </p>
                )}
              </div>

              {/* Partner Expectation Column */}
              <div className="p-4 rounded-2xl border border-[#3D5A80]/30 bg-[#3D5A80]/5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Heart className="w-4 h-4 text-[#3D5A80]" />
                    <span className="text-xs font-bold uppercase tracking-wider text-[#2B2D42]">
                      Your Ideal Partner
                    </span>
                  </div>
                  {!isAlreadyCompleted && !isEditingPartner && (
                    <button
                      type="button"
                      onClick={() => handleStartCorrection(sid, 'partner_expectation', partnerResp)}
                      className="text-xs font-semibold text-[#3D5A80] hover:underline flex items-center gap-1"
                    >
                      <Edit3 className="w-3 h-3" /> Correct
                    </button>
                  )}
                </div>

                {isEditingPartner ? (
                  <div className="space-y-2 mt-2">
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      placeholder="Type option, e.g. cool_down_first"
                      className="w-full px-3 py-2 rounded-xl border border-[#E8E3DC] text-xs focus:outline-none focus:ring-2 focus:ring-[#3D5A80]"
                    />
                    {correctionError && (
                      <p className="text-xs text-[#E07A5F]">{correctionError}</p>
                    )}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleSaveCorrection(sid, 'partner_expectation')}
                        disabled={isCorrectingPartner}
                      >
                        {isCorrectingPartner ? 'Saving...' : 'Save'}
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => {
                          setEditingKey(null);
                          setCorrectionError(null);
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm font-semibold text-[#2B2D42]">
                    {formatOptionLabel(partnerResp)}
                  </p>
                )}
              </div>
            </div>
          </Card>
        );
      })}

      {/* Confirmation CTA Bar */}
      <div className="pt-6 border-t border-[#E8E3DC] flex flex-col sm:flex-row items-center justify-between gap-4">
        {isAlreadyCompleted ? (
          <Button
            variant="primary"
            icon={CheckCircle}
            onClick={onNavigateToMatches}
            className="w-full sm:w-auto shadow-md"
          >
            Discover My Matches
          </Button>
        ) : (
          <Button
            variant="primary"
            icon={CheckCircle}
            onClick={onConfirmAssessment}
            disabled={confirming}
            className="w-full sm:w-auto py-3.5 px-8 shadow-md"
          >
            {confirming ? 'Confirming Assessment...' : 'Confirm My Assessment'}
          </Button>
        )}
      </div>
    </div>
  );
};

export default ScenarioReview;
