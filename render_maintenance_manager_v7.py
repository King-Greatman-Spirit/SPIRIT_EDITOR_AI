"""Render the Maintenance Manager interview (V7) for B.G. Technical Limited.

Changes from V6:

  * Mr. Interviewee One's voice is the original recording throughout, with the
    room tone removed and the level brought up. The interviewer's
    speech is removed by closing the question windows, which is where
    she holds the floor, and her actual questions are shown as
    on-screen cards recovered from the recording rather than
    paraphrased.
  * Subtitles follow Mr. Interviewee One's speech only, with corrected wording and
    word-level timing.
  * The approved navy-and-gold subtitle design and the existing portrait
    presentation, branding and transitions are preserved.
"""

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "media" / "originals" / "Mtce Mgr - Mr Interviewee One.mp4"
LOGO = BASE / "assets" / "branding" / "bgt_logo.png"
MUSIC = BASE / "assets" / "branding" / "background_music.mp3"
VOICE = (BASE / "analysis" / "maintenance_manager" / "v7_analysis" / "voice" /
         "atoma_voice_voiced.wav")

# The music gains were measured against the voice track that is used
# here, so the bed sits at 30% of his amplitude during the answers.
# They are written by build_voiced.py so the renderer and the
# measurements can never disagree.
MIX_SETTINGS = (BASE / "analysis" / "maintenance_manager" / "v7_analysis" /
                "voice" / "mix_settings.json")
_mix = json.loads(MIX_SETTINGS.read_text("utf-8"))
MUSIC_GAIN_ANSWER = f"{_mix['music_gain_answers']:.6f}"
MUSIC_GAIN_CARD = f"{_mix['music_gain_cards']:.6f}"
MIX_MEASURED_I = _mix["mix_measured_i"]
MIX_MEASURED_TP = _mix["mix_measured_tp"]
MIX_MEASURED_LRA = _mix["mix_measured_lra"]
MIX_MEASURED_THRESH = _mix["mix_measured_thresh"]
MIX_TARGET_I = _mix["mix_target_i"]
MIX_TARGET_TP = _mix["mix_target_tp"]
MIX_TARGET_LRA = _mix["mix_target_lra"]

OUT = BASE / "exports" / "maintenance_manager" / "main_maintenance_manager_full_interview_v7.mp4"
GRAPHICS = BASE / "analysis" / "maintenance_manager" / "v7_graphics"

CAPTIONS_JSON = BASE / "analysis" / "maintenance_manager" / "maintenance_manager_v7_captions.json"
QUESTIONS_JSON = BASE / "analysis" / "maintenance_manager" / "maintenance_manager_v7_questions.json"

for path in (SOURCE, LOGO, MUSIC, VOICE, CAPTIONS_JSON, QUESTIONS_JSON):
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")

if OUT.exists():
    raise FileExistsError(
        f"Output already exists: {OUT}\n"
        "Move or rename it before running this script again."
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


captions = json.loads(CAPTIONS_JSON.read_text(encoding="utf-8"))
questions = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))

print(f"captions: {len(captions)}   questions: {len(questions)}")

# ---------------------------------------------------------------------
# Question cards. The card is sized to its content so short questions
# do not leave a large empty panel.
# ---------------------------------------------------------------------
def create_question_card(number, question):
    """Render the question card and return its path and overlay position.

    The card is cropped to its own bounding box so the overlay filter
    only has to handle a small image. That keeps the render inside a
    modest memory budget.
    """
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    heading_font = load_font(FONT_BOLD, 31)
    question_font = load_font(FONT_BOLD, 43)

    lines = wrap_text(draw, question, question_font, 770)
    if len(lines) > 5:
        question_font = load_font(FONT_BOLD, 37)
        lines = wrap_text(draw, question, question_font, 770)
    if len(lines) > 6:
        raise ValueError(
            f"Question {number} is too long for the card: {question!r}"
        )

    line_h = 64 if len(lines) <= 4 else 58
    head_y = 785
    text_y = head_y + 90
    box_bottom = text_y + line_h * len(lines) + 45

    draw.rounded_rectangle(
        (90, 720, 990, box_bottom),
        radius=28,
        fill=NAVY,
        outline=(245, 166, 63, 210),
        width=3,
    )
    draw.rounded_rectangle(
        (90, 780, 100, box_bottom - 60),
        radius=5,
        fill=GOLD,
    )
    draw.text((145, head_y), f"INTERVIEW QUESTION {number:02d}",
              font=heading_font, fill=GOLD)

    y = text_y
    for line in lines:
        draw.text((145, y), line, font=question_font, fill=WHITE)
        y += line_h

    # Crop to the card so the overlay stays small.
    crop_box = (80, 710, 1000, box_bottom + 10)
    cropped = image.crop(crop_box)
    path = GRAPHICS / f"question_{number}.png"
    cropped.save(path)
    return path, crop_box[0], crop_box[1]


