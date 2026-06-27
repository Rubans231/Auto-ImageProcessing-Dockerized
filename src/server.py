import asyncio
import os
import json
import urllib.request

# Absolute paths mapped relative to this script's location
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOCKET_PATH = os.path.join(PROJECT_ROOT, "run/img_engine/engine.sock")
WORKFLOW_PATH = os.path.join(PROJECT_ROOT, "workflows/workflow_api.json")

COMFYUI_ADDRESS = "127.0.0.1:8188"


def run_comfyui_pipeline(image_path):
    """Loads the ComfyUI API JSON graph and injects the dynamic image path into Node ID '1'."""
    if not os.path.exists(WORKFLOW_PATH):
        return f"ERROR: API workflow file missing at {WORKFLOW_PATH}"

    try:
        with open(WORKFLOW_PATH, "r") as f:
            prompt_graph = json.load(f)
    except Exception as e:
        return f"ERROR: Failed to read workflow JSON -> {str(e)}"

    # 🎯 TARGETING NODE ID "1" FROM YOUR COMFYUI API GRAPH
    TARGET_NODE_ID = "1"

    if TARGET_NODE_ID in prompt_graph:
        prompt_graph[TARGET_NODE_ID]["inputs"]["image"] = image_path
    else:
        return f"ERROR: Node ID '{TARGET_NODE_ID}' not found in the workflow JSON graph structure."

    # Construct the execution payload packet for ComfyUI's internal loop
    payload = {"prompt": prompt_graph}
    data = json.dumps(payload).encode("utf-8")

    try:
        url = f"http://{COMFYUI_ADDRESS}/prompt"
        req = urllib.request.Request(url, data=data)
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        return f"ERROR: Failed to forward execution request to ComfyUI port -> {str(e)}"


async def handle_client(reader, writer):
    """Processes incoming data streams arriving over the Unix Domain Socket."""
    print("[SERVER] Client connected via engine.sock!")
    try:
        data = await reader.read(2048)
        if data:
            payload_raw = data.decode("utf-8").strip()
            print(f"[SERVER] Intercepted incoming payload: {payload_raw}")

            # Parse the JSON packet sent by watcher.py
            job_config = json.loads(payload_raw)
            image_path = job_config.get("image_path")

            if not image_path:
                response_msg = "ERROR: Missing 'image_path' key in payload packet.\n"
            else:
                print(
                    f"[SERVER] Routing target asset to ComfyUI pipeline: {image_path}"
                )
                # Dispatch execution down to the ComfyUI API endpoint
                api_response = run_comfyui_pipeline(image_path)
                response_msg = (
                    f"SUCCESS: ComfyUI processing loop triggered -> {api_response}\n"
                )

            # Write back acknowledgment verification down the pipe to the watcher client
            writer.write(response_msg.encode("utf-8"))
            await writer.drain()

    except json.JSONDecodeError:
        print("[SERVER] Error: Received malformed, non-JSON data packet over socket.")
        writer.write(b"ERROR: Malformed payload format. Expecting valid JSON string.\n")
        await writer.drain()
    except Exception as e:
        print(f"[SERVER] Runtime Exception: {str(e)}")
        writer.write(f"ERROR: Internal engine exception -> {str(e)}\n".encode("utf-8"))
        await writer.drain()
    finally:
        print("[SERVER] Client disconnected from engine.sock.")
        writer.close()
        await writer.wait_closed()


async def main():
    # Force runtime environment directory tracking allocations
    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)

    # Prune stale, dead socket descriptors from past iterations
    if os.path.exists(SOCKET_PATH):
        print(f"[SERVER] Cleaning up old socket handle at {SOCKET_PATH}")
        os.remove(SOCKET_PATH)

    print(f"🤖 [SERVER] Initialized. Listening on UDS channel: {SOCKET_PATH}")
    server = await asyncio.start_unix_server(handle_client, path=SOCKET_PATH)

    async with server:
        try:
            await server.serve_forever()
        except KeyboardInterrupt:
            print("\n[SERVER] Shutdown signal intercepted.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        # Final cleanup pass to prevent leaving broken descriptors on disk
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        print("[SERVER] Engine channel clean. Goodbye.")
