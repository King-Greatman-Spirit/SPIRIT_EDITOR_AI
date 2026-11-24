from pathlib import Path
import re
import sys

base = Path(__file__).resolve().parent
source = base / "render_maintenance_manager_v2.py"
target = base / "render_maintenance_manager_v3.py"

script = source.read_text(encoding="utf-8")

# Preserve the original V2 script and use separate V3 assets/output.
script = script.replace(
    'OUT = BASE / "exports" / "maintenance_manager" / "main_maintenance_manager_full_interview_v2.mp4"',
    'OUT = BASE / "exports" / "maintenance_manager" / "main_maintenance_manager_full_interview_v3.mp4"'
)
script = script.replace(
    'GRAPHICS = BASE / "analysis" / "maintenance_manager" / "v2_graphics"',
    'GRAPHICS = BASE / "analysis" / "maintenance_manager" / "v3_graphics"'
)
script = script.replace(
    'maintenance_manager_v2_ffmpeg_error.log',
    'maintenance_manager_v3_ffmpeg_error.log'
)
script = script.replace(
    'SPIRIT EDITOR AI - MAINTENANCE MANAGER VERSION 2',
    'SPIRIT EDITOR AI - MAINTENANCE MANAGER VERSION 3'
)
script = script.replace(
    'MAINTENANCE MANAGER VERSION 2 RENDERED SUCCESSFULLY',
    'MAINTENANCE MANAGER VERSION 3 RENDERED SUCCESSFULLY'
)

# Replace the old 49-image subtitle overlay graph with one ASS subtitle track.
start = script.index("# FFmpeg inputs:")
end_marker = 'filter_complex = ";".join(filters)'
end = script.index(end_marker, start) + len(end_marker)

replacement = r'''
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
Style: Default,Arial,37,&H00FFFFFF,&H00FFFFFF,&H9B3FA6F5,&HE8051405,0,0,0,0,100,100,0,0,3,2,0,2,100,100,55,1

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
'''

script = script[:start] + replacement + script[end:]

# Keep the original encoding settings, while limiting filter threading.
script = script.replace(
    '    "-filter_complex", filter_complex,',
    '    "-filter_complex_threads", "2",\n'
    '    "-filter_complex", filter_complex,'
)

# Refuse to overwrite an earlier V3 export.
output = base / "exports" / "maintenance_manager" / "main_maintenance_manager_full_interview_v3.mp4"
if output.exists():
    raise SystemExit(
        f"V3 output already exists; preserving it:\n{output}\n"
        "Rename or move it before creating another V3."
    )

target.write_text(script, encoding="utf-8")
print(f"Created: {target}")
print(f"V3 graphics folder: {base / 'analysis' / 'maintenance_manager' / 'v3_graphics'}")
print(f"V3 output: {output}")
print("Subtitle method: one ASS track")
print("Framing: complete portrait frame, no crop")
