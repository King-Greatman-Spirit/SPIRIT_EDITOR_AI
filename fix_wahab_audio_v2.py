"""Interviewee Seven wireline v1 - audio rebuild (v2).

What it does
------------
1. Takes the clean cut source (no music baked in) and applies the same
   interviewer-mute map the v1 render used, so nobody but Mr. Interviewee Seven is heard.
2. Voice chain: spectral denoise -> high-pass -> mud cut -> presence lift ->
   gate (everything under the speech floor drops to ~10%) -> speech normaliser
   -> EBU R128 to -14 LUFS / -1.5 dBTP so he is genuinely loud and forward.
3. Drops the music bed to 10% of what v1 used (0.022/0.056 -> 0.0022/0.0056)
   with the same question ducking and end fade.
4. Video stream is copied untouched - captions, cards, logo and timing are
   exactly as in v1.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "analysis" / "wahab_wireline" / "wahab_cut_source.mp4"
SRC_VIDEO = BASE / "exports" / "wahab_wireline" / "main_wahab_wireline_full_interview_v1.mp4"
MUSIC = BASE / "assets" / "branding" / "background_music.mp3"
OUT_DIR = BASE / "exports" / "wahab_wireline"
WORK = BASE / "analysis" / "wahab_wireline" / "audiofix"

TARGET_I = -14.0
TARGET_TP = -3.5
TARGET_LRA = 9.0

# Same interviewer map as render_wahab_wireline_v1.py (cut timeline).
MUTE = [
    (0.40, 2.56),
    (3.56, 7.56),
    (135.97, 144.99),
    (175.25, 182.05),
    (182.05, 186.30),
    (400.83, 404.83),
    (652.91, 665.96),
    (1006.83, 1015.47),
    (1239.12, 1240.19),
]
QUESTION = [
    (3.56, 7.56),
    (138.48, 144.99),
    (175.25, 182.05),
    (652.91, 665.96),
    (1008.83, 1015.47),
]

EQ = ",".join(
    [
        "highpass=f=90:poles=2",
        "afftdn=nr=14:nf=-46:tn=1",
        "equalizer=f=330:width_type=o:width=1.1:g=-2.5",
        "equalizer=f=2800:width_type=o:width=1.2:g=2.5",
        "equalizer=f=6500:width_type=h:width=2200:g=1.5",
    ]
)
VOICE = (
    "agate=threshold=0.012:ratio=4:range=0.05:attack=3:release=400:makeup=1,"
    "dynaudnorm=f=300:g=15:p=0.9:m=8:compress=2,"
    f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=summary,"
    "alimiter=limit=0.66:attack=4:release=80:level=disabled"
)


def expr(intervals: list[tuple[float, float]]) -> str:
    return "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in intervals)


def ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        sys.exit("ffmpeg not found on PATH")
    return str(Path(exe).resolve())


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        [ffmpeg().replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error",
         "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def loudness(path: Path) -> dict[str, str]:
    p = subprocess.run(
        [ffmpeg(), "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
         "-af", "ebur128=peak=true", "-f", "null", "NUL"],
        capture_output=True, text=True, errors="replace",
    )
    tail = p.stderr[p.stderr.rfind("Summary:"):] if "Summary:" in p.stderr else p.stderr
    out: dict[str, str] = {}
    for line in tail.splitlines():
        s = line.strip()
        if s.startswith("I:"):
            out["I"] = s.split()[1]
        elif s.startswith("Peak:"):
            out["TP"] = s.split()[1]
        elif s.startswith("LRA:"):
            out["LRA"] = s.split()[1]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, default=0.0)
    ap.add_argument("--bed", type=float, default=0.10, help="music level vs v1 (0.10 = 10%%)")
    ap.add_argument("--out", default="main_wahab_wireline_full_interview_v2.mp4")
    args = ap.parse_args()

    WORK.mkdir(parents=True, exist_ok=True)
    tag = "preview" if args.preview else "full"
    duration = probe_duration(SOURCE)
    end = args.preview or duration
    fade_start = max(0.0, duration - 2.0)

    mute_expr = expr(MUTE)
    q_expr = expr(QUESTION)
    music_gain = 0.022 * args.bed
    music_gain_q = 0.056 * args.bed

    # 1) voice only: clean source, interviewer muted, loud + gated
    voice_wav = WORK / f"{tag}_voice_only.wav"
    chain = f"volume=0:enable='{mute_expr}',{EQ},{VOICE}"
    cmd = [ffmpeg(), "-v", "error", "-y", "-i", str(SOURCE), "-map", "0:a:0",
           "-ac", "1", "-ar", "48000", "-af", chain]
    if args.preview:
        cmd += ["-t", f"{args.preview}"]
    subprocess.run(cmd + [str(voice_wav)], check=True)

    # 2) music bed at 10% of the v1 level, same ducking + fade
    music_wav = WORK / f"{tag}_music.wav"
    cmd = [ffmpeg(), "-v", "error", "-y", "-stream_loop", "-1", "-i", str(MUSIC)]
    if args.preview:
        cmd += ["-t", f"{args.preview}"]
    else:
        cmd += ["-t", f"{end:.3f}"]
    cmd += ["-af",
            f"volume='if({q_expr},{music_gain_q},{music_gain})',"
            f"afade=t=out:st={fade_start:.3f}:d=2",
            "-ac", "1", "-ar", "48000", str(music_wav)]
    subprocess.run(cmd, check=True)

    # 3) sum voice + bed, then final limiter
    mix_wav = WORK / f"{tag}_mix.wav"
    subprocess.run(
        [ffmpeg(), "-v", "error", "-y", "-i", str(voice_wav), "-i", str(music_wav),
         "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:normalize=0,"
                            "alimiter=limit=0.66:level=disabled[a]", "-map", "[a]",
         "-ar", "48000", "-ac", "1", str(mix_wav)],
        check=True,
    )

    print(f"Before : {loudness(WORK / f'{tag}_v1_audio.wav') if (WORK / f'{tag}_v1_audio.wav').exists() else ''}")
    print(f"Voice  : I={loudness(voice_wav)}")
    print(f"Mix    : {loudness(mix_wav)}")

    # 4) remux with untouched video
    OUT = OUT_DIR / args.out
    cmd = [ffmpeg(), "-v", "error", "-y", "-i", str(SRC_VIDEO), "-i", str(mix_wav),
           "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart"]
    if args.preview:
        cmd += ["-t", f"{args.preview}"]
    subprocess.run(cmd + [str(OUT)], check=True)
    print(f"Wrote {OUT}")

    (WORK / f"{tag}_report_v2.json").write_text(
        json.dumps({"voice": loudness(voice_wav), "mix": loudness(mix_wav),
                    "music_factor": args.bed, "chain": chain}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

