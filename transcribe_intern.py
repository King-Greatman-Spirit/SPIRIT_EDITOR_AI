import json
import sys
from pathlib import Path

from faster_whisper import WhisperModel

BASE = Path(__file__).resolve().parent
SRC = BASE / "media" / "interns" / f"{sys.argv[1]}.mp4"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "large-v3"
OUT = BASE / "transcripts" / "interns" / sys.argv[1].lower()
OUT.mkdir(parents=True, exist_ok=True)

print(f"Transcribing {SRC.name} with {MODEL}...", flush=True)
segments, info = WhisperModel(MODEL, device="cpu", compute_type="int8").transcribe(
    str(SRC), language="en", beam_size=8, vad_filter=True,
    condition_on_previous_text=False,
)

rows = []
for s in segments:
    text = s.text.strip()
    if not text:
        continue
    rows.append({"start": round(s.start, 2), "end": round(s.end, 2),
                 "text": text})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {text}", flush=True)

(OUT / f"{sys.argv[1].lower()}_transcript.json").write_text(
    json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
)


def ts(sec):
    ms = round(sec * 1000)
    h, r = divmod(ms, 3_600_000)
    m, r = divmod(r, 60_000)
    s, ms = divmod(r, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


with (OUT / f"{sys.argv[1].lower()}_transcript.srt").open("w", encoding="utf-8") as f:
    for i, r in enumerate(rows, 1):
        f.write(f"{i}\n{ts(r['start'])} --> {ts(r['end'])}\n{r['text']}\n\n")

print(f"\nwrote {OUT}", flush=True)
