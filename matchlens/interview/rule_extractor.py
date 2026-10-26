import re
import logging
from typing import Optional, List, Set, Tuple

from matchlens.ai.models import (
    ExtractedProfileUpdate,
    PartialUserAttributes,
    PartialPartnerPreferences,
    PartialDealbreakers,
    ConfirmationPrompt,
    ALLOWED_SMOKING,
    ALLOWED_DRINKING,
    ALLOWED_EXERCISE,
    ALLOWED_WANTS_CHILDREN,
    ALLOWED_RELATIONSHIP_INTENT,
    ALLOWED_COMMUNICATION_STYLE,
    ALLOWED_CONFLICT_RESOLUTION,
    ALLOWED_CONTACT_FREQUENCY,
)

logger = logging.getLogger(__name__)

# Known keywords for core values and shared interests
KNOWN_VALUES = {
    "honesty", "family", "ambition", "integrity", "loyalty", "growth",
    "kindness", "respect", "curiosity", "compassion", "independence",
    "creativity", "stability", "authenticity", "empathy", "balance"
}

KNOWN_INTERESTS = {
    "hiking", "reading", "cooking", "travel", "fitness", "art", "music",
    "nature", "tech", "gaming", "photography", "sports", "yoga", "movies",
    "writing", "baking", "gardening", "camping", "cycling", "running"
}


