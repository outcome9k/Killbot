from flask import Flask, request
import telebot
import re
import requests

# --- Telegram Bot Token ---
BOT_TOKEN = "7556380686:AAHkY7xVjw4j14fcQy-5dlCGu5rcXha6vRU"
bot = telebot.TeleBot(BOT_TOKEN)

# --- Flask app ---
app = Flask(__name__)

@app.route('/')
def home():
    return "KillBot API is running ✅"

@app.route('/kill', methods=['GET', 'POST'])
def kill_route():
    if request.method == 'POST':
        data = request.get_json(force=True)
        card = data.get('card')
        return {"status": "ok", "card": card}, 200
    else:
        return {"status": "GET ok"}, 200

# --- Telegram Command Handlers ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "<b>Welcome!</b>\nUse /kill CC|MM|YY|CVV",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['kill'])
def handle_kill(message):
    try:
        command_text = message.text.split(' ', 1)[1]
    except IndexError:
        bot.reply_to(message, "⚠️ Format: /kill CC|MM|YY|CVV")
        return

    match = re.match(r'(\d{16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})', command_text)
    if not match:
        bot.reply_to(message, "❌ Invalid format.")
        return

    full_cc = match.group(0)
    payload = {'card': full_cc}

    try:
        response = requests.post("https://killbot-a7mt.onrender.com/kill", json=payload)
        bot.reply_to(message, f"✅ Response:\n<code>{response.text}</code>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"🚫 Error: {e}")

# --- Run bot in background ---
import threading
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot).start()    pan = match.group(1)
    masked = pan[:6] + '*' * (len(pan)-10) + pan[-4:] if len(pan) > 10 else pan[:4] + '****' + pan[-4:]

    sent_message = bot.reply_to(message, f"<i>Kill initiated for <code>{masked}|{match.group(2)}|{match.group(3)}|{match.group(4)}</code>. Please wait...</i>", parse_mode='HTML')

    payload = {
        'chat_id': message.chat.id,
        'message_id': sent_message.message_id,
        'card': full_cc_string
    }

    headers = {
        'Content-Type': 'application/json',
        # add an authorization header if API expects it:
        # 'Authorization': 'Bearer YOUR_API_KEY'
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=20)
    except requests.exceptions.RequestException as e:
        logging.exception("Request to API failed")
        bot.edit_message_text(f"<b>Error:</b> Could not contact API. <code>{e}</code>",
                              chat_id=message.chat.id, message_id=sent_message.message_id, parse_mode='HTML')
        return

    # useful debug: include resp.text in logs (don't print sensitive data publicly)
    logging.info("API status: %s body: %s", resp.status_code, resp.text[:1000])

    if resp.status_code == 200:
        bot.edit_message_text(f"<b>Done:</b> API accepted the task. Response: <code>{resp.text}</code>",
                              chat_id=message.chat.id, message_id=sent_message.message_id, parse_mode='HTML')
    elif resp.status_code == 405:
        bot.edit_message_text("<b>Error:</b> API replied 405 Method Not Allowed. "
                              "That means this endpoint doesn't accept the method you used (POST/GET mismatch).",
                              chat_id=message.chat.id, message_id=sent_message.message_id, parse_mode='HTML')
    else:
        bot.edit_message_text(f"<b>Error:</b> API responded with status {resp.status_code}. Response body: <code>{resp.text}</code>",
                              chat_id=message.chat.id, message_id=sent_message.message_id, parse_mode='HTML')

if __name__ == "__main__":
    bot.polling(none_stop=True)