card_inputs = []
for q in questions:
    path, x, y = create_question_card(q["number"], q["text"])
    card_inputs.append((path, x, y))

# ---------------------------------------------------------------------
# Lower third with the full name and role.
#
# It is placed above the subtitle panel so the two never overlap.
# ---------------------------------------------------------------------
LOWER_TOP = 1445
LOWER_BOTTOM = 1630

lower = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(lower)

draw.rounded_rectangle(
    (65, LOWER_TOP, 790, LOWER_BOTTOM), radius=22, fill=(5, 20, 45, 220))
draw.rounded_rectangle(
    (65, LOWER_TOP, 77, LOWER_BOTTOM), radius=5, fill=GOLD)
draw.text((112, LOWER_TOP + 28), "MR. INTERVIEWEE ONE",
          font=load_font(FONT_BOLD, 43), fill=WHITE)
draw.text((112, LOWER_TOP + 93), "MAINTENANCE MANAGER",
          font=load_font(FONT_REGULAR, 29), fill=GOLD)

# Crop to the panel so the overlay stays small.
lower_crop = (55, LOWER_TOP - 10, 800, LOWER_BOTTOM + 10)
lower_path = GRAPHICS / "lower_third.png"
lower.crop(lower_crop).save(lower_path)

# ---------------------------------------------------------------------
# Timing.
#
# question_intervals  - when the question card is on screen
# lower_intervals     - when the name lower third is on screen
# ---------------------------------------------------------------------
question_intervals = [
    (q["ask_start"] - 0.10, q["ask_end"] + 0.55) for q in questions
]

# The lower third is shown for the answers, not over the question cards.
# It starts after the opening greeting so it never sits under a caption.
lower_intervals = []
prev_end = 3.10
for q in questions:
    start = prev_end
    end = q["ask_start"] - 0.20
    if end - start > 1.0:
        lower_intervals.append((start, end))
    prev_end = q["ask_end"] + 0.35
lower_intervals.append((prev_end, 329.00))


def interval_expression(intervals):
    return "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in intervals)


question_expr = interval_expression(question_intervals)
lower_expr = interval_expression(lower_intervals)

# ---------------------------------------------------------------------
# Subtitles: one ASS track, approved navy panel with a gold accent.
# ---------------------------------------------------------------------
def ass_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


