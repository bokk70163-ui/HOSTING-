import os
import shutil
from config import BASE_DIR

def create_project_folder(folder_name):
    path = os.path.join(BASE_DIR, folder_name)
    if not os.path.exists(path):
        os.makedirs(path)
        # Create mandatory files
        with open(os.path.join(path, "requirements.txt"), "w") as f:
            f.write("")
        with open(os.path.join(path, ".env"), "w") as f:
            f.write("")
        return True
    return False

def list_contents(subpath=""):
    full_path = os.path.join(BASE_DIR, subpath)
    if not os.path.exists(full_path):
        return [], []
    
    items = os.listdir(full_path)
    folders = []
    files = []
    
    for item in items:
        if os.path.isdir(os.path.join(full_path, item)):
            folders.append(item)
        else:
            files.append(item)
    return folders, files

def create_file(path, filename, content):
    full_path = os.path.join(BASE_DIR, path, filename)
    with open(full_path, "w") as f:
        f.write(content)

def read_file(path, filename):
    full_path = os.path.join(BASE_DIR, path, filename)
    if os.path.exists(full_path):
        with open(full_path, "r") as f:
            return f.read()
    return None

def delete_item(path, item_name):
    full_path = os.path.join(BASE_DIR, path, item_name)
    if os.path.exists(full_path):
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        return True
    return False

def add_env_variable(path, key, value):
    env_path = os.path.join(BASE_DIR, path, ".env")
    with open(env_path, "a") as f:
        f.write(f"\n{key}={value}")

def create_file_with_path(base_path, filename, content):
    if "/" in filename:
        parts = filename.split("/")
        folder_part = "/".join(parts[:-1])
        actual_filename = parts[-1]
        full_folder_path = os.path.join(BASE_DIR, base_path, folder_part) if base_path else os.path.join(BASE_DIR, folder_part)
        if not os.path.exists(full_folder_path):
            os.makedirs(full_folder_path)
        full_file_path = os.path.join(full_folder_path, actual_filename)
    else:
        full_file_path = os.path.join(BASE_DIR, base_path, filename) if base_path else os.path.join(BASE_DIR, filename)
    
    with open(full_file_path, "w") as f:
        f.write(content)

def move_file(src_path, src_filename, dest_folder):
    try:
        src_full = os.path.join(BASE_DIR, src_path, src_filename) if src_path else os.path.join(BASE_DIR, src_filename)
        dest_full = os.path.join(BASE_DIR, dest_folder, src_filename) if dest_folder else os.path.join(BASE_DIR, src_filename)
        
        if not os.path.exists(src_full):
            return False
        if os.path.exists(dest_full) and src_full != dest_full:
            return False
        if src_full == dest_full:
            return False
            
        shutil.move(src_full, dest_full)
        return True
    except Exception:
        return False

def rename_file(path, old_name, new_name):
    try:
        if old_name == new_name:
            return False
            
        if "/" in new_name:
            parts = new_name.split("/")
            folder_part = "/".join(parts[:-1])
            actual_new_name = parts[-1]
            new_folder_path = os.path.join(BASE_DIR, path, folder_part) if path else os.path.join(BASE_DIR, folder_part)
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
            old_full = os.path.join(BASE_DIR, path, old_name) if path else os.path.join(BASE_DIR, old_name)
            new_full = os.path.join(new_folder_path, actual_new_name)
        else:
            old_full = os.path.join(BASE_DIR, path, old_name) if path else os.path.join(BASE_DIR, old_name)
            new_full = os.path.join(BASE_DIR, path, new_name) if path else os.path.join(BASE_DIR, new_name)
        
        if not os.path.exists(old_full):
            return False
        if os.path.exists(new_full):
            return False
            
        shutil.move(old_full, new_full)
        return True
    except Exception:
        return False

def get_all_folders(base_path=""):
    folders = []
    full_path = os.path.join(BASE_DIR, base_path) if base_path else BASE_DIR
    
    if not os.path.exists(full_path):
        return folders
    
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            rel_path = os.path.join(base_path, item) if base_path else item
            folders.append(rel_path)
            folders.extend(get_all_folders(rel_path))
    
    return folders
    
