from pathlib import Path

base = Path(__file__).resolve().parent
source = base / "render_maintenance_manager_v3.py"
target = base / "render_maintenance_manager_v5.py"

script = source.read_text(encoding="utf-8")

# Separate V5 output, graphics and diagnostics.
replacements = {
    "main_maintenance_manager_full_interview_v3.mp4":
        "main_maintenance_manager_full_interview_v5.mp4",
    "maintenance_manager_v3_ffmpeg_error.log":
        "maintenance_manager_v5_ffmpeg_error.log",
    "v3_graphics":
        "v5_graphics",
    "maintenance_manager_v3_subtitles.ass":
        "maintenance_manager_v5_subtitles.ass",
    "VERSION 3":
        "VERSION 5",
    "VERSION 3 RENDERED SUCCESSFULLY":
        "VERSION 5 RENDERED SUCCESSFULLY",
}

for old, new in replacements.items():
    script = script.replace(old, new)

# Replace the subtitle generator with a proper navy graphic panel,
# a gold vertical accent, and centred white text.
start = script.index('ass_header = """')
end = script.index("# FFmpeg inputs:", start)

new_ass = r'''
ass_path = GRAPHICS / "maintenance_manager_v5_subtitles.ass"
GRAPHICS.mkdir(parents=True, exist_ok=True)

def ass_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

ass_header = """[Script Info]
Title: Maintenance Manager V5
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

events = []

# Panel dimensions and placement are matched to the approved preview.
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

for start_time, end_time, caption in captions:
    lines = textwrap.wrap(
        caption,
        width=43,
        break_long_words=False,
        break_on_hyphens=False
    )[:2]

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

ass_path.write_text(
    ass_header + "\n".join(events) + "\n",
    encoding="utf-8-sig"
)

'''

script = script[:start] + new_ass + script[end:]

output = base / "exports" / "maintenance_manager" / "main_maintenance_manager_full_interview_v5.mp4"

if output.exists():
    raise SystemExit(f"V5 already exists. Existing file preserved: {output}")

target.write_text(script, encoding="utf-8")

print("V5 script prepared.")
print("Subtitle panel: rounded deep navy")
print("Subtitle text: centred white")
print("Left accent: BGT gold")
print("Subtitle position: bottom centre")
print("Maximum lines: 2")
print(f"Output: {output}")
