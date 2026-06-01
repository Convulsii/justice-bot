import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput
import asyncio
import random
import aiosqlite
import json
import aiohttp
import time
import os
import re
import math
import shutil
from datetime import datetime, timedelta
from openai import OpenAI
from collections import defaultdict

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("❌ Токен не найден! Добавь DISCORD_TOKEN в переменные окружения")
    exit(1)

# API ключи
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
YANDEX_WEATHER_API_KEY = os.getenv('YANDEX_WEATHER_API_KEY')

# ИИ настройки (Ranvik)
AI_API_KEY = "rk_live_G15mOokgVTN8hKFBvWVda38wZGOiXkVs"
AI_BASE_URL = "https://api.ranvik.ru/v1"
AI_MODEL = "gpt-5-nano"

AI_SYSTEM_PROMPT = """Ты дружелюбный помощник в Discord сервере.
СЕЙЧАС 2026 ГОД! Отвечай кратко и по делу.
Представься как Justice Bot AI."""

# ID каналов (ЗАМЕНИ НА СВОИ!)
WELCOME_CHANNEL_ID = 1502637204982206686
LOGS_CHANNEL_ID = 1502637204982206681
LEVEL_CHANNEL_ID = 1502682125730578522
COLOR_ROLE_CHANNEL_ID = 1502637205187723424
MUTED_ROLE_ID = 1502637204072169540
DEFAULT_ROLE_ID = 1502637204487278744
VC_CREATE_CATEGORY_ID = 1507479787223126036
VC_TRIGGER_CHANNEL_ID = 1507485728739688549
TICKET_CATEGORY_ID = 1507503146744938506
TICKET_CREATE_CHANNEL_ID = 1507503353117020241
STOLOTO_CHANNEL_ID = 1509190455106211840
IDEA_REVIEW_CHANNEL_ID = 1502637204982206679

# Роли поддержки
SUPPORT_ROLE_IDS = [
    1502637204537737308,
    1507479670130741368,
    1502637204537737306,
    1507478655578673152
]

# Гендерные роли
ROLE_GIRL = 1506343912594477247
ROLE_BOY = 1506343782637896011

# Цветные роли
COLOR_ROLES = {
    "🟠": {"name": "Оранжевый", "id": 1502637204487278745},
    "🟡": {"name": "Жёлтый", "id": 1502637204487278746},
    "🟢": {"name": "Зелёный", "id": 1502637204487278747},
    "🔵": {"name": "Синий", "id": 1502637204487278748},
    "🟣": {"name": "Пурпурный", "id": 1502637204487278749},
    "🌸": {"name": "Розовый", "id": 1502637204487278750},
    "🔴": {"name": "Красный", "id": 1502637204487278751}
}

# Роли за уровни
LEVEL_ROLES = {
    5: 1502637204487278752,
    10: 1502637204487278753,
    25: 1502637204504051712,
    50: 1502637204504051713,
    100: 1502637204504051714
}

# Настройки экономики
START_BALANCE = 100
MIN_EARN = 2
MAX_EARN = 6
BANK_INTEREST = 0.03

# КД (секунды)
GAME_COOLDOWN = {
    "casino": 300, "dice": 300, "coin": 300, "rps": 300,
    "blackjack": 300, "rob": 3600, "work": 3600, "rep": 3600
}

# Шансы
WIN_CHANCE = {
    "casino": 0.35, "coin": 0.45, "dice": 0.16,
    "rps": 0.33, "blackjack": 0.42, "rob": 0.05
}

# Эмодзи
SLOT_EMOJIS = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎"]
DICE_EMOJIS = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]

# Магазин
SHOP_ITEMS = {
    "звезда": {"price": 500, "description": "⭐ Звезда в профиль", "type": "award", "role_id": None},
    "сердечко": {"price": 300, "description": "💖 Сердечко в профиль", "type": "award", "role_id": None},
    "корону": {"price": 1000, "description": "👑 Корона в профиль", "type": "award", "role_id": None},
    "радугу": {"price": 700, "description": "🌈 Радуга в профиль", "type": "award", "role_id": None},
    "бриллиант": {"price": 2000, "description": "💎 Бриллиант в профиль", "type": "award", "role_id": None},
}

CUSTOM_SHOP_ITEMS = {}

# Семена для фермы
SEEDS = {
    "пшеница": {"price": 50, "grow_time": 3600, "rarity_weights": {"обычный": 0.7, "редкий": 0.2, "эпический": 0.08, "легендарный": 0.02}, "base_price": 100},
    "кукуруза": {"price": 80, "grow_time": 7200, "rarity_weights": {"обычный": 0.6, "редкий": 0.25, "эпический": 0.1, "легендарный": 0.05}, "base_price": 150},
    "томат": {"price": 100, "grow_time": 10800, "rarity_weights": {"обычный": 0.5, "редкий": 0.3, "эпический": 0.15, "легендарный": 0.05}, "base_price": 200},
    "картофель": {"price": 60, "grow_time": 5400, "rarity_weights": {"обычный": 0.65, "редкий": 0.25, "эпический": 0.08, "легендарный": 0.02}, "base_price": 120},
    "морковь": {"price": 70, "grow_time": 7200, "rarity_weights": {"обычный": 0.6, "редкий": 0.3, "эпический": 0.08, "легендарный": 0.02}, "base_price": 130},
    "мефедрон": {"price": 500, "grow_time": 43200, "rarity_weights": {"обычный": 0.3, "редкий": 0.3, "эпический": 0.25, "легендарный": 0.15}, "base_price": 1000},
    "роза": {"price": 150, "grow_time": 14400, "rarity_weights": {"обычный": 0.5, "редкий": 0.3, "эпический": 0.15, "легендарный": 0.05}, "base_price": 300},
    "кактус": {"price": 120, "grow_time": 18000, "rarity_weights": {"обычный": 0.55, "редкий": 0.25, "эпический": 0.15, "легендарный": 0.05}, "base_price": 250},
    "подсолнух": {"price": 90, "grow_time": 9000, "rarity_weights": {"обычный": 0.6, "редкий": 0.3, "эпический": 0.08, "легендарный": 0.02}, "base_price": 180},
    "тыква": {"price": 200, "grow_time": 28800, "rarity_weights": {"обычный": 0.5, "редкий": 0.25, "эпический": 0.2, "легендарный": 0.05}, "base_price": 400}
}

RARITY_MULTIPLIERS = {
    "обычный": 1.0,
    "редкий": 2.0,
    "эпический": 4.0,
    "легендарный": 8.0,
    "мифический": 16.0
}

# КАРТЫ ДЛЯ ПОКЕРА
CARD_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
CARD_SUITS = ['♠️', '♥️', '♣️', '♦️']
FULL_DECK = [f"{r}{s}" for r in CARD_RANKS for s in CARD_SUITS]

# СТО ЛОТО
STOLOTO_TIME = "14:00"

# Настройки автомодерации
ANTISPAM_WINDOW_SECONDS = 8
ANTISPAM_MAX_MESSAGES = 5
ANTISPAM_MAX_WARNINGS = 3
ANTISPAM_WARNING_EXPIRE_HOURS = 24

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='j.', intents=intents)
bot.remove_command('help')

# Хранилища
cooldowns = defaultdict(dict)
rep_cooldowns = defaultdict(dict)
ttt_games = {}
poker_games = {}
poker_lobbies = {}
stoloto_active = False
stoloto_tickets = []
stoloto_end_time = None
guild_settings = {}
active_tickets = {}
color_message_id = None
vc_sessions = {}
user_message_timestamps = defaultdict(list)
user_warnings = defaultdict(list)
user_conversations = defaultdict(list)
MAX_CONTEXT_MESSAGES = 10

# Ролевые GIF
REACTION_GIFS = {
    "hug": "https://media.tenor.com/SYsRdiK-T7gAAAAM/hug-anime.gif",
    "kiss": "https://media.tenor.com/kmxEaVuW8AoAAAAM/kiss-gentle-kiss.gif",
    "pat": "https://media1.tenor.com/m/9u2vmryDP-cAAAAC/horimiya-animes.gif",
    "poke": "https://media.tenor.com/OgM0CeJcgd0AAAAM/zakuro-cat.gif",
    "slap": "https://media.tenor.com/Ws6Dm1ZW_vMAAAAM/girl-slap.gif",
    "punch": "https://media.tenor.com/qDDsivB4UEkAAAAM/anime-fight.gif",
    "bite": "https://media.tenor.com/5mVQ3ffWUTgAAAAM/anime-bite.gif",
    "cry": "https://media.tenor.com/Bhq1WZGJfqIAAAA1/frieren-cry-frieren-beyond-journey%27s-end.webp",
    "laugh": "https://media.tenor.com/CG8uhh9CoJcAAAAM/shikimori-shikimoris-not-just-cute.gif",
    "smile": "https://media.tenor.com/KHZEaH1uFHQAAAAM/frieren-frieren-beyond-journey%27s-end.gif",
    "blush": "https://media.tenor.com/9VmKG3_cWikAAAAM/frieren-fern.gif",
    "dance": "https://media.tenor.com/RNnVPWPk9UQAAAAM/caramelldansen-dance.gif",
    "celebrate": "https://media.tenor.com/uYUQPKe2S3QAAAAM/frieren-anime.gif",
    "airkiss": "https://media.tenor.com/Gv38EiXASmoAAAAM/frieren-sousou-no-frieren.gif",
    "handhold": "https://media.tenor.com/WUZAwo5KFdMAAAAM/love-holding-hands.gif",
    "tickle": "https://media.tenor.com/Li-ya799Ni4AAAAM/onimai-oniichan-wa-oshimai.gif",
    "run": "https://media.tenor.com/3MoXnDR3bnsAAAAM/stark-frieren-beyond-journey%27s-end.gif",
    "sleep": "https://media.tenor.com/53H3rXVJ-ksAAAAM/anime-fern.gif",
    "shrug": "https://media.tenor.com/WZd51JGLPKsAAAAM/shrug-anime-shrug.gif",
    "shy": "https://media.tenor.com/5QNYSyqDj3kAAAAM/frieren-%E8%91%AC%E9%80%81%E3%81%AE%E3%83%95%E3%83%AA%E3%83%BC%E3%83%AC%E3%83%B3.gif",
    "sorry": "https://media.tenor.com/30NShXsRidMAAAAM/anime-frieren.gif",
    "stare": "https://media.tenor.com/5XGsh4LY0FgAAAAM/anime-serie.gif",
    "wink": "https://media.tenor.com/tPfEQC6tWyYAAAAM/wink-anime.gif"
}

# ИИ клиент
ai_client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)


