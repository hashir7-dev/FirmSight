import subprocess
import r2pipe
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Tree, Log

REFRESH_INTERVAL_SECONDS = 3
TARGET_PROCESS_NAME = "dummy_process"  # swap this for the real emulated process later


class FirmSightApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #main {
        height: 1fr;
    }
    #filesystem-pane {
        width: 30%;
        border: solid green;
    }
    #network-pane {
        width: 35%;
        border: solid cyan;
    }
    #status-pane {
        width: 35%;
        border: solid yellow;
    }
    """

    def __init__(self):
        super().__init__()
        self.r2 = None
        self.attached_pid = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with Vertical(id="filesystem-pane"):
                yield Static("FILESYSTEM TREE", classes="pane-title")
                yield Tree("firmware_root")
            with Vertical(id="network-pane"):
                yield Static("NETWORK LOGS", classes="pane-title")
                yield Log(id="network-log")
            with Vertical(id="status-pane"):
                yield Static("EMULATION STATUS", classes="pane-title")
                yield Static("Status: Idle", id="status-text")
                yield Log(id="memmap-log")
        yield Footer()

    def on_mount(self) -> None:
        # --- Filesystem tree placeholder (Week 1) ---
        tree = self.query_one(Tree)
        tree.root.expand()
        etc = tree.root.add("etc")
        etc.add_leaf("passwd")
        etc.add_leaf("shadow")
        bin_dir = tree.root.add("bin")
        bin_dir.add_leaf("busybox")
        bin_dir.add_leaf("httpd")

        net_log = self.query_one("#network-log", Log)
        net_log.write_line("[Week 1] Waiting for real emulation data...")

        # --- Week 2: attach to the target process and start live polling ---
        mem_log = self.query_one("#memmap-log", Log)
        status = self.query_one("#status-text", Static)

        pid = self._find_pid(TARGET_PROCESS_NAME)
        if not pid:
            status.update(f"Status: [red]{TARGET_PROCESS_NAME} not running[/red]")
            mem_log.write_line(f"Start it first: ./{TARGET_PROCESS_NAME} &")
            return

        try:
            self.r2 = r2pipe.open(f"dbg://{pid}")
            self.attached_pid = pid
            status.update(f"Status: [green]Attached to PID {pid}[/green]")
            mem_log.write_line(f"Attached to PID {pid}. Refreshing every {REFRESH_INTERVAL_SECONDS}s...")
        except Exception as e:
            status.update("Status: [red]Attach failed[/red]")
            mem_log.write_line(f"Error attaching: {e}")
            return

        # Poll on a timer; run the actual r2 call in a worker thread so it
        # never blocks the UI event loop.
        self.set_interval(REFRESH_INTERVAL_SECONDS, self.refresh_memory_maps)

    @staticmethod
    def _find_pid(process_name: str) -> str:
        result = subprocess.run(["pgrep", "-n", process_name], capture_output=True, text=True)
        return result.stdout.strip()

    def refresh_memory_maps(self) -> None:
        self.run_worker(self._fetch_and_display, thread=True, exclusive=True)

    def _fetch_and_display(self) -> None:
        if not self.r2:
            return
        try:
            dump = self.r2.cmd("dm")
        except Exception as e:
            dump = f"[error reading memory maps: {e}]"

        # Hand the result back to the UI thread safely via call_from_thread
        self.call_from_thread(self._update_memmap_pane, dump)

    def _update_memmap_pane(self, dump: str) -> None:
        mem_log = self.query_one("#memmap-log", Log)
        mem_log.clear()
        mem_log.write_line(f"=== Memory Maps (PID {self.attached_pid}, live) ===")
        for line in dump.strip().splitlines():
            mem_log.write_line(line)

    def on_unmount(self) -> None:
        if self.r2:
            self.r2.quit()


if __name__ == "__main__":
    app = FirmSightApp()
    # mouse=False avoids a known crash in some terminal emulators (including
    # VMware's built-in terminal) where a mouse click sends a raw escape
    # sequence that isn't valid UTF-8, crashing Textual's input reader.
    app.run(mouse=False)
