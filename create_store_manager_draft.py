from pathlib import Path
import re
import subprocess
import sys

BASE = Path(__file__).resolve().parent

VIDEO = BASE / "media" / "originals" / "Store Mgr - Mr Francis (first).mp4"
LOGO = BASE / "assets" / "branding" / "bgt_logo.png"
SOURCE_SRT = BASE / "transcripts" / "store_manager_small" / "store_manager_transcript.srt"

OUTPUT_DIR = BASE / "exports" / "store_manager"
EDIT_DIR = BASE / "edits" / "store_manager"

OUTPUT = OUTPUT_DIR / "01_commitment_store_journey_manager.mp4"
DRAFT_SRT = EDIT_DIR / "01_commitment_subtitles.srt"

START = 200.05
END = 248.68
DURATION = END - START

def timestamp_to_seconds(value):
    hours, minutes, rest = value.split(":")
    seconds, milliseconds = rest.split(",")
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(milliseconds) / 1000
    )

def seconds_to_timestamp(value):
    value = max(0, value)
    milliseconds = round(value * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def prepare_subtitles():
    content = SOURCE_SRT.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
    output_blocks = []

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue

        match = re.search(
            r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
            lines[1]
        )
        if not match:
            continue

        cue_start = timestamp_to_seconds(match.group(1))
        cue_end = timestamp_to_seconds(match.group(2))

        if cue_end <= START or cue_start >= END:
            continue

        new_start = max(0, cue_start - START)
        new_end = min(DURATION, cue_end - START)

        text = "\n".join(lines[2:]).strip()
        if not text:
            continue

        output_blocks.append(
            f"{len(output_blocks) + 1}\n"
            f"{seconds_to_timestamp(new_start)} --> "
            f"{seconds_to_timestamp(new_end)}\n"
            f"{text}"
        )

    DRAFT_SRT.write_text(
        "\n\n".join(output_blocks) + "\n",
        encoding="utf-8"
    )
    print(f"Prepared {len(output_blocks)} subtitle entries.")

def main():
    for path in (VIDEO, LOGO, SOURCE_SRT):
        if not path.exists():
            print(f"Missing required file: {path}")
            sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EDIT_DIR.mkdir(parents=True, exist_ok=True)

    prepare_subtitles()

    subtitle_path = DRAFT_SRT.relative_to(BASE).as_posix()

    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
        "setsar=1,"
        f"subtitles=filename={subtitle_path}:"
        "force_style='FontName=Arial,FontSize=16,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=1,"
        "Alignment=2,MarginV=170'"
    )

    command = [
        "ffmpeg", "-y",
        "-ss", str(START),
        "-i", str(VIDEO),
        "-i", str(LOGO),
        "-t", str(DURATION),
        "-filter_complex",
        f"[0:v]{video_filter}[base];"
        "[1:v]scale=180:-1[brand];"
        "[base][brand]overlay=W-w-55:55[v]",
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-movflags", "+faststart",
        str(OUTPUT)
    ]

    print("\nCreating B.G. Technical Limited video draft...")
    subprocess.run(command, cwd=BASE, check=True)

    print("\nVIDEO DRAFT CREATED SUCCESSFULLY")
    print(f"Output: {OUTPUT}")

if __name__ == "__main__":
    main()
