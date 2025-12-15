import subprocess
import threading
import os
import signal
import time
from config import BASE_DIR

# রানিং প্রসেস স্টোর করার ডিকশনারি
running_processes = {}

def install_requirements(folder_path, update_callback):
    req_path = os.path.join(BASE_DIR, folder_path, "requirements.txt")
    if os.path.exists(req_path) and os.path.getsize(req_path) > 0:
        update_callback("📦 Installing requirements...")
        subprocess.run(["pip", "install", "-r", req_path], capture_output=True)
        update_callback("✅ Requirements installed.")
    else:
        update_callback("⚠️ No requirements found or empty. Skipping.")

def run_script(folder_name, file_name, send_message_callback):
    process_id = f"{folder_name}/{file_name}"
    
    folder_path = os.path.join(BASE_DIR, folder_name)

    # Requirements Install
    install_requirements(folder_name, send_message_callback)

    send_message_callback(f"🚀 Starting {file_name}...")

    # Process Start
    try:
        process = subprocess.Popen(
            ["python", "-u", file_name], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            cwd=folder_path,
            preexec_fn=os.setsid
        )
        
        running_processes[process_id] = process

        log_buffer = []
        buffer_lock = threading.Lock()
        
        def flush_buffer():
            with buffer_lock:
                if log_buffer:
                    combined = "\n".join(log_buffer)
                    log_buffer.clear()
                    send_message_callback(combined)

        def read_output(pipe, prefix):
            for line in iter(pipe.readline, ''):
                if line:
                    with buffer_lock:
                        log_buffer.append(f"{prefix}: {line.strip()}")
                        if len(log_buffer) >= 10:
                            combined = "\n".join(log_buffer)
                            log_buffer.clear()
                            send_message_callback(combined)
                            time.sleep(4)
                else:
                    break
            pipe.close()

        t1 = threading.Thread(target=read_output, args=(process.stdout, "LOG"))
        t2 = threading.Thread(target=read_output, args=(process.stderr, "ERR"))
        t1.start()
        t2.start()

        t1.join()
        t2.join()
        flush_buffer()
        process.wait()
        send_message_callback(f"🛑 Process finished with code {process.returncode}")
        if process_id in running_processes:
            del running_processes[process_id]

    except Exception as e:
        send_message_callback(f"❌ Error: {str(e)}")

def stop_process(process_id):
    if process_id in running_processes:
        process = running_processes[process_id]
        try:
            # প্রসেস গ্রুপ কিল করা (যাতে চাইল্ড প্রসেসও মরে)
            os.killpg(os.getpgid(process.pid), signal.SIGTERM) 
            # উইন্ডোজ হলে শুধু: process.terminate() ব্যবহার করো
        except:
            process.terminate()
        
        del running_processes[process_id]
        return True
    return False

def get_running_list():
    return list(running_processes.keys())
    
