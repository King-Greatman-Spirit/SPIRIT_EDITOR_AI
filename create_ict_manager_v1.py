from pathlib import Path

base = Path(__file__).resolve().parent
source = base / "render_store_manager_v5.py"
target = base / "render_ict_manager_v1.py"

if not source.exists():
    raise FileNotFoundError(source)

if target.exists():
    raise FileExistsError(f"Renderer already exists: {target}")

script = source.read_text(encoding="utf-8")

replacements = [
    (
        'SOURCE = BASE / "edits" / "store_manager" / "full_interview_source.mp4"',
        'SOURCE = BASE / "media" / "originals" / "Ict Mgr - Mr Ola.mp4"'
    ),
    (
        'OUT = BASE / "exports" / "store_manager" / "03_store_journey_manager_full_interview_v5.mp4"',
        'OUT = BASE / "exports" / "ict_manager" / "03_ict_manager_full_interview_v1.mp4"'
    ),
    (
        'GRAPHICS = BASE / "analysis" / "store_manager" / "v5_graphics"',
        'GRAPHICS = BASE / "analysis" / "ict_manager" / "v1_graphics"'
    ),
    (
        '    (1, "Could you introduce yourself and tell us about your role?"),\n'
        '    (2, "Could you outline the core responsibilities of your department and explain how it contributes to BGT\'s overall operations?"),\n'
        '    (3, "What are the key challenges your department faces, and how does your team ensure effective and reliable service delivery?"),\n'
        '    (5, "What advice would you give someone who wants to join your field?"),',
        '    (1, "Could you introduce yourself and tell us about your role at B.G. Technical Limited?"),\n'
        '    (2, "What are the key responsibilities of the ICT department?"),\n'
        '    (3, "What are the major challenges your department faces?"),\n'
        '    (4, "What advice would you give someone looking to build a career in ICT?"),'
    ),
    (
        '    "MR. EJIOGU FRANCIS",',
        '    "MR. IBIGBAMI OLAOLUWA",'
    ),
    (
        '    "STORE & JOURNEY MANAGER",',
        '    "ICT MANAGER",'
    ),
    (
        '    (4.00, 7.00),\n'
        '    (23.68, 31.48),\n'
        '    (73.88, 79.66),\n'
        '    (183.25, 190.85),',
        '    (0.78, 5.18),\n'
        '    (12.60, 17.02),\n'
        '    (99.16, 102.44),\n'
        '    (147.32, 150.86),'
    ),
    (
        '    (4.00, 7.00),\n'
        '    (23.68, 31.48),\n'
        '    (73.88, 81.26),\n'
        '    (183.25, 190.85),',
        '    (0.78, 6.20),\n'
        '    (12.60, 18.44),\n'
        '    (99.16, 103.92),\n'
        '    (145.88, 151.92),'
    ),
    (
        '    (12, 22),\n'
        '    (48, 58),\n'
        '    (105, 115),\n'
        '    (145, 155),\n'
        '    (220, 230),\n'
        '    (265, 275),',
        '    (22, 32),\n'
        '    (45, 55),\n'
        '    (75, 85),\n'
        '    (112, 122),\n'
        '    (160, 170),\n'
        '    (180, 190),'
    ),
    (
        'afade=t=out:st=289:d=2[music]',
        'afade=t=out:st=194.78:d=2[music]'
    ),
]

for old, new in replacements:
    count = script.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one match, found {count}:\n{old[:180]}"
        )
    script = script.replace(old, new, 1)

target.write_text(script, encoding="utf-8")

print("ICT Manager renderer created successfully.")
print(f"File: {target}")
print("Source: Ict Mgr - Mr Ola.mp4")
print("Interviewee: Mr. Ibigbami Olaoluwa")
print("Question cards: 4")
print("Output: exports/ict_manager/03_ict_manager_full_interview_v1.mp4")
