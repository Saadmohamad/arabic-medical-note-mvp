# utils/llm_helpers.py
from __future__ import annotations
import logging
from tenacity import retry, wait_exponential, stop_after_attempt
from openai import RateLimitError, APIError, OpenAI

logger = logging.getLogger(__name__)
_client: OpenAI | None = None


def _client_singleton() -> OpenAI:
    global _client
    from utils.openai_client import get_openai_client  # late import to avoid cycles

    if _client is None:
        _client = get_openai_client()
    return _client


def safe_chat_completion(
    messages: list[dict[str, str]],
    *,
    primary_model: str = "gpt-4o-mini",
    fallback_model: str = "gpt-3.5-turbo",
    temperature: float = 0.1,
    max_tokens: int = 512,
    response_format: dict | None = None,
) -> str:
    """
    Call `primary_model`, fall back to `fallback_model` on transient OpenAI errors.
    Retries each model up to 3× with exponential back-off (2 s → ≤10 s).
    """

    @retry(
        reraise=True,
        wait=wait_exponential(multiplier=2, min=2, max=10),
        stop=stop_after_attempt(3),
    )
    def _try(model: str, *, include_json_mode: bool) -> str:
        return (
            _client_singleton()
            .chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **(
                    {"response_format": {"type": "json_object"}}
                    if include_json_mode and response_format
                    else {}
                ),
            )
            .choices[0]
            .message.content.strip()
        )

    # ── primary ──────────────────────────────────────────────────────────
    try:
        return _try(primary_model, include_json_mode=True)
    except (RateLimitError, APIError) as e:
        logger.warning(
            "%s failed (%s) → falling back to %s", primary_model, e, fallback_model
        )

    # ── fallback ─────────────────────────────────────────────────────────
    try:
        return _try(fallback_model, include_json_mode=False)
    except Exception as e:
        logger.error("Both %s and %s failed: %s", primary_model, fallback_model, e)
        raise RuntimeError("LLM request failed after retries") from e
