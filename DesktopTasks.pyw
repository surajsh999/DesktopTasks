import json
import os
import subprocess
import ctypes
from ctypes import wintypes
from tkinter import Tk, Frame, Label, Text, Entry, StringVar, Button, Scale, Menu, Toplevel, BOTH, LEFT, RIGHT, X, Y, W, E, HORIZONTAL, filedialog, ttk
from tkinter import messagebox

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
AUTOHOTKEY_EXE_PATH = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"
LEGACY_AHK_PATH = r"C:\Users\Scout Better\Desktop\Onik.ahk"
COMET_EXE_PATH = r"C:\Program Files\Perplexity\Comet\Application\Comet.exe"
COMET_USER_DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")),
    "Perplexity", "Comet", "User Data"
)
CHROME_USER_DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")),
    "Google", "Chrome", "User Data"
)
CHROME_EXE_PATHS = (
    os.path.join(
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        "Google", "Chrome", "Application", "chrome.exe"
    ),
    os.path.join(
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        "Google", "Chrome", "Application", "chrome.exe"
    ),
    os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")),
        "Google", "Chrome", "Application", "chrome.exe"
    ),
)
LEGACY_COMET_PROFILE = "Profile 34"

BG = "#0b0f14"
PANEL = "#111827"
CARD = "#151b26"
NEON = "#22d3ee"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
DANGER = "#fb7185"

font_size = 10
TICK_SIZE = 13
window_opacity = 0.95
edit_mode = False
dragged_row = None
drag_order_changed = False
ITEM_SECTION_MIN_NAME_WIDTH = 48
ITEM_SECTION_DIVIDER_WIDTH = 6


def default_settings():
    return {
        "width": 820,
        "height": 480,
        "x": 100,
        "y": 60,
        "item_width": 220,
        "font_size": 10,
        "opacity": 0.95,
        "show_note_icon": True,
        "show_shortcut_icon": True,
        "show_comet_icon": True,
        "show_chrome_icon": True,
        "header_ahk_paths": ["", "", ""],
        "one_click_ahk": True,
        "show_title_shortcuts": True
    }


def default_data():
    return {
        "settings": default_settings(),
        "columns": ["Name 1", "Name 2"],
        "rows": [
            {"item": "Item 1", "ticks": [False, False]},
            {"item": "Item 2", "ticks": [False, False]}
        ]
    }


def normalize_settings(value):
    settings = {**default_settings(), **value}
    settings["width"] = max(1, int(settings["width"]))
    settings["height"] = max(1, int(settings["height"]))
    settings["item_width"] = max(
        ITEM_SECTION_MIN_NAME_WIDTH,
        int(settings["item_width"])
    )
    settings["opacity"] = max(0.35, min(1.0, float(settings["opacity"])))
    for key in (
        "show_note_icon", "show_shortcut_icon", "show_comet_icon",
        "show_chrome_icon"
    ):
        settings[key] = bool(settings[key])
    paths = settings["header_ahk_paths"]
    if not isinstance(paths, (list, tuple)):
        paths = []
    settings["header_ahk_paths"] = [
        path.strip() if isinstance(path, str) else ""
        for path in list(paths[:3]) + [""] * (3 - len(paths[:3]))
    ]
    settings["one_click_ahk"] = bool(settings["one_click_ahk"])
    settings["show_title_shortcuts"] = bool(settings["show_title_shortcuts"])
    return settings


def current_window_geometry():
    width = root.winfo_width()
    height = root.winfo_height()
    x = root.winfo_x()
    y = root.winfo_y()
    if width <= 1:
        width = settings["width"]
        x = settings["x"]
    if height <= 1:
        height = settings["height"]
        y = settings["y"]
    return {"width": width, "height": height, "x": x, "y": y}


def load_data():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if "columns" in data and "rows" in data:
                    merged = {
                        "settings": normalize_settings(data.get("settings", {})),
                        "columns": data["columns"],
                        "rows": data["rows"]
                    }
                    return merged
                if "tasks" in data and isinstance(data["tasks"], dict):
                    tasks = data["tasks"]
                    if "columns" in tasks and "rows" in tasks:
                        return {
                            "settings": normalize_settings(data.get("settings", {})),
                            "columns": tasks["columns"],
                            "rows": tasks["rows"]
                        }
        except Exception:
            pass
    return default_data()


def save_data():
    geometry = current_window_geometry()
    data = {
        "settings": {
            **geometry,
            "font_size": font_size,
            "item_width": item_section_width,
            "opacity": window_opacity,
            **icon_visibility,
            "header_ahk_paths": header_ahk_paths,
            "one_click_ahk": one_click_ahk,
            "show_title_shortcuts": show_title_shortcuts,
        },
        "columns": [c.get("1.0", "end-1c") for c in column_boxes],
        "rows": []
    }
    for row in row_widgets:
        data["rows"].append({
            "item": row["item"].get("1.0", "end-1c"),
            "note": row["note"].get("1.0", "end-1c"),
            "note_font_size": row["note_font_size"],
            "ahk_path": row["launch_settings"]["ahk_path"],
            "comet_profile": row["launch_settings"]["comet_profile"],
            "chrome_profile": row["launch_settings"]["chrome_profile"],
            "ticks": [
                [tick["text"] == "☑" for tick in cell]
                for cell in row["ticks"]
            ]
        })
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_settings():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if "settings" in data and isinstance(data["settings"], dict):
                    return normalize_settings(data["settings"])
                if "columns" in data and "rows" in data:
                    return default_settings()
        except Exception:
            pass
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return normalize_settings(json.load(f))
        except Exception:
            pass
    return default_settings()


def save_settings():
    geometry = current_window_geometry()
    existing = {}
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    if not isinstance(existing, dict):
        existing = {}

    settings = {
        **geometry,
        "font_size": font_size,
        "item_width": item_section_width,
        "opacity": window_opacity,
        **icon_visibility,
        "header_ahk_paths": header_ahk_paths,
        "one_click_ahk": one_click_ahk,
        "show_title_shortcuts": show_title_shortcuts,
    }

    if "columns" in existing and "rows" in existing:
        data = {
            "settings": settings,
            "columns": existing["columns"],
            "rows": existing["rows"]
        }
    elif "tasks" in existing and isinstance(existing["tasks"], dict):
        tasks = existing["tasks"]
        data = {
            "settings": settings,
            "tasks": tasks
        }
    else:
        data = {
            "settings": settings,
            "columns": [],
            "rows": []
        }

    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def close_app():
    try:
        save_data()
        save_settings()
    except (OSError, TypeError, ValueError) as error:
        messagebox.showerror("Could not save tasks", str(error), parent=root)
        return
    root.destroy()

def editor(parent, value="", width=14, bold=False, height=1, wrap="char"):
    box = Text(
        parent,
        height=height,
        width=width,
        wrap=wrap,
        bg=CARD,
        fg=TEXT,
        insertbackground=NEON,
        relief="flat",
        font=("Consolas", font_size, "bold" if bold else "normal"),
        padx=5,
        pady=3,
        highlightthickness=1,
        highlightbackground="#1f2937",
        highlightcolor=NEON
    )
    box.insert("1.0", value)
    box.bind("<KeyRelease>", lambda e: save_data())
    box.bind("<FocusOut>", lambda e: save_data())
    editor_boxes.append(box)
    return box

