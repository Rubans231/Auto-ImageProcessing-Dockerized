import asyncio
import os
import json
import shutil
import subprocess
from datetime import datetime
import ollama
from PIL import Image, ImageStat

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOCKET_PATH = os.path.join(PROJECT_ROOT, "run/img_engine/engine.sock")
SNAPSHOTS_DIR = os.path.join(PROJECT_ROOT, "snapshots")
PALACE_DIR = os.path.join(PROJECT_ROOT, "run/mempalace_db")
CATEGORIES_DIR = os.path.join(PROJECT_ROOT, "categories")
MODEL_NAME = "gemma4:e4b"

# Ensure runtime directories are strictly present on boot
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(PALACE_DIR, exist_ok=True)
os.makedirs(CATEGORIES_DIR, exist_ok=True)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
async_client = ollama.AsyncClient(host=OLLAMA_HOST)


def calculate_luminance(image_path):
    """Calculates the average perceived luminance of an image using Grayscale RMS."""
    try:
        with Image.open(image_path) as img:
            gray_img = img.convert("L")
            stat = ImageStat.Stat(gray_img)
            return stat.rms[0]  # Value bounds range between 0.0 and 255.0
    except Exception as e:
        print(f"[CRITICAL] Failed to read image file headers: {e}")
        return 0


def find_baseline_image(wing):
    """Looks for categories/<wing>/baseline.<ext> to use as a VLM comparison reference.
    Returns None for the "default" bucket (its true wing isn't known until after
    the VLM call) or if no baseline file exists yet for this category."""
    if not wing or wing == "default":
        return None
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        candidate = os.path.join(CATEGORIES_DIR, wing, f"baseline{ext}")
        if os.path.exists(candidate):
            return candidate
    return None


async def analyze_image_with_vlm(
    image_path, is_twilight=False, folder_category="default", baseline_path=None
):
    """Communicates directly with your local VLM layer with queue context."""
    filename = os.path.basename(image_path)
    time_context = "Daylight timeline (high baseline visibility)."
    if is_twilight:
        time_context = (
            "Twilight transition timeline (dim lighting, high shadow casting bounds)."
        )

    if baseline_path:
        baseline_note = (
            "A baseline reference photo for this category is attached as the "
            "FIRST image. The CURRENT frame under analysis is the SECOND image. "
            "Compare the current frame directly against this specific baseline "
            "and describe what has physically changed between the two."
        )
        images = [baseline_path, image_path]
    else:
        baseline_note = (
            "No baseline reference photo exists yet for this category. Describe "
            "the scene on its own merits without a direct before/after comparison."
        )
        images = [image_path]

    prompt = f"""
    You are an autonomous spatial analytics tracking agent monitoring long-term environmental drift.
    Analyze the provided image(s) and extract physical shifts relative to the category baseline.
    
    CORE ENVIRONMENT RUNTIME DATA:
    - Target File Asset: {filename}
    - Dataset Source/Folder Queue: {folder_category}
    - Light Context Window: {time_context}
    - Baseline Comparison: {baseline_note}
    
    CRITICAL INSTRUCTIONS:
    Identify environmental alterations (canopy changes, leaf drop, tree structure, erosion, terrain shifts), 
    count any human presence, and flag novel artifacts or missing objects compared to the baseline.
    
    You MUST output a raw JSON object string matching exactly this schema layout:
    {{
        "suggested_category": "string_folder_name",
        "environmental_drift_detected": true/false,
        "metrics": {{
            "human_density_count": 0,
            "novel_objects_detected": ["item_a"],
            "missing_objects": []
        }},
        "detailed_log": "A descriptive, natural, non-robotic analysis detailing the physical scene elements."
    }}
    Output ONLY the raw valid JSON string. Do not append Markdown code blocks, backticks, or conversational text.
    """

    response = await async_client.generate(
        model=MODEL_NAME, prompt=prompt, images=images
    )
    result_text = response["response"].strip()

    # Clean up any potential markdown backtick blocks from the output
    if result_text.startswith("```json"):
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif result_text.startswith("```"):
        result_text = result_text.split("```")[1].split("```")[0].strip()

    return json.loads(result_text)


