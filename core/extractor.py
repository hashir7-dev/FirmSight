import os
import subprocess
import json

def extract_firmware(firmware_path, output_dir="extracted"):
    """
    Unpacks a firmware .bin file using binwalk.
    """
    if not os.path.exists(firmware_path):
        return {"status": "error", "message": f"File {firmware_path} not found"}

    os.makedirs(output_dir, exist_ok=True)
    
    # Run binwalk to extract filesystem structures
    cmd = ["binwalk", "--extract", "--matryoshka", f"--directory={output_dir}", firmware_path]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {
            "status": "success",
            "output_dir": output_dir,
            "log": result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = extract_firmware(sys.argv[1])
        print(json.dumps(res, indent=2))
    else:
        print("Usage: python extractor.py <path_to_firmware.bin>")
