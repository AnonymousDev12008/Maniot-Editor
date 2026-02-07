from pathlib import Path
from datetime import datetime

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.margins import ScrollbarMargin, NumberedMargin
from prompt_toolkit.widgets import Frame
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import has_focus, Condition
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import input_dialog

from file_ops import write_file, append_file, read_file
from dir_state import DirState
from dir_render import render_file_palette
from state import AppState

# ---------------- State ----------------
state = AppState()

# ---------------- Editor Tabs ----------------
editors = []
active_editor = 0
pending_overwrite = None

HELP_CONTENT = """\
Welcome to Maniot Editor!

--- Commands ---
:rename NAME        → Rename current tab
:NAME               → Jump to tab named NAME
u PATH              → Open directory PATH in file pane
a FILE              → Append editor content to FILE
w FILE              → Overwrite FILE (asks confirmation if file exists)
w! FILE             → Force overwrite FILE (no confirmation)
ow FILE             → Overwrite FILE and keep a backup (.bak)
mkdir PATH          → Create directory PATH
rm PATH             → Remove file or directory PATH
saveas FILE         → Save editor content as FILE

--- Keybindings ---
Ctrl+s              → Save current file
Ctrl+Shift+s        → Save As
Ctrl+z              → Undo
Ctrl+y              → Redo
Alt+n               → New tab
Alt+w               → Close current tab
Alt+h / Alt+l       → Switch tab left/right
Alt+q               → Quit editor
Tab / Shift+Tab     → Switch Between Panes

--- Notes ---
- Arrow keys navigate the directory pane
- Enter opens files or enters directories
- Multi-line editing is enabled by default
- Existing files are never overwritten silently
"""

def new_editor(name=None, show_help=True):
    buf = Buffer(
        multiline=True,    # allow multi-line editing
        read_only=False
    )
    tab_name = name or f"Untitled {len(editors)+1}"

    if show_help:
        buf.set_document(Document(HELP_CONTENT), bypass_readonly=True)

    editors.append({
        "buffer": buf,
        "file": None,
        "mode": "r",
        "dir": DirState(None),
        "name": tab_name
    })


def current_editor():
    return editors[active_editor]

new_editor()

# ---------------- Buffers ----------------
input_buffer = Buffer()
directory_buffer = Buffer(read_only=True)
metadata_buffer = Buffer(read_only=True)
status_buffer = Buffer(read_only=True)
message_buffer = Buffer(read_only=True)
header_buffer = Buffer(read_only=True)

# ---------------- Helpers ----------------
def set_ro(buf: Buffer, text: str):
    buf.set_document(Document(text), bypass_readonly=True)

def set_message(text: str):
    set_ro(message_buffer, text)

def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def render_tab_labels_windowed(window=2):
    total = len(editors)
    start = max(0, active_editor - window)
    end = min(total, active_editor + window + 1)

    labels = []
    if start > 0:
        labels.append("…")

    for i in range(start, end):
        name = editors[i]["name"]
        labels.append(f"[{name}]" if i == active_editor else name)

    if end < total:
        labels.append("…")

    return " | ".join(labels)

# ---------------- Frames ----------------
header = Frame(
    Window(height=1, content=BufferControl(buffer=header_buffer, focusable=False),
           style="bg:#161616 fg:#e6e6e6"),
    title="Maniot TUI Editor",
)

def editor_window():
    return Window(
        content=BufferControl(buffer=current_editor()["buffer"]),
        wrap_lines=True,
        left_margins=[NumberedMargin()],
        right_margins=[ScrollbarMargin(display_arrows=True)],
        style=Condition(
            lambda: "bg:#1f2933 fg:#e6e6e6"
            if has_focus(output_pane)()
            else "bg:#0f0f0f fg:#9aa0a6"
        ),
    )

output_pane = Frame(editor_window(), title="Editor")

input_pane = Frame(
    Window(height=1, content=BufferControl(buffer=input_buffer),
           style=Condition(
               lambda: "bg:#1f2933 fg:#e6e6e6"
               if has_focus(input_pane)()
               else "bg:#0f0f0f fg:#e6e6e6")),
    title="Command"
)

