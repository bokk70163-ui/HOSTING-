import subprocess
import threading
import os
import signal
import time
import sys  # Added sys to ensure correct python interpreter
from config import BASE_DIR

# Dictionary to store running processes
running_processes = {}

# Create logs directory
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def run_script(folder_name, file_name, status_callback, completion_callback):
    process_id = f"{folder_name}/{file_name}"
    folder_path = os.path.join(BASE_DIR, folder_name)
    
    # Generate log file name
    timestamp = int(time.time())
    safe_name = f"{folder_name}_{file_name}".replace("/", "_").replace(".", "_")
    log_file_path = os.path.join(LOG_DIR, f"{safe_name}_{timestamp}.txt")

    status_callback(f"[Status] Started processing. Logs are being written to file...")

    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            # 1. Requirements Installation Log
            # FIX: Previously I had a path error here (double BASE_DIR)
            req_path = os.path.join(folder_path, "requirements.txt")
            
            if os.path.exists(req_path) and os.path.getsize(req_path) > 0:
                log_file.write("--- INSTALLING REQUIREMENTS ---\n")
                log_file.flush()
                
                # FIX: Using sys.executable ensures we use the same python environment
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                    stdout=log_file, 
                    stderr=log_file,
                    cwd=folder_path # Running inside the folder, so just requirements.txt is enough
                )
                log_file.write("\n--- REQUIREMENTS INSTALLED ---\n\n")
            else:
                log_file.write(f"--- NO REQUIREMENTS FOUND AT: {req_path} ---\n\n")
            
            log_file.flush()

            # 2. Running the Python Script
            log_file.write(f"--- STARTING SCRIPT: {file_name} ---\n")
            log_file.flush()

            process = subprocess.Popen(
                [sys.executable, "-u", file_name], # Using sys.executable here too
                stdout=log_file,
                stderr=log_file,
                text=True,
                cwd=folder_path,
                preexec_fn=os.setsid
            )
            
            running_processes[process_id] = process
            
            process.wait()
            
            log_file.write(f"\n--- PROCESS FINISHED (Code: {process.returncode}) ---")

        if process_id in running_processes:
            del running_processes[process_id]
        
        completion_callback(log_file_path, True)

    except Exception as e:
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
    
