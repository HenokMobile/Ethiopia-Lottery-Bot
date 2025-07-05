
import telebot
from telebot import types
import sqlite3
import random
import time
import traceback

# ====== Configuration ======
TOKEN = '8103310198:AAGhOrJqnAU5_2csrs5fBA47WA_Lj4zAVFM'  # Replace with your actual token
bot = telebot.TeleBot(TOKEN)
ADMIN_CHAT_ID = "7927204668"  # Replace with your admin chat ID

# Database connection
conn = sqlite3.connect('ethiowin.db', check_same_thread=False)
cur = conn.cursor()

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    referred_by INTEGER,
    birr INTEGER DEFAULT 0,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS lottery_tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    number INTEGER,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
""")

conn.commit()

# Constants
REGISTER_BONUS = 10
REFERRAL_BONUS = 5
TICKET_COST = 5
MIN_WITHDRAW = 50

# Lottery rewards - smaller amounts with better chances
lottery_rewards = {
    1: 100, 2: 80, 3: 60, 4: 50, 5: 40,
    6: 30, 7: 25, 8: 20, 9: 15, 10: 10,
    11: 8, 12: 6, 13: 5, 14: 3, 15: 2
}

# ====== Payment Handler Variables ======
PAYMENT_METHODS = {
    "telebirr": {
        "name": "በTelebirr",
        "account_number": "0974363991",
        "account_name": "Henok Belayneh Bedecho",
        "steps": [
            "💰ማስገባት የምትፈልጉትን የገንዘብ መጠን ያስገቡ",
            "📱የምታስገቡበት ስልክ ቁጥር ያስገቡ",
            "💳👇👇👇"
        ],
        "confirmation": "ካስገቡት በኋላ screenshot ይላኩ እና ያረጋገጡ 👇",
        "success_msg": "በ30 ደቂቃ ውስጥ በAccount ገቢ ይሆናል"
    },
    "cbe": {
        "name": "በCBE",
        "account_number": "1000647265123",
        "account_name": "Henok Belayneh Bedecho",
        "steps": [
            "ማስገባት የምትፈልጉትን የገንዘብ መጠን ያስገቡ ይላኩ",
            "የምታስገቡበት Account ቁጥር ያስገቡ እና ይላኩ",
            "የኔን የCBE ቁጥር እና ስም አስገባ (ቁጥር '1000647265123') (ስም 'Henok Belayneh Bedecho')"
        ],
        "confirmation": "ካስገቡት በኋላ screenshot ይላኩ እና ያረጋገጡ",
        "success_msg": "ብር በ 30 ደቂቃ ውስጥ በAccountገቢ ይሆናል"
    },
    "cbebirr": {
        "name": "በCBEbirr",
        "account_number": "0974363991",
        "account_name": "Henok Belayneh Bedecho",
        "steps": [
            "ማስገባት የምትፈልጉትን የገንዘብ መጠን ያስገቡ ይላኩ",
            "የምታስገቡበት ስልክ ቁጥር ያስገቡ እና ይላኩ",
            "የኔን የCBEbirr ቁጥር እና ስም አስገባ (ቁጥር '0974363991') (ስም 'Henok Belayneh Bedecho')"
        ],
        "confirmation": "ካስገቡት በኋላ screenshot ይላኩ እና ያረጋገጡ",
        "success_msg": "ብር በ 30 ደቂቃ ውስጥ በAccountገቢ ይሆናል"
    },
    "card": {
        "name": "በCard",
        "account_number": "0974363991",
        "account_name": "Henok Belayneh Bedecho",
        "steps": [
            "ማስገባት የምትፈልጉትን የገንዘብ መጠን ያስገቡ ይላኩ",
            "የምታስገቡበት ስልክ ቁጥር ያስገቡ እና ይላኩ",
            "የኔን የስልክ ቁጥር አስገባ (ቁጥር '0974363991')"
        ],
        "confirmation": "ካስገቡት በኋላ screenshot ይላኩ እና ያረጋገጡ",
        "success_msg": "ብር በ 30 ደቂቃ ውስጥ በAccountገቢ ይሆናል"
    }
}

# ====== Withdraw Handler Variables ======
WITHDRAW_METHODS = {
    "telebirr": {
        "name": "በTelebirr",
        "steps": [
            "ያንተን የTelebirr ስልክ ቁጥር ላክ",
            "ያንተን ሙሉ ስም ላክ",
            "ወጪ ለማድረግ የምትፈልገውን የገንዘብ መጠን አስገባ"
        ],
        "success_msg": "ገንዘብ በ30ደቂቃ ውስጥ ወጪ ይደረጋል"
    },
    "cbe": {
        "name": "በCBE",
        "steps": [
            "ያንተን የCBE Account ቁጥር ላክ",
            "ያንተን ሙሉ ስም ላክ",
            "ወጪ ለማድረግ የምትፈልገውን የገንዘብ መጠን አስገባ"
        ],
        "success_msg": "ገንዘብ በ30ደቂቃ ውስጥ ወጪ ይደረጋል"
    },
    "cbebirr": {
        "name": "በCBEbirr",
        "steps": [
            "ያንተን የCBEbirr ስልክ ቁጥር ላክ",
            "ያንተን ሙሉ ስም ላክ",
            "ወጪ ለማድረግ የምትፈልገውን የገንዘብ መጠን አስገባ"
        ],
        "success_msg": "ገንዘብ በ30ደቂቃ ውስጥ ወጪ ይደረጋል"
    },
    "card": {
        "name": "በCard",
        "steps": [
            "❌የCard አገልግሎት አልተጀመረም በሌላ አማራጭ ወጪ ያድርጉ"
        ],
        "success_msg": ""
    }
}

# ====== Helper Functions ======
def get_balance(user_id):
    cur.execute("SELECT birr FROM users WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    return result[0] if result else 0

def create_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("💰 ቀሪ ሂሳብ"),
        types.KeyboardButton("🎫 ሎተሪ ይጫወቱ"), 
        types.KeyboardButton("👥 ያጋቡ ብር ያግኙ"),
        types.KeyboardButton("🏧 ብር ማውጣት"),
        types.KeyboardButton("ℹ️ እርዳታ"),
        types.KeyboardButton("ግብ ላድርግ")
    ]
    markup.add(*buttons)
    return markup

def log_activity(user_id, action):
    print(f"[LOG] User {user_id} {action} at {time.strftime('%Y-%m-%d %H:%M:%S')}")

# ====== Main Bot Handlers ======
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        
        # Check if user exists
        cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if not cur.fetchone():
            # Check for referral
            referred_by = None
            if len(message.text.split()) > 1:
                try:
                    referred_by = int(message.text.split()[1])
                except ValueError:
                    pass
            
            # Add new user
            cur.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, referred_by, birr) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, first_name, last_name, referred_by, REGISTER_BONUS)
            )
            
            # Give referral bonus
            if referred_by:
                cur.execute("UPDATE users SET birr = birr + ? WHERE user_id = ?", (REFERRAL_BONUS, referred_by))
            
            conn.commit()
            log_activity(user_id, "registered")
            
            welcome_msg = f"🎉 እንኳን ደህና መጣህ {first_name}!\n\n" \
                         f"🎁 የመመዝገቢያ ቦነስ: {REGISTER_BONUS} ብር\n" \
                         f"💰 የእርስዎ ቀሪ ሂሳብ: {REGISTER_BONUS} ብር"
        else:
            balance = get_balance(user_id)
            welcome_msg = f"👋 እንደገና እንኳን ደህና መጣህ {first_name}!\n" \
                         f"💰 የእርስዎ ቀሪ ሂሳብ: {balance} ብር"
        
        bot.send_message(message.chat.id, welcome_msg, reply_markup=create_keyboard())
        
    except Exception as e:
        print(f"Error in start command: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

@bot.message_handler(func=lambda message: message.text == "💰 ቀሪ ሂሳብ")
def check_balance(message):
    try:
        balance = get_balance(message.from_user.id)
        bot.send_message(message.chat.id, f"💰 የእርስዎ ቀሪ ሂሳብ: {balance} ብር")
        log_activity(message.from_user.id, "checked balance")
    except Exception as e:
        print(f"Error in balance check: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

@bot.message_handler(func=lambda message: message.text == "🎫 ሎተሪ ይጫወቱ")
def play_lottery(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        if balance < TICKET_COST:
            bot.send_message(
                message.chat.id,
                f"🔴 በቂ ገንዘብ የለዎትም!\n"
                f"የትኬት ዋጋ: {TICKET_COST} ብር\n"
                f"የእርስዎ ቀሪ ሂሳብ: {balance} ብር"
            )
            return
        
        # Deduct ticket cost
        new_balance = balance - TICKET_COST
        cur.execute("UPDATE users SET birr = ? WHERE user_id = ?", (new_balance, user_id))
        
        # Generate lottery number - better chances with 1-10 range
        lottery_number = random.randint(1, 10)
        reward = lottery_rewards[lottery_number]
        
        # Add ticket to database
        cur.execute(
            "INSERT INTO lottery_tickets (user_id, number) VALUES (?, ?)",
            (user_id, lottery_number)
        )
        
        # Add reward to balance
        final_balance = new_balance + reward
        cur.execute("UPDATE users SET birr = ? WHERE user_id = ?", (final_balance, user_id))
        conn.commit()
        
        result_msg = f"🎫 የሎተሪ ትኬትዎ: #{lottery_number}\n\n"
        if reward > 0:
            result_msg += f"🎉 እንኳን ደስ አለዎት! {reward} ብር አሸንፈዋል!\n"
        else:
            result_msg += "😔 በዚህ ጊዜ አልተዘነፉም፣ እንደገና ይሞክሩ!\n"
        
        result_msg += f"💰 አዲስ ቀሪ ሂሳብ: {final_balance} ብር"
        
        bot.send_message(message.chat.id, result_msg)
        log_activity(user_id, f"played lottery, got {lottery_number}, won {reward}")
        
    except Exception as e:
        print(f"Error in lottery: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

@bot.message_handler(func=lambda message: message.text == "👥 ያጋቡ ብር ያግኙ")
def referral_info(message):
    try:
        user_id = message.from_user.id
        referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        
        # Count referrals
        cur.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,))
        referral_count = cur.fetchone()[0]
        
        msg = f"👥 የጓደኞች ግብዣ\n\n" \
              f"🔗 የእርስዎ ግብዣ ሊንክ:\n{referral_link}\n\n" \
              f"💰 ለእያንዳንዱ ጓደኛ: {REFERRAL_BONUS} ብር\n" \
              f"👥 ያጋበዋቸው ጓደኞች: {referral_count}\n" \
              f"💵 ከግብዣ የተገኘ ገቢ: {referral_count * REFERRAL_BONUS} ብር"
        
        bot.send_message(message.chat.id, msg)
        log_activity(user_id, "viewed referral info")
        
    except Exception as e:
        print(f"Error in referral info: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

@bot.message_handler(func=lambda message: message.text == "ℹ️ እርዳታ")
def help_info(message):
    try:
        help_text = """
