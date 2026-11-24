import json
from pathlib import Path

p = Path("analysis/interns/segments_sixth_words.json")
d = json.loads(p.read_text(encoding="utf-8"))
for s in d["segments"]:
    print("[{:.2f}-{:.2f}] {}".format(s["start"], s["end"], s["text"]))
    for w in s["words"]:
        print("   {:.2f}-{:.2f} {} ({})".format(
            w["start"], w["end"], w["word"], w["prob"]))
