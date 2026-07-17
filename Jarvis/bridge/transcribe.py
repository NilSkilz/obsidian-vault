#!/usr/bin/env python3
"""Transcribe a Telegram voice note to text with faster-whisper (local, CPU).

Standalone helper so bridge.py stays stdlib-only. Reads an audio file path as
argv[1], prints the transcript to stdout, nothing else. Telegram voice notes are
OGG/Opus; faster-whisper decodes them via bundled PyAV/ffmpeg, so no system
ffmpeg is needed. Runs in its own venv (see WHISPER_PY in bridge.py).

Model + compute type are overridable via env (JARVIS_WHISPER_MODEL,
JARVIS_WHISPER_COMPUTE). Default base.en/int8: fast on 4 CPU cores, low RAM,
good enough for dictation. Bump to small.en if proper nouns get mangled.

The model is loaded fresh per invocation (one short note = a second or two of
load). Kept simple on purpose: no daemon, no shared state, survives model swaps.
"""
import os
import sys

MODEL = os.environ.get("JARVIS_WHISPER_MODEL", "base.en")
COMPUTE = os.environ.get("JARVIS_WHISPER_COMPUTE", "int8")
CACHE = os.environ.get(
    "JARVIS_WHISPER_CACHE",
    os.path.expanduser("~/.local/share/jarvis-whisper/models"),
)


def main():
    if len(sys.argv) < 2:
        print("", end="")
        return
    audio = sys.argv[1]
    from faster_whisper import WhisperModel

    model = WhisperModel(MODEL, device="cpu", compute_type=COMPUTE, download_root=CACHE)
    segments, _info = model.transcribe(audio, beam_size=1, vad_filter=True)
    text = "".join(seg.text for seg in segments).strip()
    print(text, end="")


if __name__ == "__main__":
    main()
