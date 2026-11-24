"""Render intern FIRST (Mr Interviewee Three, ICT Intern).

Interviewer is muted throughout; only the interviewee is audible.
Question cards use the interviewer's real questions from the interview.
Captions are manually corrected and set at 46px for readability.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "media" / "interns" / "FIRST.mp4"
LOGO = BASE / "assets" / "branding" / "bgt_logo.png"
MUSIC = BASE / "assets" / "branding" / "background_music.mp3"
CAPTIONS_JSON = BASE / "transcripts" / "interns" / "first" / "first_captions.json"
OUT_DIR = BASE / "exports" / "interns"
GRAPHICS = BASE / "analysis" / "interns" / "first_graphics"

OUT_FINAL = OUT_DIR / "main_intern_first_bendy_paul_v1.mp4"
OUT_TEST = OUT_DIR / "main_intern_first_bendy_paul_v1_test.mp4"

W, H = 1080, 1920
NAVY = (5, 20, 45, 232)
NAVY_SOFT = (5, 20, 45, 220)
GOLD = (245, 166, 63, 255)
WHITE = (255, 255, 255, 255)
FONT_REGULAR = Path("C:/Windows/Fonts/arial.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")

DATA = json.loads(CAPTIONS_JSON.read_text(encoding="utf-8"))
QUESTIONS = DATA["questions"]
QUESTION_INTERVALS = [tuple(x) for x in DATA["question_intervals"]]
MUTE_INTERVALS = [tuple(x) for x in DATA["mute_intervals"]]


def load_font(path, size):
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def interval_expression(intervals):
    return "+".join(f"between(t,{a},{b})" for a, b in intervals)


def merge_intervals(intervals, tolerance=0.35):
    ordered = sorted(intervals)
    merged = []
    for a, b in ordered:
        if merged and a - merged[-1][1] <= tolerance:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(round(a, 2), round(b, 2)) for a, b in merged]


def make_lower_third():
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((65, 1530, 830, 1715), radius=22, fill=NAVY_SOFT)
    draw.rounded_rectangle((65, 1530, 77, 1715), radius=5, fill=GOLD)
    draw.text((112, 1560), "MR. INTERVIEWEE THREE", font=load_font(FONT_BOLD, 42), fill=WHITE)
    draw.text((112, 1625), "ICT INTERN", font=load_font(FONT_REGULAR, 29), fill=GOLD)
    path = GRAPHICS / "lower_third.png"
    image.save(path)
    return path


def make_question_card(number, question):
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((90, 730, 990, 1170), radius=28, fill=NAVY,
                           outline=(245, 166, 63, 210), width=3)
    draw.rounded_rectangle((90, 795, 100, 1105), radius=5, fill=GOLD)
    draw.text((145, 800), f"INTERVIEW QUESTION {number:02d}",
              font=load_font(FONT_BOLD, 31), fill=GOLD)
    y = 895
    for line in wrap_text(draw, question, load_font(FONT_BOLD, 43), 770):
        draw.text((145, y), line, font=load_font(FONT_BOLD, 43), fill=WHITE)
        y += 64
    path = GRAPHICS / f"question_{number}.png"
    image.save(path)
    return path


def make_subtitle_panel():
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((85, 1695, 995, 1885), radius=24, fill=NAVY,
                           outline=(245, 166, 63, 155), width=2)
    draw.rounded_rectangle((85, 1730, 96, 1850), radius=4, fill=GOLD)
    path = GRAPHICS / "subtitle_panel.png"
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
    font_size = 46
    for start, end, text in captions:
        selected = load_font(FONT_REGULAR, font_size)
        lines = wrap_text(measure, text, selected, 850)
        while len(lines) > 2 and font_size > 30:
            font_size -= 3
            selected = load_font(FONT_REGULAR, font_size)
            lines = wrap_text(measure, text, selected, 850)
        if len(lines) > 2:
            lines = lines[:2]
        ass_text = r"\N".join(lines)
        events.append(
            f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},Caption,,0,0,0,,"
            f"{{\\an5\\pos(540,1790)\\fs{font_size}}}{ass_text}"
        )
    content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(events) + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    for path in (SOURCE, LOGO, MUSIC, CAPTIONS_JSON):
        if not path.exists():
            raise FileNotFoundError(f"Required file missing: {path}")

    OUT = OUT_TEST if args.test else OUT_FINAL
    if OUT.exists():
        raise FileExistsError(f"Output already exists: {OUT}")

    GRAPHICS.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    captions = [(float(a), float(b), t) for a, b, t in DATA["captions"]]
    print(f"Captions: {len(captions)}", flush=True)

    lower_path = make_lower_third()
    question_paths = [make_question_card(i, q) for i, q in enumerate(QUESTIONS, 1)]
    panel_path = make_subtitle_panel()
    logo_path = clean_logo()
    ass_path = write_ass(GRAPHICS / "captions.ass", captions)

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(SOURCE)],
        capture_output=True, text=True, check=True,
    )
    duration = float(probe.stdout.strip())

    question_expr = interval_expression(QUESTION_INTERVALS)
    lower_expr = interval_expression([(8.0, 17.0), (80.0, 89.0), (120.0, 129.0)])
    caption_expr = interval_expression(
        merge_intervals([(a, b) for a, b, _ in captions])
    )
    mute_expr = interval_expression(MUTE_INTERVALS)

    cmd = [
        str(Path(shutil.which("ffmpeg")).resolve()), "-y",
        "-i", str(SOURCE),
        "-stream_loop", "-1", "-i", str(MUSIC),
        "-loop", "1", "-framerate", "30", "-i", str(logo_path),
        "-loop", "1", "-framerate", "30", "-i", str(lower_path),
    ]
    for path in question_paths:
        cmd += ["-loop", "1", "-framerate", "30", "-i", str(path)]
    cmd += ["-loop", "1", "-framerate", "30", "-i", str(panel_path)]

    filters = []
    # Phone clip is coded 3840x2160 with rotation -90 -> display 2160x3840 (9:16).
    filters.append("[0:v]scale=1080:1920:flags=lanczos,setsar=1[base]")
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
    for index, (start, end) in enumerate(QUESTION_INTERVALS):
        input_index = 4 + index
        label = f"vquestion{index + 1}"
        filters.append(f"[{input_index}:v]format=rgba[q{index + 1}]")
        filters.append(
            f"[{current}][q{index + 1}]overlay=0:0:enable='between(t,{start},{end})'[{label}]"
        )
        current = label

    filters.append("[7:v]format=rgba[spanel]")
    filters.append(f"[{current}][spanel]overlay=0:0:enable='{caption_expr}'[vpanel]")
    filters.append("[vpanel]subtitles=filename=captions.ass,setsar=1[vout]")

    filters.append(
        f"[0:a]highpass=f=80,volume=0:enable='{mute_expr}',alimiter=limit=0.89[voice]"
    )
    music_expr = "0.022"
    for start, end in reversed(QUESTION_INTERVALS):
        music_expr = f"if(between(t,{start},{end}),0.056,{music_expr})"
    fade_start = max(0, duration - 2.0)
    filters.append(
        f"[1:a]volume='{music_expr}',"
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
        "-t", f"{render_limit}",
        "-shortest",
        "-movflags", "+faststart",
        str(OUT),
    ]

    print("\nSPIRIT EDITOR AI - INTERN FIRST (MR. INTERVIEWEE THREE) VERSION 1")
    print("=" * 56)
    print(f"Source duration: {duration:.2f} seconds")
    print("Framing: 9:16 portrait, full-bleed 1080x1920")
    print(f"Captions: {len(captions)}, 46px, max 2 lines")
    print(f"Question cards: {len(QUESTIONS)} (from the real interview questions)")
    print("Audio: interviewer fully muted, music ducked 40%")
    print("=" * 56)
    print("\nRendering... Please wait.\n", flush=True)

    log_path = OUT_DIR / (
        "first_v1_test_ffmpeg_error.log" if args.test else "first_v1_ffmpeg_error.log"
    )
    with log_path.open("w", encoding="utf-8") as log_file:
        result = subprocess.run(cmd, stderr=log_file, cwd=str(GRAPHICS))

    if result.returncode != 0:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        raise RuntimeError(
            f"FFmpeg rendering failed (exit {result.returncode}).\n"
            + "\n".join(lines[-60:])
        )

    final = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-show_entries", "format=duration,size",
         "-of", "default=noprint_wrappers=1", str(OUT)],
        capture_output=True, text=True, check=True,
    )
    print(final.stdout.strip())
    print(f"\nOUTPUT: {OUT}")
    print("\nINTERN FIRST (MR. INTERVIEWEE THREE) VERSION 1 RENDERED SUCCESSFULLY")


if __name__ == "__main__":
    main()
