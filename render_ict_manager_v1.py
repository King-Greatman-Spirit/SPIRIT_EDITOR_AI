import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "media" / "originals" / "Ict Mgr - Mr Ola.mp4"
LOGO = BASE / "assets" / "branding" / "bgt_logo.png"
MUSIC = BASE / "assets" / "branding" / "background_music.mp3"
OUT = BASE / "exports" / "ict_manager" / "03_ict_manager_full_interview_v1.mp4"
GRAPHICS = BASE / "analysis" / "ict_manager" / "v1_graphics"

# Confirm all source assets
for path in (SOURCE, LOGO, MUSIC):
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")

if OUT.exists():
    raise FileExistsError(
        f"Output already exists: {OUT}\n"
        "Rename or move it before running this script again."
    )

GRAPHICS.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920

NAVY = (5, 20, 45, 232)
GOLD = (245, 166, 63, 255)
WHITE = (255, 255, 255, 255)

font_regular = Path("C:/Windows/Fonts/arial.ttf")
font_bold = Path("C:/Windows/Fonts/arialbd.ttf")

def font(path, size):
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()

def wrap_text(draw, text, selected_font, max_width):
    words = text.split()
    lines = []
    current = ""

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

# Create elegant question-card overlays.
questions = [
    (1, "Could you introduce yourself and tell us about your role at B.G. Technical Limited?"),
    (2, "What are the key responsibilities of the ICT department?"),
    (3, "What are the major challenges your department faces?"),
    (4, "What advice would you give someone looking to build a career in ICT?"),
]

for number, question in questions:
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Subtle navy question panel
    draw.rounded_rectangle(
        (90, 720, 990, 1200),
        radius=28,
        fill=NAVY,
        outline=(245, 166, 63, 210),
        width=3,
    )

    # Gold accent
    draw.rounded_rectangle(
        (90, 780, 100, 1140),
        radius=5,
        fill=GOLD,
    )

    heading_font = font(font_bold, 31)
    question_font = font(font_bold, 43)

    draw.text(
        (145, 785),
        f"INTERVIEW QUESTION {number:02d}",
        font=heading_font,
        fill=GOLD,
    )

    lines = wrap_text(draw, question, question_font, 770)
    y = 875

    for line in lines:
        draw.text(
            (145, y),
            line,
            font=question_font,
            fill=WHITE,
        )
        y += 64

    image.save(GRAPHICS / f"question_{number}.png")

# Create recurring name and role lower-third.
lower = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(lower)

draw.rounded_rectangle(
    (65, 1530, 790, 1715),
    radius=22,
    fill=(5, 20, 45, 220),
)

draw.rounded_rectangle(
    (65, 1530, 77, 1715),
    radius=5,
    fill=GOLD,
)

draw.text(
    (112, 1560),
    "MR. IBIGBAMI OLAOLUWA",
    font=font(font_bold, 43),
    fill=WHITE,
)

draw.text(
    (112, 1625),
    "ICT MANAGER",
    font=font(font_regular, 29),
    fill=GOLD,
)

lower_path = GRAPHICS / "lower_third.png"
lower.save(lower_path)

# Question intervals established from the transcript.
question_intervals = [
    (0.78, 5.18),
    (12.60, 17.02),
    (99.16, 102.44),
    (147.32, 150.86),
]

def interval_expression(intervals):
    return "+".join(
        f"between(t,{start},{end})"
        for start, end in intervals
    )

question_expr = interval_expression(question_intervals)

audio_mute_intervals = [
    (0.78, 6.20),
    (12.60, 18.44),
    (99.16, 103.92),
    (145.88, 151.92),
]

audio_mute_expr = interval_expression(audio_mute_intervals)

# Lower-third appearances, spaced throughout the interview.
lower_intervals = [
    (22, 32),
    (45, 55),
    (75, 85),
    (112, 122),
    (160, 170),
    (180, 190),
]

lower_expr = interval_expression(lower_intervals)

