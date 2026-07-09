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

```mermaid
graph LR
    %% Style definitions
    classDef root fill:#222,stroke:#fff,stroke-width:2px,color:#fff;
    classDef config fill:#334,stroke:#88a,stroke-width:1px,color:#ddd;
    classDef folder fill:#2c3e50,stroke:#34495e,stroke-width:1px,color:#ecf0f1;
    classDef script fill:#27ae60,stroke:#2ecc71,stroke-width:1px,color:#fff;

    %% 1. Explicitly declare nodes (Escaped with double quotes for slashes)
    ROOT["Auto-ImageProcessing-Dockerized/"] :::root
    PY["pyproject.toml"] :::config
    UV["uv.lock"] :::config
    DK["docker-compose.yml"] :::config
    INPUT["workspace/input/"] :::folder
    RUN["run/img_engine/"] :::folder
    SRC["src/"] :::folder
    CAT["categories/"] :::folder
    SOCK(["engine.sock - UDS IPC Channel"]) :::config
    WATCH["watcher.py - Kernel Monitor"] :::script
    SERV["server.py - Orchestrator"] :::script
    FOREST["forest_sector_a/"] :::folder
    VALLEY["valley_viewpoint/"] :::folder
    HIST1(["history.md - Context Journal"]) :::config
    HIST2(["history.md - Context Journal"]) :::config

    %% 2. Draw clean connection branches completely free of token symbols
    ROOT --> PY
    ROOT --> UV
    ROOT --> DK
    ROOT --> INPUT
    ROOT --> RUN
    ROOT --> SRC
    ROOT --> CAT
    
    RUN --> SOCK
    SRC --> WATCH
    SRC --> SERV
    
    CAT --> FOREST
    CAT --> VALLEY
    
    FOREST --> HIST1
    VALLEY --> HIST2

## Operational Data Lifecycle Flow

sequenceDiagram
    autonumber
    actor Host as Host File System
    participant Watcher as src/watcher.py (Container)
    participant Server as src/server.py (Container)
    participant VLM as Gemma-4:e4b via Ollama
    participant Journal as categories/history.md

    Host->>Watcher: New Image Written to /input/ (on_closed kernel event)
    Watcher->>Server: Dispatches file path payload over engine.sock (UDS IPC)
    Note over Server: Scans categories/* directories<br/>& compiles active history.md journals
    Server->>VLM: Dispatches Image + Historical Context text matrix
    Note over VLM: Evaluates input vs. historical states
    VLM-->>Server: Returns structured JSON (Delineating Drift/Anomalies)
    Server->>Host: Generates visual snapshot mirror room (Audit Trail)
    Server->>Journal: Appends markdown insights block to target history.md


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
