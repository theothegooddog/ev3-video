import shutil
import sys
import subprocess
import os

if len(sys.argv) < 2:
    print("\033[31m[ERROR]\033[0m Usage: main.py <video_path> [-s|--speed <n>]")
    sys.exit(1)

speed = 1
if len(sys.argv) > 2 and sys.argv[2] in ("-s", "--speed"):
    try:
        speed = int(sys.argv[3])
    except (IndexError, ValueError):
        print("\033[31m[ERROR]\033[0m You must include a number after -s.")
        sys.exit(1)

def get_video_frame_count(video_path):
    # Construct the ffprobe CLI command arguments
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_packets",
        "-show_entries",
        "stream=nb_read_packets,r_frame_rate",
        "-of",
        "csv=p=0",
        video_path,
    ]

    # Run the command and capture standard output string data
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=True
    )

    # Clean the output text and split by comma
    # Output format is usually: frame_rate,total_frames (e.g., "30/1,900\n")
    output_parts = result.stdout.strip().split(",")

    if len(output_parts) >= 2:
        fps_raw = output_parts[0]
        total_frames = int(output_parts[1])

        # Evaluate fractional frame rates like 30000/1001 safely
        if "/" in fps_raw:
            num, denom = map(int, fps_raw.split("/"))
            fps = round(num / denom, 2)
        else:
            fps = float(fps_raw)

        return total_frames, fps

    raise ValueError("Could not parse frame metadata from video.")


if shutil.which("brew") is None:
    print("\033[31m[ERROR]\033[0m \033]8;;https://brew.sh\033\\Homebrew\033[0m\033]8;;\033\\ must be installed to run this script.")
    sys.exit(1)

result = subprocess.run(["brew", "install", "ffmpeg"])
if result.returncode != 0:
    print("[INFO] Homebrew install failed, attempting to fix directory ownership...")
    prefix = subprocess.run(
        ["brew", "--prefix"], capture_output=True, text=True
    ).stdout.strip()
    user = os.environ.get("USER", "")
    chown_result = subprocess.run(["sudo", "chown", "-R", user, prefix])
    if chown_result.returncode != 0:
        print("\033[31m[ERROR]\033[0m Could not fix Homebrew directory ownership.")
        sys.exit(1)

    result = subprocess.run(["brew", "install", "ffmpeg"])
    if result.returncode != 0:
        print("\033[31m[ERROR]\033[0m Failed to install ffmpeg via Homebrew.")
        sys.exit(1)

os.makedirs("output/frames", exist_ok=True)

subprocess.run([
    "ffmpeg", 
    "-i", sys.argv[1], 
    "-vf", "scale=178:128:force_original_aspect_ratio=decrease,pad=178:128:(ow-iw)/2:(oh-ih)/2,format=monob,threshold=level=0.5",
    "-vsync", "0", 
    "output/frames/frame_%d.png"
    ])

subprocess.run([
    "ffmpeg", 
    "-i", sys.argv[1], 
    "-vn", 
    "-acodec", "pcm_s16le", 
    "-ar", "22050", 
    "-ac", "1", 
    "output/audio.wav"
])

try:
    total_frames, fps = get_video_frame_count(sys.argv[1])
except (IndexError, ValueError, subprocess.CalledProcessError):
    print("\033[31m[ERROR]\033[0m Could not extract frame count.")
    sys.exit(1)

with open("output/main.py", "w") as f:
    f.write(
        f"""#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from _thread import start_new_thread as snt

ev3 = EV3Brick()

def d():
    for frame in range(1, {total_frames + 1}, {speed}):
"""
        + "        ev3.screen.load_image("frames/frame_" + str(frame) + ".png")"
        + """
snt(d, ())
ev3.speaker.play_file('audio.wav')
"""
    )

print("\033[32m\033[32m[SUCCESS]\033[0m\033[0m main.py written for Pybricks runtime.")
print("\033[32m\033[32m[SUCCESS]\033[0m\033[0m Completed! Check\n\033]8;;https://pybricks.com/ev3-micropython/startinstall.html\033\\Pybricks Docs - Installation\033[0m\033]8;;\033\\\nand\n\033]8;;https://pybricks.com/ev3-micropython/startrun.html#downloading-and-running-a-program\033\\Pybricks Docs - Downloading and running a program\033[0m\033]8;;\033\\")
