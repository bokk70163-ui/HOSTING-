import os

# তোমার টেলিগ্রাম বট টোকেন এখানে দাও
BOT_TOKEN = "BOT_TOKEN"

# যেখানে সব প্রজেক্ট সেভ হবে
BASE_DIR = "projects"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