ℹ️ እርዳታ እና መረጃ

🎫 ሎተሪ መጫወት:
• የትኬት ዋጋ: 5 ብር
• የመጀመሪያ ሽልማት: 100 ብር
• 10 የተለያዩ ሽልማቶች
• ከፍተኛ የማሸነፍ እድል!

💰 ግብ ማድረግ:
• Telebirr, CBE, CBEbirr, Card

🏧 ገንዘብ ማውጣት:
• ዝቅተኛ መጠን: 50 ብር
• ሁሉም የግብ ዘዴዎች ይደገፋሉ

👥 ጓደኞችን ማጋበት:
• ለእያንዳንዱ ጓደኛ 5 ብር
• ገደብ የለውም

📞 ድጋፍ: @admin_username
        """
        bot.send_message(message.chat.id, help_text)
        log_activity(message.from_user.id, "viewed help")
        
    except Exception as e:
        print(f"Error in help: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

# ====== Admin Commands ======
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    try:
        if str(message.from_user.id) != ADMIN_CHAT_ID:
            bot.send_message(message.chat.id, "🔴 የዚህ ትዕዛዝ ፍቃድ የለዎትም!")
            return
            
        markup = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton("📊 ስታቲስቲክስ", callback_data="admin_stats"),
            types.InlineKeyboardButton("👥 ተጠቃሚዎች", callback_data="admin_users"),
            types.InlineKeyboardButton("💰 ሂሳብ ማስተዳደር", callback_data="admin_balance"),
            types.InlineKeyboardButton("📢 መልእክት ላክ", callback_data="admin_broadcast")
        ]
        for btn in buttons:
            markup.add(btn)
            
        bot.send_message(message.chat.id, "🔧 Admin Panel", reply_markup=markup)
        
    except Exception as e:
        print(f"Error in admin panel: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_actions(call):
    try:
        if str(call.from_user.id) != ADMIN_CHAT_ID:
            bot.answer_callback_query(call.id, "🔴 ፍቃድ የለዎትም!")
            return
            
        action = call.data.split('_')[1]
        
        if action == 'stats':
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM lottery_tickets")
            total_tickets = cur.fetchone()[0]
            
            cur.execute("SELECT SUM(birr) FROM users")
            total_balance = cur.fetchone()[0] or 0
            
            stats_msg = f"""