def tick_label(parent, done=False):
    tick = Label(
        parent,
        text="☑" if done else "☐",
        bg=CARD,
        fg=NEON if done else MUTED,
        font=("Segoe UI Symbol", TICK_SIZE),
        width=2,
        cursor="hand2"
    )
    tick.bind("<Button-1>", lambda e: toggle_tick(tick))
    tick.bind("<Button-3>", lambda e: show_tick_menu(e, tick))
    tick_labels.append(tick)
    return tick

def toggle_tick(tick):
    tick["text"] = "☐" if tick["text"] == "☑" else "☑"
    tick["fg"] = NEON if tick["text"] == "☑" else MUTED
    save_data()

def toggle_row_note(row):
    show_note = not row["note_visible"]
    for task_row in row_widgets:
        task_row["note_visible"] = False
        task_row["note_button"].configure(fg=MUTED)
    row["note_visible"] = show_note
    row["note_button"].configure(fg=NEON if show_note else MUTED)
    layout_task_rows()
    save_data()
    if show_note:
        row["note"].focus_set()

def adjust_note_font(row, change):
    row["note_font_size"] = max(6, min(32, row["note_font_size"] + change))
    row["note"].configure(font=("Consolas", row["note_font_size"], "normal"))
    save_data()

def tick_group_for(tick):
    for row in row_widgets:
        for cell in row["ticks"]:
            if tick in cell:
                return cell
    return None

def add_tick_box(tick):
    cell = tick_group_for(tick)
    if cell is None:
        return

    new_tick = tick_label(cell[0].master)
    new_tick.pack(side=LEFT, padx=1, expand=True)
    cell.append(new_tick)
    save_data()

def launch_shortcut_file(path):
    if not os.path.isfile(path):
        messagebox.showerror("File not found", f"Could not find:\n{path}", parent=root)
        return
    try:
        if os.path.splitext(path)[1].lower() == ".ahk":
            if not os.path.isfile(AUTOHOTKEY_EXE_PATH):
                messagebox.showerror(
                    "AutoHotkey not found",
                    f"Could not find:\n{AUTOHOTKEY_EXE_PATH}",
                    parent=root
                )
                return
            subprocess.Popen([AUTOHOTKEY_EXE_PATH, path])
        else:
            os.startfile(path)
    except OSError as error:
        messagebox.showerror("Could not open file", str(error), parent=root)


def choose_row_file(row):
    dialog = Toplevel(root)
    dialog.title("Choose file")
    dialog.configure(bg=PANEL)
    dialog.transient(root)
    dialog.resizable(False, False)
    dialog.grab_set()

    Label(dialog, text="File for this row", bg=PANEL, fg=TEXT).pack(
        anchor="w", padx=12, pady=(12, 4)
    )
    path_var = StringVar(value=row.get("ahk_path", ""))
    path_row = Frame(dialog, bg=PANEL)
    path_row.pack(fill=X, padx=12)
    path_entry = Entry(
        path_row, textvariable=path_var, width=48, bg=CARD, fg=TEXT,
        insertbackground=NEON, relief="flat"
    )
    path_entry.pack(side=LEFT, fill=X, expand=True, ipady=5)

    def browse():
        selected = filedialog.askopenfilename(
            parent=dialog,
            title="Select a file",
            filetypes=[("All files", "*.*")]
        )
        if selected:
            path_var.set(selected)

    Button(path_row, text="Browse", command=browse, bg="#334155", fg=TEXT, relief="flat").pack(
        side=LEFT, padx=(6, 0), ipady=3
    )

    def save_path(open_after_save):
        path = path_var.get().strip().strip('"')
        if not path:
            messagebox.showerror("File required", "Enter or select a file for this row.", parent=dialog)
            return
        if not os.path.isfile(path):
            messagebox.showerror("File not found", f"Could not find:\n{path}", parent=dialog)
            return
        if not save_row_launch_setting(row, "ahk_path", path, dialog):
            return
        dialog.destroy()
        if open_after_save:
            launch_shortcut_file(path)

    buttons = Frame(dialog, bg=PANEL)
    buttons.pack(anchor="e", padx=12, pady=12)
    Button(buttons, text="Save", command=lambda: save_path(False), bg="#334155", fg=TEXT, relief="flat").pack(
        side=LEFT, padx=(0, 6), ipadx=8, ipady=4
    )
    Button(buttons, text="Save and Open", command=lambda: save_path(True), bg="#0e7490", fg="white", relief="flat").pack(
        side=LEFT, ipadx=8, ipady=4
    )
    path_entry.focus_set()

def open_header_shortcut(index):
    path = header_ahk_paths[index]
    if path:
        launch_shortcut_file(path)
    else:
        choose_header_file(index, open_after_save=one_click_ahk)


def show_header_ahk_menu(event, index):
    path = header_ahk_paths[index]
    menu = Menu(
        root,
        tearoff=0,
        bg=PANEL,
        fg=TEXT,
        activebackground=NEON,
        activeforeground=BG
    )
    menu.add_command(
        label="Open assigned file",
        command=lambda: launch_shortcut_file(header_ahk_paths[index]),
        state="normal" if path else "disabled"
    )
    menu.add_command(
        label="Choose or change file...",
        command=lambda: choose_header_file(index)
    )
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()
    return "break"


def header_file_tooltip(index):
    path = header_ahk_paths[index]
    if path:
        return os.path.basename(path)
    return "No file assigned\nClick to choose a file"


def choose_header_file(index, open_after_save=False):
    dialog = Toplevel(root)
    dialog.title("Choose title shortcut file")
    dialog.configure(bg=PANEL)
    dialog.transient(root)
    dialog.resizable(False, False)
    dialog.grab_set()

    Label(dialog, text="File for this title shortcut", bg=PANEL, fg=TEXT).pack(
        anchor="w", padx=12, pady=(12, 4)
    )
    path_var = StringVar(value=header_ahk_paths[index])
    path_row = Frame(dialog, bg=PANEL)
    path_row.pack(fill=X, padx=12)
    path_entry = Entry(
        path_row, textvariable=path_var, width=48, bg=CARD, fg=TEXT,
        insertbackground=NEON, relief="flat"
    )
    path_entry.pack(side=LEFT, fill=X, expand=True, ipady=5)

    def browse():
        selected = filedialog.askopenfilename(
            parent=dialog,
            title="Select a file",
            filetypes=[("All files", "*.*")]
        )
        if selected:
            path_var.set(selected)

    Button(path_row, text="Browse", command=browse, bg="#334155", fg=TEXT, relief="flat").pack(
        side=LEFT, padx=(6, 0), ipady=3
    )

    def save_path(open_after_save):
        path = path_var.get().strip().strip('"')
        if not path:
            messagebox.showerror("File required", "Enter or select a file.", parent=dialog)
            return
        if not os.path.isfile(path):
            messagebox.showerror("File not found", f"Could not find:\n{path}", parent=dialog)
            return

        previous_path = header_ahk_paths[index]
        header_ahk_paths[index] = path
        try:
            save_data()
        except (OSError, TypeError, ValueError) as error:
            header_ahk_paths[index] = previous_path
            messagebox.showerror("Could not save shortcut", str(error), parent=dialog)
            return

        dialog.destroy()
        if open_after_save:
            launch_shortcut_file(path)

    buttons = Frame(dialog, bg=PANEL)
    buttons.pack(anchor="e", padx=12, pady=12)
    Button(buttons, text="Save", command=lambda: save_path(False), bg="#334155", fg=TEXT, relief="flat").pack(
        side=LEFT, padx=(0, 6), ipadx=8, ipady=4
    )
    if open_after_save:
        Button(
            buttons,
            text="Save and Open",
            command=lambda: save_path(True),
            bg="#0e7490",
            fg="white",
            relief="flat"
        ).pack(side=LEFT, ipadx=8, ipady=4)
    path_entry.focus_set()

