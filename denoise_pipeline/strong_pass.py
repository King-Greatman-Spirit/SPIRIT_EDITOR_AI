"""Second, stronger noise-removal pass using a real noise profile from the original audio."""
import sys
import numpy as np
import soundfile as sf
import torch
from silero_vad import get_speech_timestamps, load_silero_vad

src, dst = sys.argv[1], sys.argv[2]
orig_path = sys.argv[3] if len(sys.argv) > 3 else None

y, sr = sf.read(src, dtype="float32")
if y.ndim > 1:
    y = y.mean(axis=1)

if orig_path:
    o, osr = sf.read(orig_path, dtype="float32")
    if o.ndim > 1:
        o = o.mean(axis=1)
    model = load_silero_vad()
    ts = get_speech_timestamps(torch.tensor(o), model, sampling_rate=osr, threshold=0.5)
    gaps = []
    for i in range(len(ts) - 1):
        a, b = int(ts[i]["end"]), int(ts[i + 1]["start"])
        if b - a > osr * 1.5:
            gaps.append((b - a, a, b))
    gaps.sort(reverse=True)
    if not gaps:
        raise RuntimeError("No silent gap long enough to build a noise profile")
    _, a, b = gaps[0]
    noise = o[int(a + osr * 0.2): int(b - osr * 0.2)]
    print(f"Noise profile: {len(noise)/osr:.1f}s from original at {a/osr:.1f}s")
else:
    noise = None

import noisereduce as nr
out = nr.reduce_noise(
    y=y, sr=sr, y_noise=noise,
    stationary=True,
    prop_decrease=1.0,
    n_fft=2048,
    hop_length=512,
    freq_mask_smooth_hz=500,
    time_mask_smooth_ms=50,
)
sf.write(dst, out, sr)
print(f"wrote {dst}")
