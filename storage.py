import json
import os
from pathlib import Path

HISTORY_FILE = "history.json"
SETTINGS_FILE = "settings.json"

"""Storage module for managing data files."""

def load_history():
    """Returns the list of downloaded files from JSON."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_entry(name, size_bytes):
    """Formats and appends a new download entry to the history."""
    data = load_history()
    
    # Format size to MB
    size_mb = f"{size_bytes // (1024 * 1024)} MB"
    
    new_entry = {
        "Name": name,
        "Status": "Finished",
        "Size": size_mb,
        "Progress": "100%"
    }
    
    data.append(new_entry)
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)


def save_settings(settings_dict):
    """Saves user preferences to a JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings_dict, f)

def load_settings():
    """Loads user preferences or returns defaults from config.py."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    
    # Fallback to config.py defaults if no settings file exists
    return {
        "save_path": os.path.join(Path.home(), "Downloads"),
        "open_on_finish": False
    }