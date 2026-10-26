import React, { useState, useEffect } from 'react';
import { CheckCircle2, Send, HelpCircle, AlertCircle } from 'lucide-react';
import { Card, Button } from '../ui';

export const ScenarioResponseForm = ({
  allowedOptions,
  optionDescriptions = {},
  unresolvedClarification,
  submitting,
  onSubmitTurn,
}) => {
  const [selectedOption, setSelectedOption] = useState('');
  const [customInput, setCustomInput] = useState('');
  const [isCustomMode, setIsCustomMode] = useState(false);

  // Reset form when allowed options change (new scenario loaded)
  useEffect(() => {
    setSelectedOption('');
    setCustomInput('');
    setIsCustomMode(false);
  }, [allowedOptions]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (submitting) return;

    const valueToSubmit = isCustomMode ? customInput.trim() : selectedOption;
    if (!valueToSubmit) return;

    onSubmitTurn(valueToSubmit);
  };

  const handleClarificationChoice = (choice) => {
    if (submitting) return;
    onSubmitTurn(choice);
  };

  // 1. Clarification Required View
  if (unresolvedClarification) {
    const { clarification_prompt, proposed_option, raw_input } = unresolvedClarification;
    const confirmButtonLabel = submitting
      ? 'Confirming...'
      : proposed_option
        ? `Yes, I meant "${proposed_option.replace(/_/g, ' ')}"`
        : 'Yes, that is correct';

    const safePromptText =
      clarification_prompt ||
      (proposed_option
        ? `Did you mean '${proposed_option}'?`
        : 'Please clarify or rephrase your response.');

    return (
      <Card className="p-6 md:p-8 mb-6 border-[#F2C0B6] bg-[#FDF0ED]/30 shadow-sm">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center shrink-0">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-[#2B2D42]">Clarification Required</h3>
            {raw_input && (
              <p className="text-xs text-[#5C627A] mt-0.5">
                Your previous response: <span className="italic font-medium text-[#2B2D42]">&quot;{raw_input}&quot;</span>
              </p>
            )}
          </div>
        </div>

        <p className="text-sm font-semibold text-[#2B2D42] mb-6 bg-white p-4 rounded-xl border border-[#E8E3DC]">
          {safePromptText}
        </p>

        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="primary"
            icon={CheckCircle2}
            disabled={submitting}
            onClick={() => handleClarificationChoice('yes')}
            className="flex-1"
          >
            {confirmButtonLabel}
          </Button>
          <Button
            variant="secondary"
            disabled={submitting}
            onClick={() => setIsCustomMode(true)}
            className="flex-1"
          >
            No, let me rephrase
          </Button>
        </div>

        {isCustomMode && (
          <form onSubmit={handleSubmit} className="mt-4 pt-4 border-t border-[#E8E3DC]">
            <label className="block text-xs font-semibold text-[#5C627A] mb-2 uppercase tracking-wider">
              Type your intended response:
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder="Type your response..."
                className="flex-1 px-4 py-2.5 rounded-xl border border-[#E8E3DC] text-sm focus:outline-none focus:ring-2 focus:ring-[#E07A5F] focus:border-transparent"
                disabled={submitting}
              />
              <Button variant="primary" icon={Send} disabled={submitting || !customInput.trim()}>
                Submit
              </Button>
            </div>
          </form>
        )}
      </Card>
    );
  }

  // 2. Standard Multiple Choice Option Selection
  return (
    <Card className="p-6 md:p-8 mb-6 border-[#E8E3DC] shadow-sm">
      <form onSubmit={handleSubmit}>
        <h3 className="text-sm font-bold text-[#2B2D42] uppercase tracking-wider mb-4">
          Select the option that best applies:
        </h3>

        <div className="space-y-3 mb-6">
          {allowedOptions && allowedOptions.length > 0 ? (
            allowedOptions.map((optKey) => {
              const isSelected = selectedOption === optKey && !isCustomMode;
              const desc = optionDescriptions[optKey];
              const labelText = optKey.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

              return (
                <div
                  key={optKey}
                  onClick={() => {
                    if (submitting) return;
                    setSelectedOption(optKey);
                    setIsCustomMode(false);
                  }}
                  className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex items-start gap-3.5 ${
                    isSelected
                      ? 'border-[#E07A5F] bg-[#FDF0ED] shadow-sm ring-1 ring-[#E07A5F]'
                      : 'border-[#E8E3DC] bg-white hover:border-[#F2C0B6] hover:bg-[#FAF6F0]'
                  }`}
                >
                  <div className="pt-0.5 shrink-0">
                    <div
                      className={`w-5 h-5 rounded-full border flex items-center justify-center transition-colors ${
                        isSelected
                          ? 'border-[#E07A5F] bg-[#E07A5F] text-white'
                          : 'border-[#A0A4B8] bg-white'
                      }`}
                    >
                      {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-bold text-[#2B2D42]">{labelText}</div>
                    {desc && <div className="text-xs text-[#5C627A] mt-1 leading-relaxed">{desc}</div>}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-4 bg-[#FAF6F0] rounded-xl text-xs text-[#5C627A] flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-[#E07A5F]" />
              <span>No pre-defined options available. Please type your response below.</span>
            </div>
          )}
        </div>

        {/* Option to type custom natural language response if desired */}
        <div className="mb-6 pt-4 border-t border-[#E8E3DC]/60">
          <button
            type="button"
            onClick={() => setIsCustomMode(!isCustomMode)}
            className="text-xs font-semibold text-[#E07A5F] hover:underline flex items-center gap-1"
          >
            {isCustomMode ? '← Back to option selection' : 'Or respond in your own words...'}
          </button>

          {isCustomMode && (
            <div className="mt-3">
              <textarea
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder="Describe how you or your partner would respond in this scenario..."
                rows={3}
                className="w-full p-3.5 rounded-xl border border-[#E8E3DC] text-sm focus:outline-none focus:ring-2 focus:ring-[#E07A5F] focus:border-transparent"
                disabled={submitting}
              />
            </div>
          )}
        </div>

        <Button
          type="submit"
          variant="primary"
          icon={Send}
          disabled={submitting || (isCustomMode ? !customInput.trim() : !selectedOption)}
          className="w-full py-3 shadow-md"
        >
          {submitting ? 'Submitting Response...' : 'Submit Choice & Proceed'}
        </Button>
      </form>
    </Card>
  );
};

export default ScenarioResponseForm;
