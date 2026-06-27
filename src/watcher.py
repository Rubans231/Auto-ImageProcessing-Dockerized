import os
import sys
import time
import json
import socket
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Absolute paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WATCH_DIR = os.path.join(PROJECT_ROOT, "workspace/input")
SOCKET_PATH = os.path.join(PROJECT_ROOT, "run/img_engine/engine.sock")


class ImageDropHandler(FileSystemEventHandler):
    def on_closed(self, event):
        # Triggers when a file is completely written to disk
        if event.is_directory:
            return

        file_path = event.src_path
        # Support common raw assets/images
        if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
            print(f"[WATCHER] New asset detected: {os.path.basename(file_path)}")
            self.send_to_engine(file_path)

    def send_to_engine(self, target_image_path):
        # Opens a swift client pipe to the Unix Domain Socket file
        if not os.path.exists(SOCKET_PATH):
            print(
                f"[WATCHER] Error: Engine socket not found at {SOCKET_PATH}. Is server.py running?"
            )
            return

        # Simple single-input payload dictionary mapping to Node ID "1"
        payload = {"image_path": target_image_path}

        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(SOCKET_PATH)
            client.sendall(json.dumps(payload).encode("utf-8"))

            # Read back verification acknowledgment from server
            response = client.recv(1024)
            print(f"[ENGINE RESPONSE] {response.decode('utf-8').strip()}")
            client.close()
        except Exception as e:
            print(f"[WATCHER] Failed to communicate over socket: {e}")


def main():
    os.makedirs(WATCH_DIR, exist_ok=True)

    event_handler = ImageDropHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)

    print(f"[WATCHER] Initialized. Watching kernel folder: {WATCH_DIR}")
    print("Drop an image file in there to test the loop")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher gracefully...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
