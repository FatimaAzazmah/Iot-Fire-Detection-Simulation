# 🔥 IoT Fire-Detection Network Simulation

> A real-time **Wireless & IoT** simulation of a fire-detection system: edge **gateways** stream sensor data to a **cloud server** over a custom TCP protocol, and the cloud monitors rooms and vehicles, triggers alarms and sprinklers, and visualizes everything on a live dashboard.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Networking-TCP%20Sockets-1abc9c.svg" alt="TCP Sockets">
  <img src="https://img.shields.io/badge/Concurrency-Multithreaded-e67e22.svg" alt="Multithreaded">
  <img src="https://img.shields.io/badge/Domain-IoT%20%2F%20Edge--Cloud-9b59b6.svg" alt="IoT">
</p>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Communication Protocol](#-communication-protocol)
- [Features](#-features)
- [Monitored Entities](#-monitored-entities)
- [Installation](#-installation)
- [Running the Simulation](#-running-the-simulation)
- [Dashboard & Commands](#-dashboard--commands)
- [Scenarios](#-scenarios)
- [Project Structure](#-project-structure)
- [Authors](#-authors)

---

## 🔎 Overview

This project simulates a small **edge-to-cloud IoT network** for fire and safety monitoring. It was built for a **Wireless and IoT** course and demonstrates the core building blocks of a networked sensor system:

- **Socket programming** — a custom application-layer protocol over TCP.
- **Client–server architecture** — one cloud server accepting multiple gateways.
- **Concurrency** — a multithreaded server handling connections, UI, and plotting in parallel.
- **Real-time monitoring** — live matplotlib charts plus a terminal dashboard.
- **Reliability** — periodic heartbeats and automatic gateway reconnection.
- **Remote control** — the cloud can pause/resume gateways and inject scenarios.

The two programs form a **complete, self-contained system** — no external tools are required. Start the cloud server, start one or more gateways, and the whole pipeline runs on `localhost`.

---

## 🏗 Architecture

```
        ┌─────────────────────────┐                 ┌──────────────────────────────┐
        │      GATEWAY (edge)      │   TCP :5555     │        CLOUD SERVER          │
        │      gateway_plus.py     │ ──────────────► │      cloud_server_plus.py    │
        │                          │   DATA /        │                              │
        │  • Room 1 sensors        │   HEARTBEAT     │  • Multithreaded TCP server  │
        │  • Room 2 sensors        │                 │  • Alarm / sprinkler logic   │
        │  • Car 1 & Car 2         │ ◄────────────── │  • Live matplotlib dashboard │
        │  • Auto-reconnect        │   CONTROL       │  • Terminal dashboard + CLI  │
        └─────────────────────────┘                 │  • CSV export                │
                                                     └──────────────────────────────┘
```

- The **gateway** generates realistic sensor readings (with noise), sends them once per second, and sends a heartbeat every 15 seconds.
- The **cloud server** ingests the stream, applies threshold-based safety logic, and renders live plots. It can push `CONTROL` messages back to gateways to pause them or run scenarios.

---

## 📡 Communication Protocol

Messages are newline-delimited **JSON** objects sent over a single TCP stream. There are three message types:

| Type | Direction | Purpose |
| --- | --- | --- |
| `HEARTBEAT` | gateway → cloud | Liveness signal (`gateway_id`, `seq`, `timestamp`). |
| `DATA` | gateway → cloud | Sensor readings for both rooms and both cars. |
| `CONTROL` | cloud → gateway | Commands: `PAUSE`, `RESUME`, `SCENARIO`. |

**Example `DATA` message:**

```json
{
  "type": "DATA",
  "gateway_id": "GW-1",
  "seq": 42,
  "timestamp": 1695471116.85,
  "sensors": {
    "smoke1": 45.71, "co2_1": 445, "fire1": 24.93,
    "smoke2": 35.88, "co2_2": 393, "fire2": 25.45,
    "car1_temp": 24.9, "car1_status": "PARKED",
    "car2_temp": 25.1, "car2_status": "PARKED"
  }
}
```

---

## ✨ Features

- ✅ Custom TCP protocol with `HEARTBEAT` / `DATA` / `CONTROL` messages.
- ✅ Multithreaded cloud server supporting multiple concurrent gateways.
- ✅ Automatic reconnection on the gateway when the link drops.
- ✅ Threshold-based **alarm** and **sprinkler** activation per room.
- ✅ Live **matplotlib** dashboard (4 real-time charts) + a **terminal** dashboard.
- ✅ Interactive command console (pause/resume, scenarios, device control, stats).
- ✅ Injectable **scenarios** (fire, high CO₂, vehicle overheating).
- ✅ **CSV export** of the collected time series.

---

## 🛰 Monitored Entities

| Entity | Sensors / State | Safety logic |
| --- | --- | --- |
| **Room 1200400** | smoke, CO₂, fire | Alarm at smoke ≥ 60, sprinkler at smoke ≥ 65 |
| **Room 1211371** | smoke, CO₂, fire | Alarm at smoke ≥ 60, sprinkler at smoke ≥ 65 |
| **Car 1** | engine temperature, status | Tracks PARKED → RUNNING → OVERHEATING |
| **Car 2** | engine temperature, status | Tracks PARKED → RUNNING → OVERHEATING |

---

## 🛠 Installation

**Requirements:** Python 3.8+ (with Tkinter, bundled with standard Python on Windows/macOS).

```bash
# 1. Clone the repository
git clone https://github.com/FatimaAzazmah/Iot-Fire-Detection-Simulation.git
cd Iot-Fire-Detection-Simulation

# 2. (Recommended) create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## ▶ Running the Simulation

Open **two terminals**. Start the cloud server first, then the gateway.

**Terminal 1 — cloud server (opens the live dashboard):**

```bash
python cloud_server_plus.py
```

**Terminal 2 — gateway (starts streaming sensor data):**

```bash
python gateway_plus.py
```

You can start **multiple gateways** (each with a different `gw_id`) to simulate several edge nodes reporting to the same cloud.

---

## 🖥 Dashboard & Commands

The cloud server prints a live terminal dashboard and accepts commands:

```
==============================================================
🔥 FIRE DETECTION CLOUD DASHBOARD (LIVE)
==============================================================
Connections: 🟢 Active=1 | Packets=128 | LastSeq=128

ROOM 1200400:
  SMOKE=45.30 CO2=451.00 FIRE=24.90 ALARM=OFF SPRINK=OFF
ROOM 1211371:
  SMOKE=36.10 CO2=390.00 FIRE=25.40 ALARM=OFF SPRINK=OFF
CAR1: STATUS=PARKED ENGINE_TEMP=24.80
CAR2: STATUS=PARKED ENGINE_TEMP=25.10
```

| Command | Description |
| --- | --- |
| `help` | Show available commands. |
| `pause-gw` / `resume-gw` | Pause or resume all connected gateways. |
| `scenario <name> [room=<ID>]` | Run a scenario (see below). |
| `control <device> <on/off>` | Manually toggle an alarm/sprinkler. |
| `stats` | Show connection and packet statistics. |
| `export csv` | Export the collected data to a CSV file. |
| `events` | List all logged events. |
| `exit` | Stop the server. |

---

## 🎬 Scenarios

| Scenario | Effect |
| --- | --- |
| `fire1` / `fire2` | Gradually raise smoke/CO₂/fire in Room 1 / Room 2 until alarm + sprinkler trigger. |
| `co2_high` | Raise CO₂ in a chosen room (`room=1200400` or `room=1211371`). |
| `car1` / `car2` | Start a vehicle, heat the engine, and drive it to OVERHEATING. |
| `normal` | Reset everything back to safe baseline values. |
| `test` | Run a short self-test sequence of status events. |

---

## 📁 Project Structure

```
Iot-Fire-Detection-Simulation/
├── gateway_plus.py          # Edge gateway: simulates sensors, streams data, auto-reconnects
├── cloud_server_plus.py     # Cloud server: ingest, safety logic, live dashboard, CLI, CSV export
├── requirements.txt
└── logs/
    └── data_stream.jsonl    # Sample recorded data stream
```

---

## 👥 Authors

Created by **Fatima Azazmah** and **Aya Hammad** for a Wireless and IoT course project.

If you find this useful, consider giving the repository a ⭐.
