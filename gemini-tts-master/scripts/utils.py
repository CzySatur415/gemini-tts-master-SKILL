"""
Shared utilities for Gemini 3.1 Flash TTS scripts.

Handles:
- PCM (s16le 24kHz mono) -> WAV wrapping
- Retry-on-500 logic for the occasional flaky response
- Environment-variable-based API key loading
- Graceful fallback from google-genai SDK -> raw REST via requests
"""

from __future__ import annotations

import base64
import os
import time
import wave
from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar("T")

# Gemini TTS always returns PCM s16le mono at 24 kHz.
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH = 2  # 16-bit


def get_api_key() -> str:
    """Load the Gemini API key from the environment.

    Raises a helpful error if it's missing — never log or return a partial key.
    """
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Run: export GEMINI_API_KEY='your-key-here' "
            "before invoking the script. You can get a key at "
            "https://aistudio.google.com/apikey"
        )
    return key


def pcm_to_wav(
    pcm_data: bytes,
    output_path: str | Path,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS,
    sample_width: int = DEFAULT_SAMPLE_WIDTH,
) -> Path:
    """Wrap raw PCM bytes in a WAV container and write to disk."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return output_path


def decode_audio_payload(b64_or_bytes: str | bytes) -> bytes:
    """Normalize whatever the API gave us back into raw PCM bytes."""
    if isinstance(b64_or_bytes, bytes):
        return b64_or_bytes
    return base64.b64decode(b64_or_bytes)


def with_retry(
    fn: Callable[[], T],
    *,
    max_retries: int = 3,
    initial_backoff_s: float = 1.5,
    label: str = "Gemini TTS request",
) -> T:
    """Retry the function up to `max_retries` times on 5xx-style failures.

    The TTS docs explicitly warn that the model occasionally returns text
    tokens instead of audio tokens, causing a 500. Retry is the recommended
    mitigation.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — we genuinely want to catch all transients
            last_exc = exc
            msg = str(exc).lower()
            transient = (
                "500" in msg
                or "internal" in msg
                or "503" in msg
                or "unavailable" in msg
                or "deadline" in msg
                or "timeout" in msg
            )
            if attempt >= max_retries or not transient:
                raise
            wait_s = initial_backoff_s * (2 ** (attempt - 1))
            print(
                f"[{label}] attempt {attempt}/{max_retries} failed ({exc.__class__.__name__}: {exc}). "
                f"Retrying in {wait_s:.1f}s..."
            )
            time.sleep(wait_s)
    # Should be unreachable, but keep the type checker happy.
    assert last_exc is not None
    raise last_exc


def has_genai_sdk() -> bool:
    """Check whether the official google-genai SDK is importable."""
    try:
        import google.genai  # noqa: F401
        return True
    except ImportError:
        return False


def call_rest_generate_content(
    *,
    api_key: str,
    model: str,
    payload: dict[str, Any],
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    """Fallback REST call when the SDK isn't available.

    Hits the v1beta generateContent endpoint directly with `requests`.
    """
    import requests  # imported lazily so SDK-only environments don't need it

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
    if resp.status_code != 200:
        # Surface enough info to debug, but don't dump the whole body if it's huge.
        body_preview = resp.text[:500]
        raise RuntimeError(
            f"REST call returned HTTP {resp.status_code}: {body_preview}"
        )
    return resp.json()


def extract_inline_audio_from_response(response_json: dict[str, Any]) -> bytes:
    """Pull the base64 audio payload out of a generateContent response."""
    try:
        candidates = response_json["candidates"]
        parts = candidates[0]["content"]["parts"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(
            f"Unexpected response shape, no candidates/parts found: {e}. "
            f"Full response: {response_json}"
        ) from e

    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            return decode_audio_payload(inline["data"])

    # If we got here, the model returned text instead of audio (the documented
    # 500-class failure mode that triggers a retry).
    text_parts = [p.get("text", "") for p in parts if p.get("text")]
    raise RuntimeError(
        "Response contained no inline audio data. "
        f"Got text instead: {' '.join(text_parts)[:300]}"
    )
