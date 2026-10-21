from fastapi import APIRouter

from app.api.v1.cases import router as cases_router
from app.api.v1.documents import router as documents_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.entities import router as entities_router
from app.api.v1.graph import router as graph_router
from app.api.v1.relationships import router as relationships_router
from app.api.v1.search import router as search_router
from app.api.v1.analysis_runs import router as analysis_runs_router
from app.api.v1.answers import router as answers_router
from app.api.v1.reports import router as reports_router
from app.api.v1.findings import router as findings_router
from app.api.v1.voice import router as voice_router

api_router = APIRouter()
api_router.include_router(cases_router)
api_router.include_router(documents_router)
api_router.include_router(evidence_router)
api_router.include_router(search_router)
api_router.include_router(entities_router)
api_router.include_router(relationships_router)
api_router.include_router(graph_router)
api_router.include_router(analysis_runs_router)
api_router.include_router(answers_router)
api_router.include_router(reports_router)
api_router.include_router(findings_router)
api_router.include_router(voice_router)