directory_pane = Frame(
    Window(content=BufferControl(buffer=directory_buffer),
           style=Condition(
               lambda: "bg:#1f2933 fg:#e6e6e6"
               if has_focus(directory_pane)()
               else "bg:#161616 fg:#9aa0a6")),
    title="Directory"
)

metadata_pane = Frame(
    Window(content=BufferControl(buffer=metadata_buffer, focusable=False),
           style="bg:#161616 fg:#9aa0a6"),
    title="Metadata"
)

message_pane = Frame(
    Window(height=1, content=BufferControl(buffer=message_buffer, focusable=False),
           style="bg:#0f0f0f fg:#c5c8c6"),
    title="Message"
)

status_pane = Frame(
    Window(height=1, content=BufferControl(buffer=status_buffer, focusable=False),
           style="bg:#161616 fg:#e6e6e6 bold"),
    title="Status"
)

# ---------------- Layout ----------------
body = VSplit([
    HSplit([directory_pane, metadata_pane], width=40),
    output_pane
])

root_container = HSplit([
    header,
    body,
    message_pane,
    status_pane,
    input_pane
])

kb = KeyBindings()

# ---------------- Refresh ----------------
def refresh_directory():
    d = current_editor()["dir"]

    if d.cwd:
        set_ro(directory_buffer, render_file_palette(d))
    else:
        set_ro(directory_buffer, "No directory loaded")

    if d.selected and d.selected.exists():
        s = d.selected.stat()

        if d.selected.is_file():
            try:
                text = d.selected.read_text(encoding="utf-8", errors="ignore")
                words = len(text.split())
                lines = text.count("\n") + 1 if text else 0
            except Exception:
                words = lines = 0

            file_type = d.selected.suffix or "No extension"
        else:
            words = lines = 0
            file_type = "Directory"

        meta = (
            f"Name: {d.selected.name}\n"
            f"Type: {file_type}\n"
            f"Words: {words}\n"
            f"Lines: {lines}\n"
            f"Created: {fmt_time(s.st_ctime)}\n"
            f"Modified: {fmt_time(s.st_mtime)}"
        )
        set_ro(metadata_buffer, meta)
    else:
        set_ro(metadata_buffer, "No file selected")

def refresh_status(msg=None):
    ed = current_editor()
    info = (
        f"Tab {active_editor+1}/{len(editors)} | "
        f"{render_tab_labels_windowed()} | "
        f"Mode: {ed['mode']} | File: {ed['file'] or 'None'}"
    )
    set_ro(status_buffer, msg if msg else info)

def refresh_editor():
    output_pane.body = editor_window()
    refresh_directory()
    refresh_status()

def refresh_current_dir():
    d = current_editor()["dir"]
    if not d.cwd:
        refresh_directory()
        return

    old_selected = d.selected
    d.load(d.cwd)  # authoritative reload from filesystem

    # Clamp index safely
    if not d.entries:
        d.index = 0
    else:
        d.index = min(d.index, len(d.entries) - 1)

    # If previously selected path vanished, clear selection
    if old_selected and (not old_selected.exists()):
        d.selected = None

    refresh_directory()

# ---------------- Editor Load ----------------
def load_to_editor(path: Path, mode="r"):
    ok, content = read_file(path)
    ed = current_editor()

    ed["file"] = path
    ed["mode"] = mode
    ed["buffer"].read_only = Condition(lambda: ed["mode"] == "r")

    # If file read successfully, replace buffer content (overwriting help content)
    if ok:
        ed["buffer"].set_document(Document(content or ""), bypass_readonly=True)

    set_message(f"Opened: {path.name}")
    refresh_editor()