class RuleProfileExtractor:
    """
    Fast, deterministic, rule-based profile extractor using Python regex,
    keyword dictionaries, clause segmentation, and temporal/negation rules.
    Yields zero LLM API calls during onboarding interview turns.
    """

    def extract_from_text(
        self,
        user_input: str,
        context_prompt: Optional[str] = None,
    ) -> ExtractedProfileUpdate:
        """
        Extracts structured profile updates from user natural language input.
        """
        if not user_input or not user_input.strip():
            return ExtractedProfileUpdate()

        cleaned_input = user_input.strip()

        # Initialize partial target objects
        self_attrs = PartialUserAttributes()
        partner_prefs = PartialPartnerPreferences()
        dealbreakers = PartialDealbreakers()
        confirmations: List[ConfirmationPrompt] = []

        # Split input into clauses/sentences
        clauses = self._split_into_clauses(cleaned_input)

        for clause in clauses:
            scope, subject_type = self._determine_clause_scope(clause)

            if scope == "third_party":
                # Ignore statements referencing third parties (e.g., "my brother is 30")
                continue

            # Check temporal past indicators
            if self._is_past_temporal(clause):
                # Discard statements about past habits ("I used to smoke")
                continue

            # Process clause per scope
            if scope == "self":
                self._extract_self_clause(clause, self_attrs, confirmations, context_prompt)
            elif scope == "partner":
                self._extract_partner_clause(clause, partner_prefs, confirmations, context_prompt)
            elif scope == "dealbreaker":
                self._extract_dealbreaker_clause(clause, dealbreakers, partner_prefs)

            # Also check partner age/preferences if clause explicitly contains partner criteria
            if scope == "self" and ("partner" in clause.lower() or "between" in clause.lower() or "looking for a man" in clause.lower() or "looking for a woman" in clause.lower()):
                self._extract_partner_clause(clause, partner_prefs, confirmations, context_prompt)

        # Context-aware fallback for standalone numerical answers (e.g. user answered "28" to age question)
        if context_prompt and self_attrs.age is None and partner_prefs.min_age is None:
            self._apply_contextual_numerical_fallback(cleaned_input, context_prompt, self_attrs, partner_prefs)

        return ExtractedProfileUpdate(
            confirmed_self_attributes=self_attrs,
            confirmed_partner_preferences=partner_prefs,
            confirmed_dealbreakers=dealbreakers,
            confirmations_needed=confirmations,
        )

    def _split_into_clauses(self, text: str) -> List[str]:
        """
        Splits text into logical sentences/clauses using punctuation boundaries and conjunctions.
        """
        parts = re.split(r'[.!?;]|\b(?:but|however)\b', text, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]

    def _determine_clause_scope(self, clause: str) -> Tuple[str, str]:
        """
        Determines whether a clause applies to 'self', 'partner', 'dealbreaker', or 'third_party'.
        Returns (scope, subject_type).
        """
        lower = clause.lower()

        # Third party check
        third_party_regex = r'\b(?:my\s+(?:brother|sister|friend|mother|father|mom|dad|ex|cousin|boss|coworker))\b'
        if re.search(third_party_regex, lower) and not re.search(r'\b(?:i|my\s+age|my\s+partner)\b', lower):
            return ("third_party", "other")

        # Dealbreaker check
        if re.search(r'\b(?:dealbreaker|non-negotiable|must not|cannot stand|absolutely no|zero tolerance)\b', lower):
            return ("dealbreaker", "dealbreaker")

        # Partner check
        partner_regex = r'\b(?:for my partner|partner should|ideal match|someone who|open to dating|prefer a partner|looking for a partner|partner who is)\b'
        if re.search(partner_regex, lower) and "i am" not in lower and "i'm" not in lower:
            return ("partner", "partner")

        # Self check
        return ("self", "self")

    def _is_past_temporal(self, clause: str) -> bool:
        """
        Checks if the clause refers strictly to past states or habits.
        """
        lower = clause.lower()
        past_regex = r'\b(?:used to|in the past|previously|formerly|used to be|ex-)\b'
        return bool(re.search(past_regex, lower))

    def _extract_self_clause(
        self,
        clause: str,
        attrs: PartialUserAttributes,
        confirmations: List[ConfirmationPrompt],
        context_prompt: Optional[str],
    ) -> None:
        lower = clause.lower()

        # 1. Age
        age_match = re.search(r'\b(?:i am|i\'m|age|turning)\s*(\d{2})\b|\b(\d{2})\s*(?:years old|yo|yrs old|years)\b|^\s*(\d{2})\b|\b(\d{2})\s*,', lower)
        if age_match:
            val_str = [g for g in age_match.groups() if g is not None][0]
            val = int(val_str)
            if 18 <= val <= 120 and "brother" not in lower and "sister" not in lower and "between" not in lower and "ideal" not in lower and "aged" not in lower:
                attrs.age = val

        # 2. Gender
        if re.search(r'\b(?:female|woman|lady)\b', lower) and "looking for a woman" not in lower and "for my partner" not in lower and "want a woman" not in lower and "partner who is a man" not in lower:
            attrs.gender = "woman"
        elif re.search(r'\b(?:male|man|guy)\b', lower) and "looking for a man" not in lower and "for my partner" not in lower and "want a man" not in lower and "partner who is a man" not in lower:
            attrs.gender = "man"
        elif re.search(r'\b(?:non-binary|nonbinary|enby)\b', lower):
            attrs.gender = "non-binary"

        # 3. Relationship Intent
        if re.search(r'\b(?:long[- ]term|longterm|serious|marriage|life partner)\b', lower):
            if "marriage" in lower and "long" not in lower:
                attrs.relationship_intent = "marriage"
            else:
                attrs.relationship_intent = "long_term"
        elif re.search(r'\b(?:casual|dating casually|short[- ]term|fun|no pressure)\b', lower):
            if not re.search(r'\b(?:not|no|don\'t want|anything but)\s+casual\b', lower):
                attrs.relationship_intent = "casual"
        elif re.search(r'\b(?:friendship|friends first)\b', lower):
            attrs.relationship_intent = "friendship"

        # 4. Smoking
        if "smoke" in lower or "smoking" in lower:
            if re.search(r'\b(?:used to|in college|past)\b', lower):
                pass # Discard past smoking
            elif re.search(r'\b(?:don\'t|do not|never|non|not a)\s+smoke[rs]?\b|\bnever smoke\b|\bsmoke-free\b|\bnon-smoker\b', lower):
                attrs.smoking = "never"
            elif re.search(r'\b(?:socially|social smoker|occasionally smoke)\b', lower):
                attrs.smoking = "socially"
            elif not re.search(r'\b(?:don\'t|never|not|socially)\b', lower):
                attrs.smoking = "regularly"

        # 5. Drinking
        if re.search(r'\b(?:don\'t|do not|never|non)\s+drink[s]?\b|\bnever drink\b|\bteetotaler|sober\b', lower):
            attrs.drinking = "never"
        elif re.search(r'\b(?:socially|social drinker|occasionally drink|a drink now and then)\b', lower):
            attrs.drinking = "socially"
        elif re.search(r'\b(?:regularly|daily|heavy drinker|i drink)\b', lower) and not re.search(r'\b(?:don\'t|never|not|socially)\b', lower):
            attrs.drinking = "regularly"

        # 6. Exercise
        if re.search(r'\b(?:daily|every day|7 days a week|workout daily)\b', lower):
            attrs.exercise = "daily"
        elif re.search(r'\b(?:weekly|few times a week|3-4 times|regularly at gym)\b', lower):
            attrs.exercise = "weekly"
        elif re.search(r'\b(?:rarely|seldom|once in a while)\b', lower):
            attrs.exercise = "rarely"
        elif re.search(r'\b(?:never exercise|don\'t exercise|couch potato)\b', lower):
            attrs.exercise = "never"

        # 7. Children
        if re.search(r'\b(?:i have|have)\s+(\d+|a|kids|children|son|daughter)\b', lower) and not re.search(r'\b(?:don\'t|no|0)\s+kids\b', lower):
            attrs.has_children = True
        elif re.search(r'\b(?:don\'t have|no|zero)\s+(?:kids|children)\b', lower):
            attrs.has_children = False

        if re.search(r'\b(?:want|hoping for)\s+(?:kids|children|family)\b', lower) and not re.search(r'\b(?:don\'t|do not|no)\s+want\b', lower):
            attrs.wants_children = "yes"
        elif re.search(r'\b(?:don\'t|do not|never)\s+want\s+(?:kids|children)\b|\bchildfree\b', lower):
            attrs.wants_children = "no"
        elif re.search(r'\b(?:open to|maybe|open regarding)\s+(?:kids|children)\b', lower):
            attrs.wants_children = "open"

        # 8. Communication Style
        if re.search(r'\b(?:direct|straightforward|blunt)\b', lower):
            attrs.communication_style = "direct"
        elif re.search(r'\b(?:gentle|soft-spoken|thoughtful|kind)\b', lower):
            attrs.communication_style = "gentle"
        elif re.search(r'\b(?:expressive|open|vocal|talkative)\b', lower):
            attrs.communication_style = "expressive"
        elif re.search(r'\b(?:analytical|logical|pragmatic)\b', lower):
            attrs.communication_style = "analytical"

        # 9. Conflict Resolution
        if re.search(r'\b(?:discuss immediately|talk right away|resolve quickly|face to face)\b', lower):
            attrs.conflict_resolution = "discuss_immediately"
        elif re.search(r'\b(?:cool down first|take space|need time|space first)\b', lower):
            attrs.conflict_resolution = "cool_down_first"
        elif re.search(r'\b(?:written|text first|write it down)\b', lower):
            attrs.conflict_resolution = "written_first"

        # 10. Contact Frequency
        if re.search(r'\b(?:frequent|constantly|throughout the day)\b', lower):
            attrs.contact_frequency = "frequent"
        elif re.search(r'\b(?:daily check[- ]in|once a day|check in daily)\b', lower):
            attrs.contact_frequency = "daily_check_in"
        elif re.search(r'\b(?:as needed|when needed|few times a week)\b', lower):
            attrs.contact_frequency = "as_needed"

        # 11. Core Values & Interests
        found_vals = [v for v in KNOWN_VALUES if re.search(rf'\b{v}\b', lower)]
        if found_vals:
            attrs.core_values = list(set((attrs.core_values or []) + found_vals))

        found_interests = [i for i in KNOWN_INTERESTS if re.search(rf'\b{i}\b', lower)]
        if found_interests:
            attrs.interests = sorted(list(set((attrs.interests or []) + found_interests)))

    def _extract_partner_clause(
        self,
        clause: str,
        prefs: PartialPartnerPreferences,
        confirmations: List[ConfirmationPrompt],
        context_prompt: Optional[str],
    ) -> None:
        lower = clause.lower()

        # Age Range
        range_match = re.search(r'\b(?:between|aged|from)?\s*(\d{2})\s*(?:and|to|-)\s*(\d{2})\b', lower)
        if range_match:
            min_a, max_a = int(range_match.group(1)), int(range_match.group(2))
            if 18 <= min_a <= max_a <= 120:
                prefs.min_age = min_a
                prefs.max_age = max_a
        else:
            at_least = re.search(r'\b(?:at least|min|minimum)\s*(\d{2})\b', lower)
            if at_least:
                prefs.min_age = int(at_least.group(1))
            max_is = re.search(r'\b(?:at most|max|maximum|under|up to)\s*(\d{2})\b', lower)
            if max_is:
                prefs.max_age = int(max_is.group(1))

        # Acceptable Genders
        genders = []
        if re.search(r'\b(?:women|female|females)\b', lower) and "for a man" not in lower:
            genders.append("woman")
        if re.search(r'\b(?:men|male|males|man)\b', lower) and "for a woman" not in lower:
            genders.append("man")
        if re.search(r'\b(?:non-binary|nonbinary|enby)\b', lower):
            genders.append("non-binary")
        if re.search(r'\b(?:any gender|anyone|everyone|all genders)\b', lower):
            genders = ["any"]

        if genders:
            prefs.acceptable_genders = list(set((prefs.acceptable_genders or []) + genders))

        # Acceptable Smoking
        if re.search(r'\b(?:should not smoke|non-smoker|never smoke|no smoking)\b', lower):
            prefs.acceptable_smoking = ["never"]
        elif re.search(r'\b(?:social smoking ok|socially is fine)\b', lower):
            prefs.acceptable_smoking = ["never", "socially"]

        # Acceptable Drinking
        if re.search(r'\b(?:should not drink|non-drinker|never drink|no drinking)\b', lower):
            prefs.acceptable_drinking = ["never"]
        elif re.search(r'\b(?:social drinking ok|socially is fine)\b', lower):
            prefs.acceptable_drinking = ["never", "socially"]

        # Desired Intentions
        if re.search(r'\b(?:long[- ]term|serious|marriage)\b', lower):
            prefs.desired_intentions = list(set((prefs.desired_intentions or []) + ["long_term", "marriage"]))

    def _extract_dealbreaker_clause(
        self,
        clause: str,
        dealbreakers: PartialDealbreakers,
        prefs: PartialPartnerPreferences,
    ) -> None:
        lower = clause.lower()

        if "smoke" in lower or "smoking" in lower:
            dealbreakers.smoking_dealbreaker = True
            prefs.acceptable_smoking = ["never"]

        if "kid" in lower or "children" in lower:
            dealbreakers.children_dealbreaker = True

        if "age" in lower:
            dealbreakers.strict_age_range = True

        if "gender" in lower:
            dealbreakers.strict_gender_match = True

        if "intent" in lower or "goal" in lower or "marriage" in lower or "long term" in lower:
            dealbreakers.strict_intention_match = True

    def _apply_contextual_numerical_fallback(
        self,
        text: str,
        context: str,
        attrs: PartialUserAttributes,
        prefs: PartialPartnerPreferences,
    ) -> None:
        """
        Handles short numerical responses where question context specifies age or age range.
        """
        clean = text.strip()
        num_match = re.search(r'^\d{2}$', clean)
        if not num_match:
            return

        val = int(clean)
        if not (18 <= val <= 120):
            return

        ctx_lower = context.lower()
        if "your age" in ctx_lower or "how old are you" in ctx_lower or "topic: 'basic" in ctx_lower:
            attrs.age = val
        elif "partner" in ctx_lower and "age" in ctx_lower:
            prefs.min_age = max(18, val - 5)
            prefs.max_age = min(120, val + 5)
