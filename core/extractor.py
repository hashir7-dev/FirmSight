import os
import math
import subprocess


def calculate_entropy(file_path: str) -> float:
    """Calculates Shannon Entropy (0.0 to 8.0) to detect encryption/compression."""
    if not os.path.exists(file_path):
        return 0.0
    with open(file_path, "rb") as f:
        data = f.read()
    if not data:
        return 0.0
    entropy = 0.0
    for x in range(256):
        p_x = data.count(bytes([x])) / len(data)
        if p_x > 0:
            entropy -= p_x * math.log2(p_x)
    return round(entropy, 2)


def process_firmware_pipeline(file_path: str, action_mode: str = "auto") -> dict:
    """
    Entry point for FirmSight TUI processing pipeline.
    Supported modes: 'auto', 'decrypt', 'carve'
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File '{file_path}' not found."}

    entropy = calculate_entropy(file_path)

    # 1. High-Entropy / Encrypted Check
    if action_mode == "decrypt" or (action_mode == "auto" and entropy > 7.5):
        return {
            "status": "warning",
            "entropy": entropy,
            "message": f"High entropy ({entropy}/8.0). Firmware appears encrypted. Vendor decryption routine required.",
        }

    # 2. Partition Carving / Disk Image (.dd / FTK)
    if action_mode == "carve":
        os.makedirs("extracted", exist_ok=True)
        cmd = ["binwalk", "-e", "--directory=extracted", file_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {
            "status": "success",
            "entropy": entropy,
            "output_dir": "extracted",
            "message": "Disk image carved and partitions processed.",
        }

    # 3. Standard Binwalk Extraction (Auto)
    os.makedirs("extracted", exist_ok=True)
    cmd = ["binwalk", "-e", "--directory=extracted", file_path]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return {
        "status": "success",
        "entropy": entropy,
        "output_dir": "extracted",
        "message": "Firmware binary successfully unpacked.",
    }
