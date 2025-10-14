"""Utilities to extract and normalize project text from different inputs.

Provides ProjectTextExtractor which can:
- extract from a payload dict (keys: description, project_text, html, url)
- clean HTML (remove script/style, strip tags, unescape entities)
- optionally fetch remote URL content (disabled by default; enable with allow_fetch=True)

Note: server-side scraping may violate site ToS. By default remote fetch is off.
"""
from typing import Optional, Dict
import re
from django.utils.html import strip_tags
import html as _html


class ProjectTextExtractor:
    """Extracts plain text suitable for matching from payloads or URLs.

    Usage:
        extractor = ProjectTextExtractor()
        text = extractor.extract_from_payload(payload, allow_fetch=False)
    """

    SCRIPT_STYLE_RE = re.compile(r"<(script|style).*?>.*?</\1>", re.I | re.S)
    WHITESPACE_RE = re.compile(r"[\t\r\n]+")

    def clean_html(self, html: str) -> str:
        """Remove scripts/styles, strip tags, unescape entities and collapse whitespace."""
        if not html:
            return ''
        # remove script/style blocks
        no_scripts = self.SCRIPT_STYLE_RE.sub(' ', html)
        # strip tags
        text = strip_tags(no_scripts)
        # unescape html entities
        text = _html.unescape(text)
        # collapse whitespace
        text = self.WHITESPACE_RE.sub(' ', text)
        return text.strip()

    def fetch_url(self, url: str, timeout: int = 5) -> Optional[str]:
        raise RuntimeError('Automatic URL fetch disabled in TOS-safe mode. Please copy/paste the job description into the description field.')

    def extract_from_payload(self, payload: Dict, allow_fetch: bool = False) -> str:
        """Given a payload dict, extract the most relevant project text.

        Recognized keys (checked in order): 'description', 'project_text', 'html', 'url'.
        If 'url' is present and allow_fetch is True, the URL will be fetched and extracted.
        """
        if not payload or not isinstance(payload, dict):
            return ''

        # prefer explicit text fields
        text = payload.get('description') or payload.get('project_text') or payload.get('html')
        if text:
            return self.clean_html(text)

        # In TOS-safe mode we do not fetch remote URLs. If a URL is present, require the
        # user to paste the job text into the `description` field of the payload.
        if payload.get('url'):
            raise ValueError('Automatic URL fetching is disabled for TOS compliance. Please paste the job description into the payload.description field.')

        return ''

    def extract_from_html(self, html: str) -> str:
        """Convenience wrapper to clean a raw HTML string."""
        return self.clean_html(html)
