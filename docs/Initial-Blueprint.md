# AUTONOMOUS CONTEXT AGENT PIPELINE

## Strategic Pivot & Core Philosophy

This masterplan documents the decoupling of the cognitive intelligence pipeline from node-based execution
models (ComfyUI). By running an autonomous Vision-Language Model (VLM) Agent natively in Python via
uv , the system evaluates contexts, executes dynamic inspection routines, auto-categorizes incoming visual
data, logs environmental mutations, and archives diagnostic timelines. ComfyUI is completely sidelined for this
phase and remains an independent rendering module for future integration tests.


## The Cognitive Lifecycle Loop

- Ingestion Event: Host-side kernel file-watcher catches a finalized image write via on_closed hooks and
ships the path over a Unix Domain Socket (UDS).
- Context Extraction: The Python server scans the local categories tree and compiles all current historical
markdown journals into an in-memory string context payload.
- VLM Evaluation Loop: The server invokes Qwen-2.5-VL via Ollama, passing the new image alongside
the historical text matrix to formulate an investigation plan and check for environmental degradation.
- State Synchronization: The engine generates an isolated debugging timeline folder containing copies of
all evaluation assets and appends structured markdown insights straight back to the original category log.

## Target Project Configuration Tree

  Auto-ImageProcessing-Dockerized/
  ├── pyproject.toml   # Modern project workspace settings file
  ├── uv.lock          # Deterministic package dependency tracking file
  ├── .venv/           # Local warehouse for downloaded wheel environments
  ├── input/           # Target ingest zone tracked by host watcher
  ├── snapshots/       # Timeline capture zone (history/YYYY-MM-DD/HH-MM-SS/)
  ├── run/
  │ └── img_engine/
  │ └── engine.sock    # Inter-process loopback UDS channel file
  ├── src/
  │ ├── watcher.py     # Local folder kernel event monitor
  │ └── server.py      # Context-aware orchestrator & local VLM wrapper
  └── categories/
  ├── forest_sector_a/
  │ └── history.md     # Continuous evolutionary context journal
  └── valley_viewpoint/
  └── history.md       # Continuous evolutionary context journal


## Operational Data Lifecycle Flow

[New Image Written to /input] 
             │
             ▼
[watcher.py Intercepts Kernel on_closed Event]
             │
             ▼ (Dispatches Payload over engine.sock)
[server.py Scans /categories/* Directories]
             │
             ▼ (Compiles All active history.md Content)
[In-Context Prompt Payload Dispatched to Qwen-2.5-VL]
             │
             ▼ (Model Evaluates Input vs. Historical States)
[UDS Server Parses JSON Delineating Drift Metrics]
             │
             ├──► [Generates Snapshots Mirror Room for Audit Trail]
             └──► [Appends Structured Analysis Block to Selected history.md]


## Environment & Dependency Management

The workspace relies on uv to manage isolated execution environments and provide deterministic state synchronization across platforms.

### Phase 1: Local Host Configuration (Current State)

- Dependencies are dynamically compiled and installed within the project root's local .venv/ cache.

- An active pyproject.toml configuration maps library tracking.

- The processing engine relies on an external local Ollama daemon execution pathway.

### Phase 2: Hybrid Container Topology (Future Target Integration)

- Virtual environments are bypassed inside the cluster wall; dependencies are synced globally inside the file layer via --system flags.

- All configuration pipelines pull directly from the pyproject.toml blueprint file to guarantee perfect replication.

- Directory pointers (/categories, /snapshots, /run) transition into isolated Docker volume mounts (-v) mapped straight into host partitions.
