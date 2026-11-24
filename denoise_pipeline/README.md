# Interview audio denoise / voice isolation pipeline

Used to clean the five intern interview videos with a **different neural model** (DeepFilterNet)
after DPDFNet + `noisereduce` proved insufficient.

## Chain (v4)

```
MP4 -> extract 48 kHz mono WAV
    -> DeepFilterNet (deep-filter.exe, prebuilt Windows binary)
    -> noisereduce spectral gating with a real noise profile taken from each clip's silent gaps
    -> loudnorm (-16 LUFS, TP -1.5)
    -> Silero VAD silence gate (soft 15 ms edges)
    -> remux clean audio onto original video stream (-c:v copy)
```

## Install

```bash
pip install dpdfnet noisereduce silero-vad soundfile scipy
# DeepFilterNet on Windows: use the prebuilt CLI from
# https://github.com/Rikorose/DeepFilterNet/releases/download/v0.5.6/deep-filter-0.5.6-x86_64-pc-windows-msvc.exe
# place it at tools/deep-filter.exe
```

## Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File process_all_v4.ps1
```

Outputs go to `Final_v4/` next to the scripts.

## Tools

- `clean_pipeline.py` — DPDFNet, Demucs, Silero VAD gate, before/after metrics
- `strong_pass.py` — noise-profile spectral gating via `noisereduce`
- `df_pass.py` — wrapper around the prebuilt DeepFilterNet CLI
- `fix_subtitle.py` — burned-in caption correction for intern sixth

## Note

Rendered videos are intentionally **not** committed (see root `.gitignore`).