def comet_profiles():
    local_state = os.path.join(COMET_USER_DATA_DIR, "Local State")
    try:
        with open(local_state, "r", encoding="utf-8") as file:
            state = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read Comet profiles from:\n{local_state}\n\n{error}") from error

    profile_state = state.get("profile", {})
    profile_info = profile_state.get("info_cache", {}) if isinstance(profile_state, dict) else {}
    if not isinstance(profile_info, dict):
        raise ValueError(f"Comet profile metadata is invalid in:\n{local_state}")
    profiles = []
    for directory, details in profile_info.items():
        profile_path = os.path.join(COMET_USER_DATA_DIR, directory)
        if not os.path.isdir(profile_path) or directory == "System Profile":
            continue
        raw_name = details.get("name", "") if isinstance(details, dict) else ""
        name = raw_name.strip() if isinstance(raw_name, str) else ""
        profiles.append((name or directory, directory))
    return profiles


def chrome_profiles():
    local_state = os.path.join(CHROME_USER_DATA_DIR, "Local State")
    try:
        with open(local_state, "r", encoding="utf-8") as file:
            state = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read Chrome profiles from:\n{local_state}\n\n{error}") from error

    profile_state = state.get("profile", {})
    profile_info = profile_state.get("info_cache", {}) if isinstance(profile_state, dict) else {}
    if not isinstance(profile_info, dict):
        raise ValueError(f"Chrome profile metadata is invalid in:\n{local_state}")
    profiles = []
    for directory, details in profile_info.items():
        profile_path = os.path.join(CHROME_USER_DATA_DIR, directory)
        if not os.path.isdir(profile_path) or directory == "System Profile":
            continue
        raw_name = details.get("name", "") if isinstance(details, dict) else ""
        name = raw_name.strip() if isinstance(raw_name, str) else ""
        profiles.append((name or directory, directory))
    return profiles


