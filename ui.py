import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import subprocess
import os

# Import custom logic modules
import storage
import downloader

class ASPU_DownloadManager_UI:
    def __init__(self, root):
        self.root = root
        self.root.title("ASPU Download Manager - IDM Pro (Modular)")
        self.root.geometry("850x550")
        self.root.configure(bg="#f0f0f0")

        # Initialize the Downloader Engine from downloader.py
        self.engine = downloader.DownloadEngine()
        self.current_url = ""

        self._setup_ui()
        self._load_history_to_view()

    def _setup_ui(self):
        """Creates the visual elements."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 9))
        style.configure("TProgressbar", thickness=15, background='#2ecc71')

        # Toolbar
        toolbar = tk.Frame(self.root, bg="#ffffff", height=45, bd=1, relief="flat")
        toolbar.pack(side="top", fill="x")

        btn_style = {"bg": "#ffffff", "relief": "flat", "font": ("Segoe UI", 9), "padx": 12}

        tk.Button(toolbar, text="➕ Add URL", command=self.add_url_popup, **btn_style).pack(side="left", padx=5, pady=5)
        tk.Button(toolbar, text="▶ Start", command=self.start_download, **btn_style).pack(side="left", padx=5)
        tk.Button(toolbar, text="⏸ Pause", command=self.engine.pause, **btn_style).pack(side="left", padx=5)
        tk.Button(toolbar, text="🛑 Cancel", command=self.engine.cancel, **btn_style).pack(side="left", padx=5)

        # Main Table (Treeview)
        self.tree_frame = tk.Frame(self.root)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Name", "Status", "Size", "Progress")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        self.tree.pack(fill="both", expand=True, side="left")
        
        scroller = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroller.set)
        scroller.pack(side="right", fill="y")

        # Status Bar
        self.status_frame = tk.LabelFrame(self.root, text=" Task Control ", bg="#ffffff", padx=10, pady=10)
        self.status_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_status = tk.Label(self.status_frame, text="System Ready", bg="#ffffff", font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w")

        self.progress = ttk.Progressbar(self.status_frame, orient="horizontal", mode="determinate", style="TProgressbar")
        self.progress.pack(fill="x", pady=5)

    def add_url_popup(self):
        url = simpledialog.askstring("New Download", "URL Address:")
        if url:
            self.current_url = url
            filename = url.split('/')[-1] if '/' in url else "Unknown_File"
            self.lbl_status.config(text=f"Queued: {filename}")

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

    def start_download(self):
        if not self.current_url:
            messagebox.showwarning("System", "Please add a URL first!")
            return

        # Define Callbacks to update UI from the thread safely
        callbacks = {
            'on_progress': lambda p: self.root.after(0, lambda: self.progress.configure(value=p)),
            'on_status': lambda t: self.root.after(0, lambda: self.lbl_status.config(text=t)),
            'on_finish': self._on_finish_callback,
            'on_error': self._on_error_callback,
            'on_pause': lambda: self.root.after(0, lambda: messagebox.showinfo("Paused", "Download paused.")),
            'on_cancel': self._on_cancel_callback
        }

        # Send work to the downloader module
        self.engine.start_download(self.current_url, callbacks)

    # --- UI Update Helpers ---
    
    def _on_finish_callback(self, filename, save_path, total_size):
        def _update():
            storage.save_entry(filename, total_size)
            self._load_history_to_view()
            self.progress.configure(value=0)
            messagebox.showinfo("Success", f"Download Finished!\nPath: {save_path}")
            self.open_file(save_path)
        self.root.after(0, _update)

    def _on_error_callback(self, error_msg):
        def _update():
            self.progress.configure(value=0)
            messagebox.showerror("Error", f"Connection Failed:\n{error_msg}")
        self.root.after(0, _update)

    def _on_cancel_callback(self):
        def _update():
            self.progress.configure(value=0)
            messagebox.showwarning("Abort", "Download deleted successfully.")
        self.root.after(0, _update)

    def open_file(self, path):
        if sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path])