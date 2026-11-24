import json
from pathlib import Path
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).resolve().parent
VIDEO = BASE_DIR / "edits" / "store_manager" / "full_interview_source.mp4"
OUTPUT_DIR = BASE_DIR / "analysis" / "store_manager"

def main():
    if not VIDEO.exists():
        raise FileNotFoundError(f"Combined interview not found: {VIDEO}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nSPIRIT EDITOR AI - QUESTION REVIEW")
    print("Loading Faster-Whisper small model...")

    model = WhisperModel("small", device="cpu", compute_type="int8")

    print("Transcribing full interview without VAD filtering...")

    segments, info = model.transcribe(
        str(VIDEO),
        language="en",
        beam_size=5,
        vad_filter=False,
        condition_on_previous_text=False,
        word_timestamps=True,
    )

    results = []

    for segment in segments:
        item = {
            "start": round(float(segment.start), 3),
            "end": round(float(segment.end), 3),
            "text": segment.text.strip(),
        }

        if segment.words:
            item["words"] = [
                {
                    "start": round(float(word.start), 3),
                    "end": round(float(word.end), 3),
                    "word": word.word,
                }
                for word in segment.words
            ]

        results.append(item)

        print(
            f"[{item['start']:07.2f} - {item['end']:07.2f}] "
            f"{item['text']}"
        )

    txt_path = OUTPUT_DIR / "question_review_transcript.txt"
    json_path = OUTPUT_DIR / "question_review_transcript.json"

    with txt_path.open("w", encoding="utf-8") as f:
        f.write("B.G. TECHNICAL LIMITED\n")
        f.write("MR. EJIOGU FRANCIS - QUESTION REVIEW\n")
        f.write("=" * 65 + "\n\n")

        for item in results:
            f.write(
                f"[{item['start']:07.2f} - {item['end']:07.2f}] "
                f"{item['text']}\n"
            )

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("\nREVIEW TRANSCRIPTION COMPLETED")
    print(f"Segments: {len(results)}")
    print(f"TXT: {txt_path}")
    print(f"JSON: {json_path}")

if __name__ == "__main__":
    main()
