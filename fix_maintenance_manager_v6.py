from pathlib import Path
import json
import re
import subprocess
import sys

from faster_whisper import WhisperModel

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "media" / "originals" / "Mtce Mgr - Mr Interviewee One.mp4"
V5 = BASE / "render_maintenance_manager_v5.py"
V6 = BASE / "render_maintenance_manager_v6.py"
ANALYSIS = BASE / "analysis" / "maintenance_manager"
ANALYSIS.mkdir(parents=True, exist_ok=True)

OUTPUT = BASE / "exports" / "maintenance_manager" / "main_maintenance_manager_full_interview_v6.mp4"

if OUTPUT.exists():
    raise SystemExit(f"V6 already exists; preserving it: {OUTPUT}")

print("\nSTEP 1/3: Analysing the original interview audio...")
print("Using Faster-Whisper small model with word-level timestamps.")

model = WhisperModel("small", device="cpu", compute_type="int8")

segments, info = model.transcribe(
    str(SOURCE),
    language="en",
    beam_size=3,
    vad_filter=True,
    word_timestamps=True,
    condition_on_previous_text=True
)

words = []
transcript_lines = []

for segment in segments:
    transcript_lines.append(
        f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text.strip()}"
    )

    if segment.words:
        for word in segment.words:
            token = word.word.strip()
            if token and word.start is not None and word.end is not None:
                words.append({
                    "word": token,
                    "start": float(word.start),
                    "end": float(word.end),
                    "probability": float(word.probability or 0)
                })

if not words:
    raise RuntimeError("No word-level timestamps were returned.")

(ANALYSIS / "maintenance_manager_v6_transcript.txt").write_text(
    "\n".join(transcript_lines), encoding="utf-8"
)

print(f"Recognised {len(words)} words.")
print("\nSTEP 2/3: Aligning captions to spoken words...")

# Group words into readable phrases. Break at natural pauses,
# punctuation, or sensible phrase lengths.
captions = []
group = []

def finish_group():
    global group
    if not group:
        return

    text = " ".join(item["word"] for item in group)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    start = max(0.0, group[0]["start"] - 0.04)
    end = group[-1]["end"] + 0.08

    if text.strip() and end > start:
        captions.append([round(start, 3), round(end, 3), text.strip()])

    group = []

for item in words:
    if group:
        previous = group[-1]
        pause = item["start"] - previous["end"]
        current_duration = item["end"] - group[0]["start"]
        previous_text = previous["word"]

        punctuation_break = bool(re.search(r"[.!?]$", previous_text))
        phrase_break = bool(re.search(r"[,;:]$", previous_text))

        if (
            pause > 0.48
            or punctuation_break
            or phrase_break and len(group) >= 3
            or len(group) >= 7
            or current_duration > 4.2
        ):
            finish_group()

    group.append(item)

finish_group()

json_path = ANALYSIS / "maintenance_manager_v6_captions.json"
json_path.write_text(json.dumps(captions, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Created {len(captions)} synchronised subtitle phrases.")
print(f"Transcript saved: {ANALYSIS / 'maintenance_manager_v6_transcript.txt'}")

print("\nSTEP 3/3: Preparing V6 with the approved subtitle design...")

script = V5.read_text(encoding="utf-8")

replacements = {
    "main_maintenance_manager_full_interview_v5.mp4":
        "main_maintenance_manager_full_interview_v6.mp4",
    "maintenance_manager_v5_ffmpeg_error.log":
        "maintenance_manager_v6_ffmpeg_error.log",
    "v5_graphics": "v6_graphics",
    "maintenance_manager_v5_subtitles.ass":
        "maintenance_manager_v6_subtitles.ass",
    "VERSION 5": "VERSION 6",
    "VERSION 5 RENDERED SUCCESSFULLY":
        "VERSION 6 RENDERED SUCCESSFULLY"
}

for old, new in replacements.items():
    script = script.replace(old, new)

# Replace the old manually timed captions with the new audio-derived timings.
pattern = r"captions\s*=\s*\[.*?\]"
match = re.search(pattern, script, flags=re.DOTALL)

if not match:
    raise RuntimeError("Could not locate the original captions list in V5.")

dynamic_captions = (
    'captions = json.loads((BASE / "analysis" / "maintenance_manager" '
    '/ "maintenance_manager_v6_captions.json").read_text(encoding="utf-8"))'
)

script = script[:match.start()] + dynamic_captions + script[match.end():]

if "import json" not in script:
    script = script.replace(
        "import subprocess",
        "import subprocess\nimport json",
        1
    )

V6.write_text(script, encoding="utf-8")

print(f"V6 script: {V6}")
print("Subtitle appearance: approved navy / white / gold design")
print("Subtitle timing: generated from original audio")
print("\nStarting V6 render...\n")

result = subprocess.run([sys.executable, str(V6)], cwd=str(BASE))

if result.returncode != 0:
    raise SystemExit(f"V6 rendering failed with exit code {result.returncode}.")

if not OUTPUT.exists() or OUTPUT.stat().st_size < 1_000_000:
    raise RuntimeError("V6 output is missing or unexpectedly small.")

print("\nV6 RENDER COMPLETED.")
print(f"Output: {OUTPUT}")
