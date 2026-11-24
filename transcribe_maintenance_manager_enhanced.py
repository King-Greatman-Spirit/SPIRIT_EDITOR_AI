
import json
import subprocess
from pathlib import Path
from faster_whisper import WhisperModel

# ==========================================
# SPIRIT EDITOR AI - BGT INTERVIEW TRANSCRIBER
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
VIDEO_DIR = BASE_DIR / "media" / "originals"
OUTPUT_DIR = BASE_DIR / "transcripts" / "maintenance_manager_enhanced"

VIDEO_FILES = [
    "Mtce Mgr - Mr Interviewee One.mp4",
]

MODEL_SIZE = "small"
LANGUAGE = "en"


def get_video_duration(video_path):
    """Read the exact video duration using FFprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format."""
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)

    return (
        f"{hours:02}:{minutes:02}:{seconds:02},"
        f"{milliseconds:03}"
    )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Verify source videos
    for filename in VIDEO_FILES:
        path = VIDEO_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {path}")

    print("\nSPIRIT EDITOR AI")
    print("BGT - Maintenance Manager Interview")
    print("=" * 50)

    print("\nLoading local Whisper model...")
    model = WhisperModel(
        MODEL_SIZE,
        device="cpu",
        compute_type="int8",
    )

    all_segments = []
    interview_offset = 0.0
    video_details = []

    for index, filename in enumerate(VIDEO_FILES, start=1):
        video_path = VIDEO_DIR / filename

        print(f"\n[{index}/{len(VIDEO_FILES)}] Processing:")
        print(filename)

        duration = get_video_duration(video_path)

        print(f"Duration: {duration:.2f} seconds")
        print("Transcribing... Please wait.")

        segments, info = model.transcribe(
            str(video_path),
            language=LANGUAGE,
            beam_size=8,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            condition_on_previous_text=True,
        )

        segment_count = 0

        for segment in segments:
            start = float(segment.start) + interview_offset
            end = float(segment.end) + interview_offset

            all_segments.append({
                "start": round(start, 3),
                "end": round(end, 3),
                "text": segment.text.strip(),
                "source_video": filename,
            })

            segment_count += 1

        video_details.append({
            "filename": filename,
            "duration_seconds": round(duration, 3),
            "language": info.language,
            "language_probability": round(
                info.language_probability, 4
            ),
            "segments": segment_count,
            "offset_seconds": round(interview_offset, 3),
        })

        interview_offset += duration

        print(f"Completed: {segment_count} transcript segments.")

    # Generate TXT
    txt_path = OUTPUT_DIR / "maintenance_manager_transcript.txt"

    with txt_path.open("w", encoding="utf-8") as file:
        file.write("B.G. TECHNICAL LIMITED\n")
        file.write("MAINTENANCE MANAGER INTERVIEW\n")
        file.write("MR. INTERVIEWEE ONE\n")
        file.write("=" * 60 + "\n\n")

        for segment in all_segments:
            start = format_timestamp(segment["start"]).replace(",", ".")
            file.write(f"[{start}] {segment['text']}\n")

    # Generate SRT subtitles
    srt_path = OUTPUT_DIR / "maintenance_manager_transcript.srt"

    with srt_path.open("w", encoding="utf-8") as file:
        for number, segment in enumerate(all_segments, start=1):
            file.write(f"{number}\n")
            file.write(
                f"{format_timestamp(segment['start'])} --> "
                f"{format_timestamp(segment['end'])}\n"
            )
            file.write(segment["text"] + "\n\n")

    # Generate JSON with timestamps and source information
    json_path = OUTPUT_DIR / "maintenance_manager_transcript.json"

    data = {
        "company": "B.G. Technical Limited",
        "interviewee": "Mr. Interviewee One",
        "role": "Maintenance Manager",
        "model": MODEL_SIZE,
        "language": LANGUAGE,
        "combined_duration_seconds": round(interview_offset, 3),
        "source_videos": video_details,
        "segments": all_segments,
    }

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print("\n" + "=" * 50)
    print("TRANSCRIPTION COMPLETED")
    print("=" * 50)
    print(f"Transcript segments: {len(all_segments)}")
    print(f"Combined duration: {interview_offset:.2f} seconds")
    print(f"\nTXT:  {txt_path}")
    print(f"SRT:  {srt_path}")
    print(f"JSON: {json_path}")
    print("\nOriginal video files were not modified.")


if __name__ == "__main__":
    main()



