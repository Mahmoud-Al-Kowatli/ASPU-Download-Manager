import tkinter as tk
from ui import ASPU_DownloadManager_UI

if __name__ == "__main__":
    # 1. Create the root window
    root = tk.Tk()
    
    # 2. Pass the root window to your UI class
    app = ASPU_DownloadManager_UI(root)
    
    # 3. Start the event loop
    root.mainloop()