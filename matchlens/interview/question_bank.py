from typing import Dict, Optional
from matchlens.interview.models import InterviewTopic

# Standard deterministic questions mapped by (topic, missing_field_key)
QUESTION_BANK: Dict[str, str] = {
    # Basic & Intention
    "basic_and_intention.default": "To kick off our conversation, could you tell me a bit about yourself—like your age, gender, and what kind of relationship you're hoping to find?",
    "basic_and_intention.age": "How old are you?",
    "basic_and_intention.gender": "What is your gender identity?",
    "basic_and_intention.relationship_intent": "What type of relationship are you looking for right now (e.g., long-term, marriage, casual, or friendship)?",

    # Core Values
    "core_values.default": "What core values or principles matter most to you in life and in a partner?",
    "core_values.core_values": "Could you share two or three core values that guide your life decisions?",
    "core_values.desired_values": "What key values do you hope to share with your partner?",

    # Lifestyle
    "lifestyle.default": "Tell me about your lifestyle—for example, your habits around smoking, drinking, exercise, or family plans.",
    "lifestyle.smoking": "Do you smoke (never, socially, or regularly)?",
    "lifestyle.drinking": "Do you drink alcohol (never, socially, or regularly)?",
    "lifestyle.exercise": "How active are you with exercise (daily, weekly, rarely, or never)?",
    "lifestyle.has_children": "Do you currently have children?",
    "lifestyle.wants_children": "What are your thoughts on having or raising children (yes, no, open, or maybe)?",

    # Communication & Conflict Resolution
    "communication.default": "How do you prefer to communicate and resolve disagreements when conflict arises in a relationship?",
    "communication.communication_style": "How would you describe your communication style (e.g., direct, gentle, expressive, or analytical)?",
    "communication.conflict_resolution": "When a disagreement comes up, do you prefer discussing it immediately, cooling down first, or writing thoughts down?",
    "communication.contact_frequency": "How often do you like to stay in touch with your partner throughout the day or week?",

    # Partner Expectations
    "partner_expectations.default": "What specific preferences or age range do you have for a prospective partner?",
    "partner_expectations.acceptable_genders": "Which gender(s) are you open to dating?",
    "partner_expectations.min_age": "What is the age range you are comfortable dating?",
    "partner_expectations.acceptable_smoking": "What are your preferences regarding a partner's smoking habits?",
    "partner_expectations.acceptable_drinking": "What are your preferences regarding a partner's drinking habits?",
    "partner_expectations.desired_wants_children": "What position on children would you hope your partner has?",
    "partner_expectations.desired_communication_styles": "What communication style do you find most comfortable in a partner?",

    # Dealbreakers
    "dealbreakers.default": "Are there any strict non-negotiables or dealbreakers that would make a match completely incompatible for you?",
    "dealbreakers.dealbreakers": "Is there anything specific that is an absolute dealbreaker for you in a relationship?",
}


def get_bank_question(topic: InterviewTopic, field_key: Optional[str] = None) -> tuple[str, str]:
    """
    Retrieves a deterministic question from the bank given a topic and optional field key.
    Returns a tuple of (question_id, question_text).
    """
    topic_str = topic.value if isinstance(topic, InterviewTopic) else str(topic)
    
    if field_key:
        key = f"{topic_str}.{field_key}"
        if key in QUESTION_BANK:
            return key, QUESTION_BANK[key]
            
    default_key = f"{topic_str}.default"
    if default_key in QUESTION_BANK:
        return default_key, QUESTION_BANK[default_key]
        
    fallback_key = "basic_and_intention.default"
    return fallback_key, QUESTION_BANK[fallback_key]
