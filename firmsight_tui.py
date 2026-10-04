import os
import math
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Static, Tree, Log, Button, Input, RadioSet, RadioButton
from textual.screen import ModalScreen
from core.extractor import process_firmware_pipeline


class FileUploadModal(ModalScreen):
    """iLovePDF-style Processing Modal for FirmSight."""

    CSS = """
    FileUploadModal {
        align: center middle;
    }

    #dialog {
        padding: 1 2;
        width: 65;
        height: 24;
        border: thick $accent;
        background: $surface;
    }

    .modal-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #file-input {
        margin-bottom: 1;
    }

    #action-modes {
        margin-bottom: 1;
    }

    #button-grid {
        grid-size: 2;
        grid-gutter: 1;
    }

    #entropy-label {
        color: $warning;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("📥 FIRMWARE INGESTION & CONVERSION", classes="modal-title")
            yield Input(placeholder="Enter file path (e.g. sample_firmware.bin)...", id="file-input")
            yield Static("Entropy Score: -- (Pending file check)", id="entropy-label")
            yield Static("Select Processing Action:", classes="pane-title")
            with RadioSet(id="action-modes"):
                yield RadioButton("Auto-Detect & Extract (binwalk)", id="mode_auto", value=True)
                yield RadioButton("Vendor Decryption Routine (High Entropy)", id="mode_decrypt")
                yield RadioButton("Partition Carver (.dd / FTK Image)", id="mode_carve")
            with Grid(id="button-grid"):
                yield Button("⚡ RUN PIPELINE", variant="primary", id="btn-run")
                yield Button("Cancel", variant="error", id="btn-cancel")

    def on_input_changed(self, event: Input.Changed) -> None:
        file_path = event.value.strip()
        label = self.query_one("#entropy-label", Static)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as f:
                    data = f.read()
                if data:
                    entropy = 0
                    for x in range(256):
                        p_x = data.count(bytes([x])) / len(data)
                        if p_x > 0:
                            entropy -= p_x * math.log2(p_x)
                    entropy = round(entropy, 2)
                    status_text = f"Entropy Score: {entropy}/8.0 "
                    if entropy > 7.5:
                        status_text += "[HIGH - Likely Encrypted]"
                    else:
                        status_text += "[NORMAL - Plain Data/FS]"
                    label.update(status_text)
            except Exception:
                label.update("Entropy Score: Error reading file")
        else:
            label.update("Entropy Score: -- (File not found)")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run":
            file_path = self.query_one("#file-input", Input).value.strip()
            radios = self.query_one("#action-modes", RadioSet)
            selected_mode = "auto"
            if radios.pressed_button:
                if radios.pressed_button.id == "mode_decrypt":
                    selected_mode = "decrypt"
                elif radios.pressed_button.id == "mode_carve":
                    selected_mode = "carve"

            self.dismiss({"file_path": file_path, "mode": selected_mode})
        elif event.button.id == "btn-cancel":
            self.dismiss(None)


class FirmSightApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #top-bar {
        height: 3;
        padding: 0 1;
        background: $boost;
    }
    #main {
        height: 1fr;
    }
    #filesystem-pane {
        width: 30%;
        border: solid green;
    }
    #network-pane {
        width: 40%;
        border: solid cyan;
    }
    #status-pane {
        width: 30%;
        border: solid yellow;
    }
    .pane-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #btn-upload {
        width: 100%;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with Vertical(id="filesystem-pane"):
                yield Button("📁 PROCESS / CONVERT FILE", variant="success", id="btn-upload")
                yield Static("FILESYSTEM TREE", classes="pane-title")
                yield Tree("firmware_root")
            with Vertical(id="network-pane"):
                yield Static("NETWORK LOGS", classes="pane-title")
                yield Log(id="network-log")
            with Vertical(id="status-pane"):
                yield Static("EMULATION STATUS", classes="pane-title")
                yield Static("Status: Idle", id="status-text")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-upload":
            self.push_screen(FileUploadModal(), self.handle_pipeline_result)

    def handle_pipeline_result(self, result: dict | None) -> None:
        if not result or not result.get("file_path"):
            return

        file_path = result["file_path"]
        mode = result["mode"]

        log = self.query_one("#network-log", Log)
        status = self.query_one("#status-text", Static)

        log.write_line(f"[Pipeline] Ingesting target: {file_path} (Mode: {mode})")
        status.update(f"Status: Processing {os.path.basename(file_path)}...")

        # Invoke core/extractor backend
        try:
            res = process_firmware_pipeline(file_path, action_mode=mode)
            if res.get("status") == "success":
                log.write_line(f"[Extractor] {res.get('message')}")
                status.update("Status: Extracted & Ready")
                self.populate_tree("extracted")
            elif res.get("status") == "warning":
                log.write_line(f"[WARNING] {res.get('message')}")
                status.update("Status: Action Required (Encrypted)")
            else:
                log.write_line(f"[ERROR] {res.get('message')}")
                status.update("Status: Extraction Failed")
        except Exception as e:
            log.write_line(f"[ERROR] Failed to execute pipeline: {str(e)}")
            status.update("Status: Error")

    def populate_tree(self, root_dir: str) -> None:
        tree = self.query_one(Tree)
        tree.root.clear()
        tree.root.label = root_dir

        if not os.path.exists(root_dir):
            return

        def add_node(path, parent_node):
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        child = parent_node.add(item, expand=False)
                        add_node(item_path, child)
                    else:
                        parent_node.add_leaf(item)
            except PermissionError:
                pass

        add_node(root_dir, tree.root)
        tree.root.expand()

    def on_mount(self) -> None:
        log = self.query_one("#network-log", Log)
        log.write_line("[System] FirmSight TUI active. Click 'PROCESS / CONVERT FILE' to begin.")


if __name__ == "__main__":
    app = FirmSightApp()
    app.run()
