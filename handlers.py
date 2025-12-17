from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from file_manager import *
from process_manager import run_script, stop_process, pause_process, resume_process, get_running_list
from config import BASE_DIR
import threading
import asyncio
import os

FOLDER_NAME, FILE_NAME, FILE_CONTENT, ENV_KEY, ENV_VALUE, EDIT_CONTENT, NEW_FILENAME, UPLOAD_FILE = range(8)

# ... (বাকি উপরের সব কোড আগের মতোই থাকবে, শুধু run_command_handler পরিবর্তন হবে) ...

# --- RUN Command (/run folder file) ---
async def run_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /run <folder_name> <file_name>")
        return

    folder_name = args[0]
    file_name = args[1]
    chat_id = update.effective_chat.id
    bot = context.bot
    loop = asyncio.get_running_loop()
    
    await update.message.reply_text(f"[Info] Initializing {file_name}...\nYou will receive a log file after completion.")

    # ছোট স্ট্যাটাস মেসেজ পাঠানোর ফাংশন
    def status_callback(text):
        try:
            asyncio.run_coroutine_threadsafe(
                bot.send_message(chat_id=chat_id, text=f"```{text}```", parse_mode="Markdown"),
                loop
            )
        except Exception:
            pass

    # কাজ শেষ হলে ফাইল পাঠানোর ফাংশন
    def completion_callback(file_path, success):
        async def send_file():
            try:
                if os.path.exists(file_path):
                    caption = "✅ Process Finished Successfully" if success else "❌ Process Failed/Stopped"
                    await bot.send_document(
                        chat_id=chat_id, 
                        document=file_path, 
                        caption=caption,
                        filename=os.path.basename(file_path)
                    )
                    # পাঠানোর পর সার্ভার ক্লিন রাখতে ফাইল ডিলেট করতে পারেন (ঐচ্ছিক)
                    # os.remove(file_path) 
                else:
                    await bot.send_message(chat_id=chat_id, text="[Error] Log file generation failed.")
            except Exception as e:
                await bot.send_message(chat_id=chat_id, text=f"[Error] Sending log file failed: {e}")

        asyncio.run_coroutine_threadsafe(send_file(), loop)

    # নতুন থ্রেডে স্ক্রিপ্ট রান করা
    threading.Thread(
        target=run_script, 
        args=(folder_name, file_name, status_callback, completion_callback)
    ).start()

# ... (বাকি নিচের সব কোড যেমন running_list_handler আগের মতোই থাকবে) ...

# --- Create Folder (/cf) ---
async def start_cf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter Folder Name:")
    return FOLDER_NAME

async def create_folder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    if create_project_folder(name):
        await update.message.reply_text(f"[Success] Folder '{name}' created with requirements.txt and .env")
    else:
        await update.message.reply_text("[Error] Folder already exists.")
    return ConversationHandler.END

# --- List Folder (/lf) ---
async def list_folders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_path = context.user_data.get("current_path", "")
    folders, files = list_contents(current_path)
    
    keyboard = []
    for f in folders:
        keyboard.append([InlineKeyboardButton(f"[Folder] /{f}", callback_data=f"nav_folder|{f}")])
    for f in files:
        keyboard.append([InlineKeyboardButton(f"[File] {f}", callback_data=f"nav_file|{f}")])
    
    controls = []
    if current_path:
        controls.append(InlineKeyboardButton("<< Back", callback_data="nav_back"))
    controls.append(InlineKeyboardButton("+ Add File", callback_data="act_add_file"))
    controls.append(InlineKeyboardButton("+ Add Folder", callback_data="act_add_folder"))
    
    keyboard.append(controls)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = f"Current Path: {current_path if current_path else 'Root'}"
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup)
    else:
        await update.message.reply_text(msg, reply_markup=reply_markup)

