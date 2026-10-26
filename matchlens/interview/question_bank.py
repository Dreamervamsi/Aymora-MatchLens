from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from matchlens.interview.models import InterviewTopic


@dataclass
class QuestionDefinition:
    """
    Structured definition for a deterministic interview question.
    """
    question_id: str
    topic: InterviewTopic
    question_text: str
    target_category: str  # 'self_attributes', 'partner_preferences', or 'dealbreakers'
    field_key: Optional[str] = None
    expected_fields: List[str] = field(default_factory=list)
    permitted_values: Optional[List[Any]] = None


# Detailed structured question definitions mapped by question_id or (topic_str, field_key)
STRUCTURED_QUESTION_BANK: Dict[str, QuestionDefinition] = {
    # Basic & Intention
    "basic_and_intention.default": QuestionDefinition(
        question_id="basic_and_intention.default",
        topic=InterviewTopic.BASIC_AND_INTENTION,
        question_text="To kick off our conversation, could you tell me a bit about yourself—like your age, gender, and what kind of relationship you're hoping to find?",
        target_category="self_attributes",
        expected_fields=["age", "gender", "relationship_intent"],
        permitted_values=["long_term", "marriage", "casual", "friendship", "man", "woman", "non-binary"],
    ),
    "basic_and_intention.age": QuestionDefinition(
        question_id="basic_and_intention.age",
        topic=InterviewTopic.BASIC_AND_INTENTION,
        field_key="age",
        question_text="How old are you?",
        target_category="self_attributes",
        expected_fields=["age"],
    ),
    "basic_and_intention.gender": QuestionDefinition(
        question_id="basic_and_intention.gender",
        topic=InterviewTopic.BASIC_AND_INTENTION,
        field_key="gender",
        question_text="What is your gender identity?",
        target_category="self_attributes",
        expected_fields=["gender"],
        permitted_values=["man", "woman", "non-binary"],
    ),
    "basic_and_intention.relationship_intent": QuestionDefinition(
        question_id="basic_and_intention.relationship_intent",
        topic=InterviewTopic.BASIC_AND_INTENTION,
        field_key="relationship_intent",
        question_text="What type of relationship are you looking for right now (e.g., long-term, marriage, casual, or friendship)?",
        target_category="self_attributes",
        expected_fields=["relationship_intent"],
        permitted_values=["long_term", "marriage", "casual", "friendship"],
    ),

    # Core Values
    "core_values.default": QuestionDefinition(
        question_id="core_values.default",
        topic=InterviewTopic.CORE_VALUES,
        question_text="What core values or principles matter most to you in life and in a partner?",
        target_category="self_attributes",
        expected_fields=["core_values", "desired_values"],
    ),
    "core_values.core_values": QuestionDefinition(
        question_id="core_values.core_values",
        topic=InterviewTopic.CORE_VALUES,
        field_key="core_values",
        question_text="Could you share two or three core values that guide your life decisions?",
        target_category="self_attributes",
        expected_fields=["core_values"],
    ),
    "core_values.desired_values": QuestionDefinition(
        question_id="core_values.desired_values",
        topic=InterviewTopic.CORE_VALUES,
        field_key="desired_values",
        question_text="What key values do you hope to share with your partner?",
        target_category="partner_preferences",
        expected_fields=["desired_values"],
    ),

    # Lifestyle
    "lifestyle.default": QuestionDefinition(
        question_id="lifestyle.default",
        topic=InterviewTopic.LIFESTYLE,
        question_text="Tell me about your lifestyle—for example, your habits around smoking, drinking, exercise, or family plans.",
        target_category="self_attributes",
        expected_fields=["smoking", "drinking", "exercise", "has_children", "wants_children"],
        permitted_values=["never", "socially", "regularly", "daily", "weekly", "rarely", "yes", "no", "open", "maybe"],
    ),
    "lifestyle.smoking": QuestionDefinition(
        question_id="lifestyle.smoking",
        topic=InterviewTopic.LIFESTYLE,
        field_key="smoking",
        question_text="Do you smoke (never, socially, or regularly)?",
        target_category="self_attributes",
        expected_fields=["smoking"],
        permitted_values=["never", "socially", "regularly"],
    ),
    "lifestyle.drinking": QuestionDefinition(
        question_id="lifestyle.drinking",
        topic=InterviewTopic.LIFESTYLE,
        field_key="drinking",
        question_text="Do you drink alcohol (never, socially, or regularly)?",
        target_category="self_attributes",
        expected_fields=["drinking"],
        permitted_values=["never", "socially", "regularly"],
    ),
    "lifestyle.exercise": QuestionDefinition(
        question_id="lifestyle.exercise",
        topic=InterviewTopic.LIFESTYLE,
        field_key="exercise",
        question_text="How active are you with exercise (daily, weekly, rarely, or never)?",
        target_category="self_attributes",
        expected_fields=["exercise"],
        permitted_values=["daily", "weekly", "rarely", "never"],
    ),
    "lifestyle.has_children": QuestionDefinition(
        question_id="lifestyle.has_children",
        topic=InterviewTopic.LIFESTYLE,
        field_key="has_children",
        question_text="Do you currently have children?",
        target_category="self_attributes",
        expected_fields=["has_children"],
        permitted_values=[True, False],
    ),
    "lifestyle.wants_children": QuestionDefinition(
        question_id="lifestyle.wants_children",
        topic=InterviewTopic.LIFESTYLE,
        field_key="wants_children",
        question_text="What are your thoughts on having or raising children (yes, no, open, or maybe)?",
        target_category="self_attributes",
        expected_fields=["wants_children"],
        permitted_values=["yes", "no", "open", "maybe"],
    ),

    # Communication & Conflict Resolution
    "communication.default": QuestionDefinition(
        question_id="communication.default",
        topic=InterviewTopic.COMMUNICATION,
        question_text="How do you prefer to communicate and resolve disagreements when conflict arises in a relationship?",
        target_category="self_attributes",
        expected_fields=["communication_style", "conflict_resolution", "contact_frequency"],
        permitted_values=["direct", "gentle", "expressive", "analytical", "discuss_immediately", "cool_down_first", "written_first", "frequent", "daily_check_in", "as_needed"],
    ),
    "communication.communication_style": QuestionDefinition(
        question_id="communication.communication_style",
        topic=InterviewTopic.COMMUNICATION,
        field_key="communication_style",
        question_text="How would you describe your communication style (e.g., direct, gentle, expressive, or analytical)?",
        target_category="self_attributes",
        expected_fields=["communication_style"],
        permitted_values=["direct", "gentle", "expressive", "analytical"],
    ),
    "communication.conflict_resolution": QuestionDefinition(
        question_id="communication.conflict_resolution",
        topic=InterviewTopic.COMMUNICATION,
        field_key="conflict_resolution",
        question_text="When a disagreement comes up, do you prefer discussing it immediately, cooling down first, or writing thoughts down?",
        target_category="self_attributes",
        expected_fields=["conflict_resolution"],
        permitted_values=["discuss_immediately", "cool_down_first", "written_first"],
    ),
    "communication.contact_frequency": QuestionDefinition(
        question_id="communication.contact_frequency",
        topic=InterviewTopic.COMMUNICATION,
        field_key="contact_frequency",
        question_text="How often do you like to stay in touch with your partner throughout the day or week?",
        target_category="self_attributes",
        expected_fields=["contact_frequency"],
        permitted_values=["frequent", "daily_check_in", "as_needed"],
    ),

    # Partner Expectations
    "partner_expectations.default": QuestionDefinition(
        question_id="partner_expectations.default",
        topic=InterviewTopic.PARTNER_EXPECTATIONS,
        question_text="What specific preferences or age range do you have for a prospective partner?",
        target_category="partner_preferences",
        expected_fields=["acceptable_genders", "min_age", "max_age", "acceptable_smoking", "acceptable_drinking", "desired_wants_children", "desired_communication_styles"],
    ),
    "partner_expectations.acceptable_genders": QuestionDefinition(
        question_id="partner_expectations.acceptable_genders",
        topic=InterviewTopic.PARTNER_EXPECTATIONS,
        field_key="acceptable_genders",
        question_text="Which gender(s) are you open to dating?",
        target_category="partner_preferences",
        expected_fields=["acceptable_genders"],
        permitted_values=["man", "woman", "non-binary", "any"],
    ),
    "partner_expectations.min_age": QuestionDefinition(
        question_id="partner_expectations.min_age",
        topic=InterviewTopic.PARTNER_EXPECTATIONS,
        field_key="min_age",
        question_text="What is the age range you are comfortable dating?",
        target_category="partner_preferences",
        expected_fields=["min_age", "max_age"],
    ),
    "partner_expectations.acceptable_smoking": QuestionDefinition(
        question_id="partner_expectations.acceptable_smoking",
        topic=InterviewTopic.PARTNER_EXPECTATIONS,
        field_key="acceptable_smoking",
        question_text="What are your preferences regarding a partner's smoking habits?",
        target_category="partner_preferences",
        expected_fields=["acceptable_smoking"],
        permitted_values=["never", "socially", "regularly"],
    ),
    "partner_expectations.acceptable_drinking": QuestionDefinition(
        question_id="partner_expectations.acceptable_drinking",
        topic=InterviewTopic.PARTNER_EXPECTATIONS,
        field_key="acceptable_drinking",
        question_text="What are your preferences regarding a partner's drinking habits?",
        target_category="partner_preferences",
        expected_fields=["acceptable_drinking"],
        permitted_values=["never", "socially", "regularly"],
    ),
    "partner_expectations.desired_wants_children": QuestionDefinition(
        question_id="partner_expectations.desired_wants_children",
        topic=InterviewTopic.PARTNER_EXPECTATIONS,
        field_key="desired_wants_children",
        question_text="What position on children would you hope your partner has?",
        target_category="partner_preferences",
        expected_fields=["desired_wants_children"],
        permitted_values=["yes", "no", "open", "maybe"],
    ),
    "partner_expectations.desired_communication_styles": QuestionDefinition(
        question_id="partner_expectations.desired_communication_styles",
        topic=InterviewTopic.PARTNER_EXPECTATIONS,
        field_key="desired_communication_styles",
        question_text="What communication style do you find most comfortable in a partner?",
        target_category="partner_preferences",
        expected_fields=["desired_communication_styles"],
        permitted_values=["direct", "gentle", "expressive", "analytical"],
    ),

    # Dealbreakers
    "dealbreakers.default": QuestionDefinition(
        question_id="dealbreakers.default",
        topic=InterviewTopic.DEALBREAKERS,
        question_text="Are there any strict non-negotiables or dealbreakers that would make a match completely incompatible for you?",
        target_category="dealbreakers",
        expected_fields=["smoking_dealbreaker", "children_dealbreaker", "strict_age_range", "strict_gender_match", "strict_intention_match"],
    ),
    "dealbreakers.dealbreakers": QuestionDefinition(
        question_id="dealbreakers.dealbreakers",
        topic=InterviewTopic.DEALBREAKERS,
        field_key="dealbreakers",
        question_text="Is there anything specific that is an absolute dealbreaker for you in a relationship?",
        target_category="dealbreakers",
        expected_fields=["smoking_dealbreaker", "children_dealbreaker"],
    ),
}

