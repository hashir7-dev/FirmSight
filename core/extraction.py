import os
import math
import subprocess

def calculate_entropy(file_path):
    """Returns entropy score (0.0 to 8.0) to detect encryption."""
    with open(file_path, "rb") as f:
        data = f.read()
    if not data:
        return 0.0
    entropy = 0
    for x in range(256):
        p_x = data.count(bytes([x])) / len(data)
        if p_x > 0:
            entropy -= p_x * math.log2(p_x)
    return round(entropy, 2)

def process_firmware_pipeline(file_path, action_mode="auto"):
    """
    Acts as the entry point for the TUI file processor.
    Modes: 'auto', 'binwalk', 'decrypt', 'dd_carve'
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found"}

    entropy = calculate_entropy(file_path)
    
    # 1. Handle Encrypted Files
    if action_mode == "decrypt" or (action_mode == "auto" and entropy > 7.5):
        return {
            "status": "warning",
            "action_required": "decryption_needed",
            "entropy": entropy,
            "message": f"High entropy ({entropy}). File appears encrypted. Please select vendor decryption routine."
        }

    # 2. Standard Binwalk Extraction
    if action_mode in ["auto", "binwalk"]:
        cmd = ["binwalk", "-e", "--directory=extracted", file_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {
            "status": "success",
            "entropy": entropy,
            "output_dir": "extracted",
            "message": "Filesystem successfully extracted."
        }

