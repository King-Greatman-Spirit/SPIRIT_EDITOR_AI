import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "media" / "originals" / "Ict Mgr - Mr Ola.mp4"
LOGO = BASE / "assets" / "branding" / "bgt_logo.png"
MUSIC = BASE / "assets" / "branding" / "background_music.mp3"
OUT = BASE / "exports" / "ict_manager" / "03_ict_manager_full_interview_v5.mp4"
GRAPHICS = BASE / "analysis" / "ict_manager" / "v2_graphics"

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

FONT_REGULAR = Path("C:/Windows/Fonts/arial.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")


def load_font(path, size):
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


# Caption wording is edited for readability. User-verified phrases
# are retained. Please review the final subtitles against the audio.
captions = [
    (6.20, 11.84, "My name is Olaoluwa, and I'm in charge of ICT at B.G. Technical Limited."),
    (18.44, 24.50, "My department takes care of everything ICT at B.G. Technical Limited,"),
    (24.50, 29.08, "starting with ICT support."),
    (29.08, 35.38, "which is basically the everyday part of what we do."),
    (35.90, 40.70, "We provide support to all our end users."),
    (40.70, 46.54, "So they can effectively use ICT resources for their daily work and tasks."),
    (49.04, 56.14, "We manage and administer the ICT infrastructure."),
    (57.06, 64.08, "That is, housing the resources we have spread all over the place."),
    (64.08, 72.58, "We are responsible for cybersecurity and for the protection of data and infrastructure."),
    (72.58, 76.00, "My department is also responsible for charting the course."),
    (76.00, 80.22, "We ensure we design and implement technology solutions."),
    (80.22, 85.50, "to address organisational challenges and position B.G. Technical Limited"),
    (85.50, 89.36, "as a leading oil and sanitary company,"),
    (89.36, 98.14, "not just in Nigeria, but all over the world."),
    (103.92, 114.12, "Well, the challenges are numerous, and they range across the infrastructure we manage"),
    (114.12, 118.08, "and the end users we support."),
    (119.04, 128.26, "On the end-user side, I've come to understand that you have to do training and retraining."),
    (129.44, 140.46, "That has helped us to recently design our training programme to be more frequent"),
    (140.46, 144.32, "with our trainings."),
    (151.92, 154.60, "Somebody who wants to come into my field in the future,"),
    (154.60, 159.60, "it's a lot of fun, and it's also very demanding"),
    (159.60, 164.96, "because you have to be on your toes every time."),
    (165.54, 169.80, "The tech industry is highly dynamic,"),
    (169.80, 173.38, "and the technology you know today is out of date tomorrow."),
    (174.02, 178.14, "So you have to really be on your toes. You have to be up to date."),
    (178.44, 182.94, "You have to be willing to be involved in a lot of data and information in a short time."),
    (182.94, 187.18, "You have to be able to analyse on your foot and be able to, you know,"),
    (187.32, 189.14, "implement as you go."),
    (189.54, 193.08, "It's highly demanding, but it's also fun."),
]


def create_caption_png(index, caption_text):
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Bottom-centre caption panel, below the recurring lower-third.
    panel = (100, 1725, 980, 1865)
    draw.rounded_rectangle(
        panel,
        radius=22,
        fill=NAVY,
        outline=(245, 166, 63, 155),
        width=2,
    )
    draw.rounded_rectangle(
        (100, 1750, 109, 1840),
        radius=4,
        fill=GOLD,
    )

    caption_font = load_font(FONT_REGULAR, 37)
    lines = wrap_text(draw, caption_text, caption_font, 790)

    if len(lines) > 2:
        caption_font = load_font(FONT_REGULAR, 33)
        lines = wrap_text(draw, caption_text, caption_font, 790)

    if len(lines) > 2:
        raise ValueError(
            f"Caption {index} is too long for two lines: {caption_text}"
        )

    line_heights = [
        draw.textbbox((0, 0), line, font=caption_font)[3]
        - draw.textbbox((0, 0), line, font=caption_font)[1]
        for line in lines
    ]
    line_gap = 8
    total_height = sum(line_heights) + line_gap * (len(lines) - 1)
    y = 1795 - total_height / 2

    for line, line_height in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=caption_font)
        text_width = bbox[2] - bbox[0]
        x = (W - text_width) / 2 + 4
        draw.text((x, y), line, font=caption_font, fill=WHITE)
        y += line_height + line_gap

    path = GRAPHICS / f"subtitle_{index:02d}.png"
    image.save(path)
    return path


caption_paths = [
    create_caption_png(index, caption_text)
    for index, (_, _, caption_text) in enumerate(captions, start=1)
]

questions = [
    (1, "Could you introduce yourself and tell us about your role at B.G. Technical Limited?"),
    (2, "What are the key responsibilities of the ICT department?"),
    (3, "What are the major challenges your department faces?"),
    (4, "What advice would you give someone looking to build a career in ICT?"),
]


def create_question_card(number, question):
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (90, 720, 990, 1200),
        radius=28,
        fill=NAVY,
        outline=(245, 166, 63, 210),
        width=3,
    )
    draw.rounded_rectangle(
        (90, 780, 100, 1140),
        radius=5,
        fill=GOLD,
    )

    heading_font = load_font(FONT_BOLD, 31)
    question_font = load_font(FONT_BOLD, 43)

    draw.text(
        (145, 785),
        f"INTERVIEW QUESTION {number:02d}",
        font=heading_font,
        fill=GOLD,
    )

    lines = wrap_text(draw, question, question_font, 770)
    y = 875

    for line in lines:
        draw.text((145, y), line, font=question_font, fill=WHITE)
        y += 64

    image.save(GRAPHICS / f"question_{number}.png")


