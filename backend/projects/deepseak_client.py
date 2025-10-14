import os
import requests
from typing import Optional, Dict, Any


class DeepSeakClient:
    """Minimal wrapper for DeepSeak-like REST API.

    This class intentionally keeps the interface small: provide prompt and generation
    parameters, returns the text result or raises RuntimeError on error.

    It reads configuration from environment variables:
      - DEEPSEAK_API_URL: full URL to the generate endpoint (required)
      - DEEPSEAK_API_KEY: API key/token (optional; if missing, client will attempt unauthenticated calls)
    """

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 30):
        # Prefer a local Text-Generation-Inference (TGI) endpoint if configured.
        # DEEPSEAK_LOCAL_URL can be e.g. http://127.0.0.1:8080
        self.local_url = os.environ.get('DEEPSEAK_LOCAL_URL')
        # Remote API URL (legacy)
        self.api_url = api_url or os.environ.get('DEEPSEAK_API_URL') or "https://api.deepseek.com"
        self.api_key = api_key or os.environ.get('DEEPSEAK_API_KEY')
        self.timeout = timeout

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7, extra: Optional[Dict[str, Any]] = None) -> str:
        """Send a generation request and return the result text.

        The exact payload shape is intentionally generic; adjust per DeepSeak API docs.
        """
        # Build payloads for different endpoint shapes (TGI vs generic REST)
        payload_tgi = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
            }
        }
        payload_generic = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if extra:
            # Merge extras into both payload shapes if present
            if isinstance(extra, dict):
                payload_tgi.update(extra)
                # for generic payload, merge shallow keys
                payload_generic.update(extra)

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Helper to record diagnostics to the ai_usage log (best-effort)
        def _log_diag(line: str):
            try:
                logs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
                os.makedirs(logs_dir, exist_ok=True)
                with open(os.path.join(logs_dir, 'ai_usage.log'), 'a', encoding='utf-8') as fh:
                    fh.write(line + "\n")
            except Exception:
                pass

        # Candidate endpoints. Prefer local TGI if configured.
        tried_urls = []
        try_urls = []
        if self.local_url:
            # TGI REST endpoints
            try_urls.extend([
                self.local_url.rstrip('/') + '/generate',
                self.local_url.rstrip('/') + '/api/predict',
                self.local_url.rstrip('/') + '/v1/generate',
            ])
        # Add remote/legacy endpoints
        if self.api_url:
            try_urls.append(self.api_url)
            if '/' == self.api_url.rstrip('/').split('://', 1)[-1] or self.api_url.rstrip('/').count('/') == 1:
                try_urls.extend([
                    self.api_url.rstrip('/') + '/generate',
                    self.api_url.rstrip('/') + '/v1/generate',
                    self.api_url.rstrip('/') + '/api/generate',
                ])

        resp = None
        last_exc = None
        for u in try_urls:
            tried_urls.append(u)
            try:
                # Choose payload shape heuristically based on endpoint
                j = payload_tgi if any(p in u for p in ['/predict', '/generate']) else payload_generic
                resp = requests.post(u, json=j, headers=headers, timeout=self.timeout)
                # stop trying on any non-5xx response (i.e., 200/4xx)
                if resp is not None:
                    break
            except requests.RequestException as e:
                last_exc = e
                resp = None

        if resp is None:
            raise RuntimeError(f"DeepSeak request failed: {last_exc} (tried: {tried_urls})")

        # Log non-200 responses for diagnosis
        if resp.status_code >= 400:
            diag = f"DeepSeak error {resp.status_code} on {resp.url}: {resp.text} (tried: {tried_urls})"
            _log_diag(diag)
            raise RuntimeError(diag)

        try:
            data = resp.json()
        except ValueError:
            # Non-json response
            raise RuntimeError("DeepSeak returned non-JSON response")

        # Common shapes: {"generated_text": "..."} or {"choices": [{"text": "..."}]}
        if isinstance(data, dict):
            if "generated_text" in data and isinstance(data["generated_text"], str):
                return data["generated_text"].strip()
            if "text" in data and isinstance(data["text"], str):
                return data["text"].strip()
            choices = data.get("choices")
            if choices and isinstance(choices, list) and len(choices) > 0:
                first = choices[0]
                if isinstance(first, dict) and "text" in first:
                    return first["text"].strip()
        # Fallback: try raw text
        return resp.text.strip()
