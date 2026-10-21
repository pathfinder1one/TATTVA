from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class GraphIntegrityFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule: Literal["self_relationship", "orphan_relationship", "duplicate_relationship_record"]
    record_ids: list[str] = Field(min_length=1, max_length=100)
    explanation: str = Field(max_length=300)
    status: Literal["requires_review"] = "requires_review"


def detect_graph_integrity_flags(
    entity_ids: set[str], relationships: list[dict[str, Any]]
) -> list[GraphIntegrityFlag]:
    """Find malformed or duplicated graph records; flags concern data quality only."""
    duplicate_groups: dict[tuple[str, str, str], list[str]] = {}
    flags: list[GraphIntegrityFlag] = []
    for relationship in relationships:
        relationship_id = relationship.get("relationship_id")
        subject = relationship.get("subject_entity_id")
        predicate = relationship.get("predicate")
        object_ = relationship.get("object_entity_id")
        if not all(isinstance(value, str) and value for value in (relationship_id, subject, predicate, object_)):
            continue
        if subject == object_:
            flags.append(GraphIntegrityFlag(
                rule="self_relationship", record_ids=[relationship_id],
                explanation="Relationship connects an entity to itself.",
            ))
        if subject not in entity_ids or object_ not in entity_ids:
            flags.append(GraphIntegrityFlag(
                rule="orphan_relationship", record_ids=[relationship_id],
                explanation="Relationship references an entity absent from this case graph.",
            ))
        key = (subject, predicate.casefold(), object_)
        duplicate_groups.setdefault(key, []).append(relationship_id)
    for ids in duplicate_groups.values():
        if len(ids) > 1:
            flags.append(GraphIntegrityFlag(
                rule="duplicate_relationship_record", record_ids=ids[:100],
                explanation="Multiple records have the same directed subject, predicate, and object.",
            ))
    return flags