# Standard legacy string map for backwards compatibility
QUESTION_BANK: Dict[str, str] = {
    k: v.question_text for k, v in STRUCTURED_QUESTION_BANK.items()
}


def get_bank_definition(topic: InterviewTopic, field_key: Optional[str] = None) -> QuestionDefinition:
    """
    Retrieves structured QuestionDefinition from bank given topic and optional field key.
    """
    topic_str = topic.value if isinstance(topic, InterviewTopic) else str(topic)
    
    if field_key:
        key = f"{topic_str}.{field_key}"
        if key in STRUCTURED_QUESTION_BANK:
            return STRUCTURED_QUESTION_BANK[key]
            
    default_key = f"{topic_str}.default"
    if default_key in STRUCTURED_QUESTION_BANK:
        return STRUCTURED_QUESTION_BANK[default_key]
        
    fallback_key = "basic_and_intention.default"
    return STRUCTURED_QUESTION_BANK[fallback_key]


def get_bank_question(topic: InterviewTopic, field_key: Optional[str] = None) -> tuple[str, str]:
    """
    Retrieves a deterministic question from the bank given a topic and optional field key.
    Returns a tuple of (question_id, question_text).
    """
    defn = get_bank_definition(topic, field_key)
    return defn.question_id, defn.question_text