def activate_comet_profile_window(profile):
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    propsys = ctypes.WinDLL("propsys", use_last_error=True)
    ole32 = ctypes.WinDLL("ole32", use_last_error=True)
    process_query_limited_information = 0x1000

    class GUID(ctypes.Structure):
        _fields_ = [
            ("data1", wintypes.DWORD),
            ("data2", wintypes.WORD),
            ("data3", wintypes.WORD),
            ("data4", ctypes.c_ubyte * 8),
        ]

    class PROPERTYKEY(ctypes.Structure):
        _fields_ = [("fmtid", GUID), ("pid", wintypes.DWORD)]

    class PROPVARIANT_UNION(ctypes.Union):
        _fields_ = [("wide_string", wintypes.LPWSTR), ("pointer", ctypes.c_void_p)]

    class PROPVARIANT(ctypes.Structure):
        _fields_ = [
            ("vt", wintypes.WORD),
            ("reserved1", wintypes.WORD),
            ("reserved2", wintypes.WORD),
            ("reserved3", wintypes.WORD),
            ("value", PROPVARIANT_UNION),
        ]

    shell_iid = GUID(
        0x886D8EEB, 0x8CF2, 0x4446,
        (ctypes.c_ubyte * 8)(0x8D, 0x02, 0xCD, 0xBA, 0x1D, 0xBD, 0xCF, 0x99)
    )
    app_id_key = PROPERTYKEY(
        GUID(
            0x9F4C2855, 0x9F79, 0x4B39,
            (ctypes.c_ubyte * 8)(0xA8, 0xD0, 0xE1, 0xD4, 0x2D, 0xE1, 0xD5, 0xF3)
        ),
        5
    )

    shell32.SHGetPropertyStoreForWindow.argtypes = [
        wintypes.HWND, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)
    ]
    shell32.SHGetPropertyStoreForWindow.restype = ctypes.c_long
    propsys.PropVariantToStringAlloc.argtypes = [
        ctypes.POINTER(PROPVARIANT), ctypes.POINTER(wintypes.LPWSTR)
    ]
    propsys.PropVariantToStringAlloc.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    user32.EnumWindows.argtypes = [
        ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM
    ]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.GetForegroundWindow.restype = wintypes.HWND

    def window_app_id(hwnd):
        property_store = ctypes.c_void_p()
        result = shell32.SHGetPropertyStoreForWindow(
            hwnd, ctypes.byref(shell_iid), ctypes.byref(property_store)
        )
        if result < 0:
            raise OSError(result, "Could not read a Comet window's profile.")

        try:
            vtable = ctypes.cast(
                property_store, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
            ).contents
            get_value = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p,
                ctypes.POINTER(PROPERTYKEY), ctypes.POINTER(PROPVARIANT)
            )(vtable[5])
            release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
            value = PROPVARIANT()
            result = get_value(property_store, ctypes.byref(app_id_key), ctypes.byref(value))
            if result < 0:
                raise OSError(result, "Could not read a Comet window's profile.")
            try:
                app_id = wintypes.LPWSTR()
                result = propsys.PropVariantToStringAlloc(ctypes.byref(value), ctypes.byref(app_id))
                if result < 0:
                    raise OSError(result, "Could not read a Comet window's profile.")
                try:
                    return app_id.value
                finally:
                    ole32.CoTaskMemFree(app_id)
            finally:
                ole32.PropVariantClear.argtypes = [ctypes.POINTER(PROPVARIANT)]
                ole32.PropVariantClear.restype = ctypes.c_long
                ole32.PropVariantClear(ctypes.byref(value))
        finally:
            release(property_store)

    matching_windows = []
    callback_errors = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def collect_window(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True

        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        process = kernel32.OpenProcess(
            process_query_limited_information, False, process_id.value
        )
        if not process:
            return True
        try:
            executable = ctypes.create_unicode_buffer(32768)
            length = wintypes.DWORD(len(executable))
            if not kernel32.QueryFullProcessImageNameW(
                process, 0, executable, ctypes.byref(length)
            ):
                return True
            if os.path.normcase(os.path.abspath(executable.value)) != os.path.normcase(
                os.path.abspath(COMET_EXE_PATH)
            ):
                return True
        finally:
            kernel32.CloseHandle(process)

        try:
            app_id = window_app_id(hwnd)
            if app_id == f"Comet.UserData.{profile.replace(' ', '')}":
                matching_windows.append(hwnd)
        except OSError as error:
            callback_errors.append(error)
            return False
        return True

    ctypes.set_last_error(0)
    if not user32.EnumWindows(collect_window, 0):
        if callback_errors:
            raise callback_errors[0]
        error = ctypes.get_last_error()
        if error:
            raise OSError(error, "Could not enumerate open Comet windows.")

    if not matching_windows:
        return False

    hwnd = matching_windows[0]
    user32.ShowWindow(hwnd, 9)
    user32.BringWindowToTop(hwnd)
    if user32.GetForegroundWindow() != hwnd and not user32.SetForegroundWindow(hwnd):
        error = ctypes.get_last_error()
        raise OSError(error, "Windows would not activate the existing Comet profile.")
    return True

def launch_comet_profile(profile):
    if not os.path.isfile(COMET_EXE_PATH):
        messagebox.showerror("Comet not found", f"Could not find:\n{COMET_EXE_PATH}", parent=root)
        return
    profile_path = os.path.join(COMET_USER_DATA_DIR, profile)
    if not os.path.isdir(profile_path):
        messagebox.showerror("Comet profile not found", f"Could not find:\n{profile_path}", parent=root)
        return
    try:
        if activate_comet_profile_window(profile):
            return
        subprocess.Popen([
            COMET_EXE_PATH,
            f"--user-data-dir={COMET_USER_DATA_DIR}",
            f"--profile-directory={profile}",
            "--restore-last-session"
        ])
    except OSError as error:
        messagebox.showerror("Could not open Comet", str(error), parent=root)

def choose_comet_profile(row):
    try:
        profiles = comet_profiles()
    except ValueError as error:
        messagebox.showerror("Could not load Comet profiles", str(error), parent=root)
        return
    if not profiles:
        messagebox.showerror("No Comet profiles", "No Comet browser profiles were found.", parent=root)
        return

    dialog = Toplevel(root)
    dialog.title("Choose Comet profile")
    dialog.configure(bg=PANEL)
    dialog.transient(root)
    dialog.resizable(False, False)
    dialog.grab_set()
    Label(dialog, text="Comet profile for this row", bg=PANEL, fg=TEXT).pack(
        anchor="w", padx=12, pady=(12, 4)
    )

    display_names = [
        f"{name} ({directory})" if name != directory else directory
        for name, directory in profiles
    ]
    profile_by_name = {
        display_name: directory
        for display_name, (_, directory) in zip(display_names, profiles)
    }
    current_profile = row.get("comet_profile", "")
    current_name = next(
        (
            display_name
            for display_name, (_, directory) in zip(display_names, profiles)
            if directory == current_profile
        ),
        ""
    )
    selected_name = StringVar(value=current_name or display_names[0])
    profile_menu = ttk.Combobox(
        dialog, textvariable=selected_name, values=display_names, state="readonly", width=42
    )
    profile_menu.pack(padx=12, pady=4)

    def save_profile(open_after_save):
        profile = profile_by_name.get(selected_name.get())
        if not profile:
            messagebox.showerror("Choose a profile", "Select a Comet profile from the list.", parent=dialog)
            return
        if not save_row_launch_setting(row, "comet_profile", profile, dialog):
            return
        dialog.destroy()
        if open_after_save:
            launch_comet_profile(profile)

    buttons = Frame(dialog, bg=PANEL)
    buttons.pack(anchor="e", padx=12, pady=12)
    Button(buttons, text="Save", command=lambda: save_profile(False), bg="#334155", fg=TEXT, relief="flat").pack(
        side=LEFT, padx=(0, 6), ipadx=8, ipady=4
    )
    Button(buttons, text="Save and Open", command=lambda: save_profile(True), bg="#0e7490", fg="white", relief="flat").pack(
        side=LEFT, ipadx=8, ipady=4
    )


def launch_chrome_profile(profile):
    chrome_exe = next((path for path in CHROME_EXE_PATHS if os.path.isfile(path)), None)
    if chrome_exe is None:
        messagebox.showerror(
            "Chrome not found",
            "Could not find Google Chrome in the standard installation locations.",
            parent=root
        )
        return
    profile_path = os.path.join(CHROME_USER_DATA_DIR, profile)
    if not os.path.isdir(profile_path):
        messagebox.showerror("Chrome profile not found", f"Could not find:\n{profile_path}", parent=root)
        return
    try:
        subprocess.Popen([
            chrome_exe,
            f"--user-data-dir={CHROME_USER_DATA_DIR}",
            f"--profile-directory={profile}",
            "--restore-last-session"
        ])
    except OSError as error:
        messagebox.showerror("Could not open Chrome", str(error), parent=root)


def choose_chrome_profile(row):
    try:
        profiles = chrome_profiles()
    except ValueError as error:
        messagebox.showerror("Could not load Chrome profiles", str(error), parent=root)
        return
    if not profiles:
        messagebox.showerror("No Chrome profiles", "No Chrome browser profiles were found.", parent=root)
        return

    dialog = Toplevel(root)
    dialog.title("Choose Chrome profile")
    dialog.configure(bg=PANEL)
    dialog.transient(root)
    dialog.resizable(False, False)
    dialog.grab_set()
    Label(dialog, text="Chrome profile for this row", bg=PANEL, fg=TEXT).pack(
        anchor="w", padx=12, pady=(12, 4)
    )

    display_names = [
        f"{name} ({directory})" if name != directory else directory
        for name, directory in profiles
    ]
    profile_by_name = {
        display_name: directory
        for display_name, (_, directory) in zip(display_names, profiles)
    }
    current_profile = row.get("chrome_profile", "")
    current_name = next(
        (
            display_name
            for display_name, (_, directory) in zip(display_names, profiles)
            if directory == current_profile
        ),
        ""
    )
    selected_name = StringVar(value=current_name or display_names[0])
    profile_menu = ttk.Combobox(
        dialog, textvariable=selected_name, values=display_names, state="readonly", width=42
    )
    profile_menu.pack(padx=12, pady=4)

    def save_profile(open_after_save):
        profile = profile_by_name.get(selected_name.get())
        if not profile:
            messagebox.showerror("Choose a profile", "Select a Chrome profile from the list.", parent=dialog)
            return
        if not save_row_launch_setting(row, "chrome_profile", profile, dialog):
            return
        dialog.destroy()
        if open_after_save:
            launch_chrome_profile(profile)

    buttons = Frame(dialog, bg=PANEL)
    buttons.pack(anchor="e", padx=12, pady=12)
    Button(buttons, text="Save", command=lambda: save_profile(False), bg="#334155", fg=TEXT, relief="flat").pack(
        side=LEFT, padx=(0, 6), ipadx=8, ipady=4
    )
    Button(buttons, text="Save and Open", command=lambda: save_profile(True), bg="#0e7490", fg="white", relief="flat").pack(
        side=LEFT, ipadx=8, ipady=4
    )


def save_row_launch_setting(row, key, value, parent):
    previous_value = row.get(key, "")
    row[key] = value
    try:
        save_data()
    except (OSError, TypeError, ValueError) as error:
        row[key] = previous_value
        messagebox.showerror("Could not save row settings", str(error), parent=parent)
        return False
    return True

def open_row_file(row):
    path = row.get("ahk_path", "").strip()
    if path:
        launch_shortcut_file(path)
    else:
        choose_row_file(row)

def open_row_comet(row):
    profile = row.get("comet_profile", "").strip()
    if profile:
        launch_comet_profile(profile)
    else:
        choose_comet_profile(row)


def open_row_chrome(row):
    profile = row.get("chrome_profile", "").strip()
    if profile:
        launch_chrome_profile(profile)
    else:
        choose_chrome_profile(row)


def show_row_launch_menu(event, row):
    menu = Menu(root, tearoff=0, bg=PANEL, fg=TEXT, activebackground=NEON, activeforeground=BG)
    menu.add_command(
        label="Open assigned file",
        command=lambda: open_row_file(row),
        state="normal" if row.get("ahk_path", "").strip() else "disabled"
    )
    menu.add_command(
        label="Open Comet profile",
        command=lambda: open_row_comet(row),
        state="normal" if row.get("comet_profile", "").strip() else "disabled"
    )
    menu.add_command(
        label="Open Chrome profile",
        command=lambda: open_row_chrome(row),
        state="normal" if row.get("chrome_profile", "").strip() else "disabled"
    )
    menu.add_separator()
    menu.add_command(label="Choose file...", command=lambda: choose_row_file(row))
    menu.add_command(label="Choose Comet profile...", command=lambda: choose_comet_profile(row))
    menu.add_command(label="Choose Chrome profile...", command=lambda: choose_chrome_profile(row))
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()
    return "break"


def row_file_tooltip(row):
    path = row.get("ahk_path", "").strip()
    if path:
        return os.path.basename(path)
    return "No file assigned\nClick to choose"


def row_comet_tooltip(row):
    profile = row.get("comet_profile", "").strip()
    if not profile:
        return "No Comet profile assigned\nClick to choose"
    try:
        profile_name = next(
            (name for name, directory in comet_profiles() if directory == profile),
            None
        )
    except ValueError as error:
        return f"Comet profile name unavailable: {error}"
    if profile_name is None:
        return f"Comet profile name unavailable: {profile}"
    return f"Comet profile: {profile_name}"


def row_chrome_tooltip(row):
    profile = row.get("chrome_profile", "").strip()
    if not profile:
        return "No Chrome profile assigned\nClick to choose"
    try:
        profile_name = next(
            (name for name, directory in chrome_profiles() if directory == profile),
            None
        )
    except ValueError as error:
        return f"Chrome profile name unavailable: {error}"
    if profile_name is None:
        return f"Chrome profile name unavailable: {profile}"
    return f"Chrome profile: {profile_name}"


def add_tooltip(widget, text):
    tooltip = None

    def show(event):
        nonlocal tooltip
        if tooltip is not None:
            return
        tooltip_text = text() if callable(text) else text
        tooltip = Toplevel(root)
        tooltip.wm_overrideredirect(True)
        tooltip.attributes("-topmost", True)
        tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 12}")
        Label(tooltip, text=tooltip_text, bg=PANEL, fg=TEXT, font=("Segoe UI", 8), padx=6, pady=3).pack()

    def hide(event):
        nonlocal tooltip
        if tooltip is not None:
            tooltip.destroy()
            tooltip = None

    widget.bind("<Enter>", show)
    widget.bind("<Leave>", hide)

