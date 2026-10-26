import React from 'react';
import { User, Heart } from 'lucide-react';
import { Card, Badge } from '../ui';

export const ScenarioCard = ({ scenarioDefinition, currentStage }) => {
  if (!scenarioDefinition) return null;

  const { title, description, self_prompt, partner_prompt } = scenarioDefinition;
  const isSelf = currentStage === 'self_behavior';

  return (
    <Card className="p-6 md:p-8 mb-6 border-[#E8E3DC] shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <Badge variant="stone" className="text-xs font-semibold uppercase tracking-wider">
          {scenarioDefinition.target_dimension ? scenarioDefinition.target_dimension.replace(/_/g, ' ') : 'Scenario'}
        </Badge>
      </div>

      <h2 className="text-xl sm:text-2xl font-bold text-[#2B2D42] mb-3 tracking-tight">
        {title}
      </h2>

      {description && (
        <p className="text-sm text-[#5C627A] leading-relaxed mb-6 bg-[#FAF6F0] p-4 rounded-xl border border-[#E8E3DC]/60">
          {description}
        </p>
      )}

      {/* Active Perspective Prompt */}
      <div className="p-4 sm:p-5 rounded-2xl border transition-all duration-200 bg-[#FDF0ED]/50 border-[#F2C0B6]">
        <div className="flex items-center gap-2.5 mb-2">
          {isSelf ? (
            <div className="w-8 h-8 rounded-lg bg-[#E07A5F] text-white flex items-center justify-center shrink-0">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-lg bg-[#3D5A80] text-white flex items-center justify-center shrink-0">
              <Heart className="w-4 h-4" />
            </div>
          )}
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#2B2D42]">
              {isSelf ? 'Perspective A — Your Behavior' : 'Perspective B — Your Ideal Partner'}
            </span>
            <p className="text-xs text-[#5C627A]">
              {isSelf
                ? 'How would you personally respond in this situation?'
                : 'How would you want your ideal partner to respond in this situation?'}
            </p>
          </div>
        </div>

        <p className="text-sm font-semibold text-[#2B2D42] mt-3 pl-10">
          {isSelf
            ? (self_prompt || 'What would you most likely do in this situation?')
            : (partner_prompt || 'What would you prefer or be comfortable with your partner doing?')}
        </p>
      </div>
    </Card>
  );
};

export default ScenarioCard;
