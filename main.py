import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog # Added simpledialog
from pathlib import Path
import requests 
import os
import subprocess
import threading
import sys
import json

class ASPU_DownloadManager_Pro:
    def __init__(self, root):
        self.root = root
        self.root.title("ASPU Download Manager - IDM Pro")
        self.root.geometry("850x550")
        self.root.configure(bg="#f0f0f0")

        self.downloading = False
        self.stop_requested = False
        self.cancel_requested = False
        self.current_url = ""

        # UI Styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 9))
        style.configure("TProgressbar", thickness=15, background='#2ecc71')

        # Toolbar
        toolbar = tk.Frame(root, bg="#ffffff", height=45, bd=1, relief="flat")
        toolbar.pack(side="top", fill="x")

        btn_style = {"bg": "#ffffff", "relief": "flat", "font": ("Segoe UI", 9), "padx": 12}
        
        self.add_btn = tk.Button(toolbar, text="➕ Add URL", command=self.add_url_popup, **btn_style)
        self.add_btn.pack(side="left", padx=5, pady=5)

        self.start_btn = tk.Button(toolbar, text="▶ Start", command=self.run_threaded_download, **btn_style)
        self.start_btn.pack(side="left", padx=5)

        self.pause_btn = tk.Button(toolbar, text="⏸ Pause", command=self.pause_download, **btn_style)
        self.pause_btn.pack(side="left", padx=5)

        self.stop_btn = tk.Button(toolbar, text="🛑 Cancel", command=self.cancel_download, **btn_style)
        self.stop_btn.pack(side="left", padx=5)

        # Main Table (Treeview)
        self.tree_frame = tk.Frame(root)
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

        # Bottom Status Frame
        self.status_frame = tk.LabelFrame(root, text=" Task Control ", bg="#ffffff", padx=10, pady=10)
        self.status_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_status = tk.Label(self.status_frame, text="System Ready", bg="#ffffff", font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w")

        self.progress = ttk.Progressbar(self.status_frame, orient="horizontal", mode="determinate", style="TProgressbar")
        self.progress.pack(fill="x", pady=5)

        self.load_history()

    def add_url_popup(self):
        # Fixed: using simpledialog instead of filedialog for askstring
        url = simpledialog.askstring("New Download", "URL Address:")
        if url:
            self.current_url = url
            filename = url.split('/')[-1] if '/' in url else "Unknown_File"
            self.lbl_status.config(text=f"Queued: {filename}")

    def run_threaded_download(self):
        if not self.current_url:
            messagebox.showwarning("System", "Please add a URL first!")
            return
        if self.downloading: return
        
        self.downloading = True
        self.stop_requested = False
        self.cancel_requested = False
        
        thread = threading.Thread(target=self.core_download, args=(self.current_url,))
        thread.daemon = True
        thread.start()

    def core_download(self, url):
        try:
            filename = url.split("/")[-1] or "downloaded_file"
            save_dir = os.path.join(Path.home(), "Downloads")
            save_path = os.path.join(save_dir, filename)
            
            existing_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
            headers = {"Range": f"bytes={existing_size}-"}
            
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            total_size = int(response.headers.get('content-length', 0)) + existing_size

            self.root.after(0, lambda: self.lbl_status.config(text=f"Downloading: {filename}"))

            downloaded = existing_size
            with open(save_path, 'ab') as f:
                for chunk in response.iter_content(chunk_size=1024*16):
                    if self.stop_requested or self.cancel_requested: break
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / total_size) * 100
                        self.root.after(0, lambda v=percent: self.progress.configure(value=v))

            if self.cancel_requested:
                f.close()
                if os.path.exists(save_path): os.remove(save_path)
                messagebox.showwarning("Abort", "Download deleted successfully.")
            elif self.stop_requested:
                messagebox.showinfo("Paused", "Download paused. Resume later.")
            else:
                self.save_to_history(filename, total_size)
                self.root.after(0, self.load_history)
                messagebox.showinfo("Success", f"Download Finished!\nPath: {save_path}")
                self.open_file(save_path)

        except Exception as e:
            messagebox.showerror("Error", f"Connection Failed:\n{str(e)}")
        finally:
            self.downloading = False
            self.root.after(0, lambda: self.progress.configure(value=0))

    def pause_download(self): self.stop_requested = True
    def cancel_download(self): self.cancel_requested = True

    def open_file(self, path):
        if sys.platform == "win32": os.startfile(path)
        else: subprocess.run(["xdg-open", path])

    def save_to_history(self, name, size):
        data = []
        if os.path.exists("history.json"):
            with open("history.json", "r") as f: data = json.load(f)
        data.append({"Name": name, "Status": "Finished", "Size": f"{size//(1024*1024)} MB", "Progress": "100%"})
        with open("history.json", "w") as f: json.dump(data, f, indent=4)

    def load_history(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        if os.path.exists("history.json"):
            with open("history.json", "r") as f:
                history_list = json.load(f)
                for item in history_list:
                    self.tree.insert("", "end", values=(item["Name"], item["Status"], item["Size"], item["Progress"]))

if __name__ == "__main__":
    root = tk.Tk()
    app = ASPU_DownloadManager_Pro(root)
    root.mainloop()
    