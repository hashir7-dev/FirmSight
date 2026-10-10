# FirmSight — IoT Firmware Emulation & Dynamic Analysis Sandbox

**Domain:** Reverse Engineering / IoT Security
**Status:** ✅ Weeks 1–4 Complete (Dynamic Analysis & UI track)

FirmSight is a security research tool that lets researchers safely analyze suspicious IoT firmware (routers, cameras, smart locks) by extracting and emulating it in a virtual sandbox — without needing the physical device. It automatically unpacks `.bin` firmware files, boots the extracted Linux filesystem inside QEMU (even for foreign architectures like ARM/MIPS), and displays live behavioral data — filesystem structure, network activity, and emulation status — in a terminal dashboard.

This repository contains the **Track 2 (Dynamic Analysis & UI)** component, built independently across all four project weeks.

---

## Project Architecture

| Track | Tools | Role |
|---|---|---|
| Extraction & Emulation | Python, Binwalk, QEMU, iptables, tcpdump | Unpacks firmware and boots it in an isolated virtual network |
| Dynamic Analysis & UI *(this repo)* | Python, Textual, r2pipe (Radare2) | Visualizes filesystem, network logs, and live process behavior |

---

## Honest Note on Scope

The Extraction & Emulation track (Binwalk/QEMU) was not completed by the team. Rather than block progress, this track's data sources were built against **realistic stand-ins**:

- `dummy_process` — a long-running local C program standing in for a real QEMU-emulated firmware process
- `mock_network.py` — a simulated network event generator standing in for real captured PCAP traffic, using RFC 5737 documentation-reserved IP ranges as "known-malicious" addresses (never real-world infrastructure)

The underlying techniques — `r2pipe` process attachment and live memory introspection, and heuristic-based malicious-traffic detection — are fully real and implemented exactly as they would be against genuine emulated firmware. Both stand-ins sit behind a single, narrow interface so real extraction/emulation output can be substituted later with no redesign of the detection or UI logic.

---

## Setup & Usage — All Weeks

### Step 1 — Python environment

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
python3 -m venv firmsight-env
source firmsight-env/bin/activate
python3 -m pip install --upgrade pip
pip install textual textual-dev r2pipe
```

### Step 2 — Install Radare2

```bash
sudo apt install -y radare2
```

Grant it process-attach permission without needing full `sudo` each run:
```bash
sudo setcap cap_sys_ptrace=eip $(which radare2)
```

### Step 3 — Build the stand-in target process

```bash
gcc -o dummy_process dummy_process.c
./dummy_process &
```

### Step 4 — Run the application

```bash
python3 firmsight_tui.py
```

---

## What Each Week Added

### Week 1 — TUI Scaffolding
Three-pane Textual layout: **Filesystem Tree**, **Network Logs**, **Emulation Status**. Verified working with placeholder data before any live integration.

### Week 2 — r2pipe Hooking
On startup, the app finds the target process and attaches via Radare2's debug backend (`dbg://<pid>`). A background worker thread polls `dm` (display memory maps) every 3 seconds and streams the result into the Emulation Status pane — without blocking the UI.

```python
r2 = r2pipe.open(f"dbg://{pid}")
dump = r2.cmd("dm")
```

### Week 3 — Behavioral Analysis
Every 1.5 seconds, a simulated outbound connection event is generated and checked against a small set of known-malicious IP addresses. Matches are flagged in the Network Logs pane in real time (`ALERT: ...`), with a running **Threats Detected** counter displayed above the log.

### Week 4 — Teardown & Polish
Pressing `q` (or closing the app) triggers a graceful teardown: the active Radare2 debug session is cleanly closed before exit, avoiding orphaned processes. This is the same hook where QEMU process termination and TUN/TAP interface cleanup will be added once Track 1 exists.

---

## Project Files

| File | Purpose |
|---|---|
| `firmsight_tui.py` | Main application — all four weeks' functionality |
| `mock_network.py` | Simulated network event generator (Week 3 stand-in) |
| `dummy_process.c` | Stand-in long-running process for r2pipe to attach to (Week 2 stand-in) |
| `requirements.txt` | Python dependencies |

---

## Requirements

```
python >= 3.10
textual
textual-dev
r2pipe
```

System dependency: `radare2` (installed via `apt`, not pip)

Install Python dependencies via:
```bash
pip install -r requirements.txt
```

---

## Roadmap

- [x] **Week 1** — TUI scaffolding with Filesystem Tree, Network Logs, and Emulation Status panes
- [x] **Week 2** — `r2pipe` hooked into a live process; memory maps streaming live to the UI
- [x] **Mid-Project Review** — UI displaying filesystem structure (stand-in data, pending real extraction)
- [x] **Week 3** — Real-time behavioral analysis with known-malicious IP alerting
- [x] **Week 4** — Graceful teardown on exit; full four-week integration tested end-to-end
- [ ] **Future** — Swap stand-in data sources for real Binwalk extraction and QEMU emulation output once Track 1 is built

---

## Project Context

Built as part of the Infotact Solutions Advanced Cybersecurity Engineering internship program.

## License

TBD
