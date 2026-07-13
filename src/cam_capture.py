#!/usr/bin/env python3
"""
Run this ON THE LAPTOP — it is NOT part of the Docker stack and has no
dependency on the rest of this repo. It captures frames from the laptop's
webcam and drops them into the PC's workspace/input/<wing>/ hot-folder over
an SSHFS mount, so watcher.py picks them up exactly as if they'd been
dropped locally. No new networking server or protocol is required.

--------------------------------------------------------------------------
ONE-TIME SETUP
--------------------------------------------------------------------------

1) On the PC (Arch Linux host), make sure SSH is reachable:
       sudo systemctl enable --now sshd

2) On the laptop, install sshfs and mount the two folders this script needs
   (the input hot-folder to write into, and categories/ to read the
   "processed.jpg" completion signal from):

   Linux:
       sudo pacman -S sshfs      # or: sudo apt install sshfs
       mkdir -p ~/mnt/pc-input ~/mnt/pc-categories
       sshfs robin@<PC_IP>:/home/robin/Projects/Auto-ImageProcessing-Dockerized/workspace/input ~/mnt/pc-input
       sshfs robin@<PC_IP>:/home/robin/Projects/Auto-ImageProcessing-Dockerized/categories ~/mnt/pc-categories

   macOS:
       brew install macfuse sshfs
       (same mkdir/sshfs commands as above)

   Windows:
       Install WinFsp + SSHFS-Win, then map a network location to a path like
       \\\\sshfs\\robin@<PC_IP>\\home\\robin\\Projects\\Auto-ImageProcessing-Dockerized\\workspace\\input
       (and the same for .../categories), and pass those drive paths via
       --input-dir / --categories-dir below.

3) Install the one Python dependency this script needs, on the laptop:
       pip install opencv-python

--------------------------------------------------------------------------
USAGE
--------------------------------------------------------------------------
    python3 cam_capture.py --wing robinson2

This drops a frame into ~/mnt/pc-input/robinson2/, then waits for
categories/robinson2/processed.jpg (on the PC) to update before grabbing the
next one — so you get exactly one frame in flight at a time, paced by how
long your VLM actually takes, rather than a fixed guessed interval.
"""

import argparse
import os
import time

import cv2


def wait_for_processing(categories_dir, wing, dropped_at, timeout, poll_seconds=1):
    """Polls categories/<wing>/processed.jpg until its mtime is newer than the
    moment we dropped the frame — meaning the server finished this cycle."""
    marker = os.path.join(categories_dir, wing, "processed.jpg")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(marker) and os.path.getmtime(marker) > dropped_at:
            return True
        time.sleep(poll_seconds)
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Laptop webcam -> PC hot-folder frame feeder (paced by processing completion)"
    )
    parser.add_argument("--wing", required=True, help="Category folder name, e.g. robinson2")
    parser.add_argument("--input-dir", default=os.path.expanduser("~/mnt/pc-input"))
    parser.add_argument("--categories-dir", default=os.path.expanduser("~/mnt/pc-categories"))
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Minimum seconds to wait between frames, on top of the processing wait",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="Max seconds to wait for a frame to finish processing before moving on anyway",
    )
    args = parser.parse_args()

    drop_dir = os.path.join(args.input_dir, args.wing)
    os.makedirs(drop_dir, exist_ok=True)

    cap = cv2.VideoCapture(args.camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open camera index {args.camera_index}. On Linux, check "
            f"you're in the 'video' group and no other app has the camera open."
        )

    print(f"[CAM] Streaming into {drop_dir} (wing='{args.wing}'). Ctrl+C to stop.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("[CAM] Frame grab failed, retrying...")
                time.sleep(2)
                continue

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            final_name = f"{args.wing}_{timestamp}.jpg"
            tmp_path = os.path.join(drop_dir, f".{final_name}.tmp")
            final_path = os.path.join(drop_dir, final_name)

            cv2.imwrite(tmp_path, frame)
            os.rename(tmp_path, final_path)  # atomic rename: watcher only ever sees a finished file
            dropped_at = time.time()
            print(f"[CAM] Dropped {final_name}, waiting for processing...")

            done = wait_for_processing(
                args.categories_dir, args.wing, dropped_at, args.timeout
            )
            if not done:
                print(
                    "[CAM] Timed out waiting for processed.jpg to update — continuing "
                    "anyway. Check the SSHFS mount and `docker compose logs agent-server`."
                )
            time.sleep(max(0, args.interval))
    except KeyboardInterrupt:
        print("\n[CAM] Stopped by user.")
    finally:
        cap.release()


if __name__ == "__main__":
    main()
