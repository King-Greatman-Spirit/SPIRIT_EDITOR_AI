<div align="center">

# 🎬 SPIRIT EDITOR AI

### *An automated post-production pipeline that turns raw corporate interview footage into polished, social-ready portrait videos — with the interviewer silently removed.*

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-7%2B-4c8c3f?logo=ffmpeg&logoColor=white)
![Whisper](https://img.shields.io/badge/Whisper-large--v3-2ea44f?logo=openai&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Stars](https://img.shields.io/github/stars/King-Greatman-Spirit/SPIRIT_EDITOR_AI?style=social)

</div>

---

## 👀 What is this?

**SPIRIT EDITOR AI** is a battle-tested video production toolkit built for one very specific, very annoying problem:

> You record a corporate interview on a phone. The camera is held the wrong way, the interviewer keeps talking over the answer, there's room noise in the background, and you need a clean 9:16 portrait video with accurate subtitles and branded graphics — for ten different people.

This repo contains the full pipeline that solves that, end to end. It's not a toy demo: it has produced a library of finished interviews with a consistent look, correct display aspect ratio, word-accurate captions, and only the interviewee audible.

**No interview footage, transcripts, rendered videos, or personal data are included in this repository — source code only.**

---

## ✨ The headline features

| Feature | What it actually does |
|---|---|
| 🎯 **Display-ratio repair** | Detects source files that are *coded* landscape but *display* portrait (non-square SAR) and rebuilds them to true 9:16 1080×1920 — no stretching, no pillarboxing. |
| 🗣️ **Interviewer removal** | Maps the interviewer's exact questions and interjections, then mutes them completely while leaving the interviewee untouched. |
| 🧹 **Second-voice surgery** | Uses MFCC speaker fingerprints to find a *second* voice hiding inside the answer, then cuts those blocks out of the source timeline entirely. |
| 📝 **Word-accurate captions** | Uses Whisper `large-v3` with word timestamps so every subtitle appears on the exact word being spoken — no drift, no "subtitle faster than speech". |
| 🔊 **Audio forensics** | Envelope analysis and A/B transcription detect gated syllables, clipping and processing artifacts before delivery. |
| 🎨 **Brand-consistent graphics** | Generates question cards, lower-thirds and caption panels with a navy / white / gold identity, a cleaned logo, and a ducked music bed. |
| 📈 **Version discipline** | Every change produces a new version number. Approved renders are never overwritten. |

---

## 🧠 How it works

```
RAW FOOTAGE (phone, 4K, rotated, noisy)
        │
        ▼
┌───────────────────────┐
│  1. PROBE & INSPECT   │  ffprobe: codec, SAR/DAR, rotation, fps, audio
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  2. TRANSCRIBE        │  faster-whisper large-v3, beam 8, word timestamps
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  3. SPEAKER ANALYSIS  │  MFCC fingerprints → interviewer / interviewee / other voice
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  4. DECISION LAYER    │  mute? cut? keep? → edit decision list with exact timings
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  5. CLEAN SOURCE      │  optional frame-accurate cuts, re-mapped timeline
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  6. RENDER            │  FFmpeg filter_complex: scale, blur, overlays, ASS,
│                       │  denoise, mute windows, gain, limiter, music ducking
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│  7. VERIFY            │  container probe · loudness · mute windows ·
│                       │  envelope diff · A/B transcription · frame review
└───────────┬───────────┘
            ▼
     ✅ DELIVERABLE (vN.mp4)
```

### The audio decision layer

The most interesting part isn't the rendering — it's knowing **what to remove**:

1. **Transcribe everything.** Words, not just sentences, with timestamps.
2. **Build speaker centroids** from known interviewer and interviewee clips using MFCC statistics.
3. **Score every ambiguous segment** and validate with leave-one-out cross-validation before trusting it.
4. **Two responses:**
   - *Interviewer question* → keep the time, show a branded question card, mute the audio.
   - *Stray voice inside the answer* → cut the block out of the source entirely so no dead air is left behind.
5. **Re-map every downstream timestamp** (captions, cards, lower-thirds) through the cut timeline.

### Why gentle audio processing matters

An early version used an aggressive noise gate plus spectral denoise. It passed level checks but **silently deleted quiet syllables**. The fix was a verification method, not a guess:

- Compare RMS envelopes of source vs render → find windows where speech disappears.
- Re-transcribe both → if the render invents words, processing is too aggressive.
- Result: the gate was removed, denoise softened, and all speech preserved.

---

## 🛠️ Tech stack

- **Python 3.10+** — orchestration, graphics generation, analysis
- **faster-whisper / Whisper large-v3** — transcription with word timestamps
- **FFmpeg** (`libx264`, `libass`, `freetype`) — the entire render graph
- **Pillow** — branded PNG graphics (cards, lower-thirds, panels)
- **NumPy** — speaker fingerprinting and envelope diagnostics
- **ASS subtitles** — crisp, scalable captions burned in during render

---

## 🚀 Quick start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install FFmpeg (with libass + libx264)
winget install Gyan.FFmpeg          # Windows
# apt install ffmpeg                # Linux
# brew install ffmpeg               # macOS

# 3. Add your own source footage and branding assets
#    media/ and assets/ are intentionally git-ignored.

# 4. Transcribe an interview
python transcribe_intern.py FIRST large-v3

# 5. Review the transcript, build a curated caption JSON,
#    then render
python render_intern_first_v2.py --test   # 6-second smoke test
python render_intern_first_v2.py          # full render
```

> The renderer writes numbered outputs (`..._v1.mp4`, `..._v2.mp4`) and refuses to overwrite an existing file. You can't accidentally destroy an approved deliverable.

---

## 📁 Repository layout

```
SPIRIT_EDITOR_AI/
├── render_*.py              # Render pipelines (per interview, versioned)
├── transcribe_*.py          # Whisper transcription passes
├── build_*.py               # Caption / graphics builders
├── detect_*.py              # Question and speaker detection
├── fix_*.py                 # Targeted post-production corrections
├── make_*_short.py          # Short-form derivatives
├── requirements.txt
└── README.md
```

The versioned scripts (`v1`, `v2`, … `v7`) are intentional: they document how the pipeline evolved, including the problems that were found and fixed along the way.

---

## 🧪 Verification philosophy

Every deliverable is checked against its source, not just "looks fine":

- **Container:** resolution, SAR/DAR, fps, channel layout
- **Audio:** integrated loudness, true peak, per-window levels
- **Mute integrity:** interviewer windows must contain music only
- **Speech integrity:** envelope comparison + A/B transcription
- **Visuals:** sampled frames for cards, lower-thirds, caption fit and overflow

This is what turned several "good enough" renders into trustworthy ones.

---

## 🎯 Who is this for?

- Video editors who need repeatable, batch-friendly interview cleanup
- Developers interested in practical speech processing and FFmpeg filter graphs
- Anyone who has ever fought with portrait footage shot the wrong way

---

## ⚠️ Privacy & licensing note

This repository deliberately contains **no** interview recordings, faces, voices, transcripts, or client branding assets. The render scripts reference local paths that you must supply yourself. Any names appearing in code are generic placeholders/demo text from the development process — no personal interview material is distributed here.

---

<div align="center">

**Built with patience, ffmpeg, and an unreasonable attention to detail.**

⭐ Star the repo if this saved you an afternoon of editing.

</div>