def remove_tick_box(tick):
    cell = tick_group_for(tick)
    if cell is None or len(cell) <= 1:
        return

    cell.remove(tick)
    tick_labels.remove(tick)
    tick.destroy()
    save_data()

def show_tick_menu(event, tick):
    cell = tick_group_for(tick)
    if cell is None:
        return

    menu = Menu(
        root,
        tearoff=0,
        bg=PANEL,
        fg=TEXT,
        activebackground=NEON,
        activeforeground=BG
    )
    menu.add_command(label="Add tick box", command=lambda: add_tick_box(tick))
    menu.add_command(
        label="Remove tick box",
        command=lambda: remove_tick_box(tick),
        state="normal" if len(cell) > 1 else "disabled"
    )
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()

def untick_all():
    for tick in tick_labels:
        tick["text"] = "☐"
        tick["fg"] = MUTED
    save_data()

def update_minimum_width():
    global item_section_width
    root.update_idletasks()

    header_min_width = (
        sum(button.winfo_reqwidth() + 2 for button in header_ahk_buttons)
        if show_title_shortcuts else 0
    ) + ITEM_SECTION_MIN_NAME_WIDTH + 4
    row_min_widths = [
        sum(
            button.winfo_reqwidth() + 2
            for key, button in row["icon_buttons"].items()
            if icon_visibility[key]
        )
        + ITEM_SECTION_MIN_NAME_WIDTH + 4
        for row in row_widgets
    ]
    item_min_width = max([header_min_width, *row_min_widths])
    item_section_width = max(item_section_width, item_min_width)
    grid_area.columnconfigure(0, weight=0, minsize=item_section_width)
    grid_area.columnconfigure(1, weight=0, minsize=ITEM_SECTION_DIVIDER_WIDTH)

    column_widths = []
    for column_index in range(len(column_boxes)):
        ticks = [
            tick
            for row in row_widgets
            for tick in row["ticks"][column_index]
        ]
        tick_width = max((tick.winfo_reqwidth() + 8 for tick in ticks), default=28)
        button_width = (
            column_remove_buttons[column_index].winfo_reqwidth() + 3
            if edit_mode else 0
        )
        width = max(tick_width, button_width)
        grid_area.columnconfigure(column_index + 2, weight=1, minsize=width)
        column_widths.append(width)

    delete_width = (
        max(
            (row["delete"].winfo_reqwidth() + 4 for row in row_widgets),
            default=28
        )
        if edit_mode else 0
    )
    grid_area.columnconfigure(
        len(column_boxes) + 2,
        weight=0,
        minsize=delete_width
    )
    column_divider.grid(
        row=0,
        column=1,
        rowspan=max(1, len(row_widgets) + 1),
        sticky="ns",
        padx=1,
        pady=2
    )
    right_section_min_width = sum(column_widths) + delete_width
    root.item_section_min_width = item_min_width
    root.right_section_min_width = right_section_min_width
    root.minsize(
        item_section_width + ITEM_SECTION_DIVIDER_WIDTH + right_section_min_width + 20,
        1
    )
    return item_min_width, right_section_min_width

def start_item_section_resize(event):
    root.item_resize_start_x = event.x_root
    root.item_resize_start_width = item_section_width

def resize_item_section(event):
    global item_section_width
    item_min_width = root.item_section_min_width
    right_min_width = root.right_section_min_width
    max_width = max(
        item_min_width,
        root.winfo_width() - right_min_width - ITEM_SECTION_DIVIDER_WIDTH - 20
    )
    item_section_width = max(
        item_min_width,
        min(
            max_width,
            root.item_resize_start_width + event.x_root - root.item_resize_start_x
        )
    )
    grid_area.columnconfigure(0, weight=0, minsize=item_section_width)
    root.minsize(
        item_section_width + ITEM_SECTION_DIVIDER_WIDTH + right_min_width + 20,
        1
    )

def finish_item_section_resize(event):
    save_settings()

def add_column(name="New"):
    index = len(column_boxes)

    header_cell = Frame(grid_area, bg=BG)
    header_cell.grid_propagate(False)
    header_cell.grid(row=0, column=index + 2, padx=2, pady=3, sticky="ew")

    box = editor(header_cell, name, width=10, bold=True)
    box.pack(side=LEFT, fill="x", expand=True)

    remove_btn = Button(
        header_cell,
        text="✕",
        command=lambda: remove_column(index),
        bg=CARD,
        fg=DANGER,
        activebackground="#7f1d1d",
        relief="flat",
        font=("Segoe UI", 8, "bold"),
        width=2,
        cursor="hand2"
    )
    if edit_mode:
        remove_btn.pack(side=RIGHT, padx=(3, 0))

    column_header_cells.append(header_cell)
    column_boxes.append(box)
    column_remove_buttons.append(remove_btn)

    for row in row_widgets:
        cell_frame = Frame(grid_area, bg=BG)
        cell_frame.grid(row=row["row_number"], column=index + 2, padx=2, pady=2, sticky="ew")
        tick = tick_label(cell_frame)
        tick.pack(side=LEFT, padx=1, expand=True)
        row["cell_frames"].insert(index, cell_frame)
        row["ticks"].insert(index, [tick])

    grid_area.columnconfigure(index + 2, weight=1)
    layout_task_rows()
    update_minimum_width()
    save_data()