# ---------------- Commands ----------------
def handle_command(text: str):
    global pending_overwrite, active_editor
    parts = text.strip().split(maxsplit=1)
    if not parts:
        return

    raw = parts[0]
    arg = parts[1] if len(parts) > 1 else None
    cmd = raw.lower()

    ed = current_editor()
    d = ed["dir"]

    # ---------- Help ----------
    if cmd == ":help":
        ed["buffer"].set_document(Document(HELP_CONTENT), bypass_readonly=True)
        ed["file"] = None
        ed["mode"] = "r"
        set_message("Help loaded")
        refresh_editor()
        return
    # ---------- Tab rename ----------
    if cmd == ":rename" and arg:
        ed["name"] = arg
        set_message(f"Tab renamed to {arg}")
        refresh_editor()
        return

    # ---------- Tab jump ----------
    if raw.startswith(":") and cmd != ":rename":
        name = raw[1:]
        for i, e in enumerate(editors):
            if e["name"] == name:
                global active_editor
                active_editor = i
                refresh_editor()
                return
        set_message(f"No tab named '{name}'")
        return

    # ---------- Load directory ----------
    if cmd == "u" and arg:
        global pt
        pt = Path(arg)
        if pt.exists() and pt.is_dir():
            d.load(pt)
            set_message(f"Loaded directory: {pt}")
            refresh_directory()
        else:
            set_message("Invalid directory")
        return

    
    
    # ---------- Tab jump ----------
    if raw.startswith(":") and cmd not in [":help", ":rename"]:
        name = raw[1:]
        for i, e in enumerate(editors):
            if e["name"] == name:
                
                active_editor = i
                refresh_editor()
                return
        set_message(f"No tab named '{name}'")
        return

    # ---------- Append to file ----------
    if cmd == "a" and arg:
        fpath = Path(arg)
        ok, msg = append_file(fpath, ed["buffer"].text)
        set_message(msg)
        refresh_status()
        refresh_current_dir()
        return

    
    #---------- Overwrite file ----------
    if cmd == "w" and arg:
        fpath = Path(arg)

        if fpath.exists():
            set_message(
                f"Refusing to overwrite existing file: '{fpath.name}'. "
                f"Use 'w!' to force or 'ow {fpath.name}' to keep backup."
            )
            return

        ok, msg = write_file(fpath, ed["buffer"].text)
        set_message(msg)
        refresh_status()
        refresh_current_dir()
        return


    #---------- Force overwrite ----------
    if cmd == "w!" and arg:
        fpath = Path(arg)

        ok, msg = write_file(fpath, ed["buffer"].text)
        set_message(f"{msg} (forced)")
        refresh_status()
        refresh_current_dir()
        return




    # ---------- Overwrite with backup ----------
    if cmd == "ow" and arg:
        fpath = Path(arg)

        if fpath.exists():
            backup = fpath.with_suffix(fpath.suffix + ".bak")
            if backup.exists():
                backup = backup.with_suffix(
                    backup.suffix + f".{int(datetime.now().timestamp())}"
                )
            fpath.rename(backup)
        else:
            backup = None

        ok, msg = write_file(fpath, ed["buffer"].text)
        set_message(
            f"{msg} (backup: {backup.name if backup else 'none'})"
        )
        refresh_status()
        refresh_current_dir()
        return


    # ---------- Make directory ----------
    if cmd == "mkdir" and arg:
        p = Path(arg)
        try:
            p.mkdir(parents=True, exist_ok=False)
            set_message(f"Directory created: {p}")
        except FileExistsError:
            set_message(f"Directory already exists: {p}")
        except Exception as e:
            set_message(f"Error creating directory: {e}")
        refresh_current_dir()
        return

    # ---------- Remove file or directory ----------
    if cmd == "rm" and arg:
        p = Path(arg)
        if not p.exists():
            set_message(f"Path does not exist: {p}")
        else:
            try:
                if p.is_dir():
                    import shutil, os, stat
                    def remove_readonly(func, path, excinfo):
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    shutil.rmtree(p, onerror=remove_readonly)
                else:
                    p.unlink()
                set_message(f"Removed: {p}")
            except Exception as e:
                set_message(f"Error removing: {e}")
        refresh_current_dir()
        return

    # ---------- Save As ----------
    if cmd == "saveas" and arg:
        fpath = Path(arg)
        ok, msg = write_file(fpath, ed["buffer"].text)
        if ok:
            ed["file"] = fpath
            ed["mode"] = "w"
        set_message(msg)
        refresh_status()
        refresh_current_dir()
        return

# ---------------- Keybindings ----------------
@kb.add("tab")
def _(e): e.app.layout.focus_next()

@kb.add("s-tab")
def _(e): e.app.layout.focus_previous()