ass_header = """[Script Info]
Title: Maintenance Manager V7
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,38,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Panel dimensions and placement are matched to the approved design.
panel_path = (
    "m 26 0 l 844 0 "
    "b 858 0 870 12 870 26 "
    "l 870 154 "
    "b 870 168 858 180 844 180 "
    "l 26 180 "
    "b 12 180 0 168 0 154 "
    "l 0 26 "
    "b 0 12 12 0 26 0 c"
)
gold_path = "m 0 0 l 12 0 12 180 0 180 c"

events = []
for start_time, end_time, caption in captions:
    lines = textwrap.wrap(
        caption, width=43, break_long_words=False, break_on_hyphens=False
    )
    if len(lines) > 2:
        raise ValueError(
            f"Caption needs more than two lines: {caption!r} -> {lines}"
        )
    subtitle_text = r"\N".join(lines)
    start_stamp = ass_time(start_time)
    end_stamp = ass_time(end_time)

    # Layer 0: deep navy rounded panel.
    events.append(
        f"Dialogue: 0,{start_stamp},{end_stamp},Default,,0,0,0,,"
        f"{{\\an7\\pos(105,1675)\\bord0\\shad0"
        f"\\1c&H2D1405&\\1a&H17&\\p1}}"
        f"{panel_path}{{\\p0}}"
    )
    # Layer 1: BGT gold accent strip.
    events.append(
        f"Dialogue: 1,{start_stamp},{end_stamp},Default,,0,0,0,,"
        f"{{\\an7\\pos(105,1675)\\bord0\\shad0"
        f"\\1c&H3FA6F5&\\1a&H00&\\p1}}"
        f"{gold_path}{{\\p0}}"
    )
    # Layer 2: white, centred subtitle text.
    events.append(
        f"Dialogue: 2,{start_stamp},{end_stamp},Default,,0,0,0,,"
        f"{{\\an5\\pos(540,1765)\\fnArial\\fs38"
        f"\\b0\\bord0\\shad0\\1c&HFFFFFF&}}"
        f"{subtitle_text}"
    )

ass_path = GRAPHICS / "maintenance_manager_v7_subtitles.ass"
ass_path.write_text(ass_header + "\n".join(events) + "\n", encoding="utf-8-sig")

# ---------------------------------------------------------------------
# FFmpeg.
#   0 interview (video), 1 background music, 2 logo, 3 lower third,
#   4+ question cards, then the isolated voice track.
# ---------------------------------------------------------------------
probe = subprocess.run(
    [
        str(Path(shutil.which("ffprobe")).resolve()), "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(SOURCE),
    ],
    capture_output=True, text=True, check=True,
)
duration = float(probe.stdout.strip())

cmd = [
    str(Path(shutil.which("ffmpeg")).resolve()), "-y",
    "-i", str(SOURCE),
    "-stream_loop", "-1", "-i", str(MUSIC),
    "-loop", "1", "-framerate", "30", "-i", str(LOGO),
    "-loop", "1", "-framerate", "30", "-i", str(lower_path),
]
for path, _x, _y in card_inputs:
    cmd += ["-loop", "1", "-framerate", "30", "-i", str(path)]
cmd += ["-i", str(VOICE)]

filters = []

# The source is anamorphic: convert its complete displayed frame to
# square pixels first. This preserves the full image and does not crop.
filters.append(
    "[0:v]scale=608:1080:flags=lanczos,setsar=1,"
    "scale=1080:1920:flags=lanczos,setsar=1,"
    "split=2[vsharp][vblur]"
)
filters.append(
    f"[vblur]boxblur=18:10:enable='{question_expr}',"
    f"eq=brightness=-0.12:saturation=0.85:enable='{question_expr}'[vblurred]"
)
filters.append(f"[vsharp][vblurred]overlay=0:0:enable='{question_expr}'[vbg]")

filters.append("[2:v]scale=220:-1,format=rgba[logo]")
filters.append("[vbg][logo]overlay=W-w-55:55[vlogo]")
filters.append("[3:v]format=rgba[lower]")
filters.append(
    f"[vlogo][lower]overlay={lower_crop[0]}:{lower_crop[1]}:"
    f"enable='{lower_expr}'[vlower]"
)

current = "vlower"
voice_input = 4 + len(questions)
for index, (qstart, qend) in enumerate(question_intervals):
    input_index = 4 + index
    next_label = f"vquestion{index + 1}"
    _path, cx, cy = card_inputs[index]
    filters.append(f"[{input_index}:v]format=rgba[q{index + 1}]")
    filters.append(
        f"[{current}][q{index + 1}]overlay={cx}:{cy}:"
        f"enable='between(t,{qstart:.3f},{qend:.3f})'[{next_label}]"
    )
    current = next_label

ass_filter_path = (
    ass_path.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")
)
filters.append(f"[{current}]ass=filename='{ass_filter_path}'[vout]")

# The voice track: Mr. Interviewee One only, the interviewer removed, the
# background cleaned, and the level brought up.
#
# The track was prepared by analysis/maintenance_manager/v7_analysis/
# build_voiced.py, which:
#
#   removed the room tone with a spectral subtraction whose noise
#   floor is found by minimum statistics, running at full strength
#   outside the caption windows and gently inside them, with a guard
#   band around every caption so no word can be touched,
#
#   silenced the question windows and the greeting, which is where
#   the interviewer holds the floor, and
#
#   brought him up with EBU R128 normalisation in linear mode, which
#   applies a single static gain with true-peak limiting rather than
#   pumping the level. It was measured to reach -15 LUFS with a true
#   peak of -1.5 dBFS and a crest factor of 18.6 dB, so his natural
#   movement survives and the encode cannot clip.
filters.append(
    f"[{voice_input}:a]aformat=sample_fmts=fltp:sample_rates=48000:"
    f"channel_layouts=stereo[voice]"
)

# The music bed is placed at 30% of his amplitude during the answers,
# as requested, and 3 dB below that during a question card where there
# is no speech at all.
#
# The expression must be evaluated per frame: the volume filter defaults
# to evaluating once, which would apply a single gain to the whole file
# and silently drop the question card lift.
filters.append(
    f"[1:a]volume='if({question_expr},{MUSIC_GAIN_CARD},"
    f"{MUSIC_GAIN_ANSWER})':eval=frame,"
    f"afade=t=out:st={max(0, duration - 2.0):.3f}:d=2[music]"
)

# The finished mix is normalised in one step, in linear mode, which
# applies a single static gain with true-peak limiting. Normalising
# the voice first and limiting the mix afterwards was measured to take
# 4.5 dB out of everything and flatten his dynamics.
#
# The measured values come from a trial mix built with exactly this
# filter graph, so the normalisation is exact.
filters.append(
    "[voice][music]amix=inputs=2:duration=first:dropout_transition=2:"
    "normalize=0,"
    f"loudnorm=I={MIX_TARGET_I}:TP={MIX_TARGET_TP}:LRA={MIX_TARGET_LRA}:"
    f"measured_I={MIX_MEASURED_I}:measured_TP={MIX_MEASURED_TP}:"
    f"measured_LRA={MIX_MEASURED_LRA}:"
    f"measured_thresh={MIX_MEASURED_THRESH}:linear=true[aout]"
)

cmd += [
    "-filter_complex_threads", "1",
    "-filter_threads", "1",
    "-filter_complex", ";".join(filters),
    "-map", "[vout]",
    "-map", "[aout]",
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    "-r", "30",
    "-c:a", "aac",
    "-b:a", "192k",
    # The loudness filter runs at 192 kHz internally, so the output is
    # brought back to the standard 48 kHz for the deliverable.
    "-ar", "48000",
    "-movflags", "+faststart",
    "-t", f"{duration:.3f}",
    "-shortest",
    str(OUT),
]

print("\nSPIRIT EDITOR AI - MAINTENANCE MANAGER VERSION 7")
print("=" * 58)
print(f"Source duration: {duration:.2f} seconds")
print(f"Subtitles: {len(captions)} captions, bottom-centre, maximum two lines")
print("Subtitle design: semi-transparent navy, white text, gold accent")
print(f"Question cards: {len(questions)}")
print("Interviewer voice: removed by closing her question windows")
print("Mr. Interviewee One's voice: original recording, background cleaned")
print(f"Voice level: {_mix['final_lufs']:.1f} LUFS mix, "
      f"peak {_mix['final_true_peak']:.1f} dBFS")
print(f"Music bed: {_mix['bed_under_answer_db']:.0f} dB below his voice")
print("BGT logo: enlarged")
print("Lower-third: full name and role, recurring")
print("\nRendering may take several minutes. Please wait.\n")

log_path = OUT.parent / "maintenance_manager_v7_ffmpeg_error.log"
print(f"FFmpeg diagnostic log: {log_path}")

with log_path.open("w", encoding="utf-8", errors="replace") as log_file:
    result = subprocess.run(cmd, stderr=log_file)

if result.returncode != 0:
    print("\nFFmpeg failed. Last 60 diagnostic lines:")
    log_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    print("\n".join(log_lines[-60:]))
    raise RuntimeError(
        f"FFmpeg rendering failed (exit code {result.returncode}). "
        f"See diagnostic log: {log_path}"
    )

final_probe = subprocess.run(
    [
        str(Path(shutil.which("ffprobe")).resolve()), "-v", "error",
        "-show_entries", "format=duration,size:stream=width,height,codec_name",
        "-of", "default=noprint_wrappers=1",
        str(OUT),
    ],
    capture_output=True, text=True, check=True,
)

print("\nMAINTENANCE MANAGER VERSION 7 RENDERED SUCCESSFULLY")
print(final_probe.stdout)
print(f"OUTPUT: {OUT}")
