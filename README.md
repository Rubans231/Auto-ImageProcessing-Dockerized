# Autonomous Context Agent Pipeline

An intelligent, microservice-based autonomous image analytics pipeline. It combines kernel-level filesystem events with generative local vision models to provide a seamless, low-overhead contextual logging and environmental monitoring platform.

## Features

* **L1 Luminance Filter:** Automatically calculates frame exposure metrics to instantly drop zero-visibility nocturnal frames, saving active GPU compute cycles.
* **Decoupled Architecture:** Built on top of an asynchronous IPC loop over local Unix Domain Sockets (UDS), isolating the lightweight filesystem listener from the heavy token processing runtime.
* **Local Memory Matrix:** Programmatically commits semantic tracking data directly to a persistent, localized vector space database (MemPalace), keeping environmental records separated by logical wings.

## Documentation

* **Initial Blueprint:** [Initial Blueprint](docs/Initial-Blueprint.md) – Project masterplan, cognitive evaluation lifecycle loops, and foundational data management schemas.

## Quick Start (Docker Compose)

Best for local testing with GPU support.

### 1. Clone & Setup:

```bash
git clone <repository-url>
cd Auto-ImageProcessing-Dockerized

2. Run Backend & Services:

docker-compose up --build

3. Use:

- Ingestion Hot-Folder: Drop raw daylight snapshots (.jpg, .png) directly into workspace/input/ to trigger the automated evaluation sequence.

- Query Console: Execute conversational analysis inquiries against past dataset logs using your terminal space:

uv run python src/query.py <category_wing_folder> "<your analytical question>"
