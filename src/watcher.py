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

# Ensure the watched root directory exists structurally on boot
os.makedirs(WATCH_DIR, exist_ok=True)


class DirectedCategoryHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    def on_created(self, event):
        self._handle_new_file(event)

    def on_moved(self, event):
        # IMPORTANT: many copy tools and file managers write a temp file
        # then rename() it into its final name once the write is complete
        # (an atomic-write pattern, common enough that it's the actual cause
        # of "the last file in a batch never got processed" — that file was
        # never `created` in the directory at all, it was moved/renamed into
        # it, which watchdog reports as on_moved, not on_created).
        # dest_path is where the file ended up; that's what we care about.
        self._handle_new_file(event, path=event.dest_path)

    def _handle_new_file(self, event, path=None):
        file_path = path or event.src_path

        # Ignore raw directory creation/move events
        if event.is_directory:
            return

        # Target only incoming image assets
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in [".jpg", ".jpeg", ".png", ".webp"]:
            # Extract relative directory structure to determine wing/room.
            # NOTE: MemPalace's data model is two-level (wing, then room),
            # not a single flat category string. We now preserve BOTH levels
            # instead of collapsing everything down to path_parts[0]:
            #   workspace/input/img.jpg                      -> wing=default, room=None
            #   workspace/input/robinson2/img.jpg             -> wing=robinson2, room=None
            #   workspace/input/Terrestrial/Forestry/img.jpg  -> wing=Terrestrial, room=Forestry
            # Anything nested deeper than 2 levels still only uses the first two.
            relative_path = os.path.relpath(file_path, WATCH_DIR)
            path_parts = relative_path.split(os.sep)

            if len(path_parts) >= 3:
                wing, room = path_parts[0], path_parts[1]
            elif len(path_parts) == 2:
                wing, room = path_parts[0], None
            else:
                wing, room = "default", None

            print(
                f"\n[WATCHER] Detected asset drop: {os.path.basename(file_path)} "
                f"Wing/Room Queue: [{wing}/{room or '-'}]"
            )

            # Thread-safe dispatch back to the main async event socket runner loop
            asyncio.run_coroutine_threadsafe(
                self.send_to_server(file_path, wing, room), self.loop
            )

    async def send_to_server(self, image_path, wing, room):
        """Dispatches an asynchronous transaction token payload down the active UDS link."""
        # Introduce a brief structural delay to guarantee the file system write stream has fully closed
        await asyncio.sleep(0.5)

        if not os.path.exists(SOCKET_PATH):
            print(
                f"[ERROR] Cannot route job. Server socket interface not found at: {SOCKET_PATH}"
            )
            return

        try:
            print(f"[WATCHER] Linking to domain socket connection stream...")
            reader, writer = await asyncio.open_unix_connection(SOCKET_PATH)

            # Construct a clear, unified processing instructions packet including wing/room routing
            payload_data = {
                "image_path": os.path.abspath(image_path),
                "wing": wing,
                "room": room,
            }
            payload = json.dumps(payload_data)

            writer.write(payload.encode("utf-8"))
            await writer.drain()
            print(
                f"[WATCHER] Payload matrix for [{wing}/{room or '-'}] successfully dispatched to server. Awaiting conclusion..."
            )

            # Maintain active stream state until server responds or terminates connection line
            response = await reader.read(1024)
            print(f"[SERVER RESPONSE]: {response.decode('utf-8').strip()}")

            # Post-processing cleanup: Remove asset from the active hot folder drop target
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"[CLEANUP] Purged asset temporary pointer from hot-folder.")

        except Exception as e:
            print(f"[WATCHER CRITICAL ERROR] Pipeline connection broken: {e}")
        finally:
            if "writer" in locals():
                writer.close()
                await writer.wait_closed()


def start_watcher():
    print(
        f"[ONLINE] Directory hot-folder observer active. Monitoring workspace area: {WATCH_DIR}"
    )
    loop = asyncio.new_event_loop()

    # Initialize the Watchdog monitoring thread configuration structures
    event_handler = DirectedCategoryHandler(loop)
    observer = Observer()

    # CRITICAL REFRACTOR: recursive=True enables tracking subfolders dropped into input/
    observer.schedule(event_handler, path=WATCH_DIR, recursive=True)
    observer.start()

    # Start the persistent background thread loop execution window
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Terminating file system observation loops.")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_watcher()
