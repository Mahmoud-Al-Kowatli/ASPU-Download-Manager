import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import subprocess

class ASPU_DownloadManager:
    def __init__(self, root):
        self.root = root
        self.root.title("ASPU Download Manager")
        self.root.geometry("600x450")

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
        self.start_btn = tk.Button(root, text="Start Download", bg="green", fg="white", command=self.download_file)
        self.start_btn.pack(pady=10)

    def select_dest(self):
        """Allows user to pick where to save the file [cite: 15]"""
        path = filedialog.askdirectory()
        if path:
            self.save_path = path
            self.path_label.config(text=f"Save to: {path}", fg="black")

    def download_file(self):
        """Main download logic [cite: 14]"""
        url = self.url_entry.get()
        if not url or not self.save_path:
            messagebox.showerror("Error", "Please provide a URL and select a save location.")
            return

        try:
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            # Display info [cite: 17]
            filename = url.split("/")[-1]
            self.file_name_lbl.config(text=f"Name: {filename}")
            self.file_size_lbl.config(text=f"Size: {total_size // (1024*1024)} MB")

            full_path = os.path.join(self.save_path, filename)
            
            # Download and update progress [cite: 16]
            downloaded = 0
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress['value'] = (downloaded / total_size) * 100
                        self.root.update_idletasks()

            messagebox.showinfo("Success", "Download Completed!")
            
            # Requirement #7: Open file immediately 
            subprocess.run(['xdg-open', full_path])

        except Exception as e:
            messagebox.showerror("Error", f"Failed to download: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ASPU_DownloadManager(root)
    root.mainloop()