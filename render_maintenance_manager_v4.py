import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "media" / "originals" / "Mtce Mgr - Mr Interviewee One.mp4"
LOGO = BASE / "assets" / "branding" / "bgt_logo.png"
MUSIC = BASE / "assets" / "branding" / "background_music.mp3"
OUT = BASE / "exports" / "maintenance_manager" / "main_maintenance_manager_full_interview_v4.mp4"
GRAPHICS = BASE / "analysis" / "maintenance_manager" / "v3_graphics"

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
    (2.53, 5.50, "Please tell us about GFC and your work."),
    (5.53, 11.18, "My name is Interviewee One."),
    (11.18, 18.14, "I'm the Senior Maintenance Advisor with the Technical Department,"),
    (18.14, 23.90, "and I'm in charge of equipment maintenance."),
    (24.44, 29.80, "Please tell us about the equipment."),
    (30.90, 40.49, "Okay, just like I mentioned before,"),
    (40.49, 44.67, "the Maintenance Department is in charge of maintenance."),
    (44.67, 56.50, "We ensure equipment availability and reliability for projects brought into the Technical Department."),
    (56.78, 60.90, "Okay, sir. Wow, there are a lot."),
    (60.90, 68.17, "We have just mentioned a few that come to mind."),
    (68.17, 78.04, "We work in remote locations, offshore and in swamps."),
    (78.04, 87.04, "Those places are difficult to operate in,"),
    (87.04, 95.59, "and it's difficult to get quality diesel transported to such areas."),
    (95.59, 102.55, "Most times, what you get there is adulterated diesel."),
    (102.55, 112.89, "Because of the sensitivity of our equipment, such diesel does not work well."),
    (112.89, 129.89, "So that's a challenge we have to deal with whenever we work in such locations."),
    (129.89, 140.31, "There are a lot of challenges."),
    (140.31, 149.42, "We have done modifications of our units."),
    (154.42, 159.90, "You know, units don't die."),
    (159.90, 169.76, "We work for different customers. Nigeria is going towards gas,"),
    (169.76, 174.81, "and not every piece of equipment can work in gas locations,"),
    (174.81, 177.19, "because those areas are Zone 0 locations."),
    (177.19, 183.50, "For instance, you have NLNG."),
    (183.50, 191.15, "You don't just take your equipment to work at NLNG."),
    (191.15, 195.76, "The equipment has to meet the criteria"),
    (195.76, 201.49, "to be able to work in such an area."),
    (201.49, 208.29, "Those are the kind of challenges we see."),
    (208.29, 214.29, "For our equipment to work in such locations,"),
    (214.29, 219.49, "there are certain modifications we have to make."),
    (219.49, 227.18, "For instance, every piece of equipment has to have a spark arrestor."),
    (227.18, 235.30, "We use battery and electrical cables, which can cause exposure"),
    (235.30, 237.30, "in such locations."),
    (237.30, 242.85, "So most times, instead of using electrical systems,"),
    (242.85, 245.04, "we use air systems,"),
    (245.04, 249.45, "like air starters."),
    (249.45, 256.56, "Instead of a kick-starter, we use a battery to cause a spark."),
    (256.56, 260.80, "We make these modifications from time to time,"),
    (260.80, 264.00, "depending on the location we are going to."),
    (273.85, 275.65, "Why?"),
    (275.65, 281.65, "You have to be innovative, be open-minded,"),
    (281.65, 285.12, "and be ready to learn."),
    (285.12, 291.09, "In maintenance, we don't fix machines."),
    (291.09, 293.31, "I'm surprised to hear that."),
    (293.31, 296.31, "We fix the reasons in machines."),
    (296.31, 301.00, "We don't fix machines, but we fix the reasons in machines."),
    (301.00, 305.80, "Learn to communicate, plan, work,"),
    (305.80, 316.19, "and relate with operations, because it's operations"),
    (316.19, 321.70, "that use those equipment, even though we are the ones"),
    (321.70, 326.00, "who make them ready."),
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
    (1, "Could you introduce yourself and explain your role?"),
    (2, "What is the role of the Maintenance Department?"),
    (3, "What challenges affect equipment in remote and gas locations?"),
    (4, "Why is innovation important in maintenance?"),
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
    "MR. INTERVIEWEE ONE",
    font=load_font(FONT_BOLD, 43),
    fill=WHITE,
)
draw.text(
    (112, 1625),
    "MAINTENANCE MANAGER",
    font=load_font(FONT_REGULAR, 29),
    fill=GOLD,
)

lower_path = GRAPHICS / "lower_third.png"
lower.save(lower_path)


question_intervals = [
    (0.78, 5.50),
    (24.44, 29.80),
    (129.89, 140.31),
    (269.85, 275.65),
]

audio_mute_intervals = [
    (2.53, 5.50),
    (24.44, 29.80),
    (129.89, 140.31),
    (273.85, 275.65),
]

