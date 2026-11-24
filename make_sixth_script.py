from pathlib import Path

base = Path(__file__).resolve().parent
src = (base / "render_intern_fourth_v1.py").read_text(encoding="utf-8")

replacements = {
    '"""Render intern FOURTH v1 (Mr Interviewee Six, Construction Department).':
        '"""Render intern SIXTH v1 (Mr Interviewee Nine, Maintenance Department).',
    'Uses the gentle audio chain from THIRD v2 (no aggressive gate) so his\nquiet syllables are preserved. Interviewer muted, captions word-accurate.':
        'Uses the gentle audio chain from THIRD v2 (no aggressive gate) so his\nquiet syllables are preserved. Interviewer muted, captions word-accurate.',
    'CAPTIONS_JSON = BASE / "transcripts" / "interns" / "fourth" / "fourth_captions.json"':
        'CAPTIONS_JSON = BASE / "transcripts" / "interns" / "sixth" / "sixth_captions.json"',
    'GRAPHICS = BASE / "analysis" / "interns" / "fourth_graphics"':
        'GRAPHICS = BASE / "analysis" / "interns" / "sixth_graphics"',
    'OUT_FINAL = OUT_DIR / "main_intern_fourth_joshua_umoh_v1.mp4"':
        'OUT_FINAL = OUT_DIR / "main_intern_sixth_emmanuel_v1.mp4"',
    'OUT_TEST = OUT_DIR / "main_intern_fourth_joshua_umoh_v1_test.mp4"':
        'OUT_TEST = OUT_DIR / "main_intern_sixth_emmanuel_v1_test.mp4"',
    '"MR. INTERVIEWEE SIX"': '"MR. INTERVIEWEE NINE"',
    '"CONSTRUCTION DEPARTMENT"': '"MAINTENANCE DEPARTMENT"',
    '"main_intern_fourth_joshua_umoh_v1_test_ffmpeg_error.log" if args.test else "fourth_v1_ffmpeg_error.log"':
        '"main_intern_sixth_emmanuel_v1_test_ffmpeg_error.log" if args.test else "sixth_v1_ffmpeg_error.log"',
    'SPIRIT EDITOR AI - INTERN FOURTH (MR. INTERVIEWEE SIX) VERSION 1':
        'SPIRIT EDITOR AI - INTERN SIXTH (MR. INTERVIEWEE NINE) VERSION 1',
    'INTERN FOURTH (MR. INTERVIEWEE SIX) VERSION 1 RENDERED SUCCESSFULLY':
        'INTERN SIXTH (MR. INTERVIEWEE NINE) VERSION 1 RENDERED SUCCESSFULLY',
}

for old, new in replacements.items():
    if old not in src:
        print("MISSING:", old[:80])
    src = src.replace(old, new)

out = base / "render_intern_sixth_v1.py"
out.write_text(src, encoding="utf-8")
print("Wrote", out)
