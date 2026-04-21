import telebot
import sqlite3
import random
import json
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8629386115:AAGp0P8iNH9PiRtzRCxxF8If_7ZiodXf3X8"
ADMIN_ID = 7040677455

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DB_FILE = "crimson_rp.db"

# ========== БД ==========
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Игроки
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        nick TEXT,
        balance INTEGER DEFAULT 5000,
        bank INTEGER DEFAULT 0,
        job TEXT DEFAULT 'Безработный',
        faction TEXT DEFAULT 'Нет',
        cars TEXT DEFAULT '[]',
        houses TEXT DEFAULT '[]',
        businesses TEXT DEFAULT '[]',
        boats TEXT DEFAULT '[]',
        planes TEXT DEFAULT '[]',
        passport INTEGER DEFAULT 0,
        license INTEGER DEFAULT 0,
        work_time TEXT DEFAULT NULL,
        daily_date TEXT DEFAULT NULL
    )''')
    
    # Бизнесы
    c.execute('''CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        city TEXT,
        price INTEGER,
        salary INTEGER,
        tax INTEGER,
        owner_id INTEGER DEFAULT 0,
        owner_name TEXT DEFAULT '',
        description TEXT
    )''')
    
    # Самолёты (авиасалон)
    c.execute('''CREATE TABLE IF NOT EXISTS planes_shop (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        description TEXT
    )''')
    
    # Промокоды
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
    
    # Логи
    c.execute('''CREATE TABLE IF NOT EXISTS salary_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        comment TEXT,
        admin_id INTEGER,
        date TEXT
    )''')
    
    # Добавляем бизнесы, если пусто
    c.execute("SELECT COUNT(*) FROM businesses")
    if c.fetchone()[0] == 0:
        businesses = [
            # Город Дубровка
            ('Заправка', 'Дубровка', 3000000, 600000, 200000, '', 'Автозаправочный комплекс (АЗК) — розничная продажа топлива'),
            ('Магазин Пятёрочка', 'Дубровка', 4000000, 800700, 200000, '', 'Продуктовый магазин в центре города'),
            ('Шаурмечная', 'Дубровка', 6700000, 1000000, 400000, '', 'Быстрое питание, шаурма, фастфуд'),
            ('Ресторан', 'Дубровка', 9000000, 3000000, 1000000, 'ivanstein11', 'Элитное заведение с высокой кухней'),
            ('Бургерная', 'Дубровка', 6700000, 1000000, 400000, '', 'Бургеры, картошка фри, напитки'),
            ('СТО', 'Дубровка', 6700000, 1000000, 400000, '', 'Станция технического обслуживания автомобилей'),
            ('Мебельный магазин', 'Дубровка', 14000000, 6000000, 1700000, 'pampers_0000', 'Продажа мебели и предметов интерьера'),
            ('Автошкола', 'Дубровка', 20000000, 7000000, 1700000, '', 'Обучение вождению, подготовка водителей'),
            ('Автосалон', 'Дубровка', 40000000, 0, 2000000, 'MustafaPRO_PUBGmobile', 'Продажа автомобилей (зарплата от продаж)'),
            ('Завод и База дальнобойщиков', 'Дубровка', 40000000, 12000000, 3000000, 'Pelmen4ik', 'Промышленное производство и логистика'),
            ('Аэропорт', 'Дубровка', 40000000, 13000000, 3000000, 'Rick_sanhez45', 'Приём и отправка воздушных судов'),
            ('Нефтебаза', 'Дубровка', 45000000, 15000000, 4000000, 'Rick_sanhez45', 'Хранение и переработка нефтепродуктов'),
            # Город Арзамас
            ('Заправка', 'Арзамас', 3000000, 600000, 200000, 'pampers_0000', 'Автозаправочный комплекс (АЗК)'),
            ('СТО', 'Арзамас', 6700000, 1000000, 400000, 'PELMEN4IK_RIP', 'Станция технического обслуживания'),
            ('База дальнобойщиков', 'Арзамас', 20000000, 7000000, 1700000, 'Rick_sanhez45', 'Логистический терминал для большегрузов'),
        ]
        for b in businesses:
            c.execute("INSERT INTO businesses (name, city, price, salary, tax, owner_name, description) VALUES (?, ?, ?, ?, ?, ?, ?)", b)
    
    # Добавляем самолёты из скриншотов
    c.execute("SELECT COUNT(*) FROM planes_shop")
    if c.fetchone()[0] == 0:
        planes = [
            ('Cessna 172 (Красный)', 23000000, 'Американский лёгкий самолёт. Самый массовый самолёт в истории авиации.'),
            ('Cessna 172 (Зелёный)', 23000000, 'Американский лёгкий самолёт. Самый массовый самолёт в истории авиации.'),
            ('Cessna 185 Skywagon (Синий)', 25000000, 'Американский лёгкий самолёт компании Cessna.'),
            ('Як-52', 22000000, 'Советский спортивно-тренировочный самолёт.'),
            ('Як-55', 28000000, 'Одноместный пилотажный самолёт для тренировок и соревнований.'),
            ('Boeing-Stearman Model 75', 24000000, 'Американский биплан, учебно-тренировочный самолёт 1930-40х годов.'),
            ('МиГ-17', 29000000, 'Советский реактивный истребитель, достигал скорости звука.'),
            ('North American F-86 Sabre', 29000000, 'Американский реактивный истребитель конца 1940-х годов.'),
            ('Pilatus PC-7', 29000000, 'Швейцарский учебно-тренировочный самолёт.'),
            ('Canadair CT-114 Tutor', 45000000, 'Канадский реактивный учебно-тренировочный самолёт.'),
            ('Curtiss P-40', 42000000, 'Американский истребитель Второй мировой войны.'),
            ('Boeing B-52 Stratofortress', 59000000, 'Американский межконтинентальный стратегический бомбардировщик.'),
            ('MQ-1 Predator', 55000000, 'Американский многоцелевой беспилотный летательный аппарат.'),
            ('Dassault Falcon 50/900', 35000000, 'Французские трёхдвигательные бизнес-джеты.'),
            ('Air Racer', 32000000, 'Спортивный самолёт с мощным двигателем (прототип).'),
            ('Ан-2 Кукурузник', 40000000, 'Советский лёгкий многоцелевой самолёт, биплан.'),
            ('Су-39', 34000000, 'Модификация штурмовика Су-25, всепогодный.'),
            ('ATR 42', 40000000, 'Турбовинтовой региональный пассажирский самолёт.'),
            ('Learjet 23', 24000000, 'Двухдвигательный реактивный самолёт бизнес-класса.'),
            ('Grumman F6F Hellcat', 32000000, 'Легендарный палубный истребитель США времен ВМВ.'),
            ('Де Хэвилленд DH.100 Вампир', 22000000, 'Британский реактивный истребитель 1940-х годов.'),
            ('Boeing 707', 35000000, 'Американский реактивный пассажирский лайнер 1950-х годов.'),
            ('Cy-47 Беркут', 36000000, 'Российский экспериментальный палубный истребитель с крылом обратной стреловидности.'),
            ('Northrop B-2 Spirit', 49000000, 'Американский малозаметный стратегический бомбардировщик.'),
        ]
        for p in planes:
            c.execute("INSERT INTO planes_shop (name, price, description) VALUES (?, ?, ?)", p)
    
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
        "job": p[4], "faction": p[5],
        "cars": json.loads(p[6]), "houses": json.loads(p[7]),
        "businesses": json.loads(p[8]), "boats": json.loads(p[9]),
        "planes": json.loads(p[10]), "passport": p[11], "license": p[12],
        "work_time": p[13], "daily_date": p[14]
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

def get_businesses(city=None, available_only=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if city and available_only:
        c.execute("SELECT id, name, price, salary, tax, owner_name, description FROM businesses WHERE city = ? AND owner_id = 0", (city,))
    elif city:
        c.execute("SELECT id, name, price, salary, tax, owner_name, description FROM businesses WHERE city = ?", (city,))
    elif available_only:
        c.execute("SELECT id, name, price, salary, tax, owner_name, description FROM businesses WHERE owner_id = 0")
    else:
        c.execute("SELECT id, name, price, salary, tax, owner_name, description FROM businesses")
    biz = c.fetchall()
    conn.close()
    return biz

def buy_business(user_id, biz_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, price, salary, tax, owner_id, owner_name, city FROM businesses WHERE id = ?", (biz_id,))
    biz = c.fetchone()
    if not biz:
        conn.close()
        return False, "Бизнес не найден"
    if biz[4] != 0:
        conn.close()
        return False, f"Бизнес уже принадлежит {biz[5]}"
    p = get_player(user_id)
    if p["balance"] < biz[1]:
        conn.close()
        return False, f"Не хватает {biz[1]}$"
    new_balance = p["balance"] - biz[1]
    update_player(user_id, balance=new_balance)
    businesses = p["businesses"] + [biz[0]]
    update_player(user_id, businesses=businesses)
    c.execute("UPDATE businesses SET owner_id = ?, owner_name = ? WHERE id = ?", (user_id, p["nick"], biz_id))
    conn.commit()
    conn.close()
    return True, f"Вы купили бизнес {biz[0]} за {biz[1]}$"

def get_planes():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, price, description FROM planes_shop")
    planes = c.fetchall()
    conn.close()
    return planes

def buy_plane(user_id, plane_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, price FROM planes_shop WHERE id = ?", (plane_id,))
    plane = c.fetchone()
    if not plane:
        conn.close()
        return False, "Самолёт не найден"
    p = get_player(user_id)
    if p["balance"] < plane[1]:
        conn.close()
        return False, f"Не хватает {plane[1]}$"
    new_balance = p["balance"] - plane[1]
    update_player(user_id, balance=new_balance)
    planes = p["planes"] + [plane[0]]
    update_player(user_id, planes=planes)
    conn.commit()
    conn.close()
    return True, f"Вы купили самолёт {plane[0]} за {plane[1]}$"

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
        InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        InlineKeyboardButton("🏦 Банк", callback_data="bank_menu"),
        InlineKeyboardButton("💼 Работа", callback_data="work_menu"),
        InlineKeyboardButton("🛒 Магазин", callback_data="shop_menu"),
        InlineKeyboardButton("✈️ Авиасалон", callback_data="planes_menu"),
        InlineKeyboardButton("🏭 Бизнесы", callback_data="businesses_menu"),
        InlineKeyboardButton("🎫 Промокод", callback_data="promo"),
        InlineKeyboardButton("🏆 Топ", callback_data="top"),
        InlineKeyboardButton("💸 Перевод", callback_data="transfer"),
        InlineKeyboardButton("📋 Имущество", callback_data="inventory"),
        InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="daily"),
        InlineKeyboardButton("👑 Админ", callback_data="admin_panel")
    )
    return kb

def back_button():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    return kb

def admin_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💰 Выдать зарплату", callback_data="admin_salary"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("🎫 Создать промокод", callback_data="admin_create_promo"),
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
    )
    return kb

def bank_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Внести", callback_data="bank_deposit"),
        InlineKeyboardButton("💸 Снять", callback_data="bank_withdraw"),
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
    )
    return kb

def work_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🚛 Грузчик (+5000)", callback_data="work_loader"),
        InlineKeyboardButton("🚕 Такси (+8000)", callback_data="work_taxi"),
        InlineKeyboardButton("🔧 Механик (+12000)", callback_data="work_mechanic"),
        InlineKeyboardButton("🏥 Врач (+15000)", callback_data="work_doctor"),
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
    )
    return kb

def shop_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🚗 Авто", callback_data="shop_cars"),
        InlineKeyboardButton("🏠 Дома", callback_data="shop_houses"),
        InlineKeyboardButton("🛥️ Яхты", callback_data="shop_boats"),
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
    )
    return kb

def businesses_menu(city=None):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🏙️ Дубровка", callback_data="biz_dubrovka"),
        InlineKeyboardButton("🏘️ Арзамас", callback_data="biz_arzamas"),
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
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
    bot.send_message(user_id, "🔥 Добро пожаловать в Crimson RP бот!\n\nИспользуй кнопки ниже.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data
    msg = call.message
    chat_id = msg.chat.id
    message_id = msg.message_id

    if data == "menu":
        bot.edit_message_text("🔥 Главное меню:", chat_id, message_id, reply_markup=main_menu())
        return

    # ===== ПРОФИЛЬ =====
    if data == "profile":
        p = get_player(user_id)
        text = (
            f"👤 <b>Профиль</b>\n\n"
            f"🆔 ID: {p['user_id']}\n"
            f"📛 Ник: {p['nick']}\n"
            f"💰 Наличные: {p['balance']}$\n"
            f"🏦 Банк: {p['bank']}$\n"
            f"💼 Работа: {p['job']}\n"
            f"⚔️ Фракция: {p['faction']}\n"
            f"📄 Паспорт: {'✅' if p['passport'] else '❌'}\n"
            f"🚗 Права: {'✅' if p['license'] else '❌'}"
        )
        bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button())
        return

    if data == "balance":
        p = get_player(user_id)
        text = f"💰 <b>Ваш баланс</b>\n\nНаличные: {p['balance']}$\nБанк: {p['bank']}$"
        bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button())
        return

    # ===== БАНК =====
    if data == "bank_menu":
        bot.edit_message_text("🏦 <b>Банковские операции</b>", chat_id, message_id, reply_markup=bank_menu())
        return

    if data == "bank_deposit":
        bot.send_message(user_id, "Введите сумму для внесения:")
        bot.register_next_step_handler_by_chat_id(user_id, lambda m: bank_action(m, "deposit"))
        bot.answer_callback_query(call.id)
        return

    if data == "bank_withdraw":
        bot.send_message(user_id, "Введите сумму для снятия:")
        bot.register_next_step_handler_by_chat_id(user_id, lambda m: bank_action(m, "withdraw"))
        bot.answer_callback_query(call.id)
        return

    # ===== РАБОТА =====
    if data == "work_menu":
        bot.edit_message_text("💼 <b>Выбери работу</b>", chat_id, message_id, reply_markup=work_menu())
        return

    if data.startswith("work_"):
        jobs = {"loader": 5000, "taxi": 8000, "mechanic": 12000, "doctor": 15000}
        salary = jobs.get(data.split("_")[1], 5000)
        p = get_player(user_id)
        if p["work_time"]:
            last_work = datetime.fromisoformat(p["work_time"])
            if datetime.now() - last_work < timedelta(minutes=5):
                remaining = 5 - (datetime.now() - last_work).seconds // 60
                bot.answer_callback_query(call.id, f"⏰ Отдыхай! Следующая работа через {remaining} мин", show_alert=True)
                return
        update_player(user_id, balance=p["balance"] + salary, work_time=datetime.now().isoformat())
        bot.answer_callback_query(call.id, f"✅ +{salary}$", show_alert=True)
        p = get_player(user_id)
        bot.edit_message_text(f"💼 Вы отработали и получили {salary}$\n\nБаланс: {p['balance']}$", chat_id, message_id, reply_markup=back_button())
        return

    # ===== МАГАЗИН =====
    if data == "shop_menu":
        bot.edit_message_text("🛒 <b>Магазин</b>", chat_id, message_id, reply_markup=shop_menu())
        return

    if data.startswith("shop_"):
        bot.answer_callback_query(call.id, "🚧 В разработке", show_alert=True)
        return

    # ===== АВИАСАЛОН =====
    if data == "planes_menu":
        planes = get_planes()
        if not planes:
            bot.edit_message_text("✈️ Самолётов пока нет", chat_id, message_id, reply_markup=back_button())
            return
        text = "✈️ <b>Авиасалон</b>\n\n"
        kb = InlineKeyboardMarkup(row_width=1)
        for pid, name, price, desc in planes:
            text += f"• {name} — {price}$\n"
            kb.add(InlineKeyboardButton(f"✈️ {name}", callback_data=f"plane_{pid}"))
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data="menu"))
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        return

    if data.startswith("plane_"):
        plane_id = int(data.split("_")[1])
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT name, price, description FROM planes_shop WHERE id = ?", (plane_id,))
        plane = c.fetchone()
        conn.close()
        if not plane:
            bot.answer_callback_query(call.id, "Самолёт не найден", show_alert=True)
            return
        name, price, desc = plane
        text = f"✈️ <b>{name}</b>\n\n💰 Цена: {price}$\n\n📖 {desc}\n\nКупить?"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Купить", callback_data=f"buy_plane_{plane_id}"))
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data="planes_menu"))
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        return

    if data.startswith("buy_plane_"):
        plane_id = int(data.split("_")[2])
        success, msg = buy_plane(user_id, plane_id)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if success:
            p = get_player(user_id)
            bot.edit_message_text(f"✅ {msg}\n\n💰 Новый баланс: {p['balance']}$", chat_id, message_id, reply_markup=back_button())
        return

    # ===== БИЗНЕСЫ =====
    if data == "businesses_menu":
        bot.edit_message_text("🏭 <b>Бизнесы</b>\n\nВыбери город:", chat_id, message_id, reply_markup=businesses_menu())
        return

    if data == "biz_dubrovka":
        biz_list = get_businesses(city="Дубровка")
        if not biz_list:
            bot.edit_message_text("🏭 Бизнесов в Дубровке пока нет", chat_id, message_id, reply_markup=back_button())
            return
        text = "🏭 <b>Бизнесы Дубровка</b>\n\n"
        kb = InlineKeyboardMarkup(row_width=1)
        for bid, name, price, salary, tax, owner, desc in biz_list:
            status = f"❌ Владелец: {owner}" if owner else "✅ Доступно"
            text += f"• {name} — {price}$\n   {status}\n"
            if not owner:
                kb.add(InlineKeyboardButton(f"🏭 {name}", callback_data=f"biz_{bid}"))
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data="businesses_menu"))
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        return

    if data == "biz_arzamas":
        biz_list = get_businesses(city="Арзамас")
        if not biz_list:
            bot.edit_message_text("🏭 Бизнесов в Арзамасе пока нет", chat_id, message_id, reply_markup=back_button())
            return
        text = "🏭 <b>Бизнесы Арзамас</b>\n\n"
        kb = InlineKeyboardMarkup(row_width=1)
        for bid, name, price, salary, tax, owner, desc in biz_list:
            status = f"❌ Владелец: {owner}" if owner else "✅ Доступно"
            text += f"• {name} — {price}$\n   {status}\n"
            if not owner:
                kb.add(InlineKeyboardButton(f"🏭 {name}", callback_data=f"biz_{bid}"))
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data="businesses_menu"))
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        return

    if data.startswith("biz_"):
        biz_id = int(data.split("_")[1])
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT name, price, salary, tax, description, owner_name FROM businesses WHERE id = ?", (biz_id,))
        biz = c.fetchone()
        conn.close()
        if not biz:
            bot.answer_callback_query(call.id, "Бизнес не найден", show_alert=True)
            return
        name, price, salary, tax, desc, owner = biz
        if owner:
            bot.answer_callback_query(call.id, f"❌ Бизнес уже принадлежит {owner}", show_alert=True)
            return
        text = f"🏭 <b>{name}</b>\n\n💰 Цена: {price}$\n💵 Доход: {salary}$\n📉 Налог: {tax}$\n\n📖 {desc}\n\nКупить?"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Купить", callback_data=f"buy_biz_{biz_id}"))
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data="businesses_menu"))
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        return

    if data.startswith("buy_biz_"):
        biz_id = int(data.split("_")[2])
        success, msg = buy_business(user_id, biz_id)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        if success:
            p = get_player(user_id)
            bot.edit_message_text(f"✅ {msg}\n\n💰 Новый баланс: {p['balance']}$", chat_id, message_id, reply_markup=back_button())
        return

    # ===== ТОП =====
    if data == "top":
        top = get_top_players(10)
        text = "🏆 <b>Топ игроков</b>\n\n"
        for i, (uid, nick, balance) in enumerate(top, 1):
            text += f"{i}. {nick} — {balance}$\n"
        bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button())
        return

    # ===== ПЕРЕВОД =====
    if data == "transfer":
        bot.send_message(user_id, "💸 Введите ID или ник (@nick) и сумму через пробел\nПример: @nick 500")
        bot.register_next_step_handler_by_chat_id(user_id, transfer_handler)
        bot.answer_callback_query(call.id)
        return

    # ===== ИМУЩЕСТВО =====
    if data == "inventory":
        p = get_player(user_id)
        text = (
            f"📋 <b>Имущество</b>\n\n"
            f"🚗 Авто: {', '.join(p['cars']) if p['cars'] else 'Нет'}\n"
            f"🏠 Домов: {', '.join(p['houses']) if p['houses'] else 'Нет'}\n"
            f"🏭 Бизнесов: {', '.join(p['businesses']) if p['businesses'] else 'Нет'}\n"
            f"🛥️ Катеров: {', '.join(p['boats']) if p['boats'] else 'Нет'}\n"
            f"✈️ Самолётов: {', '.join(p['planes']) if p['planes'] else 'Нет'}"
        )
        bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button())
        return

    # ===== ЕЖЕДНЕВНЫЙ БОНУС =====
    if data == "daily":
        p = get_player(user_id)
        if p["daily_date"]:
            last_daily = datetime.fromisoformat(p["daily_date"])
            if datetime.now() - last_daily < timedelta(days=1):
                remaining = 24 - (datetime.now() - last_daily).seconds // 3600
                bot.answer_callback_query(call.id, f"⏰ Бонус через {remaining} ч", show_alert=True)
                return
        bonus = random.randint(500, 2000)
        update_player(user_id, balance=p["balance"] + bonus, daily_date=datetime.now().isoformat())
        bot.answer_callback_query(call.id, f"🎁 +{bonus}$", show_alert=True)
        p = get_player(user_id)
        bot.edit_message_text(f"🎁 Ежедневный бонус: +{bonus}$\n\n💰 Баланс: {p['balance']}$", chat_id, message_id, reply_markup=back_button())
        return

    # ===== ПРОМОКОД =====
    if data == "promo":
        bot.send_message(user_id, "🎫 Введите промокод:")
        bot.register_next_step_handler_by_chat_id(user_id, promo_handler)
        bot.answer_callback_query(call.id)
        return

    # ===== АДМИНКА =====
    if data == "admin_panel":
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Нет доступа!", show_alert=True)
            return
        bot.edit_message_text("👑 <b>Админ панель</b>", chat_id, message_id, reply_markup=admin_menu())
        return

    if data == "admin_salary":
        if user_id != ADMIN_ID:
            return
        bot.send_message(user_id, "Введите: ID_игрока Сумма Комментарий\nПример: 123456789 500 За работу")
        bot.register_next_step_handler_by_chat_id(user_id, salary_handler)
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
        c.execute("SELECT SUM(bank) FROM players")
        total_bank = c.fetchone()[0] or 0
        conn.close()
        text = f"📊 <b>Статистика</b>\n\n👥 Игроков: {players}\n💰 Денег в экономике: {total_money + total_bank}$\n💳 На руках: {total_money}$\n🏦 В банке: {total_bank}$"
        bot.edit_message_text(text, chat_id, message_id, reply_markup=admin_menu())
        return

    if data == "admin_create_promo":
        if user_id != ADMIN_ID:
            return
        bot.send_message(user_id, "Введите: КОД ТИП СУММА ЛИМИТ ДНЕЙ\nТипы: money, bank\nПример: PROMO100 money 100 50 7")
        bot.register_next_step_handler_by_chat_id(user_id, create_promo_handler)
        bot.answer_callback_query(call.id)
        return

# ========== ОБРАБОТЧИКИ ==========
def bank_action(m, action):
    user_id = m.from_user.id
    try:
        amount = int(m.text)
        if amount <= 0:
            bot.send_message(user_id, "❌ Сумма должна быть больше 0")
            return
        p = get_player(user_id)
        if action == "deposit":
            if p["balance"] < amount:
                bot.send_message(user_id, f"❌ Не хватает {amount}$ на руках")
                return
            update_player(user_id, balance=p["balance"] - amount, bank=p["bank"] + amount)
            bot.send_message(user_id, f"✅ Внесено {amount}$ на счёт")
        else:
            if p["bank"] < amount:
                bot.send_message(user_id, f"❌ Не хватает {amount}$ на счёте")
                return
            update_player(user_id, balance=p["balance"] + amount, bank=p["bank"] - amount)
            bot.send_message(user_id, f"✅ Снято {amount}$ со счёта")
    except:
        bot.send_message(user_id, "❌ Ошибка! Введите число")

def transfer_handler(m):
    user_id = m.from_user.id
    try:
        parts = m.text.split()
        target = parts[0]
        amount = int(parts[1])
        if amount <= 0:
            bot.send_message(user_id, "❌ Сумма должна быть больше 0")
            return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if target.startswith("@"):
            nick = target[1:]
            c.execute("SELECT user_id FROM players WHERE nick = ?", (nick,))
            row = c.fetchone()
            if not row:
                bot.send_message(user_id, "❌ Игрок не найден")
                conn.close()
                return
            target_id = row[0]
        else:
            target_id = int(target)
        conn.close()
        if target_id == user_id:
            bot.send_message(user_id, "❌ Нельзя перевести деньги самому себе")
            return
        p = get_player(user_id)
        if p["balance"] < amount:
            bot.send_message(user_id, f"❌ Не хватает {amount}$")
            return
        update_player(user_id, balance=p["balance"] - amount)
        target_p = get_player(target_id)
        update_player(target_id, balance=target_p["balance"] + amount)
        bot.send_message(user_id, f"✅ Переведено {amount}$ игроку {target_id}")
        bot.send_message(target_id, f"💰 Вам переведено {amount}$ от {p['nick']}")
    except:
        bot.send_message(user_id, "❌ Ошибка! Формат: @nick 500 или ID 500")

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
    if m.from_user.id != ADMIN_ID:
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
                  (target_id, amount, comment, ADMIN_ID, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID, f"✅ Выдано {amount}$ игроку {target_id}")
        bot.send_message(target_id, f"💰 Вам выдана зарплата: {amount}$\nКомментарий: {comment}")
    except:
        bot.send_message(ADMIN_ID, "❌ Ошибка! Формат: ID Сумма Комментарий")

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