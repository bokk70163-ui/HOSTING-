import subprocess
import threading
import os
import signal
import time
from config import BASE_DIR

# রানিং প্রসেস স্টোর করার ডিকশনারি
running_processes = {}

# লগ ফোল্ডার তৈরি
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def run_script(folder_name, file_name, status_callback, completion_callback):
    process_id = f"{folder_name}/{file_name}"
    folder_path = os.path.join(BASE_DIR, folder_name)
    
    # লগ ফাইলের নাম জেনারেট করা (যেমন: logs/folder_file_timestamp.txt)
    timestamp = int(time.time())
    safe_name = f"{folder_name}_{file_name}".replace("/", "_").replace(".", "_")
    log_file_path = os.path.join(LOG_DIR, f"{safe_name}_{timestamp}.txt")

    status_callback(f"[Status] Started processing. Logs are being written to file...")

    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            # 1. Requirements Installation Log
            req_path = os.path.join(BASE_DIR, folder_path, "requirements.txt")
            if os.path.exists(req_path) and os.path.getsize(req_path) > 0:
                log_file.write("--- INSTALLING REQUIREMENTS ---\n")
                log_file.flush() # বাফারিং এড়াতে সাথে সাথে রাইট করা
                
                # pip install আউটপুট সরাসরি ফাইলে রিডাইরেক্ট করা
                subprocess.run(
                    ["pip", "install", "-r", req_path], 
                    stdout=log_file, 
                    stderr=log_file,
                    cwd=folder_path
                )
                log_file.write("\n--- REQUIREMENTS INSTALLED ---\n\n")
            else:
                log_file.write("--- NO REQUIREMENTS FOUND ---\n\n")
            
            log_file.flush()

            # 2. Running the Python Script
            log_file.write(f"--- STARTING SCRIPT: {file_name} ---\n")
            log_file.flush()

            process = subprocess.Popen(
                ["python", "-u", file_name], 
                stdout=log_file,  # stdout সরাসরি ফাইলে
                stderr=log_file,  # stderr সরাসরি ফাইলে
                text=True,
                cwd=folder_path,
                preexec_fn=os.setsid
            )
            
            running_processes[process_id] = process
            
            # প্রসেস শেষ হওয়া পর্যন্ত অপেক্ষা
            process.wait()
            
            log_file.write(f"\n--- PROCESS FINISHED (Code: {process.returncode}) ---")

        # প্রসেস শেষ হলে লগ ফাইল পাঠানো
        if process_id in running_processes:
            del running_processes[process_id]
        
        completion_callback(log_file_path, True)

    except Exception as e:
        # এরর হলে সেটাও লগে লিখে পাঠানো
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n\n--- CRITICAL ERROR ---\n{str(e)}")
        
        if process_id in running_processes:
            del running_processes[process_id]
            
        completion_callback(log_file_path, False)

def stop_process(process_id):
    if process_id in running_processes:
        process = running_processes[process_id]
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM) 
        except:
            process.terminate()
        
        del running_processes[process_id]
        return True
    return False

def pause_process(process_id):
    if process_id in running_processes:
        process = running_processes[process_id]
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGSTOP)
            return True
        except Exception:
            return False
    return False

def resume_process(process_id):
    if process_id in running_processes:
        process = running_processes[process_id]
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGCONT)
            return True
        except Exception:
            return False
    return False

def get_running_list():
    return list(running_processes.keys())
    
