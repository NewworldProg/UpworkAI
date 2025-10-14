from typing import Dict, Any, Optional
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from .models import Project
from .compute_match import MatchScorer
from .inputs import normalize_skills
from .project_text_extractor import ProjectTextExtractor


class JobIngestor:
    """Ingests job payloads into Project model, computes match score and returns the created instance."""

    def __init__(self, scorer=None):
        # avoid importing services here to prevent circular imports; use MatchScorer directly
        self.scorer = scorer or MatchScorer().compute
        self.extractor = ProjectTextExtractor()

    def sanitize(self, text: Optional[str]) -> str:
        if not text:
            return ''
        # remove HTML tags and trim
        return strip_tags(text).strip()

    def ingest(self, payload: Dict[str, Any]) -> Project:
        title = self.sanitize(payload.get('title') or payload.get('job_title') or '')
        # use extractor to normalize/obtain description if missing
        raw_desc = payload.get('description') or payload.get('project_text') or ''
        # enforce TOS-safe mode: if no description is provided, require tos_safe True or disallow ingest
        tos_safe_flag = payload.get('tos_safe') or False
        if not raw_desc and payload.get('url'):
            # do not fetch by default in ingest(); require tos_safe or explicit allow
            if not tos_safe_flag:
                raise ValueError('Description is required unless tos_safe=True is provided (manual ingestion).')
            raw_desc = self.extractor.extract_from_payload({'url': payload.get('url')}, allow_fetch=False)
        description = self.sanitize(raw_desc)
        budget = payload.get('budget') or ''
        raw_skills = payload.get('skills_required') or payload.get('skills') or ''
        skills_input = normalize_skills(raw_skills)
        skills = skills_input.as_string()
        deadline = payload.get('deadline') or None
        url = payload.get('url') or ''
        language = payload.get('language') or ''
        client = payload.get('client') or ''

        # compute match score
        score = None
        try:
            score = float(self.scorer(description, skills))
        except Exception:
            score = None

        project = Project.objects.create(
            title=title,
            description=description,
            budget=budget,
            skills_required=skills,
            deadline=deadline,
            url=url,
            language=language,
            client=client,
            source_url=payload.get('url') or '',
            fetched_at=None,
            fetch_method='manual' if not payload.get('url') else 'api',
            saved_pdf_path=payload.get('saved_pdf_path') or '',
            tos_safe=bool(tos_safe_flag),
            match_score=score,
        )
        return project

    def ingest_with_fetch(self, payload: Dict[str, Any], allow_fetch: bool = False) -> Project:
        """Ingest but allow fetching URL content if allow_fetch=True."""
        title = self.sanitize(payload.get('title') or payload.get('job_title') or '')
        raw_desc = payload.get('description') or payload.get('project_text') or ''
        tos_safe_flag = payload.get('tos_safe') or False
        if not raw_desc and payload.get('url') and allow_fetch:
            # only allow fetch if scraping is allowed in settings or tos_safe explicitly True
            if not getattr(settings, 'ALLOW_SCRAPING', False) and not tos_safe_flag:
                raise ValueError('Fetching disabled by settings; set ALLOW_SCRAPING=True or provide tos_safe=True with manual approval')
            raw_desc = self.extractor.extract_from_payload({'url': payload.get('url')}, allow_fetch=True)
        description = self.sanitize(raw_desc)

        budget = payload.get('budget') or ''
        raw_skills = payload.get('skills_required') or payload.get('skills') or ''
        skills_input = normalize_skills(raw_skills)
        skills = skills_input.as_string()
        deadline = payload.get('deadline') or None
        url = payload.get('url') or ''
        language = payload.get('language') or ''
        client = payload.get('client') or ''

        # compute match score
        score = None
        try:
            score = float(self.scorer(description, skills))
        except Exception:
            score = None

        project = Project.objects.create(
            title=title,
            description=description,
            budget=budget,
            skills_required=skills,
            deadline=deadline,
            url=url,
            language=language,
            client=client,
            source_url=payload.get('url') or '',
            fetched_at=timezone.now() if (payload.get('url') and allow_fetch) else None,
            fetch_method='scrape' if allow_fetch else ('manual' if not payload.get('url') else 'api'),
            saved_pdf_path=payload.get('saved_pdf_path') or '',
            tos_safe=bool(tos_safe_flag),
            match_score=score,
        )
        return project
