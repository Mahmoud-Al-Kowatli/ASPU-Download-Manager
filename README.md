# 🚀 ASPU Multimedia Download Manager
**Academic Project for Sham Private University (ASPU)**

A lightweight, efficient multimedia download manager built with Python and Tkinter. This project is part of the Multimedia Systems course requirements.

---

## 🏗️ Project Structure
The project is now refactored into modular components for better maintainability:
* **main.py**: The application entry point.
* **ui.py**: Handles the Tkinter interface and user events.
* **downloader.py**: Contains the core logic for multi-threaded downloads.
* **storage.py**: Manages local data persistence (JSON history).


## 🛠️ Installation & Setup (تجهيز البيئة وتشغيل المشروع)

To run this project locally, please follow these steps carefully to ensure all dependencies are met.

### 1. Clone the Repository
Open your terminal and run:
 
git clone [https://github.com/Mahmoud-Al-Kowatli/ASPU-Download-Manager.git](https://github.com/Mahmoud-Al-Kowatli/ASPU-Download-Manager.git)
cd ASPU-Download-Manager

# Create the environment
python -m venv venv

# Activate it

# On Linux/macOS:
source venv/bin/activate
pip install requests
# On Windows:
.\venv\Scripts\activate

pip install -r requirements.txt

# Run
python main.py