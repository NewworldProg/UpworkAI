"""Thin delegator exposing service functions used by the API endpoints.

This module keeps the same function-level API (compute_match_score,
generate_cover_letter, generate_cover_letter_async, create_monday_task) but
delegates implementation to classes in separate modules so each component
can be developed and tested independently.
"""
from .compute_match import MatchScorer
from .cover_generator import CoverGenerator
from .monday_client import MondayClient
from .job_ingest import JobIngestor
from .project_text_extractor import ProjectTextExtractor


# default instances (can be swapped in tests)
_scorer = MatchScorer()
_ai = CoverGenerator()
_monday = MondayClient()


def compute_match_score(project_text: str, skills: str) -> float:
    return _scorer.compute(project_text, skills)


def generate_cover_letter(project_description: str, skills: str, mode: str | None = None, job_title: str | None = None, company_name: str | None = None) -> str:
    # Use only_backend parameter to override backend choice
    return _ai.generate(project_description, skills, job_title=job_title, company_name=company_name, only_backend=mode)


async def generate_cover_letter_async(project_description: str, skills: str, job_title: str | None = None) -> str:
    return await _ai.generate_async(project_description, skills, job_title=job_title)


def create_monday_task(title: str, deadline: str, assignee: str, api_key: str | None = None) -> dict:
    if api_key:
        client = MondayClient(api_key=api_key)
    else:
        client = _monday
    return client.create_task(title, deadline, assignee)


def ingest_job(payload: dict):
    """Ingest a single job payload, compute match score, and create a Project record.

    Payload keys accepted: title, description (or project_text), budget, skills_required (or skills),
    deadline, url, language, client
    """
    ingestor = JobIngestor()
    return ingestor.ingest(payload)


def ingest_job_with_fetch(payload: dict, allow_fetch: bool = False):
    ingestor = JobIngestor()
    return ingestor.ingest_with_fetch(payload, allow_fetch=allow_fetch)


def extract_project_text(payload: dict, allow_fetch: bool = False) -> str:
    extractor = ProjectTextExtractor()
    return extractor.extract_from_payload(payload or {}, allow_fetch=allow_fetch)


def ingest_rss(url: str, dedupe: bool = True):
    raise NotImplementedError('RSS ingestion has been disabled in TOS-safe mode.')
