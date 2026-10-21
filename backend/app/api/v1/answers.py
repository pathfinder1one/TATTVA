from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.llm.hosted_provider import HostedProviderError, get_core_provider
from app.llm.prompts import RAG_ANSWER_SYSTEM
from app.schemas.requests import CaseSearchRequest
from app.schemas.responses import CaseAnswerResponse
from app.services.case_access import require_case_access
from app.services.retrieval_service import search_case


class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=8000)
    citation_ids: list[str] = Field(default_factory=list, max_length=20)
    insufficient_evidence: bool
    limitations: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def citation_ids_are_unique(self):
        if len(set(self.citation_ids)) != len(self.citation_ids):
            raise ValueError("citation_ids must be unique")
        return self


router = APIRouter(prefix="/cases/{case_id}/answers", tags=["retrieval"])


@router.post("", response_model=CaseAnswerResponse)
async def answer_case_question(
    case_id: str,
    request: Request,
    body: CaseSearchRequest,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
) -> CaseAnswerResponse:
    await require_case_access(database, actor, case_id)
    if not settings.core_llm_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Case answer synthesis is not configured.",
        )

    citations = await search_case(
        database,
        request.app.state.qdrant,
        settings,
        case_id=case_id,
        tenant_id=actor.tenant_id,
        query=body.query,
        top_k=body.top_k,
    )
    request.app.state.qdrant_ready = True
    if not citations:
        return CaseAnswerResponse(
            case_id=case_id,
            query=body.query,
            answer="The indexed case sources do not contain enough retrieved information to answer this question.",
            citation_ids=[],
            citations=[],
            insufficient_evidence=True,
            limitations=["No authorized source passages matched the query."],
        )

    supplied_ids = {citation.citation_id for citation in citations}
    provider_input = {
        "question": body.query,
        "passages": [
            {
                "citation_id": citation.citation_id,
                "document_id": citation.document_id,
                "unit_type": citation.unit_type,
                "unit_number": citation.unit_number,
                "text": citation.text,
            }
            for citation in citations
        ],
    }
    try:
        output = await get_core_provider(settings).generate_structured(
            system=RAG_ANSWER_SYSTEM,
            input_data=provider_input,
            schema=GroundedAnswer,
            timeout_s=settings.core_llm_timeout_seconds,
            max_output_tokens=settings.core_llm_max_output_tokens,
        )
    except (HostedProviderError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The case answer provider is unavailable or returned an invalid answer.",
        ) from exc

    unknown_ids = set(output.citation_ids) - supplied_ids
    if unknown_ids:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The case answer provider cited a source passage that was not supplied.",
        )
    if not output.insufficient_evidence and not output.citation_ids:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The case answer provider returned an answer without source citations.",
        )
    selected_citations = [citation for citation in citations if citation.citation_id in output.citation_ids]
    return CaseAnswerResponse(
        case_id=case_id,
        query=body.query,
        answer=output.answer,
        citation_ids=output.citation_ids,
        citations=selected_citations,
        insufficient_evidence=output.insufficient_evidence,
        limitations=[
            *output.limitations,
            "Citation IDs are checked against retrieved source passages; investigators must review whether each passage supports the answer.",
        ],
    )

