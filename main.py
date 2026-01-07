import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import requests 
import os
import subprocess
import threading
import sys
import json

class ASPU_DownloadManager:
    def __init__(self, root):
        # Initialize the main window settings
        self.root = root
        self.root.title("ASPU Download Manager")
        self.root.geometry("600x450")
    
        # State tracking: flags to control the download flow and cancellation
        self.downloading = False       # True if a download is currently running
        self.cancel_requested = False    # Set to True when the 'Cancel' button is clicked
        self.stop_requested = False    # Set to True when the 'Stop' button is clicked

        # 1. URL Input (Requirement #1)
        tk.Label(root, text="Enter URL:", font=("Arial", 10, "bold")).pack(pady=5)
        self.url_entry = tk.Entry(root, width=70)
        self.url_entry.pack(pady=5)

        # 2. Save Path (Requirement #3)
        self.save_path = str(os.path.join(Path.home(), "Downloads")) # Default saving path
        self.path_btn = tk.Button(root, text="Select Save Location", command=self.select_dest)
        self.path_btn.pack(pady=5)
        self.path_label = tk.Label(root, text=f"Save to: {self.save_path}", fg="grey")
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
        self.history_btn = tk.Button(root, text="History", bg="gray", fg="black", command=self.show_history_window)
        self.history_btn.pack(pady=5)

        self.start_btn = tk.Button(root, text="Start Download", bg="green", fg="white", command=self.start_thread)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop Download", bg="orange", fg="white", command=self.stop_download)
        self.stop_btn.pack(pady=5)

        self.cancel_btn = tk.Button(root, text="Cancel Download", bg="red", fg="white", command=self.cancel_download)
        self.cancel_btn.pack(pady=5)

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
        self.cancel_requested = False
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
            # Extract filename from URL or use a default
            filename = url.split("/")[-1] or "downloaded_file"
            full_path = os.path.join(self.save_path, filename)
            
            # Check if file already exists and get its size to resume (if needed)
            existing_size = 0
            if os.path.exists(full_path):
                existing_size = os.path.getsize(full_path)

            # 3. Request only the missing part from the server
            # Header format: {"Range": "bytes=start-"}
            headers = {"Range": f"bytes={existing_size}-"}

            # stream=True allows us to download the file piece by piece
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            total_size = int(response.headers.get('content-length', 0)) + existing_size # Total size includes already downloaded part
            
            # Update UI labels using .after() for thread safety
            self.root.after(0, lambda: self.file_name_lbl.config(text=f"Name: {filename}"))
            self.root.after(0, lambda: self.file_size_lbl.config(text=f"Size: {total_size // (1024*1024)} MB"))

            downloaded = existing_size
            with open(full_path, 'ab') as f:
                # Process the file in 8KB chunks
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancel_requested or self.stop_requested:
                        break # Exit loop if user clicked Cancel or Stop
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Calculate and update progress bar
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            self.root.after(0, lambda p=percent: self.progress.configure(value=p))

            # Handle completion or cancellation
            if self.cancel_requested:
                f.close()
                if os.path.exists(full_path):
                    os.remove(full_path) # Delete the unfinished file
                messagebox.showwarning("Cancelled", "Download was cancelled.")
            elif self.stop_requested:
                f.close()
                messagebox.showinfo("Stopped", "Download was stopped. You can resume later.")
            else:
                self.update_history_file(filename, url, total_size, full_path) # Update download history 
                messagebox.showinfo("Success", "Download Completed!") # Notify user of completion (Additional Requirement #5)
                self.root.after(0, lambda: self.progress.configure(value=0))
                self.open_file(full_path) # Auto-open file on finish (Requirement #7)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to download: {e}")
        
        finally:
            # Reset the UI state regardless of success or failure
            self.downloading = False
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
            # self.root.after(0, lambda: self.progress.configure(value=0))

    def cancel_download(self):
        """Triggers the cancellation flag used in the download loop.""" # (Requirement #6)
        if self.downloading:
            self.cancel_requested = True

    def stop_download(self):
        """Triggers the stop flag used in the download loop.""" # (Additional Requirement #2)
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

    def update_history_file(self, file_name, file_url, file_size, file_path):
        """Saves the downloaded file to a JSON file to keep track of download history."""
        history_file = "history.json"    
        new_entry = {
            "name": file_name,
            "size": f"{file_size // (1024*1024)} MB",
            "url": file_url,
            "path": file_path
        }
        # 1. Read existing data
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    data = json.load(f) # Load existing list
            except (json.JSONDecodeError, ValueError):
                data = [] # If file is empty or corrupted, start a new list
        else:
            data = [] # If file doesn't exist, start a new list

        # 2. Append the new download to the list
        data.append(new_entry)

        # 3. Write everything back to the file
        with open(history_file, "w") as f:
            json.dump(data, f, indent=4) # indent=4 makes it readable for humans

    def show_history_window(self):
        """Shows download history in a different window.""" # (Additional Requirement #1)
        # 1. Create a new pop-up window
        history_win = tk.Toplevel(self.root)
        history_win.title("Download History")
        history_win.geometry("500x400")

        # 2. Add a title label
        tk.Label(history_win, text="Recent Downloads", font=("Arial", 12, "bold")).pack(pady=10)

        # 3. Create a frame with a scrollbar for the history list
        list_frame = tk.Frame(history_win)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # We use a Text widget to easily display all history items
        history_display = tk.Text(list_frame, state="disabled", wrap="word")
        scrollbar = tk.Scrollbar(list_frame, command=history_display.yview)
        history_display.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        history_display.pack(side="left", fill="both", expand=True)

        # 4. Read the JSON file
        history_file = "history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history_data = json.load(f)
                
                # 5. Format and insert the data into the Text widget
                history_display.configure(state="normal") # Enable editing to insert text
                for item in history_data:
                    if not os.path.exists(item['path']):
                        continue # Skip entries with missing files
                    entry_text = f"Name: {item['name']}\nSize: {item['size']}\nURL: {item['url']}\nPath: {item['path']}\n"
                    entry_text += "-"*50 + "\n"
                    history_display.insert("end", entry_text)
                history_display.configure(state="disabled") # Set back to read-only
                
            except (json.JSONDecodeError, ValueError):
                history_display.insert("end", "Error reading history file.")
        else:
            history_display.configure(state="normal")
            history_display.insert("end", "No download history found.")
            history_display.configure(state="disabled")

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

# --- Satisfied Requirements ---
""""
-- Bare Minimum Requirements --
1. URL Input: (Done)
2. Start Download: (Done)
3. Save Location: (Done)
4. Progress Tracking: (Done)
5. File Information: (Done)
6. Cancel Download: (Done)
7. Auto-Open: (Done)

-- Additional Requirements --
1. Download History: (Done) Needs to be tested more thoroughly, duplicated and missing files are not handled perfectly.
2. Pause Download: (Done)
3. Resume Download: (Done)
4. Multi-Downloading:
5. Notifications: (Done)
6. Thumbnails: 

"""