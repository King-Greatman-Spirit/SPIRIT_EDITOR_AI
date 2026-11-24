import os
import subprocess

base = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(base, "Final_v4", "main_intern_sixth_emmanuel_v2.mp4")
dst = os.path.join(base, "Final_v4", "main_intern_sixth_emmanuel_v2_fixed.mp4")

f = ("drawbox=x=108:y=1164:w=516:h=64:color=0x14233b@1:t=fill:enable='between(t,9.95,15.5)',"
     "drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='My name is Emmanuel and I was placed':"
     "fontsize=27:fontcolor=white:x=(w-text_w)/2:y=1168:enable='between(t,9.95,15.5)',"
     "drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='at the Maintenance Department.':"
     "fontsize=27:fontcolor=white:x=(w-text_w)/2:y=1198:enable='between(t,9.95,15.5)'")

subprocess.run([
    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
    "-i", src,
    "-vf", f,
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    dst,
], check=True)
print("wrote", dst)
