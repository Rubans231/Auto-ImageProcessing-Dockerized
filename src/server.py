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
MODEL_NAME = "gemma4:e4b"

# Ensure runtime directories are strictly present on boot
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(PALACE_DIR, exist_ok=True)

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
        print(f"❌ [CRITICAL] Failed to read image file headers: {e}")
        return 0


async def analyze_image_with_vlm(image_path, is_twilight=False):
    """Communicates directly with your local Qwen 3.6 MoE model layer."""
    filename = os.path.basename(image_path)
    time_context = "Daylight timeline (high baseline visibility)."
    if is_twilight:
        time_context = (
            "Twilight transition timeline (dim lighting, high shadow casting bounds)."
        )

    prompt = f"""
    You are an autonomous spatial analytics tracking agent monitoring long-term environmental drift.
    Analyze the provided image and extract physical shifts compared to typical dataset folder baselines.
    
    CORE ENVIRONMENT RUNTIME DATA:
    - Target File Asset: {filename}
    - Light Context Window: {time_context}
    
    CRITICAL INSTRUCTIONS:
    Identify environmental alterations (canopy changes, leaf drop, tree structure, erosion, terrain shifts), 
    count any human presence, and flag novel artifacts or missing objects compared to standard baseline frames.
    
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
        model=MODEL_NAME, prompt=prompt, images=[image_path]
    )
    result_text = response["response"].strip()

    # Clean up any potential markdown backtick blocks from the output
    if result_text.startswith("```json"):
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif result_text.startswith("```"):
        result_text = result_text.split("```")[1].split("```")[0].strip()

    return json.loads(result_text)


def commit_to_mempalace(category, log_string):
    """Programmatically pipes the log string into MemPalace via its CLI layer."""
    # Write log content to a temporary workspace file that MemPalace can mine
    tmp_log_path = os.path.join(PROJECT_ROOT, f"run/tmp_mem_{category}.txt")
    os.makedirs(os.path.dirname(tmp_log_path), exist_ok=True)

    with open(tmp_log_path, "w", encoding="utf-8") as f:
        f.write(log_string)

    try:
        # 1. Structural Guard: Force initialization check for MemPalace workspace files
        if not os.path.exists(os.path.join(PALACE_DIR, "mempalace.yaml")):
            subprocess.run(
                ["mempalace", "init"],
                cwd=PALACE_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # 2. Corrected Command Blueprint: Strip out --room entirely
        cmd = ["mempalace", "mine", "--wing", category, tmp_log_path]

        subprocess.run(
            cmd,
            cwd=PALACE_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        # Catch and print the underlying shell error strings to debug problems instantly
        error_msg = e.stderr.decode("utf-8").strip() if e.stderr else str(e)
        print(f"⚠️ [WARNING] MemPalace CLI error: {error_msg}")
    except Exception as e:
        print(f"⚠️ [WARNING] MemPalace CLI ingestion pipe encountered a hitch: {e}")
    finally:
        if os.path.exists(tmp_log_path):
            os.remove(tmp_log_path)


def archive_snapshot(image_path, date_str, time_str, analysis_summary):
    """Creates a chronological historical storage archive of the transaction."""
    snapshot_path = os.path.join(SNAPSHOTS_DIR, date_str, time_str)
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
        filename = os.path.basename(image_path)

        print(f"\n┠─ 📥 [INGESTION] Processing incoming drop element: {filename}")

        # 1. Run L1 Light Density Guardrail
        luminance = calculate_luminance(image_path)
        print(f"┃  ┣━━ Pixel Intensity: {luminance:.2f} RMS")

        if luminance < 2.0:
            print(
                f"┠─ 🌙 [PRE-FILTER] Dropping pitch black night frame. Terminating VLM compute line."
            )
            analysis = {
                "suggested_category": "unknown",
                "environmental_drift_detected": False,
                "metrics": {"status": "Nocturnal / Zero Visibility"},
                "detailed_log": "Asset automatically dropped by L1 pre-filter due to low light values.",
            }
            archive_snapshot(image_path, date_str, time_str, analysis)
            writer.write(b"SUCCESS: Night frame archived without compute footprint.\n")
            return

        # 2. Extract twilight parameters
        is_twilight = luminance < 35.0
        if is_twilight:
            print("┃  ┗━━ 🌗 Twilight shadow variance flagged. Adjusting logic bounds.")

        # 3. Trigger Local GPU Accelerated VLM Processing Matrix
        print(
            f"┠─ 🧠 [VLM COMPUTE] Offloading tensor graphs to {MODEL_NAME} over local CUDA..."
        )
        analysis = await analyze_image_with_vlm(image_path, is_twilight=is_twilight)
        category = analysis.get("suggested_category", "unknown")
        print(f"┃  ┗━━ 🎯 Model Categorization Match -> {category}")

        # 4. Commit Verbatim Analytics Directly into MemPalace CLI
        print(
            f"┠─ 🏛️ [MEMPALACE] Writing tracking matrices into Wing Memory Slot: {category}"
        )
        log_string = f"Timestamp: {now.isoformat()} | File: {filename} | Analysis: {analysis.get('detailed_log')}"
        commit_to_mempalace(category, log_string)

        archive_snapshot(image_path, date_str, time_str, analysis)
        writer.write(b"SUCCESS: Analytics loop committed cleanly.\n")
        print(
            f"┗─ 🏁 [PIPELINE CLEAN] Channel sequence reset. Monitoring active filesystem hooks."
        )

    except Exception as e:
        writer.write(f"ERROR: Execution failure -> {str(e)}\n".encode("utf-8"))
        print(f"❌ [CRITICAL RUNTIME ERROR]: {str(e)}")
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
