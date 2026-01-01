import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class DownloadManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ASPU Download Manager - Team Project")
        self.root.geometry("600x450")

        # --- UI Header ---
        self.header = tk.Label(root, text="Multimedia Download Manager", font=("Arial", 16, "bold"))
        self.header.pack(pady=10)

        # --- URL Input Section ---
        tk.Label(root, text="Enter Download URL:").pack(pady=5)
        self.url_entry = tk.Entry(root, width=60)
        self.url_entry.pack(pady=5)

        # --- Save Path Section (Requirement #3) ---
        self.save_path = ""
        self.path_btn = tk.Button(root, text="Select Save Location", command=self.browse_file)
        self.path_btn.pack(pady=5)
        self.path_label = tk.Label(root, text="No path selected", fg="gray")
        self.path_label.pack()

        # --- File Info Section (Requirement #5) ---
        self.info_frame = tk.LabelFrame(root, text="File Information", padx=10, pady=10)
        self.info_frame.pack(pady=10, fill="x", padx=20)
        
        self.file_name_label = tk.Label(self.info_frame, text="Name: N/A")
        self.file_name_label.pack(anchor="w")
        
        self.file_size_label = tk.Label(self.info_frame, text="Size: N/A")
        self.file_size_label.pack(anchor="w")

        # --- Progress Bar (Requirement #4) ---
        tk.Label(root, text="Download Progress:").pack(pady=5)
        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=5)

        # --- Control Buttons ---
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=20)

        self.start_btn = tk.Button(self.btn_frame, text="Start Download", bg="green", fg="white", width=15, command=self.start_download)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.cancel_btn = tk.Button(self.btn_frame, text="Cancel", bg="red", fg="white", width=15, state="disabled", command=self.cancel_download)
        self.cancel_btn.grid(row=0, column=1, padx=5)

        # --- Open File Button (Requirement #7) ---
        self.open_btn = tk.Button(root, text="Open Downloaded File", state="disabled", command=self.open_file)
        self.open_btn.pack(pady=5)

    def browse_file(self):
        """Allows user to choose where to save the file """
        file_path = filedialog.asksaveasfilename()
        if file_path:
            self.save_path = file_path
            self.path_label.config(text=f"Save to: {file_path}", fg="black")

    def start_download(self):
        """Logic to be implemented by Student 2 """
        url = self.url_entry.get()
        if not url or not self.save_path:
            messagebox.showwarning("Input Error", "Please provide a URL and select a save path.")
            return
        
        # UI updates to show download has started
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        print(f"Starting download from: {url}")

    def cancel_download(self):
        """Logic to cancel the process """
        print("Download cancelled by user.")
        self.start_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")

    def open_file(self):
        """Logic to open the file after completion [cite: 5]"""
        print("Opening file...")

if __name__ == "__main__":
    root = tk.Tk()
    app = DownloadManagerApp(root)
    root.mainloop()