# ========== БАЗА ДАННЫХ ==========
async def init_db():
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER, guild_id INTEGER,
            xp INTEGER DEFAULT 0, level INTEGER DEFAULT 0,
            balance INTEGER DEFAULT 100, bank INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 0, join_date TEXT,
            warning_count INTEGER DEFAULT 0, total_messages INTEGER DEFAULT 0,
            last_daily TEXT, last_weekly TEXT, last_monthly TEXT, last_timely TEXT,
            last_work TEXT, color_role_id INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            awards TEXT DEFAULT '[]',
            inventory TEXT DEFAULT '[]',
            gender TEXT DEFAULT '',
            today_messages INTEGER DEFAULT 0,
            week_messages INTEGER DEFAULT 0,
            month_messages INTEGER DEFAULT 0,
            last_message_time TEXT,
            steam_id TEXT DEFAULT '',
            voice_streak INTEGER DEFAULT 0,
            last_voice_join TEXT,
            pots INTEGER DEFAULT 0,
            crops TEXT DEFAULT '[]',
            PRIMARY KEY (user_id, guild_id)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, guild_id INTEGER,
            moderator_id INTEGER, reason TEXT, expires_at TEXT
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, guild_id INTEGER,
            suggestion TEXT, status TEXT DEFAULT 'pending',
            verdict TEXT, date TEXT
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS private_vc (
            owner_id INTEGER, guild_id INTEGER,
            channel_name TEXT, user_limit INTEGER DEFAULT 0,
            is_locked INTEGER DEFAULT 0,
            banned_users TEXT DEFAULT '[]',
            created_at TEXT
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER, message_id INTEGER,
            prize TEXT, winners INTEGER, end_time TEXT,
            entries TEXT, ended INTEGER DEFAULT 0
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS stoloto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            winner_id INTEGER,
            prize INTEGER
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS custom_shop (
            name TEXT PRIMARY KEY,
            price INTEGER,
            description TEXT,
            role_id INTEGER
        )''')
        await db.commit()
    
    async with aiosqlite.connect("justice.db") as db:
        async with db.execute('SELECT name, price, description, role_id FROM custom_shop') as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                CUSTOM_SHOP_ITEMS[row[0]] = {"price": row[1], "description": row[2], "type": "role", "role_id": row[3]}
    
    print("✅ База данных готова")


async def get_user(user_id, guild_id):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM users WHERE user_id=? AND guild_id=?', (user_id, guild_id))
        row = await cur.fetchone()
        if not row:
            now = datetime.now().isoformat()
            await db.execute('''INSERT INTO users (user_id, guild_id, join_date, balance, today_messages, week_messages, month_messages, total_messages, last_message_time, pots) 
                               VALUES (?,?,?,?,?,?,?,?,?,0)''', (user_id, guild_id, now, START_BALANCE, 0, 0, 0, 0, now))
            await db.commit()
            return await get_user(user_id, guild_id)
        return row


async def add_balance(user_id, guild_id, amount):
    user = await get_user(user_id, guild_id)
    new_bal = user[4] + amount
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET balance=? WHERE user_id=? AND guild_id=?', (new_bal, user_id, guild_id))
        await db.commit()
    return new_bal


async def add_bank(user_id, guild_id, amount):
    user = await get_user(user_id, guild_id)
    new_bank = (user[5] if len(user) > 5 else 0) + amount
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET bank=? WHERE user_id=? AND guild_id=?', (new_bank, user_id, guild_id))
        await db.commit()
    return new_bank


async def add_reputation(user_id, guild_id, amount):
    user = await get_user(user_id, guild_id)
    new_rep = (user[6] if len(user) > 6 else 0) + amount
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET reputation=? WHERE user_id=? AND guild_id=?', (new_rep, user_id, guild_id))
        await db.commit()
    return new_rep


async def add_xp(user_id, guild_id, amount):
    user = await get_user(user_id, guild_id)
    new_xp = user[2] + amount
    new_level = int((new_xp / 200) ** 0.55)
    level_up = new_level > user[3]
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('''UPDATE users SET xp=?, level=?, total_messages=total_messages+1, 
                         today_messages=today_messages+1, week_messages=week_messages+1, 
                         month_messages=month_messages+1, last_message_time=? 
                         WHERE user_id=? AND guild_id=?''', 
                         (new_xp, new_level, datetime.now().isoformat(), user_id, guild_id))
        await db.commit()
    
    return level_up, new_level


async def send_log(guild_id, embed):
    settings = guild_settings.get(guild_id, {})
    log_channel_id = settings.get("log_channel", LOGS_CHANNEL_ID)
    ch = bot.get_channel(log_channel_id)
    if ch:
        await ch.send(embed=embed)


def check_cooldown(user_id, action):
    if action in cooldowns[user_id]:
        elapsed = time.time() - cooldowns[user_id][action]
        if elapsed < GAME_COOLDOWN[action]:
            return False, int(GAME_COOLDOWN[action] - elapsed)
    return True, 0


def set_cooldown(user_id, action):
    cooldowns[user_id][action] = time.time()


def check_rep_cooldown(from_id, to_id):
    key = f"{from_id}_{to_id}"
    if key in rep_cooldowns:
        elapsed = time.time() - rep_cooldowns[key]
        if elapsed < GAME_COOLDOWN["rep"]:
            return False, int(GAME_COOLDOWN["rep"] - elapsed)
    return True, 0


def set_rep_cooldown(from_id, to_id):
    key = f"{from_id}_{to_id}"
    rep_cooldowns[key] = time.time()


# ========== ПОГОДА ==========
@bot.command()
async def weather(ctx, *, city: str = None):
    """🌤️ Погода в любом городе (Яндекс.Погода)"""
    if city is None:
        await ctx.send("🌤️ **Погода**\n`j.weather <город>` - показать погоду\nПример: `j.weather Москва`")
        return
    
    if not YANDEX_WEATHER_API_KEY:
        await ctx.send("❌ Погода не настроена! Добавьте YANDEX_WEATHER_API_KEY в переменные окружения.")
        return
    
    async with aiohttp.ClientSession() as session:
        geo_url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
        headers = {'User-Agent': 'JusticeBot/1.0'}
        try:
            async with session.get(geo_url, headers=headers) as resp:
                data = await resp.json()
                if not data:
                    await ctx.send(f"❌ Город **{city}** не найден!")
                    return
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                city_name = data[0].get('display_name', city).split(',')[0]
        except Exception as e:
            await ctx.send(f"❌ Ошибка поиска города: {str(e)[:100]}")
            return
    
    headers = {'X-Yandex-API-Key': YANDEX_WEATHER_API_KEY}
    url = f"https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}&limit=1&lang=ru_RU"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 401:
                    await ctx.send("❌ Неверный API ключ Яндекс.Погоды!")
                    return
                if resp.status != 200:
                    await ctx.send(f"❌ Ошибка API: {resp.status}")
                    return
                
                data = await resp.json()
                fact = data.get('fact', {})
                
                condition_map = {"clear": "☀️", "partly-cloudy": "⛅", "cloudy": "☁️", "overcast": "☁️",
                                "light-rain": "🌧️", "rain": "🌧️", "heavy-rain": "🌧️", "showers": "🌧️",
                                "wet-snow": "🌨️", "light-snow": "❄️", "snow": "❄️", "heavy-snow": "❄️",
                                "thunderstorm": "⛈️", "hail": "🌨️"}
                condition_ru = {"clear": "Ясно", "partly-cloudy": "Малооблачно", "cloudy": "Облачно с прояснениями",
                              "overcast": "Пасмурно", "light-rain": "Небольшой дождь", "rain": "Дождь",
                              "heavy-rain": "Сильный дождь", "showers": "Ливень", "wet-snow": "Дождь со снегом",
                              "light-snow": "Небольшой снег", "snow": "Снег", "heavy-snow": "Сильный снег",
                              "thunderstorm": "Гроза", "hail": "Град"}
                wind_dir_map = {"nw": "Северо-западный", "n": "Северный", "ne": "Северо-восточный",
                              "w": "Западный", "e": "Восточный", "sw": "Юго-западный",
                              "s": "Южный", "se": "Юго-восточный", "c": "Штиль"}
                
                embed = discord.Embed(title=f"{condition_map.get(fact.get('condition'), '🌡️')} Погода в {city_name}",
                                    description=f"*{condition_ru.get(fact.get('condition'), fact.get('condition', 'Неизвестно')).capitalize()}*",
                                    color=discord.Color.blue())
                embed.add_field(name="🌡️ Температура", value=f"{fact.get('temp')}°C", inline=True)
                embed.add_field(name="🤔 Ощущается как", value=f"{fact.get('feels_like')}°C", inline=True)
                embed.add_field(name="💧 Влажность", value=f"{fact.get('humidity')}%", inline=True)
                embed.add_field(name="💨 Ветер", value=f"{fact.get('wind_speed')} м/с, {wind_dir_map.get(fact.get('wind_dir'), '')}".strip(', '), inline=True)
                embed.add_field(name="📊 Давление", value=f"{fact.get('pressure_mm')} мм рт. ст.", inline=True)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Ошибка: {str(e)[:100]}")


# ========== ИИ ==========
async def get_ai_response(user_id, user_message, with_web=False):
    global user_conversations
    
    lower_msg = user_message.lower()
    
    # Быстрые ответы
    if any(x in lower_msg for x in ["привет", "здравствуй"]):
        return "👋 Привет!"
    if "как дела" in lower_msg:
        return "😊 Всё отлично!"
    if "спасибо" in lower_msg:
        return "🙏 Пожалуйста!"
    if any(x in lower_msg for x in ["дата", "сегодня", "число"]):
        return f"📅 Сегодня {datetime.now().strftime('%d.%m.%Y')}"
    if any(x in lower_msg for x in ["время", "который час"]):
        return f"🕐 Сейчас {datetime.now().strftime('%H:%M:%S')}"
    if "погода" in lower_msg:
        return "🌤️ Используй `j.weather <город>`"
    
    # Контекст
    conv = user_conversations.get(user_id, [])
    messages = [{"role": "system", "content": f"Ты помощник. Сегодня {datetime.now().strftime('%d.%m.%Y')}. Отвечай кратко."}]
    messages.extend(conv[-MAX_CONTEXT_MESSAGES:])
    messages.append({"role": "user", "content": user_message})
    
    try:
        resp = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ai_client.chat.completions.create(
                    model=AI_MODEL,
                    messages=messages,
                    max_tokens=500
                )
            ),
            timeout=10.0
        )
        answer = resp.choices[0].message.content
        user_conversations[user_id].append({"role": "user", "content": user_message})
        user_conversations[user_id].append({"role": "assistant", "content": answer})
        return answer if answer else "😊 Понял!"
    except asyncio.TimeoutError:
        return "⏳ Немного подтормаживает... Попробуй ещё раз."
    except Exception as e:
        return f"❌ Ошибка: {str(e)[:100]}"


@bot.command()
async def ai(ctx, *, question: str = None):
    """🤖 Задать вопрос ИИ"""
    if not question:
        await ctx.send("❌ Напиши вопрос: `j.ai Как дела?`")
        return
    if len(question) > 500:
        await ctx.send("❌ Вопрос слишком длинный! Максимум 500 символов.")
        return
    msg = await ctx.send("💭 Думаю...")
    async with ctx.typing():
        response = await get_ai_response(ctx.author.id, question)
    await msg.edit(content=response)


# ========== АВТОМОДЕРАЦИЯ ==========
async def check_spam(message):
    user_id = message.author.id
    content = message.content.strip().lower()
    now = time.time()
    
    settings = guild_settings.get(message.guild.id, {})
    
    # Запрещённые слова
    for word in settings.get("automod_bad_words", []):
        if word in content:
            return True, f"запрещённое слово: {word}"
    
    # Реклама Discord серверов
    if settings.get("automod_invites_enabled", True):
        if "discord.gg/" in content or "discord.com/invite/" in content or "dsc.gg/" in content:
            return True, "реклама Discord сервера"
    
    # Фишинг
    if settings.get("automod_phishing_enabled", True):
        if ("free" in content or "giveaway" in content) and ("nitro" in content or "steam" in content):
            return True, "подозрение на фишинг"
        if ("пополни" in content or "баланс" in content) and ("http" in content or "www" in content):
            return True, "подозрение на фишинг"
    
    # Флуд
    if user_id not in user_message_timestamps:
        user_message_timestamps[user_id] = []
    
    user_message_timestamps[user_id].append(now)
    user_message_timestamps[user_id] = [t for t in user_message_timestamps[user_id] if now - t < ANTISPAM_WINDOW_SECONDS]
    
    if len(user_message_timestamps[user_id]) > ANTISPAM_MAX_MESSAGES:
        user_message_timestamps[user_id] = []
        return True, f"флуд ({ANTISPAM_MAX_MESSAGES} сообщений за {ANTISPAM_WINDOW_SECONDS} секунд)"
    
    return False, None


async def add_auto_warning(user, reason, channel):
    user_id = user.id
    now = time.time()
    user_warnings[user_id] = [w for w in user_warnings[user_id] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    user_warnings[user_id].append({"reason": reason, "time": now, "moderator": "Automod"})
    warning_count = len(user_warnings[user_id])
    
    embed = discord.Embed(title="⚠️ АВТОМАТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ", color=discord.Color.orange(), timestamp=datetime.now())
    embed.add_field(name="👤 Пользователь", value=f"{user.mention}\n{user.name} (ID: {user.id})", inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=True)
    embed.add_field(name="📊 Всего варнов", value=f"{warning_count}/{ANTISPAM_MAX_WARNINGS}", inline=True)
    embed.add_field(name="📍 Канал", value=channel.mention, inline=True)
    await send_log(user.guild.id, embed)
    
    if warning_count >= ANTISPAM_MAX_WARNINGS:
        alert = discord.Embed(title="🚨 ПРЕВЫШЕН ЛИМИТ ПРЕДУПРЕЖДЕНИЙ",
                             description=f"Пользователь {user.mention} получил {warning_count} автоматических предупреждений за 24 часа.",
                             color=discord.Color.red())
        await send_log(user.guild.id, alert)
    
    return warning_count


@bot.command()
@commands.has_permissions(administrator=True)
async def automod(ctx, action: str = None, module: str = None, *args):
    if ctx.guild.id not in guild_settings:
        guild_settings[ctx.guild.id] = {}
    settings = guild_settings[ctx.guild.id]
    
    if "automod_enabled" not in settings:
        settings.update({"automod_enabled": True, "automod_bad_words": [], "automod_invites_enabled": True,
                        "automod_phishing_enabled": True, "automod_exempt_roles": []})
    
    if action is None or action == "status":
        embed = discord.Embed(title="⚙️ НАСТРОЙКИ АВТОМОДЕРАЦИИ", color=discord.Color.blue())
        embed.add_field(name="📊 Общий статус", value="✅ ВКЛЮЧЁН" if settings["automod_enabled"] else "❌ ВЫКЛЮЧЕН", inline=False)
        embed.add_field(name="📝 Запрещённые слова", value=f"Слов в списке: {len(settings['automod_bad_words'])}", inline=True)
        embed.add_field(name="🚫 Реклама серверов", value="✅ ВКЛ" if settings["automod_invites_enabled"] else "❌ ВЫКЛ", inline=True)
        embed.add_field(name="🎣 Фишинг/мошенничество", value="✅ ВКЛ" if settings["automod_phishing_enabled"] else "❌ ВЫКЛ", inline=True)
        roles = [ctx.guild.get_role(rid).mention for rid in settings["automod_exempt_roles"] if ctx.guild.get_role(rid)]
        embed.add_field(name="👑 Исключённые роли", value=", ".join(roles) if roles else "Нет", inline=False)
        await ctx.send(embed=embed)
        return
    
    if action == "enable":
        settings["automod_enabled"] = True
        await ctx.send("✅ Автомодерация **ВКЛЮЧЕНА**")
    elif action == "disable":
        settings["automod_enabled"] = False
        await ctx.send("❌ Автомодерация **ВЫКЛЮЧЕНА**")
    elif action == "words":
        if len(args) == 0:
            await ctx.send("**📖 Настройка запрещённых слов:**\n`j.automod words add <слово>`\n`j.automod words remove <слово>`\n`j.automod words list`\n`j.automod words clear`")
        elif args[0] == "add" and len(args) >= 2:
            word = " ".join(args[1:]).lower()
            if word not in settings["automod_bad_words"]:
                settings["automod_bad_words"].append(word)
                await ctx.send(f"✅ Добавлено слово: **{word}**")
        elif args[0] == "remove" and len(args) >= 2:
            word = " ".join(args[1:]).lower()
            if word in settings["automod_bad_words"]:
                settings["automod_bad_words"].remove(word)
                await ctx.send(f"✅ Удалено слово: **{word}**")
        elif args[0] == "list":
            words = settings["automod_bad_words"]
            if words:
                await ctx.send(f"**📝 Список запрещённых слов ({len(words)}):**\n" + ", ".join([f"`{w}`" for w in words[:50]]))
            else:
                await ctx.send("📝 Список запрещённых слов пуст")
        elif args[0] == "clear":
            settings["automod_bad_words"] = []
            await ctx.send("✅ Список запрещённых слов очищен")
    elif action == "invites":
        if len(args) == 0:
            await ctx.send("`j.automod invites on` - включить\n`j.automod invites off` - выключить")
        elif args[0] == "on":
            settings["automod_invites_enabled"] = True
            await ctx.send("✅ Проверка на рекламу серверов **ВКЛЮЧЕНА**")
        elif args[0] == "off":
            settings["automod_invites_enabled"] = False
            await ctx.send("❌ Проверка на рекламу серверов **ВЫКЛЮЧЕНА**")
    elif action == "phishing":
        if len(args) == 0:
            await ctx.send("`j.automod phishing on` - включить\n`j.automod phishing off` - выключить")
        elif args[0] == "on":
            settings["automod_phishing_enabled"] = True
            await ctx.send("✅ Проверка на фишинг **ВКЛЮЧЕНА**")
        elif args[0] == "off":
            settings["automod_phishing_enabled"] = False
            await ctx.send("❌ Проверка на фишинг **ВЫКЛЮЧЕНА**")
    elif action == "exempt":
        if len(args) == 0:
            await ctx.send("**📖 Исключённые роли:**\n`j.automod exempt add @роль`\n`j.automod exempt remove @роль`\n`j.automod exempt list`")
        elif args[0] == "add" and ctx.message.role_mentions:
            role = ctx.message.role_mentions[0]
            if role.id not in settings["automod_exempt_roles"]:
                settings["automod_exempt_roles"].append(role.id)
                await ctx.send(f"✅ Роль {role.mention} добавлена в исключения")
        elif args[0] == "remove" and ctx.message.role_mentions:
            role = ctx.message.role_mentions[0]
            if role.id in settings["automod_exempt_roles"]:
                settings["automod_exempt_roles"].remove(role.id)
                await ctx.send(f"✅ Роль {role.mention} удалена из исключений")
        elif args[0] == "list":
            roles = [ctx.guild.get_role(rid).mention for rid in settings["automod_exempt_roles"] if ctx.guild.get_role(rid)]
            await ctx.send(f"**👑 Исключённые роли:**\n" + ", ".join(roles) if roles else "👑 Нет исключённых ролей")
    else:
        await ctx.send("❌ Неизвестная команда.")


@bot.command()
async def mywarns(ctx):
    user_id = ctx.author.id
    now = time.time()
    user_warnings[user_id] = [w for w in user_warnings[user_id] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    
    if not user_warnings[user_id]:
        await ctx.send(f"✅ {ctx.author.mention}, у вас нет активных предупреждений!")
        return
    
    embed = discord.Embed(title=f"⚠️ Ваши предупреждения", color=discord.Color.orange())
    for i, warn in enumerate(user_warnings[user_id], 1):
        left = ANTISPAM_WARNING_EXPIRE_HOURS * 3600 - (now - warn["time"])
        embed.add_field(name=f"Предупреждение #{i}", value=f"📝 Причина: {warn['reason']}\n⏰ Сгорает через: {int(left//3600)}ч {int((left%3600)//60)}мин", inline=False)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(moderate_members=True)
async def warns(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = target.id
    now = time.time()
    
    if user_id in user_warnings:
        user_warnings[user_id] = [w for w in user_warnings[user_id] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    
    if not user_warnings.get(user_id, []):
        await ctx.send(f"✅ У {target.mention} нет активных предупреждений!")
        return
    
    embed = discord.Embed(title=f"⚠️ Предупреждения {target.display_name}", color=discord.Color.orange())
    for i, warn in enumerate(user_warnings[user_id], 1):
        left = ANTISPAM_WARNING_EXPIRE_HOURS * 3600 - (now - warn["time"])
        embed.add_field(name=f"Варн #{i}", value=f"📝 Причина: {warn['reason']}\n👮 Выдал: {warn.get('moderator', 'Automod')}\n⏰ Сгорает через: {int(left//3600)}ч {int((left%3600)//60)}мин", inline=False)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(moderate_members=True)
async def unwarn(ctx, member: discord.Member, warn_number: int = None):
    user_id = member.id
    now = time.time()
    
    if user_id in user_warnings:
        user_warnings[user_id] = [w for w in user_warnings[user_id] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    
    if not user_warnings.get(user_id, []):
        await ctx.send(f"✅ У {member.mention} нет активных предупреждений!")
        return
    
    if not warn_number or warn_number < 1 or warn_number > len(user_warnings[user_id]):
        await ctx.send(f"❌ Укажите номер варна (1-{len(user_warnings[user_id])}).")
        return
    
    removed = user_warnings[user_id].pop(warn_number - 1)
    embed = discord.Embed(title="✅ Варн снят", description=f"С {member.mention} снято предупреждение", color=discord.Color.green())
    embed.add_field(name="📝 Причина варна", value=removed['reason'], inline=False)
    embed.add_field(name="👮 Снял", value=ctx.author.mention, inline=True)
    embed.add_field(name="📊 Осталось варнов", value=len(user_warnings[user_id]), inline=True)
    await ctx.send(embed=embed)
    await send_log(ctx.guild.id, embed)


@bot.command()
@commands.has_permissions(moderate_members=True)
async def awarn(ctx, member: discord.Member, *, reason: str = "Не указана"):
    user_id = member.id
    now = time.time()
    
    if user_id in user_warnings:
        user_warnings[user_id] = [w for w in user_warnings[user_id] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    else:
        user_warnings[user_id] = []
    
    user_warnings[user_id].append({"reason": reason, "time": now, "moderator": ctx.author.name})
    warning_count = len(user_warnings[user_id])
    
    embed = discord.Embed(title="⚠️ РУЧНОЕ ПРЕДУПРЕЖДЕНИЕ", color=discord.Color.orange(), timestamp=datetime.now())
    embed.add_field(name="👤 Пользователь", value=f"{member.mention}\n{member.name}", inline=True)
    embed.add_field(name="👮 Модератор", value=ctx.author.mention, inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=True)
    embed.add_field(name="📊 Всего варнов", value=f"{warning_count}/{ANTISPAM_MAX_WARNINGS}", inline=True)
    await ctx.send(embed=embed)
    await send_log(ctx.guild.id, embed)
    
    try:
        await member.send(f"⚠️ **Вы получили предупреждение** на сервере {ctx.guild.name}\n📝 Причина: {reason}\n⚠️ Предупреждений: {warning_count}/{ANTISPAM_MAX_WARNINGS}")
    except:
        pass


# ========== ОГОНЁК ==========
async def update_voice_streak(member):
    today = datetime.now().date()
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT voice_streak, last_voice_join FROM users WHERE user_id=? AND guild_id=?', 
                               (member.id, member.guild.id))
        row = await cur.fetchone()
        
        if not row:
            streak = 1
        else:
            current = row[0] or 0
            last = row[1]
            if last:
                last_date = datetime.fromisoformat(last).date() if isinstance(last, str) else last
                if last_date == today:
                    return current
                elif last_date == today - timedelta(days=1):
                    streak = current + 1
                else:
                    streak = 1
            else:
                streak = 1
        
        await db.execute('UPDATE users SET voice_streak=?, last_voice_join=? WHERE user_id=? AND guild_id=?',
                        (streak, datetime.now().isoformat(), member.id, member.guild.id))
        await db.commit()
        await add_balance(member.id, member.guild.id, streak * 5)
        return streak


# ========== ФЕРМА ==========
@bot.command()
async def farm(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    pots = data[28] if len(data) > 28 else 0
    crops = json.loads(data[29] if len(data) > 29 else "[]")
    
    embed = discord.Embed(title="🌾 ФЕРМА", color=discord.Color.green())
    embed.add_field(name="🏺 Горшки", value=f"**{pots}/5**", inline=True)
    embed.add_field(name="🌱 Посажено", value=f"**{len(crops)}** культур", inline=True)
    
    if crops:
        crop_list = ""
        for i, crop in enumerate(crops[:5]):
            if crop:
                planted = datetime.fromisoformat(crop["planted_at"])
                left = (planted + timedelta(seconds=SEEDS[crop["seed"]]["grow_time"]) - datetime.now())
                status = f"🌱 {int(left.total_seconds()//3600)}ч {int((left.total_seconds()%3600)//60)}мин" if left.total_seconds() > 0 else "✅ ГОТОВО К СБОРУ!"
                crop_list += f"**{i+1}.** {crop['seed'].capitalize()} ({crop['rarity']}) - {status}\n"
        embed.add_field(name="📋 Посевы", value=crop_list[:1024], inline=False)
    
    embed.set_footer(text="j.buy_pot | j.buy_seed <семя> | j.plant <номер> <семя> | j.harvest <номер>")
    await ctx.send(embed=embed)


@bot.command()
async def buy_pot(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    pots = data[28] if len(data) > 28 else 0
    if pots >= 5:
        await ctx.send("❌ У вас уже максимальное количество горшков (5)!")
        return
    
    price = 500 * (pots + 1)
    if data[4] < price:
        await ctx.send(f"❌ Недостаточно средств! Нужно **{price}** 💎")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -price)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET pots=? WHERE user_id=? AND guild_id=?', (pots + 1, ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"✅ Вы купили горшок №{pots + 1} за {price} 💎!")


@bot.command()
async def buy_seed(ctx, seed: str = None):
    if not seed or seed.lower() not in SEEDS:
        await ctx.send(f"🌱 **Доступные семена:**\n{', '.join(SEEDS.keys())}\n\nЦены: пшеница(50), кукуруза(80), томат(100), картофель(60), морковь(70), мефедрон(500), роза(150), кактус(120), подсолнух(90), тыква(200)")
        return
    
    seed = seed.lower()
    price = SEEDS[seed]["price"]
    if (await get_user(ctx.author.id, ctx.guild.id))[4] < price:
        await ctx.send(f"❌ Недостаточно средств! Нужно **{price}** 💎")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -price)
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        inv.append(f"seed_{seed}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"✅ Вы купили семена **{seed.capitalize()}** за {price} 💎!")


@bot.command()
async def plant(ctx, pot: int = None, seed: str = None):
    if not pot or not seed:
        await ctx.send("❌ Использование: `j.plant <номер_горшка> <семя>`\nПример: `j.plant 1 пшеница`")
        return
    
    data = await get_user(ctx.author.id, ctx.guild.id)
    pots = data[28] if len(data) > 28 else 0
    if pot < 1 or pot > pots:
        await ctx.send(f"❌ У вас нет горшка №{pot}. У вас {pots} горшков.")
        return
    
    crops = json.loads(data[29] if len(data) > 29 else "[]")
    if pot-1 < len(crops) and crops[pot-1] and crops[pot-1].get("planted_at"):
        await ctx.send(f"❌ Горшок №{pot} уже занят! Сначала соберите урожай командой `j.harvest {pot}`")
        return
    
    seed = seed.lower()
    if seed not in SEEDS:
        await ctx.send(f"❌ Семя '{seed}' не найдено!")
        return
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        if f"seed_{seed}" not in inv:
            await ctx.send(f"❌ У вас нет семян **{seed.capitalize()}**! Купите командой `j.buy_seed {seed}`")
            return
        inv.remove(f"seed_{seed}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
    
    weights = SEEDS[seed]["rarity_weights"]
    rarity = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    
    while len(crops) < pot:
        crops.append(None)
    crops[pot-1] = {"seed": seed, "planted_at": datetime.now().isoformat(), "rarity": rarity}
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET crops=? WHERE user_id=? AND guild_id=?', (json.dumps(crops), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"✅ Вы посадили **{seed.capitalize()}** ({rarity}) в горшок №{pot}! Время роста: {SEEDS[seed]['grow_time']//3600} часов.")


@bot.command()
async def harvest(ctx, pot: int = None):
    if not pot:
        await ctx.send("❌ Использование: `j.harvest <номер_горшка>`")
        return
    
    data = await get_user(ctx.author.id, ctx.guild.id)
    if pot < 1 or pot > (data[28] if len(data) > 28 else 0):
        await ctx.send(f"❌ У вас нет горшка №{pot}")
        return
    
    crops = json.loads(data[29] if len(data) > 29 else "[]")
    if pot-1 >= len(crops) or not crops[pot-1]:
        await ctx.send(f"❌ В горшке №{pot} ничего не посажено!")
        return
    
    crop = crops[pot-1]
    planted = datetime.fromisoformat(crop["planted_at"])
    ready = planted + timedelta(seconds=SEEDS[crop["seed"]]["grow_time"])
    
    if datetime.now() < ready:
        left = ready - datetime.now()
        await ctx.send(f"❌ Урожай ещё не готов! Осталось: {int(left.total_seconds()//3600)}ч {int((left.total_seconds()%3600)//60)}мин")
        return
    
    price = int(SEEDS[crop["seed"]]["base_price"] * RARITY_MULTIPLIERS.get(crop["rarity"], 1.0))
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        inv.append(f"crop_{crop['seed']}_{crop['rarity']}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
    
    crops[pot-1] = None
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET crops=? WHERE user_id=? AND guild_id=?', (json.dumps(crops), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"✅ Вы собрали **{crop['seed'].capitalize()}** ({crop['rarity']}) с горшка №{pot}!\n💰 Цена: {price} 💎")


@bot.command()
async def sell_crop(ctx, crop: str = None, rarity: str = None):
    if not crop or not rarity:
        await ctx.send("❌ Использование: `j.sell_crop <культура> <редкость>`\nПример: `j.sell_crop пшеница редкий`")
        return
    
    crop = crop.lower()
    if crop not in SEEDS:
        await ctx.send(f"❌ Культура '{crop}' не найдена!")
        return
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        item = f"crop_{crop}_{rarity}"
        if item not in inv:
            await ctx.send(f"❌ У вас нет **{crop}** ({rarity}) в инвентаре!")
            return
        inv.remove(item)
        price = int(SEEDS[crop]["base_price"] * RARITY_MULTIPLIERS.get(rarity, 1.0))
        await add_balance(ctx.author.id, ctx.guild.id, price)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"💰 Вы продали **{crop}** ({rarity}) за **{price}** 💎!")


@bot.command()
async def sell_all_crops(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        crops = [item for item in inv if item.startswith("crop_")]
        if not crops:
            await ctx.send("❌ У вас нет урожая в инвентаре!")
            return
        
        total = 0
        for item in crops:
            parts = item.split("_")
            if len(parts) >= 3:
                total += int(SEEDS.get(parts[1], {}).get("base_price", 100) * RARITY_MULTIPLIERS.get(parts[2], 1.0))
                inv.remove(item)
        
        await add_balance(ctx.author.id, ctx.guild.id, total)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"💰 Вы продали весь урожай за **{total}** 💎!")


# ========== ПРОФИЛЬ ==========
@bot.command()
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = await get_user(target.id, ctx.guild.id)
    
    level, xp, balance = data[3], data[2], data[4]
    bank = data[5] if len(data) > 5 else 0
    reputation = data[6] if len(data) > 6 else 0
    total_msgs = data[9] if len(data) > 9 else 0
    today_msgs = data[21] if len(data) > 21 else 0
    week_msgs = data[22] if len(data) > 22 else 0
    month_msgs = data[23] if len(data) > 23 else 0
    voice_streak = data[26] if len(data) > 26 else 0
    bio = data[17] if len(data) > 17 and data[17] else "Нет биографии"
    gender = data[20] if len(data) > 20 else ""
    
    xp_for_next = 200 * ((level + 1) ** 2)
    xp_for_current = 200 * (level ** 2)
    percent = min(100, int((xp - xp_for_current) / (xp_for_next - xp_for_current) * 100)) if xp_for_next > xp_for_current else 0
    bar = "█" * (percent // 5) + "░" * (20 - (percent // 5))
    
    gender_text, gender_emoji = ("Мужчина", "👨") if gender == "male" else ("Женщина", "👩") if gender == "female" else ("Не указан", "❓")
    
    embed = discord.Embed(title=f"📊 ПРОФИЛЬ | {target.display_name}", color=discord.Color.gold())
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎚️ УРОВЕНЬ", value=f"**{level}** уровень\n`{bar}` {percent}%\n✨ {xp} XP", inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💰 ЭКОНОМИКА", value=f"💎 В кошельке: **{balance}**\n🏦 В банке: **{bank}**\n⭐ Репутация: **{reputation}**", inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📆 АКТИВНОСТЬ", value=f"📅 Сегодня: **{today_msgs}**\n📅 Неделя: **{week_msgs}**\n📅 Месяц: **{month_msgs}**\n💬 Всего: **{total_msgs}**\n🔥 Огонёк: **{voice_streak}** дней", inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚧ ПОЛ", value=f"{gender_emoji} {gender_text}", inline=True)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📝 БИОГРАФИЯ", value=bio[:500], inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def bio(ctx, *, text: str = None):
    if not text:
        await ctx.send("📝 Использование: `j.bio Твоя биография`\nМаксимум 500 символов.")
        return
    if len(text) > 500:
        await ctx.send("❌ Биография не может быть длиннее 500 символов!")
        return
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET bio=? WHERE user_id=? AND guild_id=?', (text, ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send("✅ Ваша биография обновлена!")


# ========== STEAM (С КНОПКАМИ) ==========
class SteamProfileView(discord.ui.View):
    def __init__(self, target_user, steam_id):
        super().__init__(timeout=120)
        self.target_user = target_user
        self.steam_id = steam_id
        self.current_action = "profile"
        
        self.add_item(discord.ui.Button(label="Открыть в Steam", style=discord.ButtonStyle.link, url=f"https://steamcommunity.com/profiles/{steam_id}"))
    
    async def fetch_steam_data(self, action: str, page: int = 0):
        if not STEAM_API_KEY:
            return None, "❌ Steam API не настроен!"
        
        async with aiohttp.ClientSession() as session:
            if action == "profile":
                url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={self.steam_id}"
                async with session.get(url) as resp:
                    data = await resp.json()
                    players = data.get('response', {}).get('players', [])
                    if not players:
                        return None, "❌ Steam профиль не найден или скрыт."
                    p = players[0]
                    status_map = {0: "Офлайн", 1: "В сети", 2: "Занят", 3: "Нет на месте", 4: "Спит", 5: "Ищет игру", 6: "Играет"}
                    embed = discord.Embed(title=f"🎮 Steam Профиль: {self.target_user.display_name}",
                                        description=f"**{p.get('personaname', 'Неизвестно')}**",
                                        color=discord.Color.blue())
                    if p.get('avatarfull'):
                        embed.set_thumbnail(url=p['avatarfull'])
                    embed.add_field(name="🆔 Steam ID", value=self.steam_id, inline=True)
                    embed.add_field(name="🎮 Статус", value=status_map.get(p.get('personastate', 0), "Неизвестно"), inline=True)
                    
                    games_url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={self.steam_id}&include_appinfo=true"
                    async with session.get(games_url) as gr:
                        games_data = await gr.json()
                        if games_data.get('response', {}).get('games'):
                            games_list = games_data['response']['games']
                            embed.add_field(name="📚 Игр в библиотеке", value=len(games_list), inline=True)
                            total_hours = sum(g.get('playtime_forever', 0) for g in games_list) / 60
                            embed.add_field(name="⏱️ Часов в играх", value=f"{total_hours:.0f}ч", inline=True)
                    return embed, None
            
            elif action == "games":
                url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={self.steam_id}&include_appinfo=true"
                async with session.get(url) as resp:
                    games_data = await resp.json()
                    if not games_data.get('response', {}).get('games'):
                        return None, "❌ Список игр не найден или скрыт."
                    games = sorted(games_data['response']['games'], key=lambda x: x.get('playtime_forever', 0), reverse=True)
                    games_per_page = 10
                    total_pages = (len(games) + games_per_page - 1) // games_per_page
                    page = max(0, min(page, total_pages - 1))
                    start = page * games_per_page
                    end = start + games_per_page
                    current_games = games[start:end]
                    text = "\n".join([f"{i+1+start}. **{g.get('name', 'Неизвестно')}** - {g.get('playtime_forever',0)/60:.1f} ч" for i, g in enumerate(current_games)])
                    embed = discord.Embed(title=f"🎮 Игры: {self.target_user.display_name}", description=text, color=discord.Color.blue())
                    embed.set_footer(text=f"Страница {page+1} из {total_pages}")
                    return embed, total_pages
            
            elif action == "friends":
                url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={STEAM_API_KEY}&steamid={self.steam_id}&relationship=friend"
                async with session.get(url) as resp:
                    data = await resp.json()
                    friends = data.get('friendslist', {}).get('friends', [])
                    if not friends:
                        return None, "❌ Список друзей не найден или скрыт."
                    text = "\n".join([f"**{f.get('steamid', 'Неизвестно')}**" for f in friends[:10]])
                    embed = discord.Embed(title=f"👥 Друзья: {self.target_user.display_name}", description=text or "Список друзей пуст.", color=discord.Color.blue())
                    return embed, None
            
            return None, "❌ Неизвестный раздел."
    
    async def update_message(self, interaction: discord.Interaction, action: str, page: int = 0):
        embed, total_pages = await self.fetch_steam_data(action, page)
        if embed is None:
            await interaction.response.edit_message(content=total_pages or "❌ Ошибка загрузки.", view=self)
            return
        
        for item in self.children[:]:
            if isinstance(item, (PrevPageButton, NextPageButton)):
                self.remove_item(item)
        
        if action == "games" and total_pages and total_pages > 1:
            self.add_item(PrevPageButton(action, page))
            self.add_item(NextPageButton(action, page, total_pages))
        
        self.current_action = action
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Профиль", style=discord.ButtonStyle.primary, row=0)
    async def profile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id and not any(interaction.guild.get_role(rid) in interaction.user.roles for rid in SUPPORT_ROLE_IDS):
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        await self.update_message(interaction, "profile")
    
    @discord.ui.button(label="Игры", style=discord.ButtonStyle.primary, row=0)
    async def games_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id and not any(interaction.guild.get_role(rid) in interaction.user.roles for rid in SUPPORT_ROLE_IDS):
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        await self.update_message(interaction, "games", 0)
    
    @discord.ui.button(label="Друзья", style=discord.ButtonStyle.primary, row=0)
    async def friends_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user.id and not any(interaction.guild.get_role(rid) in interaction.user.roles for rid in SUPPORT_ROLE_IDS):
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        await self.update_message(interaction, "friends")


class PrevPageButton(discord.ui.Button):
    def __init__(self, action: str, current_page: int):
        super().__init__(label="◀", style=discord.ButtonStyle.secondary, row=1)
        self.action = action
        self.current_page = current_page
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        await view.update_message(interaction, self.action, self.current_page - 1)


class NextPageButton(discord.ui.Button):
    def __init__(self, action: str, current_page: int, total_pages: int):
        super().__init__(label="▶", style=discord.ButtonStyle.secondary, row=1)
        self.action = action
        self.current_page = current_page
        self.total_pages = total_pages
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        await view.update_message(interaction, self.action, self.current_page + 1)


@bot.command()
async def steam(ctx, action: str = None, *, arg: str = None):
    if not action:
        await ctx.send("🎮 **Steam команды:**\n`j.steam set <steam_id>` - привязать Steam ID\n`j.steam profile [@user]` - показать профиль")
        return
    
    if action == "set":
        if not arg:
            await ctx.send("❌ Использование: `j.steam set <steam_id>`")
            return
        async with aiosqlite.connect("justice.db") as db:
            await db.execute('UPDATE users SET steam_id=? WHERE user_id=? AND guild_id=?', (arg, ctx.author.id, ctx.guild.id))
            await db.commit()
        await ctx.send(f"✅ Steam ID привязан: `{arg}`")
        return
    
    if action == "profile":
        target_user = ctx.author
        if arg:
            match = re.match(r'<@!?(\d+)>', arg)
            if match:
                user_id = int(match.group(1))
                target_user = ctx.guild.get_member(user_id) or await bot.fetch_user(user_id)
            else:
                await ctx.send("❌ Укажите пользователя через @, например `j.steam profile @user`")
                return
        
        user_data = await get_user(target_user.id, ctx.guild.id)
        steam_id = user_data[25] if len(user_data) > 25 else None
        if not steam_id:
            await ctx.send(f"❌ У пользователя {target_user.mention} не привязан Steam ID!")
            return
        
        view = SteamProfileView(target_user, steam_id)
        embed, _ = await view.fetch_steam_data("profile")
        if embed:
            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send("❌ Не удалось загрузить профиль.")
        return
    
    await ctx.send("❌ Неизвестная команда. Используйте `j.steam set <id>` или `j.steam profile [@user]`.")


# ========== МАГАЗИН И ИНВЕНТАРЬ ==========
@bot.command()
async def shop(ctx):
    embed = discord.Embed(title="🛍️ МАГАЗИН", color=discord.Color.blue())
    for item, data in SHOP_ITEMS.items():
        embed.add_field(name=f"🔹 {item.capitalize()}", value=f"💰 Цена: {data['price']} 💎\n📝 {data['description']}\n`j.buy {item}`", inline=False)
    if CUSTOM_SHOP_ITEMS:
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━\n📦 КАСТОМНЫЕ ТОВАРЫ", value="", inline=False)
        for item, data in CUSTOM_SHOP_ITEMS.items():
            embed.add_field(name=f"🔸 {item.capitalize()}", value=f"💰 Цена: {data['price']} 💎\n📝 {data['description']}\n`j.buy {item}`", inline=False)
    embed.set_footer(text="j.buy [товар] - купить | j.use [товар] - использовать")
    await ctx.send(embed=embed)


@bot.command()
async def buy(ctx, *, item: str = None):
    if not item:
        await ctx.send("❌ Использование: `j.buy [товар]`")
        return
    item = item.lower()
    data = SHOP_ITEMS.get(item) or CUSTOM_SHOP_ITEMS.get(item)
    if not data:
        await ctx.send(f"❌ Товар `{item}` не найден")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < data["price"]:
        await ctx.send(f"❌ Недостаточно средств ({user[4]} 💎, нужно {data['price']} 💎)")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -data["price"])
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        inv.append(item)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"✅ {ctx.author.mention} купил **{item.capitalize()}** за {data['price']} 💎!")


@bot.command()
async def use(ctx, *, item: str = None):
    if not item:
        await ctx.send("❌ Использование: `j.use [товар]`")
        return
    item = item.lower()
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        if item not in inv:
            await ctx.send(f"❌ У вас нет **{item.capitalize()}** в инвентаре!")
            return
        inv.remove(item)
        
        if item in SHOP_ITEMS and SHOP_ITEMS[item]["type"] == "award":
            cur2 = await db.execute('SELECT awards FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
            aw = json.loads((await cur2.fetchone())[0] or "[]")
            if item not in aw:
                aw.append(item)
                await db.execute('UPDATE users SET awards=? WHERE user_id=? AND guild_id=?', (json.dumps(aw), ctx.author.id, ctx.guild.id))
                await ctx.send(f"✅ Вы использовали **{item.capitalize()}**! Теперь он отображается в вашем профиле.")
            else:
                await ctx.send(f"⚠️ У вас уже есть **{item.capitalize()}** в профиле!")
                inv.append(item)
        elif item in CUSTOM_SHOP_ITEMS:
            rid = CUSTOM_SHOP_ITEMS[item]["role_id"]
            role = ctx.guild.get_role(rid) if rid else None
            if role:
                if role in ctx.author.roles:
                    await ctx.send(f"⚠️ У вас уже есть роль {role.mention}!")
                else:
                    await ctx.author.add_roles(role)
                    await ctx.send(f"✅ Вы получили роль {role.mention}!")
            else:
                await ctx.send(f"❌ Роль для этого предмета не найдена!")
        
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await db.commit()


@bot.command()
async def inventory(ctx, member: discord.Member = None):
    target = member or ctx.author
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (target.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
    
    if not inv:
        await ctx.send(f"📦 Инвентарь {target.mention} пуст!")
        return
    
    items = {}
    for i in inv:
        items[i] = items.get(i, 0) + 1
    
    embed = discord.Embed(title=f"📦 Инвентарь {target.display_name}", color=discord.Color.blue())
    for i, c in items.items():
        embed.add_field(name=f"🔹 {i.capitalize()}", value=f"Количество: {c}\n`j.use {i}`", inline=True)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def add_shop_item(ctx, name: str, price: int, role_id: int, *, description: str = "Кастомный товар"):
    if name.lower() in SHOP_ITEMS or name.lower() in CUSTOM_SHOP_ITEMS:
        await ctx.send(f"❌ Товар с именем `{name}` уже существует!")
        return
    
    CUSTOM_SHOP_ITEMS[name.lower()] = {"price": price, "description": description, "type": "role", "role_id": role_id}
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT OR REPLACE INTO custom_shop (name, price, description, role_id) VALUES (?,?,?,?)', (name.lower(), price, description, role_id))
        await db.commit()
    await ctx.send(f"✅ Товар **{name}** добавлен в магазин!\n💰 Цена: {price} 💎\n🎭 Роль: <@&{role_id}>\n📝 Описание: {description}")


@bot.command()
@commands.has_permissions(administrator=True)
async def remove_shop_item(ctx, *, name: str):
    name = name.lower()
    if name not in CUSTOM_SHOP_ITEMS:
        await ctx.send(f"❌ Товар `{name}` не найден!")
        return
    del CUSTOM_SHOP_ITEMS[name]
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('DELETE FROM custom_shop WHERE name=?', (name,))
        await db.commit()
    await ctx.send(f"✅ Товар **{name}** удалён из магазина!")


# ========== РОЛЕВЫЕ КОМАНДЫ ==========
@bot.command()
async def hug(ctx, member: discord.Member = None):
    embed = discord.Embed(description=f"{ctx.author.mention} обнимает {member.mention if member else 'себя'}! 🤗", color=discord.Color.pink())
    embed.set_image(url=REACTION_GIFS["hug"])
    await ctx.send(embed=embed)


@bot.command()
async def kiss(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} целует {member.mention}! 💋", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["kiss"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} целует воздух! 💋")


@bot.command()
async def pat(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} гладит {member.mention}! 🖐️", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["pat"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} гладит себя! 🖐️")


@bot.command()
async def poke(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} тыкает {member.mention}! 👉", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["poke"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} тыкает в воздух! 👉")


@bot.command()
async def slap(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} шлёпает {member.mention}! 👋", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["slap"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} шлёпает воздух! 👋")


@bot.command()
async def punch(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} бьёт {member.mention}! 👊", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["punch"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} бьёт воздух! 👊")


@bot.command()
async def bite(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} кусает {member.mention}! 🦷", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["bite"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} кусает воздух! 🦷")


@bot.command()
async def cry(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} плачет! 😢", color=discord.Color.blue())
    embed.set_image(url=REACTION_GIFS["cry"])
    await ctx.send(embed=embed)


@bot.command()
async def laugh(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} смеётся! 😂", color=discord.Color.green())
    embed.set_image(url=REACTION_GIFS["laugh"])
    await ctx.send(embed=embed)


@bot.command()
async def smile(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} улыбается! 😊", color=discord.Color.yellow())
    embed.set_image(url=REACTION_GIFS["smile"])
    await ctx.send(embed=embed)


@bot.command()
async def blush(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} краснеет! 😊", color=discord.Color.pink())
    embed.set_image(url=REACTION_GIFS["blush"])
    await ctx.send(embed=embed)


@bot.command()
async def dance(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} танцует! 💃", color=discord.Color.purple())
    embed.set_image(url=REACTION_GIFS["dance"])
    await ctx.send(embed=embed)


@bot.command()
async def celebrate(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} празднует! 🎉", color=discord.Color.gold())
    embed.set_image(url=REACTION_GIFS["celebrate"])
    await ctx.send(embed=embed)


@bot.command()
async def airkiss(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} посылает воздушный поцелуй {member.mention}! 💋", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["airkiss"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} посылает воздушный поцелуй! 💋")


@bot.command()
async def handhold(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} держит за руку {member.mention}! 👫", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["handhold"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} держит себя за руку! 👫")


@bot.command()
async def tickle(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} щекочет {member.mention}! 😂", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["tickle"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} щекочет себя! 😂")


@bot.command()
async def run(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} бежит! 🏃", color=discord.Color.blue())
    embed.set_image(url=REACTION_GIFS["run"])
    await ctx.send(embed=embed)


@bot.command()
async def sleep(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} спит! 😴", color=discord.Color.dark_blue())
    embed.set_image(url=REACTION_GIFS["sleep"])
    await ctx.send(embed=embed)


@bot.command()
async def shrug(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} пожимает плечами! 🤷", color=discord.Color.orange())
    embed.set_image(url=REACTION_GIFS["shrug"])
    await ctx.send(embed=embed)


@bot.command()
async def shy(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} стесняется! 😊", color=discord.Color.pink())
    embed.set_image(url=REACTION_GIFS["shy"])
    await ctx.send(embed=embed)


@bot.command()
async def sorry(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} извиняется перед {member.mention}! 🙏", color=discord.Color.blue())
        embed.set_image(url=REACTION_GIFS["sorry"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} извиняется! 🙏")


@bot.command()
async def stare(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} смотрит на {member.mention}! 👀", color=discord.Color.blue())
        embed.set_image(url=REACTION_GIFS["stare"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} смотрит в пустоту! 👀")


@bot.command()
async def wink(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} подмигивает {member.mention}! 😉", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["wink"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{ctx.author.mention} подмигивает! 😉")


# ========== ГЕНДЕРНЫЕ РОЛИ ==========
@bot.command()
async def gender(ctx, choice: str = None):
    if not choice:
        await ctx.send("⚧ **Выбор гендера**\n`j.gender male` - роль Мужчина\n`j.gender female` - роль Девушка")
        return
    
    choice = choice.lower()
    male_role = ctx.guild.get_role(ROLE_BOY)
    female_role = ctx.guild.get_role(ROLE_GIRL)
    
    if choice in ["male", "мужчина", "мужской", "м"]:
        if male_role:
            if female_role in ctx.author.roles:
                await ctx.author.remove_roles(female_role)
            await ctx.author.add_roles(male_role)
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('UPDATE users SET gender="male" WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
                await db.commit()
            await ctx.send(f"✅ {ctx.author.mention} выбрал гендер: Мужчина")
    elif choice in ["female", "девушка", "женский", "ж"]:
        if female_role:
            if male_role in ctx.author.roles:
                await ctx.author.remove_roles(male_role)
            await ctx.author.add_roles(female_role)
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('UPDATE users SET gender="female" WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
                await db.commit()
            await ctx.send(f"✅ {ctx.author.mention} выбрал гендер: Девушка")
    else:
        await ctx.send("❌ Используйте: `j.gender male` или `j.gender female`")


# ========== ИДЕИ ==========
@bot.command()
async def suggest(ctx, *, suggestion: str):
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT INTO suggestions (user_id, guild_id, suggestion, date) VALUES (?,?,?,?)', (ctx.author.id, ctx.guild.id, suggestion, datetime.now().isoformat()))
        await db.commit()
        cur = await db.execute('SELECT last_insert_rowid()')
        sid = (await cur.fetchone())[0]
    
    embed = discord.Embed(title="💡 Новая идея", color=discord.Color.blue())
    embed.add_field(name=f"ID: {sid}", value=suggestion, inline=False)
    embed.add_field(name="Автор", value=ctx.author.mention, inline=True)
    embed.add_field(name="Статус", value="⏳ Ожидает рассмотрения", inline=True)
    await ctx.send(embed=embed)
    
    admin_ch = bot.get_channel(IDEA_REVIEW_CHANNEL_ID)
    if admin_ch:
        aembed = discord.Embed(title="💡 НОВАЯ ИДЕЯ", description=suggestion, color=discord.Color.gold(), timestamp=datetime.now())
        aembed.add_field(name="ID", value=sid, inline=True)
        aembed.add_field(name="Автор", value=ctx.author.mention, inline=True)
        aembed.add_field(name="Канал", value=ctx.channel.mention, inline=True)
        aembed.set_footer(text="j.accept <id> [вердикт] | j.deny <id> [вердикт]")
        await admin_ch.send(embed=aembed)


@bot.command()
@commands.has_permissions(administrator=True)
async def accept(ctx, sid: int, *, verdict: str = "Принято!"):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT user_id, suggestion FROM suggestions WHERE id=? AND guild_id=?', (sid, ctx.guild.id))
        row = await cur.fetchone()
        if not row:
            await ctx.send(f"❌ Идея #{sid} не найдена!")
            return
        uid, sug = row
        await db.execute('UPDATE suggestions SET status="accepted", verdict=? WHERE id=? AND guild_id=?', (verdict, sid, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"✅ Идея #{sid} принята! Вердикт: {verdict}")
    try:
        author = await bot.fetch_user(uid)
        await author.send(f"✅ **Ваша идея принята!** на сервере {ctx.guild.name}\n📝 **Идея:** {sug}\n📋 **Вердикт:** {verdict}")
    except:
        pass


@bot.command()
@commands.has_permissions(administrator=True)
async def deny(ctx, sid: int, *, verdict: str = "Отклонено"):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT user_id, suggestion FROM suggestions WHERE id=? AND guild_id=?', (sid, ctx.guild.id))
        row = await cur.fetchone()
        if not row:
            await ctx.send(f"❌ Идея #{sid} не найдена!")
            return
        uid, sug = row
        await db.execute('UPDATE suggestions SET status="denied", verdict=? WHERE id=? AND guild_id=?', (verdict, sid, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"❌ Идея #{sid} отклонена. Вердикт: {verdict}")
    try:
        author = await bot.fetch_user(uid)
        await author.send(f"❌ **Ваша идея отклонена** на сервере {ctx.guild.name}\n📝 **Идея:** {sug}\n📋 **Вердикт:** {verdict}")
    except:
        pass


# ========== РОЗЫГРЫШИ ==========
@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx, action: str, channel: discord.TextChannel = None, prize: str = None, winners: int = None, duration: str = None):
    if action != "create":
        await ctx.send("Доступно: create")
        return
    if not channel or not prize or not winners or not duration:
        await ctx.send("❌ j.giveaway create #канал приз кол-во 1д/1ч/10м")
        return
    
    units = {"м": 60, "ч": 3600, "д": 86400}
    unit = duration[-1]
    if unit not in units:
        await ctx.send("❌ Используйте м, ч, д")
        return
    try:
        sec = int(duration[:-1]) * units[unit]
    except:
        await ctx.send("❌ Неверный формат времени")
        return
    
    end = datetime.now() + timedelta(seconds=sec)
    embed = discord.Embed(title="🎉 **РОЗЫГРЫШ**", description=f"**Приз:** {prize}\n**Победителей:** {winners}\n**Заканчивается:** <t:{int(end.timestamp())}:R>", color=discord.Color.gold())
    embed.set_footer(text="Нажми на 🎉 чтобы участвовать!")
    msg = await channel.send(embed=embed)
    await msg.add_reaction("🎉")
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT INTO giveaways (channel_id, message_id, prize, winners, end_time, entries) VALUES (?,?,?,?,?,?)', (channel.id, msg.id, prize, winners, end.isoformat(), '[]'))
        await db.commit()
    await ctx.send(f"✅ Розыгрыш создан в {channel.mention}!")
    await asyncio.sleep(sec)
    await end_giveaway(msg.id, channel)


async def end_giveaway(mid, channel):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT prize, winners, entries FROM giveaways WHERE message_id=? AND ended=0', (mid,))
        row = await cur.fetchone()
        if not row:
            return
        prize, wcount, entries_json = row
        entries = json.loads(entries_json)
        await db.execute('UPDATE giveaways SET ended=1 WHERE message_id=?', (mid,))
        await db.commit()
    
    if not entries:
        await channel.send("😔 В розыгрыше никто не участвовал.")
        return
    
    selected = random.sample(entries, min(wcount, len(entries)))
    winners = ", ".join(f"<@{uid}>" for uid in selected)
    embed = discord.Embed(title="🏆 **РЕЗУЛЬТАТЫ РОЗЫГРЫША**", description=f"**Приз:** {prize}\n**Победители:** {winners}", color=discord.Color.gold())
    await channel.send(embed=embed)


# ========== ЭКОНОМИЧЕСКИЕ КОМАНДЫ ==========
@bot.command()
async def balance(ctx, member: discord.Member = None):
    t = member or ctx.author
    d = await get_user(t.id, ctx.guild.id)
    await ctx.send(f"💰 Баланс {t.mention}: **{d[4]}** 💎 | 🏦 В банке: **{d[5] if len(d)>5 else 0}** 💎")


@bot.command()
async def bank(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    await ctx.send(f"🏦 **Банковский счёт** {ctx.author.mention}\n💰 На счету: **{d[5] if len(d)>5 else 0}** 💎\n📈 Проценты: **{BANK_INTEREST * 100}%** в день")


@bot.command()
async def deposit(ctx, amount: int):
    if amount < 10:
        await ctx.send("❌ Минимальный вклад 10 💎")
        return
    d = await get_user(ctx.author.id, ctx.guild.id)
    if d[4] < amount:
        await ctx.send(f"❌ Недостаточно средств ({d[4]} 💎)")
        return
    await add_balance(ctx.author.id, ctx.guild.id, -amount)
    await add_bank(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"🏦 Вы внесли **{amount}** 💎 в банк")


@bot.command()
async def withdraw(ctx, amount: int):
    d = await get_user(ctx.author.id, ctx.guild.id)
    bank = d[5] if len(d) > 5 else 0
    if bank < amount:
        await ctx.send(f"❌ В банке {bank} 💎")
        return
    await add_bank(ctx.author.id, ctx.guild.id, -amount)
    await add_balance(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"🏦 Вы вывели **{amount}** 💎 из банка")


@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    if amount <= 0 or member == ctx.author:
        await ctx.send("❌ Неверная сумма или нельзя перевести себе")
        return
    s = await get_user(ctx.author.id, ctx.guild.id)
    if s[4] < amount:
        await ctx.send(f"❌ Недостаточно средств ({s[4]} 💎)")
        return
    await add_balance(ctx.author.id, ctx.guild.id, -amount)
    await add_balance(member.id, ctx.guild.id, amount)
    await ctx.send(f"💸 {ctx.author.mention} перевёл {amount} 💎 {member.mention}")


@bot.command()
@commands.has_permissions(administrator=True)
async def give(ctx, member: discord.Member, amount: int):
    await add_balance(member.id, ctx.guild.id, amount)
    await ctx.send(f"✅ Выдано {amount} 💎 {member.mention}")


@bot.command()
@commands.has_permissions(administrator=True)
async def take(ctx, member: discord.Member, amount: int):
    await add_balance(member.id, ctx.guild.id, -amount)
    await ctx.send(f"✅ Забрано {amount} 💎 у {member.mention}")


@bot.command()
async def daily(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    last = d[10] if len(d) > 10 else None
    if last:
        ld = datetime.fromisoformat(last)
        if (datetime.now() - ld).days < 1:
            rem = 86400 - (datetime.now() - ld).seconds
            await ctx.send(f"⏰ Ежедневный бонус будет доступен через {rem//3600}ч {(rem%3600)//60}мин")
            return
    earn = random.randint(50, 150)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET last_daily=? WHERE user_id=? AND guild_id=?', (datetime.now().isoformat(), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🎁 Ежедневный бонус! +{earn} 💎")


@bot.command()
async def weekly(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    last = d[11] if len(d) > 11 else None
    if last:
        ld = datetime.fromisoformat(last)
        if (datetime.now() - ld).days < 7:
            rem = 604800 - (datetime.now() - ld).seconds
            await ctx.send(f"⏰ Еженедельный бонус будет доступен через {rem//86400}д {(rem%86400)//3600}ч")
            return
    earn = random.randint(300, 600)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET last_weekly=? WHERE user_id=? AND guild_id=?', (datetime.now().isoformat(), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🎁 Еженедельный бонус! +{earn} 💎")


@bot.command()
async def monthly(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    last = d[12] if len(d) > 12 else None
    if last:
        ld = datetime.fromisoformat(last)
        if (datetime.now() - ld).days < 30:
            rem = 2592000 - (datetime.now() - ld).seconds
            await ctx.send(f"⏰ Ежемесячный бонус будет доступен через {rem//86400}д")
            return
    earn = random.randint(1000, 2000)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET last_monthly=? WHERE user_id=? AND guild_id=?', (datetime.now().isoformat(), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🎁 Ежемесячный бонус! +{earn} 💎")


@bot.command()
async def timely(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    last = d[13] if len(d) > 13 else None
    if last:
        ld = datetime.fromisoformat(last)
        if (datetime.now() - ld).seconds < 7200:
            rem = 7200 - (datetime.now() - ld).seconds
            await ctx.send(f"⏰ Бонус будет доступен через {rem//60} минут")
            return
    earn = random.randint(20, 50)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET last_timely=? WHERE user_id=? AND guild_id=?', (datetime.now().isoformat(), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🎁 Бонус! +{earn} 💎")


@bot.command()
async def work(ctx):
    can, w = check_cooldown(ctx.author.id, "work")
    if not can:
        await ctx.send(f"❌ КД! Подождите {w//60} минут")
        return
    earn = random.randint(30, 80)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    set_cooldown(ctx.author.id, "work")
    await ctx.send(f"💼 Вы поработали и заработали {earn} 💎")


@bot.command()
async def rob(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("❌ Нельзя ограбить себя")
        return
    can, w = check_cooldown(ctx.author.id, "rob")
    if not can:
        await ctx.send(f"❌ КД! Подождите {w//60} минут")
        return
    td = await get_user(member.id, ctx.guild.id)
    if td[4] < 50:
        await ctx.send(f"❌ У {member.mention} слишком мало денег для ограбления")
        return
    success = random.random() < WIN_CHANCE["rob"]
    set_cooldown(ctx.author.id, "rob")
    if success:
        steal = random.randint(10, int(td[4] * 0.3))
        await add_balance(ctx.author.id, ctx.guild.id, steal)
        await add_balance(member.id, ctx.guild.id, -steal)
        await ctx.send(f"🔫 **ОГРАБЛЕНИЕ УДАЛОСЬ!** {ctx.author.mention} украл у {member.mention} **{steal}** 💎")
    else:
        if random.random() < 0.5:
            rl = random.randint(5, 15)
            await add_reputation(ctx.author.id, ctx.guild.id, -rl)
            await ctx.send(f"🔫 **ТЕБЯ СПАЛИЛИ!** {ctx.author.mention}, ты пытался ограбить {member.mention}, но охрана заметила тебя!\nТвоя репутация упала на {rl} пунктов 😔")
        else:
            await ctx.send(f"🔫 **НЕ УДАЛОСЬ!** {ctx.author.mention} пытался ограбить {member.mention}, но вовремя сбежал.")


@bot.command()
async def rep(ctx, member: discord.Member = None):
    t = member or ctx.author
    d = await get_user(t.id, ctx.guild.id)
    await ctx.send(f"⭐ Репутация {t.mention}: **{d[6] if len(d)>6 else 0}**")


@bot.command()
async def plusrep(ctx, member: discord.Member, *, reason: str = "Не указана"):
    if member == ctx.author:
        await ctx.send("❌ Нельзя ставить +rep себе")
        return
    can, w = check_rep_cooldown(ctx.author.id, member.id)
    if not can:
        await ctx.send(f"❌ КД! Подождите {w//60} минут")
        return
    set_rep_cooldown(ctx.author.id, member.id)
    nr = await add_reputation(member.id, ctx.guild.id, 1)
    await ctx.send(f"👍 {ctx.author.mention} повысил репутацию {member.mention}!\n📝 Причина: {reason}\n⭐ Теперь: {nr}")


@bot.command()
async def minusrep(ctx, member: discord.Member, *, reason: str = "Не указана"):
    if member == ctx.author:
        await ctx.send("❌ Нельзя ставить -rep себе")
        return
    can, w = check_rep_cooldown(ctx.author.id, member.id)
    if not can:
        await ctx.send(f"❌ КД! Подождите {w//60} минут")
        return
    set_rep_cooldown(ctx.author.id, member.id)
    nr = await add_reputation(member.id, ctx.guild.id, -1)
    await ctx.send(f"👎 {ctx.author.mention} понизил репутацию {member.mention}!\n📝 Причина: {reason}\n⭐ Теперь: {nr}")


# ========== ИГРЫ ==========
@bot.command()
async def casino(ctx, amount: int = None):
    if not amount:
        await ctx.send("🎰 **Казино**\n`j.casino [ставка]` - шанс x2 (35%)\n⏰ КД: 5 минут")
        return
    can, w = check_cooldown(ctx.author.id, "casino")
    if not can:
        await ctx.send(f"❌ КД! Подождите {w} секунд")
        return
    if amount < 10:
        await ctx.send("❌ Мин. ставка 10 💎")
        return
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal < amount:
        await ctx.send(f"❌ Не хватает ({bal} 💎)")
        return
    msg = await ctx.send(f"🎰 {ctx.author.mention} крутит слот...")
    for _ in range(3):
        await asyncio.sleep(0.3)
        await msg.edit(content=f"🎰 {' '.join(random.choices(SLOT_EMOJIS, k=3))}")
    win = random.random() < WIN_CHANCE["casino"]
    set_cooldown(ctx.author.id, "casino")
    if win:
        wa = amount * 2
        await add_balance(ctx.author.id, ctx.guild.id, wa)
        await msg.edit(content=f"🎰 **ВЫИГРЫШ!** {ctx.author.mention} +{wa} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await msg.edit(content=f"🎰 **ПРОИГРЫШ!** {ctx.author.mention} -{amount} 💎")


@bot.command()
async def slots(ctx, bet: int = None):
    if not bet:
        await ctx.send("🎰 **Слоты**\n`j.slots [ставка]` - сыграйте в слоты (x2, x5, x10)\n⏰ КД: 5 минут")
        return
    can, w = check_cooldown(ctx.author.id, "casino")
    if not can:
        await ctx.send(f"❌ КД! Подождите {w} секунд")
        return
    if bet < 10:
        await ctx.send("❌ Мин. ставка 10 💎")
        return
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal < bet:
        await ctx.send(f"❌ Не хватает ({bal} 💎)")
        return
    msg = await ctx.send(f"🎰 {ctx.author.mention} крутит слоты...")
    for _ in range(3):
        await asyncio.sleep(0.3)
        await msg.edit(content=f"🎰 {' '.join(random.choices(SLOT_EMOJIS, k=3))}")
    res = random.choices(SLOT_EMOJIS, k=3)
    mul = 10 if res[0] == res[1] == res[2] else 2 if res[0] == res[1] or res[1] == res[2] or res[0] == res[2] else 0
    set_cooldown(ctx.author.id, "casino")
    if mul:
        win = bet * mul
        await add_balance(ctx.author.id, ctx.guild.id, win)
        await msg.edit(content=f"🎰 **{' '.join(res)}**\n🎉 ВЫИГРЫШ! {ctx.author.mention} +{win} 💎 (x{mul})")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🎰 **{' '.join(res)}**\n💔 ПРОИГРЫШ! {ctx.author.mention} -{bet} 💎")


@bot.command()
async def dice(ctx, num: int = None, bet: int = None):
    if not num or not bet:
        await ctx.send("🎲 **Кубик**\n`j.dice [1-6] [ставка]` - угадай цифру (x6)\n⏰ КД: 5 минут")
        return
    can, w = check_cooldown(ctx.author.id, "dice")
    if not can:
        await ctx.send(f"❌ КД! Подождите {w} секунд")
        return
    if num < 1 or num > 6:
        await ctx.send("❌ Цифра 1-6")
        return
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal < bet:
        await ctx.send(f"❌ Не хватает ({bal} 💎)")
        return
    msg = await ctx.send(f"🎲 {ctx.author.mention} бросает кубик...")
    for _ in range(2):
        await asyncio.sleep(0.3)
        await msg.edit(content=f"🎲 {random.choice(DICE_EMOJIS)}")
    roll = random.randint(1, 6)
    set_cooldown(ctx.author.id, "dice")
    if roll == num:
        win = bet * 6
        await add_balance(ctx.author.id, ctx.guild.id, win)
        await msg.edit(content=f"🎲 **ВЫПАЛО {roll}!** {ctx.author.mention} угадал! +{win} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🎲 **ВЫПАЛО {roll}!** {ctx.author.mention} не угадал. -{bet} 💎")


@bot.command()
async def coinflip(ctx, side: str = None, bet: int = None):
    if not side or not bet:
        await ctx.send("🪙 **Монетка**\n`j.coinflip [орёл/решка] [ставка]` - угадай сторону (x2)\n⏰ КД: 5 минут")
        return
    can, w = check_cooldown(ctx.author.id, "coin")
    if not can:
        await ctx.send(f"❌ КД! Подождите {w} секунд")
        return
    side = side.lower()
    if side not in ["орёл", "орел", "решка"]:
        await ctx.send("❌ орёл или решка")
        return
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal < bet:
        await ctx.send(f"❌ Не хватает ({bal} 💎)")
        return
    msg = await ctx.send(f"🪙 {ctx.author.mention} подбрасывает монетку...")
    await asyncio.sleep(0.5)
    res = random.choice(["орёл", "решка"])
    win = random.random() < WIN_CHANCE["coin"]
    set_cooldown(ctx.author.id, "coin")
    if (side in ["орёл", "орел"] and res == "орёл" and win) or (side == "решка" and res == "решка" and win):
        wa = bet * 2
        await add_balance(ctx.author.id, ctx.guild.id, wa)
        await msg.edit(content=f"🪙 **ВЫПАЛ {res.upper()}!** {ctx.author.mention} угадал! +{wa} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🪙 **ВЫПАЛ {res.upper()}!** {ctx.author.mention} не угадал. -{bet} 💎")


@bot.command()
async def rps(ctx, choice: str = None, bet: int = None):
    if not choice or not bet:
        await ctx.send("✊ **КНБ**\n`j.rps [камень/ножницы/бумага] [ставка]` - игра с ботом (x2)\n⏰ КД: 5 минут")
        return
    can, w = check_cooldown(ctx.author.id, "rps")
    if not can:
        await ctx.send(f"❌ КД! Подождите {w} секунд")
        return
    choice = choice.lower()
    if choice not in ["камень", "ножницы", "бумага"]:
        await ctx.send("❌ камень/ножницы/бумага")
        return
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal < bet:
        await ctx.send(f"❌ Не хватает ({bal} 💎)")
        return
    botc = random.choice(["камень", "ножницы", "бумага"])
    msg = await ctx.send(f"✊ {ctx.author.mention} vs бот...")
    await asyncio.sleep(0.5)
    win = random.random() < WIN_CHANCE["rps"]
    set_cooldown(ctx.author.id, "rps")
    if choice == botc:
        await msg.edit(content=f"✊ {choice} vs {botc} → **НИЧЬЯ!** Ставка возвращена")
        return
    if (choice == "камень" and botc == "ножницы") or (choice == "ножницы" and botc == "бумага") or (choice == "бумага" and botc == "камень"):
        if win:
            wa = bet * 2
            await add_balance(ctx.author.id, ctx.guild.id, wa)
            await msg.edit(content=f"✊ {choice} vs {botc} → **ВЫИГРЫШ!** +{wa} 💎")
        else:
            await add_balance(ctx.author.id, ctx.guild.id, -bet)
            await msg.edit(content=f"✊ {choice} vs {botc} → **ПРОИГРЫШ!** -{bet} 💎")
    else:
        if win:
            wa = bet * 2
            await add_balance(ctx.author.id, ctx.guild.id, wa)
            await msg.edit(content=f"✊ {choice} vs {botc} → **ВЫИГРЫШ!** +{wa} 💎")
        else:
            await add_balance(ctx.author.id, ctx.guild.id, -bet)
            await msg.edit(content=f"✊ {choice} vs {botc} → **ПРОИГРЫШ!** -{bet} 💎")


@bot.command()
async def blackjack(ctx, bet: int = None):
    if not bet:
        await ctx.send("🃏 **Блэкджек**\n`j.blackjack [ставка]` - игра против дилера\n⏰ КД: 5 минут")
        return
    can, w = check_cooldown(ctx.author.id, "blackjack")
    if not can:
        await ctx.send(f"❌ КД! Подождите {w} секунд")
        return
    if bet < 10:
        await ctx.send("❌ Мин. ставка 10 💎")
        return
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal < bet:
        await ctx.send(f"❌ Не хватает ({bal} 💎)")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -bet)
    deck = FULL_DECK.copy()
    random.shuffle(deck)
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    
    def hv(hand):
        v, a = 0, 0
        for c in hand:
            r = c[:-2] if len(c) > 2 else c[:-1]
            if r in ['J','Q','K']:
                v += 10
            elif r == 'A':
                a += 1; v += 11
            else:
                v += int(r)
        while v > 21 and a > 0:
            v -= 10; a -= 1
        return v
    
    msg = await ctx.send(f"🃏 **БЛЭКДЖЕК** | Ставка: {bet} 💎\n\nВаши карты: {' '.join(player)} ({hv(player)})\nКарты дилера: {dealer[0]} ?")
    
    class BJView(View):
        def __init__(self):
            super().__init__(timeout=30)
            self.ended = False
        
        @discord.ui.button(label="Ещё", style=discord.ButtonStyle.primary)
        async def hit(self, interaction, button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Не ваша игра!", ephemeral=True)
                return
            player.append(deck.pop())
            pv = hv(player)
            if pv > 21:
                await interaction.response.edit_message(content=f"🃏 **БЛЭКДЖЕК**\n\nВаши карты: {' '.join(player)} ({pv})\nКарты дилера: {' '.join(dealer)} ({hv(dealer)})\n\n💔 **ПЕРЕБОР!** Вы проиграли!", view=None)
                self.ended = True
                set_cooldown(ctx.author.id, "blackjack")
                return
            await interaction.response.edit_message(content=f"🃏 **БЛЭКДЖЕК**\n\nВаши карты: {' '.join(player)} ({pv})\nКарты дилера: {dealer[0]} ?")
        
        @discord.ui.button(label="Стоп", style=discord.ButtonStyle.success)
        async def stand(self, interaction, button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Не ваша игра!", ephemeral=True)
                return
            pv = hv(player)
            dv = hv(dealer)
            while dv < 17:
                dealer.append(deck.pop())
                dv = hv(dealer)
            win = random.random() < WIN_CHANCE["blackjack"]
            set_cooldown(ctx.author.id, "blackjack")
            if dv > 21 or (pv > dv and win):
                wa = bet * 2
                await add_balance(ctx.author.id, ctx.guild.id, wa)
                await interaction.response.edit_message(content=f"🃏 **БЛЭКДЖЕК**\n\nВаши карты: {' '.join(player)} ({pv})\nКарты дилера: {' '.join(dealer)} ({dv})\n\n🎉 **ВЫИГРЫШ!** +{wa} 💎", view=None)
            elif pv == dv:
                await add_balance(ctx.author.id, ctx.guild.id, bet)
                await interaction.response.edit_message(content=f"🃏 **БЛЭКДЖЕК**\n\nВаши карты: {' '.join(player)} ({pv})\nКарты дилера: {' '.join(dealer)} ({dv})\n\n🤝 **НИЧЬЯ!** Ставка возвращена", view=None)
            else:
                await interaction.response.edit_message(content=f"🃏 **БЛЭКДЖЕК**\n\nВаши карты: {' '.join(player)} ({pv})\nКарты дилера: {' '.join(dealer)} ({dv})\n\n💔 **ПРОИГРЫШ!**", view=None)
            self.ended = True
        
        async def on_timeout(self):
            if not self.ended:
                await msg.edit(content="⏰ Время вышло! Ставка возвращена.", view=None)
                await add_balance(ctx.author.id, ctx.guild.id, bet)
    
    view = BJView()
    await msg.edit(view=view)


# ========== КРЕСТИКИ-НОЛИКИ ==========
@bot.command()
async def ttt(ctx, opp: discord.Member = None, bet: int = None):
    if not opp or not bet:
        await ctx.send("❌ **Крестики-нолики**\n`j.ttt @user [ставка]`")
        return
    if ctx.author == opp:
        await ctx.send("❌ Нельзя с собой")
        return
    if bet < 10:
        await ctx.send("❌ Мин. ставка 10 💎")
        return
    bal1 = (await get_user(ctx.author.id, ctx.guild.id))[4]
    bal2 = (await get_user(opp.id, ctx.guild.id))[4]
    if bal1 < bet or bal2 < bet:
        await ctx.send("❌ У кого-то не хватает")
        return
    
    embed = discord.Embed(title="🎮 Приглашение", description=f"{opp.mention}, игра на {bet} 💎? ✅ / ❌", color=discord.Color.purple())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    def check(r, u):
        return u.id == opp.id and str(r.emoji) in ["✅", "❌"] and r.message.id == msg.id
    
    try:
        r, u = await bot.wait_for('reaction_add', timeout=60, check=check)
        await msg.delete()
        if str(r.emoji) == "✅":
            ttt_games[ctx.channel.id] = {"p1": ctx.author.id, "p2": opp.id, "bet": bet, "board": ["⬜"]*9, "turn": ctx.author.id, "symbols": {ctx.author.id: "❌", opp.id: "⭕"}, "msg": None}
            await draw_board(ctx)
            await ctx.send(f"🎮 Игра началась! Ставка {bet} 💎. Ход {ctx.author.mention} (❌). `j.hod 1-9`")
        else:
            await ctx.send(f"❌ {opp.mention} отказался")
    except asyncio.TimeoutError:
        await msg.delete()
        await ctx.send(f"⏰ {opp.mention} не ответил")


async def draw_board(ctx):
    g = ttt_games.get(ctx.channel.id)
    if not g: return
    board = g["board"]
    display = "\n".join([" ".join(board[i:i+3]) for i in range(0,9,3)])
    cur = await bot.fetch_user(g["turn"])
    embed = discord.Embed(title="❌⭕ Крестики-нолики", description=f"Ставка: {g['bet']} 💎\n```\n{display}\n```\nХодит: {cur.mention}", color=discord.Color.purple())
    if g["msg"]:
        try:
            old = await ctx.channel.fetch_message(g["msg"])
            await old.edit(embed=embed)
        except:
            g["msg"] = (await ctx.send(embed=embed)).id
    else:
        g["msg"] = (await ctx.send(embed=embed)).id


def ttt_winner(board):
    wins = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
    for w in wins:
        if board[w[0]] == board[w[1]] == board[w[2]] and board[w[0]] != "⬜":
            return board[w[0]]
    return None


@bot.command()
async def hod(ctx, pos: int = None):
    if not pos:
        await ctx.send("❌ `j.hod [1-9]`\n1 2 3\n4 5 6\n7 8 9")
        return
    g = ttt_games.get(ctx.channel.id)
    if not g:
        await ctx.send("❌ Нет игры. Создайте: `j.ttt @user 100`")
        return
    if ctx.author.id not in [g["p1"], g["p2"]]:
        await ctx.send("❌ Вы не игрок")
        return
    if g["turn"] != ctx.author.id:
        await ctx.send("❌ Не ваш ход")
        return
    if pos < 1 or pos > 9:
        await ctx.send("❌ 1-9")
        return
    idx = pos-1
    if g["board"][idx] != "⬜":
        await ctx.send("❌ Занято")
        return
    g["board"][idx] = g["symbols"][ctx.author.id]
    winner = ttt_winner(g["board"])
    if winner:
        wid = g["p1"] if winner == "❌" else g["p2"]
        lid = g["p2"] if winner == "❌" else g["p1"]
        prize = g["bet"] * 2
        await add_balance(wid, ctx.guild.id, prize)
        await add_balance(lid, ctx.guild.id, -g["bet"])
        wu = await bot.fetch_user(wid)
        await draw_board(ctx)
        await ctx.send(f"🎉 {wu.mention} победил! Выигрыш: {prize} 💎")
        del ttt_games[ctx.channel.id]
        return
    if "⬜" not in g["board"]:
        await draw_board(ctx)
        await ctx.send("🤝 Ничья! Ставки возвращены")
        del ttt_games[ctx.channel.id]
        return
    g["turn"] = g["p1"] if g["turn"] == g["p2"] else g["p2"]
    await draw_board(ctx)


# ========== ТОПЫ ==========
@bot.command()
async def top(ctx, category: str = "messages", period: str = "всего"):
    if category == "messages":
        async with aiosqlite.connect("justice.db") as db:
            if period == "день":
                cur = await db.execute('SELECT user_id, today_messages FROM users WHERE guild_id=? AND today_messages>0 ORDER BY today_messages DESC LIMIT 10', (ctx.guild.id,))
            elif period == "неделя":
                cur = await db.execute('SELECT user_id, week_messages FROM users WHERE guild_id=? AND week_messages>0 ORDER BY week_messages DESC LIMIT 10', (ctx.guild.id,))
            elif period == "месяц":
                cur = await db.execute('SELECT user_id, month_messages FROM users WHERE guild_id=? AND month_messages>0 ORDER BY month_messages DESC LIMIT 10', (ctx.guild.id,))
            else:
                cur = await db.execute('SELECT user_id, total_messages FROM users WHERE guild_id=? AND total_messages>0 ORDER BY total_messages DESC LIMIT 10', (ctx.guild.id,))
            rows = await cur.fetchall()
        if not rows:
            await ctx.send("📊 Нет данных")
            return
        pn = {"день": "сегодня", "неделя": "за неделю", "месяц": "за месяц", "всего": "за всё время"}.get(period, "за всё время")
        msg = f"**🏆 ТОП ПО СООБЩЕНИЯМ {pn.upper()}**\n"
        for i, (uid, c) in enumerate(rows, 1):
            u = await bot.fetch_user(uid)
            if u: msg += f"{i}. {u.name} – {c} сообщ.\n"
        await ctx.send(msg)
    elif category == "reps":
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT user_id, reputation FROM users WHERE guild_id=? ORDER BY reputation DESC LIMIT 10', (ctx.guild.id,))
            rows = await cur.fetchall()
        if not rows:
            await ctx.send("📊 Нет данных")
            return
        msg = "**🏆 ТОП ПО РЕПУТАЦИИ**\n"
        for i, (uid, r) in enumerate(rows, 1):
            u = await bot.fetch_user(uid)
            if u: msg += f"{i}. {u.name} – {r} ⭐\n"
        await ctx.send(msg)
    elif category == "balance":
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT user_id, balance FROM users WHERE guild_id=? ORDER BY balance DESC LIMIT 10', (ctx.guild.id,))
            rows = await cur.fetchall()
        if not rows:
            await ctx.send("📊 Нет данных")
            return
        msg = "**🏆 ТОП ПО БАЛАНСУ**\n"
        for i, (uid, b) in enumerate(rows, 1):
            u = await bot.fetch_user(uid)
            if u: msg += f"{i}. {u.name} – {b} 💎\n"
        await ctx.send(msg)
    elif category == "level":
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT user_id, level, xp FROM users WHERE guild_id=? ORDER BY level DESC, xp DESC LIMIT 10', (ctx.guild.id,))
            rows = await cur.fetchall()
        if not rows:
            await ctx.send("📊 Нет данных")
            return
        msg = "**🏆 ТОП ПО УРОВНЮ**\n"
        for i, (uid, l, x) in enumerate(rows, 1):
            u = await bot.fetch_user(uid)
            if u: msg += f"{i}. {u.name} – {l} ур. ({x} XP)\n"
        await ctx.send(msg)
    else:
        await ctx.send("❌ Доступные категории: messages, reps, balance, level")


# ========== ИНФОРМАЦИОННЫЕ КОМАНДЫ ==========
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    t = member or ctx.author
    d = await get_user(t.id, ctx.guild.id)
    embed = discord.Embed(title=f"👤 Информация о {t.display_name}", color=discord.Color.blue())
    embed.set_thumbnail(url=t.avatar.url if t.avatar else t.default_avatar.url)
    embed.add_field(name="ID", value=t.id, inline=True)
    embed.add_field(name="Уровень", value=d[3], inline=True)
    embed.add_field(name="Репутация", value=d[6] if len(d)>6 else 0, inline=True)
    embed.add_field(name="Аккаунт создан", value=t.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="Присоединился", value=t.joined_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="Роли", value=", ".join([r.mention for r in t.roles[1:10]]), inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    embed = discord.Embed(title=f"📊 Информация о сервере {g.name}", color=discord.Color.blue())
    embed.add_field(name="👑 Владелец", value=g.owner.mention, inline=True)
    embed.add_field(name="👥 Участников", value=g.member_count, inline=True)
    embed.add_field(name="💬 Каналов", value=len(g.channels), inline=True)
    embed.add_field(name="🎭 Ролей", value=len(g.roles), inline=True)
    embed.add_field(name="📅 Создан", value=g.created_at.strftime("%d.%m.%Y"), inline=True)
    if g.icon: embed.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=embed)


@bot.command()
async def avatar(ctx, member: discord.Member = None):
    t = member or ctx.author
    embed = discord.Embed(title=f"🖼️ Аватар {t.display_name}", color=discord.Color.blue())
    embed.set_image(url=t.avatar.url if t.avatar else t.default_avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Понг! Задержка: **{round(bot.latency*1000)} мс**")


@bot.command()
async def about(ctx):
    embed = discord.Embed(title="🤖 Justice Bot", color=discord.Color.blue())
    embed.add_field(name="Версия", value="5.0", inline=True)
    embed.add_field(name="Библиотека", value="discord.py", inline=True)
    embed.add_field(name="Серверов", value=len(bot.guilds), inline=True)
    embed.add_field(name="Команд", value="200+", inline=True)
    embed.add_field(name="Префикс", value="j.", inline=True)
    embed.set_footer(text="Разработан для Justice Server")
    await ctx.send(embed=embed)


@bot.command()
async def invites(ctx, member: discord.Member = None):
    t = member or ctx.author
    invs = await ctx.guild.invites()
    c = sum(inv.uses for inv in invs if inv.inviter == t)
    await ctx.send(f"📨 {t.mention} пригласил **{c}** участников!")


@bot.command()
async def reminder(ctx, time_str: str = None, *, text: str = None):
    if not time_str or not text:
        await ctx.send("⏰ **Напоминание**\n`j.reminder 10м Написать отчёт` - напомнить через 10 минут\nДоступно: м, ч, д")
        return
    units = {"м": 60, "ч": 3600, "д": 86400}
    u = time_str[-1]
    if u not in units:
        await ctx.send("❌ Используйте: 10м, 1ч, 1д")
        return
    try:
        sec = int(time_str[:-1]) * units[u]
    except:
        await ctx.send("❌ Неверный формат времени")
        return
    await ctx.send(f"✅ Напоминание установлено! Я напомню через {time_str}")
    await asyncio.sleep(sec)
    await ctx.author.send(f"⏰ **НАПОМИНАНИЕ!**\nВы просили напомнить: {text}")


# ========== ЦВЕТНЫЕ РОЛИ ==========
async def create_color_message():
    global color_message_id
    ch = bot.get_channel(COLOR_ROLE_CHANNEL_ID)
    if not ch:
        print(f"❌ Канал для цветных ролей {COLOR_ROLE_CHANNEL_ID} не найден!")
        return
    
    async for msg in ch.history(limit=20):
        if msg.author == bot.user: await msg.delete()
    
    desc = "**👇 Нажми на реакцию – получишь цветную роль!**\n\n"
    for emoji, data in COLOR_ROLES.items():
        role = ch.guild.get_role(data["id"])
        if role: desc += f"{emoji} - {role.mention}\n"
    desc += "\n⚠️ **Чтобы убрать роль – сними реакцию.**"
    embed = discord.Embed(title="🎨 Выбери свой цвет!", description=desc, color=discord.Color.blue())
    msg = await ch.send(embed=embed)
    for emoji in COLOR_ROLES:
        await msg.add_reaction(emoji)
    color_message_id = msg.id
    print(f"✅ Сообщение с цветными ролями отправлено в канал {ch.mention}")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id or payload.channel_id != COLOR_ROLE_CHANNEL_ID:
        return
    g = bot.get_guild(payload.guild_id)
    if not g: return
    m = g.get_member(payload.user_id)
    if not m: return
    emoji = str(payload.emoji.name) if hasattr(payload.emoji, 'name') else None
    if emoji not in COLOR_ROLES: return
    rid = COLOR_ROLES[emoji]["id"]
    role = g.get_role(rid)
    if not role: return
    for r in COLOR_ROLES.values():
        old = g.get_role(r["id"])
        if old and old in m.roles: await m.remove_roles(old)
    await m.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != COLOR_ROLE_CHANNEL_ID: return
    g = bot.get_guild(payload.guild_id)
    if not g: return
    m = g.get_member(payload.user_id)
    if not m: return
    emoji = str(payload.emoji.name) if hasattr(payload.emoji, 'name') else None
    if emoji not in COLOR_ROLES: return
    rid = COLOR_ROLES[emoji]["id"]
    role = g.get_role(rid)
    if role and role in m.roles: await m.remove_roles(role)


# ========== ТИКЕТЫ ==========
class AcceptTicketButton(Button):
    def __init__(self, channel_id, creator_id):
        super().__init__(label="✅ Принять тикет", style=discord.ButtonStyle.success, emoji="✅")
        self.channel_id = channel_id
        self.creator_id = creator_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        is_support = False
        for role_id in SUPPORT_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role and role in interaction.user.roles:
                is_support = True
                break
        
        if not is_support:
            await interaction.followup.send("❌ Только поддержка может принимать тикеты!", ephemeral=True)
            return
        
        channel = bot.get_channel(self.channel_id)
        if not channel:
            await interaction.followup.send("❌ Канал не найден!", ephemeral=True)
            return
        
        new_name = f"принят-{channel.name.replace('тикет-', '')}"
        await channel.edit(name=new_name)
        
        old_topic = channel.topic or ""
        await channel.edit(topic=f"{old_topic}\nПринят: {interaction.user.name} | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        embed = discord.Embed(title="✅ ТИКЕТ ПРИНЯТ", description=f"Тикет принят {interaction.user.mention}\nОтветственный: {interaction.user.mention}", color=discord.Color.green())
        await channel.send(embed=embed)
        
        try:
            msg = await channel.fetch_message(interaction.message.id)
            await msg.edit(view=None)
        except:
            pass
        
        await interaction.followup.send("✅ Тикет принят!", ephemeral=True)


class CloseTicketButton(Button):
    def __init__(self, channel_id, creator_id):
        super().__init__(label="🔒 Закрыть тикет", style=discord.ButtonStyle.danger, emoji="🔒")
        self.channel_id = channel_id
        self.creator_id = creator_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        is_support = False
        for role_id in SUPPORT_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role and role in interaction.user.roles:
                is_support = True
                break
        
        is_creator = interaction.user.id == self.creator_id
        
        if not (is_support or is_creator):
            await interaction.followup.send("❌ Только создатель тикета или поддержка могут закрыть тикет!", ephemeral=True)
            return
        
        channel = bot.get_channel(self.channel_id)
        if not channel:
            await interaction.followup.send("❌ Канал не найден!", ephemeral=True)
            return
        
        messages = []
        async for m in channel.history(limit=200, oldest_first=True):
            messages.append(f"[{m.created_at.strftime('%d.%m.%Y %H:%M:%S')}] {m.author.name}: {m.content[:100] if m.content else '[вложение]'}")
        
        if not os.path.exists("ticket_logs"):
            os.makedirs("ticket_logs")
        
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = f"ticket_logs/ticket_{channel.name}_{now}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== ТИКЕТ {channel.name} ===\n")
            f.write(f"Создатель: {self.creator_id}\n")
            f.write(f"Закрыл: {interaction.user.name}\n")
            f.write(f"Дата: {now}\n")
            f.write(f"Всего сообщений: {len(messages)}\n\n")
            f.write("\n".join(messages))
        
        log_channel = bot.get_channel(LOGS_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"📋 **Закрыт тикет** {channel.mention}\n👤 Закрыл: {interaction.user.mention}\n📊 Сообщений: {len(messages)}")
            await log_channel.send(file=discord.File(log_file))
        
        await channel.delete()
        os.remove(log_file)
        
        await interaction.followup.send("🔒 Тикет закрыт!", ephemeral=True)


class TicketButton(Button):
    def __init__(self):
        super().__init__(label="🎫 Создать тикет", style=discord.ButtonStyle.primary, emoji="🎫")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            await interaction.followup.send("❌ Категория для тикетов не найдена!", ephemeral=True)
            return
        
        for channel in category.channels:
            if channel.topic and str(interaction.user.id) in channel.topic:
                await interaction.followup.send("❌ У вас уже есть открытый тикет!", ephemeral=True)
                return
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True)
        }
        
        for role_id in SUPPORT_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True, manage_channels=True)
        
        ticket_number = len([c for c in category.channels if c.name.startswith("тикет-")]) + 1
        channel = await category.create_text_channel(
            name=f"тикет-{ticket_number}",
            overwrites=overwrites,
            topic=f"Создатель: {interaction.user.id}"
        )
        
        active_tickets[channel.id] = {"creator": interaction.user.id}
        
        embed = discord.Embed(
            title="🎫 Тикет создан",
            description=f"{interaction.user.mention}, опишите вашу проблему.\n\nПоддержка скоро ответит.\n\n**Для закрытия тикета используйте кнопку ниже.**",
            color=discord.Color.green()
        )
        
        view = View()
        view.add_item(AcceptTicketButton(channel.id, interaction.user.id))
        view.add_item(CloseTicketButton(channel.id, interaction.user.id))
        
        await channel.send(embed=embed, view=view)
        await interaction.followup.send(f"✅ Тикет создан! Перейдите в {channel.mention}", ephemeral=True)


@bot.command()
async def close_ticket(ctx):
    if not ctx.channel.category or ctx.channel.category.id != TICKET_CATEGORY_ID:
        await ctx.send("❌ Эта команда доступна только в каналах тикетов!")
        return
    
    creator_id = None
    if ctx.channel.id in active_tickets:
        creator_id = active_tickets[ctx.channel.id]["creator"]
    elif ctx.channel.topic and "Создатель:" in ctx.channel.topic:
        try:
            creator_id = int(ctx.channel.topic.split("Создатель:")[1].strip().split()[0])
        except:
            pass
    
    is_support = False
    for role_id in SUPPORT_ROLE_IDS:
        role = ctx.guild.get_role(role_id)
        if role and role in ctx.author.roles:
            is_support = True
            break
    
    if not (is_support or ctx.author.id == creator_id):
        await ctx.send("❌ Только создатель тикета или поддержка могут закрыть тикет!")
        return
    
    messages = []
    async for m in ctx.channel.history(limit=200, oldest_first=True):
        messages.append(f"[{m.created_at.strftime('%d.%m.%Y %H:%M:%S')}] {m.author.name}: {m.content[:100] if m.content else '[вложение]'}")
    
    if not os.path.exists("ticket_logs"):
        os.makedirs("ticket_logs")
    
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = f"ticket_logs/ticket_{ctx.channel.name}_{now}.txt"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"=== ТИКЕТ {ctx.channel.name} ===\n")
        f.write(f"Создатель: {creator_id}\n")
        f.write(f"Закрыл: {ctx.author.name}\n")
        f.write(f"Дата: {now}\n")
        f.write(f"Всего сообщений: {len(messages)}\n\n")
        f.write("\n".join(messages))
    
    log_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"📋 **Закрыт тикет** {ctx.channel.mention}\n👤 Закрыл: {ctx.author.mention}\n📊 Сообщений: {len(messages)}")
        await log_channel.send(file=discord.File(log_file))
    
    await ctx.channel.delete()
    os.remove(log_file)


@bot.command()
async def tickets_list(ctx):
    if not any(ctx.guild.get_role(rid) in ctx.author.roles for rid in SUPPORT_ROLE_IDS):
        await ctx.send("❌ Только поддержка может просматривать список тикетов!")
        return
    
    if not active_tickets:
        await ctx.send("📭 Нет активных тикетов.")
        return
    
    embed = discord.Embed(title="📋 Активные тикеты", color=discord.Color.blue())
    for cid, data in active_tickets.items():
        ch = ctx.guild.get_channel(cid)
        if ch:
            creator = await bot.fetch_user(data["creator"])
            embed.add_field(name=f"#{ch.name}", value=f"Создатель: {creator.mention}\nСсылка: {ch.mention}", inline=False)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def ticket_history(ctx, ticket: discord.TextChannel = None):
    if not ticket:
        await ctx.send("❌ Укажите канал тикета: `j.ticket_history #канал`")
        return
    if not ticket.name.startswith(("тикет-", "принят-")):
        await ctx.send("❌ Это не канал тикета!")
        return
    
    await ctx.send(f"⏳ Сбор истории канала {ticket.mention}...")
    
    messages = []
    async for m in ticket.history(limit=500, oldest_first=True):
        messages.append(f"[{m.created_at.strftime('%d.%m.%Y %H:%M:%S')}] {m.author.name}: {m.content[:100] if m.content else '[вложение]'}")
    
    if not messages:
        await ctx.send("📭 Нет сообщений в этом тикете.")
        return
    
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = f"ticket_history_{ticket.name}_{now}.txt"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"=== ИСТОРИЯ ТИКЕТА ===\n")
        f.write(f"Канал: {ticket.name}\n")
        f.write(f"Топик: {ticket.topic or 'Нет'}\n")
        f.write(f"Всего сообщений: {len(messages)}\n\n")
        f.write("\n".join(messages))
    
    await ctx.send(file=discord.File(log_file))
    os.remove(log_file)


async def setup_ticket_system():
    channel = bot.get_channel(TICKET_CREATE_CHANNEL_ID)
    if not channel:
        print(f"❌ Канал для тикетов {TICKET_CREATE_CHANNEL_ID} не найден!")
        return
    
    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            await msg.delete()
    
    rules_embed = discord.Embed(
        title="📜 ПРАВИЛА ТИКЕТОВ",
        color=discord.Color.gold(),
        description="1. Не создавайте тикеты по пустякам\n2. Опишите проблему подробно\n3. Приложите доказательства\n4. Не спамьте в тикете\n5. Дождитесь ответа поддержки"
    )
    await channel.send(embed=rules_embed)
    
    embed = discord.Embed(
        title="🎫 ТИКЕТЫ ПОДДЕРЖКИ",
        description="Нажмите на кнопку ниже, чтобы создать тикет.\n\nПосле создания тикета вы увидите кнопку **🔒 Закрыть тикет** в самом канале.",
        color=discord.Color.blue()
    )
    view = View()
    view.add_item(TicketButton())
    await channel.send(embed=embed, view=view)
    print(f"✅ Система тикетов настроена в канале {channel.mention}")


# ========== ПРИВАТНЫЕ ГОЛОСОВЫЕ ==========
class VCControlPanel(View):
    def __init__(self, cid, oid):
        super().__init__(timeout=None)
        self.cid, self.oid = cid, oid
    
    @discord.ui.button(label="🔒 Закрыть", style=discord.ButtonStyle.danger)
    async def lock(self, i, b):
        if i.user.id != self.oid:
            await i.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        ch = bot.get_channel(self.cid)
        if ch: await ch.set_permissions(i.guild.default_role, connect=False)
        await i.response.send_message("🔒 Канал закрыт", ephemeral=True)
    
    @discord.ui.button(label="🔓 Открыть", style=discord.ButtonStyle.success)
    async def unlock(self, i, b):
        if i.user.id != self.oid:
            await i.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        ch = bot.get_channel(self.cid)
        if ch: await ch.set_permissions(i.guild.default_role, connect=True)
        await i.response.send_message("🔓 Канал открыт", ephemeral=True)
    
    @discord.ui.button(label="👥 Лимит", style=discord.ButtonStyle.primary)
    async def limit(self, i, b):
        if i.user.id != self.oid:
            await i.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        modal = LimitModal(self.cid)
        await i.response.send_modal(modal)
    
    @discord.ui.button(label="📝 Название", style=discord.ButtonStyle.primary)
    async def rename(self, i, b):
        if i.user.id != self.oid:
            await i.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        modal = RenameModal(self.cid)
        await i.response.send_modal(modal)
    
    @discord.ui.button(label="🚫 Бан", style=discord.ButtonStyle.danger)
    async def ban(self, i, b):
        if i.user.id != self.oid:
            await i.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        modal = BanModal(self.cid, self.oid)
        await i.response.send_modal(modal)
    
    @discord.ui.button(label="🗑 Удалить", style=discord.ButtonStyle.danger)
    async def delete(self, i, b):
        if i.user.id != self.oid:
            await i.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        ch = bot.get_channel(self.cid)
        if ch: await ch.delete()
        await i.response.send_message("🗑 Канал удалён", ephemeral=True)


class LimitModal(Modal):
    def __init__(self, cid):
        super().__init__(title="Лимит участников")
        self.cid = cid
        self.l = TextInput(label="Лимит (1-99)", placeholder="10", required=True)
        self.add_item(self.l)
    
    async def on_submit(self, i):
        try:
            lim = int(self.l.value)
            if lim < 1 or lim > 99:
                await i.response.send_message("❌ Лимит от 1 до 99", ephemeral=True)
                return
            ch = bot.get_channel(self.cid)
            if ch: await ch.edit(user_limit=lim)
            await i.response.send_message(f"✅ Лимит участников: {lim}", ephemeral=True)
        except:
            await i.response.send_message("❌ Введите число", ephemeral=True)


class RenameModal(Modal):
    def __init__(self, cid):
        super().__init__(title="Переименовать канал")
        self.cid = cid
        self.n = TextInput(label="Новое название", placeholder="Новый канал", required=True)
        self.add_item(self.n)
    
    async def on_submit(self, i):
        ch = bot.get_channel(self.cid)
        if ch: await ch.edit(name=self.n.value)
        await i.response.send_message(f"✅ Канал переименован в {self.n.value}", ephemeral=True)


class BanModal(Modal):
    def __init__(self, cid, oid):
        super().__init__(title="Забанить пользователя")
        self.cid, self.oid = cid, oid
        self.uid = TextInput(label="ID пользователя или @упоминание", placeholder="Введите ID или @username", required=True)
        self.add_item(self.uid)
    
    async def on_submit(self, i):
        ch = bot.get_channel(self.cid)
        if not ch:
            await i.response.send_message("❌ Канал не найден", ephemeral=True)
            return
        inp = self.uid.value.strip()
        target = None
        if inp.startswith('<@') and inp.endswith('>'):
            uid = int(inp.strip('<@!>'))
            target = i.guild.get_member(uid)
        elif inp.isdigit():
            target = i.guild.get_member(int(inp))
        if not target:
            await i.response.send_message("❌ Пользователь не найден", ephemeral=True)
            return
        if target.id == self.oid:
            await i.response.send_message("❌ Нельзя забанить владельца канала", ephemeral=True)
            return
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT banned_users FROM private_vc WHERE owner_id=?', (self.oid,))
            row = await cur.fetchone()
            banned = json.loads(row[0]) if row and row[0] else []
            if target.id not in banned:
                banned.append(target.id)
                await db.execute('UPDATE private_vc SET banned_users=? WHERE owner_id=?', (json.dumps(banned), self.oid))
                await db.commit()
        if target in ch.members: await target.move_to(None)
        await i.response.send_message(f"✅ {target.mention} забанен в голосовом канале", ephemeral=True)


@bot.event
async def on_voice_state_update(m, b, a):
    if a.channel and (not b.channel or b.channel != a.channel):
        await update_voice_streak(m)
    
    if a.channel and a.channel.id in vc_sessions:
        vc = a.channel
        oid = vc_sessions[vc.id]["owner"]
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT banned_users, is_locked, user_limit FROM private_vc WHERE owner_id=?', (oid,))
            row = await cur.fetchone()
            if row:
                banned = json.loads(row[0]) if row[0] else []
                locked = row[1] or 0
                lim = row[2] or 0
                if m.id in banned or (locked and m.id != oid) or (lim > 0 and len(vc.members) > lim and m.id != oid):
                    await m.move_to(None)
                    return
    
    if a.channel and a.channel.id == VC_TRIGGER_CHANNEL_ID:
        cat = m.guild.get_channel(VC_CREATE_CATEGORY_ID)
        if cat:
            name = f"👤 {m.display_name}"
            ov = {m.guild.default_role: discord.PermissionOverwrite(connect=True), m: discord.PermissionOverwrite(connect=True, manage_channels=True)}
            vc = await cat.create_voice_channel(name=name, overwrites=ov)
            await m.move_to(vc)
            panel = VCControlPanel(vc.id, m.id)
            await vc.send(f"{m.mention}, панель управления:", view=panel)
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('INSERT OR REPLACE INTO private_vc (owner_id, guild_id, channel_name, user_limit, is_locked, banned_users, created_at) VALUES (?,?,?,?,?,?,?)', (m.id, m.guild.id, name, 0, 0, json.dumps([]), datetime.now().isoformat()))
                await db.commit()
            vc_sessions[vc.id] = {"owner": m.id}
    
    if b.channel and b.channel.id in vc_sessions and len(b.channel.members) == 0:
        await asyncio.sleep(10)
        if len(b.channel.members) == 0:
            await b.channel.delete()
            del vc_sessions[b.channel.id]


# ========== СТО ЛОТО ==========
async def stoloto_scheduler():
    while True:
        now = datetime.now()
        target = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
        await run_stoloto()


async def run_stoloto():
    global stoloto_active, stoloto_tickets, stoloto_end_time
    ch = bot.get_channel(STOLOTO_CHANNEL_ID)
    if not ch: return
    stoloto_active, stoloto_tickets, stoloto_end_time = True, [], datetime.now().replace(hour=14, minute=0, second=0) + timedelta(days=1)
    embed = discord.Embed(title="🎰 СТО ЛОТО", description=f"**Новый розыгрыш начался!**\n\n⏰ Продажа билетов до: <t:{int(stoloto_end_time.timestamp())}:R>\n💰 Призовой фонд: **0** 💎\n\n**Купить билет:** `j.loto_buy` (цена: 50💎)", color=discord.Color.gold())
    await ch.send(embed=embed)
    await asyncio.sleep(86400)
    if not stoloto_tickets:
        await ch.send(embed=discord.Embed(title="🎰 СТО ЛОТО", description="😔 **Никто не купил билеты сегодня!**", color=discord.Color.red()))
    else:
        wid = random.choice(stoloto_tickets)
        prize = len(stoloto_tickets) * 50
        await add_balance(wid, ch.guild.id, prize)
        w = await bot.fetch_user(wid)
        await ch.send(embed=discord.Embed(title="🎰 СТО ЛОТО", description=f"**РОЗЫГРЫШ СОСТОЯЛСЯ!**\n\n🏆 **ПОБЕДИТЕЛЬ:** {w.mention}\n💰 **ПРИЗ:** {prize} 💎\n📊 Всего участников: {len(stoloto_tickets)}", color=discord.Color.gold()))
    stoloto_active = False


@bot.command()
async def loto_buy(ctx):
    global stoloto_tickets, stoloto_active, stoloto_end_time
    if not stoloto_active:
        await ctx.send("❌ Сейчас нет активного розыгрыша! Новый начинается каждый день в 14:00 МСК")
        return
    if datetime.now() >= stoloto_end_time:
        await ctx.send("❌ Продажа билетов на сегодня закончена!")
        return
    if ctx.author.id in stoloto_tickets:
        await ctx.send("❌ У вас уже есть билет на сегодня!")
        return
    if (await get_user(ctx.author.id, ctx.guild.id))[4] < 50:
        await ctx.send("❌ Недостаточно средств! Билет стоит 50 💎")
        return
    await add_balance(ctx.author.id, ctx.guild.id, -50)
    stoloto_tickets.append(ctx.author.id)
    await ctx.send(f"✅ {ctx.author.mention}, вы купили билет за 50 💎! Всего участников: {len(stoloto_tickets)}")


# ========== НАСТРОЙКИ ==========
@bot.command()
@commands.has_permissions(administrator=True)
async def settings(ctx, module: str = None, value: str = None):
    if ctx.guild.id not in guild_settings:
        guild_settings[ctx.guild.id] = {"welcome_channel": None, "log_channel": LOGS_CHANNEL_ID, "level_channel": LEVEL_CHANNEL_ID}
    if not module:
        s = guild_settings[ctx.guild.id]
        embed = discord.Embed(title="⚙️ НАСТРОЙКИ СЕРВЕРА", color=discord.Color.blue())
        embed.add_field(name="Канал приветствий", value=f"<#{s['welcome_channel']}>" if s['welcome_channel'] else "Не установлен", inline=False)
        embed.add_field(name="Канал логов", value=f"<#{s['log_channel']}>" if s['log_channel'] else "Не установлен", inline=False)
        embed.add_field(name="Канал уровней", value=f"<#{s['level_channel']}>" if s['level_channel'] else "Не установлен", inline=False)
        await ctx.send(embed=embed)
        return
    try:
        if module == "welcome":
            guild_settings[ctx.guild.id]["welcome_channel"] = int(value.strip('<#>'))
            await ctx.send(f"✅ Канал приветствий установлен: <#{guild_settings[ctx.guild.id]['welcome_channel']}>")
        elif module == "logs":
            guild_settings[ctx.guild.id]["log_channel"] = int(value.strip('<#>'))
            await ctx.send(f"✅ Канал логов установлен: <#{guild_settings[ctx.guild.id]['log_channel']}>")
        elif module == "levels":
            guild_settings[ctx.guild.id]["level_channel"] = int(value.strip('<#>'))
            await ctx.send(f"✅ Канал уровней установлен: <#{guild_settings[ctx.guild.id]['level_channel']}>")
        else:
            await ctx.send("❌ Доступные модули: welcome, logs, levels")
    except:
        await ctx.send("❌ Неверный канал")


@bot.command()
@commands.has_permissions(administrator=True)
async def reset_user(ctx, member: discord.Member = None):
    t = member or ctx.author
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET xp=0, level=0, balance=100, bank=0, reputation=0, warning_count=0, total_messages=0, today_messages=0, week_messages=0, month_messages=0, voice_streak=0, pots=0, crops="[]" WHERE user_id=? AND guild_id=?', (t.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🔄 Прогресс {t.mention} полностью сброшен!")


@bot.command()
@commands.has_permissions(administrator=True)
async def reset_db(ctx, confirm: str = None):
    if confirm != "confirm":
        await ctx.send("⚠️ **ВНИМАНИЕ!** Эта команда УДАЛИТ ВСЕ ДАННЫЕ!\n🔒 Чтобы подтвердить: `j.reset_db confirm`")
        return
    await ctx.send("⏳ Удаление базы данных...")
    try:
        if os.path.exists("justice.db"):
            os.remove("justice.db")
            await ctx.send("✅ База данных удалена! Перезапустите бота.")
        else:
            await ctx.send("❌ Файл базы данных не найден!")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)[:100]}")


@bot.command()
@commands.has_permissions(administrator=True)
async def backup_db(ctx):
    await ctx.send("⏳ Создание резервной копии...")
    try:
        if os.path.exists("justice.db"):
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_name = f"justice_db_backup_{now}.db"
            shutil.copy2("justice.db", backup_name)
            size = os.path.getsize(backup_name)
            size_mb = size / (1024 * 1024)
            embed = discord.Embed(title="💾 Резервная копия создана!", description=f"**Имя:** `{backup_name}`\n**Размер:** {size_mb:.2f} MB\n**Дата:** {now}", color=discord.Color.green())
            await ctx.send(embed=embed)
            os.remove(backup_name)
        else:
            await ctx.send("❌ База данных не найдена!")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)[:100]}")


@bot.command()
@commands.has_permissions(administrator=True)
async def download_backup(ctx):
    if not os.path.exists("justice.db"):
        await ctx.send("❌ База данных не найдена!")
        return
    await ctx.send("⏳ Подготовка файла...")
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    temp_backup = f"justice_db_{now}.db"
    shutil.copy2("justice.db", temp_backup)
    await ctx.send(file=discord.File(temp_backup))
    os.remove(temp_backup)
    await ctx.send("✅ Резервная копия отправлена!")


@bot.command()
@commands.has_permissions(administrator=True)
async def upload_backup(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Прикрепите файл .db к сообщению!")
        return
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith('.db'):
        await ctx.send("❌ Нужен файл .db!")
        return
    embed = discord.Embed(title="⚠️ ПОДТВЕРЖДЕНИЕ", description=f"Восстановить БД из файла **{attachment.filename}**?\nТекущая БД будет заменена!", color=discord.Color.orange())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    def check(r, u):
        return u.id == ctx.author.id and str(r.emoji) in ["✅", "❌"] and r.message.id == msg.id
    
    try:
        r, u = await bot.wait_for('reaction_add', timeout=30, check=check)
        if str(r.emoji) == "✅":
            await ctx.send("⏳ Восстановление...")
            if os.path.exists("justice.db"):
                shutil.copy2("justice.db", f"justice_db_before_restore_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db")
            await attachment.save("justice.db")
            await ctx.send("✅ База данных восстановлена! Перезапустите бота.")
        else:
            await ctx.send("❌ Отменено.")
    except asyncio.TimeoutError:
        await ctx.send("⏰ Время вышло.")
    await msg.delete()


@bot.command()
@commands.has_permissions(administrator=True)
async def backup_info(ctx):
    if not os.path.exists("justice.db"):
        await ctx.send("❌ База данных не найдена!")
        return
    size = os.path.getsize("justice.db")
    size_mb = size / (1024 * 1024)
    modified = datetime.fromtimestamp(os.path.getmtime("justice.db"))
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT COUNT(DISTINCT user_id) FROM users')
        user_count = (await cur.fetchone())[0]
    
    embed = discord.Embed(title="📊 ИНФОРМАЦИЯ О БД", color=discord.Color.blue())
    embed.add_field(name="📁 Файл", value="`justice.db`", inline=True)
    embed.add_field(name="📦 Размер", value=f"{size_mb:.2f} MB", inline=True)
    embed.add_field(name="🕐 Изменён", value=modified.strftime("%d.%m.%Y %H:%M:%S"), inline=True)
    embed.add_field(name="👥 Пользователей", value=user_count, inline=True)
    await ctx.send(embed=embed)


# ========== НОВЫЙ HELP С КНОПКАМИ ==========
class HelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.current_category = "profile"
        
        self.categories = {
            "profile": {
                "name": "👤 ПРОФИЛЬ И ЭКОНОМИКА",
                "commands": (
                    "`j.profile [@user]` - Показать профиль\n"
                    "`j.bio <текст>` - Установить биографию\n"
                    "`j.balance [@user]` - Показать баланс\n"
                    "`j.bank` - Показать банковский счёт\n"
                    "`j.deposit <сумма>` - Внести в банк\n"
                    "`j.withdraw <сумма>` - Вывести из банка\n"
                    "`j.pay @user <сумма>` - Перевести деньги\n"
                    "`j.daily` - Ежедневный бонус (50-150💎)\n"
                    "`j.weekly` - Еженедельный бонус (300-600💎)\n"
                    "`j.monthly` - Ежемесячный бонус (1000-2000💎)\n"
                    "`j.timely` - Бонус раз в 2 часа (20-50💎)\n"
                    "`j.work` - Работа (30-80💎, КД 1 час)"
                )
            },
            "games": {
                "name": "🎲 ИГРЫ",
                "commands": (
                    "`j.casino <ставка>` - Казино (x2, шанс 35%)\n"
                    "`j.slots <ставка>` - Слоты (x2/x10)\n"
                    "`j.dice <1-6> <ставка>` - Кубик (x6)\n"
                    "`j.coinflip <орёл/решка> <ставка>` - Монетка (x2)\n"
                    "`j.rps <камень/ножницы/бумага> <ставка>` - КНБ с ботом (x2)\n"
                    "`j.blackjack <ставка>` - Блэкджек (x2)\n"
                    "`j.ttt @user <ставка>` - Крестики-нолики\n"
                    "`j.hod <1-9>` - Ход в крестиках-ноликах\n"
                    "`j.poker create <2-6> <ставка>` - Создать покер лобби\n"
                    "`j.poker join` - Присоединиться к лобби\n"
                    "`j.poker start` - Начать игру\n"
                    "`j.poker_bet <сумма>` - Сделать ставку\n"
                    "`j.poker_check` - Чек (пропустить ход)\n"
                    "`j.poker_fold` - Спасовать"
                )
            },
            "reputation": {
                "name": "⭐ РЕПУТАЦИЯ И ОГРАБЛЕНИЕ",
                "commands": (
                    "`j.rep [@user]` - Показать репутацию\n"
                    "`j.plusrep @user [причина]` - +1 репутации (КД 1 час)\n"
                    "`j.minusrep @user [причина]` - -1 репутации (КД 1 час)\n"
                    "`+rep` / `-rep` (в ответ на сообщение) - Быстрая репутация\n"
                    "`j.rob @user` - Ограбить (шанс 5%, КД 1 час)"
                )
            },
            "farming": {
                "name": "🌾 ФЕРМА",
                "commands": (
                    "`j.farm` - Показать ферму\n"
                    "`j.buy_pot` - Купить горшок (макс 5)\n"
                    "`j.buy_seed <семя>` - Купить семена\n"
                    "`j.plant <номер> <семя>` - Посадить семя\n"
                    "`j.harvest <номер>` - Собрать урожай\n"
                    "`j.sell_crop <культура> <редкость>` - Продать урожай\n"
                    "`j.sell_all_crops` - Продать весь урожай\n\n"
                    "**Семена:** пшеница(50), кукуруза(80), томат(100),\n"
                    "картофель(60), морковь(70), мефедрон(500),\n"
                    "роза(150), кактус(120), подсолнух(90), тыква(200)"
                )
            },
            "shop": {
                "name": "🛍️ МАГАЗИН И ИНВЕНТАРЬ",
                "commands": (
                    "`j.shop` - Показать магазин\n"
                    "`j.buy <товар>` - Купить товар\n"
                    "`j.use <товар>` - Использовать предмет\n"
                    "`j.inventory [@user]` - Показать инвентарь\n\n"
                    "**Товары:** звезда(500💎), сердечко(300💎),\n"
                    "корона(1000💎), радуга(700💎), бриллиант(2000💎)"
                )
            },
            "moderation": {
                "name": "🛠️ МОДЕРАЦИЯ",
                "commands": (
                    "`j.warn @user [дни] [причина]` - Предупреждение\n"
                    "`j.warns [@user]` - Список варнов\n"
                    "`j.unwarn @user <номер>` - Снять варн\n"
                    "`j.awarn @user <причина>` - Ручной варн\n"
                    "`j.mywarns` - Свои варны\n"
                    "`j.mute @user <10м/1ч/1д> [причина]` - Мут\n"
                    "`j.unmute @user [причина]` - Снять мут\n"
                    "`j.timeout @user <минуты> [причина]` - Таймаут\n"
                    "`j.ban @user [время] [причина]` - Бан\n"
                    "`j.kick @user [причина]` - Кик\n"
                    "`j.clear <количество>` - Очистка чата"
                )
            },
            "automod": {
                "name": "🤖 АВТОМОДЕРАЦИЯ",
                "commands": (
                    "`j.automod status` - Текущие настройки\n"
                    "`j.automod enable/disable` - Вкл/выкл автомод\n"
                    "`j.automod words add/remove/list/clear` - Запрещённые слова\n"
                    "`j.automod invites on/off` - Реклама серверов\n"
                    "`j.automod phishing on/off` - Фишинг\n"
                    "`j.automod exempt add/remove/list` - Исключённые роли"
                )
            },
            "tickets": {
                "name": "🎟️ ТИКЕТЫ",
                "commands": (
                    "`j.close_ticket` - Закрыть текущий тикет\n"
                    "`j.tickets_list` - Список активных тикетов\n\n"
                    "**Для админов:**\n"
                    "`j.ticket_history #канал` - История тикета"
                )
            },
            "steam": {
                "name": "🎮 STEAM",
                "commands": (
                    "`j.steam set <steam_id>` - Привязать Steam ID\n"
                    "`j.steam profile [@user]` - Показать профиль (с кнопками)\n"
                    "`j.steam games [@user]` - Список игр (топ 10)\n"
                    "`j.steam recent [@user]` - Недавние игры"
                )
            },
            "stoloto": {
                "name": "🎰 СТО ЛОТО",
                "commands": (
                    "`j.loto_buy` - Купить билет (50💎)\n"
                    "Розыгрыш каждый день в **14:00 МСК**"
                )
            },
            "info": {
                "name": "📊 ИНФОРМАЦИОННЫЕ",
                "commands": (
                    "`j.userinfo [@user]` - Информация о пользователе\n"
                    "`j.serverinfo` - Информация о сервере\n"
                    "`j.avatar [@user]` - Аватар\n"
                    "`j.ping` - Задержка бота\n"
                    "`j.about` - О боте\n"
                    "`j.invites [@user]` - Приглашения\n"
                    "`j.reminder <10м/1ч/1д> <текст>` - Напоминание\n"
                    "`j.weather <город>` - Погода\n"
                    "`j.top messages [день/неделя/месяц/всего]` - Топ сообщений\n"
                    "`j.top reps` - Топ репутации\n"
                    "`j.top balance` - Топ баланса\n"
                    "`j.top level` - Топ уровня"
                )
            },
            "other": {
                "name": "🤖 ДРУГОЕ",
                "commands": (
                    "`j.ai <вопрос>` - Задать вопрос ИИ\n"
                    "`j.gender male/female` - Выбрать гендерную роль\n"
                    "`j.suggest <идея>` - Предложить идею\n"
                    "`j.accept <id> [вердикт]` - Принять идею (админ)\n"
                    "`j.deny <id> [вердикт]` - Отклонить идею (админ)\n"
                    "`j.giveaway create #канал <приз> <кол-во> <1д/1ч/10м>` - Розыгрыш (админ)\n"
                    "`j.add_shop_item <название> <цена> <роль_id> [описание]` - Добавить товар (админ)\n"
                    "`j.remove_shop_item <название>` - Удалить товар (админ)\n"
                    "`j.settings welcome/logs/levels #канал` - Настройки (админ)\n"
                    "`j.reset_user [@user]` - Сброс пользователя (админ)\n"
                    "`j.backup_db` - Создать бэкап (админ)\n"
                    "`j.download_backup` - Скачать БД (админ)\n"
                    "`j.upload_backup` - Восстановить БД (админ)\n"
                    "`j.backup_info` - Информация о БД (админ)"
                )
            },
            "voice": {
                "name": "🎤 ГОЛОСОВЫЕ КАНАЛЫ",
                "commands": (
                    "Зайдите в специальный канал, чтобы создать приватный голосовой канал.\n\n"
                    "**Кнопки управления:**\n"
                    "🔒 - Закрыть канал\n"
                    "🔓 - Открыть канал\n"
                    "👥 - Лимит участников (1-99)\n"
                    "📝 - Переименовать\n"
                    "🚫 - Забанить пользователя\n"
                    "🗑 - Удалить канал\n\n"
                    "🔥 **Огонёк:** Заходите в голосовой канал каждый день,\n"
                    "чтобы увеличивать серию и получать бонусы!"
                )
            }
        }
    
    async def send_embed(self, interaction: discord.Interaction, category: str):
        cat = self.categories.get(category, self.categories["profile"])
        embed = discord.Embed(title=f"{cat['name']}", description=cat["commands"], color=discord.Color.blue())
        total = len(self.categories)
        current = list(self.categories.keys()).index(category) + 1
        embed.set_footer(text=f"Страница {current}/{total} | Префикс: j. | Стрелки для навигации")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=0)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        cats = list(self.categories.keys())
        cur_idx = cats.index(self.current_category)
        prev_idx = (cur_idx - 1) % len(cats)
        self.current_category = cats[prev_idx]
        await self.send_embed(interaction, self.current_category)
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=0)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        cats = list(self.categories.keys())
        cur_idx = cats.index(self.current_category)
        next_idx = (cur_idx + 1) % len(cats)
        self.current_category = cats[next_idx]
        await self.send_embed(interaction, self.current_category)
    
    @discord.ui.button(label="🏠 Главная", style=discord.ButtonStyle.success, row=1)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        self.current_category = "profile"
        await self.send_embed(interaction, "profile")
    
    @discord.ui.button(label="🎲 Игры", style=discord.ButtonStyle.primary, row=1)
    async def games_shortcut(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        self.current_category = "games"
        await self.send_embed(interaction, "games")
    
    @discord.ui.button(label="🛠️ Модерация", style=discord.ButtonStyle.primary, row=1)
    async def mod_shortcut(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        self.current_category = "moderation"
        await self.send_embed(interaction, "moderation")
    
    @discord.ui.button(label="🎟️ Тикеты", style=discord.ButtonStyle.primary, row=1)
    async def tickets_shortcut(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        self.current_category = "tickets"
        await self.send_embed(interaction, "tickets")
    
    @discord.ui.button(label="🔒 Закрыть", style=discord.ButtonStyle.danger, row=2)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Эта панель не для вас!", ephemeral=True)
            return
        await interaction.response.delete_message()
        self.stop()


@bot.command()
async def help(ctx, *, command: str = None):
    if command:
        embed = discord.Embed(title=f"📖 Помощь по команде j.{command}", description="Используйте `j.help` для полного списка команд.", color=discord.Color.blue())
        await ctx.send(embed=embed)
        return
    
    view = HelpView(ctx.author.id)
    first_cat = view.categories["profile"]
    embed = discord.Embed(title=f"{first_cat['name']}", description=first_cat["commands"], color=discord.Color.blue())
    embed.set_footer(text=f"Страница 1/{len(view.categories)} | Префикс: j. | Стрелки для навигации")
    await ctx.send(embed=embed, view=view)


# ========== КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦА ==========
def is_owner(ctx):
    return ctx.author.id == ctx.guild.owner_id


@bot.command()
@commands.check(is_owner)
async def admin_help(ctx):
    embed = discord.Embed(title="👑 КОМАНДЫ ВЛАДЕЛЬЦА СЕРВЕРА", description="Только создатель сервера может использовать эти команды", color=discord.Color.gold())
    embed.add_field(name="💰 УПРАВЛЕНИЕ ЭКОНОМИКОЙ", value="`j.owner_give @user <сумма>` - выдать деньги\n`j.owner_take @user <сумма>` - забрать деньги\n`j.owner_set_balance @user <сумма>` - установить баланс\n`j.owner_reset_user @user` - полный сброс пользователя", inline=False)
    embed.add_field(name="💾 УПРАВЛЕНИЕ БЭКАПАМИ", value="`j.backup_db` - создать резервную копию\n`j.download_backup` - скачать БД на компьютер\n`j.upload_backup` - восстановить БД из файла\n`j.backup_info` - информация о БД", inline=False)
    embed.add_field(name="🛍️ УПРАВЛЕНИЕ МАГАЗИНОМ", value="`j.add_shop_item <название> <цена> <роль_id> [описание]` - добавить товар\n`j.remove_shop_item <название>` - удалить товар", inline=False)
    embed.add_field(name="⚙️ НАСТРОЙКИ", value="`j.settings` - показать настройки\n`j.settings welcome/logs/levels #канал` - установить каналы", inline=False)
    embed.add_field(name="🤖 АВТОМОДЕРАЦИЯ", value="`j.automod status` - текущие настройки\n`j.automod enable/disable` - вкл/выкл\n`j.automod words add/remove/list` - запрещённые слова\n`j.automod invites on/off` - реклама серверов\n`j.automod phishing on/off` - фишинг\n`j.automod exempt add/remove/list` - исключённые роли", inline=False)
    embed.set_footer(text="👑 Эти команды доступны только владельцу сервера")
    await ctx.send(embed=embed)


@bot.command()
@commands.check(is_owner)
async def owner_give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть положительной!")
        return
    await add_balance(member.id, ctx.guild.id, amount)
    embed = discord.Embed(title="👑 ВЫДАЧА СРЕДСТВ (Владелец)", description=f"{ctx.author.mention} выдал {amount} 💎 {member.mention}", color=discord.Color.gold())
    await ctx.send(embed=embed)
    try: await member.send(f"👑 Владелец сервера выдал вам **{amount}** 💎!")
    except: pass


@bot.command()
@commands.check(is_owner)
async def owner_take(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть положительной!")
        return
    ud = await get_user(member.id, ctx.guild.id)
    if ud[4] < amount:
        await ctx.send(f"❌ У {member.mention} недостаточно средств! Баланс: {ud[4]} 💎")
        return
    await add_balance(member.id, ctx.guild.id, -amount)
    embed = discord.Embed(title="👑 ИЗЪЯТИЕ СРЕДСТВ (Владелец)", description=f"{ctx.author.mention} забрал {amount} 💎 у {member.mention}", color=discord.Color.gold())
    await ctx.send(embed=embed)
    try: await member.send(f"👑 Владелец сервера забрал у вас **{amount}** 💎!")
    except: pass


@bot.command()
@commands.check(is_owner)
async def owner_set_balance(ctx, member: discord.Member, amount: int):
    if amount < 0:
        await ctx.send("❌ Баланс не может быть отрицательным!")
        return
    ud = await get_user(member.id, ctx.guild.id)
    diff = amount - ud[4]
    if diff > 0: await add_balance(member.id, ctx.guild.id, diff)
    elif diff < 0: await add_balance(member.id, ctx.guild.id, diff)
    embed = discord.Embed(title="👑 УСТАНОВКА БАЛАНСА (Владелец)", description=f"{ctx.author.mention} установил баланс {member.mention} на **{amount}** 💎", color=discord.Color.gold())
    await ctx.send(embed=embed)
    try: await member.send(f"👑 Владелец сервера установил ваш баланс на **{amount}** 💎!")
    except: pass


@bot.command()
@commands.check(is_owner)
async def owner_reset_user(ctx, member: discord.Member):
    embed = discord.Embed(title="⚠️ ПОДТВЕРЖДЕНИЕ", description=f"Вы уверены, что хотите полностью сбросить прогресс {member.mention}?\n\nНажмите ✅ для подтверждения.", color=discord.Color.red())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    def check(r, u):
        return u.id == ctx.author.id and str(r.emoji) in ["✅", "❌"] and r.message.id == msg.id
    
    try:
        r, u = await bot.wait_for('reaction_add', timeout=30, check=check)
        if str(r.emoji) == "✅":
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('UPDATE users SET xp=0, level=0, balance=100, bank=0, reputation=0, warning_count=0, total_messages=0, today_messages=0, week_messages=0, month_messages=0, voice_streak=0, pots=0, crops="[]", inventory="[]", awards="[]" WHERE user_id=? AND guild_id=?', (member.id, ctx.guild.id))
                await db.commit()
            await ctx.send(f"✅ Прогресс {member.mention} полностью сброшен!")
            try: await member.send(f"👑 Владелец сервера полностью сбросил ваш прогресс!")
            except: pass
        else:
            await ctx.send("❌ Сброс отменён.")
    except asyncio.TimeoutError:
        await ctx.send("⏰ Время вышло. Сброс отменён.")
    await msg.delete()


@bot.command()
@commands.check(is_owner)
async def owner_stats(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT COUNT(DISTINCT user_id) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_users = (await cur.fetchone())[0]
        cur = await db.execute('SELECT SUM(balance) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_balance = (await cur.fetchone())[0] or 0
        cur = await db.execute('SELECT SUM(xp) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_xp = (await cur.fetchone())[0] or 0
        cur = await db.execute('SELECT SUM(total_messages) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_messages = (await cur.fetchone())[0] or 0
    embed = discord.Embed(title="📊 СТАТИСТИКА СЕРВЕРА", description=f"Статистика для **{ctx.guild.name}**", color=discord.Color.gold())
    embed.add_field(name="👥 Пользователей в БД", value=total_users, inline=True)
    embed.add_field(name="💰 Общий баланс", value=f"{total_balance} 💎", inline=True)
    embed.add_field(name="✨ Общий опыт", value=f"{total_xp} XP", inline=True)
    embed.add_field(name="💬 Всего сообщений", value=total_messages, inline=True)
    await ctx.send(embed=embed)


# ========== СОБЫТИЯ ==========
@bot.event
async def on_message(msg):
    if msg.author.bot: return
    
    # Автомод
    sett = guild_settings.get(msg.guild.id, {})
    exempt = any(msg.guild.get_role(rid) in msg.author.roles for rid in sett.get("automod_exempt_roles", []))
    if not exempt and sett.get("automod_enabled", True):
        spam, reason = await check_spam(msg)
        if spam:
            try:
                await msg.delete()
                wc = await add_auto_warning(msg.author, reason, msg.channel)
                asyncio.create_task(send_warning_dm(msg.author, reason, wc, msg.channel))
                warn_msg = await msg.channel.send(f"⚠️ {msg.author.mention}, удалено за: **{reason}**")
                await asyncio.sleep(3)
                await warn_msg.delete()
            except: pass
            return
    
    # +rep/-rep
    if msg.reference and msg.content:
        try:
            ref = await msg.channel.fetch_message(msg.reference.message_id)
            target = ref.author
            if target != msg.author:
                cl = msg.content.lower().strip()
                if cl in ["+rep", "+реп", "++", "👍", "спасибо", "+"]:
                    can, w = check_rep_cooldown(msg.author.id, target.id)
                    if can:
                        set_rep_cooldown(msg.author.id, target.id)
                        nr = await add_reputation(target.id, msg.guild.id, 1)
                        await msg.reply(f"👍 +1 репутации {target.mention}! ⭐ Теперь: {nr}")
                elif cl in ["-rep", "-реп", "--", "👎", "-"]:
                    can, w = check_rep_cooldown(msg.author.id, target.id)
                    if can:
                        set_rep_cooldown(msg.author.id, target.id)
                        nr = await add_reputation(target.id, msg.guild.id, -1)
                        await msg.reply(f"👎 -1 репутации {target.mention}! ⭐ Теперь: {nr}")
        except: pass
    
    # ИИ на упоминание
    if bot.user in msg.mentions:
        clean = msg.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if clean:
            async with msg.channel.typing():
                resp = await get_ai_response(msg.author.id, clean)
            await msg.reply(resp, mention_author=False)
            return
    
    # Опыт и деньги
    if random.randint(1,3) == 1:
        xp_gain = random.randint(10, 25)
        lv_up, nl = await add_xp(msg.author.id, msg.guild.id, xp_gain)
        if lv_up:
            lch = bot.get_channel(LEVEL_CHANNEL_ID)
            if lch: await lch.send(f"🎉 {msg.author.mention} достиг {nl} уровня!")
            if nl in LEVEL_ROLES:
                role = msg.guild.get_role(LEVEL_ROLES[nl])
                if role and role not in msg.author.roles:
                    await msg.author.add_roles(role)
    
    earn = random.randint(MIN_EARN, MAX_EARN)
    await add_balance(msg.author.id, msg.guild.id, earn)
    await bot.process_commands(msg)


async def send_warning_dm(user, reason, wc, channel):
    try:
        await user.send(f"⚠️ **Автомодерация**\nВаше сообщение в {channel.mention} удалено.\n📝 Причина: {reason}\n⚠️ Предупреждений: {wc}/{ANTISPAM_MAX_WARNINGS}")
    except: pass


async def reset_activity_counters():
    now = datetime.now()
    async with aiosqlite.connect("justice.db") as db:
        if now.hour == 0 and now.minute < 5:
            await db.execute('UPDATE users SET today_messages = 0')
            print(f"[{now.strftime('%H:%M:%S')}] ✅ Дневные счетчики сброшены")
        if now.weekday() == 0 and now.hour == 0 and now.minute < 5:
            await db.execute('UPDATE users SET week_messages = 0')
            print(f"[{now.strftime('%H:%M:%S')}] ✅ Недельные счетчики сброшены")
        if now.day == 1 and now.hour == 0 and now.minute < 5:
            await db.execute('UPDATE users SET month_messages = 0')
            print(f"[{now.strftime('%H:%M:%S')}] ✅ Месячные счетчики сброшены")
        await db.commit()


@bot.event
async def on_ready():
    await init_db()
    await create_color_message()
    await setup_ticket_system()
    
    bot.loop.create_task(stoloto_scheduler())
    
    async def reset_loop():
        while True:
            await asyncio.sleep(60)
            await reset_activity_counters()
    bot.loop.create_task(reset_loop())
    
    print(f'✅ Бот {bot.user} запущен!')
    print(f'📊 На серверах: {len(bot.guilds)}')
    print(f'💡 Префикс команд: j.')
    print('=' * 50)


@bot.event
async def on_member_join(member):
    role = member.guild.get_role(DEFAULT_ROLE_ID)
    if role:
        try: await member.add_roles(role)
        except: pass
    sett = guild_settings.get(member.guild.id, {})
    wch = sett.get("welcome_channel", WELCOME_CHANNEL_ID)
    ch = bot.get_channel(wch)
    if ch:
        embed = discord.Embed(title="🎉 Добро пожаловать!", description=f"{member.mention} присоединился!", color=discord.Color.green())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await ch.send(embed=embed)


if __name__ == "__main__":
    print("🚀 Запуск бота Justice...")
    bot.run(TOKEN)
