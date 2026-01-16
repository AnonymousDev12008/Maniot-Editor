# Maniot (Maniot-Editor)

Maniot is a lightweight, keyboard-centric Terminal User Interface (TUI) file manager and editor built with Python. It provides a split-pane environment to navigate directories, inspect file metadata, and edit text files—all without leaving your terminal.

# *Key Features* 

1 . Dual-Pane Interface: View your directory structure on the left and your editor/output on the right.

2 . Live Metadata Inspector: Instant display of file size, type, line count, and character count as you browse.

3 . Automatic Backup System: Security first! When you overwrite a file, Maniot automatically generates a ''.bak'' version to ensure you never lose work.

4 . Command-Line Control: A dedicated command input at the bottom for quick navigation and file operations.

5 . Pure Python: Highly portable and easy to customize for your own workflow.

# *Demo*

![Maniot Demo](demo.gif)

# *Installation* 

*1 .* *Clone the Repo* 

```Bash
git clone https://github.com/Anonymous/Maniot-Editor.git
cd Maniot-Editor
```

# *Setting Environment*

```bash
python -m venv .venv
```
*Windows*
```bash
.venv\Scripts\activate
```
*Mac/Linux*
```bash
source .venv/bin/activate
```

# *Installing Dependencies*

```bash
pip install -r requiremnts.txt
```

# *How to use*

## *Launch the Editor*
```bash
python main.py
```
## *Commands and Navigation*

### *Commands*

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

### *Keybindings*

Ctrl+s              → Save current file

Ctrl+Shift+s        → Save As

Ctrl+z              → Undo

Ctrl+y              → Redo

Alt+n               → New tab

Alt+w               → Close current tab

Alt+h / Alt+l       → Switch tab left/right

Alt+q               → Quit editor

## Notes 

- Arrow keys navigate the directory pane
- Enter opens files or enters directories
- Multi-line editing is enabled by default
- Existing files are never overwritten silently

# File - Structure

The project is divided into specialized modules to keep the logic clean and maintainable:

*tui_main.py* – The application entry point. It initializes the terminal interface, manages the main event loop, and coordinates between the UI and the backend.

*dir_render.py* – Responsible for the visual representation of the file system. It handles how directories and files are drawn in the left-hand pane.

*dir_state.py* – Manages the logic of directory navigation (e.g., tracking the current path, history, and expanding/collapsing folders).

*state.py* – The global state manager. It stores application-wide variables like the currently selected file, user configurations, and UI toggle states.

*file_ops.py* – The engine for file interactions. This handles reading, writing, and the automatic backup (.bak) logic.

# Development & Extension

Maniot is designed with a State-Action architecture. To add a new functionality , follow these steps:

## How to Add a New Command

*1.Update state.py:* Add any new variables needed to track the state of your feature.

*2.Modify file_ops.py:* Create the backend logic .

*3.Register in tui_main.py:* Add a new case to the command parser.

# Licence 

This project is Licenced under GNU Affero General Public License version 3 .


