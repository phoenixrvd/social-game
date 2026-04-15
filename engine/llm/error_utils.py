from __future__ import annotations

import openai


def llm_error_message(exc: openai.OpenAIError, provider_name: str) -> str:
    error_codes: dict[str, str] = {
        "insufficient_quota": "Kontingent erschoepft - Plan und Abrechnung pruefen.",
        "rate_limit_exceeded": "Anfragelimit erreicht - bitte kurz warten.",
        "invalid_api_key": "Ungueltiger API-Schluessel.",
        "model_not_found": "Das angeforderte Modell wurde nicht gefunden.",
        "content_policy_violation": "Anfrage durch Inhaltsrichtlinien abgelehnt.",
        "moderation_blocked": "Anfrage durch Moderation blockiert.",
    }
    if isinstance(exc, openai.APIStatusError):
        code: str = getattr(exc, "code", None) or ""
        status: int = exc.status_code
        if code in error_codes:
            return error_codes[code]
        if status == 429:
            return "Anfragelimit erreicht - bitte kurz warten."
        if status == 401:
            return "Authentifizierung fehlgeschlagen."
        if status >= 500:
            return f"Serverfehler ({status}) - bitte spaeter erneut versuchen."
        return f"Fehler ({status})"
    if isinstance(exc, openai.APIConnectionError):
        return f"{provider_name} nicht erreichbar - Verbindung pruefen."
    if isinstance(exc, openai.APITimeoutError):
        return "Anfrage hat zu lange gedauert (Timeout)."
    return str(exc)


