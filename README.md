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
  over SSHFS; see [`cam_capture.py`](/src/cam_capture.py).

## Documentation

- **Initial Blueprint:** [Initial Blueprint](docs/Initial-Blueprint.md) — original project masterplan.
- **System Architecture:** [System Architecture & Lifecycle Guide](docs/architecture.md) — service topology and data flow.
- **Deployment Guide:** [Deployment Guide](docs/DEPLOYMENT.md) — container setup, verification, and live-camera setup.

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

## Dashboard

A browser dashboard is available at `http://localhost:8080` once `api-server`
and `frontend` are running (see `docker-compose.additions.yml`). It covers:

- **Overview** — baseline vs. latest frame, the core-sample timeline, the
  timelapse journal, and plain-English search
- **Snapshot Logs** — a full detail table per snapshot (novel/missing
  objects, human counts, complete log text)
- **Graphs** — drift events and people-detected counts over time, updating
  live via server-sent events
- **Add Frames** — drop a batch of images (queued client-side, uploads a
  couple at a time), drop a video (choose frame-extraction mode per upload —
  every frame, or every N seconds), or capture directly from the browser's
  own camera. A capture-interval **Settings** panel (⚙, top right) applies
  globally or per-category
- **Browse Files** — read-only browser over `categories/`, `snapshots/`, and
  `workspace/input/`, with download links

Note: browser camera capture requires a secure context (`localhost` or
HTTPS) — browsers block camera access otherwise. For a camera on a
*different* machine, use [`cam_capture.py`](/src/cam_capture.py) instead
(see the Deployment guide); that path still works independently of the
dashboard's browser-capture option.
