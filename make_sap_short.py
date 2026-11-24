"""Build a short-form cut from the SAP specialist interview (<2 min).

Source: C:\\Users\\greatman.u\\Downloads\\SHORTS INTERVIEW\\sap_specialist_full_interview.mp4
Source already carries the house captions/logo, so the short keeps that look and adds:
  * a hook card over the first seconds,
  * a hard-cut montage of the strongest answers,
  * a hold-and-CTA end card ("full interview on YouTube").
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
SRC_DIR = Path(r"C:\Users\greatman.u\Downloads\SHORTS INTERVIEW")
WORK = Path(r"C:\Users\greatman.u\Projects\SPIRIT_EDITOR_AI\analysis\sap_short")
GRAPHICS = WORK / "graphics"
OUT_DIR = SRC_DIR

W, H = 1080, 1920
NAVY = (8, 22, 48, 235)
NAVY_SOFT = (8, 22, 48, 205)
GOLD = (245, 166, 63, 255)
WHITE = (255, 255, 255, 255)
GREY = (205, 214, 228, 255)
FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")
FONT_REG = Path("C:/Windows/Fonts/arial.ttf")

# --- editorial timeline (source timestamps, seconds) ---------------------------
SEGMENTS = [
    # Q: what is SAP / the global system ("you can't walk for any angle of the world")
    (169.00, 198.00),
    # Q: recent achievement - batch 8 -> batch 10 upgrade
    (442.00, 472.00),
    # Q: user growth / global operations across departments
    (505.00, 535.00),
]
HOOK_TEXT = "ONE GLOBAL SYSTEM"
HOOK_SUB = "Mrs. Interviewee Eight  |  SAP Specialist, B.G. Technical"
END_TEXT = "WATCH THE FULL INTERVIEW"
END_BIG = "ON YOUTUBE"
END_SUB = "12 minutes  |  Mrs. Interviewee Eight on SAP operations"
END_HOLD = 4.0


def font(path: Path, size: int):
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for word in text.split():
        cand = f"{cur} {word}".strip()
        if draw.textbbox((0, 0), cand, font=fnt)[2] <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def rounded_panel(draw, box, radius, fill):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def fit_font(draw, text, path, start, min_size, max_w):
    """Largest font size whose wrapped lines all fit inside max_w."""
    for size in range(start, min_size - 2, -2):
        fnt = font(path, size)
        lines = wrap(draw, text, fnt, max_w)
        if all(draw.textbbox((0, 0), ln, font=fnt)[2] <= max_w for ln in lines):
            return fnt, lines
    return font(path, min_size), wrap(draw, text, font(path, min_size), max_w)


def make_card(path: Path, kind: str):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if kind == "hook":
        pad_x, top = 88, 845
        inner_w = W - 2 * pad_x - 88
        eye_f = font(FONT_BOLD, 40)
        title_f, lines = fit_font(d, HOOK_TEXT, FONT_BOLD, 82, 58, inner_w)
        sub_f, subs = fit_font(d, HOOK_SUB, FONT_REG, 36, 26, inner_w)
        line_h = int(title_f.size * 1.2)
        block_h = 44 + 52 + len(lines) * line_h + 14 + len(subs) * int(sub_f.size * 1.35) + 44
        box = (pad_x, top, W - pad_x, top + block_h)
        rounded_panel(d, box, 26, NAVY)
        d.rectangle([box[0], box[1], box[0] + 12, box[3]], fill=GOLD)
        y = box[1] + 40
        d.text((box[0] + 44, y), "SHORT VERSION", font=eye_f, fill=GOLD)
        y += 52
        for ln in lines:
            d.text((box[0] + 44, y), ln, font=title_f, fill=WHITE)
            y += line_h
        y += 14
        for ln in subs:
            d.text((box[0] + 44, y), ln, font=sub_f, fill=GREY)
            y += int(sub_f.size * 1.35)
    else:
        pad_x, top = 88, 865
        inner_w = W - 2 * pad_x - 88
        title_f = font(FONT_BOLD, 54)
        big_f, big_lines = fit_font(d, END_BIG, FONT_BOLD, 96, 64, inner_w)
        sub_f, subs = fit_font(d, END_SUB, FONT_REG, 34, 26, inner_w)
        big_h = int(big_f.size * 1.25)
        block_h = 44 + 66 + len(big_lines) * big_h + 12 + len(subs) * int(sub_f.size * 1.35) + 40
        box = (pad_x, top, W - pad_x, top + block_h)
        rounded_panel(d, box, 26, NAVY)
        d.rectangle([box[0], box[1], box[0] + 12, box[3]], fill=GOLD)
        y = box[1] + 40
        d.text((box[0] + 44, y), END_TEXT, font=title_f, fill=GOLD)
        y += 66
        for ln in big_lines:
            d.text((box[0] + 44, y), ln, font=big_f, fill=WHITE)
            y += big_h
        y += 12
        for ln in subs:
            d.text((box[0] + 44, y), ln, font=sub_f, fill=GREY)
            y += int(sub_f.size * 1.35)

    img.save(str(path))


def ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        sys.exit("ffmpeg not found")
    return str(Path(exe).resolve())


def run(cmd):
    print("> running ffmpeg ...", flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="sap_specialist_full_interview.mp4")
    ap.add_argument("--out", default="sap_specialist_short.mp4")
    ap.add_argument("--lufs", type=float, default=-15.0)
    ap.add_argument("--reuse", action="store_true", help="keep existing seg/body cuts")
    args = ap.parse_args()

    GRAPHICS.mkdir(parents=True, exist_ok=True)
    src = SRC_DIR / args.src
    out = OUT_DIR / args.out
    hook_png = GRAPHICS / "hook_card.png"
    end_png = GRAPHICS / "end_card.png"
    make_card(hook_png, "hook")
    make_card(end_png, "end")

    # 1) cut the three segments and concatenate
    parts, labels = [], []
    for i, (a, b) in enumerate(SEGMENTS):
        v = GRAPHICS / f"seg{i+1}.mp4"
        if not (args.reuse and v.exists()):
            run([ffmpeg(), "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", str(src), "-t", f"{(b - a):.3f}",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(v)])
        parts.append(v)
        labels.append(f"[seg{i+1}]")

    # 2) assemble body with concat demuxer, then overlay cards + pad end hold
    list_file = GRAPHICS / "concat.txt"
    list_file.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts), encoding="utf-8")
    body = GRAPHICS / "body.mp4"
    if not (args.reuse and body.exists()):
        run([ffmpeg(), "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
             "-c", "copy", str(body)])

    dur_cmd = [ffmpeg().replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries",
               "format=duration", "-of", "default=nw=1:nk=1", str(body)]
    body_dur = float(subprocess.run(dur_cmd, capture_output=True, text=True, check=True).stdout.strip())
    print(f"body duration {body_dur:.2f}s", flush=True)
    end_start = max(0.0, body_dur - 0.2)

    vf = (
        f"[0:v]tpad=stop_mode=clone:stop={END_HOLD}[vb];"
        f"[vb][1:v]overlay=0:0:enable='between(t,0,4)'[vh];"
        f"[vh][2:v]overlay=0:0:enable='gte(t,{end_start:.3f})'[v]"
    )
    af = (
        f"[0:a]apad=pad_dur={END_HOLD},"
        f"afade=t=out:st={max(0.0, body_dur - 2.0):.3f}:d=2,"
        f"loudnorm=I={args.lufs}:TP=-1.5:LRA=8:print_format=summary,"
        f"alimiter=limit=0.85:attack=4:release=60[a]"
    )
    filter_complex = f"{vf};{af}"

    cmd = [ffmpeg(), "-v", "error", "-y", "-i", str(body),
           "-loop", "1", "-t", f"{body_dur + END_HOLD:.3f}", "-i", str(hook_png),
           "-loop", "1", "-t", f"{body_dur + END_HOLD:.3f}", "-i", str(end_png),
           "-filter_complex", filter_complex,
           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart"]
    run(cmd + [str(out)])
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
