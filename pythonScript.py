import threading
import subprocess
import os
import time


#Dictionary of your network cameras (IP address/RTSP URLs)
#Replace these with the actual IP streams provided in your training lab

CAMERAS = {
    "camera_01" : "rstp://192.168.1.101:554/live",
    "camera_02" : "rstp://192.168.1.102:554/live",
    "camera_03" : "rstp://192.168.1.103:554/live"
}

#The single server storage directory
STORAGE_DIR = "./central_camera_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

#Retention policy: Delete files older than 7 days (in seconcds)
MAX_FILE_AGE_SECONDS = 7 * 24 * 60 * 60


def auto_cleanup_storage():
    """Background thread that automatically deletes video files older than 7 days."""
    print("[START] Storage retention monitor is running...")
    while True:
        try:
            current_time = time.time()
            #Scan through all recorded filesin the storage folder
            for filename in os.listdir(STORAGE_DIR):
                file_path = os.path.join(STORAGE_DIR, filename)

                #Check if it is a file (and not a folder)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)

                    #If the file is older than 7 days
                    if file_age > MAX_FILE_AGE_SECONDS:
                        os.remove(file_path)
                        print(f"[CLEANUP] Deleted old footage file: {filename}")

        except Exception as e:
            print(f"[ERROR] Retention monitor encountered an error: {e}")

        #Runcheck on storage evry hour
        time.sleep(3600)


def record_camera_stream(camera_name, rstp_url):
    print(f"\n[START] Monitoring {camera_name}...")

    #Loop ensures the software reconnects if the camera drops off the network
    while True:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_file = os.path.join(STORAGE_DIR, f"{camera_name}_{timestamp}.mp4")


        #FFmpeg command: Copies the stream directly without re-encoding (-c:v copy)
        #This saves massive CPU power, allowing 1 server to do the job of many.
        cmd = [
            'ffmpeg',                   #
            '-rtsp_transport', 'tcp',   #Use TCP for reliable network transmission
            '-i', rstp_url,             #Input URL
            '-c:v', 'copy',             #Copy video directly without decoding
            '-c:a', 'copy',             #Copy audio directly without decoding
            '-f', 'mp4',                #Output format
            '-t', '3600',               #Split filese every 1 hour (3600 seconds)
            output_file                 #
        ]


        try:
            #Execute the network transmission process
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
        except Exception as e:
            print(f"[ERROR] {camera_name} encountered an issue: {e}")

        print(f"[RECONNECTING] Lost connection to {camera_name}. Retrying in 5 seconds...")
        time.sleep(5)


#Starting auto cleanup thread first
cleanup_thread = threading.Thread(target=auto_cleanup_storage)
cleanup_thread.daemon = True
cleanup_thread.start()

#Spawn a seperate background thread for every single camera
threads = []
for name, url in CAMERAS.items():
    t = threading.Thread(target=record_camera_stream, args=(name, url))
    t.daemon = True
    threads.append(t)
    t.start()

#Keep the main script running on the server
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("[STOP] Central transmission software shutting down.")