import argparse
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "media" / "originals" / "Pps Cordinator - Mr Interviewee Two.mp4"
LOGO = BASE / "assets" / "branding" / "bgt_logo.png"
MUSIC = BASE / "assets" / "branding" / "background_music.mp3"
TRANSCRIPT = BASE / "transcripts" / "jesse_pps_small" / "jesse_pps_transcript.json"
OUT_DIR = BASE / "exports" / "jesse_pps"
GRAPHICS = BASE / "analysis" / "jesse_pps" / "v1_graphics"

OUT_FINAL = OUT_DIR / "main_jesse_pps_full_interview_v1.mp4"
OUT_TEST = OUT_DIR / "main_jesse_pps_full_interview_v1_test.mp4"

W, H = 1080, 1920
NAVY = (5, 20, 45, 232)
NAVY_SOFT = (5, 20, 45, 220)
GOLD = (245, 166, 63, 255)
WHITE = (255, 255, 255, 255)
FONT_REGULAR = Path("C:/Windows/Fonts/arial.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")

questions = [
    (1, "Please introduce yourself and your role at B.G. Technical."),
    (2, "What are your responsibilities in your department?"),
    (3, "What challenges do you normally face in your department?"),
    (4, "What would you advise someone who wants to come into your field?"),
]

# Interviewer questions, measured from word timestamps.
question_intervals = [
    (2.90, 6.60),
    (17.10, 21.30),
    (77.00, 81.50),
    (121.40, 126.00),
]

# Interviewer voice — mute completely, his voice is never muted.
audio_mute_intervals = [
    (0.00, 1.60),
    (2.90, 6.60),
    (15.60, 21.30),
    (77.00, 81.50),
    (121.40, 126.00),
    (138.40, 141.40),
    (171.50, 176.85),
]

lower_intervals = [
    (11.5, 16.5),
    (40.5, 45.0),
    (56.5, 61.5),
    (91.5, 96.5),
    (149.5, 154.5),
]


