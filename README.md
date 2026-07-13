# Autonomous Context Agent Pipeline

An intelligent, microservice-based image analytics pipeline. It combines kernel-level
filesystem events with a locally-run vision-language model to provide low-overhead
environmental drift monitoring and contextual logging, backed by a local vector
memory layer ([MemPalace](https://mempalaceofficial.com)).

## Features

- **L1 Luminance Filter** — calculates frame exposure metrics to instantly drop
  zero-visibility nocturnal frames, saving GPU compute cycles.
- **Decoupled architecture** — an async IPC loop over a Unix Domain Socket (UDS)
  isolates the lightweight filesystem watcher from the VLM processing runtime.
- **Baseline comparison** — each category can define a `baseline.jpg` reference
  photo; every new frame is compared directly against it by the VLM.
- **Timelapse journal** — a separate, running `history.md` log per category tracks
  incremental frame-to-frame change, distinct from the baseline-relative record.
- **Local memory matrix** — commits semantic tracking data to MemPalace, organized
  into wings (category) and rooms (sub-topic), queryable in plain English.
- **Live camera ingestion** — feed a webcam on a separate machine into the hot-folder
  over SSHFS; see [`cam_capture.py`](../cam_capture.py).

## Documentation

- **Initial Blueprint:** [Initial Blueprint](Initial-Blueprint.md) — original project masterplan.
- **System Architecture:** [System Architecture & Lifecycle Guide](architecture.md) — service topology and data flow.
- **Deployment Guide:** [Deployment Guide](DEPLOYMENT.md) — container setup, verification, and live-camera setup.

## Quick Start (Docker Compose)

### 1. Clone & set up

```bash
git clone <repository-url>
cd Auto-ImageProcessing-Dockerized
```

### 2. Start the stack

```bash
docker compose up -d --build
```

### 3. Drop images to trigger analysis

Drop a `.jpg`/`.png` directly into a category folder to tag it explicitly, or into
`workspace/input/` on its own to let the VLM suggest a category:

```bash
cp my_photo.jpg workspace/input/robinson2/
```

Optional per-category assets (all under `categories/<wing>/`):

| File/Folder | Purpose |
|---|---|
| `baseline.jpg` | Fixed reference photo the VLM compares every new frame against |
| `processed.jpg` | Auto-generated copy of the last frame processed (also the "previous frame" reference for the timelapse diff) |
| `history.md` | Auto-generated running timelapse journal |
| `logs/` | Staged/mined log files feeding MemPalace (managed automatically) |

### 4. Query past analysis

```bash
docker compose exec agent-server python src/query.py <wing> "<your question>"
```

`<wing>` accepts either a plain category name (`robinson2`) or `wing/room`
(`robinson2/general`) if you're using rooms. Example:

```bash
docker compose exec agent-server python src/query.py robinson2 "what changed recently?"
```

For the raw, unsummarized MemPalace search results (useful for debugging):

```bash
docker compose exec agent-server mempalace search "<question>" --wing robinson2
```

### 5. Monitor logs

```bash
docker compose logs -f agent-server agent-watcher
```
