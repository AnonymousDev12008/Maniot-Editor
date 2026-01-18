from pathlib import Path

class AppState:
    def __init__(self):
        self.current_file: Path | None = None
        self.mode: str = "idle"
        self.message: str = "Press 'u' to load a directory | Tab to switch panes | q to quit"
        self.buffer: str = ""

       