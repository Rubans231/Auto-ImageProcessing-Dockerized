import sys
import os
import time
import json
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WATCH_DIR = os.path.join(PROJECT_ROOT, "workspace/input")
SOCKET_PATH = os.path.join(PROJECT_ROOT, "run/img_engine/engine.sock")

# Ensure the watched directory exists structurally on boot
os.makedirs(WATCH_DIR, exist_ok=True)


class ImageDropHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    def on_created(self, event):
        # Ignore raw directory creation events
        if event.is_directory:
            return

        # Target only incoming image assets
        file_ext = os.path.splitext(event.src_path)[1].lower()
        if file_ext in [".jpg", ".jpeg", ".png", ".webp"]:
            print(
                f"\n✨ [WATCHER] Detected new asset drop: {os.path.basename(event.src_path)}"
            )
            # Thread-safe dispatch back to the main async event socket runner loop
            asyncio.run_coroutine_threadsafe(
                self.send_to_server(event.src_path), self.loop
            )

    async def send_to_server(self, image_path):
        """Dispatches an asynchronous transaction token payload down the active UDS link."""
        # Introduce a brief structural delay to guarantee the file system write stream has fully closed
        await asyncio.sleep(0.5)

        if not os.path.exists(SOCKET_PATH):
            print(
                f"⚠️ [ERROR] Cannot route job. Server socket interface not found at: {SOCKET_PATH}"
            )
            return

        try:
            print(f"📡 [WATCHER] Linking to domain socket connection stream...")
            reader, writer = await asyncio.open_unix_connection(SOCKET_PATH)

            # Construct a clear, unified processing instructions packet
            payload = json.dumps({"image_path": os.path.abspath(image_path)})

            writer.write(payload.encode("utf-8"))
            await writer.drain()
            print(
                "🚀 [WATCHER] Payload matrix successfully dispatched to server engine. Awaiting conclusion..."
            )

            # Maintain active stream state until server responds or terminates connection line
            response = await reader.read(1024)
            print(f"🏁 [SERVER RESPONSE]: {response.decode('utf-8').strip()}")

            # Post-processing cleanup: Remove asset from the active hot folder drop target
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"🧹 [CLEANUP] Purged asset temporary pointer from hot-folder.")

        except Exception as e:
            print(f"❌ [WATCHER CRITICAL ERROR] Pipeline connection broken: {e}")
        finally:
            if "writer" in locals():
                writer.close()
                await writer.wait_closed()


def start_watcher():
    print(
        f"🟢 [ONLINE] Directory hot-folder observer active. Monitoring workspace area: {WATCH_DIR}"
    )
    loop = asyncio.new_event_loop()

    # Initialize the Watchdog monitoring thread configuration structures
    event_handler = ImageDropHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIR, recursive=False)
    observer.start()

    # Start the persistent background thread loop execution window
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n🛑 [SHUTDOWN] Terminating file system observation loops.")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_watcher()
