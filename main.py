import warnings
from telegram.warnings import PTBUserWarning
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.ext.filters import Document
from config import BOT_TOKEN
from handlers import *

warnings.filterwarnings("ignore", message=".*per_message=False.*", category=PTBUserWarning)

def main():
    print("Bot is starting...")
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation Handlers
    cf_handler = ConversationHandler(
        entry_points=[CommandHandler("cf", start_cf)],
        states={FOLDER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_folder_handler)]},
        fallbacks=[]
    )
    
    file_add_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^act_add_.*")],
        states={
            FILE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, file_name_handler)],
            FILE_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, file_content_handler)],
            ENV_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, env_key_handler)],
            ENV_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, env_value_handler)],
        },
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^nav_.*")],
        per_message=False
    )

    upload_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^act_upload$")],
        states={
            UPLOAD_FILE: [MessageHandler(filters.Document.ALL, file_upload_handler)],
        },
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^nav_.*")],
        per_message=False
    )

    write_code_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^act_write$")],
        states={
            FILE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, file_name_handler)],
            FILE_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, file_content_handler)],
        },
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^nav_.*")],
        per_message=False
    )

    edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^act_edit\\|.*")],
        states={
            EDIT_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_content_handler)],
        },
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^nav_.*")],
        per_message=False
    )

    rename_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^act_rename\\|.*")],
        states={
            NEW_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, rename_handler)],
        },
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^nav_.*")],
        per_message=False
    )

    # General Handlers
    app.add_handler(cf_handler)
    app.add_handler(file_add_handler)
    app.add_handler(upload_handler)
    app.add_handler(write_code_handler)
    app.add_handler(edit_handler)
    app.add_handler(rename_conv_handler)
    app.add_handler(CommandHandler("lf", list_folders))
    app.add_handler(CommandHandler("run", run_command_handler))
    app.add_handler(CommandHandler("running", running_list_handler))
    
    app.add_handler(CallbackQueryHandler(process_control_handler, pattern="^proc_.*"))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
