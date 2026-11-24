"""Run the prebuilt DeepFilterNet CLI on a WAV file."""
import os
import shutil
import subprocess
import sys
import tempfile

base = os.path.dirname(os.path.abspath(__file__))
exe = os.path.join(base, "tools", "deep-filter.exe")
src, dst = sys.argv[1], sys.argv[2]

with tempfile.TemporaryDirectory() as td:
    subprocess.run([exe, src, "--output-dir", td], check=True)
    found = []
    for root, _dirs, files in os.walk(td):
        for f in files:
            if f.lower().endswith(".wav"):
                found.append(os.path.join(root, f))
    if not found:
        raise RuntimeError("DeepFilterNet produced no output WAV")
    shutil.move(found[0], dst)
print(f"[deepfilter] wrote {dst}")