@kb.add("enter", filter=has_focus(input_pane) | has_focus(directory_pane))
def _(e):
    if has_focus(input_pane)():
        handle_command(input_buffer.text)
        input_buffer.text = ""
        return
    if has_focus(directory_pane)():
        d = current_editor()["dir"]
        if not d.selected:
            return
        if d.selected.is_dir():
            d.load(d.selected)
            set_message(f"Entered: {d.selected}")
            refresh_directory()
        else:
            load_to_editor(d.selected, "r")
        return

@kb.add("up", filter=has_focus(directory_pane))
def _(e):
    d = current_editor()["dir"]
    d.index = max(0, d.index - 1)
    refresh_directory()

@kb.add("down", filter=has_focus(directory_pane))
def _(e):
    d = current_editor()["dir"]
    d.index = min(len(d.entries)-1, d.index + 1)
    refresh_directory()

@kb.add("backspace", filter=has_focus(directory_pane))
def _(e):
    d = current_editor()["dir"]
    if d.cwd == pt :
        set_message("Can't access direcory outside initial directory loaded !")
        return
    if d.cwd:
        d.load(d.cwd.parent)
        refresh_directory()

@kb.add("a", filter=has_focus(directory_pane))
def _(e):
    d = current_editor()["dir"]
    if d.selected and d.selected.is_file():
        load_to_editor(d.selected, "a")

@kb.add("w", filter=has_focus(directory_pane))
def _(e):
    d = current_editor()["dir"]
    if d.selected and d.selected.is_file():
        load_to_editor(d.selected, "w")

@kb.add("o", filter=has_focus(directory_pane))
def _(e):
    d = current_editor()["dir"]
    if d.selected and d.selected.is_file():
        load_to_editor(d.selected, "ow")

@kb.add("escape", "n")
def _(e):
    global active_editor
    new_editor()
    active_editor = len(editors) - 1
    refresh_editor()

@kb.add("escape", "l")
def _(e):
    global active_editor
    active_editor = (active_editor + 1) % len(editors)
    refresh_editor()

@kb.add("escape", "h")
def _(e):
    global active_editor
    active_editor = (active_editor - 1) % len(editors)
    refresh_editor()

@kb.add("escape", "w")
def _(e):
    global active_editor
    if len(editors) > 1:
        editors.pop(active_editor)
        active_editor = max(0, active_editor - 1)
        refresh_editor()

@kb.add("escape", "q")
def _(e):
    e.app.exit()

# ---------------- Save / Save As ----------------
@kb.add("c-s")  # Ctrl+s
def _(e):
    ed = current_editor()
    d=current_editor()["dir"]
    path = ed["file"]
    if not path:
        set_message("No file loaded in current tab")
        return
    content = ed["buffer"].text
    ok, msg = write_file(path, content)
    set_message(msg)
    refresh_status()
    refresh_directory()
    load_to_editor(d.selected, "r")
    e.app.layout.focus_previous()
    

@kb.add("escape", "s")  # Save As
def _(e):
    ed = current_editor()

    result = input_dialog(
        title="Save As",
        text="Enter file path:"
    ).run()

    if not result:
        return

    fpath = Path(result)
    ok, msg = write_file(fpath, ed["buffer"].text)

    if ok:
        ed["file"] = fpath
        ed["mode"] = "w"

    set_message(msg)
    refresh_status()
    refresh_current_dir()





# ---------------- Undo / Redo ----------------
@kb.add("c-z")  # Ctrl+Z
def _(e):
    buf = current_editor()["buffer"]
    if buf.undo_stack:
        buf.undo()
    else:
        set_message("Nothing to undo")


@kb.add("c-y")  # Ctrl+Y
def _(e):
    buf = current_editor()["buffer"]
    if buf.undo_stack and buf.undo_stack.can_redo:
        buf.redo()
    else:
        set_message("Nothing to redo")


# ---------------- App ----------------
app = Application(
    layout=Layout(root_container, focused_element=input_pane),
    key_bindings=kb,
    full_screen=True,
    style=Style.from_dict({
        "frame.border": "fg:#3b4252",
        "frame.border.focused": "fg:#3b4252 bold",
        "frame.label": "bold fg:#e6e6e6",
    })
)

set_ro(
    header_buffer,
    "Ctrl+s save | Ctrl+Z undo | Ctrl+Y redo | Alt+n new tab | Alt+h/l switch | Alt+w close tab | Alt+q quit"
)

refresh_editor()

if __name__ == "__main__":
    app.run()

