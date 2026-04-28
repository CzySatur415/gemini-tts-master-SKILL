"""
Multi-speaker (up to 2 speakers) TTS via Gemini 3.1 Flash TTS Preview.

Usage as a module:

    from scripts.tts_multi import generate_multi

    transcript = '''TTS the following conversation between Joe and Jane:
    Joe: How's it going today, Jane?
    Jane: Not too bad, how about you?'''

    generate_multi(
        transcript=transcript,
        speakers=[
            {"name": "Joe",  "voice": "Kore"},
            {"name": "Jane", "voice": "Puck"},
        ],
        output_path="conversation.wav",
    )

Important: speaker names in `transcript` (e.g. "Joe:", "Jane:") MUST match
the `name` field in `speakers` exactly, including case.

Reads GEMINI_API_KEY from the environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TypedDict

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
MAX_SPEAKERS = 2  # Gemini's documented limit


class SpeakerSpec(TypedDict):
    name: str
    voice: str


def _validate_speakers(speakers: list[SpeakerSpec], transcript: str) -> None:
    if len(speakers) == 0:
        raise ValueError("speakers list cannot be empty")
    if len(speakers) > MAX_SPEAKERS:
        raise ValueError(
            f"Gemini 3.1 Flash TTS supports at most {MAX_SPEAKERS} speakers per call. "
            f"Got {len(speakers)}. For more speakers, generate per-speaker segments "
            "and stitch them together with audio editing."
        )
    names = [s["name"] for s in speakers]
    if len(set(names)) != len(names):
        raise ValueError(f"Duplicate speaker names: {names}")
    # Soft warning: each speaker should appear at least once in the transcript.
    for s in speakers:
        if s["name"] not in transcript:
            print(
                f"⚠ Speaker '{s['name']}' is configured but does not appear in the "
                f"transcript. Did you forget a '{s['name']}:' line?",
                file=sys.stderr,
            )


def _generate_via_sdk(
    transcript: str,
    speakers: list[SpeakerSpec],
) -> bytes:
    from google import genai
    from google.genai import types

    speaker_configs = [
        types.SpeakerVoiceConfig(
            speaker=s["name"],
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=s["voice"],
                )
            ),
        )
        for s in speakers
    ]

    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=transcript,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=speaker_configs,
                )
            ),
        ),
    )
    data = response.candidates[0].content.parts[0].inline_data.data
    return data if isinstance(data, (bytes, bytearray)) else bytes(data)


def _generate_via_rest(
    transcript: str,
    speakers: list[SpeakerSpec],
) -> bytes:
    payload = {
        "contents": [{"parts": [{"text": transcript}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "multiSpeakerVoiceConfig": {
                    "speakerVoiceConfigs": [
                        {
                            "speaker": s["name"],
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {"voiceName": s["voice"]}
                            },
                        }
                        for s in speakers
                    ]
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


def generate_multi(
    transcript: str,
    speakers: list[SpeakerSpec],
    output_path: str | Path = "out.wav",
    max_retries: int = 3,
) -> Path:
    """Generate a multi-speaker audio file (up to 2 speakers).

    Args:
        transcript: The full conversation script. Speaker names must be
                    formatted as "Name: line" lines, where each Name matches
                    a `speakers[i]["name"]` exactly. The transcript should
                    typically begin with a framing line such as:
                        "TTS the following conversation between Joe and Jane:"
                    so the prompt classifier knows it's a synthesis request.
        speakers: List of {"name": str, "voice": str} dicts. Up to 2 entries.
                  `voice` must be one of the 30 Gemini prebuilt voice names
                  (see references/voices.md).
        output_path: Where to save the WAV file.
        max_retries: Retry count for transient 5xx errors.

    Returns:
        Path to the saved WAV file.
    """
    _validate_speakers(speakers, transcript)

    backend = _generate_via_sdk if has_genai_sdk() else _generate_via_rest
    label = "multi[" + "+".join(f"{s['name']}={s['voice']}" for s in speakers) + "]"

    pcm_bytes = with_retry(
        lambda: backend(transcript, speakers),
        max_retries=max_retries,
        label=label,
    )

    wav_path = pcm_to_wav(pcm_bytes, output_path)
    print(f"✓ Saved {len(pcm_bytes)} bytes of PCM as WAV → {wav_path}")
    return wav_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-speaker (≤2) Gemini TTS")
    parser.add_argument(
        "--transcript",
        required=True,
        help="Conversation script with 'Name: line' formatting",
    )
    parser.add_argument(
        "--speakers",
        required=True,
        help=(
            'JSON list of speaker specs, e.g.: '
            '\'[{"name":"Joe","voice":"Kore"},{"name":"Jane","voice":"Puck"}]\''
        ),
    )
    parser.add_argument("--output", default="out.wav", help="Output WAV path")
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    try:
        speakers = json.loads(args.speakers)
        generate_multi(
            transcript=args.transcript,
            speakers=speakers,
            output_path=args.output,
            max_retries=args.max_retries,
        )
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"✗ Failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
