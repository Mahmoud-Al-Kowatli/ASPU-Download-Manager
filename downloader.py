import requests
import os
import threading
from pathlib import Path

class DownloadEngine:
    def __init__(self):
        self.downloading = False
        self.stop_requested = False
        self.cancel_requested = False

    def start_download(self, url, callbacks):
        """
        Starts the download in a separate thread.
        :param url: The URL to download
        :param callbacks: Dictionary containing functions for UI updates:
                          on_progress, on_status, on_finish, on_error, on_pause, on_cancel
        """
        if self.downloading:
            return

        self.downloading = True
        self.stop_requested = False
        self.cancel_requested = False

        thread = threading.Thread(target=self._core_worker, args=(url, callbacks))
        thread.daemon = True
        thread.start()

    def pause(self):
        self.stop_requested = True

    def cancel(self):
        self.cancel_requested = True

    def _core_worker(self, url, callbacks):
        try:
            filename = url.split("/")[-1] or "downloaded_file"
            save_dir = os.path.join(Path.home(), "Downloads")
            save_path = os.path.join(save_dir, filename)

            # Check existing file for resume capability
            existing_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
            headers = {"Range": f"bytes={existing_size}-"}

            # Start request
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            total_size = int(response.headers.get('content-length', 0)) + existing_size

            callbacks['on_status'](f"Downloading: {filename}")

            downloaded = existing_size
            
            with open(save_path, 'ab') as f:
                for chunk in response.iter_content(chunk_size=1024 * 16):
                    if self.stop_requested or self.cancel_requested:
                        break
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / total_size) * 100
                        callbacks['on_progress'](percent)

            # Handle Stop/Cancel/Finish
            if self.cancel_requested:
                f.close()
                if os.path.exists(save_path):
                    os.remove(save_path)
                callbacks['on_cancel']()

            elif self.stop_requested:
                callbacks['on_pause']()

            else:
                callbacks['on_finish'](filename, save_path, total_size)

        except Exception as e:
            callbacks['on_error'](str(e))
        finally:
            self.downloading = False
            # Reset progress bar visually if needed via callback, or handle in UI