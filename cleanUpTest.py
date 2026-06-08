import os
import time


#Target the same storage folder your main script uses
STORAGE_DIR = "./central_camera_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

#Define a fake video file name
fake_file_name = "Camera_01_TEST_OLD_FILE.mp4" 
fake_file_path = os.path.join(STORAGE_DIR, fake_file_name)

#1. Create an empty fake video file
with open(fake_file_path, "w") as f:
    f.write("fake video data")
print(f"[TEST] Created fake file: {fake_file_name}")

#2. Calculate a timestamp from 8 days ago (in seconds)
eight_days_ago = time.time() - (8*24*60*60)

#3. Force the operating system to change the file's modification time
os.utime(fake_file_path, (eight_days_ago, eight_days_ago))
print("[TEST] Successfully backdated file modified to 8 days ago!")
print("[TEST] Now, start your main script.It will find this file and delete it within 1 hour.")
