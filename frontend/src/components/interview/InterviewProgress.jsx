import { ProgressBar } from '../ui/ProgressBar';

/**
 * Topic mapping display labels for human readability.
 */
const TOPIC_LABELS = {
  basic_and_intention: 'Basic & Intention',
  core_values: 'Core Values',
  lifestyle: 'Lifestyle',
  communication: 'Communication',
  partner_expectations: 'Partner Expectations',
  dealbreakers: 'Dealbreakers',
};

const ALL_TOPICS = [
  'basic_and_intention',
  'core_values',
  'lifestyle',
  'communication',
  'partner_expectations',
  'dealbreakers',
];

/**
 * Visual progress component displaying interview completion percentage and active topic pill tags.
 */
export const InterviewProgress = ({
  percentage = 0,
  currentTopic = 'basic_and_intention',
  completedTopics = [],
}) => {
  return (
    <div className="w-full bg-white p-4 rounded-2xl border border-[#E8E3DC] shadow-2xs mb-4">
      <ProgressBar
        progress={percentage}
        label="Onboarding Progress"
        stepText={`${Math.round(percentage)}%`}
      />

      {/* Topic Pill Badges */}
      <div className="mt-3.5 flex flex-wrap gap-1.5 items-center justify-between">
        {ALL_TOPICS.map((topicKey) => {
          const isCompleted = completedTopics.includes(topicKey);
          const isCurrent = currentTopic === topicKey;

          let badgeStyle = 'bg-[#FAF6F0] text-[#A0A4B8] border-[#E8E3DC]'; // Pending
          if (isCompleted) {
            badgeStyle = 'bg-[#EBF7F0] text-[#2A7B4C] border-[#C2E8D0] font-semibold';
          } else if (isCurrent) {
            badgeStyle = 'bg-[#FDF0ED] text-[#E07A5F] border-[#F2C0B6] font-bold shadow-2xs';
          }

          return (
            <span
              key={topicKey}
              className={`text-[11px] px-2.5 py-1 rounded-lg border transition-all ${badgeStyle}`}
            >
              {TOPIC_LABELS[topicKey] || topicKey}
            </span>
          );
        })}
      </div>
    </div>
  );
};

export default InterviewProgress;
