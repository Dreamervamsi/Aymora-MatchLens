from typing import Dict, Literal, Tuple

# Minimum evidence coverage threshold for recommendation eligibility
DEFAULT_MIN_EVIDENCE_COVERAGE: float = 60.0

# Default dimension weights
DEFAULT_DIMENSION_WEIGHTS: Dict[str, float] = {
    "core_values": 0.30,
    "relationship_intentions": 0.25,
    "lifestyle_compatibility": 0.20,
    "communication_preferences": 0.15,
    "shared_interests": 0.10,
}

# Dimension names constant
DIMENSION_CORE_VALUES = "core_values"
DIMENSION_RELATIONSHIP_INTENTIONS = "relationship_intentions"
DIMENSION_LIFESTYLE = "lifestyle_compatibility"
DIMENSION_COMMUNICATION = "communication_preferences"
DIMENSION_INTERESTS = "shared_interests"

SupportedDimension = Literal[
    "core_values",
    "relationship_intentions",
    "lifestyle_compatibility",
    "communication_preferences",
    "shared_interests",
]

ALL_DIMENSIONS: Tuple[str, ...] = (
    DIMENSION_CORE_VALUES,
    DIMENSION_RELATIONSHIP_INTENTIONS,
    DIMENSION_LIFESTYLE,
    DIMENSION_COMMUNICATION,
    DIMENSION_INTERESTS,
)
