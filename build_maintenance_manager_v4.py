from pathlib import Path

base = Path(__file__).resolve().parent
source = base / "render_maintenance_manager_v3.py"
target = base / "render_maintenance_manager_v4.py"

script = source.read_text(encoding="utf-8")

replacements = {
    'main_maintenance_manager_full_interview_v3.mp4':
        'main_maintenance_manager_full_interview_v4.mp4',
    'maintenance_manager_v3_ffmpeg_error.log':
        'maintenance_manager_v4_ffmpeg_error.log',
    'MAINTENANCE MANAGER VERSION 3':
        'MAINTENANCE MANAGER VERSION 4',
    'MAINTENANCE MANAGER V3':
        'MAINTENANCE MANAGER V4',
}

for old, new in replacements.items():
    script = script.replace(old, new)

# Match the lower-third's white, navy and gold colour palette.
style_line = (
    "Style: Default,Arial,37,"
    "&H00FFFFFF,&H00FFFFFF,"
    "&H003FA6F5,&H232D1405,"
    "0,0,0,0,100,100,0,0,3,2,0,2,100,100,55,1"
)

lines = script.splitlines()
style_found = False

for i, line in enumerate(lines):
    if line.startswith("Style: Default,Arial,37,"):
        lines[i] = style_line
        style_found = True
        break

if not style_found:
    raise RuntimeError("Could not locate the V3 subtitle style.")

script = "\n".join(lines) + "\n"

output = base / "exports" / "maintenance_manager" / "main_maintenance_manager_full_interview_v4.mp4"

if output.exists():
    raise SystemExit(f"V4 already exists. Preserving it: {output}")

target.write_text(script, encoding="utf-8")

print("V4 script created.")
print("Subtitle text: white")
print("Subtitle background: deep navy")
print("Subtitle accent: BGT gold")
print(f"Output: {output}")