📊 የBot ስታቲስቲክስ:

👥 ጠቅላላ ተጠቃሚዎች: {total_users}
🎫 የተሸጡ ትኬቶች: {total_tickets}
💰 ጠቅላላ ሂሳብ: {total_balance} ብር
            """
            bot.send_message(call.message.chat.id, stats_msg)
            
        elif action == 'users':
            cur.execute("SELECT user_id, first_name, birr FROM users ORDER BY birr DESC LIMIT 10")
            top_users = cur.fetchall()
            
            users_msg = "👥 ከፍተኛ ተጠቃሚዎች:\n\n"
            for i, (user_id, name, balance) in enumerate(top_users, 1):
                users_msg += f"{i}. {name} - {balance} ብር\n"
                
            bot.send_message(call.message.chat.id, users_msg)
            
        elif action == 'balance':
            msg = bot.send_message(call.message.chat.id, "💰 ተጠቃሚ ID ያስገቡ:")
            bot.register_next_step_handler(msg, admin_balance_management)
            
        elif action == 'broadcast':
            msg = bot.send_message(call.message.chat.id, "📢 ለሁሉም ተጠቃሚዎች የሚላከውን መልእክት ያስገቡ:")
            bot.register_next_step_handler(msg, admin_broadcast_message)
            
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        print(f"Error in admin actions: {e}")
        bot.answer_callback_query(call.id, "🔴 ስህተት ተከስቷል")

def admin_balance_management(message):
    try:
        user_id = int(message.text)
        
        cur.execute("SELECT first_name, birr FROM users WHERE user_id = ?", (user_id,))
        user_data = cur.fetchone()
        
        if not user_data:
            bot.send_message(message.chat.id, "🔴 ተጠቃሚ አልተገኘም!")
            return
            
        name, balance = user_data
        
        markup = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton("➕ ሂሳብ ጨምር", callback_data=f"add_balance_{user_id}"),
            types.InlineKeyboardButton("➖ ሂሳብ ቀንስ", callback_data=f"sub_balance_{user_id}")
        ]
        for btn in buttons:
            markup.add(btn)
            
        bot.send_message(
            message.chat.id, 
            f"👤 {name}\n💰 ቀሪ ሂሳብ: {balance} ብር",
            reply_markup=markup
        )
        
    except ValueError:
        bot.send_message(message.chat.id, "🔴 ትክክለኛ ተጠቃሚ ID ያስገቡ!")
    except Exception as e:
        print(f"Error in balance management: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል")

def admin_broadcast_message(message):
    try:
        broadcast_msg = message.text
        
        cur.execute("SELECT user_id FROM users")
        all_users = cur.fetchall()
        
        sent_count = 0
        for (user_id,) in all_users:
            try:
                bot.send_message(user_id, f"📢 {broadcast_msg}")
                sent_count += 1
            except:
                pass
                
        bot.send_message(message.chat.id, f"✅ መልእክት ለ {sent_count} ተጠቃሚዎች ተልኳል")
        
    except Exception as e:
        print(f"Error in broadcast: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል")

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_balance_') or call.data.startswith('sub_balance_'))
def handle_balance_change(call):
    try:
        if str(call.from_user.id) != ADMIN_CHAT_ID:
            bot.answer_callback_query(call.id, "🔴 ፍቃድ የለዎትም!")
            return
            
        action, user_id = call.data.split('_', 2)[0], call.data.split('_', 2)[2]
        
        msg = bot.send_message(
            call.message.chat.id, 
            f"💰 መጠን ያስገቡ ({'ለመጨመር' if action == 'add' else 'ለመቀነስ'}):"
        )
        bot.register_next_step_handler(msg, process_balance_change, action, user_id)
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        print(f"Error in balance change: {e}")
        bot.answer_callback_query(call.id, "🔴 ስህተት ተከስቷል")

def process_balance_change(message, action, user_id):
    try:
        amount = float(message.text)
        
        if action == 'add':
            cur.execute("UPDATE users SET birr = birr + ? WHERE user_id = ?", (amount, user_id))
            action_text = "ተጨምሯል"
        else:
            cur.execute("UPDATE users SET birr = birr - ? WHERE user_id = ?", (amount, user_id))
            action_text = "ቀንሷል"
            
        conn.commit()
        
        cur.execute("SELECT birr FROM users WHERE user_id = ?", (user_id,))
        new_balance = cur.fetchone()[0]
        
        bot.send_message(
            message.chat.id, 
            f"✅ {amount} ብር {action_text}\n💰 አዲስ ቀሪ ሂሳብ: {new_balance} ብር"
        )
        
    except ValueError:
        bot.send_message(message.chat.id, "🔴 ትክክለኛ ቁጥር ያስገቡ!")
    except Exception as e:
        print(f"Error in processing balance change: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል")

# ====== Payment Handlers ======
@bot.message_handler(func=lambda message: message.text == "ግብ ላድርግ")
def handle_payment_start(message):
    try:
        markup = types.InlineKeyboardMarkup()
        for method in PAYMENT_METHODS:
            btn = types.InlineKeyboardButton(
                PAYMENT_METHODS[method]["name"],
                callback_data=f"payment_{method}"
            )
            markup.add(btn)

        bot.send_message(
            message.chat.id,
            "👇 የግብ ማድረጊያ ዘዴ ይምረጡ",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error in payment start: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

@bot.callback_query_handler(func=lambda call: call.data.startswith('payment_'))
def handle_payment_method(call):
    try:
        method = call.data.split('_')[1]
        user_data = PAYMENT_METHODS[method]

        bot.answer_callback_query(call.id, f"የ{user_data['name']} ዘዴ ተመርጧል")

        msg = bot.send_message(
            call.message.chat.id,
            f"🔹 {user_data['steps'][0]}"
        )

        bot.register_next_step_handler(msg, process_payment_amount, method, 1)

    except Exception as e:
        print(f"Error in payment method: {e}")
        bot.send_message(call.message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

def process_payment_amount(message, method, step):
    try:
        try:
            amount = float(message.text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "🔴 ትክክለኛ የገንዘብ መጠን ያስገቡ!")
            return

        user_data = PAYMENT_METHODS[method]
        msg = bot.send_message(
            message.chat.id,
            f"🔹 {user_data['steps'][1]}"
        )
        bot.register_next_step_handler(msg, process_payment_details, method, 2, amount)

    except Exception as e:
        print(f"Error in payment amount: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

def process_payment_details(message, method, step, amount):
    try:
        user_data = PAYMENT_METHODS[method]

        account_info = f"ቁጥር: {user_data['account_number']}"
        if 'account_name' in user_data:
            account_info += f"\nስም: {user_data['account_name']}"

        confirmation_msg = (
            f"🔹 {user_data['steps'][2]}\n\n"
            f"💳 የግብ ማድረጊያ ዝርዝር:\n"
            f"• መጠን: {amount} ብር\n"
            f"• ዘዴ: {user_data['name']}\n"
            f"• {account_info}\n\n"
            f"{user_data['confirmation']}"
        )

        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton(
            "አረጋግጥ",
            callback_data=f"confirm_{method}_{amount}"
        )
        markup.add(confirm_btn)

        bot.send_message(
            message.chat.id,
            confirmation_msg,
            reply_markup=markup
        )

    except Exception as e:
        print(f"Error in payment details: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def handle_payment_confirmation(call):
    try:
        _, method, amount = call.data.split('_')
        user_data = PAYMENT_METHODS[method]

        bot.answer_callback_query(call.id, "✅ የግብ ማድረጊያ ተመዝግቧል")

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ {user_data['success_msg']}\n\n"
                 f"• መጠን: {amount} ብር\n"
                 f"• ዘዴ: {user_data['name']}"
        )

    except Exception as e:
        print(f"Error in payment confirmation: {e}")
        bot.send_message(call.message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

# ====== Withdraw Handlers ======
@bot.message_handler(func=lambda message: message.text == "🏧 ብር ማውጣት")
def handle_withdraw_start(message):
    try:
        user_balance = get_balance(message.from_user.id)
        if user_balance < MIN_WITHDRAW:
            bot.send_message(
                message.chat.id,
                f"🔴 ዝቅተኛ የማውጣት መጠን {MIN_WITHDRAW} ብር ነው!\n"
                f"የእርስዎ ቀሪ ሂሳብ: {user_balance} ብር"
            )
            return

        markup = types.InlineKeyboardMarkup()
        for method in WITHDRAW_METHODS:
            btn = types.InlineKeyboardButton(
                WITHDRAW_METHODS[method]["name"],
                callback_data=f"withdraw_{method}"
            )
            markup.add(btn)

        bot.send_message(
            message.chat.id,
            "👇 የወጪ ዘዴ ይምረጡ",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error in withdraw start: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

@bot.callback_query_handler(func=lambda call: call.data.startswith('withdraw_'))
def handle_withdraw_method(call):
    try:
        method = call.data.split('_')[1]
        withdraw_data = WITHDRAW_METHODS[method]

        if method == "card":
            bot.send_message(call.message.chat.id, withdraw_data["steps"][0])
            return

        bot.answer_callback_query(call.id, f"የ{withdraw_data['name']} ዘዴ ተመርጧል")

        msg = bot.send_message(
            call.message.chat.id,
            f"🔹 {withdraw_data['steps'][0]}"
        )

        bot.register_next_step_handler(msg, process_withdraw_step, method, 1)

    except Exception as e:
        print(f"Error in withdraw method: {e}")
        bot.send_message(call.message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

def process_withdraw_step(message, method, step):
    try:
        withdraw_data = WITHDRAW_METHODS[method]

        if step < len(withdraw_data["steps"])-1:
            msg = bot.send_message(
                message.chat.id,
                f"🔹 {withdraw_data['steps'][step]}"
            )
            bot.register_next_step_handler(msg, process_withdraw_step, method, step+1)
        else:
            try:
                amount = float(message.text)
                user_balance = get_balance(message.from_user.id)

                if amount > user_balance:
                    bot.send_message(
                        message.chat.id,
                        f"🔴 በቂ ገንዘብ የለዎትም!\n"
                        f"የእርስዎ ቀሪ ሂሳብ: {user_balance} ብር"
                    )
                    return

                if amount < MIN_WITHDRAW:
                    bot.send_message(
                        message.chat.id,
                        f"🔴 ዝቅተኛ የማውጣት መጠን {MIN_WITHDRAW} ብር ነው!"
                    )
                    return

                # Deduct balance
                new_balance = user_balance - amount
                cur.execute(
                    "UPDATE users SET birr = ? WHERE user_id = ?",
                    (new_balance, message.from_user.id)
                )
                conn.commit()

                # Notify admin
                admin_msg = (
                    f"🔄 አዲስ የወጪ ጥያቄ!\n"
                    f"• ተጠቃሚ: {message.from_user.first_name} (@{message.from_user.username})\n"
                    f"• መጠን: {amount} ብር\n"
                    f"• ዘዴ: {withdraw_data['name']}\n"
                    f"• የተጠቃሚ ID: {message.from_user.id}\n"
                    f"• አዲስ ቀሪ ሂሳብ: {new_balance} ብር"
                )

                bot.send_message(
                    message.chat.id,
                    f"✅ {withdraw_data['success_msg']}\n"
                    f"• መጠን: {amount} ብር\n"
                    f"• ዘዴ: {withdraw_data['name']}"
                )

                bot.send_message(ADMIN_CHAT_ID, admin_msg)

            except ValueError:
                bot.send_message(message.chat.id, "🔴 ትክክለኛ የገንዘብ መጠን ያስገቡ!")

    except Exception as e:
        print(f"Error in withdraw process: {e}")
        bot.send_message(message.chat.id, "🔴 ስህተት ተከስቷል፣ እባክዎ ቆይተው እንደገና ይሞክሩ")

# ====== Run Bot ======
if __name__ == '__main__':
    print("🤖 Bot is starting...")
    try:
        bot.polling(none_stop=True, interval=3, timeout=30)
    except Exception as e:
        print(f"🔴 Bot stopped with error: {e}")
        traceback.print_exc()
    finally:
        conn.close()
        print("🔴 Bot has stopped")
