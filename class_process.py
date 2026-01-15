import os
from urllib import response 
import requests
from pathlib import Path

import storage

class Process:
    
    process_id_counter = 1
    
    def __init__(self, url, callbacks):
        # Unique Process ID
        self.pid = Process.process_id_counter
        Process.process_id_counter += 1
        # Status flags
        self.downloading = False
        self.stop_requested = False
        self.cancel_requested = False
        # Download parameters
        self.url = url
        self.callbacks = callbacks        

    def start(self):
        self.downloading = True
        self.stop_requested = False
        self.cancel_requested = False

        try:
            filename = self.url.split("/")[-1] or "Untitled"
            save_dir = storage.load_settings().get('save_path', os.path.join(Path.home(), "Downloads"))
            save_path = os.path.join(save_dir, filename)

            existing_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
            headers = {"Range": f"bytes={existing_size}-"}

            response = requests.get(self.url, headers=headers, stream=True, timeout=15)
            
            # If server returns 416, it means file is already finished
            if response.status_code == 416:
                self.callbacks['on_finish'](filename, save_path, existing_size)
                return

            total_size = int(response.headers.get('content-length', 0)) + existing_size
            self.callbacks['on_status']("Downloading...")

            write_mode = 'ab' if response.status_code == 206 else 'wb'
            downloaded = existing_size if response.status_code == 206 else 0
                
            with open(save_path, write_mode) as f:
                for chunk in response.iter_content(chunk_size=1024 * 8):
                    if self.stop_requested or self.cancel_requested:
                        break
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            self.callbacks['on_progress'](percent)
           
            if self.cancel_requested:
                if os.path.exists(save_path):
                    os.remove(save_path)
                self.callbacks['on_cancel']()

            elif self.stop_requested:
                self.callbacks['on_pause']()

            else:
                self.callbacks['on_finish'](filename, save_path, total_size)

        except Exception as e:
            self.callbacks['on_error'](str(e))
        finally:
            self.downloading = False

    def pause(self):
        self.stop_requested = True

    def cancel(self):
        self.cancel_requested = True