def layout_task_rows():
    note_row = next((row for row in row_widgets if row["note_visible"]), None)
    for header_cell in column_header_cells:
        if note_row is not None:
            header_cell.grid_remove()
        else:
            header_cell.grid()
    for remove_btn in column_remove_buttons:
        if edit_mode and note_row is None:
            if not remove_btn.winfo_manager():
                remove_btn.pack(side=RIGHT, padx=(3, 0))
        else:
            remove_btn.pack_forget()

    for row in row_widgets:
        row_number = row["row_number"]
        row["item_cell"].grid_configure(row=row_number)
        row["item"].grid_configure(row=0, column=1)
        if edit_mode:
            row["drag_handle"].grid_configure(row=0, column=0, padx=(0, 4))
        else:
            row["drag_handle"].grid_remove()
        layout_row_icons(row)
        for column_index, cell_frame in enumerate(row["cell_frames"]):
            if note_row is not None:
                cell_frame.grid_remove()
            else:
                cell_frame.grid_configure(
                    row=row_number,
                    column=column_index + 2,
                    padx=2,
                    pady=2,
                    sticky="ew"
                )
        if note_row is not None or not edit_mode:
            row["delete"].grid_remove()
        else:
            row["delete"].grid_configure(
                row=row_number,
                column=len(column_boxes) + 2
            )
        row["delete"].configure(
            command=lambda task_row=row: remove_row(row_widgets.index(task_row))
        )

    for row in row_widgets:
        if row is note_row:
            grid_area.update_idletasks()
            header_x, header_y, _, _ = grid_area.grid_bbox(2, 0)
            row["note_panel"].place(
                x=header_x,
                y=header_y,
                relwidth=1,
                relheight=1,
                width=-header_x,
                height=-header_y
            )
        else:
            row["note_panel"].place_forget()

    column_divider.grid_configure(rowspan=max(1, len(row_widgets) + 1))


def start_row_drag(event, row):
    global dragged_row, drag_order_changed
    if not edit_mode:
        return

    dragged_row = row
    drag_order_changed = False


def move_row_drag(event):
    global drag_order_changed
    row = dragged_row
    if not edit_mode or row not in row_widgets:
        return

    other_rows = [candidate for candidate in row_widgets if candidate is not row]
    target_index = sum(
        event.y_root
        >= candidate["item_cell"].winfo_rooty()
        + candidate["item_cell"].winfo_height() / 2
        for candidate in other_rows
    )
    source_index = row_widgets.index(row)
    if target_index == source_index:
        return

    row_widgets.pop(source_index)
    row_widgets.insert(target_index, row)
    for index, item in enumerate(row_widgets):
        item["row_number"] = index + 1
    layout_task_rows()
    drag_order_changed = True


def finish_row_drag(event):
    global dragged_row, drag_order_changed
    if drag_order_changed:
        save_data()
    dragged_row = None
    drag_order_changed = False


def toggle_edit_mode():
    global edit_mode
    edit_mode = not edit_mode
    edit_toggle_button.configure(
        text=f"EDIT: {'ON' if edit_mode else 'OFF'}",
        bg="#0e7490" if edit_mode else "#334155"
    )
    layout_task_rows()
    update_minimum_width()


def toggle_icon_visibility(key, label, button):
    icon_visibility[key] = not icon_visibility[key]
    button.configure(
        text=f"{label}: {'ON' if icon_visibility[key] else 'OFF'}",
        bg="#0e7490" if icon_visibility[key] else "#334155"
    )
    for row in row_widgets:
        layout_row_icons(row)
    update_minimum_width()
    save_settings()

def layout_title_shortcuts():
    for button in header_ahk_buttons:
        if show_title_shortcuts:
            button.grid()
        else:
            button.grid_remove()


def toggle_title_shortcuts():
    global show_title_shortcuts
    show_title_shortcuts = not show_title_shortcuts
    layout_title_shortcuts()
    title_shortcuts_button.configure(
        text=f"TITLE SHORTCUTS: {'ON' if show_title_shortcuts else 'OFF'}",
        bg="#0e7490" if show_title_shortcuts else "#334155"
    )
    update_minimum_width()
    save_settings()

def layout_row_icons(row):
    column = 2
    for key, button in row["icon_buttons"].items():
        if icon_visibility[key]:
            button.grid_configure(row=0, column=column)
            column += 1
        else:
            button.grid_remove()

def add_row(
    item="New item", ticks=None, ahk_path="", comet_profile="", note="",
    note_font_size=None, chrome_profile=""
):
    if not isinstance(ticks, (list, tuple)):
        ticks = []
    normalized_ticks = []
    for index in range(len(column_boxes)):
        cell = ticks[index] if index < len(ticks) else False
        if isinstance(cell, list):
            normalized_ticks.append([bool(done) for done in cell] or [False])
        else:
            normalized_ticks.append([bool(cell)])
    row_number = len(row_widgets) + 1

    item_cell = Frame(grid_area, bg=BG)
    item_cell.grid(row=row_number, column=0, padx=2, pady=2, sticky="ew")
    item_cell.grid_propagate(False)
    item_cell.columnconfigure(1, weight=1)

    drag_handle = Button(
        item_cell,
        text="⋮⋮",
        bg=CARD,
        fg=MUTED,
        activebackground="#155e75",
        relief="flat",
        font=("Segoe UI Symbol", 9, "bold"),
        width=2,
        cursor="size_ns"
    )

    item_box = editor(item_cell, item, width=14)
    item_box.grid(row=0, column=1, sticky="ew")
    drag_handle.grid(row=0, column=0, padx=(0, 4))
    note_panel = Frame(grid_area, bg=BG)
    note_font_size = max(6, min(32, int(note_font_size or font_size)))
    note_box = editor(note_panel, note, width=14, height=3, wrap="word")
    note_box.configure(font=("Consolas", note_font_size, "normal"))
    note_box.pack(fill=BOTH, expand=True)
    for symbol, change, tooltip in (
        ("A−", -1, "Decrease note font size"),
        ("A+", 1, "Increase note font size"),
    ):
        font_button = Button(
            note_panel,
            text=symbol,
            command=lambda amount=change: adjust_note_font(row_entry, amount),
            bg=CARD,
            fg=NEON,
            activebackground="#155e75",
            relief="flat",
            font=("Consolas", 8, "bold"),
            padx=4,
            pady=1,
            cursor="hand2"
        )
        font_button.place(relx=1.0, x=-4 if change < 0 else -34, y=4, anchor="ne")
        add_tooltip(font_button, tooltip)

    row_data = {
        "ahk_path": ahk_path,
        "comet_profile": comet_profile,
        "chrome_profile": chrome_profile,
    }

    ahk_btn = Button(
        item_cell,
        text="▤",
        command=lambda: open_row_file(row_data),
        bg=CARD,
        fg=NEON,
        activebackground="#155e75",
        relief="flat",
        font=("Segoe UI Symbol", 9),
        width=2,
        cursor="hand2"
    )
    ahk_btn.grid(row=0, column=2, padx=(2, 0))
    ahk_btn.bind("<Button-3>", lambda event: show_row_launch_menu(event, row_data))
    add_tooltip(ahk_btn, lambda: row_file_tooltip(row_data))

    comet_btn = Button(
        item_cell,
        text="◉",
        command=lambda: open_row_comet(row_data),
        bg=CARD,
        fg=NEON,
        activebackground="#155e75",
        relief="flat",
        font=("Segoe UI Symbol", 9),
        width=2,
        cursor="hand2"
    )
    comet_btn.grid(row=0, column=3, padx=(2, 0))
    comet_btn.bind("<Button-3>", lambda event: show_row_launch_menu(event, row_data))
    add_tooltip(comet_btn, lambda: row_comet_tooltip(row_data))

    chrome_btn = Button(
        item_cell,
        text="🌐",
        command=lambda: open_row_chrome(row_data),
        bg=CARD,
        fg=NEON,
        activebackground="#155e75",
        relief="flat",
        font=("Segoe UI Symbol", 9),
        width=2,
        cursor="hand2"
    )
    chrome_btn.grid(row=0, column=4, padx=(2, 0))
    chrome_btn.bind("<Button-3>", lambda event: show_row_launch_menu(event, row_data))
    add_tooltip(chrome_btn, lambda: row_chrome_tooltip(row_data))

    note_btn = Button(
        item_cell,
        text="✎",
        command=lambda: toggle_row_note(row_entry),
        bg=CARD,
        fg=NEON if note else MUTED,
        activebackground="#155e75",
        relief="flat",
        font=("Segoe UI Symbol", 9),
        width=2,
        cursor="hand2"
    )
    note_btn.grid(row=0, column=5, padx=(2, 0))
    add_tooltip(note_btn, "Show or hide this row's note")
    icon_buttons = {
        "show_shortcut_icon": ahk_btn,
        "show_comet_icon": comet_btn,
        "show_chrome_icon": chrome_btn,
        "show_note_icon": note_btn,
    }
    item_cell.configure(
        height=max(
            item_box.winfo_reqheight(),
            ahk_btn.winfo_reqheight(),
            comet_btn.winfo_reqheight(),
            chrome_btn.winfo_reqheight(),
            note_btn.winfo_reqheight()
        )
    )

    tick_groups_for_row = []
    cell_frames_for_row = []
    for column_index, cell in enumerate(normalized_ticks):
        cell_frame = Frame(grid_area, bg=BG)
        cell_frame.grid(row=row_number, column=column_index + 2, padx=2, pady=2, sticky="ew")
        cell_frames_for_row.append(cell_frame)

        tick_group = []
        for done in cell:
            tick = tick_label(cell_frame, done)
            tick.pack(side=LEFT, padx=1, expand=True)
            tick_group.append(tick)
        tick_groups_for_row.append(tick_group)

    delete_btn = Button(
        grid_area,
        text="✕",
        command=lambda: remove_row(row_widgets.index(row_entry)),
        bg=CARD,
        fg=DANGER,
        activebackground="#7f1d1d",
        relief="flat",
        font=("Segoe UI", 8, "bold"),
        width=2,
        cursor="hand2"
    )
    delete_btn.grid(row=row_number, column=len(column_boxes) + 2, padx=2, pady=2)

    row_entry = {
        "row_number": row_number,
        "item": item_box,
        "note": note_box,
        "note_panel": note_panel,
        "note_font_size": note_font_size,
        "note_visible": False,
        "note_button": note_btn,
        "item_cell": item_cell,
        "launch_buttons": [ahk_btn, comet_btn, chrome_btn],
        "icon_buttons": icon_buttons,
        "launch_settings": row_data,
        "ticks": tick_groups_for_row,
        "cell_frames": cell_frames_for_row,
        "delete": delete_btn,
        "drag_handle": drag_handle
    }

    drag_handle.bind(
        "<ButtonPress-1>",
        lambda event, task_row=row_entry: start_row_drag(event, task_row)
    )
    drag_handle.bind("<B1-Motion>", move_row_drag)
    drag_handle.bind("<ButtonRelease-1>", finish_row_drag)

    row_widgets.append(row_entry)

    layout_row_icons(row_entry)
    layout_task_rows()
    update_minimum_width()
    save_data()

