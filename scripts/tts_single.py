"""
Single-speaker TTS via Gemini 3.1 Flash TTS Preview.

Usage as a module:

    from scripts.tts_single import generate_single

    generate_single(
        text="Have a wonderful day!",
        voice_name="Kore",
        output_path="out.wav",
        style_prompt="Say cheerfully:",  # optional
    )

Usage as CLI:

    python scripts/tts_single.py \\
        --voice Kore \\
        --output out.wav \\
        --text "Have a wonderful day!" \\
        --style "Say cheerfully:"

Reads GEMINI_API_KEY from the environment.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as a script (python scripts/tts_single.py ...) by adding the
# parent dir to sys.path so the sibling `utils` module resolves.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from utils import (  # noqa: E402
    call_rest_generate_content,
    extract_inline_audio_from_response,
    get_api_key,
    has_genai_sdk,
    pcm_to_wav,
    with_retry,
)

MODEL_ID = "gemini-3.1-flash-tts-preview"


def _build_prompt(text: str, style_prompt: str | None) -> str:
    """Compose a single-string prompt that minimizes the prompt-classifier
    failure mode where style instructions get spoken aloud.

    Strategy: when a style prompt is supplied, wrap the actual text in quotes
    and prefix with a clear "Read the following:" marker. When no style is
    supplied, pass through verbatim.
    """
    if not style_prompt:
        return text

    style = style_prompt.strip()
    # If the user already wrote something like "Say cheerfully:", keep their
    # form — it's a recognized lightweight pattern in the docs.
    if style.endswith(":"):
        return f'{style} "{text}"'

    return f'{style}\n\nRead the following aloud:\n"{text}"'


def _generate_via_sdk(
    prompt: str,
    voice_name: str,
) -> bytes:
    """Use the official google-genai SDK if available."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name,
                    )
                )
            ),
        ),
    )
    data = response.candidates[0].content.parts[0].inline_data.data
    return data if isinstance(data, (bytes, bytearray)) else bytes(data)


def _generate_via_rest(
    prompt: str,
    voice_name: str,
) -> bytes:
    """Fallback: hit the REST endpoint directly."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice_name}
                }
            },
        },
    }
    response_json = call_rest_generate_content(
        api_key=get_api_key(),
        model=MODEL_ID,
        payload=payload,
    )
    return extract_inline_audio_from_response(response_json)


def generate_single(
    text: str,
    voice_name: str = "Kore",
    output_path: str | Path = "out.wav",
    style_prompt: str | None = None,
    max_retries: int = 3,
) -> Path:
    """Generate single-speaker TTS audio and save it as a WAV file.

    Args:
        text: The transcript to speak. Can include audio tags like
              [whispers] or [excited]. Can mix English tags with text in
              other languages.
        voice_name: One of the 30 Gemini prebuilt voices. See
                    references/voices.md. Defaults to 'Kore' (Firm).
        output_path: Where to save the WAV file. Parent dirs are created.
        style_prompt: Optional natural-language style direction. The function
                      wraps the transcript in quotes to keep the prompt
                      classifier from reading the style aloud. Examples:
                          "Say cheerfully:"
                          "You are a calm documentary narrator. Read slowly:"
        max_retries: Retry count for transient 5xx errors (the model
                     occasionally returns text instead of audio).

    Returns:
        Path to the saved WAV file.
    """
    prompt = _build_prompt(text, style_prompt)

    use_sdk = has_genai_sdk()
    backend = _generate_via_sdk if use_sdk else _generate_via_rest

    pcm_bytes = with_retry(
        lambda: backend(prompt, voice_name),
        max_retries=max_retries,
        label=f"single-speaker[{voice_name}]",
    )

    wav_path = pcm_to_wav(pcm_bytes, output_path)
    print(f"✓ Saved {len(pcm_bytes)} bytes of PCM as WAV → {wav_path}")
    return wav_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Single-speaker Gemini TTS")
    parser.add_argument("--text", required=True, help="Transcript to speak")
    parser.add_argument(
        "--voice",
        default="Kore",
        help="One of 30 Gemini voices (default: Kore). See references/voices.md",
    )
    parser.add_argument(
        "--output",
        default="out.wav",
        help="Output WAV file path (default: out.wav)",
    )
    parser.add_argument(
        "--style",
        default=None,
        help='Optional style prompt, e.g. "Say cheerfully:"',
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Retry count on transient 5xx errors (default: 3)",
    )
    args = parser.parse_args()

    try:
        generate_single(
            text=args.text,
            voice_name=args.voice,
            output_path=args.output,
            style_prompt=args.style,
            max_retries=args.max_retries,
        )
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"✗ Failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
