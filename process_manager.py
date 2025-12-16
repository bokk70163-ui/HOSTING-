import subprocess
import threading
import os
import signal
import time
import queue
from config import BASE_DIR

running_processes = {}

def install_requirements(folder_path, update_callback):
    req_path = os.path.join(BASE_DIR, folder_path, "requirements.txt")
    if os.path.exists(req_path) and os.path.getsize(req_path) > 0:
        update_callback("[Info] Installing requirements...")
        subprocess.run(["pip", "install", "-r", req_path], capture_output=True)
        update_callback("[Success] Requirements installed.")
    else:
        update_callback("[Info] No requirements found or empty. Skipping.")

def run_script(folder_name, file_name, send_message_callback):
    process_id = f"{folder_name}/{file_name}"
    folder_path = os.path.join(BASE_DIR, folder_name)

    install_requirements(folder_name, send_message_callback)
    send_message_callback(f"[Start] Initiating {file_name}...")

    log_queue = queue.Queue()
    
    try:
        # setsid is used to create a process group so we can pause/kill the whole tree
        process = subprocess.Popen(
            ["python", "-u", file_name], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            cwd=folder_path,
            preexec_fn=os.setsid 
        )
        
        running_processes[process_id] = process

        def read_output(pipe, prefix):
            for line in iter(pipe.readline, ''):
                if line:
                    log_queue.put(f"{prefix}: {line.strip()}")
                else:
                    break
            pipe.close()

        t1 = threading.Thread(target=read_output, args=(process.stdout, ""))
        t2 = threading.Thread(target=read_output, args=(process.stderr, "ERR"))
        t1.start()
        t2.start()

        while t1.is_alive() or t2.is_alive() or not log_queue.empty():
            batch_logs = []
            start_time = time.time()
            
            # Collect logs for 3 seconds
            while time.time() - start_time < 3:
                try:
                    line = log_queue.get(timeout=0.5)
                    batch_logs.append(line)
                except queue.Empty:
                    if not (t1.is_alive() or t2.is_alive()):
                        break
                    continue
            
            if batch_logs:
                full_message = "\n".join(batch_logs)
                if len(full_message) > 4000:
                    full_message = full_message[:4000] + "\n... (truncated)"
                send_message_callback(full_message)

        process.wait()
        send_message_callback(f"[Stop] Process finished with code {process.returncode}")
        
        if process_id in running_processes:
            del running_processes[process_id]

    except Exception as e:
        send_message_callback(f"[Error] {str(e)}")
        if process_id in running_processes:
            del running_processes[process_id]

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
            # SIGSTOP pauses the process (Linux/Unix only)
            os.killpg(os.getpgid(process.pid), signal.SIGSTOP)
            return True
        except Exception:
            return False
    return False

def resume_process(process_id):
    if process_id in running_processes:
        process = running_processes[process_id]
        try:
            # SIGCONT resumes the process (Linux/Unix only)
            os.killpg(os.getpgid(process.pid), signal.SIGCONT)
            return True
        except Exception:
            return False
    return False

def get_running_list():
    return list(running_processes.keys())
    
