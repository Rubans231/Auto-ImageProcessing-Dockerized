import sys
import os
import subprocess
import ollama

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PALACE_DIR = os.path.join(PROJECT_ROOT, "run/mempalace_db")
MODEL_NAME = "gemma4:e4b"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
sync_client = ollama.Client(host=OLLAMA_HOST)


def query_mempalace(wing, room, question):
    """Queries the MemPalace database programmatically through the CLI search runner.

    MemPalace's `--wing` and `--room` are two SEPARATE filters (there's no
    slash-delimited nesting inside a single --wing value), e.g.:
        mempalace search "query" --wing myapp --room auth
    """
    try:
        cmd = ["mempalace", "search", question, "--wing", wing]
        if room:
            cmd += ["--room", room]

        result = subprocess.run(
            cmd,
            cwd=PALACE_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # This is the important fix: surface the ACTUAL mempalace error text
        # (e.stderr) instead of the generic "non-zero exit status" message.
        error_msg = e.stderr.strip() if e.stderr else str(e)
        print(f"[WARNING] MemPalace search failed: {error_msg}")
        return "No historical records extracted."
    except Exception as e:
        print(f"[WARNING] Failed to gather vector space fields from MemPalace CLI: {e}")
        return "No historical records extracted."


def ask_agent(category_wing, user_question):
    # Backward-compatible with calls like "Terrestrial/Forestry": split on the
    # first "/" into a proper (wing, room) pair instead of passing the whole
    # string as one literal --wing value that will never match anything.
    if "/" in category_wing:
        wing, room = category_wing.split("/", 1)
    else:
        wing, room = category_wing, None

    print(
        f"🔍 [QUERY] Scanning MemPalace structural matrix inside Wing: '{wing}'"
        + (f" / Room: '{room}'" if room else "")
        + "..."
    )

    # 1. Fetch exact matching memories from the CLI layer
    context_str = query_mempalace(wing, room, user_question)
    if not context_str:
        context_str = "No structural historical tracking entries registered for this location yet."

    prompt = f"""
    You are answering a quick factual question about historical camera logs.
    
    LOG MEMORIES RECOVERED:
    {context_str}
    
    QUESTION:
    {user_question}
    
    Answer in 2-4 plain, everyday sentences. No headers, no markdown, no
    bullet points, no repeating the question back, no filler phrases like
    "based on the analysis." Just the direct answer a person would say out
    loud. If the recovered memories don't actually answer the question, say
    so in one sentence instead of guessing.
    """

    print(
        f"[THINKING] Processing context tokens through {MODEL_NAME} log analyzer matrix..."
    )
    response = sync_client.generate(model=MODEL_NAME, prompt=prompt)

    print("\n[AGENT HISTORICAL REPORT]:")
    print("-" * 60)
    print(response["response"].strip())
    print("-" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: uv run python src/query.py <category_wing_folder> '<your analytical question>'"
        )
        sys.exit(1)
    ask_agent(sys.argv[1], sys.argv[2])