def ensure_palace_initialized():
    """Runs `mempalace init` exactly once, using our own marker file (not a guessed
    mempalace-internal filename) so we can tell whether init actually succeeded."""
    marker = os.path.join(PALACE_DIR, ".initialized")
    if os.path.exists(marker):
        return
    try:
        # `mempalace init` REQUIRES a positional <dir> argument (docs: "Running
        # `mempalace init` with no argument will exit with `error: the following
        # arguments are required: dir`"). The old code called it with no dir at
        # all, so it silently failed every single time.
        subprocess.run(
            ["mempalace", "init", ".", "--yes"],
            cwd=PALACE_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        with open(marker, "w") as f:
            f.write("ok")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode("utf-8").strip() if e.stderr else str(e)
        print(f"[WARNING] mempalace init failed: {error_msg}")


def commit_to_mempalace(wing, room, log_string):
    """Pipes the log string into MemPalace via its CLI layer.

    Logs are staged under categories/<wing>/logs/pending/<room>/ — a real,
    permanent location (matching your existing categories/<wing>/baseline.jpg
    layout) rather than a throwaway temp file. This matters because
    `mempalace mine <dir>` mines a DIRECTORY, not a single file (confirmed in
    the official CLI reference) — the previous version pointed it at one
    .txt file, which is very likely why nothing was landing in the palace.

    After a successful mine, everything just mined is moved from
    logs/pending/ into logs/mined/, so the next commit's `mine` call only
    ever sees genuinely new material (mempalace's CLI doesn't document
    built-in incremental/skip-already-mined behavior for `mine`, so we track
    that ourselves rather than assume it).
    """
    ensure_palace_initialized()

    room_name = room if room else "general"
    category_dir = os.path.join(CATEGORIES_DIR, wing)
    pending_root = os.path.join(category_dir, "logs", "pending")
    mined_root = os.path.join(category_dir, "logs", "mined")
    pending_room_dir = os.path.join(pending_root, room_name)
    os.makedirs(pending_room_dir, exist_ok=True)
    os.makedirs(mined_root, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_path = os.path.join(pending_room_dir, f"log_{timestamp}.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_string)

    cmd = ["mempalace", "mine", pending_root, "--wing", wing]

    try:
        result = subprocess.run(
            cmd,
            cwd=PALACE_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(
            f"[MEMPALACE] Mined wing='{wing}' room='{room_name}': "
            f"{result.stdout.decode('utf-8').strip()}"
        )
        # Archive everything that was just mined so it's never re-mined.
        for root, _dirs, files in os.walk(pending_root):
            for fname in files:
                src = os.path.join(root, fname)
                rel = os.path.relpath(src, pending_root)
                dst = os.path.join(mined_root, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode("utf-8").strip() if e.stderr else str(e)
        print(f"[WARNING] MemPalace CLI error: {error_msg}")
        # Leave files in pending/ untouched so they're retried on the next commit.
    except Exception as e:
        print(f"[WARNING] MemPalace CLI ingestion pipe encountered a hitch: {e}")


def archive_snapshot(image_path, date_str, time_str, category, analysis_summary):
    """Creates a chronological historical storage archive broken down by target category."""
    snapshot_path = os.path.join(SNAPSHOTS_DIR, category, date_str, time_str)
    os.makedirs(snapshot_path, exist_ok=True)
    shutil.copy(image_path, os.path.join(snapshot_path, os.path.basename(image_path)))
    with open(os.path.join(snapshot_path, "analytics_conclusion.json"), "w") as f:
        json.dump(analysis_summary, f, indent=2)


async def handle_client(reader, writer):
    data = await reader.read(2048)
    if not data:
        return

    now = datetime.now()
    date_str, time_str = now.strftime("%Y-%m-%d"), now.strftime("%H-%M-%S")

    try:
        job = json.loads(data.decode("utf-8").strip())
        image_path = job.get("image_path")
        watcher_wing = job.get("wing", "default")
        watcher_room = job.get("room")
        filename = os.path.basename(image_path)

        print(f"\n┠─ [INGESTION] Processing incoming drop element: {filename}")
        print(f"┃  ┣━━ Watcher Wing/Room Queue: [{watcher_wing}/{watcher_room or '-'}]")

        # 1. Run L1 Light Density Guardrail
        luminance = calculate_luminance(image_path)
        print(f"┃  ┣━━ Pixel Intensity: {luminance:.2f} RMS")

        if luminance < 2.0:
            print(
                f"┠─ [PRE-FILTER] Dropping pitch black night frame. Terminating VLM compute line."
            )
            analysis = {
                "suggested_category": watcher_wing,
                "environmental_drift_detected": False,
                "metrics": {"status": "Nocturnal / Zero Visibility"},
                "detailed_log": "Asset automatically dropped by L1 pre-filter due to low light values.",
            }
            archive_snapshot(image_path, date_str, time_str, watcher_wing, analysis)
            writer.write(b"SUCCESS: Night frame archived without compute footprint.\n")
            return

        # 2. Extract twilight parameters
        is_twilight = luminance < 35.0
        if is_twilight:
            print("┃  ┗━━ Twilight shadow variance flagged. Adjusting logic bounds.")

        # 3. Trigger Local GPU Accelerated VLM Processing Matrix
        print(
            f"┠─ [VLM COMPUTE] Offloading tensor graphs to {MODEL_NAME} over local CUDA..."
        )
        baseline_path = find_baseline_image(watcher_wing)
        if baseline_path:
            print(f"┃  ┣━━ Baseline reference found: {baseline_path}")
        # Pass the watcher directory category into the prompt context for better inference
        analysis = await analyze_image_with_vlm(
            image_path,
            is_twilight=is_twilight,
            folder_category=watcher_wing,
            baseline_path=baseline_path,
        )

        # Route to the explicitly watched folder wing unless it's default fallback
        final_wing = (
            watcher_wing
            if watcher_wing != "default"
            else analysis.get("suggested_category", "unknown")
        )
        final_room = watcher_room  # None if the drop wasn't in a nested subfolder
        print(
            f"┃  ┗━━ Final Resolved Target Storage Allocation Slot -> [{final_wing}/{final_room or '-'}]"
        )

        # 4. Commit Verbatim Analytics Directly into MemPalace CLI
        print(
            f"┠─ [MEMPALACE] Writing tracking matrices into Wing Memory Slot: {final_wing}/{final_room or '-'}"
        )
        log_string = f"Timestamp: {now.isoformat()} | File: {filename} | Wing: {final_wing} | Room: {final_room or 'general'} | Analysis: {analysis.get('detailed_log')}"
        commit_to_mempalace(final_wing, final_room, log_string)

        archive_snapshot(image_path, date_str, time_str, final_wing, analysis)
        writer.write(b"SUCCESS: Analytics loop committed cleanly.\n")
        print(
            f"┗─ [PIPELINE CLEAN] Channel sequence reset. Monitoring active filesystem hooks."
        )

    except Exception as e:
        writer.write(f"ERROR: Execution failure -> {str(e)}\n".encode("utf-8"))
        print(f"[CRITICAL RUNTIME ERROR]: {str(e)}")
    finally:
        await writer.drain()
        writer.close()


async def main():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)

    server = await asyncio.start_unix_server(handle_client, path=SOCKET_PATH)
    print(
        f"🟢 [ONLINE] Core server engine successfully listening on domain socket: {SOCKET_PATH}"
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
