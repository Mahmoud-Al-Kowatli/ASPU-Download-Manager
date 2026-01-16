import requests
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Import  custon logic modules
import class_process

"""
DownloadEngine class to manage multiple download processes using a threadpool.
- This class handles starting, pausing, and canceling download tasks while preventing duplicate downloads.
- This class manages a pool of threads and tracks active download processes.
"""

class DownloadEngine:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.processes: dict[int, class_process.Process] = {} 
        # I used this instead of simply using self.processes = {} becuase of Pylance error. :)

    def start_download(self, url, callbacks):
        """
        Starts or Resumes a download while preventing duplicate threads.
        Args:
            url (str): The URL of the file to download.
            callbacks (dict): A dictionary of callback functions for status updates.
        Returns:
            int: The Process ID of the download task.
        """
        # 1. Check if we already have a process for this URL to avoid duplicates
        for existing_pid, proc in self.processes.items():
            if proc.url == url:
                # If it's already downloading, don't start a second thread
                if proc.downloading:
                    return existing_pid
                
                # If it exists but is paused, we will replace it with a fresh process 
                self.pause_download(existing_pid)

        # 2. Create the new Process instance
        new_process = class_process.Process(url, callbacks) 
        pid = new_process.pid

        # 3. Store it in our tracking dictionary
        self.processes[pid] = new_process 

        # 4. Submit to the ThreadPool
        self.executor.submit(new_process.start) 

        return pid

    def pause_download(self, pid):
        """Finds a specific process by ID and pauses it."""
        if pid in self.processes:
            self.processes[pid].pause()

    def cancel_download(self, pid):
        """Finds a specific process by ID and cancels it."""
        if pid in self.processes:
            self.processes[pid].cancel()
            
            # Remove from tracking dictionary after canceling
            del self.processes[pid]
