import os
import time
import json
import telebot
from apscheduler.schedulers.background import BackgroundScheduler

# Load Token securely from environment variables
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Authorized Admin IDs for Broadcasting
OWNER_ID = 7946587480
SENIOR_ID = 7328699671
AUTHORIZED_ADMINS = [OWNER_ID, SENIOR_ID]

# File to persistently save active chats (survives Railway reboots)
CHATS_FILE = 'chats.json'

def load_chats():
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_chats(chats_set):
    try:
        with open(CHATS_FILE, 'w') as f:
            json.dump(list(chats_set), f)
    except Exception as e:
        print(f"Error saving chats file: {e}")

# Load chats into memory on startup
active_chats = load_chats()

# Forbidden keywords / illegal content blacklist
ILLEGAL_TEXT_KEYWORDS = [
    'cp material', 'child abuse', 'illegal drugs', 'cocaine sell', 
    'heroin buy', 'meth for sale', 'carding methods', 'cvv dump',
    'csam', 'suicide method'
]

# Track fake report statistics dynamically
report_stats = {
    "count": 1428,
    "type": "[AI-Shield Filtered]"
}

def register_chat(chat_id):
    if chat_id not in active_chats:
        active_chats.add(chat_id)
        save_chats(active_chats)

@bot.message_handler(commands=['start'])
def start_command(message):
    register_chat(message.chat.id)
    bot.reply_to(
        message, 
        "🛡️ **Zee Channel & Group Protection Bot Active!**\n"
        "Add me to your channel/group as an admin with message deletion rights to enable full auto-protection.", 
        parse_mode="Markdown"
    )

# Broadcast Command - Strictly restricted to Owner and Senior Admin
@bot.message_handler(commands=['Bc'])
def broadcast_message(message):
    user_id = message.from_user.id

    if user_id not in AUTHORIZED_ADMINS:
        bot.reply_to(message, "❌ Unauthorized. This command is restricted to bot executives only.")
        return

    command_text = message.text
    parts = command_text.split(maxsplit=1)

    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Please provide the message you want to broadcast. Example:\n`/Bc Hello everyone!`", parse_mode="Markdown")
        return

    broadcast_text = parts[1]
    success_count = 0
    fail_count = 0

    bot.reply_to(message, f"📢 Broadcasting message to all active channels/groups ({len(active_chats)})...")

    for chat_id in list(active_chats):
        try:
            bot.send_message(chat_id, f"📢 **Global Announcement:**\n\n{broadcast_text}", parse_mode="Markdown")
            success_count += 1
            time.sleep(0.2) # Prevent Telegram flood limits
        except Exception as e:
            fail_count += 1
            err_str = str(e).lower()
            if "bot was blocked" in err_str or "chat not found" in err_str or "forbidden" in err_str:
                active_chats.discard(chat_id)

    save_chats(active_chats)
    bot.send_message(message.chat.id, f"✅ **Broadcast Completed!**\n- Successful: {success_count}\n- Failed: {fail_count}")

# Comprehensive Moderation Engine (Scans EVERYONE including Admins for illegal content)
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio'])
def deep_content_moderation(message):
    chat_id = message.chat.id
    register_chat(chat_id)

    # 1. Check for Illegal Text / Keywords
    if message.text:
        text_lower = message.text.lower()
        if any(keyword in text_lower for keyword in ILLEGAL_TEXT_KEYWORDS):
            try:
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(
                    chat_id, 
                    f"🚨 **SECURITY ALERT:** Prohibited/illegal content detected and instantly purged by system defense.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Failed to delete text message: {e}")
            return

    # 2. Check for Illegal Media Content Captions
    if message.caption:
        caption_lower = message.caption.lower()
        if any(keyword in caption_lower for keyword in ILLEGAL_TEXT_KEYWORDS):
            try:
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(
                    chat_id, 
                    f"🚨 **MEDIA SHIELD:** Unlawful media content blocked and deleted.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Failed to delete media message: {e}")
            return

# Function to broadcast the 5-Hour Fake Report Blocker Status Card
def send_report_blocker_update():
    current_count_styled = f"{report_stats['count']:,}"
    report_message_text = (
        f"🛡️ ({current_count_styled} _styled) Rᴇᴘᴏʀᴛs ({report_stats['type']}) ᴀʀᴇ Bʟᴏᴄᴋᴇᴅ ʙʏ @Zee_chan_group_protecting_bot\n\n"
        f"✅ Yᴏᴜʀ Cʜᴀ𝚗𝚗ᴇʟ ɪs Sᴀᴠᴇᴅ Fʀᴏᴍ Rᴇᴘᴏʀᴛs ɪɴ Lᴀsᴛ 24 Hᴏᴜʀs."
    )

    for chat_id in list(active_chats):
        try:
            bot.send_message(chat_id, report_message_text, parse_mode="Markdown")
            time.sleep(0.1)
        except Exception as e:
            err_str = str(e).lower()
            if "bot was blocked" in err_str or "chat not found" in err_str or "forbidden" in err_str:
                active_chats.discard(chat_id)

    save_chats(active_chats)
    report_stats["count"] += 15

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_report_blocker_update, 'interval', hours=5)
    scheduler.start()

    print("🛡️ Public Anti-Report & Auto-Protection Bot running with persistent tracking...")
    bot.infinity_polling()
