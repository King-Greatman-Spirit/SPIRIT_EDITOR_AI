"""
Voice noise reduction / isolation pipeline for the intern interview videos.

Usage examples:
  python clean_pipeline.py denoise-dpdfnet audio\test.wav audio\test_dpdfnet.wav
  python clean_pipeline.py denoise-deepfilter audio\test.wav audio\test_deepfilter.wav
  python clean_pipeline.py strip-music audio\test.wav audio\test_vocals.wav
  python clean_pipeline.py gate-silence audio\test.wav audio\test_gated.wav
  python clean_pipeline.py verify audio\test.wav audio\test_clean.wav
"""
import os
import subprocess
import sys
import tempfile

SR = 48000


def denoise_dpdfnet(src, dst, model="dpdfnet2", attn=12):
    import dpdfnet
    out = dpdfnet.enhance_file(src, model=model, attn_limit_db=attn)
    if os.path.abspath(out) != os.path.abspath(dst):
        import shutil
        shutil.move(out, dst)
    print(f"[dpdfnet] wrote {dst}")


def denoise_deepfilter(src, dst):
    import soundfile as sf
    import torch
    from df import enhance, init_df

    x, sr = sf.read(src, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    model, df_state, _ = init_df()
    x = torch.tensor(x)
    y = enhance(model, df_state, x).cpu().numpy()
    sf.write(dst, y, sr)
    print(f"[deepfilter] wrote {dst}")


def strip_music(src, dst):
    """Keep only the 'vocals' (speech) stem using Demucs htdemucs."""
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [sys.executable, "-m", "demucs", "--two-stems=vocals", "-o", td, src],
            check=True,
        )
        found = []
        for root, _dirs, files in os.walk(td):
            for f in files:
                if f.lower().startswith("vocals"):
                    found.append(os.path.join(root, f))
        if not found:
            raise RuntimeError("Demucs produced no vocals stem")
        import shutil
        # Demucs emits 44.1 kHz stereo; normalize to 48 kHz mono for VAD + remux.
        tmp48 = dst + ".48k.wav"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", found[0], "-ar", str(SR), "-ac", "1",
             "-c:a", "pcm_s16le", tmp48],
            check=True,
        )
        shutil.move(tmp48, dst)
    print(f"[demucs] wrote {dst}")


def gate_silence(src, dst, threshold=0.5, min_silence_ms=350, pad_ms=250):
    """Mute every stretch where no speech is detected (uses Silero VAD)."""
    import numpy as np
    import soundfile as sf
    import torch

    y, sr = sf.read(src, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)

    try:
        from silero_vad import get_speech_timestamps, load_silero_vad
        model = load_silero_vad()
        ts = get_speech_timestamps(
            torch.tensor(y), model, sampling_rate=sr,
            threshold=threshold,
            min_silence_duration_ms=min_silence_ms,
            speech_pad_ms=pad_ms,
        )
    except Exception as e:
        print(f"[vad] silero_vad API failed ({e}); falling back to torch.hub", file=sys.stderr)
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad", model="silero_vad", trust_repo=True
        )
        get_ts = utils[0]
        ts = get_ts(
            torch.tensor(y), model, sampling_rate=sr,
            threshold=threshold,
            min_silence_duration_ms=min_silence_ms,
            speech_pad_ms=pad_ms,
        )

    mask = np.zeros_like(y)
    for seg in ts:
        a = max(0, int(seg["start"]))
        b = min(len(y), int(seg["end"]))
        mask[a:b] = 1.0
    # Soft 15 ms ramps at every boundary so hard gating doesn't click.
    from scipy.ndimage import uniform_filter1d
    mask = uniform_filter1d(mask, size=int(sr * 0.015), mode="nearest")
    out = y * mask
    sf.write(dst, out, sr)
    kept = sum(int(s["end"]) - int(s["start"]) for s in ts) / len(y)
    print(f"[vad] {len(ts)} speech segments, {kept*100:.1f}% of audio kept -> {dst}")


def stats(path):
    import numpy as np
    import soundfile as sf
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    rms = float(np.sqrt(np.mean(y ** 2)))
    peak = float(np.max(np.abs(y)))
    frame = int(sr * 0.02)
    n = len(y) // frame
    levels = np.array([
        np.sqrt(np.mean(y[i*frame:(i+1)*frame] ** 2)) + 1e-12 for i in range(n)
    ])
    db = 20 * np.log10(levels)
    return {
        "rms_db": round(20 * np.log10(rms + 1e-12), 1),
        "peak_db": round(20 * np.log10(peak + 1e-12), 1),
        "noise_floor_db": round(float(np.percentile(db, 20)), 1),
        "speech_db": round(float(np.percentile(db, 90)), 1),
        "duration_s": round(len(y) / sr, 1),
    }


def verify(a, b):
    print(f"  {'ORIGINAL':<28} {stats(a)}")
    print(f"  {'CLEANED':<28} {stats(b)}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    args = sys.argv[2:]
    {
        "denoise-dpdfnet": lambda: denoise_dpdfnet(*args),
        "denoise-deepfilter": lambda: denoise_deepfilter(*args),
        "strip-music": lambda: strip_music(*args),
        "gate-silence": lambda: gate_silence(*args),
        "verify": lambda: verify(*args),
    }[cmd]()
