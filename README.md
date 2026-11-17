# Desktop Tasks

A lightweight Windows checklist built with Python and Tkinter. It keeps task rows, checkbox columns, notes, and optional file, Comet, and Chrome shortcuts in a small always-on-top window.

## Requirements

- Windows
- Python 3 with Tkinter (included with most standard Python for Windows installations)
- Optional: AutoHotkey v2 and Perplexity Comet for their respective shortcuts

## Run

Open a terminal in this folder and run:

```powershell
python .\DesktopTasks.pyw
```

You can also open `DesktopTasks.pyw` directly if `.pyw` files are associated with Python on your system.

## Using the checklist

- Click a checkbox to mark it complete or incomplete.
- Right-click a checkbox to add another checkbox to that cell or remove one (a cell keeps at least one).
- Click a row's note icon to show or hide its note. Use the `A−` and `A+` controls in the note to adjust its text size.
- Click the gear button to open settings:
  - **＋ ROW / ＋ COL** adds a task row or checkbox column.
  - **A− / A+** changes the general text size.
  - **UNTICK** clears every checkbox.
  - **EDIT: ON** shows row drag handles and delete controls. Drag the `⋮⋮` handle to reorder a complete row, including its checkbox states and shortcuts.
  - **TEXT / SHORTCUT / COMET / CHROME** toggles the corresponding row icons.
  - **Transparency** adjusts the window opacity.
  - **TITLE SHORTCUTS** shows or hides the shortcut buttons beside the item heading.
- Drag the title bar to move the window. Drag the bottom-right corner to resize it. Drag the divider between the item list and checkbox columns to resize the item section.
- Hover over a shortcut icon to see its assigned file name or browser profile. Click a row icon to open its configured target.
- Right-click a row's file, Comet, or Chrome icon to open its target or choose/change its file or browser profile. Right-click a header shortcut icon to open its assigned file or choose/change it.

## Data and settings

Task rows, checkbox columns, notes, shortcut assignments, window position and size, and display settings are saved to `tasks.json` beside the application. Back up this file to preserve your data or move it to another copy of the project.

## Optional integrations

### AutoHotkey

File shortcuts accept any file type and open using its Windows default application. `.ahk` files run through AutoHotkey v2, which the application currently looks for at:

```text
C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe
```

If it is installed elsewhere, update `AUTOHOTKEY_EXE_PATH` near the top of `DesktopTasks.pyw`.

### Perplexity Comet

Install Comet and configure a row's Comet profile from the row shortcut menu. The application currently expects Comet at:

```text
C:\Program Files\Perplexity\Comet\Application\Comet.exe
```

If Comet is installed elsewhere, update `COMET_EXE_PATH` near the top of `DesktopTasks.pyw`. The profile list is read from Comet's user data under the current Windows user's local application data directory.

### Google Chrome

Install Google Chrome and configure a row's Chrome profile from the row shortcut menu. Profiles are read from Chrome's user data under the current Windows user's local application data directory. Chrome is searched for in the standard Program Files and per-user installation locations.
