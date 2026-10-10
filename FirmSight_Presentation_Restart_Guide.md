# FirmSight — Presentation Day Restart Guide

Follow these steps in order, every time you power on your Ubuntu VM before presenting. Unlike CAN-Sentinel, FirmSight doesn't need a virtual network interface recreated — your Python environment, compiled programs, and permissions all persist across reboots since they're just files on disk. So this restart is shorter and simpler.

---

## Step 1 — Open a terminal and go to your project folder

```bash
cd ~/project2
```

**What this does:** moves you into the folder containing all your FirmSight files (`firmsight_tui.py`, `mock_network.py`, `dummy_process`, your virtual environment folder, etc.) so every command after this works correctly.

---

## Step 2 — Activate your Python virtual environment

```bash
source firmsight-env/bin/activate
```

**What this does:** switches your terminal to use the isolated Python environment where `textual`, `r2pipe`, and their dependencies are installed — separate from the system's default Python. Your prompt should change to show `(firmsight-env)` at the start, confirming it worked.

---

## Step 3 — Confirm Radare2 still has its process-attach permission

```bash
getcap $(which radare2)
```

**What this does:** checks that Radare2 still has the special `cap_sys_ptrace` permission you granted it earlier — this is what lets it attach to another running process without needing full `sudo`. This permission is stored on the binary file itself, so it survives reboots, but it's worth a 2-second check before you're in front of reviewers.

**Expected output:** something like `/usr/bin/radare2 cap_sys_ptrace=eip`

**If nothing prints** (permission was lost, e.g., radare2 got reinstalled/updated), re-grant it:
```bash
sudo setcap cap_sys_ptrace=eip $(which radare2)
```

---

## Step 4 — Start the stand-in target process

```bash
./dummy_process &
```

**What this does:** launches your compiled C program in the background. This is the process that stands in for a real QEMU-emulated firmware process — `r2pipe` will attach to this and read its live memory maps. The `&` at the end means "run this in the background" so your terminal is free for the next command.

**Confirm it's running:**
```bash
pgrep -a dummy_process
```
You should see a line with its process ID and the command — if nothing shows, the process didn't start; just run `./dummy_process &` again.

---

## Step 5 — Run the FirmSight application

```bash
python3 firmsight_tui.py
```

**What this does:** launches the actual Textual terminal UI. On startup, it:
- Finds `dummy_process`'s PID and attaches Radare2 to it via `r2pipe`
- Starts a timer refreshing the memory map display every 3 seconds
- Starts a second timer generating simulated network events every 1.5 seconds, checking each one against a known-malicious IP list

You should see all three panes come alive: **Filesystem Tree** (static placeholder data), **Network Logs** (scrolling with OK/ALERT lines), and **Emulation Status** (showing "Attached to PID ..." with live memory maps).

---

## Quick Reference — All 5 Commands in Order

```bash
cd ~/project2
source firmsight-env/bin/activate
getcap $(which radare2)
./dummy_process &
python3 firmsight_tui.py
```

---

## During the Presentation

- **Let it run for 15-20 seconds** before explaining anything, so reviewers can see real scrolling data, not a static screen.
- **Point out the "Threats Detected" counter** increasing — that's your heuristic detection working live.
- **Press `q` to quit cleanly** at the end of your demo, and mention that this triggers your Week 4 graceful teardown (the Radare2 session closes cleanly instead of being left dangling).

---

## If Something Breaks Live

**"Attach failed" or status shows `dummy_process not running`:**
→ You skipped Step 4, or the process died. Press `Ctrl+C` to exit the app, run `./dummy_process &` again, then `python3 firmsight_tui.py` again.

**`ModuleNotFoundError` for `textual` or `r2pipe`:**
→ Your venv isn't activated. Check your prompt shows `(firmsight-env)`; if not, re-run Step 2.

**App crashes with a `UnicodeDecodeError` after clicking inside the terminal:**
→ This was the known mouse-click issue from earlier — the app already has `mouse=False` set to prevent this, but if it still happens, avoid clicking inside the terminal window during the demo; use only the keyboard.