# --- Button Handler ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    action = data[0]
    
    current_path = context.user_data.get("current_path", "")

    if action == "nav_folder":
        folder_name = data[1]
        context.user_data["current_path"] = os.path.join(current_path, folder_name) if current_path else folder_name
        await list_folders(update, context)

    elif action == "nav_back":
        if current_path:
            context.user_data["current_path"] = os.path.dirname(current_path)
        await list_folders(update, context)

    elif action == "nav_file":
        file_name = data[1]
        content = read_file(current_path, file_name)
        context.user_data["selected_file"] = file_name
        
        keyboard = [
            [InlineKeyboardButton("Edit", callback_data=f"act_edit|{file_name}"),
             InlineKeyboardButton("Delete", callback_data=f"act_del|{file_name}")],
            [InlineKeyboardButton("Move", callback_data=f"act_move|{file_name}"),
             InlineKeyboardButton("Rename", callback_data=f"act_rename|{file_name}")]
        ]
        
        if file_name == ".env":
            keyboard.append([InlineKeyboardButton("+ Add Variable", callback_data="act_add_var")])

        keyboard.append([InlineKeyboardButton("<< Back List", callback_data="nav_back_list")])
        
        if content is None:
            content = "(Empty or unreadable)"
        
        if len(content) > 3500:
            content = content[:3500] + "\n... (truncated)"
        
        # Markdown Code Block for click-to-copy
        msg_text = f"File: {file_name}\n\n```\n{content}\n```"
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif action == "nav_back_list":
        await list_folders(update, context)

    elif action == "act_add_file":
        keyboard = [
            [InlineKeyboardButton("Upload File", callback_data="act_upload")],
            [InlineKeyboardButton("Write Code", callback_data="act_write")],
            [InlineKeyboardButton("Cancel", callback_data="nav_back_list")]
        ]
        await query.edit_message_text("How to add file?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == "act_upload":
        await query.message.reply_text("Upload your file now:")
        return UPLOAD_FILE

    elif action == "act_write":
        await query.message.reply_text("Enter file name (with extension, e.g. folder/file.py):")
        context.user_data["action_type"] = "file"
        return FILE_NAME

    elif action == "act_add_folder":
        await query.message.reply_text("Enter new folder name:")
        context.user_data["action_type"] = "folder"
        return FILE_NAME
        
    elif action == "act_del":
        file_name = data[1]
        delete_item(current_path, file_name)
        await query.answer("File Deleted!")
        await list_folders(update, context)

    elif action == "act_add_var":
        await query.message.reply_text("Enter Variable Name (KEY):")
        return ENV_KEY

    elif action == "act_edit":
        file_name = data[1]
        context.user_data["edit_filename"] = file_name
        await query.message.reply_text(f"Enter new content for '{file_name}':")
        return EDIT_CONTENT

    elif action == "act_move":
        file_name = data[1]
        context.user_data["move_filename"] = file_name
        folders = get_all_folders()
        keyboard = [[InlineKeyboardButton("[Folder] Root", callback_data="move_to|")]]
        for folder in folders:
            keyboard.append([InlineKeyboardButton(f"[Folder] {folder}", callback_data=f"move_to|{folder}")])
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="nav_back_list")])
        await query.edit_message_text(f"Where to move '{file_name}'?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == "move_to":
        dest_folder = data[1] if len(data) > 1 else ""
        file_name = context.user_data.get("move_filename")
        if move_file(current_path, file_name, dest_folder):
            await query.answer("File Moved!")
        else:
            await query.answer("Move Failed!")
        await list_folders(update, context)

    elif action == "act_rename":
        file_name = data[1]
        context.user_data["rename_old_name"] = file_name
        await query.message.reply_text(f"Enter new name for '{file_name}':")
        return NEW_FILENAME

# --- File Creation Flow ---
async def file_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    action_type = context.user_data.get("action_type")
    current_path = context.user_data.get("current_path", "")

    if action_type == "folder":
        full_path = os.path.join(current_path, name) if current_path else name
        create_project_folder(full_path)
        await update.message.reply_text("Folder created.")
        return ConversationHandler.END
    else:
        context.user_data["temp_filename"] = name
        await update.message.reply_text("Enter code/text content:")
        return FILE_CONTENT

async def file_content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = update.message.text
    filename = context.user_data["temp_filename"]
    path = context.user_data.get("current_path", "")
    
    create_file_with_path(path, filename, content)
    await update.message.reply_text(f"[Success] {filename} saved.")
    return ConversationHandler.END

async def edit_content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_content = update.message.text
    filename = context.user_data.get("edit_filename")
    path = context.user_data.get("current_path", "")
    
    create_file(path, filename, new_content)
    await update.message.reply_text(f"[Success] {filename} updated.")
    return ConversationHandler.END

async def rename_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    old_name = context.user_data.get("rename_old_name")
    path = context.user_data.get("current_path", "")
    
    if rename_file(path, old_name, new_name):
        await update.message.reply_text(f"[Success] Renamed '{old_name}' to '{new_name}'.")
    else:
        await update.message.reply_text("[Error] Rename failed.")
    return ConversationHandler.END

async def file_upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("[Error] Please upload a file.")
        return UPLOAD_FILE
    
    document = update.message.document
    file_name = document.file_name
    path = context.user_data.get("current_path", "")
    
    try:
        file = await context.bot.get_file(document.file_id)
        file_path = os.path.join(BASE_DIR, path, file_name) if path else os.path.join(BASE_DIR, file_name)
        
        if "/" in file_name:
            parts = file_name.split("/")
            folder_part = "/".join(parts[:-1])
            full_folder = os.path.join(BASE_DIR, path, folder_part) if path else os.path.join(BASE_DIR, folder_part)
            if not os.path.exists(full_folder):
                os.makedirs(full_folder)
            file_path = os.path.join(full_folder, parts[-1])
        
        await file.download_to_drive(file_path)
        await update.message.reply_text(f"[Success] '{file_name}' uploaded!")
    except Exception as e:
        await update.message.reply_text(f"[Error] Upload failed: {str(e)}")
    
    return ConversationHandler.END

# --- ENV Variable Flow ---
async def env_key_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["env_key"] = update.message.text
    await update.message.reply_text("Enter Value:")
    return ENV_VALUE

async def env_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = context.user_data["env_key"]
    value = update.message.text
    path = context.user_data.get("current_path", "")
    add_env_variable(path, key, value)
    await update.message.reply_text("[Success] Environment variable added.")
    return ConversationHandler.END

# --- Running Processes (/running) ---
async def running_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processes = get_running_list()
    if not processes:
        await update.message.reply_text("No running processes.")
        return

    keyboard = []
    for p in processes:
        keyboard.append([InlineKeyboardButton(f"[Process] {p}", callback_data=f"proc_opt|{p}")])
    
    await update.message.reply_text("Running Processes:", reply_markup=InlineKeyboardMarkup(keyboard))

async def process_control_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("|")
    
    if data[0] == "proc_opt":
        pid = data[1]
        keyboard = [
            [InlineKeyboardButton("Pause", callback_data=f"proc_pause|{pid}"),
             InlineKeyboardButton("Resume", callback_data=f"proc_resume|{pid}")],
            [InlineKeyboardButton("Stop", callback_data=f"proc_stop|{pid}")],
            [InlineKeyboardButton("<< Back", callback_data="proc_back")]
        ]
        await query.edit_message_text(f"Process Options: {pid}", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data[0] == "proc_stop":
        pid = data[1]
        if stop_process(pid):
            await query.answer("Process Stopped.")
            await query.edit_message_text(f"[Stopped] {pid}")
        else:
            await query.answer("Process not found or already stopped.")

    elif data[0] == "proc_pause":
        pid = data[1]
        if pause_process(pid):
            await query.answer("Process Paused.")
        else:
            await query.answer("Failed to pause.")

    elif data[0] == "proc_resume":
        pid = data[1]
        if resume_process(pid):
            await query.answer("Process Resumed.")
        else:
            await query.answer("Failed to resume.")
            
    elif data[0] == "proc_back":
        await running_list_handler(update, context)
                              
