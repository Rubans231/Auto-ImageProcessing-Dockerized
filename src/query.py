import sys
import os
import subprocess
import ollama

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PALACE_DIR = os.path.join(PROJECT_ROOT, "run/mempalace_db")
MODEL_NAME = "gemma4:e4b"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
sync_client = ollama.Client(host=OLLAMA_HOST)


def query_mempalace(category_wing, question):
    """Queries the MemPalace database programmatically through the CLI search runner."""
    try:
        # Executes the local search command isolated strictly to your target Wing
        result = subprocess.run(
            ["mempalace", "search", question, "--wing", category_wing],
            cwd=PALACE_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except Exception as e:
        print(
            f"⚠️ [WARNING] Failed to gather vector space fields from MemPalace CLI: {e}"
        )
        return "No historical records extracted."


def ask_agent(category_wing, user_question):
    print(
        f"🔍 [QUERY] Scanning MemPalace structural matrix inside Wing: '{category_wing}'..."
    )

    # 1. Fetch exact matching memories from the CLI layer
    context_str = query_mempalace(category_wing, user_question)
    if not context_str:
        context_str = "No structural historical tracking entries registered for this location yet."

    prompt = f"""
    You are an expert environmental analysis system evaluating historical camera timeline logs.
    
    HISTORICAL AUDIT LOG MEMORIES RECOVERED:
    {context_str}
    
    USER INVESTIGATION QUESTION:
    {user_question}
    
    Formulate a clear, descriptive, highly definitive, non-robotic conclusion summarizing the logs.
    """

    print(
        f"🧠 [THINKING] Processing context tokens through {MODEL_NAME} log analyzer matrix..."
    )
    response = sync_client.generate(model=MODEL_NAME, prompt=prompt)

    print("\n🕵️ [AGENT HISTORICAL REPORT]:")
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
