import tkinter as tk
from ui import ASPU_DownloadManager_UI

"""This is the main entry point for the ASPU Download Manager application."""

if __name__ == "__main__":
    # 1. Create the root window
    root = tk.Tk()
    
    # 2. Pass the root window to your UI class
    app = ASPU_DownloadManager_UI(root)
    
    # 3. Start the event loop
    root.mainloop()

"""
test cases:
1. 10 MB file: https://www.google.com/search?q=http://xcal1.vodafone.co.uk/10MB.zip
2. 50 MB file: https://speed.hetzner.de/50MB.bin
3. 100 MB file: https://speed.hetzner.de/100MB.bin
"""