# tcp_view_v3

# Linux TcpView (Python/GTK3)

**Linux TcpView** is a lightweight, GUI-based network monitoring tool for Linux, written in Python using GTK3. Inspired by the classic Windows Sysinternals TCPView, it provides a graphical representation of all TCP and UDP endpoints on your system, including the local and remote addresses and the state of TCP connections.

> **Note:** This tool is designed for Linux systems and utilizes native GTK bindings.

## 📸 Screenshot

![App Screenshot](screenshot.png)
*(Place a screenshot of your running app here and name it screenshot.png)*

## ✨ Features

*   **Real-time Monitoring:** Automatically refreshes connection lists every 5 seconds.
*   **Protocol Support:** View TCP, UDP, IPv4, and IPv6 connections.
*   **Filtering:**
    *   Toggle specific protocols or IP versions.
    *   "Active Only" mode to filter out listening ports.
    *   Live Search bar to filter by Process Name, PID, or IP address.
*   **Process Identification:** specific coloring per process name for easy visual grouping.
*   **Context Menu Actions (Right-Click):**
    *   📋 **Copy Details:** Copy connection info to the clipboard.
    *   💀 **Kill Process:** Force kill (SIGKILL) a specific process directly from the UI.
    *   🌐 **Whois Lookup:** Run a Whois query on the remote IP address.

## 🛠 Prerequisites

To run this application, you need **Python 3** and the following system dependencies:

1.  **GTK3** and **PyGObject** (for the GUI).
2.  **Whois** (for the context menu lookup feature).
3.  **Psutil** (Python library for fetching system info).

### 📦 Installation

#### 1. System Dependencies
**Ubuntu / Debian / Mint:**
```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 whois
Fedora:
code
Bash
sudo dnf install python3-gobject gtk3 whois
Arch Linux:
code
Bash
sudo pacman -S python-gobject gtk3 whois
2. Python Dependencies
Install psutil via pip:
code
Bash
pip3 install psutil
🚀 Usage
Clone the repository and run the script.
code
Bash
git clone https://github.com/yourusername/linux-tcpview.git
cd linux-tcpview
Running the Application
For basic usage (viewing processes owned by your user):
code
Bash
python3 tcpview.py
⚠️ Important: Running as Root
To view all network connections (including system processes) and to use the Kill Process feature effectively, you must run the script with sudo:
code
Bash
sudo python3 tcpview.py
🕹 Controls
Toggles (Top Bar): Click to show/hide Active connections, TCP, UDP, IPv4, or IPv6.
Sorting: Click any column header (e.g., "PID" or "State") to sort the list.
Right-Click: Select a row and right-click to access the context menu (Copy, Kill, Whois).
🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
Fork the Project
Create your Feature Branch (git checkout -b feature/AmazingFeature)
Commit your Changes (git commit -m 'Add some AmazingFeature')
Push to the Branch (git push origin feature/AmazingFeature)
Open a Pull Request
📝 License
Distributed under the MIT License. See LICENSE for more information.
🛑 Troubleshooting
"ImportError: No module named gi": You are missing the system GTK bindings. Please review the Installation section for your specific Linux distribution.
"Permission Denied" when killing a process: Ensure you launched the application using sudo.
Whois not working: Ensure the whois utility is installed (which whois).
