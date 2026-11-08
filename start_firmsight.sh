#!/bin/bash
# start_firmsight.sh
# One-command restart for FirmSight after a VM reboot/logout.
# Run this from your project folder: ./start_firmsight.sh

set -e

echo "=== FirmSight startup ==="

# 1. Activate the Python virtual environment
if [ ! -d "firmsight-env" ]; then
    echo "ERROR: firmsight-env not found in this folder. Run this script from ~/project2."
    exit 1
fi
source firmsight-env/bin/activate
echo "[OK] Virtual environment activated."

# 2. Confirm Radare2 still has its process-attach permission (survives reboot,
# but re-grant it just in case radare2 was updated/reinstalled)
if ! getcap "$(which radare2)" | grep -q cap_sys_ptrace; then
    echo "[FIX] Re-granting radare2 ptrace permission..."
    sudo setcap cap_sys_ptrace=eip "$(which radare2)"
fi
echo "[OK] radare2 permission confirmed."

# 3. Start the stand-in target process if it's not already running
if ! pgrep -x dummy_process > /dev/null; then
    echo "[START] Launching dummy_process..."
    ./dummy_process &
    sleep 1
else
    echo "[OK] dummy_process already running."
fi

# 4. Launch the app
echo "[START] Launching FirmSight..."
python3 firmsight_tui.py
