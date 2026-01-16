import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sys
import subprocess
import os
from pathlib import Path

# Import custom logic modules
import storage
import downloader

"""
This class manages the graphical user interface for the download manager.
- This class contains all UI elements, event handlers, and integrates with the DownloadEngine.
- All meet-in-the-middle logic between UI and backend is handled here.
"""

class ASPU_DownloadManager_UI:
    def __init__(self, root):
        self.root = root
        self.root.title("ASPU Download Manager - IDM Pro (Modular)")
        self.root.geometry("850x550")
        self.root.configure(bg="#f0f0f0")

        self.engine = downloader.DownloadEngine()
        self.current_url = "" # Stores the last added URL for convenience

        self._setup_ui()
        self._load_history_to_view()

    def _setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=35, font=("Segoe UI", 9))
        style.configure("TProgressbar", thickness=15, background='#2ecc71')

        toolbar = tk.Frame(self.root, bg="#ffffff", height=45, bd=1, relief="flat")
        toolbar.pack(side="top", fill="x")

        btn_style = {"bg": "#ffffff", "relief": "flat", "font": ("Segoe UI", 9), "padx": 12}

        tk.Button(toolbar, text="➕ Add URL", command=self.add_url_popup, **btn_style).pack(side="left", padx=5, pady=5)
        tk.Button(toolbar, text="▶ Start", command=self.start_selected_in_GUI, **btn_style).pack(side="left", padx=5)
        tk.Button(toolbar, text="⏸ Pause", command=self.pause_selected_in_GUI, **btn_style).pack(side="left", padx=5)
        tk.Button(toolbar, text="🛑 Cancel", command=self.cancel_selected_in_GUI, **btn_style).pack(side="left", padx=5)
        tk.Button(toolbar, text="⚙️ Settings", command=self.open_settings , **btn_style).pack(side="left", padx=5)

        self.tree_frame = tk.Frame(self.root)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Name", "Status", "Size", "Progress")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings")
        # Bind selection event: Calls update_task_control whenever a user clicks a row
        self.tree.bind("<<TreeviewSelect>>", self.update_task_control)
        
        self.tree.heading("Name", text="File Name")
        self.tree.column("Name", width=250, stretch=True)
        self.tree.heading("Status", text="Status")
        self.tree.column("Status", width=120, anchor="center")
        self.tree.heading("Size", text="Size")
        self.tree.column("Size", width=100, anchor="center")
        self.tree.heading("Progress", text="Progress")
        self.tree.column("Progress", width=200, stretch=True) 
        
        self.tree.pack(fill="both", expand=True, side="left")
        
        scroller = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroller.set)
        scroller.pack(side="right", fill="y")

        self.status_frame = tk.LabelFrame(self.root, text=" Task Control ", bg="#ffffff", padx=10, pady=10)
        self.status_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_status = tk.Label(self.status_frame, text="System Ready", bg="#ffffff", font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w")

        self.progress = ttk.Progressbar(self.status_frame, orient="horizontal", mode="determinate", style="TProgressbar")
        self.progress.pack(fill="x", pady=5)

    def add_url_popup(self):
        url = simpledialog.askstring("New Download", "URL Address:")
        if url:
            filename = url.split('/')[-1] if '/' in url else "Unknown_File"
            # Requirement: When URL is added, it shows up in treeview immediately
            # We store the URL in a custom 'tag' named 'url' for later retrieval
            item_id = self.tree.insert("", "end", values=(filename, "Queued", "---", "[░░░░░░░░░░] 0%"), tags=("url_storage",))
            # Tag the item with the actual URL so Start can find it later
            self.tree.item(item_id, values=(filename, "Queued", "---", "[░░░░░░░░░░] 0%"))
            # Storing the URL in the item's private data (tags aren't just for PIDs!)
            self.tree.set(item_id, "Name", filename)
            self.tree.item(item_id, tags=("queued", url)) 
            self.lbl_status.config(text=f"Added to list: {filename}")

    def start_selected_in_GUI(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("System", "Please select a file from the list to start!")
            return

        item_id = selected_item[0]
        item_tags = self.tree.item(item_id, "tags")
        
        # Retrieve the URL from our storage tag
        # We assume the second tag is the URL (based on add_url_popup)
        url = item_tags[1] 

        # Define Callbacks
        callbacks = {
            'on_progress': lambda p: self.root.after(0, lambda: self._update_row_progress(item_id, p)),
            'on_status': lambda t: self.root.after(0, lambda: self.tree.set(item_id, "Status", t)),
            'on_finish': lambda f, p, s: self._on_finish_callback(item_id, f, p, s),
            'on_error': lambda e: self._on_error_callback(item_id, e),
            'on_pause': lambda: self.tree.set(item_id, "Status", "Paused"),
            'on_cancel': lambda: self._on_cancel_callback(item_id)
        }

        # Send work to engine
        pid = self.engine.start_download(url, callbacks)

        # Update tags to include the live PID so Pause/Cancel can work
        self.tree.item(item_id, tags=("active", url, pid))
        self.tree.set(item_id, "Status", "Downloading...")

    def _update_row_progress(self, item_id, percent):
        """Calculates text bar and updates the specific row."""
        bar_length = 10
        filled = int(percent / 10)
        bar_str = "█" * filled + "░" * (bar_length - filled)
        display_text = f"[{bar_str}] {int(percent)}%"
        
        # 1. Always update the table row
        self.tree.set(item_id, "Progress", display_text)
        
        # 2. Update the Task Bar ONLY if this row is the one the user is looking at
        selected = self.tree.selection()
        if selected and selected[0] == item_id:
            self.progress.configure(value=percent)
            self.lbl_status.config(text=f"Downloading: {int(percent)}%")

    def update_task_control(self, event=None):
        """Updates the bottom Task Bar based on the currently selected row."""
        selected = self.tree.selection()
        
        if not selected:
            self.progress.configure(value=0)
            self.lbl_status.config(text="System Ready")
            return

        item_id = selected[0]
        item_data = self.tree.item(item_id, "values")
        
        # item_data indices: 0:Name, 1:Status, 2:Size, 3:Progress
        status_text = item_data[1]
        progress_text = item_data[3] # Looks like "[██░░] 20%"

        # Extract the number from the progress text using split
        try:
            # Splits "[██░░] 20%" at the space and removes the %
            percent_val = float(progress_text.split()[-1].replace('%', ''))
        except (ValueError, IndexError):
            percent_val = 0

        # Update the widgets
        self.lbl_status.config(text=f"{item_data[0]} - {status_text}")
        self.progress.configure(value=percent_val)

    def cancel_selected_in_GUI(self):
        selected_item = self.tree.selection() 
        if not selected_item:
            messagebox.showinfo("Selection", "Please select a download to cancel.")
            return
        
        item_id = selected_item[0]
        tags = self.tree.item(item_id, "tags")
        
        # If it's active, it will have a PID at index 2
        if len(tags) > 2:
            pid = tags[2]
            self.engine.cancel_download(pid)
        
        self.tree.delete(item_id)

    def pause_selected_in_GUI(self):
        selected_item = self.tree.selection() 
        if not selected_item:
            messagebox.showinfo("Selection", "Please select a download to pause.")
            return
        
        item_id = selected_item[0]
        tags = self.tree.item(item_id, "tags")
        
        if len(tags) > 2:
            pid = tags[2]
            self.engine.pause_download(pid)
            self.tree.set(item_id, "Status", "Paused")

    # --- UI Update Helpers ---
    
    def _on_finish_callback(self, item_id, filename, save_path, total_size):
        def _update():
            self.tree.set(item_id, "Status", "Finished")
            self.tree.set(item_id, "Progress", "[██████████] 100%")
            # Formatting size to MB for better readability
            self.tree.set(item_id, "Size", f"{total_size / (1024*1024):.2f} MB")
            
            storage.save_entry(filename, total_size)
            if storage.load_settings().get("open_on_finish", True):
                self.open_file(save_path)
            messagebox.showinfo("Success", f"Download Finished: {filename}")
        self.root.after(0, _update)

    def _on_error_callback(self, item_id, error_msg):
        def _update():
            self.tree.set(item_id, "Status", "Error")
            messagebox.showerror("Error", f"Failed: {error_msg}")
        self.root.after(0, _update)

    def _on_cancel_callback(self, item_id):
        def _update():
            if self.tree.exists(item_id):
                self.tree.delete(item_id)
            self.progress.configure(value=0)
            self.lbl_status.config(text="Download Canceled & Deleted")
        self.root.after(0, _update)

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("400x300")
        settings_win.configure(bg="#f0f0f0", padx=20, pady=20)
        settings_win.transient(self.root)
        settings_win.grab_set()

        # 1. Load current settings from JSON to show in the UI
        current_data = storage.load_settings()
        
        # Create local UI variables
        var_open_finish = tk.BooleanVar(value=current_data.get("open_on_finish", False))
        var_save_path = tk.StringVar(value=current_data.get("save_path", os.path.join(Path.home(), "Downloads")))

        # --- UI Elements ---
        tk.Label(settings_win, text="Post-Download Action:", font=("Segoe UI", 10, "bold"), bg="#f0f0f0").pack(anchor="w")
        tk.Radiobutton(settings_win, text="Open files automatically", variable=var_open_finish, value=True, bg="#f0f0f0").pack(anchor="w")
        tk.Radiobutton(settings_win, text="Don't open files automatically", variable=var_open_finish, value=False, bg="#f0f0f0").pack(anchor="w")

        tk.Frame(settings_win, height=1, bg="#cccccc").pack(fill="x", pady=15)
        tk.Label(settings_win, text="Default Save Location:", font=("Segoe UI", 10, "bold"), bg="#f0f0f0").pack(anchor="w")
        
        path_frame = tk.Frame(settings_win, bg="#f0f0f0")
        path_frame.pack(fill="x", pady=5)
        tk.Entry(path_frame, textvariable=var_save_path, state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def browse_path():
            path = filedialog.askdirectory()
            if path: var_save_path.set(path)
                
        tk.Button(path_frame, text="Browse...", command=browse_path).pack(side="right")

        # 2. Updated Save Logic
        def save_and_exit():
            new_settings = {
                "open_on_finish": var_open_finish.get(),
                "save_path": var_save_path.get()
            }
            storage.save_settings(new_settings)
            self.lbl_status.config(text="Settings updated successfully.")
            settings_win.destroy()

        tk.Button(settings_win, text="Save & Close", command=save_and_exit, 
                  bg="#2ecc71", fg="white", width=15).pack(pady=20)
    
    def _load_history_to_view(self):
        """Fetches data from storage.py and updates the table."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Load safely from storage module
        try:
            history = storage.load_history()
            for item in history:
                self.tree.insert("", "end", values=(item["Name"], item["Status"], item["Size"], item["Progress"]))
        except Exception as e:
            print(f"Error loading history: {e}")

    def open_file(self, path):
        if sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path])