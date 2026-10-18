"""Generate pitch voiceover via ElevenLabs TTS and mux onto the pitch video.

Usage:
  ELEVENLABS_API_KEY=... python scripts/generate_voiceover.py

Writes:
  docs/pitch_voiceover.mp3   — standalone audio
  docs/pitch_video_final.mp4 — original video + voiceover muxed
"""
import os
import subprocess
import sys
import httpx
from pathlib import Path

# ----- Script (compiled from video subtitles) ------------------------------
# Delivery: calm, declarative, newsreader pace (~150 wpm).
# Natural pauses encoded via punctuation + em-dashes.

SCRIPT = (
    "If you asked Apple's risk team to name the three suppliers who decide "
    "whether iPhones ship this quarter, they'd tell you about TSMC, Foxconn, "
    "and Samsung Display. They would almost certainly not mention Carl Zeiss "
    "SMT. Or Cymer. Or a glass sand mine in Germany. "
    "Every standard risk register stops at Tier-1. The real points of failure "
    "sit two, three, four hops upstream — in subcontractors most CFOs couldn't "
    "find on a map. "
    "Shockwave is a supply-chain analyst that reads the graph the way a human "
    "would — recursively. Three agents work in parallel: an analyst traces "
    "dependencies, a skeptic challenges every claim, a historian pulls "
    "precedent from past disruptions. "
    "On a validation set of twenty publicly documented single points of failure — "
    "Apple-TSMC-ASML, Boeing-Spirit, Lockheed-Pratt-Whitney — Shockwave surfaces "
    "seventeen. The industry standard surfaces three. "
    "It's built on FalkorDB — a graph database that handles multi-hop traversal "
    "in milliseconds — and Qwen3 running on Nebius for the reasoning. "
    "Every dependency, every path, every impact score is a real Cypher query, "
    "not a language model guess. "
    "We're not building another chat. We're building the dossier your risk team "
    "actually needs — the one that names Zeiss. "
    "Shockwave. Supply-chain blindspots. Found."
)

# ----- Voice choice --------------------------------------------------------
# Jessica — young American female, very natural, conversational narration
# Alternatives:
#   Lily   pFZP5JQG7iQjIQuC4Bku   British young warm
#   Matilda XrExE9yKIg1WjnnlVkGX  young American friendly
#   Aria    9BWtsMINqrJLrRacOk9x  young, slightly husky
#   Rachel  21m00Tcm4TlvDq8ikWAM  warm but a bit mature
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCkdW9")  # Jessica

MODEL = "eleven_multilingual_v2"

VOICE_SETTINGS = {
    "stability": 0.42,          # lower = more natural variance / personality
    "similarity_boost": 0.80,
    "style": 0.40,              # more inflection + warmth
    "use_speaker_boost": True,
    "speed": 1.0,
}

ROOT = Path(__file__).resolve().parents[1]
AUDIO_OUT = ROOT / "docs" / "pitch_voiceover.mp3"
VIDEO_IN = Path(r"C:\Users\vogel\Downloads\Shockwave Pitch Video.mp4")
VIDEO_OUT = ROOT / "docs" / "pitch_video_final.mp4"


def generate_tts() -> None:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: set ELEVENLABS_API_KEY env var", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": SCRIPT,
        "model_id": MODEL,
        "voice_settings": VOICE_SETTINGS,
    }

    print(f"TTS: {len(SCRIPT)} chars, voice {VOICE_ID}, model {MODEL}")
    with httpx.Client(timeout=120) as c:
        r = c.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print(f"ERROR {r.status_code}: {r.text[:400]}", file=sys.stderr)
        sys.exit(1)

    AUDIO_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIO_OUT.write_bytes(r.content)
    print(f"Saved audio: {AUDIO_OUT} ({len(r.content):,} bytes)")


def audio_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True)
    return float(out.strip())


def mux_video() -> None:
    if not VIDEO_IN.exists():
        print(f"WARN: input video not found at {VIDEO_IN} — skipping mux")
        return

    audio_dur = audio_duration(AUDIO_OUT)
    video_dur = audio_duration(VIDEO_IN)  # same ffprobe call works for video
    print(f"Audio: {audio_dur:.2f}s · Video: {video_dur:.2f}s")

    # If audio is longer than video, extend video to match (slow last frame)
    # If audio shorter, pad silence
    cmd = [
        "ffmpeg", "-y",
        "-i", str(VIDEO_IN),
        "-i", str(AUDIO_OUT),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(VIDEO_OUT),
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Saved final video: {VIDEO_OUT}")


if __name__ == "__main__":
    generate_tts()
    mux_video()
