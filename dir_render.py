from pathlib import Path
from dir_state import DirState

def render_file_palette(ds: "DirState") -> str:
    if not ds.entries:
        return "No directory loaded"
    lines = []
    for i, p in enumerate(ds.entries):
        name = p.name + ("/" if p.is_dir() else "")
        lines.append(f"▶ {name}" if i == ds.index else f"  {name}")
    return "\n".join(lines)

def render_metadata(path: Path | None) -> str:
    if not path or not path.exists():
        return "No file selected"
    try:
        stat = path.stat()
        lines = [
            f"Name: {path.name}",
            f"Type: {'Directory' if path.is_dir() else 'File'}",
            f"Size: {stat.st_size} bytes",
            f"Last Modified: {stat.st_mtime:.0f}",
        ]
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as f:
                    content = f.read()
                lines.append(f"Lines: {content.count(chr(10)) + 1 if content else 0}")
                lines.append(f"Characters: {len(content)}")
            except Exception:
                pass
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"
