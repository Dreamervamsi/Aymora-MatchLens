import React from 'react';
import { ProgressBar } from '../ui';

export const ScenarioProgress = ({ progress, currentStage }) => {
  if (!progress) return null;

  const { current_scenario_index = 0, total_scenarios = 3, percentage = 0 } = progress;

  const stageLabel = () => {
    if (currentStage === 'self_behavior') return 'Part A: Your Behavior';
    if (currentStage === 'partner_expectation') return 'Part B: Ideal Partner';
    if (currentStage === 'review') return 'Reviewing Responses';
    if (currentStage === 'completed') return 'Assessment Complete';
    return '';
  };

  return (
    <div className="bg-white rounded-2xl border border-[#E8E3DC] p-4 sm:p-5 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-[#E07A5F]">
            Scenario {Math.min(current_scenario_index + 1, total_scenarios)} of {total_scenarios}
          </span>
          {stageLabel() && (
            <span className="ml-2 text-xs font-medium text-[#5C627A]">
              • {stageLabel()}
            </span>
          )}
        </div>
        <span className="text-xs font-semibold text-[#2B2D42]">
          {Math.round(percentage)}% Completed
        </span>
      </div>
      <ProgressBar value={percentage} className="h-2.5" />
    </div>
  );
};

export default ScenarioProgress;
