import re
import unicodedata
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DuplicateEntitySuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: str
    normalized_name: str
    entity_ids: list[str] = Field(min_length=2, max_length=100)
    action: str = "human_review_required"


def normalize_entity_name(value: str) -> str:
    """Normalize whitespace and Unicode for exact-name comparisons only."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def suggest_exact_duplicates(entities: list[dict[str, Any]]) -> list[DuplicateEntitySuggestion]:
    """Group exact normalized labels of the same type; never merge or fuzzy-match."""
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for entity in entities:
        entity_id = entity.get("entity_id")
        entity_type = entity.get("entity_type")
        name = entity.get("display_name")
        if not all(isinstance(value, str) and value.strip() for value in (entity_id, entity_type, name)):
            continue
        groups[(entity_type, normalize_entity_name(name))].append(entity_id)
    return [
        DuplicateEntitySuggestion(entity_type=entity_type, normalized_name=name, entity_ids=sorted(ids))
        for (entity_type, name), ids in sorted(groups.items())
        if len(ids) > 1
    ]
