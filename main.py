import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import subprocess
import threading
import sys

class ASPU_DownloadManager:
    def __init__(self, root):
        # Initialize the main window settings
        self.root = root
        self.root.title("ASPU Download Manager")
        self.root.geometry("600x450")
    
        # State tracking: flags to control the download flow and cancellation
        self.downloading = False       # True if a download is currently running
        self.stop_requested = False    # Set to True when the 'Cancel' button is clicked

        # 1. URL Input (Requirement #1)
        tk.Label(root, text="Enter URL:", font=("Arial", 10, "bold")).pack(pady=5)
        self.url_entry = tk.Entry(root, width=70)
        self.url_entry.pack(pady=5)

        # 2. Save Path (Requirement #3)
        self.save_path = ""
        self.path_btn = tk.Button(root, text="Select Save Location", command=self.select_dest)
        self.path_btn.pack(pady=5)
        self.path_label = tk.Label(root, text="No location selected", fg="gray")
        self.path_label.pack()

        # 3. File Info (Requirement #5)
        self.info_frame = tk.LabelFrame(root, text="File Information", padx=10, pady=10)
        self.info_frame.pack(pady=10, fill="x", padx=20)
        
        self.file_name_lbl = tk.Label(self.info_frame, text="Name: N/A")
        self.file_name_lbl.pack(anchor="w")
        
        self.file_size_lbl = tk.Label(self.info_frame, text="Size: 0 MB")
        self.file_size_lbl.pack(anchor="w")

        # 4. Progress Bar (Requirement #4)
        tk.Label(root, text="Progress:").pack()
        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        # 5. Control Buttons
        self.start_btn = tk.Button(root, text="Start Download", bg="green", fg="white", command=self.start_thread)
        self.start_btn.pack(pady=10)

        self.cancel_btn = tk.Button(root, text="Cancel Download", bg="red", fg="white", command=self.cancel_download)
        self.cancel_btn.pack(pady=10)

    def select_dest(self):
        """Allows user to pick where to save the file [cite: 15]"""
        path = filedialog.askdirectory()
        if path:
            self.save_path = path
            self.path_label.config(text=f"Save to: {path}", fg="black")

    def start_thread(self):
        """
        Validates inputs and starts the download in a 'Thread'.
        This prevents the GUI from freezing while the file is being downloaded.
        """
        if self.downloading:
            return # Don't start a second download if one is already running
        
        url = self.url_entry.get()
        if not url or not self.save_path:
            messagebox.showerror("Error", "Please provide a URL and select a save location.")
            return

        # Update state and disable button to prevent double-clicks
        self.downloading = True
        self.stop_requested = False
        self.start_btn.config(state="disabled")
        
        # Create a background worker (Thread)
        download_thread = threading.Thread(target=self.download_file, args=(url,))
        download_thread.daemon = True # Thread closes if the main window is closed
        download_thread.start()

    def download_file(self, url):
        """
        The core download logic. 
        Requests data in chunks and updates the progress bar.
        """
        try:
            # stream=True allows us to download the file piece by piece
            response = requests.get(url, stream=True, timeout=10)
            total_size = int(response.headers.get('content-length', 0))
            
            # Extract filename from URL or use a default
            filename = url.split("/")[-1] or "downloaded_file"
            full_path = os.path.join(self.save_path, filename)

            # Update UI labels using .after() for thread safety
            self.root.after(0, lambda: self.file_name_lbl.config(text=f"Name: {filename}"))
            self.root.after(0, lambda: self.file_size_lbl.config(text=f"Size: {total_size // (1024*1024)} MB"))

            downloaded = 0
            with open(full_path, 'wb') as f:
                # Process the file in 8KB chunks
                for chunk in response.iter_content(chunk_size=8192):
                    if self.stop_requested:
                        break # Exit loop if user clicked Cancel
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Calculate and update progress bar
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            self.root.after(0, lambda p=percent: self.progress.configure(value=p))

            # Handle completion or cancellation
            if self.stop_requested:
                f.close()
                if os.path.exists(full_path):
                    os.remove(full_path) # Delete the unfinished file
                messagebox.showwarning("Cancelled", "Download was cancelled.")
            else:
                messagebox.showinfo("Success", "Download Completed!")
                self.open_file(full_path) # Auto-open file on finish

        except Exception as e:
            messagebox.showerror("Error", f"Failed to download: {e}")
        
        finally:
            # Reset the UI state regardless of success or failure
            self.downloading = False
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
            self.root.after(0, lambda: self.progress.configure(value=0))

    def cancel_download(self):
        """Triggers the cancellation flag used in the download loop."""
        if self.downloading:
            self.stop_requested = True

    def open_file(self, path):
        """ Detects the User's Operating System and opens the downloaded file using the default system application."""
        if sys.platform == "win32": # Windows
            os.startfile(path)
        elif sys.platform == "darwin": # macOS
            subprocess.run(["open", path])
        else: # Linux/Unix
            subprocess.run(["xdg-open", path])

# --- Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ASPU_DownloadManager(root)
    root.mainloop()


# --- Test URLs ---
""" URL1: http://speedtest.tele2.net/10MB.zip
    URL2: http://speedtest.tele2.net/100MB.zip
    URL3: https://raw.githubusercontent.com/py-pdf/sample-files/main/README.md
"""