def load_font(path, size):
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def wrap_text(draw, text, selected_font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=selected_font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def clean_text(text):
    replacements = [
        ("Interviewee Two", "Interviewee Two"),
        ("Interviewee Two.", "Interviewee Two"),
        ("BG Technical", "B.G. Technical"),
        ("BGT", "B.G. Technical"),
        ("Good operations in the base are also operations outside",
         "Field operations in the base and also operations outside"),
        ("planning and planning", "planning"),
        ("personal selection", "personnel selection"),
        ("documentation to pre-mobilization documentation like",
         "pre-mobilization documentation like"),
        ("my responsibilities are responsible for", "my responsibilities include"),
        ("the thing is have engineering background", "the thing is, have an engineering background"),
        ("For me our advice should have an engineering background",
         "For me, I advise we should have an engineering background"),
        ("the basics For me", "the basics. For me"),
        ("assurance that yes they can", "assurance that yes they can do it"),
        ("Okay, I'm busy.", "Okay, basically."),
    ]
    cleaned = text.strip()
    for old, new in replacements:
        cleaned = cleaned.replace(old, new)
    # capitalise first letter and ensure ending punctuation
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
        if not cleaned.endswith((".", "!", "?", "…")):
            cleaned += "."
    return cleaned


def load_captions():
    data = json.loads(TRANSCRIPT.read_text(encoding="utf-8"))
    captions = []
    for seg in data["segments"]:
        start = float(seg["start"])
        end = float(seg["end"])
        # Segment 1 merges the interviewer's greeting/question with his answer.
        if start < 2:
            start, end = 7.10, 9.90
            text = "My name is Interviewee Two."
        else:
            text = seg["text"]
        cleaned = clean_text(text)
        if cleaned in (".", "…", ""):
            continue
        # Split long captions into two halves for 2-line readability
        words = cleaned.split()
        if len(cleaned) > 130 and len(words) >= 8:
            mid = len(words) // 2
            first = " ".join(words[:mid])
            second = " ".join(words[mid:])
            if not first.endswith((".", "!", "?")):
                first += ""
            if not second[0].isupper():
                second = second[0].upper() + second[1:]
            split_at = start + (end - start) * (len(first) / max(1, len(cleaned)))
            captions.append((start, round(split_at, 2), first))
            captions.append((round(split_at + 0.04, 2), end, second))
        else:
            captions.append((start, end, cleaned))
    # Remove overlaps / out-of-order, keep at least 0.6s
    captions.sort()
    fixed = []
    for start, end, text in captions:
        if end - start < 0.6:
            end = start + 0.6
        if fixed and start < fixed[-1][1]:
            start = fixed[-1][1] + 0.04
            if end <= start:
                continue
        fixed.append((round(start, 2), round(end, 2), text))

    # v2: remove/trim captions that overlap muted interviewer audio.
    trimmed = []
    for start, end, text in fixed:
        keep = True
        for mute_start, mute_end in audio_mute_intervals:
            if start < mute_end and end > mute_start:
                if start >= mute_start and end <= mute_end:
                    keep = False
                    break
                if start < mute_start and end > mute_start and end <= mute_end:
                    end = mute_start - 0.04
                elif start >= mute_start and start < mute_end and end > mute_end:
                    start = mute_end + 0.04
                elif start < mute_start and end > mute_end:
                    # split not needed for v2; trim to after mute
                    start = mute_end + 0.04
        if keep and end - start >= 0.6:
            trimmed.append((round(start, 2), round(end, 2), text))
    return trimmed


def make_lower_third():
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((65, 1530, 800, 1715), radius=22, fill=NAVY_SOFT)
    draw.rounded_rectangle((65, 1530, 77, 1715), radius=5, fill=GOLD)
    draw.text((112, 1560), "MR. INTERVIEWEE TWO", font=load_font(FONT_BOLD, 42), fill=WHITE)
    draw.text((112, 1625), "PPS COORDINATOR", font=load_font(FONT_REGULAR, 29), fill=GOLD)
    path = GRAPHICS / "lower_third.png"
    image.save(path)
    return path


def make_question_card(number, question):
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((90, 740, 990, 1160), radius=28, fill=NAVY, outline=(245, 166, 63, 210), width=3)
    draw.rounded_rectangle((90, 800, 100, 1100), radius=5, fill=GOLD)
    draw.text((145, 805), f"INTERVIEW QUESTION {number:02d}", font=load_font(FONT_BOLD, 31), fill=GOLD)
    lines = wrap_text(draw, question, load_font(FONT_BOLD, 43), 770)
    y = 895
    for line in lines:
        draw.text((145, y), line, font=load_font(FONT_BOLD, 43), fill=WHITE)
        y += 64
    path = GRAPHICS / f"question_{number}.png"
    image.save(path)
    return path


def make_subtitle_panel():
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((100, 1725, 980, 1865), radius=22, fill=NAVY, outline=(245, 166, 63, 155), width=2)
    draw.rounded_rectangle((100, 1750, 109, 1840), radius=4, fill=GOLD)
    path = GRAPHICS / "subtitle_panel.png"
    image.save(path)
    return path


def make_foreground_shadow():
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((14, FG_Y + 18, W - 14, FG_Y + FG_H + 18), fill=(0, 0, 0, 150))
    image = image.filter(ImageFilter.GaussianBlur(22))
    path = GRAPHICS / "foreground_shadow.png"
    image.save(path)
    return path


def clean_logo():
    image = Image.open(LOGO).convert("RGB")
    pixels = image.load()
    border = (39, 107, 161)
    for y in range(image.height):
        for x in range(image.width):
            r, g, b = pixels[x, y]
            if max(r, g, b) < 80:
                pixels[x, y] = border
    image = image.crop((0, 0, 314, 213))
    path = GRAPHICS / "bgt_logo_clean.png"
    image.save(path)
    return path


def ass_timestamp(seconds):
    total_cs = round(seconds * 100)
    hours, remainder = divmod(total_cs, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def write_ass(path, captions):
    measure_image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    measure = ImageDraw.Draw(measure_image)
    events = []
    max_font = 37
    for start, end, text in captions:
        font_size_local = max_font
        selected = load_font(FONT_REGULAR, font_size_local)
        lines = wrap_text(measure, text, selected, 790)
        while len(lines) > 2 and font_size_local > 24:
            font_size_local -= 3
            selected = load_font(FONT_REGULAR, font_size_local)
            lines = wrap_text(measure, text, selected, 790)
        if len(lines) > 2:
            lines = lines[:2]
        ass_text = r"\N".join(lines)
        events.append(
            f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},Caption,,0,0,0,,"
            f"{{\\an5\\pos(540,1795)\\fs{font_size_local}}}{ass_text}"
        )
    content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,{max_font},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(events) + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def interval_expression(intervals):
    return "+".join(f"between(t,{start},{end})" for start, end in intervals)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    for path in (SOURCE, LOGO, MUSIC, TRANSCRIPT):
        if not path.exists():
            raise FileNotFoundError(f"Required file missing: {path}")

    OUT = OUT_TEST if args.test else OUT_FINAL
    if OUT.exists():
        raise FileExistsError(f"Output already exists: {OUT}")

    GRAPHICS.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    captions = load_captions()
    print(f"Captions prepared: {len(captions)}")

    lower_path = make_lower_third()
    question_paths = [make_question_card(number, text) for number, text in questions]
    panel_path = make_subtitle_panel()
    logo_path = clean_logo()
    ass_path = write_ass(GRAPHICS / "captions.ass", captions)

    probe = subprocess.run(
        [str(Path(shutil.which("ffprobe")).resolve()), "-v", "error",
         "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(SOURCE)],
        capture_output=True, text=True, check=True,
    )
    duration = float(probe.stdout.strip())

    question_expr = interval_expression(question_intervals)
    lower_expr = interval_expression(lower_intervals)
    caption_expr = interval_expression([(start, end) for start, end, _ in captions])
    audio_mute_expr = interval_expression(audio_mute_intervals)

    cmd = [
        str(Path(shutil.which("ffmpeg")).resolve()), "-y",
        "-i", str(SOURCE),
        "-stream_loop", "-1", "-i", str(MUSIC),
        "-loop", "1", "-framerate", "30", "-i", str(logo_path),
        "-loop", "1", "-framerate", "30", "-i", str(lower_path),
    ]
    for path in question_paths:
        cmd += ["-loop", "1", "-framerate", "30", "-i", str(path)]
    cmd += [
        "-loop", "1", "-framerate", "30", "-i", str(panel_path),
    ]

    filters = []
    # Source is 1920x1080 coded but SAR 81:256, DAR 9:16 portrait.
    # Correct to display 608x1080 square pixels, then to 1080x1920 full-bleed.
    filters.append(
        "[0:v]scale=608:1080:flags=lanczos,setsar=1,"
        "scale=1080:1920:flags=lanczos,setsar=1[base]"
    )
    filters.append(
        "[base]split=2[sharp][soft];"
        "[soft]scale=360:640,boxblur=8:4,scale=1080:1920:flags=bicubic,"
        "eq=brightness=-0.16:saturation=0.82[soft2];"
        f"[sharp][soft2]overlay=0:0:enable='{question_expr}'[vbg]"
    )
    filters.append("[2:v]scale=190:-1,format=rgba[logo]")
    filters.append("[vbg][logo]overlay=W-w-55:55[vlogo]")
    filters.append("[3:v]format=rgba[lower]")
    filters.append(f"[vlogo][lower]overlay=0:0:enable='{lower_expr}'[vlower]")

    current = "vlower"
    for index, (start, end) in enumerate(question_intervals):
        input_index = 4 + index
        label = f"vquestion{index + 1}"
        filters.append(f"[{input_index}:v]format=rgba[q{index + 1}]")
        filters.append(f"[{current}][q{index + 1}]overlay=0:0:enable='between(t,{start},{end})'[{label}]")
        current = label

    filters.append("[8:v]format=rgba[spanel]")
    filters.append(f"[{current}][spanel]overlay=0:0:enable='{caption_expr}'[vpanel]")
    filters.append("[vpanel]subtitles=filename=captions.ass,setsar=1[vout]")

    # v2: interviewer completely muted, interviewee untouched apart from clean-up.
    filters.append(
        f"[0:a]highpass=f=80,volume=0:enable='{audio_mute_expr}',alimiter=limit=0.89[voice]"
    )

    fade_start = max(0, duration - 2.0)
    filters.append(
        "[1:a]volume='if(" + question_expr + ",0.056,0.022)',"
        f"afade=t=out:st={fade_start:.3f}:d=2[music]"
    )
    filters.append(
        "[voice][music]amix=inputs=2:duration=first:"
        "dropout_transition=2:normalize=0,alimiter=limit=0.95[aout]"
    )

    filter_complex = ";".join(filters)
    render_limit = 6.0 if args.test else duration

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-t", f"{render_limit:.3f}",
        "-shortest",
        str(OUT),
    ]

    print("\nSPIRIT EDITOR AI - PPS COORDINATOR (MR. INTERVIEWEE TWO) VERSION 1")
    print("=" * 58)
    print(f"Source duration: {duration:.2f} seconds")
    print("Framing: Original 9:16 display ratio, full-bleed 1080x1920")
    print(f"Captions: {len(captions)}, max 2 lines, ASS subtitles")
    print("Question cards: 4, lower-third recurring")
    print("Audio: interviewer completely muted, interviewee only, music ducked")
    print("Logo: corner artefacts removed")
    print("\nRendering... Please wait.\n")

    log_path = OUT_DIR / ("jesse_pps_v1_test_ffmpeg_error.log" if args.test else "jesse_pps_v1_ffmpeg_error.log")
    print(f"FFmpeg diagnostic log: {log_path}")
    print(f"FFmpeg executable: {cmd[0]}")
    print(f"FFmpeg arguments: {len(cmd)}")

    with log_path.open("w", encoding="utf-8", errors="replace") as log_file:
        result = subprocess.run(cmd, stderr=log_file, cwd=str(GRAPHICS))

    if result.returncode != 0:
        print("\nFFmpeg failed. Last 60 diagnostic lines:")
        log_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        print("\n".join(log_lines[-60:]))
        raise RuntimeError(f"FFmpeg rendering failed (exit code {result.returncode}). See log: {log_path}")

    final_probe = subprocess.run(
        [str(Path(shutil.which("ffprobe")).resolve()), "-v", "error",
         "-show_entries", "format=duration,size:stream=width,height",
         "-of", "default=noprint_wrappers=1", str(OUT)],
        capture_output=True, text=True, check=True,
    )
    print("\nPPS COORDINATOR (MR. INTERVIEWEE TWO) VERSION 1 RENDERED SUCCESSFULLY")
    print(final_probe.stdout)
    print(f"OUTPUT: {OUT}")


if __name__ == "__main__":
    main()
