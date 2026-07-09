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

```text
Auto-ImageProcessing-Dockerized/
├── pyproject.toml              # Project workspace settings
├── uv.lock                    # Deterministic dependency tracking
├── docker-compose.yml          # Multi-service container orchestration
│
├── workspace/
│   └── input/                  # Host ingestion hot-folder (Mounted Volume)
│
├── run/
│   └── img_engine/
│       └── engine.sock         # Inter-process UDS IPC channel file
│
├── src/
│   ├── watcher.py              # File-system kernel event monitor
│   └── server.py               # Context-aware orchestrator / VLM driver
│
└── categories/
    ├── forest_sector_a/
    │   └── history.md          # Continuous evolutionary context journal
    └── valley_viewpoint/
        └── history.md          # Continuous evolutionary context journal```
```
```

## Operational Data Lifecycle Flow

```text
```
[1. HOST FILESYSTEM] ──( New Image Dropped )──> [2. WATCHER.PY (Container)]
                                                          │
                                                ( Unix Domain Socket IPC )
                                                          ▼
[4. GEMMA-4:E4B (Ollama)] <──( Image+Context Matrix )── [3. SERVER.PY (Container)]
         │                                                │
  ( Evaluates Drift )                                     │ ( Appends Update )
         ▼                                                ▼
[ Structured JSON ]                             [5. CATEGORIES/HISTORY.MD]
```
```

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
