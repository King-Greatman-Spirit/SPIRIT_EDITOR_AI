import json
import subprocess
from pathlib import Path
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).resolve().parent
VIDEO_PATH = BASE_DIR / "media" / "originals" / "Ict Mgr - Mr Ola.mp4"
OUTPUT_DIR = BASE_DIR / "transcripts" / "ict_manager"

MODEL_SIZE = "small"
LANGUAGE = "en"


def get_video_duration(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def main():
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"Video not found: {VIDEO_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nSPIRIT EDITOR AI")
    print("B.G. TECHNICAL LIMITED")
    print("ICT MANAGER - MR. OLA")
    print("=" * 50)

    duration = get_video_duration(VIDEO_PATH)
    print(f"\nVideo duration: {duration:.2f} seconds")
    print("Loading local Whisper small model...")

    model = WhisperModel(
        MODEL_SIZE,
        device="cpu",
        compute_type="int8",
    )

    print("Transcribing... Please wait.")

    segments, info = model.transcribe(
        str(VIDEO_PATH),
        language=LANGUAGE,
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=True,
    )

    all_segments = []

    for segment in segments:
        all_segments.append({
            "start": round(float(segment.start), 3),
            "end": round(float(segment.end), 3),
            "text": segment.text.strip(),
        })

    txt_path = OUTPUT_DIR / "ict_manager_transcript.txt"
    srt_path = OUTPUT_DIR / "ict_manager_transcript.srt"
    json_path = OUTPUT_DIR / "ict_manager_transcript.json"

    with txt_path.open("w", encoding="utf-8") as file:
        file.write("B.G. TECHNICAL LIMITED\n")
        file.write("ICT MANAGER INTERVIEW\n")
        file.write("MR. OLA\n")
        file.write("=" * 60 + "\n\n")

        for segment in all_segments:
            start = timestamp(segment["start"]).replace(",", ".")
            end = timestamp(segment["end"]).replace(",", ".")
            file.write(f"[{start} - {end}] {segment['text']}\n")

    with srt_path.open("w", encoding="utf-8") as file:
        for number, segment in enumerate(all_segments, start=1):
            file.write(f"{number}\n")
            file.write(
                f"{timestamp(segment['start'])} --> "
                f"{timestamp(segment['end'])}\n"
            )
            file.write(segment["text"] + "\n\n")

    data = {
        "company": "B.G. Technical Limited",
        "interviewee": "Mr. Ola",
        "role": "ICT Manager",
        "source_video": VIDEO_PATH.name,
        "duration_seconds": round(duration, 3),
        "model": MODEL_SIZE,
        "language": info.language,
        "language_probability": round(info.language_probability, 4),
        "segments": all_segments,
    }

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print("\n" + "=" * 50)
    print("TRANSCRIPTION COMPLETED")
    print("=" * 50)
    print(f"Segments: {len(all_segments)}")
    print(f"TXT:  {txt_path}")
    print(f"SRT:  {srt_path}")
    print(f"JSON: {json_path}")
    print("\nOriginal video remains untouched.")


if __name__ == "__main__":
    main()
