
import os
import shutil
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import simpledialog, messagebox



# ==========================
# CONFIG & GLOBAL CONSTANTS
# ==========================

# Where your notes live on disk (change if you like).
BASE_DIR = os.path.expanduser("~/RaccoonNotes")
APP_DIR = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(APP_DIR, "raccoon_icon.png")

# Toggle to True to see detailed prints about what the app is doing.
DEBUG = False

# Placeholder colors (swap later for your raccoon textures)
COLOR_BG = "#264A2A"        #4b543a
COLOR_HEADER = "#232727"    #232727
COLOR_SURFACE = "white"
button_colors = "#1b1c07"

# ==========================
# FILESYSTEM (TXT) BACKEND
# ==========================

def debug(msg: str):
    """Print debug info if DEBUG is True."""
    if DEBUG:
        print(f"[DEBUG] {msg}")

def ensure_base_dir():
    """Create the base directory if it does not exist."""
    if not os.path.isdir(BASE_DIR):
        debug(f"Creating BASE_DIR at: {BASE_DIR}")
        os.makedirs(BASE_DIR, exist_ok=True)

def list_stashes():
    """
    Return a sorted list of stash names.
    A stash is a *directory* inside BASE_DIR (files are ignored).
    """
    ensure_base_dir()
    entries = []
    for name in os.listdir(BASE_DIR):
        p = os.path.join(BASE_DIR, name)
        if os.path.isdir(p):
            entries.append(name)
    entries.sort(key=str.casefold)
    debug(f"Stashes found: {entries}")
    return entries

def list_notes(stash_name: str):
    """
    Return a sorted list of note filenames (stems) in this stash.
    Only files ending with .txt are considered notes.
    """
    stash_path = os.path.join(BASE_DIR, stash_name)
    if not os.path.isdir(stash_path):
        debug(f"list_notes: Stash path missing (creating): {stash_path}")
        os.makedirs(stash_path, exist_ok=True)

    notes = []
    for fname in os.listdir(stash_path):
        if fname.lower().endswith(".txt"):
            notes.append(os.path.splitext(fname)[0])  # title without .txt
    notes.sort(key=str.casefold)
    debug(f"Notes in '{stash_name}': {notes}")
    return notes

def safe_title_to_filename(title: str) -> str:
    """
    Convert a user-entered title into a safe filename.
    Linux is liberal, but we still:
      - strip leading/trailing whitespace
      - replace '/' with '-' (avoid subdirectories)
      - disallow leading dot to avoid hidden files
      - collapse weird whitespace
    We keep spaces; Ubuntu handles them fine.
    """
    t = title.strip().replace("/", "-")
    if t.startswith("."):
        t = t.lstrip(".")
    # fall back if empty
    if not t:
        t = "Untitled"
    return t

def unique_filename(stash_name: str, base_stem: str) -> str:
    """
    Ensure we don't overwrite an existing file.
    If 'Note.txt' exists, try 'Note (1).txt', 'Note (2).txt', etc.
    Returns a *filename with extension*, not a full path.
    """
    stash_path = os.path.join(BASE_DIR, stash_name)
    stem = base_stem
    candidate = f"{stem}.txt"
    i = 1
    while os.path.exists(os.path.join(stash_path, candidate)):
        candidate = f"{stem} ({i}).txt"
        i += 1
    return candidate

def create_stash(stash_title: str):
    """Make a new stash directory. (No duplicate checks; last write wins.)"""
    name = safe_title_to_filename(stash_title)
    path = os.path.join(BASE_DIR, name)
    debug(f"create_stash -> {path}")
    os.makedirs(path, exist_ok=True)
    return name

def delete_stash(stash_name: str):
    """
    Recursively remove a stash directory and all notes inside it.
    WARNING: No confirmation by design (minimal app). Be careful.
    """
    path = os.path.join(BASE_DIR, stash_name)
    debug(f"delete_stash -> {path}")
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)

