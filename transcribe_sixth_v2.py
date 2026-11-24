import json
from pathlib import Path

from faster_whisper import WhisperModel

BASE = Path(__file__).resolve().parent
SRC = BASE / "media" / "interns" / "SIXTH.mp4"
OUT = BASE / "analysis" / "interns"
OUT.mkdir(parents=True, exist_ok=True)

print("Loading medium model with word timestamps...", flush=True)
model = WhisperModel("medium", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    str(SRC),
    language="en",
    beam_size=8,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=400),
    condition_on_previous_text=True,
    word_timestamps=True,
    initial_prompt=(
        "This is an interview at B.G. Technical (BGT), an oil and gas engineering "
        "company in Port Harcourt, Nigeria. They discuss SIWES industrial training "
        "placements, the maintenance department, engineering equipment, pipelines, "
        "and recommendations for future interns."
    ),
)

rows = []
for seg in segments:
    words = [
        {"start": round(w.start, 2), "end": round(w.end, 2),
         "word": w.word, "prob": round(w.probability, 3)}
        for w in (seg.words or [])
    ]
    rows.append({
        "start": round(seg.start, 2),
        "end": round(seg.end, 2),
        "text": seg.text.strip(),
        "words": words,
    })
    print(f"[{seg.start:7.2f}-{seg.end:7.2f}] {seg.text.strip()}", flush=True)

(OUT / "segments_sixth_words.json").write_text(
    json.dumps({"language": info.language, "segments": rows}, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"\nSaved {OUT / 'segments_sixth_words.json'}", flush=True)