for number, question in questions:
    create_question_card(number, question)


# Full-name lower-third.
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
    font=load_font(FONT_BOLD, 43),
    fill=WHITE,
)
draw.text(
    (112, 1625),
    "ICT MANAGER",
    font=load_font(FONT_REGULAR, 29),
    fill=GOLD,
)

lower_path = GRAPHICS / "lower_third.png"
lower.save(lower_path)


question_intervals = [
    (0.78, 5.18),
    (12.60, 17.02),
    (99.16, 102.44),
    (147.32, 150.86),
]

audio_mute_intervals = [
    (0.78, 6.20),
    (12.60, 18.44),
    (99.16, 103.92),
    (145.88, 151.92),
]

lower_intervals = [
    (22, 32),
    (45, 55),
    (75, 85),
    (112, 122),
    (160, 170),
    (180, 190),
]


def interval_expression(intervals):
    return "+".join(
        f"between(t,{start},{end})"
        for start, end in intervals
    )


question_expr = interval_expression(question_intervals)
audio_mute_expr = interval_expression(audio_mute_intervals)
lower_expr = interval_expression(lower_intervals)


# Detect the actual source duration.
probe = subprocess.run(
    [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(SOURCE),
    ],
    capture_output=True,
    text=True,
    check=True,
)

duration = float(probe.stdout.strip())


# FFmpeg inputs:
# 0 = interview video
# 1 = looping background music
# 2 = BGT logo
# 3 = lower-third
# 4-7 = question cards
# 8 onward = subtitle cards

cmd = [
    shutil.which("ffmpeg") or "ffmpeg", "-y",
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

for caption_path in caption_paths:
    cmd += [
        "-loop", "1",
        "-framerate", "30",
        "-i", str(caption_path),
    ]


filters = []

filters.append(
    "[0:v]scale=608:1080:flags=lanczos,setsar=1,"
    "scale=1080:1920:flags=lanczos,setsar=1,"
    "split=2[vsharp][vblur]"
)

filters.append(
    f"[vblur]boxblur=18:10:enable='{question_expr}',"
    f"eq=brightness=-0.12:saturation=0.85:enable='{question_expr}'[vblurred]"
)

filters.append(
    f"[vsharp][vblurred]overlay=0:0:enable='{question_expr}'[vbg]"
)

filters.append("[2:v]scale=220:-1,format=rgba[logo]")
filters.append("[vbg][logo]overlay=W-w-55:55[vlogo]")

filters.append("[3:v]format=rgba[lower]")
filters.append(
    f"[vlogo][lower]overlay=0:0:enable='{lower_expr}'[vlower]"
)

current = "vlower"

# Question cards.
for index, (start, end) in enumerate(question_intervals):
    input_index = 4 + index
    next_label = f"vquestion{index + 1}"

    filters.append(f"[{input_index}:v]format=rgba[q{index + 1}]")
    filters.append(
        f"[{current}][q{index + 1}]overlay=0:0:"
        f"enable='between(t,{start},{end})'[{next_label}]"
    )

    current = next_label


# Subtitles are layered last to keep them crisp.
caption_input_start = 4 + len(questions)

for index, (start, end, _) in enumerate(captions):
    input_index = caption_input_start + index
    next_label = f"vsubtitle{index + 1}"

    filters.append(f"[{input_index}:v]format=rgba[sub{index + 1}]")
    filters.append(
        f"[{current}][sub{index + 1}]overlay=0:0:"
        f"enable='between(t,{start},{end})'[{next_label}]"
    )

    current = next_label


filters.append(f"[{current}]null[vout]")

filters.append(
    f"[0:a]volume=2.0,volume=0:enable='{audio_mute_expr}'[voice]"
)

fade_start = max(0, duration - 2.0)

filters.append(
    f"[1:a]volume='if({question_expr},0.14,0.0385)',"
    f"afade=t=out:st={fade_start:.3f}:d=2[music]"
)

filters.append(
    "[voice][music]amix=inputs=2:duration=first:"
    "dropout_transition=2:normalize=0,alimiter=limit=0.95[aout]"
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
    "-t", f"{duration:.3f}",
    "-shortest",
    str(OUT),
]


print("\nSPIRIT EDITOR AI - ICT MANAGER VERSION 5")
print("=" * 58)
print(f"Source duration: {duration:.2f} seconds")
print("Subtitles: bottom-centre, maximum two lines")
print("Subtitle design: semi-transparent navy, white text, gold accent")
print("Question cards: 4, unchanged from V1")
print("Interviewer audio: muted during question intervals")
print("BGT logo: enlarged")
print("Lower-third: full name and role, recurring")
print("\nRendering may take several minutes. Please wait.\n")


log_path = OUT.parent / "v5_ffmpeg_error.log"

print(f"FFmpeg diagnostic log: {log_path}")
print(f"FFmpeg executable: {cmd[0]}")
print(f"FFmpeg arguments: {len(cmd)}")

with log_path.open("w", encoding="utf-8", errors="replace") as log_file:
    result = subprocess.run(cmd, stderr=log_file)

if result.returncode != 0:
    print("\\nFFmpeg failed. Last 60 diagnostic lines:")
    log_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    print("\\n".join(log_lines[-60:]))
    raise RuntimeError(
        f"FFmpeg rendering failed (exit code {result.returncode}). "
        f"See diagnostic log: {log_path}"
    )


final_probe = subprocess.run(
    [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size:stream=width,height",
        "-of", "default=noprint_wrappers=1",
        str(OUT),
    ],
    capture_output=True,
    text=True,
    check=True,
)

print("\nICT MANAGER VERSION 5 RENDERED SUCCESSFULLY")
print(final_probe.stdout)
print(f"OUTPUT: {OUT}")