def read_note(stash_name: str, note_title: str):
    """
    Load note content from disk.
    - stash_name: folder name
    - note_title: filename stem (without .txt)
    Returns: content (str)
    """
    path = os.path.join(BASE_DIR, stash_name, f"{note_title}.txt")
    debug(f"read_note -> {path}")
    if not os.path.isfile(path):
        return ""  # If it got deleted outside, just show empty
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()

def write_note(stash_name: str, note_title: str, content: str):
    """
    Save note content to disk (overwrites existing).
    """
    path = os.path.join(BASE_DIR, stash_name, f"{note_title}.txt")
    debug(f"write_note -> {path} (len={len(content)})")
    # Ensure stash exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def create_note(stash_name: str, note_title: str):
    """
    Create a new empty note in the given stash.
    - Ensures unique filename if collision.
    Returns the actual note title (may have (1), (2) suffix).
    """
    safe = safe_title_to_filename(note_title)
    fname = unique_filename(stash_name, safe)  # adds .txt
    final_title = os.path.splitext(fname)[0]
    path = os.path.join(BASE_DIR, stash_name, fname)
    debug(f"create_note -> {path}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("")  # start empty
    return final_title

def delete_note(stash_name: str, note_title: str):
    """Remove a single note file (no confirmation)."""
    path = os.path.join(BASE_DIR, stash_name, f"{note_title}.txt")
    debug(f"delete_note -> {path}")
    if os.path.isfile(path):
        os.remove(path)

def rename_note(stash_name: str, old_title: str, new_title: str):
    """
    Rename a note file if the title changed.
    If the target name exists, we create a unique variant to avoid overwrite.
    Returns the *final* note title after rename (may include (1) suffix).
    """
    if old_title == new_title:
        return old_title

    old_path = os.path.join(BASE_DIR, stash_name, f"{old_title}.txt")
    base = safe_title_to_filename(new_title)
    new_fname = unique_filename(stash_name, base)
    new_path = os.path.join(BASE_DIR, stash_name, new_fname)
    debug(f"rename_note -> {old_path}  ==>  {new_path}")

    # If original file vanished externally, just treat as a new file.
    if not os.path.isfile(old_path):
        with open(new_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("")  # empty new file
    else:
        os.rename(old_path, new_path)

    return os.path.splitext(new_fname)[0]


# ==========================
# UI lAYER
# ==========================


class RaccoonNotesTXT_Grid:
    def __init__(self, root):
        self.root = root
        self.root.title("Raccoon Notes")
        self.root.geometry("800x600")

        icon_path = os.path.join(APP_DIR, "raccoon_icon.png")
        self.root.iconphoto(True, tk.PhotoImage(file=icon_path))

        # give weight to columns to configure button placements.
        for i in range(50):  # or however many rows you expect
            self.root.grid_rowconfigure(i, weight=1)

        for i in range(10):
            self.root.grid_columnconfigure(i, weight=1)

        img = Image.open(os.path.join(APP_DIR, "forest_raccoons_adventure_bg.png")).resize((800, 600))
        self.bg_image = ImageTk.PhotoImage(img)
        self.bg_label = tk.Label(self.root, image=self.bg_image)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.current_stash = None
        self.current_note = None
        self.title_entry = None
        self.text_area = None

        ensure_base_dir()
        self.view_home()


    def clear_window(self):
        for w in self.root.winfo_children():
            if w != self.bg_label:
                w.destroy()

    def view_home(self):
        self.clear_window()
        tk.Label(self.root, text="My Stashes", fg="white", bg=COLOR_HEADER, padx=6, pady=6).grid(row=0, column=3, columnspan=4, sticky="ew")

        row_num = 1
        for name in list_stashes():
            tk.Button(self.root, text=name, bg=COLOR_BG, fg="white", highlightbackground="black", command=lambda n=name: self.view_stash(n)).grid(row=row_num, column=4, sticky="ew", padx=4, pady=2)
            tk.Button(self.root, text="Delete", bg=COLOR_BG, fg="white", highlightbackground="black", command=lambda n=name: self.confirm_delete_stash(n) or self.view_home()).grid(row=row_num, column=5, sticky="ew", padx=4, pady=2)
            row_num += 1

        tk.Button(self.root, text="+ New Stash", bg=COLOR_BG, highlightbackground="black", fg="white", command=self.prompt_new_stash).grid(row=row_num, column=4, columnspan=2, pady=10)

    def confirm_delete_stash(self, stash_name):
        """Ask user before deleting a stash and all its notes."""
        confirm = messagebox.askyesno("Delete Stash",
                                      f"Are you sure you want to delete the stash '{stash_name}'?\nAll notes inside will be permanently removed.")
        if confirm:
            delete_stash(stash_name)
            self.view_home()

    def prompt_new_stash(self):
        title = simpledialog.askstring("New Stash", "Enter stash title:")
        if title:
            create_stash(title)
            self.view_home()

    def view_stash(self, stash_name):
        self.clear_window()

        tk.Label(self.root, text=f"Stash: {stash_name}", bg=COLOR_HEADER, fg="white", padx=6, pady=6).grid(row=0, column=1, columnspan=4, sticky="ew")

        row_num = 1
        for note in list_notes(stash_name):
            tk.Button(self.root, text=note, bg=COLOR_BG, fg="white", highlightbackground="black", command=lambda n=note: self.view_note(stash_name, n)).grid(row=row_num, column=1, sticky="ew", padx=4, pady=2)
            tk.Button(self.root, text="Delete", bg=COLOR_BG, fg="white", highlightbackground="black", command=lambda n=note: self.confirm_delete_note(stash_name, n) or self.view_stash(stash_name)).grid(row=row_num, column=2, sticky="ew", padx=4, pady=2)
            row_num += 1

        tk.Button(self.root, text="+ New Note", bg=COLOR_BG, fg="white", highlightbackground="black", command=lambda: self.prompt_new_note(stash_name)).grid(row=row_num, column=1, columnspan=1, pady=10)
        tk.Button(self.root, text="Back to Home", bg=COLOR_BG, fg="white", highlightbackground="black",
                  command=self.view_home).grid(row=50, column=0, columnspan=1, pady=10)

    def confirm_delete_note(self, stash_name, note_title):
        """Ask user before deleting a note file."""
        confirm = messagebox.askyesno(
            "Delete Note",f"Are you sure you want to delete the note '{note_title}'?")
        if confirm:
            delete_note(stash_name, note_title)
            self.view_stash(stash_name)

    def prompt_new_note(self, stash_name):
        title = simpledialog.askstring("New Note", "Enter note title:")
        if title:
            create_note(stash_name, title)
            self.view_stash(stash_name)

    def view_note(self, stash_name, note):
        self.clear_window()
        tk.Label(self.root, fg="white", text=f"{stash_name} → {note}", bg=COLOR_HEADER).grid(row=0, column=0, columnspan=10, sticky="ew")

        self.title_entry = tk.Entry(self.root, borderwidth=5)
        self.title_entry.insert(0, note)
        self.title_entry.grid(row=1, column=0, columnspan=10, sticky="ew", padx=8, pady=6)

        self.text_area = tk.Text(self.root, borderwidth=5)
        self.text_area.grid(row=2, column=0, columnspan=10, rowspan=40, sticky="nsew", padx=8, pady=6)
        self.text_area.insert("1.0", read_note(stash_name, note))

        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        tk.Button(self.root, text="Save and Exit", command=lambda: self.save_and_back(stash_name, note)).grid(row=50, column=0, columnspan=2, pady=10)

    def save_and_back(self, stash, old_note):
        new_title = self.title_entry.get().strip() or "Untitled"
        final_title = rename_note(stash, old_note, new_title)
        write_note(stash, final_title, self.text_area.get("1.0", "end-1c"))
        self.view_stash(stash)

# ==========================
# MAIN
# ==========================

if __name__ == "__main__":
    ensure_base_dir()
    root = tk.Tk()
    app = RaccoonNotesTXT_Grid(root)
    root.mainloop()