from typing import Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DraftReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_type: str = "machine_generated_draft"
    report_id: str | None = None
    version: int | None = Field(default=None, ge=1)
    created_at: datetime | None = None
    run_id: str = Field(min_length=1, max_length=120)
    case_id: str = Field(min_length=1, max_length=120)
    query: str = Field(min_length=2, max_length=2000)
    source_citations: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    candidate_mentions: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    candidate_relationships: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    potential_value_discrepancies: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    hypotheses: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    graph_pattern_summary: dict[str, Any] | None = None
    reviewed_findings: list[dict[str, Any]] = Field(default_factory=list, max_length=500)
    limitations: list[str] = Field(default_factory=list, max_length=30)
    review_required: bool = True


def build_draft_report(
    *, run_id: str, case_id: str, query: str, task_outputs: list[dict[str, Any]],
    reviewed_findings: list[dict[str, Any]] | None = None,
) -> DraftReport:
    """Assemble a source-linked draft; does not label candidates as supported findings."""
    citations: dict[str, dict[str, Any]] = {}
    mentions: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    discrepancies: list[dict[str, Any]] = []
    hypotheses: list[dict[str, Any]] = []
    graph_pattern_summary: dict[str, Any] | None = None
    limitations = {
        "Machine-generated draft; investigator review is required.",
        "Candidate mentions and relationships are unverified and are not findings.",
    }
    for output in task_outputs:
        if not isinstance(output, dict):
            continue
        for citation in output.get("citations", []):
            if isinstance(citation, dict) and isinstance(citation.get("citation_id"), str):
                citations[citation["citation_id"]] = citation
        mentions.extend(item for item in output.get("mentions", []) if isinstance(item, dict))
        relationships.extend(item for item in output.get("relationships", []) if isinstance(item, dict))
        discrepancies.extend(
            item for item in output.get("potential_value_discrepancies", []) if isinstance(item, dict)
        )
        hypotheses.extend(item for item in output.get("hypotheses", []) if isinstance(item, dict))
        pattern_output = output.get("summary")
        if isinstance(pattern_output, dict) and "degree_counts" in pattern_output:
            graph_pattern_summary = pattern_output
        limitations.update(item for item in output.get("limitations", []) if isinstance(item, str))
    valid_citations = set(citations)
    mentions = [item for item in mentions if item.get("citation_id") in valid_citations]
    relationships = [item for item in relationships if item.get("citation_id") in valid_citations]
    discrepancies = [
        item for item in discrepancies
        if item.get("claims") and all(
            isinstance(claim, dict) and claim.get("evidence_id") in valid_citations
            for claim in item.get("claims", [])
        )
    ]
    hypotheses = [
        item for item in hypotheses
        if all(
            _reference_matches_citation(reference, citations)
            for side in ("evidence_for", "evidence_against")
            for reference in item.get(side, [])
        ) and item.get("evidence_for") and item.get("evidence_against")
    ]
    if discrepancies:
        limitations.add("Potential value discrepancies are review leads, not confirmed contradictions.")
    if hypotheses:
        limitations.add("Hypotheses are unverified suggestions requiring balanced human review.")
    return DraftReport(
        run_id=run_id,
        case_id=case_id,
        query=query,
        source_citations=list(citations.values()),
        candidate_mentions=mentions,
        candidate_relationships=relationships,
        potential_value_discrepancies=discrepancies,
        hypotheses=hypotheses,
        graph_pattern_summary=graph_pattern_summary,
        reviewed_findings=reviewed_findings or [],
        limitations=sorted(limitations),
    )


def _reference_matches_citation(reference: Any, citations: dict[str, dict[str, Any]]) -> bool:
    if not isinstance(reference, dict):
        return False
    citation = citations.get(reference.get("citation_id"))
    quote = reference.get("quote")
    start = reference.get("start_offset")
    end = reference.get("end_offset")
    if (
        citation is None or not isinstance(quote, str)
        or not isinstance(start, int) or not isinstance(end, int)
        or end <= start
    ):
        return False
    local_start = start - citation.get("start_offset", 0)
    local_end = end - citation.get("start_offset", 0)
    text = citation.get("text")
    return (
        isinstance(text, str) and local_start >= 0 and local_end <= len(text)
        and text[local_start:local_end] == quote
    )