def remove_column(index):
    save_data()
    data = load_data()

    if 0 <= index < len(data["columns"]):
        data["columns"].pop(index)
        for row in data["rows"]:
            if index < len(row["ticks"]):
                row["ticks"].pop(index)

    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    rebuild_table()

def remove_row(index):
    row = row_widgets[index]
    editor_boxes.remove(row["item"])
    editor_boxes.remove(row["note"])
    for cell in row["ticks"]:
        for tick in cell:
            tick_labels.remove(tick)
    for widget in [row["item_cell"], row["note_panel"], *row["cell_frames"], row["delete"]]:
        widget.destroy()
    row_widgets.pop(index)
    layout_task_rows()
    update_minimum_width()
    save_data()

def add_new_row():
    add_row("New item")
    save_data()

def add_new_column():
    add_column("New")
    save_data()

def rebuild_table():
    for column_index in range(len(column_boxes) + 3):
        grid_area.columnconfigure(column_index, weight=0, minsize=0)

    for widget in grid_area.winfo_children():
        if widget not in (column_divider, item_header_cell):
            widget.destroy()

    column_boxes.clear()
    column_header_cells.clear()
    column_remove_buttons.clear()
    row_widgets.clear()
    editor_boxes.clear()
    tick_labels.clear()

    data = load_data()
    item_header_cell.grid(row=0, column=0, padx=2, pady=3, sticky="ew")

    for name in data["columns"]:
        add_column(name)

    for row in data["rows"]:
        add_row(
            row.get("item", ""),
            row.get("ticks", []),
            row.get("ahk_path", LEGACY_AHK_PATH),
            row.get("comet_profile", LEGACY_COMET_PROFILE),
            row.get("note", ""),
            row.get("note_font_size"),
            row.get("chrome_profile", "")
        )
    update_minimum_width()

def increase_font():
    global font_size
    font_size += 1
    apply_font_size()

def decrease_font():
    global font_size
    if font_size > 6:
        font_size -= 1
    apply_font_size()

def apply_font_size():
    note_boxes = {row["note"] for row in row_widgets}
    for box in editor_boxes:
        if box in note_boxes:
            continue
        bold = "bold" in box["font"]
        box["font"] = ("Consolas", font_size, "bold" if bold else "normal")

    item_head["font"] = ("Consolas", font_size, "bold")
    update_minimum_width()
    save_settings()


def apply_opacity(value=None):
    global window_opacity
    if value is not None:
        window_opacity = max(0.35, min(1.0, float(value)))
    root.attributes("-alpha", window_opacity)
    save_settings()


data = load_data()
settings = load_settings()

font_size = settings.get("font_size", 10)
item_section_width = settings["item_width"]
window_opacity = float(settings.get("opacity", 0.95))
header_ahk_paths = settings["header_ahk_paths"]
one_click_ahk = settings["one_click_ahk"]
show_title_shortcuts = settings["show_title_shortcuts"]
icon_visibility = {
    key: settings[key]
    for key in (
        "show_note_icon", "show_shortcut_icon", "show_comet_icon",
        "show_chrome_icon"
    )
}

column_boxes = []
column_header_cells = []
column_remove_buttons = []
row_widgets = []
editor_boxes = []
tick_labels = []

root = Tk()
root.title("Neon Checklist")
root.geometry(
    f"{settings['width']}x{settings['height']}+{settings['x']}+{settings['y']}"
)
root.minsize(1, 1)
root.configure(bg=BG)
root.attributes("-topmost", True)
root.attributes("-alpha", window_opacity)
root.overrideredirect(True)

settings_open = False
settings_panel = None
settings_panel_extra_height = 0


def toggle_settings_panel():
    global settings_open, settings_panel_extra_height
    settings_open = not settings_open
    if settings_open:
        root.update_idletasks()
        settings_panel_extra_height = settings_panel.winfo_reqheight() + 8
        root.geometry(
            f"{root.winfo_width()}x{root.winfo_height() + settings_panel_extra_height}"
            f"+{root.winfo_x()}+{root.winfo_y()}"
        )
        settings_panel.pack(fill=X, padx=8, pady=(0, 8))
    else:
        settings_panel.pack_forget()
        root.geometry(
            f"{root.winfo_width()}x{max(1, root.winfo_height() - settings_panel_extra_height)}"
            f"+{root.winfo_x()}+{root.winfo_y()}"
        )
        settings_panel_extra_height = 0
    save_settings()


