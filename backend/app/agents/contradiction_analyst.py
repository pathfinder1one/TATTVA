from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClaimValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str = Field(min_length=1, max_length=120)
    predicate: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=500)
    evidence_id: str = Field(min_length=1, max_length=120)


class PotentialContradiction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str
    predicate: str
    claims: list[ClaimValue] = Field(min_length=2)
    status: str = "potential_value_discrepancy_requires_review"


def find_explicit_value_conflicts(claims: list[ClaimValue | dict[str, Any]]) -> list[PotentialContradiction]:
    """Group explicitly different values for a subject/predicate, without resolving truth."""
    parsed = [ClaimValue.model_validate(claim) for claim in claims]
    grouped: dict[tuple[str, str], dict[str, list[ClaimValue]]] = defaultdict(lambda: defaultdict(list))
    for claim in parsed:
        normalized_value = " ".join(claim.value.casefold().split())
        grouped[(claim.subject_id, claim.predicate)][normalized_value].append(claim)
    conflicts = []
    for (subject_id, predicate), by_value in grouped.items():
        if len(by_value) > 1:
            conflicts.append(PotentialContradiction(
                subject_id=subject_id,
                predicate=predicate,
                claims=[claim for value_claims in by_value.values() for claim in value_claims],
            ))
    return conflicts