# FFmpeg inputs:
# 0 = interview video
# 1 = looping background music
# 2 = BGT logo
# 3 = lower third
# 4-7 = question cards
cmd = [
    "ffmpeg", "-y",
    "-i", str(SOURCE),
    "-stream_loop", "-1", "-i", str(MUSIC),
    "-loop", "1", "-framerate", "30", "-i", str(LOGO),
    "-loop", "1", "-framerate", "30", "-i", str(lower_path),
]

for number, _ in questions:
    cmd += [
        "-loop", "1",
        "-framerate", "30",
        "-i", str(GRAPHICS / f"question_{number}.png"),
    ]

filters = []

# Correct the source's unusual sample aspect ratio and create a portrait frame.
filters.append(
    "[0:v]scale=608:1080:flags=lanczos,setsar=1,"
    "scale=1080:1920:flags=lanczos,setsar=1,"
    "split=2[vsharp][vblur]"
)

# Blur the picture only while interviewer questions are displayed.
filters.append(
    f"[vblur]boxblur=18:10:enable='{question_expr}',"
    f"eq=brightness=-0.12:saturation=0.85:enable='{question_expr}'[vblurred]"
)
filters.append(
    f"[vsharp][vblurred]overlay=0:0:enable='{question_expr}'[vbg]"
)

# Larger BGT logo.
filters.append("[2:v]scale=220:-1,format=rgba[logo]")
filters.append("[vbg][logo]overlay=W-w-55:55[vlogo]")

# Recurring name and role.
filters.append("[3:v]format=rgba[lower]")
filters.append(
    f"[vlogo][lower]overlay=0:0:enable='{lower_expr}'[vlower]"
)

# Question cards.
current = "vlower"

for index, (number, (start, end)) in enumerate(zip(
    [item[0] for item in questions],
    question_intervals
)):
    input_index = 4 + index
    next_label = f"vquestion{index + 1}"

    filters.append(f"[{input_index}:v]format=rgba[q{index + 1}]")
    filters.append(
        f"[{current}][q{index + 1}]overlay=0:0:"
        f"enable='between(t,{start},{end})'[{next_label}]"
    )

    current = next_label

filters.append(f"[{current}]null[vout]")

# Remove interviewer audio only during the question intervals.
filters.append(
    f"[0:a]volume=0:enable='{audio_mute_expr}'[voice]"
)

# Music is stronger during question cards and quieter under answers.
filters.append(
    f"[1:a]volume='if({question_expr},0.20,0.055)',"
    "afade=t=out:st=194.78:d=2[music]"
)

filters.append(
    "[voice][music]amix=inputs=2:duration=first:"
    "dropout_transition=2,alimiter=limit=0.95[aout]"
)

filter_complex = ";".join(filters)

cmd += [
    "-filter_complex", filter_complex,
    "-map", "[vout]",
    "-map", "[aout]",
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    "-r", "30",
    "-c:a", "aac",
    "-b:a", "192k",
    "-movflags", "+faststart",
    "-t", "291.04",
    "-shortest",
    str(OUT),
]

print("\nSPIRIT EDITOR AI - VERSION 5")
print("=" * 55)
print("Rendering the complete Store & Journey Manager interview.")
print("Subtitles: removed")
print("Question cards: 4")
print("Interviewer audio: muted during identified question intervals")
print("BGT logo: enlarged")
print("Lower-third: recurring")
print("\nPlease wait. Video rendering may take several minutes.\n")

result = subprocess.run(cmd)

if result.returncode != 0:
    raise RuntimeError("FFmpeg rendering failed. The original recordings remain untouched.")

print("\nVERSION 5 RENDERED SUCCESSFULLY")

probe = subprocess.run(
    [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size",
        "-of", "default=noprint_wrappers=1",
        str(OUT),
    ],
    capture_output=True,
    text=True,
    check=True,
)

print(probe.stdout)
print(f"OUTPUT: {OUT}")