def start_move(event):
    root.move_x = event.x
    root.move_y = event.y


def do_move(event):
    x = root.winfo_x() + event.x - root.move_x
    y = root.winfo_y() + event.y - root.move_y
    root.geometry(f"+{x}+{y}")
    save_settings()


top = Frame(root, bg=PANEL)
top.pack(fill=X)

top.bind("<Button-1>", start_move)
top.bind("<B1-Motion>", do_move)

Label(
    top,
    text="◈ CHECKLIST",
    bg=PANEL,
    fg=NEON,
    font=("Consolas", 11, "bold")
).pack(side=LEFT, padx=8, pady=7)


def small_button(parent, text, command, color):
    return Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg="white",
        activebackground="#155e75",
        relief="flat",
        font=("Consolas", 9, "bold"),
        padx=7,
        pady=4,
        cursor="hand2"
    )


small_button(top, "✕", close_app, "#9f1239").pack(side=RIGHT, padx=(3, 8), pady=6)
settings_button = small_button(top, "⚙", toggle_settings_panel, "#334155")
settings_button.pack(side=RIGHT, padx=3, pady=6)

settings_panel = Frame(root, bg=PANEL, highlightthickness=1, highlightbackground="#1f2937")
settings_panel.pack_forget()

settings_row = Frame(settings_panel, bg=PANEL)
settings_row.pack(fill=X, padx=8, pady=(6, 0))
settings_row2 = Frame(settings_panel, bg=PANEL)
settings_row2.pack(fill=X, padx=8, pady=(0, 6))
settings_row3 = Frame(settings_panel, bg=PANEL)
settings_row3.pack(fill=X, padx=8, pady=(0, 6))

small_button(settings_row, "＋ ROW", add_new_row, "#0e7490").pack(side=LEFT, padx=3, pady=4)
small_button(settings_row, "＋ COL", add_new_column, "#0e7490").pack(side=LEFT, padx=3, pady=4)
small_button(settings_row, "A−", decrease_font, "#334155").pack(side=LEFT, padx=3, pady=4)
small_button(settings_row, "A+", increase_font, "#334155").pack(side=LEFT, padx=3, pady=4)
small_button(settings_row, "UNTICK", untick_all, "#334155").pack(side=LEFT, padx=3, pady=4)
edit_toggle_button = small_button(
    settings_row, "EDIT: OFF", toggle_edit_mode, "#334155"
)
edit_toggle_button.pack(side=LEFT, padx=3, pady=4)
icon_toggle_buttons = {}
for key, label in (
    ("show_note_icon", "TEXT"),
    ("show_shortcut_icon", "SHORTCUT"),
    ("show_comet_icon", "COMET"),
    ("show_chrome_icon", "CHROME"),
):
    button = small_button(
        settings_row2,
        f"{label}: {'ON' if icon_visibility[key] else 'OFF'}",
        lambda setting=key, title=label: toggle_icon_visibility(
            setting, title, icon_toggle_buttons[setting]
        ),
        "#0e7490" if icon_visibility[key] else "#334155"
    )
    button.pack(side=LEFT, padx=3, pady=4)
    icon_toggle_buttons[key] = button

title_shortcuts_button = small_button(
    settings_row3,
    f"TITLE SHORTCUTS: {'ON' if show_title_shortcuts else 'OFF'}",
    toggle_title_shortcuts,
    "#0e7490" if show_title_shortcuts else "#334155"
)
title_shortcuts_button.pack(side=LEFT, padx=3, pady=4)

transparency_label = Label(settings_row2, text="Transparency", bg=PANEL, fg=TEXT, font=("Consolas", 9, "bold"))
transparency_label.pack(side=LEFT, padx=(12, 5), pady=4)

transparency_slider = Scale(
    settings_row2,
    from_=0.35,
    to=1.0,
    resolution=0.05,
    orient=HORIZONTAL,
    length=110,
    bg=PANEL,
    fg=TEXT,
    highlightthickness=0,
    command=lambda value: apply_opacity(value)
)
transparency_slider.set(window_opacity)
transparency_slider.pack(side=LEFT, padx=3, pady=4)

grid_area = Frame(root, bg=BG)
grid_area.pack(fill=BOTH, expand=True, padx=8, pady=(0, 8))

column_divider = Frame(
    grid_area,
    bg="#334155",
    cursor="sb_h_double_arrow",
    width=ITEM_SECTION_DIVIDER_WIDTH
)
column_divider.bind("<Button-1>", start_item_section_resize)
column_divider.bind("<B1-Motion>", resize_item_section)
column_divider.bind("<ButtonRelease-1>", finish_item_section_resize)

item_header_cell = Frame(grid_area, bg=BG)
item_header_cell.grid(row=0, column=0, padx=2, pady=3, sticky="ew")
item_header_cell.grid_propagate(False)
item_header_cell.columnconfigure(0, weight=1)

item_head = Label(
    item_header_cell,
    text="ITEM",
    bg=BG,
    fg=MUTED,
    font=("Consolas", font_size, "bold"),
    anchor="w"
)
item_head.grid(row=0, column=0, sticky="ew")

header_ahk_buttons = []
for index, symbol in enumerate(("▤", "◉", "✎")):
    button = Button(
        item_header_cell,
        text=symbol,
        command=lambda shortcut_index=index: open_header_shortcut(shortcut_index),
        bg=CARD,
        fg=NEON,
        activebackground="#155e75",
        relief="flat",
        font=("Segoe UI Symbol", 9),
        width=2,
        cursor="hand2"
    )
    button.grid(row=0, column=index + 1, padx=(2, 0))
    button.bind(
        "<Button-3>",
        lambda event, shortcut_index=index: show_header_ahk_menu(
            event, shortcut_index
        )
    )
    add_tooltip(button, lambda shortcut_index=index: header_file_tooltip(shortcut_index))
    header_ahk_buttons.append(button)

item_header_cell.configure(
    height=max(
        item_head.winfo_reqheight(),
        *(button.winfo_reqheight() for button in header_ahk_buttons)
    )
)
layout_title_shortcuts()

for name in data["columns"]:
    add_column(name)

for row in data["rows"]:
    add_row(
        row.get("item", ""),
        row.get("ticks", []),
        row.get("ahk_path", LEGACY_AHK_PATH),
        row.get("comet_profile", LEGACY_COMET_PROFILE),
        row.get("note", ""),
        row.get("note_font_size"),
        row.get("chrome_profile", "")
    )

resize_corner = Frame(root, bg=NEON, cursor="bottom_right_corner")
resize_corner.place(relx=1.0, rely=1.0, anchor="se", width=10, height=10)

def start_resize(event):
    root.resize_start_x = event.x_root
    root.resize_start_y = event.y_root
    root.resize_start_w = root.winfo_width()
    root.resize_start_h = root.winfo_height()

def do_resize(event):
    minimum_width, minimum_height = root.minsize()
    new_w = max(minimum_width, root.resize_start_w + (event.x_root - root.resize_start_x))
    new_h = max(minimum_height, root.resize_start_h + (event.y_root - root.resize_start_y))
    root.geometry(f"{new_w}x{new_h}")
    save_settings()

resize_corner.bind("<Button-1>", start_resize)
resize_corner.bind("<B1-Motion>", do_resize)

root.mainloop()