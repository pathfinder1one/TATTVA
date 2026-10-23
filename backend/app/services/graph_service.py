from collections import Counter
from typing import Any


def build_case_graph(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    mentions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a scoped graph projection with simple, non-inferential metrics."""
    entity_ids = {
        entity["entity_id"] for entity in entities
        if isinstance(entity.get("entity_id"), str)
    }
    evidence_by_entity: dict[str, list[str]] = {}
    for mention in mentions:
        entity_id = mention.get("entity_id")
        evidence_id = mention.get("evidence_id")
        if isinstance(entity_id, str) and entity_id in entity_ids and isinstance(evidence_id, str):
            evidence_by_entity.setdefault(entity_id, []).append(evidence_id)

    degrees: Counter[str] = Counter({entity_id: 0 for entity_id in entity_ids})
    valid_relationships = []
    pairs = set()
    for relationship in relationships:
        subject = relationship.get("subject_entity_id")
        object_ = relationship.get("object_entity_id")
        if not isinstance(subject, str) or not isinstance(object_, str):
            continue
        if subject not in entity_ids or object_ not in entity_ids:
            continue
        valid_relationships.append(relationship)
        degrees[subject] += 1
        degrees[object_] += 1
        pairs.add((subject, object_))

    node_count = len(entity_ids)
    possible_edges = node_count * (node_count - 1)
    
    # Enrich entities with evidence IDs
    scoped_entities = [
        {**entity, "evidence_ids": evidence_by_entity.get(entity["entity_id"], [])}
        for entity in entities
        if isinstance(entity.get("entity_id"), str) and entity.get("entity_id") in entity_ids
    ]

    # Run MHA NCRB Algorithmic Influencer & Centrality Analysis
    from app.services.centrality_service import analyze_criminal_network_influencers
    analysis_res = analyze_criminal_network_influencers(scoped_entities, valid_relationships)
    enriched_entities = analysis_res["entities"]
    syndicate_analysis = analysis_res["syndicate_analysis"]

    return {
        "entities": enriched_entities,
        "relationships": valid_relationships,
        "metrics": {
            "entity_count": node_count,
            "relationship_count": len(valid_relationships),
            "average_degree": sum(degrees.values()) / node_count if node_count else 0.0,
            "directed_density": len(pairs) / possible_edges if possible_edges else 0.0,
        },
        "syndicate_intelligence": syndicate_analysis,
        "metrics_note": "Structural graph metrics & algorithmic centralities (PageRank Kingpins & Betweenness Brokers) computed under MHA NCRB specifications.",
    }
