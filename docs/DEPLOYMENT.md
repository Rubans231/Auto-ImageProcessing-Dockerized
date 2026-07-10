# Deployment Guide

This document provides exhaustive instructions for initializing, configuring, and verifying the Autonomous Context Agent Pipeline within a containerized Docker environment.

---

## System Prerequisites

Ensure your host machine running Arch Linux meets the following infrastructure baselines:
* **Docker Engine** v20.10.0+ 
* **Docker Compose** v2.0.0+
* **NVIDIA Container Toolkit** (For CUDA-accelerated VLM execution)

---

## Orchestration Quickstart

### 1. Environment Configuration
The pipeline relies on a global configuration file to map host vector storage spaces. Ensure `mempalace_config.json` exists in your repository root:

```json
{
  "palace_path": "/app/run/mempalace_db",
  "collection_name": "mempalace_drawers",
  "people_map": {},
  "max_backups": 10
}
```


## Launching the Multi-Service Stack

Execute the orchestration command to clean trailing virtual volumes, build the custom agent layers, and spin up the microservices detached in the background:

```bash
docker compose down --volumes
docker compose up -d --build
```

## Service Topology & Verification

Once initialization routines conclude, verify operational status across your core execution engines:

| Service Name | Purpose | Validation Command |
| :--- | :--- | :--- |
| `ollama-core` | Accelerated VLM Graph Processing | `docker compose logs -f ollama-core` |
| `agent-server` | Socket Analytical API Webserver | `docker compose logs -f agent-server` |
| `agent-watcher` | Filesystem Event Hot-Folder Watchdog | `docker compose logs -f agent-watcher` |

---

### Database Persistence Check
To verify that SQLite and Chroma vector entries are successfully binding to your persistent host workspace drive instead of evaporating inside container boundaries, run:

```bash
ls -la run/mempalace_db/
```

## Database Persistence Check

To verify that SQLite and Chroma vector entries are successfully binding to your persistent host workspace drive instead of evaporating inside container boundaries, run:

```bash
ls -la run/mempalace_db/
```

