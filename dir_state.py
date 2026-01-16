from pathlib import Path

#states the directory state and information about currrent working directory

class DirState:
    def __init__(self, path: Path | None = None):
        self.cwd: Path | None = path
        self.entries: list[Path] = []
        self.index: int = 0
        if path and path.exists():
            self.load(path)

    def load(self, path: Path):
        self.cwd = path
        self.entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        self.index = 0

    @property
    def selected(self) -> Path | None:
        if not self.entries:
            return None
        return self.entries[self.index]
