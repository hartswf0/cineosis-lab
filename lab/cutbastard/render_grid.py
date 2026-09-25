"""The four WYGWYL cuts as one 2×2 grid film (1920×1080, suite audio) → wygwyl/cuts/grid.mp4."""
import os, subprocess
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wygwyl", "cuts")
FONT = "/System/Library/Fonts/Menlo.ttc"
CUTS = ["suite", "scenes", "cineosis", "drift"]
lab = lambda t: (f"scale=960:540,drawbox=x=0:y=0:w={20 + 11 * len(t)}:h=34:color=black@0.55:t=fill,"
                 f"drawtext=fontfile='{FONT}':text='{t}':x=12:y=9:fontsize=17:fontcolor=white")
fc = ";".join(f"[{i}:v]{lab(c.upper())}[v{i}]" for i, c in enumerate(CUTS)) + ";[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]"
args = ["ffmpeg", "-v", "error", "-y"] + sum([["-i", os.path.join(D, c, "cut.mp4")] for c in CUTS], []) + \
       ["-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", os.path.join(D, "grid.mp4")]
subprocess.run(args, check=True)
print("DONE", os.path.join(D, "grid.mp4"))