lower_intervals = [
    (5.50, 23.90),
    (30.90, 56.50),
    (68.17, 129.89),
    (140.31, 264.00),
    (275.65, 329.40),
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
        str(Path(shutil.which("ffprobe")).resolve()), "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(SOURCE),
    ],
    capture_output=True,
    text=True,
    check=True,
)

duration = float(probe.stdout.strip())



# V3: one subtitle track, full-frame portrait conversion, and fewer overlays.
import textwrap

ass_path = GRAPHICS / "maintenance_manager_v3_subtitles.ass"
GRAPHICS.mkdir(parents=True, exist_ok=True)

def ass_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

ass_header = """[Script Info]
Title: Maintenance Manager Interview V3
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,37,&H00FFFFFF,&H00FFFFFF,&H003FA6F5,&H232D1405,0,0,0,0,100,100,0,0,3,2,0,2,100,100,55,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

events = []
for start_time, end_time, caption in captions:
    lines = textwrap.wrap(
        caption,
        width=43,
        break_long_words=False,
        break_on_hyphens=False
    )
    subtitle_text = r"\N".join(lines[:2])
    events.append(
        f"Dialogue: 0,{ass_time(start_time)},{ass_time(end_time)},"
        f"Default,,0,0,0,,{subtitle_text}"
    )

ass_path.write_text(
    ass_header + "\n".join(events) + "\n",
    encoding="utf-8-sig"
)

# FFmpeg inputs:
# 0 interview, 1 background music, 2 logo, 3 lower third,
# 4-7 question cards. Subtitles are rendered from one ASS file.
cmd = [
    str(Path(shutil.which("ffmpeg")).resolve()), "-y",
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

# The source is anamorphic: convert its complete displayed frame to square
# pixels first. This preserves the full image and does not crop the sides.
filters.append(
    "[0:v]scale=608:1080:flags=lanczos,setsar=1,"
    "scale=1080:1920:flags=lanczos,setsar=1,"
    "split=2[vsharp][vblur]"
)

filters.append(
    f"[vblur]boxblur=18:10:enable='{question_expr}',"
    f"eq=brightness=-0.12:saturation=0.85:"
    f"enable='{question_expr}'[vblurred]"
)

filters.append(
    f"[vsharp][vblurred]overlay=0:0:"
    f"enable='{question_expr}'[vbg]"
)

filters.append("[2:v]scale=220:-1,format=rgba[logo]")
filters.append("[vbg][logo]overlay=W-w-55:55[vlogo]")
filters.append("[3:v]format=rgba[lower]")

filters.append(
    f"[vlogo][lower]overlay=0:0:"
    f"enable='{lower_expr}'[vlower]"
)

current = "vlower"

for index, (qstart, qend) in enumerate(question_intervals):
    input_index = 4 + index
    next_label = f"vquestion{index + 1}"

    filters.append(f"[{input_index}:v]format=rgba[q{index + 1}]")
    filters.append(
        f"[{current}][q{index + 1}]overlay=0:0:"
        f"enable='between(t,{qstart},{qend})'[{next_label}]"
    )
    current = next_label

# Escape the Windows drive colon for FFmpeg filter parsing.
ass_filter_path = (
    ass_path.resolve().as_posix()
    .replace(":", r"\:")
    .replace("'", r"\'")
)

filters.append(
    f"[{current}]ass=filename='{ass_filter_path}'[vout]"
)

filters.append(
    f"[0:a]volume=2.0,"
    f"volume=0:enable='{audio_mute_expr}'[voice]"
)

fade_start = max(0, duration - 2.0)

filters.append(
    f"[1:a]volume='if({question_expr},0.14,0.01925)',"
    f"afade=t=out:st={fade_start:.3f}:d=2[music]"
)

filters.append(
    "[voice][music]amix=inputs=2:duration=first:"
    "dropout_transition=2:normalize=0,"
    "alimiter=limit=0.95[aout]"
)

filter_complex = ";".join(filters)


cmd += [
    "-filter_complex_threads", "2",
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


print("\nSPIRIT EDITOR AI - MAINTENANCE MANAGER VERSION 4")
print("=" * 58)
print(f"Source duration: {duration:.2f} seconds")
print("Subtitles: bottom-centre, maximum two lines")
print("Subtitle design: semi-transparent navy, white text, gold accent")
print("Question cards: 4, Maintenance Manager interview")
print("Interviewer audio: muted during question intervals")
print("BGT logo: enlarged")
print("Lower-third: full name and role, recurring")
print("\nRendering may take several minutes. Please wait.\n")


log_path = OUT.parent / "maintenance_manager_v4_ffmpeg_error.log"

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
        str(Path(shutil.which("ffprobe")).resolve()), "-v", "error",
        "-show_entries", "format=duration,size:stream=width,height",
        "-of", "default=noprint_wrappers=1",
        str(OUT),
    ],
    capture_output=True,
    text=True,
    check=True,
)

print("\nMAINTENANCE MANAGER VERSION 4 RENDERED SUCCESSFULLY")
print(final_probe.stdout)
print(f"OUTPUT: {OUT}")













