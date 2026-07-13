# Deployment Guide

Instructions for initializing, configuring, and verifying the Autonomous Context
Agent Pipeline in a containerized Docker environment.

---

## System Prerequisites

- **Docker Engine** v20.10.0+
- **Docker Compose** v2.0.0+
- **NVIDIA Container Toolkit** (for CUDA-accelerated VLM execution)
- Host OS: Arch Linux (other Linux distributions should work but are untested)

---

## Orchestration Quickstart

### 1. Environment configuration

Ensure `mempalace_config.json` exists in the repository root:

```json
{
  "palace_path": "/app/run/mempalace_db",
  "collection_name": "mempalace_drawers",
  "people_map": {},
  "max_backups": 10
}
```

### 2. Launch the stack

```bash
docker compose down --volumes
docker compose up -d --build
```

---

## Service Topology & Verification

| Service | Purpose | Validation command |
|---|---|---|
| `ollama-core` | Accelerated VLM graph processing | `docker compose logs -f ollama-core` |
| `agent-server` | Socket-based analytics processor | `docker compose logs -f agent-server` |
| `agent-watcher` | Filesystem hot-folder watchdog | `docker compose logs -f agent-watcher` |

### Database persistence check

Confirm MemPalace entries are binding to the host volume instead of evaporating
inside the container:

```bash
ls -la run/mempalace_db/
docker compose exec agent-server mempalace status
```

`mempalace status` is the fastest sanity check — it shows drawer counts broken
down by wing/room, so you can confirm ingestion is actually landing before
trusting a `query.py` result.

### End-to-end smoke test

```bash
cp some_test_photo.jpg workspace/input/robinson2/
docker compose logs -f agent-server   # watch for "Drawers filed: N"
docker compose exec agent-server python src/query.py robinson2 "last log"
```

---

## Live Camera Ingestion (Optional)

If you want to feed a webcam on a *different* machine (e.g. a laptop) into this
pipeline running on the PC, the simplest approach is an SSHFS mount rather than a
custom streaming server — no extra ports or protocols required.

### 1. On the PC: ensure SSH is reachable

```bash
sudo systemctl enable --now sshd
```

### 2. On the laptop: mount the two folders you need

```bash
sudo pacman -S sshfs        # or apt install sshfs / brew install macfuse sshfs
mkdir -p ~/mnt/pc-input ~/mnt/pc-categories
sshfs robin@<PC_IP>:/home/robin/Projects/Auto-ImageProcessing-Dockerized/workspace/input ~/mnt/pc-input
sshfs robin@<PC_IP>:/home/robin/Projects/Auto-ImageProcessing-Dockerized/categories ~/mnt/pc-categories
```

### 3. On the laptop: install the capture script's one dependency

```bash
pip install opencv-python
```

### 4. Run the capture loop

```bash
python3 cam_capture.py --wing robinson2
```

This drops a frame into `~/mnt/pc-input/robinson2/`, then waits for
`categories/robinson2/processed.jpg` (on the PC) to update before capturing the
next one — so the capture rate is naturally paced by how long the VLM actually
takes, rather than a fixed guessed interval. See the script's own docstring for
Windows/macOS mount variants and all CLI flags.

> Note: this is a *different* direction than Sunshine/Moonlight, which streams
> the PC's display and input to the laptop. There's no need to change your
> Sunshine/Moonlight setup for this — the camera feed travels over the SSHFS
> mount independently.
