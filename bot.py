import telebot
import sqlite3
import random
import json
import os
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8629386115:AAGp0P8iNH9PiRtzRCxxF8If_7ZiodXf3X8"
ADMIN_ID = 7040677455

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ========== БД ==========
DB_FILE = "crimson_rp.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        nick TEXT,
        balance INTEGER DEFAULT 0,
        bank INTEGER DEFAULT 0,
        job TEXT DEFAULT 'Безработный',
        job_rank TEXT DEFAULT '',
        faction TEXT DEFAULT 'Нет',
        cars TEXT DEFAULT '[]',
        houses TEXT DEFAULT '[]',
        businesses TEXT DEFAULT '[]',
        boats TEXT DEFAULT '[]',
        planes TEXT DEFAULT '[]',
        passport INTEGER DEFAULT 0,
        license INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY,
        reward_type TEXT,
        reward_amount INTEGER,
        used_count INTEGER DEFAULT 0,
        max_uses INTEGER,
        expires TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS promo_used (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        user_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        items TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS shop_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        name TEXT,
        price INTEGER,
        description TEXT,
        forum_link TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS salary_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        comment TEXT,
        admin_id INTEGER,
        date TEXT
    )''')
    
    # Добавляем тестовые данные, если пусто
    c.execute("SELECT COUNT(*) FROM shop_items")
    if c.fetchone()[0] == 0:
        shop_items = [
            ('cars', 'BMW X5', 5000, 'Крутой внедорожник', ''),
            ('cars', 'Mercedes S63', 8000, 'Бизнес-класс', ''),
            ('houses', 'Особняк', 15000, 'Дом у озера', ''),
            ('houses', 'Апартаменты', 8000, 'В центре города', ''),
            ('boats', 'Yamaha 242', 12000, 'Скоростной катер', ''),
            ('planes', 'Cessna 172', 25000, 'Легкий самолет', ''),
        ]
        for item in shop_items:
            c.execute("INSERT INTO shop_items (category, name, price, description, forum_link) VALUES (?, ?, ?, ?, ?)", item)
    
    c.execute("SELECT COUNT(*) FROM cases")
    if c.fetchone()[0] == 0:
        items1 = json.dumps([{"type":"money","amount":100},{"type":"money","amount":200},{"type":"money","amount":500},{"type":"car","name":"Honda Civic"}])
        c.execute("INSERT INTO cases (name, price, items) VALUES (?, ?, ?)", ('Обычный кейс', 500, items1))
        items2 = json.dumps([{"type":"money","amount":1000},{"type":"money","amount":2000},{"type":"car","name":"BMW X5"},{"type":"house","name":"Особняк"}])
        c.execute("INSERT INTO cases (name, price, items) VALUES (?, ?, ?)", ('VIP кейс', 2000, items2))
    
    conn.commit()
    conn.close()

def get_player(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    p = c.fetchone()
    if not p:
        c.execute("INSERT INTO players (user_id, nick) VALUES (?, ?)", (user_id, str(user_id)))
        conn.commit()
        c.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        p = c.fetchone()
    conn.close()
    return {
        "user_id": p[0], "nick": p[1], "balance": p[2], "bank": p[3],
        "job": p[4], "job_rank": p[5], "faction": p[6],
        "cars": json.loads(p[7]), "houses": json.loads(p[8]),
        "businesses": json.loads(p[9]), "boats": json.loads(p[10]),
        "planes": json.loads(p[11]), "passport": p[12], "license": p[13]
    }

def update_player(user_id, **kwargs):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for k, v in kwargs.items():
        if k in ["cars", "houses", "businesses", "boats", "planes"]:
            v = json.dumps(v)
        c.execute(f"UPDATE players SET {k} = ? WHERE user_id = ?", (v, user_id))
    conn.commit()
    conn.close()

def get_top_players(limit=10):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, nick, balance FROM players ORDER BY balance DESC LIMIT ?", (limit,))
    top = c.fetchall()
    conn.close()
    return top

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
        InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
        InlineKeyboardButton("📦 Кейсы", callback_data="cases"),
        InlineKeyboardButton("🎫 Промокод", callback_data="promo"),
        InlineKeyboardButton("🏆 Топ игроков", callback_data="top"),
        InlineKeyboardButton("💸 Перевод", callback_data="transfer"),
        InlineKeyboardButton("👑 Админ панель", callback_data="admin_panel")
    )
    return kb

def profile_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔙 Главное меню", callback_data="menu"))
    return kb

def admin_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💰 Выдать зарплату", callback_data="admin_salary"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("🎫 Создать промокод", callback_data="admin_create_promo"),
        InlineKeyboardButton("🔙 Главное меню", callback_data="menu")
    )
    return kb

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    user_id = m.from_user.id
    nick = m.from_user.username or m.from_user.first_name
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO players (user_id, nick) VALUES (?, ?)", (user_id, nick))
        conn.commit()
    conn.close()
    bot.send_message(user_id, "🔥 Добро пожаловать в бота Crimson RP!\n\nИспользуй кнопки ниже.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data

    if data == "menu":
        bot.edit_message_text("🔥 Главное меню:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        return

    # ===== ПРОФИЛЬ =====
    if data == "profile":
        p = get_player(user_id)
        text = (
            f"👤 <b>Профиль игрока</b>\n\n"
            f"🆔 ID: {p['user_id']}\n"
            f"📛 Ник: {p['nick']}\n"
            f"💰 Наличные: {p['balance']}$\n"
            f"🏦 Банк: {p['bank']}$\n"
            f"💼 Работа: {p['job']} | {p['job_rank']}\n"
            f"⚔️ Фракция: {p['faction']}\n\n"
            f"🚗 Авто: {len(p['cars'])}\n"
            f"🏠 Домов: {len(p['houses'])}\n"
            f"🏢 Бизнесов: {len(p['businesses'])}\n"
            f"🛥️ Катеров: {len(p['boats'])}\n"
            f"✈️ Самолётов: {len(p['planes'])}\n\n"
            f"📄 Паспорт: {'✅' if p['passport'] else '❌'}\n"
            f"🚗 Права: {'✅' if p['license'] else '❌'}"
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=profile_menu())
        return

    # ===== ТОП =====
    if data == "top":
        top = get_top_players(10)
        text = "🏆 <b>Топ игроков по балансу</b>\n\n"
        for i, (uid, nick, balance) in enumerate(top, 1):
            text += f"{i}. {nick} — {balance}$\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=profile_menu())
        return

    # ===== ПЕРЕВОД =====
    if data == "transfer":
        bot.send_message(user_id, "Введите ID или ник игрока и сумму через пробел:\nПример: 123456789 500\nИли: @nick 500")
        bot.register_next_step_handler_by_chat_id(user_id, transfer_handler)
        bot.answer_callback_query(call.id)
        return

    # ===== ПРОМОКОД =====
    if data == "promo":
        bot.send_message(user_id, "Введите промокод:")
        bot.register_next_step_handler_by_chat_id(user_id, promo_handler)
        bot.answer_callback_query(call.id)
        return

    # ===== АДМИНКА =====
    if data == "admin_panel":
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Нет доступа!", show_alert=True)
            return
        bot.edit_message_text("👑 Админ панель", call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
        return

    if data == "admin_salary":
        if user_id != ADMIN_ID:
            return
        bot.send_message(user_id, "Введите: ID_игрока Сумма Комментарий\nПример: 123456789 500 За работу")
        bot.register_next_step_handler_by_chat_id(user_id, salary_handler)
        bot.answer_callback_query(call.id)
        return

    if data == "admin_create_promo":
        if user_id != ADMIN_ID:
            return
        bot.send_message(user_id, "Введите: КОД ТИП СУММА ЛИМИТ ДНЕЙ\nТипы: money (наличные), bank (банк)\nПример: PROMO100 money 100 50 7")
        bot.register_next_step_handler_by_chat_id(user_id, create_promo_handler)
        bot.answer_callback_query(call.id)
        return

    if data == "admin_stats":
        if user_id != ADMIN_ID:
            return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM players")
        players = c.fetchone()[0]
        c.execute("SELECT SUM(balance) FROM players")
        total_money = c.fetchone()[0] or 0
        conn.close()
        text = f"📊 Статистика сервера\n\n👥 Игроков: {players}\n💰 Денег в экономике: {total_money}$"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_menu())
        return

    # ===== МАГАЗИН =====
    if data == "shop":
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("🚗 Авто", callback_data="shop_cars"),
            InlineKeyboardButton("🏠 Дома", callback_data="shop_houses"),
            InlineKeyboardButton("🛥️ Яхты", callback_data="shop_boats"),
            InlineKeyboardButton("✈️ Самолёты", callback_data="shop_planes"),
            InlineKeyboardButton("🔙 Назад", callback_data="menu")
        )
        bot.edit_message_text("🛒 Выбери категорию:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        return

    if data.startswith("shop_"):
        category = data.split("_")[1]
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT name, price, description, forum_link FROM shop_items WHERE category = ?", (category,))
        items = c.fetchall()
        conn.close()
        if not items:
            bot.answer_callback_query(call.id, "Товаров пока нет", show_alert=True)
            return
        text = f"🛒 {category.upper()}\n\n"
        kb = InlineKeyboardMarkup(row_width=1)
        for name, price, desc, link in items:
            text += f"• {name} — {price}$\n"
            kb.add(InlineKeyboardButton(f"Купить {name}", callback_data=f"buy_{category}_{name}"))
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data="shop"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        return

    if data.startswith("buy_"):
        parts = data.split("_")
        category = parts[1]
        item_name = "_".join(parts[2:])
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT price, description FROM shop_items WHERE category = ? AND name = ?", (category, item_name))
        item = c.fetchone()
        conn.close()
        if not item:
            bot.answer_callback_query(call.id, "Товар не найден", show_alert=True)
            return
        price, desc = item
        p = get_player(user_id)
        if p["balance"] < price:
            bot.answer_callback_query(call.id, f"❌ Не хватает {price}$!", show_alert=True)
            return
        # Зачисление предмета
        if category == "cars":
            cars = p["cars"] + [item_name]
            update_player(user_id, cars=cars)
        elif category == "houses":
            houses = p["houses"] + [item_name]
            update_player(user_id, houses=houses)
        elif category == "boats":
            boats = p["boats"] + [item_name]
            update_player(user_id, boats=boats)
        elif category == "planes":
            planes = p["planes"] + [item_name]
            update_player(user_id, planes=planes)
        new_balance = p["balance"] - price
        update_player(user_id, balance=new_balance)
        bot.answer_callback_query(call.id, f"✅ {item_name} куплен!", show_alert=True)
        bot.edit_message_text(f"✅ Вы купили {item_name} за {price}$\n\n{desc}", call.message.chat.id, call.message.message_id, reply_markup=profile_menu())
        return

    # ===== КЕЙСЫ =====
    if data == "cases":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, name, price FROM cases")
        cases = c.fetchall()
        conn.close()
        if not cases:
            bot.answer_callback_query(call.id, "Кейсов пока нет", show_alert=True)
            return
        text = "📦 Доступные кейсы:\n\n"
        kb = InlineKeyboardMarkup(row_width=1)
        for cid, name, price in cases:
            text += f"• {name} — {price}$\n"
            kb.add(InlineKeyboardButton(f"Открыть {name}", callback_data=f"open_case_{cid}"))
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data="menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        return

    if data.startswith("open_case_"):
        case_id = int(data.split("_")[2])
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT name, price, items FROM cases WHERE id = ?", (case_id,))
        case = c.fetchone()
        conn.close()
        if not case:
            bot.answer_callback_query(call.id, "Кейс не найден", show_alert=True)
            return
        name, price, items_json = case
        items = json.loads(items_json)
        p = get_player(user_id)
        if p["balance"] < price:
            bot.answer_callback_query(call.id, f"❌ Не хватает {price}$!", show_alert=True)
            return
        # Выбор случайного предмета
        reward = random.choice(items)
        new_balance = p["balance"] - price
        update_player(user_id, balance=new_balance)
        # Зачисление предмета
        if reward["type"] == "money":
            update_player(user_id, balance=p["balance"] + reward["amount"])
            result = f"💰 +{reward['amount']}$"
        elif reward["type"] == "car":
            cars = p["cars"] + [reward["name"]]
            update_player(user_id, cars=cars)
            result = f"🚗 {reward['name']}"
        elif reward["type"] == "house":
            houses = p["houses"] + [reward["name"]]
            update_player(user_id, houses=houses)
            result = f"🏠 {reward['name']}"
        else:
            result = reward["name"]
        bot.answer_callback_query(call.id, f"🎉 Выпало: {result}!", show_alert=True)
        bot.edit_message_text(f"📦 {name}\n\nВыпало: {result}", call.message.chat.id, call.message.message_id, reply_markup=profile_menu())
        return

# ========== ОБРАБОТЧИКИ ==========
def transfer_handler(m):
    user_id = m.from_user.id
    try:
        parts = m.text.split()
        target = parts[0]
        amount = int(parts[1])
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if target.startswith("@"):
            nick = target[1:]
            c.execute("SELECT user_id FROM players WHERE nick = ?", (nick,))
            row = c.fetchone()
            if not row:
                bot.send_message(user_id, "❌ Игрок не найден")
                return
            target_id = row[0]
        else:
            target_id = int(target)
        p = get_player(user_id)
        if p["balance"] < amount:
            bot.send_message(user_id, "❌ Не хватает денег")
            return
        update_player(user_id, balance=p["balance"] - amount)
        target_p = get_player(target_id)
        update_player(target_id, balance=target_p["balance"] + amount)
        bot.send_message(user_id, f"✅ Переведено {amount}$ игроку {target_id}")
        bot.send_message(target_id, f"💰 Вам переведено {amount}$ от {p['nick']}")
        conn.close()
    except:
        bot.send_message(user_id, "❌ Ошибка! Формат: ID_или_ник сумма")

def promo_handler(m):
    user_id = m.from_user.id
    code = m.text.upper()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT reward_type, reward_amount, max_uses, used_count, expires FROM promocodes WHERE code = ?", (code,))
    promo = c.fetchone()
    if not promo:
        bot.send_message(user_id, "❌ Промокод не найден")
        return
    rt, ra, mu, uc, exp = promo
    if exp and datetime.now() > datetime.fromisoformat(exp):
        bot.send_message(user_id, "❌ Промокод истёк")
        return
    if uc >= mu:
        bot.send_message(user_id, "❌ Промокод уже использован")
        return
    c.execute("SELECT * FROM promo_used WHERE code = ? AND user_id = ?", (code, user_id))
    if c.fetchone():
        bot.send_message(user_id, "❌ Вы уже использовали этот промокод")
        return
    p = get_player(user_id)
    if rt == "money":
        update_player(user_id, balance=p["balance"] + ra)
        bot.send_message(user_id, f"✅ Промокод активирован! +{ra}$")
    elif rt == "bank":
        update_player(user_id, bank=p["bank"] + ra)
        bot.send_message(user_id, f"✅ Промокод активирован! +{ra}$ на счёт")
    c.execute("UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?", (code,))
    c.execute("INSERT INTO promo_used (code, user_id) VALUES (?, ?)", (code, user_id))
    conn.commit()
    conn.close()

def salary_handler(m):
    admin_id = m.from_user.id
    if admin_id != ADMIN_ID:
        return
    try:
        parts = m.text.split()
        target_id = int(parts[0])
        amount = int(parts[1])
        comment = " ".join(parts[2:])
        p = get_player(target_id)
        update_player(target_id, balance=p["balance"] + amount)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO salary_log (user_id, amount, comment, admin_id, date) VALUES (?, ?, ?, ?, ?)",
                  (target_id, amount, comment, admin_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        bot.send_message(admin_id, f"✅ Выдано {amount}$ игроку {target_id}")
        bot.send_message(target_id, f"💰 Вам выдана зарплата: {amount}$\nКомментарий: {comment}")
    except:
        bot.send_message(admin_id, "❌ Ошибка! Формат: ID Сумма Комментарий")

def create_promo_handler(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        parts = m.text.split()
        code = parts[0].upper()
        rt = parts[1].lower()
        ra = int(parts[2])
        mu = int(parts[3])
        days = int(parts[4])
        expires = (datetime.now() + timedelta(days=days)).isoformat()
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO promocodes (code, reward_type, reward_amount, max_uses, expires) VALUES (?, ?, ?, ?, ?)",
                  (code, rt, ra, mu, expires))
        conn.commit()
        conn.close()
        bot.send_message(m.from_user.id, f"✅ Промокод {code} создан!")
    except:
        bot.send_message(m.from_user.id, "❌ Ошибка! Формат: КОД ТИП СУММА ЛИМИТ ДНЕЙ")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    init_db()
    print("✅ Crimson RP бот запущен!")
    bot.infinity_polling()