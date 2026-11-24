from pathlib import Path
from faster_whisper import WhisperModel

base = Path(__file__).resolve().parent
video = base / "media" / "originals" / "Pps Cordinator - Mr Interviewee Two.mp4"
out = base / "analysis" / "pps_coordinator"
out.mkdir(parents=True, exist_ok=True)

print("TRANSCRIBING: PPS COORDINATOR - MR. INTERVIEWEE TWO")
print("Model: medium | CPU int8")
print("Please wait...\n")

model = WhisperModel("medium", device="cpu", compute_type="int8")

segments, info = model.transcribe(
    str(video),
    language="en",
    beam_size=5,
    vad_filter=True,
    word_timestamps=True
)

transcript = []
srt = []
index = 1

def stamp(seconds):
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

for segment in segments:
    line = f"[{segment.start:08.2f} - {segment.end:08.2f}] {segment.text.strip()}"
    transcript.append(line)
    srt.append(
        f"{index}\n{stamp(segment.start)} --> {stamp(segment.end)}\n"
        f"{segment.text.strip()}\n"
    )
    index += 1

txt_path = out / "pps_coordinator_transcript.txt"
srt_path = out / "pps_coordinator_transcript.srt"

txt_path.write_text("\n".join(transcript), encoding="utf-8")
srt_path.write_text("\n".join(srt), encoding="utf-8-sig")

print("\n========== TRANSCRIPT ==========\n")
print("\n".join(transcript))
print("\n========== FILES SAVED ==========")
print(txt_path)
print(srt_path)
print(f"\nDetected language: {info.language}")
print(f"Duration: {info.duration:.2f} seconds")
