# Centralized RTSP Stream Ingestion Engine

A high-efficiency, multi-threaded Video Management System (VMS) data transmission tool built with Python and FFmpeg. This software consolidates multiple IP security camera feeds onto a single centralized storage server while maintaining a near-zero CPU overhead.

## 🚀 Project Mission & Context
Organizations frequently run too many individual servers to handle security camera networks because standard applications waste massive CPU resources decoding and rendering video frames in real time. 

This project solves that hardware bottleneck. By intercepting raw network data packets and routing them directly to disk without decoding, a single modern server can comfortably take over the job of an entire multi-server infrastructure.

---

## 🛠️ Core Engineering Features

* **Direct Stream Pass-Through:** Utilizes FFmpeg stream copying flags (`-c:v copy`), bypassing video rendering to drop CPU consumption by over 90%.
* **Multi-Threaded Fault Isolation:** Assigns each camera feed to an independent execution thread. If a single network link drops, its specific thread attempts a 5-second loop reconnection while the rest of the camera network records uninterrupted.
* **Network Reliability:** Forces network socket connections over **RTSP via TCP** to prevent frame dropping and video corruption common with UDP transmissions over busy local area networks (LANs).
* **Automated Retention Management:** Features an isolated, automated storage cleanup monitor that runs on a secondary background clock, purging footage older than **7 days** to prevent hard drive saturation.

---

## 🏗️ System Architecture

```text
 [ IP Camera 01 ] ──(RTSP over TCP)──┐
 [ IP Camera 02 ] ──(RTSP over TCP)──┼──► [ SINGLE CENTRAL SERVER ] ──► [ Automated 7-Day Storage ]
 [ IP Camera 03 ] ──(RTSP over TCP)──┘     (Multi-Threaded Python Engine)     (Surveillance HDDs / RAID)
```

---

## ⚙️ Dependencies & Prerequisites

The host server requires **Python 3** and **FFmpeg** configured on the system environment path.

### Linux (Ubuntu/Debian) Installation:
```bash
sudo apt update && sudo apt install python3 ffmpeg -y
```

### Windows Installation:
1. Download Python from [python.org](https://python.org) (ensure **"Add python.exe to PATH"** is checked during setup).
2. Download the FFmpeg essentials build from [gyan.dev](https://gyan.dev).
3. Extract the folder to `C:\ffmpeg` and add `C:\ffmpeg\bin` to your system environment variables (Path).

---

## 💻 Code Structure

### 1. Main Application (`main.py`)
This script manages background thread generation, handles network socket drops, and runs the stream configuration variables.

```python
import threading
import subprocess
import os
import time

# Camera Registry Network Config
CAMERAS = {
    "Camera_01": "rtsp://192.168.1.101:554/live",
    "Camera_02": "rtsp://192.168.1.102:554/live",
    "Camera_03": "rtsp://192.168.1.103:554/live"
}

STORAGE_DIR = "./central_camera_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)
MAX_FILE_AGE_SECONDS = 7 * 24 * 60 * 60  # 7 Days in seconds

def auto_cleanup_storage():
    """Background thread enforcing the 7-day data retention policy."""
    print("[START] Storage retention monitor is running...")
    while True:
        try:
            current_time = time.time()
            for filename in os.listdir(STORAGE_DIR):
                file_path = os.path.join(STORAGE_DIR, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > MAX_FILE_AGE_SECONDS:
                        os.remove(file_path)
                        print(f"[CLEANUP] Deleted old footage file: {filename}")
        except Exception as e:
            print(f"[ERROR] Retention monitor error: {e}")
        time.sleep(3600)

def record_camera_stream(camera_name, rtsp_url):
    """Isolated ingestion worker thread for capturing camera network traffic."""
    print(f"[START] Monitoring {camera_name}...")
    while True:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_file = os.path.join(STORAGE_DIR, f"{camera_name}_{timestamp}.mp4")
        
        # Stream copy argument saves server CPU cycles
        cmd = [
            'ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
            '-c:v', 'copy', '-c:a', 'copy', '-f', 'mp4', '-t', '3600', output_file
        ]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
        except Exception as e:
            print(f"[ERROR] {camera_name} exception: {e}")
            
        print(f"[RECONNECTING] Lost link to {camera_name}. Retrying in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    # Launch system maintenance loop
    cleanup_thread = threading.Thread(target=auto_cleanup_storage, daemon=True)
    cleanup_thread.start()

    # Launch parallel ingestion pipelines
    for name, url in CAMERAS.items():
        t = threading.Thread(target=record_camera_stream, args=(name, url), daemon=True)
        t.start()

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("[STOP] Central transmission software shutting down.")
```

### 2. Retention Simulation Tester (`test_cleanup.py`)
Artificially backdates sample files to immediately verify storage protection logic without waiting 7 days.

```python
import os, time
STORAGE_DIR = "./central_camera_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

fake_file_path = os.path.join(STORAGE_DIR, "Camera_01_TEST_OLD_FILE.mp4")
with open(fake_file_path, "w") as f: f.write("fake video data")

eight_days_ago = time.time() - (8 * 24 * 60 * 60)
os.utime(fake_file_path, (eight_days_ago, eight_days_ago))
print("[TEST] Created backdated simulation file. Run main.py to verify automatic removal.")
```

---

## 📈 Deployment Specifications

To maximize stability when deploying this network platform in production, adhere to the following network engineering guidelines:
1. **Infrastructure Isolation:** Allocate cameras and the central storage server onto their own dedicated **Video VLAN** to protect corporate office bandwidth.
2. **Hardware Storage Profile:** Utilize dedicated **Surveillance-Class Mechanical HDDs** configured in a high-fault-tolerant array (like RAID 10). Standard desktop or standard cloud computing storage profiles are not physically optimized for 24/7/365 continuous packet writing.
