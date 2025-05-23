import json
import time
import string
import random
import re
import threading
import os
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === НАСТРОЙКИ ===
ADMIN_ID = 5486843553
TOKEN = "7789577835:AAGUe_uhpUpodEM-GOfr3aR7TUk8_RMFUKg"
KEYS_FILE = "keys.json"

# === FLASK СЕРВЕР ===
flask_app = Flask(__name__)

def load_keys():
    try:
        with open(KEYS_FILE, "r") as f:
            keys = json.load(f)
            now = time.time()
            keys = [k for k in keys if k["expires"] > now]
            save_keys(keys)
            return keys
    except:
        return []

def save_keys(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

@flask_app.route("/check", methods=["POST"])
def check_key():
    data = request.json
    key = data.get("key")
    machine_id = data.get("machine_id")

    keys = load_keys()
    for entry in keys:
        if entry["key"] == key:
            if entry["used"] and entry["machine_id"] != machine_id:
                return jsonify({"valid": False, "message": "Ключ уже использован на другом устройстве"})
            if time.time() > entry["expires"]:
                return jsonify({"valid": False, "message": "Ключ просрочен"})
            entry["used"] = True
            entry["machine_id"] = machine_id
            save_keys(keys)
            return jsonify({"valid": True})
    return jsonify({"valid": False, "message": "Ключ не найден"})

# === УТИЛИТЫ ===
def generate_key(length=16):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def parse_duration(arg):
    match = re.match(r"^(\d+)([smhd])$", arg.lower())
    if not match:
        return None
    value, unit = match.groups()
    value = int(value)
    multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return value * multiplier[unit]

# === ТЕЛЕГРАМ-БОТ ===
async def handle_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Только админ может использовать эту команду.")
        return

    if not context.args:
        await update.message.reply_text("Формат: /generate 10m | 1h | 2d | 30s")
        return

    duration = parse_duration(context.args[0])
    if not duration:
        await update.message.reply_text("❌ Неверный формат. Примеры: 10m, 1h, 2d, 30s")
        return

    key = generate_key()
    keys = load_keys()
    keys.append({
        "key": key,
        "expires": time.time() + duration,
        "used": False,
        "machine_id": None
    })
    save_keys(keys)
    await update.message.reply_text(f"🔑 Ключ: `{key}` (на {context.args[0]})", parse_mode="Markdown")

async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keys = load_keys()
    now = time.time()
    if not keys:
        await update.message.reply_text("Нет активных ключей.")
        return

    msg = "📋 Активные ключи:\n"
    for k in keys:
        left = int(k["expires"] - now)
        status = "✅" if k["used"] else "🟢"
        msg += f"{status} `{k['key']}` — осталось {left // 60} мин\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Пример: /revoke ABC123KEY")
        return

    key_to_remove = context.args[0].strip().upper()
    keys = load_keys()
    keys = [k for k in keys if k["key"] != key_to_remove]
    save_keys(keys)
    await update.message.reply_text(f"❌ Ключ `{key_to_remove}` удалён", parse_mode="Markdown")

# === ЗАПУСК ВСЕГО ===
def run_flask():
    port = int(os.getenv("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()

    tg_app = ApplicationBuilder().token(TOKEN).build()
    tg_app.add_handler(CommandHandler("generate", handle_generate))
    tg_app.add_handler(CommandHandler("list", handle_list))
    tg_app.add_handler(CommandHandler("revoke", handle_revoke))
    tg_app.run_polling()
