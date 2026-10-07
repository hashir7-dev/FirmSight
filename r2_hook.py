import r2pipe
import subprocess

def get_dummy_pid():
    result = subprocess.run(["pgrep", "-n", "dummy_process"], capture_output=True, text=True)
    return result.stdout.strip()

pid = get_dummy_pid()
if not pid:
    print("dummy_process not running — start it first with ./dummy_process &")
    exit(1)

print(f"Attaching to PID {pid}...")

r2 = r2pipe.open(f"dbg://{pid}")

memory_maps = r2.cmd("dm")
print("=== Active Memory Maps ===")
print(memory_maps)

r2.quit()
