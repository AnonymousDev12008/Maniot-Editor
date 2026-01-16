from pathlib import Path
import shutil

def read_file(path: Path) -> tuple[bool, str]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return True, f.read()
    except Exception as e:
        return False, str(e)

def write_file(path: Path, content: str) -> tuple[bool, str]:
    try:
        with path.open("w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Written to {path.name}"
    except Exception as e:
        return False, str(e)

def append_file(path: Path, content: str) -> tuple[bool, str]:
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(content)
        return True, f"Appended to {path.name}"
    except Exception as e:
        return False, str(e)

def overwrite_file(path: Path, content: str) -> tuple[bool, str]:
    try:
        backup = path.with_suffix(path.suffix + ".bak")
        if path.exists():
            shutil.copy2(path, backup)
        with path.open("w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Overwritten {path.name} (backup: {backup.name if path.exists() else 'none'})"
    except Exception as e:
        return False, str(e)
