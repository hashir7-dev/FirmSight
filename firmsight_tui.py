from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Tree, Log

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
        width: 40%;
        border: solid cyan;
    }
    #status-pane {
        width: 30%;
        border: solid yellow;
    }
    """

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
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        tree.root.expand()
        etc = tree.root.add("etc")
        etc.add_leaf("passwd")
        etc.add_leaf("shadow")
        bin_dir = tree.root.add("bin")
        bin_dir.add_leaf("busybox")
        bin_dir.add_leaf("httpd")

        log = self.query_one("#network-log", Log)
        log.write_line("[Week 1] Waiting for real emulation data...")

if __name__ == "__main__":
    app = FirmSightApp()
    app.run()
