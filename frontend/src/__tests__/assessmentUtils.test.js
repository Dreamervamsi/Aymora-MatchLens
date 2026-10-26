import { describe, it, expect } from 'vitest';
import { isAssessmentPersistedInProfile, CANONICAL_MVP_SCENARIO_IDS } from '../utils/assessmentUtils';

describe('assessmentUtils — Strict Assessment Completion Verification (Phase 7.5 Improvement A)', () => {
  const completeThreeScenariosProfile = {
    user_id: 'alex_101',
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
      {
        scenario_id: 'financial_planning_01',
        target_dimension: 'core_values',
        normalized_preference: 'balanced_spending',
        expected_partner_preference: 'balanced_spending',
      },
    ],
  };

  it('1. Returns false when profile has zero persisted scenarios', () => {
    const profile = { user_id: 'alex_101', scenario_responses: [] };
    expect(isAssessmentPersistedInProfile(profile)).toBe(false);
  });

  it('2. Returns false when profile has only one persisted scenario out of 3 required', () => {
    const profile = {
      user_id: 'alex_101',
      scenario_responses: [completeThreeScenariosProfile.scenario_responses[0]],
    };
    expect(isAssessmentPersistedInProfile(profile)).toBe(false);
  });

  it('3. Returns false when profile has two persisted scenarios out of 3 required', () => {
    const profile = {
      user_id: 'alex_101',
      scenario_responses: [
        completeThreeScenariosProfile.scenario_responses[0],
        completeThreeScenariosProfile.scenario_responses[1],
      ],
    };
    expect(isAssessmentPersistedInProfile(profile)).toBe(false);
  });

  it('4. Returns true when profile has all 3 complete scenarios with self behavior AND partner expectation', () => {
    expect(isAssessmentPersistedInProfile(completeThreeScenariosProfile)).toBe(true);
  });

  it('5. Returns false when all 3 scenarios exist but one is missing partner expectation', () => {
    const profile = {
      user_id: 'alex_101',
      scenario_responses: [
        completeThreeScenariosProfile.scenario_responses[0],
        completeThreeScenariosProfile.scenario_responses[1],
        {
          scenario_id: 'financial_planning_01',
          target_dimension: 'core_values',
          normalized_preference: 'balanced_spending',
          expected_partner_preference: null, // MISSING PARTNER EXPECTATION
        },
      ],
    };
    expect(isAssessmentPersistedInProfile(profile)).toBe(false);
  });

  it('6. Returns false when all 3 scenarios exist but one is missing self behavior', () => {
    const profile = {
      user_id: 'alex_101',
      scenario_responses: [
        completeThreeScenariosProfile.scenario_responses[0],
        completeThreeScenariosProfile.scenario_responses[1],
        {
          scenario_id: 'financial_planning_01',
          target_dimension: 'core_values',
          normalized_preference: null, // MISSING SELF BEHAVIOR
          expected_partner_preference: 'balanced_spending',
        },
      ],
    };
    expect(isAssessmentPersistedInProfile(profile)).toBe(false);
  });

  it('7. Returns false when session is completed in memory/sessionStorage but profile persisted data is incomplete', () => {
    const incompleteProfile = {
      user_id: 'alex_101',
      scenario_responses: [completeThreeScenariosProfile.scenario_responses[0]],
    };
    const completedSessionData = {
      assessment_id: 'assess_999',
      status: 'completed',
      current_stage: 'completed',
      selected_scenario_ids: CANONICAL_MVP_SCENARIO_IDS,
    };
    expect(isAssessmentPersistedInProfile(incompleteProfile, completedSessionData)).toBe(false);
  });

  it('8. Returns false when assessmentId is stale or belongs to a different assessment session', () => {
    const wrongSessionData = {
      assessment_id: 'stale_123',
      selected_scenario_ids: ['custom_scenario_X', 'custom_scenario_Y'],
    };
    expect(isAssessmentPersistedInProfile(completeThreeScenariosProfile, wrongSessionData)).toBe(false);
  });

  it('9. Returns true when assessment ID is missing or null, but complete persisted data exists in profile', () => {
    expect(isAssessmentPersistedInProfile(completeThreeScenariosProfile, null)).toBe(true);
  });

  it('10. Returns false when assessment belongs to another user (ownership check)', () => {
    const otherUserAssessmentData = {
      assessment_id: 'assess_456',
      user_id: 'other_user_202',
      selected_scenario_ids: CANONICAL_MVP_SCENARIO_IDS,
    };
    expect(
      isAssessmentPersistedInProfile(completeThreeScenariosProfile, otherUserAssessmentData, 'alex_101')
    ).toBe(false);
  });

  it('11. Returns false when profile belongs to another user than expectedUserId', () => {
    expect(
      isAssessmentPersistedInProfile(completeThreeScenariosProfile, null, 'different_user_999')
    ).toBe(false);
  });

  it('12. Rejects arbitrary non-empty or poorly formed response arrays', () => {
    const arbitraryProfile = {
      user_id: 'alex_101',
      scenario_responses: [
        { foo: 'bar' },
        { scenario_id: 'random_id', preference: 'something' },
      ],
    };
    expect(isAssessmentPersistedInProfile(arbitraryProfile)).toBe(false);
  });
});
