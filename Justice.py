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
from datetime import datetime, timedelta
from openai import OpenAI
from collections import defaultdict
import re
import math
import shutil
import glob
# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("❌ Токен не найден! Добавь DISCORD_TOKEN в переменные окружения")
    exit(1)

# API ключи
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
YANDEX_WEATHER_API_KEY = os.getenv('YANDEX_WEATHER_API_KEY')

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
QUIZ_CHANNEL_ID = 1502637205187723433

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

# ИИ настройки
AI_API_KEY = "rk_live_G15mOokgVTN8hKFBvWVda38wZGOiXkVs"
AI_BASE_URL = "https://api.ranvik.ru/v1"
AI_MODEL = "gpt-5-nano"

AI_SYSTEM_PROMPT = """Ты дружелюбный помощник в Discord сервере.

ВАЖНО: СЕЙЧАС 2026 ГОД!
Если тебя спрашивают о текущей дате, времени, погоде или новостях — честно скажи, что ты не можешь получить актуальные данные в реальном времени, и предложи пользователю использовать команду `j.weather <город>` для погоды или проверить новости самостоятельно.

Никогда не выдумывай факты о текущих событиях, погоде или датах.
Отвечай кратко и по делу.
Представься как Justice Bot AI."""

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

# Викторина
QUIZ_INTERVAL_SECONDS = 7200
QUIZ_ANSWER_TIME = 180
QUIZ_REWARD = 200

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
durak_games = {}
quiz_active = False
quiz_question = None
quiz_answer = None
quiz_options = {}
quiz_message_id = None
stoloto_active = False
stoloto_tickets = []
stoloto_end_time = None
daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
active_vc_sessions = {}
voice_streaks = {}
farm_data = {}
guild_settings = {}
active_tickets = {}
color_message_id = None
vc_sessions = {}
user_message_timestamps = defaultdict(list)
user_warnings = defaultdict(list)
spam_messages_to_delete = defaultdict(list)
# Хранилище контекстов диалогов для каждого пользователя
user_conversations = defaultdict(list)  # {user_id: [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]}
MAX_CONTEXT_MESSAGES = 10  # Храним последние 10 сообщений из диалога
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

# Отладка ИИ
print(f"🤖 AI_MODEL: {AI_MODEL}")
print(f"🤖 AI_BASE_URL: {AI_BASE_URL}")
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
                CUSTOM_SHOP_ITEMS[row[0]] = {
                    "price": row[1],
                    "description": row[2],
                    "type": "role",
                    "role_id": row[3]
                }
    
    print("✅ База данных готова")


async def get_user(user_id, guild_id):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM users WHERE user_id=? AND guild_id=?', (user_id, guild_id))
        row = await cur.fetchone()
        if not row:
            now = datetime.now().isoformat()
            await db.execute('''
                INSERT INTO users (user_id, guild_id, join_date, balance, today_messages, week_messages, month_messages, total_messages, last_message_time, pots) 
                VALUES (?,?,?,?,?,?,?,?,?,0)
            ''', (user_id, guild_id, now, START_BALANCE, 0, 0, 0, 0, now))
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
        await db.execute('''
            UPDATE users SET 
                xp=?, level=?, 
                total_messages=total_messages+1, 
                today_messages=today_messages+1,
                week_messages=week_messages+1,
                month_messages=month_messages+1,
                last_message_time=?
            WHERE user_id=? AND guild_id=?
        ''', (new_xp, new_level, datetime.now().isoformat(), user_id, guild_id))
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


# ========== ПОГОДА (ЯНДЕКС) ==========
@bot.command()
async def weather(ctx, *, city: str = None):
    """🌤️ Погода в любом городе (Яндекс.Погода)"""
    
    if city is None:
        await ctx.send("🌤️ **Погода**\n`j.weather <город>` - показать погоду\nПример: `j.weather Москва`\n`j.weather 55.75,37.62` - по координатам")
        return
    
    if not YANDEX_WEATHER_API_KEY:
        await ctx.send("❌ Погода не настроена! Администратор должен добавить YANDEX_WEATHER_API_KEY в переменные окружения Railway.")
        return
    
    lat = None
    lon = None
    city_name = city
    
    coord_pattern = r'^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$'
    match = re.match(coord_pattern, city.replace(' ', ''))
    
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        city_name = f"{lat}, {lon}"
    else:
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
                
                condition_map = {
                    "clear": "☀️", "partly-cloudy": "⛅", "cloudy": "☁️",
                    "overcast": "☁️", "light-rain": "🌧️", "rain": "🌧️",
                    "heavy-rain": "🌧️", "showers": "🌧️", "wet-snow": "🌨️",
                    "light-snow": "❄️", "snow": "❄️", "heavy-snow": "❄️",
                    "thunderstorm": "⛈️", "hail": "🌨️"
                }
                emoji = condition_map.get(fact.get('condition'), "🌡️")
                
                condition_ru = {
                    "clear": "Ясно", "partly-cloudy": "Малооблачно",
                    "cloudy": "Облачно с прояснениями", "overcast": "Пасмурно",
                    "light-rain": "Небольшой дождь", "rain": "Дождь",
                    "heavy-rain": "Сильный дождь", "showers": "Ливень",
                    "wet-snow": "Дождь со снегом", "light-snow": "Небольшой снег",
                    "snow": "Снег", "heavy-snow": "Сильный снег",
                    "thunderstorm": "Гроза", "hail": "Град"
                }
                condition_text = condition_ru.get(fact.get('condition'), fact.get('condition', 'Неизвестно'))
                
                wind_dir_map = {
                    "nw": "Северо-западный", "n": "Северный", "ne": "Северо-восточный",
                    "w": "Западный", "e": "Восточный", "sw": "Юго-западный",
                    "s": "Южный", "se": "Юго-восточный", "c": "Штиль"
                }
                wind_dir_text = wind_dir_map.get(fact.get('wind_dir'), fact.get('wind_dir', ''))
                
                embed = discord.Embed(
                    title=f"{emoji} Погода в {city_name}",
                    description=f"*{condition_text.capitalize()}*",
                    color=discord.Color.blue()
                )
                embed.add_field(name="🌡️ Температура", value=f"{fact.get('temp')}°C", inline=True)
                embed.add_field(name="🤔 Ощущается как", value=f"{fact.get('feels_like')}°C", inline=True)
                embed.add_field(name="💧 Влажность", value=f"{fact.get('humidity')}%", inline=True)
                embed.add_field(name="💨 Ветер", value=f"{fact.get('wind_speed')} м/с, {wind_dir_text}".strip(', '), inline=True)
                embed.add_field(name="📊 Давление", value=f"{fact.get('pressure_mm')} мм рт. ст.", inline=True)
                
                await ctx.send(embed=embed)
                
        except aiohttp.ClientError:
            await ctx.send("❌ Ошибка соединения с сервером погоды. Попробуйте позже.")
        except Exception as e:
            await ctx.send(f"❌ Ошибка: {str(e)[:100]}")


# ========== ИИ С ВЕБ-ПОИСКОМ ==========
async def get_ai_response(user_id, user_message, with_web=True):
    """Максимально оптимизированный ИИ с веб-поиском"""
    global user_conversations
    
    lower_msg = user_message.lower()
    
    # ========== БЫСТРЫЕ ОТВЕТЫ БЕЗ API (чтобы не грузить сервер) ==========
    if "привет" in lower_msg or "здравствуй" in lower_msg or "ку" in lower_msg:
        return "👋 Привет! Чем могу помочь?"
    
    if "как дела" in lower_msg:
        return "😊 Всё отлично! А у тебя?"
    
    if "спасибо" in lower_msg or "благодарю" in lower_msg:
        return "🙏 Пожалуйста! Обращайся."
    
    if "кто ты" in lower_msg or "ты кто" in lower_msg:
        return "🤖 Я Justice Bot AI — твой помощник на этом сервере! Могу искать информацию в интернете."
    
    if "команды" in lower_msg or "help" in lower_msg or "помощь" in lower_msg:
        return "📋 **Мои команды:** `j.help` — список всех команд\n`j.profile` — твой профиль\n`j.ai <вопрос>` — задать вопрос\n`j.weather <город>` — погода"
    
    if "дата" in lower_msg or "сегодня" in lower_msg or "число" in lower_msg:
        now = datetime.now()
        days_ru = {"Monday": "понедельник", "Tuesday": "вторник", "Wednesday": "среда", 
                   "Thursday": "четверг", "Friday": "пятница", "Saturday": "суббота", "Sunday": "воскресенье"}
        return f"📅 Сегодня **{now.strftime('%d.%m.%Y')}**, {days_ru.get(now.strftime('%A'), now.strftime('%A'))}."
    
    if "время" in lower_msg or "сколько время" in lower_msg or "который час" in lower_msg:
        now = datetime.now()
        return f"🕐 Сейчас **{now.strftime('%H:%M:%S')}** по МСК."
    
    if "доброе утро" in lower_msg:
        return "🌅 Доброе утро! Хорошего дня!"
    
    if "добрый вечер" in lower_msg:
        return "🌆 Добрый вечер! Как прошёл день?"
    
    if "спокойной ночи" in lower_msg:
        return "🌙 Спокойной ночи! Сладких снов!"
    
    if "погода" in lower_msg:
        return "🌤️ Используй команду `j.weather <город>` для точной погоды!"
    
    # ========== ОСНОВНОЙ ЗАПРОС С ВЕБ-ПОИСКОМ ==========
    conversation = user_conversations.get(user_id, [])
    
    # Собираем контекст (только последние 5 сообщений для скорости)
    context_messages = []
    for msg in conversation[-10:]:  # Последние 10 сообщений
        context_messages.append(msg)
    
    # Пробуем ответить с веб-поиском
    for attempt in range(3):  # 3 попытки
        try:
            if with_web:
                # ВЕБ-ПОИСК через responses.create (максимально быстро)
                resp = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: ai_client.responses.create(
                            model=AI_MODEL,
                            input=user_message,
                            tools=[{"type": "web_search"}],
                            max_completion_tokens=500,  # Короткие ответы
                            temperature=0.5  # Меньше фантазий
                        )
                    ),
                    timeout=8.0  # Таймаут 8 секунд
                )
                answer = resp.output_text
            else:
                # Обычный чат
                messages = [
                    {"role": "system", "content": "Ты помощник. Отвечай кратко, максимум 2-3 предложения. Сегодня " + datetime.now().strftime('%d.%m.%Y')},
                ]
                for msg in context_messages:
                    messages.append(msg)
                messages.append({"role": "user", "content": user_message})
                
                resp = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: ai_client.chat.completions.create(
                            model=AI_MODEL,
                            messages=messages,
                            max_tokens=500,
                            temperature=0.7
                        )
                    ),
                    timeout=6.0
                )
                answer = resp.choices[0].message.content
            
            # Сохраняем в историю
            user_conversations[user_id].append({"role": "user", "content": user_message})
            user_conversations[user_id].append({"role": "assistant", "content": answer})
            
            if len(user_conversations[user_id]) > 20:
                user_conversations[user_id] = user_conversations[user_id][-20:]
            
            return answer
            
        except asyncio.TimeoutError:
            if attempt == 2:  # Последняя попытка
                return "⏳ **Поиск занял слишком много времени.** Попробуй спросить проще или повтори через минуту."
            continue
        except Exception as e:
            error_msg = str(e)
            if "rate" in error_msg.lower():
                return "📊 **Слишком много запросов!** Подожди 30 секунд."
            elif "key" in error_msg.lower():
                return "🔑 **Проблема с ключом API.** Сообщи администратору."
            elif "web_search" in error_msg.lower():
                # Если веб-поиск не работает, пробуем без него
                if with_web and attempt < 2:
                    with_web = False
                    continue
            if attempt == 2:
                return f"⚡ **Ошибка:** {error_msg[:100]}\nПопробуй переформулировать вопрос."
            continue
    
    return "❌ **Не удалось получить ответ.** Попробуй позже."


@bot.command()
async def ai(ctx, *, question: str):
    """🤖 Задать вопрос ИИ с веб-поиском"""
    if len(question) > 500:
        await ctx.send("❌ Вопрос слишком длинный! Максимум 500 символов.")
        return
    
    msg = await ctx.send("🔍 **Ищу информацию в интернете...**")
    async with ctx.typing():
        response = await get_ai_response(ctx.author.id, question, with_web=True)
    await msg.edit(content=response)

# ========== АВТОМОДЕРАЦИЯ ==========
@bot.command()
@commands.has_permissions(administrator=True)
async def reset_db(ctx, confirm: str = None):
    """🗑️ ПОЛНАЯ ОЧИСТКА БАЗЫ ДАННЫХ (все данные будут удалены!)
    Использование: j.reset_db confirm"""
    
    if confirm != "confirm":
        await ctx.send("⚠️ **ВНИМАНИЕ!** Эта команда УДАЛИТ ВСЕ ДАННЫЕ:\n"
                       "• Всех пользователей\n"
                       "• Балансы, уровни, опыт\n"
                       "• Инвентари, фермы\n"
                       "• Предупреждения, идеи, розыгрыши\n\n"
                       "🔒 Чтобы подтвердить, введите: `j.reset_db confirm`")
        return
    
    await ctx.send("⏳ Удаление базы данных...")
    
    try:
        # Закрываем все соединения с БД
        async with aiosqlite.connect("justice.db") as db:
            await db.close()
        
        # Удаляем файл
        if os.path.exists("justice.db"):
            os.remove("justice.db")
            await ctx.send("✅ База данных `justice.db` успешно удалена!\n🔄 Бот перезапускается...")
            
            # Перезапускаем бота
            await bot.close()
            # Бот автоматически перезапустится на Railway
        else:
            await ctx.send("❌ Файл базы данных не найден!")
            
    except Exception as e:
        await ctx.send(f"❌ Ошибка при удалении БД: {str(e)[:100]}")
async def check_spam(message):
    user_id = message.author.id
    content = message.content.strip().lower()
    now = time.time()
    
    settings = guild_settings.get(message.guild.id, {})
    bad_words = settings.get("automod_bad_words", [])
    for word in bad_words:
        if word in content:
            spam_messages_to_delete[user_id].append(message.id)
            return True, f"использование запрещённого слова: {word}"
    
    invite_pattern = r'(?:https?://)?(?:www\.)?(?:discord\.(?:gg|com/invite)|dsc\.gg)/[a-zA-Z0-9]+'
    if re.search(invite_pattern, content, re.IGNORECASE):
        spam_messages_to_delete[user_id].append(message.id)
        return True, "реклама Discord сервера"
    
    phishing_patterns = [
        r'(?:nitro|steam|discord)(?:\.gift|gift|\.com).*\b(free|giveaway|бесплатно)\b',
        r'(?:пополни|пополнение|баланс|займ|кредит|деньги)\b.*\b(https?://|www\.)',
        r'\b(банк|карт[аы]|сбер|тиньк|паспорт|снилс|инн|пароль|логин)\b.*\b(https?://|www\.)',
    ]
    for pattern in phishing_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            spam_messages_to_delete[user_id].append(message.id)
            return True, "подозрение на фишинг/мошенничество"
    
    if user_id not in user_message_timestamps:
        user_message_timestamps[user_id] = []
    
    user_message_timestamps[user_id].append(now)
    user_message_timestamps[user_id] = [t for t in user_message_timestamps[user_id] if now - t < ANTISPAM_WINDOW_SECONDS]
    
    spam_messages_to_delete[user_id].append(message.id)
    
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
        alert_embed = discord.Embed(
            title="🚨 ПРЕВЫШЕН ЛИМИТ ПРЕДУПРЕЖДЕНИЙ",
            description=f"Пользователь {user.mention} получил {warning_count} автоматических предупреждений за 24 часа.",
            color=discord.Color.red()
        )
        await send_log(user.guild.id, alert_embed)
    
    return warning_count


@bot.command()
@commands.has_permissions(administrator=True)
async def automod(ctx, action: str = None, module: str = None, *args):
    if ctx.guild.id not in guild_settings:
        guild_settings[ctx.guild.id] = {}
    
    settings = guild_settings[ctx.guild.id]
    
    if "automod_enabled" not in settings:
        settings["automod_enabled"] = True
        settings["automod_bad_words"] = []
        settings["automod_invites_enabled"] = True
        settings["automod_phishing_enabled"] = True
        settings["automod_exempt_roles"] = []
    
    if action is None or action == "status":
        embed = discord.Embed(title="⚙️ НАСТРОЙКИ АВТОМОДЕРАЦИИ", color=discord.Color.blue())
        status = "✅ ВКЛЮЧЁН" if settings["automod_enabled"] else "❌ ВЫКЛЮЧЕН"
        embed.add_field(name="📊 Общий статус", value=status, inline=False)
        embed.add_field(name="📝 Запрещённые слова", value=f"Слов в списке: {len(settings['automod_bad_words'])}", inline=True)
        invites_status = "✅ ВКЛ" if settings["automod_invites_enabled"] else "❌ ВЫКЛ"
        phishing_status = "✅ ВКЛ" if settings["automod_phishing_enabled"] else "❌ ВЫКЛ"
        embed.add_field(name="🚫 Реклама серверов", value=invites_status, inline=True)
        embed.add_field(name="🎣 Фишинг/мошенничество", value=phishing_status, inline=True)
        
        exempt_roles = []
        for role_id in settings["automod_exempt_roles"]:
            role = ctx.guild.get_role(role_id)
            if role:
                exempt_roles.append(role.mention)
        embed.add_field(name="👑 Исключённые роли", value=", ".join(exempt_roles) if exempt_roles else "Нет", inline=False)
        await ctx.send(embed=embed)
        return
    
    if action == "enable":
        settings["automod_enabled"] = True
        await ctx.send("✅ Автомодерация **ВКЛЮЧЕНА**")
        return
    if action == "disable":
        settings["automod_enabled"] = False
        await ctx.send("❌ Автомодерация **ВЫКЛЮЧЕНА**")
        return
    
    if action == "words":
        if len(args) == 0:
            await ctx.send("**📖 Настройка запрещённых слов:**\n`j.automod words add <слово>`\n`j.automod words remove <слово>`\n`j.automod words list`\n`j.automod words clear`")
            return
        if args[0] == "add" and len(args) >= 2:
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
        return
    
    if action == "invites":
        if len(args) == 0:
            await ctx.send("`j.automod invites on` - включить\n`j.automod invites off` - выключить")
            return
        if args[0] == "on":
            settings["automod_invites_enabled"] = True
            await ctx.send("✅ Проверка на рекламу серверов **ВКЛЮЧЕНА**")
        elif args[0] == "off":
            settings["automod_invites_enabled"] = False
            await ctx.send("❌ Проверка на рекламу серверов **ВЫКЛЮЧЕНА**")
        return
    
    if action == "phishing":
        if len(args) == 0:
            await ctx.send("`j.automod phishing on` - включить\n`j.automod phishing off` - выключить")
            return
        if args[0] == "on":
            settings["automod_phishing_enabled"] = True
            await ctx.send("✅ Проверка на фишинг **ВКЛЮЧЕНА**")
        elif args[0] == "off":
            settings["automod_phishing_enabled"] = False
            await ctx.send("❌ Проверка на фишинг **ВЫКЛЮЧЕНА**")
        return
    
    if action == "exempt":
        if len(args) == 0:
            await ctx.send("**📖 Исключённые роли:**\n`j.automod exempt add @роль`\n`j.automod exempt remove @роль`\n`j.automod exempt list`")
            return
        if args[0] == "add" and len(ctx.message.role_mentions) > 0:
            role = ctx.message.role_mentions[0]
            if role.id not in settings["automod_exempt_roles"]:
                settings["automod_exempt_roles"].append(role.id)
                await ctx.send(f"✅ Роль {role.mention} добавлена в исключения")
        elif args[0] == "remove" and len(ctx.message.role_mentions) > 0:
            role = ctx.message.role_mentions[0]
            if role.id in settings["automod_exempt_roles"]:
                settings["automod_exempt_roles"].remove(role.id)
                await ctx.send(f"✅ Роль {role.mention} удалена из исключений")
        elif args[0] == "list":
            roles = []
            for role_id in settings["automod_exempt_roles"]:
                role = ctx.guild.get_role(role_id)
                if role:
                    roles.append(role.mention)
            if roles:
                await ctx.send(f"**👑 Исключённые роли:**\n" + ", ".join(roles))
            else:
                await ctx.send("👑 Нет исключённых ролей")
        return
    
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
        time_left = ANTISPAM_WARNING_EXPIRE_HOURS * 3600 - (now - warn["time"])
        hours_left = int(time_left // 3600)
        minutes_left = int((time_left % 3600) // 60)
        embed.add_field(name=f"Предупреждение #{i}", value=f"📝 Причина: {warn['reason']}\n⏰ Сгорает через: {hours_left}ч {minutes_left}мин", inline=False)
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
        time_left = ANTISPAM_WARNING_EXPIRE_HOURS * 3600 - (now - warn["time"])
        hours_left = int(time_left // 3600)
        minutes_left = int((time_left % 3600) // 60)
        embed.add_field(name=f"Варн #{i}", value=f"📝 Причина: {warn['reason']}\n👮 Выдал: {warn.get('moderator', 'Automod')}\n⏰ Сгорает через: {hours_left}ч {minutes_left}мин", inline=False)
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
    
    if warn_number is None or warn_number < 1 or warn_number > len(user_warnings[user_id]):
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
    """Обновление огонька при заходе в голосовой канал"""
    today = datetime.now().date()
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT voice_streak, last_voice_join FROM users WHERE user_id=? AND guild_id=?', 
                               (member.id, member.guild.id))
        row = await cur.fetchone()
        
        if not row:
            streak = 1
        else:
            current_streak = row[0] or 0
            last_join = row[1]
            
            if last_join:
                last_date = datetime.fromisoformat(last_join).date() if isinstance(last_join, str) else last_join
                if last_date == today:
                    return current_streak  # Уже сегодня заходил
                elif last_date == today - timedelta(days=1):
                    streak = current_streak + 1  # Продолжение серии
                else:
                    streak = 1  # Серия СБРАСЫВАЕТСЯ (пропущен день)
            else:
                streak = 1
        
        await db.execute('UPDATE users SET voice_streak=?, last_voice_join=? WHERE user_id=? AND guild_id=?',
                        (streak, datetime.now().isoformat(), member.id, member.guild.id))
        await db.commit()
        
        # Бонус за огонёк (каждый день серии даёт бонус)
        bonus = streak * 5
        await add_balance(member.id, member.guild.id, bonus)
        return streak


# ========== ФЕРМА ==========
@bot.command()
async def farm(ctx):
    user_data = await get_user(ctx.author.id, ctx.guild.id)
    pots = user_data[28] if len(user_data) > 28 else 0
    crops_json = user_data[29] if len(user_data) > 29 else "[]"
    crops = json.loads(crops_json)
    
    embed = discord.Embed(title="🌾 ФЕРМА", color=discord.Color.green())
    embed.add_field(name="🏺 Горшки", value=f"**{pots}/5**", inline=True)
    embed.add_field(name="🌱 Посажено", value=f"**{len(crops)}** культур", inline=True)
    
    if crops:
        crop_list = ""
        for i, crop in enumerate(crops[:5]):
            if crop:
                planted = datetime.fromisoformat(crop["planted_at"])
                time_left = (planted + timedelta(seconds=SEEDS[crop["seed"]]["grow_time"]) - datetime.now())
                if time_left.total_seconds() > 0:
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    status = f"🌱 {hours}ч {minutes}мин"
                else:
                    status = "✅ ГОТОВО К СБОРУ!"
                crop_list += f"**{i+1}.** {crop['seed'].capitalize()} ({crop['rarity']}) - {status}\n"
        embed.add_field(name="📋 Посевы", value=crop_list[:1024], inline=False)
    
    embed.set_footer(text="j.buy_pot | j.buy_seed <семя> | j.plant <номер> <семя> | j.harvest <номер>")
    await ctx.send(embed=embed)


@bot.command()
async def buy_pot(ctx):
    user_data = await get_user(ctx.author.id, ctx.guild.id)
    pots = user_data[28] if len(user_data) > 28 else 0
    balance = user_data[4]
    
    if pots >= 5:
        await ctx.send("❌ У вас уже максимальное количество горшков (5)!")
        return
    
    price = 500 * (pots + 1)
    if balance < price:
        await ctx.send(f"❌ Недостаточно средств! Нужно **{price}** 💎")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -price)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET pots=? WHERE user_id=? AND guild_id=?', (pots + 1, ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"✅ Вы купили горшок №{pots + 1} за {price} 💎!")


@bot.command()
async def buy_seed(ctx, seed: str = None):
    if seed is None or seed.lower() not in SEEDS:
        seeds_list = ", ".join(SEEDS.keys())
        await ctx.send(f"🌱 **Доступные семена:**\n{seeds_list}\n\nЦены: пшеница(50), кукуруза(80), томат(100), картофель(60), морковь(70), мефедрон(500), роза(150), кактус(120), подсолнух(90), тыква(200)")
        return
    
    seed = seed.lower()
    price = SEEDS[seed]["price"]
    user_data = await get_user(ctx.author.id, ctx.guild.id)
    
    if user_data[4] < price:
        await ctx.send(f"❌ Недостаточно средств! Нужно **{price}** 💎")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -price)
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        row = await cur.fetchone()
        inventory = json.loads(row[0]) if row[0] else []
        inventory.append(f"seed_{seed}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inventory), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"✅ Вы купили семена **{seed.capitalize()}** за {price} 💎!")


@bot.command()
async def plant(ctx, pot: int = None, seed: str = None):
    if pot is None or seed is None:
        await ctx.send("❌ Использование: `j.plant <номер_горшка> <семя>`\nПример: `j.plant 1 пшеница`")
        return
    
    user_data = await get_user(ctx.author.id, ctx.guild.id)
    pots = user_data[28] if len(user_data) > 28 else 0
    crops_json = user_data[29] if len(user_data) > 29 else "[]"
    crops = json.loads(crops_json)
    
    if pot < 1 or pot > pots:
        await ctx.send(f"❌ У вас нет горшка №{pot}. У вас {pots} горшков.")
        return
    
    crop_index = pot - 1
    if crop_index < len(crops) and crops[crop_index] and crops[crop_index].get("planted_at"):
        await ctx.send(f"❌ Горшок №{pot} уже занят! Сначала соберите урожай командой `j.harvest {pot}`")
        return
    
    seed = seed.lower()
    if seed not in SEEDS:
        await ctx.send(f"❌ Семя '{seed}' не найдено! Доступны: {', '.join(SEEDS.keys())}")
        return
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        row = await cur.fetchone()
        inventory = json.loads(row[0]) if row[0] else []
        
        if f"seed_{seed}" not in inventory:
            await ctx.send(f"❌ У вас нет семян **{seed.capitalize()}**! Купите командой `j.buy_seed {seed}`")
            return
        
        inventory.remove(f"seed_{seed}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inventory), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    weights = SEEDS[seed]["rarity_weights"]
    rarity = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    
    while len(crops) < pot:
        crops.append(None)
    crops[pot - 1] = {"seed": seed, "planted_at": datetime.now().isoformat(), "rarity": rarity}
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET crops=? WHERE user_id=? AND guild_id=?', (json.dumps(crops), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    grow_time_hours = SEEDS[seed]["grow_time"] // 3600
    await ctx.send(f"✅ Вы посадили **{seed.capitalize()}** ({rarity}) в горшок №{pot}! Время роста: {grow_time_hours} часов.")


@bot.command()
async def harvest(ctx, pot: int = None):
    if pot is None:
        await ctx.send("❌ Использование: `j.harvest <номер_горшка>`")
        return
    
    user_data = await get_user(ctx.author.id, ctx.guild.id)
    pots = user_data[28] if len(user_data) > 28 else 0
    crops_json = user_data[29] if len(user_data) > 29 else "[]"
    crops = json.loads(crops_json)
    
    if pot < 1 or pot > pots:
        await ctx.send(f"❌ У вас нет горшка №{pot}")
        return
    
    crop_index = pot - 1
    if crop_index >= len(crops) or not crops[crop_index]:
        await ctx.send(f"❌ В горшке №{pot} ничего не посажено!")
        return
    
    crop = crops[crop_index]
    planted = datetime.fromisoformat(crop["planted_at"])
    grow_time = SEEDS[crop["seed"]]["grow_time"]
    ready_time = planted + timedelta(seconds=grow_time)
    
    if datetime.now() < ready_time:
        remaining = ready_time - datetime.now()
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        await ctx.send(f"❌ Урожай ещё не готов! Осталось: {hours}ч {minutes}мин")
        return
    
    base_price = SEEDS[crop["seed"]]["base_price"]
    multiplier = RARITY_MULTIPLIERS.get(crop["rarity"], 1.0)
    price = int(base_price * multiplier)
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        row = await cur.fetchone()
        inventory = json.loads(row[0]) if row[0] else []
        inventory.append(f"crop_{crop['seed']}_{crop['rarity']}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inventory), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    crops[crop_index] = None
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET crops=? WHERE user_id=? AND guild_id=?', (json.dumps(crops), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"✅ Вы собрали **{crop['seed'].capitalize()}** ({crop['rarity']}) с горшка №{pot}!\n💰 Цена: {price} 💎 (можно продать командой `j.sell_crop {crop['seed']} {crop['rarity']}`)")


@bot.command()
async def sell_crop(ctx, crop: str = None, rarity: str = None):
    if crop is None or rarity is None:
        await ctx.send("❌ Использование: `j.sell_crop <культура> <редкость>`\nПример: `j.sell_crop пшеница редкий`")
        return
    
    crop = crop.lower()
    if crop not in SEEDS:
        await ctx.send(f"❌ Культура '{crop}' не найдена!")
        return
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        row = await cur.fetchone()
        inventory = json.loads(row[0]) if row[0] else []
        
        item = f"crop_{crop}_{rarity}"
        if item not in inventory:
            await ctx.send(f"❌ У вас нет **{crop}** ({rarity}) в инвентаре!")
            return
        
        inventory.remove(item)
        
        base_price = SEEDS[crop]["base_price"]
        multiplier = RARITY_MULTIPLIERS.get(rarity, 1.0)
        price = int(base_price * multiplier)
        
        await add_balance(ctx.author.id, ctx.guild.id, price)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inventory), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"💰 Вы продали **{crop}** ({rarity}) за **{price}** 💎!")


@bot.command()
async def sell_all_crops(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        row = await cur.fetchone()
        inventory = json.loads(row[0]) if row[0] else []
        
        crops = [item for item in inventory if item.startswith("crop_")]
        if not crops:
            await ctx.send("❌ У вас нет урожая в инвентаре!")
            return
        
        total_price = 0
        for item in crops:
            parts = item.split("_")
            if len(parts) >= 3:
                crop = parts[1]
                rarity = parts[2]
                base_price = SEEDS.get(crop, {}).get("base_price", 100)
                multiplier = RARITY_MULTIPLIERS.get(rarity, 1.0)
                total_price += int(base_price * multiplier)
                inventory.remove(item)
        
        await add_balance(ctx.author.id, ctx.guild.id, total_price)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inventory), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"💰 Вы продали весь урожай за **{total_price}** 💎!")


# ========== ПРОФИЛЬ (ИСПРАВЛЕННЫЙ) ==========
@bot.command()
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = await get_user(target.id, ctx.guild.id)
    
    # ПРАВИЛЬНЫЕ ИНДЕКСЫ
    level = data[3]
    xp = data[2]
    balance = data[4]
    bank = data[5] if len(data) > 5 else 0
    reputation = data[6] if len(data) > 6 else 0
    total_msgs = data[9] if len(data) > 9 else 0
    today_msgs = data[21] if len(data) > 21 else 0
    week_msgs = data[22] if len(data) > 22 else 0
    month_msgs = data[23] if len(data) > 23 else 0
    voice_streak = data[26] if len(data) > 26 else 0
    bio = data[17] if len(data) > 17 and data[17] else "Нет биографии"
    gender = data[20] if len(data) > 20 else ""
    
    # Расчёт XP
    xp_for_next = 200 * ((level + 1) ** 2)
    xp_for_current = 200 * (level ** 2)
    percent = min(100, int((xp - xp_for_current) / (xp_for_next - xp_for_current) * 100)) if xp_for_next > xp_for_current else 0
    bar = "█" * (percent // 5) + "░" * (20 - (percent // 5))
    
    # Пол
    if gender == "male":
        gender_text = "Мужчина"
        gender_emoji = "👨"
    elif gender == "female":
        gender_text = "Женщина"
        gender_emoji = "👩"
    else:
        gender_text = "Не указан"
        gender_emoji = "❓"
    
    embed = discord.Embed(title=f"📊 ПРОФИЛЬ | {target.display_name}", color=discord.Color.gold())
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎚️ УРОВЕНЬ",
                    value=f"**{level}** уровень\n`{bar}` {percent}%\n✨ {xp} XP", inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💰 ЭКОНОМИКА",
                    value=f"💎 В кошельке: **{balance}**\n🏦 В банке: **{bank}**\n⭐ Репутация: **{reputation}**", inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📆 АКТИВНОСТЬ",
                    value=f"📅 Сегодня: **{today_msgs}**\n📅 Неделя: **{week_msgs}**\n📅 Месяц: **{month_msgs}**\n💬 Всего: **{total_msgs}**\n🔥 Огонёк: **{voice_streak}** дней", inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚧ ПОЛ", value=f"{gender_emoji} {gender_text}", inline=True)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📝 БИОГРАФИЯ", value=bio[:500], inline=False)
    
    await ctx.send(embed=embed)


@bot.command()
async def bio(ctx, *, text: str = None):
    if text is None:
        await ctx.send("📝 Использование: `j.bio Твоя биография`\nМаксимум 500 символов.")
        return
    
    if len(text) > 500:
        await ctx.send("❌ Биография не может быть длиннее 500 символов!")
        return
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET bio=? WHERE user_id=? AND guild_id=?', (text, ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send("✅ Ваша биография обновлена!")


# ========== STEAM СТАТИСТИКА ==========
@bot.command()
async def steam(ctx, action: str = None, *, user_input: str = None):
    if action is None:
        await ctx.send("🎮 **Steam команды:**\n`j.steam set <steam_id>` - привязать Steam ID\n`j.steam profile` - показать профиль\n`j.steam games` - список игр (топ 10)\n`j.steam recent` - недавние игры")
        return
    
    data = await get_user(ctx.author.id, ctx.guild.id)
    steam_id = data[25] if len(data) > 25 else None
    
    if action == "set":
        if user_input is None:
            await ctx.send("❌ Использование: `j.steam set <steam_id>`")
            return
        async with aiosqlite.connect("justice.db") as db:
            await db.execute('UPDATE users SET steam_id=? WHERE user_id=? AND guild_id=?', (user_input, ctx.author.id, ctx.guild.id))
            await db.commit()
        await ctx.send(f"✅ Steam ID привязан: `{user_input}`")
        return
    
    if not steam_id:
        await ctx.send("❌ Вы не привязали Steam ID! Используйте `j.steam set <id>`")
        return
    
    if not STEAM_API_KEY:
        await ctx.send("❌ Steam API не настроен! Администратор должен добавить STEAM_API_KEY в переменные окружения Railway.")
        return
    
    async with aiohttp.ClientSession() as session:
        if action == "profile":
            url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steam_id}"
            async with session.get(url) as resp:
                data_profile = await resp.json()
                if 'response' in data_profile and data_profile['response']['players']:
                    player = data_profile['response']['players'][0]
                    
                    status_map = {0: "Офлайн", 1: "В сети", 2: "Занят", 3: "Нет на месте", 4: "Спит", 5: "Ищет игру", 6: "Играет"}
                    status = status_map.get(player.get('personastate', 0), "Неизвестно")
                    
                    embed = discord.Embed(title=f"🎮 Steam Профиль", description=f"**{player.get('personaname', 'Неизвестно')}**", color=discord.Color.blue())
                    if player.get('avatarfull'):
                        embed.set_thumbnail(url=player['avatarfull'])
                    embed.add_field(name="🆔 Steam ID", value=steam_id, inline=True)
                    embed.add_field(name="🎮 Статус", value=status, inline=True)
                    
                    games_url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={steam_id}&include_appinfo=true&include_played_free_games=true"
                    async with session.get(games_url) as games_resp:
                        games_data = await games_resp.json()
                        if 'response' in games_data and games_data['response'].get('games'):
                            games_list = games_data['response']['games']
                            game_count = len(games_list)
                            total_hours = sum(g.get('playtime_forever', 0) for g in games_list) / 60
                            embed.add_field(name="📚 Игр в библиотеке", value=f"{game_count}", inline=True)
                            embed.add_field(name="⏱️ Часов в играх", value=f"{total_hours:.0f}ч", inline=True)
                        else:
                            embed.add_field(name="📚 Игр в библиотеке", value="Профиль приватный", inline=True)
                            embed.add_field(name="⏱️ Часов в играх", value="Профиль приватный", inline=True)
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"❌ Steam профиль с ID `{steam_id}` не найден!")
        
        elif action == "games":
            url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={steam_id}&include_appinfo=true&include_played_free_games=true"
            async with session.get(url) as resp:
                data_games = await resp.json()
                if 'response' in data_games and data_games['response'].get('games'):
                    games = sorted(data_games['response']['games'], key=lambda x: x.get('playtime_forever', 0), reverse=True)[:10]
                    game_list = ""
                    for i, game in enumerate(games, 1):
                        hours = game.get('playtime_forever', 0) / 60
                        name = game.get('name', 'Неизвестно')
                        game_list += f"{i}. {name} - {hours:.1f}ч\n"
                    
                    embed = discord.Embed(title="🎮 Ваши игры (топ 10 по времени)", color=discord.Color.blue())
                    embed.description = game_list if game_list else "Нет данных"
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Не удалось получить список игр. Возможно, профиль приватный.")
        
        elif action == "recent":
            url = f"https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/?key={STEAM_API_KEY}&steamid={steam_id}&count=5"
            async with session.get(url) as resp:
                data_recent = await resp.json()
                if 'response' in data_recent and data_recent['response'].get('games'):
                    games = data_recent['response']['games']
                    game_list = ""
                    for game in games:
                        name = game.get('name', 'Неизвестно')
                        minutes = game.get('playtime_2weeks', 0) / 60
                        game_list += f"🎮 {name} - {minutes:.1f}ч за 2 недели\n"
                    
                    embed = discord.Embed(title="🎮 Недавно сыгранные игры", color=discord.Color.blue())
                    embed.description = game_list if game_list else "Нет данных за последние 2 недели"
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Не удалось получить недавние игры. Возможно, профиль приватный.")
        else:
            await ctx.send("❌ Неизвестная команда.")


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
    if item is None:
        await ctx.send("❌ Использование: `j.buy [товар]`")
        return
    
    item = item.lower()
    
    if item in SHOP_ITEMS:
        data = SHOP_ITEMS[item]
    elif item in CUSTOM_SHOP_ITEMS:
        data = CUSTOM_SHOP_ITEMS[item]
    else:
        await ctx.send(f"❌ Товар `{item}` не найден")
        return
    
    user_data = await get_user(ctx.author.id, ctx.guild.id)
    if user_data[4] < data["price"]:
        await ctx.send(f"❌ Недостаточно средств ({user_data[4]} 💎, нужно {data['price']} 💎)")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -data["price"])
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        row = await cur.fetchone()
        inventory = json.loads(row[0]) if row[0] else []
        inventory.append(item)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inventory), ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"✅ {ctx.author.mention} купил **{item.capitalize()}** за {data['price']} 💎!")


@bot.command()
async def use(ctx, *, item: str = None):
    if item is None:
        await ctx.send("❌ Использование: `j.use [товар]`")
        return
    
    item = item.lower()
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        row = await cur.fetchone()
        inventory = json.loads(row[0]) if row[0] else []
        
        if item not in inventory:
            await ctx.send(f"❌ У вас нет **{item.capitalize()}** в инвентаре!")
            return
        
        inventory.remove(item)
        
        if item in SHOP_ITEMS:
            if SHOP_ITEMS[item]["type"] == "award":
                cur2 = await db.execute('SELECT awards FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
                row2 = await cur2.fetchone()
                awards = json.loads(row2[0]) if row2[0] else []
                if item not in awards:
                    awards.append(item)
                    await db.execute('UPDATE users SET awards=? WHERE user_id=? AND guild_id=?', (json.dumps(awards), ctx.author.id, ctx.guild.id))
                    await ctx.send(f"✅ Вы использовали **{item.capitalize()}**! Теперь он отображается в вашем профиле.")
                else:
                    await ctx.send(f"⚠️ У вас уже есть **{item.capitalize()}** в профиле!")
                    inventory.append(item)
        elif item in CUSTOM_SHOP_ITEMS:
            role_id = CUSTOM_SHOP_ITEMS[item]["role_id"]
            if role_id:
                role = ctx.guild.get_role(role_id)
                if role:
                    if role in ctx.author.roles:
                        await ctx.send(f"⚠️ У вас уже есть роль {role.mention}!")
                    else:
                        await ctx.author.add_roles(role)
                        await ctx.send(f"✅ Вы получили роль {role.mention}!")
                else:
                    await ctx.send(f"❌ Роль для этого предмета не найдена!")
        
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inventory), ctx.author.id, ctx.guild.id))
        await db.commit()


@bot.command()
async def inventory(ctx, member: discord.Member = None):
    target = member or ctx.author
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (target.id, ctx.guild.id))
        row = await cur.fetchone()
        inventory = json.loads(row[0]) if row[0] else []
    
    if not inventory:
        await ctx.send(f"📦 Инвентарь {target.mention} пуст!")
        return
    
    embed = discord.Embed(title=f"📦 Инвентарь {target.display_name}", color=discord.Color.blue())
    items = {}
    for i in inventory:
        items[i] = items.get(i, 0) + 1
    
    for item, count in items.items():
        embed.add_field(name=f"🔹 {item.capitalize()}", value=f"Количество: {count}\n`j.use {item}`", inline=True)
    
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def add_shop_item(ctx, name: str, price: int, role_id: int, *, description: str = "Кастомный товар"):
    if name.lower() in SHOP_ITEMS or name.lower() in CUSTOM_SHOP_ITEMS:
        await ctx.send(f"❌ Товар с именем `{name}` уже существует!")
        return
    
    CUSTOM_SHOP_ITEMS[name.lower()] = {"price": price, "description": description, "type": "role", "role_id": role_id}
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT OR REPLACE INTO custom_shop (name, price, description, role_id) VALUES (?,?,?,?)',
                        (name.lower(), price, description, role_id))
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
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} обнимает {member.mention}! 🤗", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["hug"])
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} обнимает себя! 🤗", color=discord.Color.pink())
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
    if choice is None:
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
        await db.execute('INSERT INTO suggestions (user_id, guild_id, suggestion, date) VALUES (?,?,?,?)',
                        (ctx.author.id, ctx.guild.id, suggestion, datetime.now().isoformat()))
        await db.commit()
        cur = await db.execute('SELECT last_insert_rowid()')
        suggestion_id = (await cur.fetchone())[0]
    
    embed = discord.Embed(title="💡 Новая идея", color=discord.Color.blue())
    embed.add_field(name=f"ID: {suggestion_id}", value=suggestion, inline=False)
    embed.add_field(name="Автор", value=ctx.author.mention, inline=True)
    embed.add_field(name="Статус", value="⏳ Ожидает рассмотрения", inline=True)
    await ctx.send(embed=embed)
    
    admin_channel = bot.get_channel(IDEA_REVIEW_CHANNEL_ID)
    if admin_channel:
        admin_embed = discord.Embed(title="💡 НОВАЯ ИДЕЯ", description=suggestion, color=discord.Color.gold(), timestamp=datetime.now())
        admin_embed.add_field(name="ID", value=suggestion_id, inline=True)
        admin_embed.add_field(name="Автор", value=ctx.author.mention, inline=True)
        admin_embed.add_field(name="Канал", value=ctx.channel.mention, inline=True)
        admin_embed.set_footer(text="j.accept <id> [вердикт] | j.deny <id> [вердикт]")
        await admin_channel.send(embed=admin_embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def accept(ctx, suggestion_id: int, *, verdict: str = "Принято!"):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT user_id, suggestion FROM suggestions WHERE id=? AND guild_id=?', (suggestion_id, ctx.guild.id))
        row = await cur.fetchone()
        if not row:
            await ctx.send(f"❌ Идея #{suggestion_id} не найдена!")
            return
        
        user_id, suggestion = row
        await db.execute('UPDATE suggestions SET status="accepted", verdict=? WHERE id=? AND guild_id=?',
                        (verdict, suggestion_id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"✅ Идея #{suggestion_id} принята! Вердикт: {verdict}")
    
    try:
        author = await bot.fetch_user(user_id)
        await author.send(f"✅ **Ваша идея принята!** на сервере {ctx.guild.name}\n📝 **Идея:** {suggestion}\n📋 **Вердикт:** {verdict}")
    except:
        pass


@bot.command()
@commands.has_permissions(administrator=True)
async def deny(ctx, suggestion_id: int, *, verdict: str = "Отклонено"):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT user_id, suggestion FROM suggestions WHERE id=? AND guild_id=?', (suggestion_id, ctx.guild.id))
        row = await cur.fetchone()
        if not row:
            await ctx.send(f"❌ Идея #{suggestion_id} не найдена!")
            return
        
        user_id, suggestion = row
        await db.execute('UPDATE suggestions SET status="denied", verdict=? WHERE id=? AND guild_id=?',
                        (verdict, suggestion_id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"❌ Идея #{suggestion_id} отклонена. Вердикт: {verdict}")
    
    try:
        author = await bot.fetch_user(user_id)
        await author.send(f"❌ **Ваша идея отклонена** на сервере {ctx.guild.name}\n📝 **Идея:** {suggestion}\n📋 **Вердикт:** {verdict}")
    except:
        pass


# ========== РОЗЫГРЫШИ ==========
@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx, action: str, channel: discord.TextChannel = None, prize: str = None, winners: int = None, duration: str = None):
    if action == "create":
        if not channel or not prize or not winners or not duration:
            await ctx.send("❌ j.giveaway create #канал приз кол-во 1д/1ч/10м")
            return
        time_units = {"м": 60, "ч": 3600, "д": 86400}
        unit = duration[-1]
        if unit not in time_units:
            await ctx.send("❌ Используйте м, ч, д")
            return
        try:
            value = int(duration[:-1])
            seconds = value * time_units[unit]
        except:
            await ctx.send("❌ Неверный формат времени")
            return
        end_time = datetime.now() + timedelta(seconds=seconds)
        embed = discord.Embed(title="🎉 **РОЗЫГРЫШ**",
                              description=f"**Приз:** {prize}\n**Победителей:** {winners}\n**Заканчивается:** <t:{int(end_time.timestamp())}:R>",
                              color=discord.Color.gold())
        embed.set_footer(text="Нажми на 🎉 чтобы участвовать!")
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🎉")
        async with aiosqlite.connect("justice.db") as db:
            await db.execute('INSERT INTO giveaways (channel_id, message_id, prize, winners, end_time, entries) VALUES (?,?,?,?,?,?)',
                            (channel.id, msg.id, prize, winners, end_time.isoformat(), '[]'))
            await db.commit()
        await ctx.send(f"✅ Розыгрыш создан в {channel.mention}!")
        await asyncio.sleep(seconds)
        await end_giveaway(msg.id, channel)
    else:
        await ctx.send("Доступно: create")


async def end_giveaway(message_id, channel):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT prize, winners, entries FROM giveaways WHERE message_id=? AND ended=0', (message_id,))
        row = await cur.fetchone()
        if not row:
            return
        prize, winners_count, entries_json = row
        entries = json.loads(entries_json)
        await db.execute('UPDATE giveaways SET ended=1 WHERE message_id=?', (message_id,))
        await db.commit()
    
    if not entries:
        await channel.send("😔 В розыгрыше никто не участвовал.")
        return
    
    selected = random.sample(entries, min(winners_count, len(entries)))
    winners = ", ".join(f"<@{uid}>" for uid in selected)
    embed = discord.Embed(title="🏆 **РЕЗУЛЬТАТЫ РОЗЫГРЫША**",
                          description=f"**Приз:** {prize}\n**Победители:** {winners}",
                          color=discord.Color.gold())
    await channel.send(embed=embed)


# ========== ЭКОНОМИЧЕСКИЕ КОМАНДЫ ==========
@bot.command()
async def balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = await get_user(target.id, ctx.guild.id)
    bank = data[5] if len(data) > 5 else 0
    await ctx.send(f"💰 Баланс {target.mention}: **{data[4]}** 💎 | 🏦 В банке: **{bank}** 💎")


@bot.command()
async def bank(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    bank = data[5] if len(data) > 5 else 0
    await ctx.send(f"🏦 **Банковский счёт** {ctx.author.mention}\n💰 На счету: **{bank}** 💎\n📈 Проценты: **{BANK_INTEREST * 100}%** в день")


@bot.command()
async def deposit(ctx, amount: int):
    if amount < 10:
        await ctx.send("❌ Минимальный вклад 10 💎")
        return
    data = await get_user(ctx.author.id, ctx.guild.id)
    if data[4] < amount:
        await ctx.send(f"❌ Недостаточно средств ({data[4]} 💎)")
        return
    await add_balance(ctx.author.id, ctx.guild.id, -amount)
    await add_bank(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"🏦 Вы внесли **{amount}** 💎 в банк")


@bot.command()
async def withdraw(ctx, amount: int):
    data = await get_user(ctx.author.id, ctx.guild.id)
    bank = data[5] if len(data) > 5 else 0
    if bank < amount:
        await ctx.send(f"❌ В банке {bank} 💎")
        return
    await add_bank(ctx.author.id, ctx.guild.id, -amount)
    await add_balance(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"🏦 Вы вывели **{amount}** 💎 из банка")


@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть положительной")
        return
    if member == ctx.author:
        await ctx.send("❌ Нельзя перевести самому себе")
        return
    sender = await get_user(ctx.author.id, ctx.guild.id)
    if sender[4] < amount:
        await ctx.send(f"❌ Недостаточно средств ({sender[4]} 💎)")
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
    data = await get_user(ctx.author.id, ctx.guild.id)
    last = data[10] if len(data) > 10 else None
    if last:
        last_date = datetime.fromisoformat(last)
        if (datetime.now() - last_date).days < 1:
            remaining = 86400 - (datetime.now() - last_date).seconds
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await ctx.send(f"⏰ Ежедневный бонус будет доступен через {hours}ч {minutes}мин")
            return
    earn = random.randint(50, 150)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET last_daily=? WHERE user_id=? AND guild_id=?', (datetime.now().isoformat(), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🎁 Ежедневный бонус! +{earn} 💎")


@bot.command()
async def weekly(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    last = data[11] if len(data) > 11 else None
    if last:
        last_date = datetime.fromisoformat(last)
        if (datetime.now() - last_date).days < 7:
            remaining = 604800 - (datetime.now() - last_date).seconds
            days = remaining // 86400
            hours = (remaining % 86400) // 3600
            await ctx.send(f"⏰ Еженедельный бонус будет доступен через {days}д {hours}ч")
            return
    earn = random.randint(300, 600)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET last_weekly=? WHERE user_id=? AND guild_id=?', (datetime.now().isoformat(), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🎁 Еженедельный бонус! +{earn} 💎")


@bot.command()
async def monthly(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    last = data[12] if len(data) > 12 else None
    if last:
        last_date = datetime.fromisoformat(last)
        if (datetime.now() - last_date).days < 30:
            remaining = 2592000 - (datetime.now() - last_date).seconds
            days = remaining // 86400
            await ctx.send(f"⏰ Ежемесячный бонус будет доступен через {days}д")
            return
    earn = random.randint(1000, 2000)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET last_monthly=? WHERE user_id=? AND guild_id=?', (datetime.now().isoformat(), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🎁 Ежемесячный бонус! +{earn} 💎")


@bot.command()
async def timely(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    last = data[13] if len(data) > 13 else None
    if last:
        last_date = datetime.fromisoformat(last)
        if (datetime.now() - last_date).seconds < 7200:
            remaining = 7200 - (datetime.now() - last_date).seconds
            mins = remaining // 60
            await ctx.send(f"⏰ Бонус будет доступен через {mins} минут")
            return
    earn = random.randint(20, 50)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET last_timely=? WHERE user_id=? AND guild_id=?', (datetime.now().isoformat(), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🎁 Бонус! +{earn} 💎")


@bot.command()
async def work(ctx):
    can, wait = check_cooldown(ctx.author.id, "work")
    if not can:
        mins = wait // 60
        await ctx.send(f"❌ КД! Подождите {mins} минут")
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
    can, wait = check_cooldown(ctx.author.id, "rob")
    if not can:
        mins = wait // 60
        await ctx.send(f"❌ КД! Подождите {mins} минут")
        return
    target_data = await get_user(member.id, ctx.guild.id)
    if target_data[4] < 50:
        await ctx.send(f"❌ У {member.mention} слишком мало денег для ограбления")
        return
    success = random.random() < WIN_CHANCE["rob"]
    set_cooldown(ctx.author.id, "rob")
    if success:
        steal = random.randint(10, int(target_data[4] * 0.3))
        await add_balance(ctx.author.id, ctx.guild.id, steal)
        await add_balance(member.id, ctx.guild.id, -steal)
        await ctx.send(f"🔫 **ОГРАБЛЕНИЕ УДАЛОСЬ!** {ctx.author.mention} украл у {member.mention} **{steal}** 💎")
    else:
        if random.random() < 0.5:
            rep_loss = random.randint(5, 15)
            await add_reputation(ctx.author.id, ctx.guild.id, -rep_loss)
            await ctx.send(f"🔫 **ТЕБЯ СПАЛИЛИ!** {ctx.author.mention}, ты пытался ограбить {member.mention}, но охрана заметила тебя!\nТвоя репутация упала на {rep_loss} пунктов 😔")
        else:
            await ctx.send(f"🔫 **НЕ УДАЛОСЬ!** {ctx.author.mention} пытался ограбить {member.mention}, но вовремя сбежал.")


@bot.command()
async def rep(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = await get_user(target.id, ctx.guild.id)
    rep = data[6] if len(data) > 6 else 0
    await ctx.send(f"⭐ Репутация {target.mention}: **{rep}**")


@bot.command()
async def plusrep(ctx, member: discord.Member, *, reason: str = "Не указана"):
    if member == ctx.author:
        await ctx.send("❌ Нельзя ставить +rep себе")
        return
    can, wait = check_rep_cooldown(ctx.author.id, member.id)
    if not can:
        mins = wait // 60
        await ctx.send(f"❌ КД! Вы уже меняли репутацию этому пользователю. Подождите {mins} минут")
        return
    set_rep_cooldown(ctx.author.id, member.id)
    new_rep = await add_reputation(member.id, ctx.guild.id, 1)
    await ctx.send(f"👍 {ctx.author.mention} повысил репутацию {member.mention}!\n📝 Причина: {reason}\n⭐ Теперь: {new_rep}")


@bot.command()
async def minusrep(ctx, member: discord.Member, *, reason: str = "Не указана"):
    if member == ctx.author:
        await ctx.send("❌ Нельзя ставить -rep себе")
        return
    can, wait = check_rep_cooldown(ctx.author.id, member.id)
    if not can:
        mins = wait // 60
        await ctx.send(f"❌ КД! Вы уже меняли репутацию этому пользователю. Подождите {mins} минут")
        return
    set_rep_cooldown(ctx.author.id, member.id)
    new_rep = await add_reputation(member.id, ctx.guild.id, -1)
    await ctx.send(f"👎 {ctx.author.mention} понизил репутацию {member.mention}!\n📝 Причина: {reason}\n⭐ Теперь: {new_rep}")


# ========== ИГРЫ ==========
@bot.command()
async def casino(ctx, amount: int = None):
    if amount is None:
        await ctx.send("🎰 **Казино**\n`j.casino [ставка]` - шанс x2 (35%)\n⏰ КД: 5 минут")
        return
    can, wait = check_cooldown(ctx.author.id, "casino")
    if not can:
        await ctx.send(f"❌ КД! Подождите {wait} секунд")
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
        win_amount = amount * 2
        await add_balance(ctx.author.id, ctx.guild.id, win_amount)
        await msg.edit(content=f"🎰 **ВЫИГРЫШ!** {ctx.author.mention} +{win_amount} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await msg.edit(content=f"🎰 **ПРОИГРЫШ!** {ctx.author.mention} -{amount} 💎")


@bot.command()
async def slots(ctx, bet: int = None):
    if bet is None:
        await ctx.send("🎰 **Слоты**\n`j.slots [ставка]` - сыграйте в слоты (x2, x5, x10)\n⏰ КД: 5 минут")
        return
    can, wait = check_cooldown(ctx.author.id, "casino")
    if not can:
        await ctx.send(f"❌ КД! Подождите {wait} секунд")
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
    slots_result = random.choices(SLOT_EMOJIS, k=3)
    win_mult = 0
    if slots_result[0] == slots_result[1] == slots_result[2]:
        win_mult = 10
    elif slots_result[0] == slots_result[1] or slots_result[1] == slots_result[2] or slots_result[0] == slots_result[2]:
        win_mult = 2
    set_cooldown(ctx.author.id, "casino")
    if win_mult > 0:
        win = bet * win_mult
        await add_balance(ctx.author.id, ctx.guild.id, win)
        await msg.edit(content=f"🎰 **{' '.join(slots_result)}**\n🎉 ВЫИГРЫШ! {ctx.author.mention} +{win} 💎 (x{win_mult})")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🎰 **{' '.join(slots_result)}**\n💔 ПРОИГРЫШ! {ctx.author.mention} -{bet} 💎")


@bot.command()
async def dice(ctx, цифра: int = None, ставка: int = None):
    if цифра is None or ставка is None:
        await ctx.send("🎲 **Кубик**\n`j.dice [1-6] [ставка]` - угадай цифру (x6)\n⏰ КД: 5 минут")
        return
    can, wait = check_cooldown(ctx.author.id, "dice")
    if not can:
        await ctx.send(f"❌ КД! Подождите {wait} секунд")
        return
    if цифра < 1 or цифра > 6:
        await ctx.send("❌ Цифра 1-6")
        return
    if ставка < 1:
        await ctx.send("❌ Ставка минимум 1 💎")
        return
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal < ставка:
        await ctx.send(f"❌ Не хватает ({bal} 💎)")
        return
    msg = await ctx.send(f"🎲 {ctx.author.mention} бросает кубик...")
    for _ in range(2):
        await asyncio.sleep(0.3)
        await msg.edit(content=f"🎲 {random.choice(DICE_EMOJIS)}")
    roll = random.randint(1, 6)
    set_cooldown(ctx.author.id, "dice")
    if roll == цифра:
        win = ставка * 6
        await add_balance(ctx.author.id, ctx.guild.id, win)
        await msg.edit(content=f"🎲 **ВЫПАЛО {roll}!** {ctx.author.mention} угадал! +{win} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -ставка)
        await msg.edit(content=f"🎲 **ВЫПАЛО {roll}!** {ctx.author.mention} не угадал. -{ставка} 💎")


@bot.command()
async def coinflip(ctx, сторона: str = None, ставка: int = None):
    if сторона is None or ставка is None:
        await ctx.send("🪙 **Монетка**\n`j.coinflip [орёл/решка] [ставка]` - угадай сторону (x2)\n⏰ КД: 5 минут")
        return
    can, wait = check_cooldown(ctx.author.id, "coin")
    if not can:
        await ctx.send(f"❌ КД! Подождите {wait} секунд")
        return
    сторона = сторона.lower()
    if сторона not in ["орёл", "орел", "решка"]:
        await ctx.send("❌ орёл или решка")
        return
    if ставка < 1:
        await ctx.send("❌ Укажите ставку")
        return
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal < ставка:
        await ctx.send(f"❌ Не хватает ({bal} 💎)")
        return
    msg = await ctx.send(f"🪙 {ctx.author.mention} подбрасывает монетку...")
    await asyncio.sleep(0.5)
    result = random.choice(["орёл", "решка"])
    win = random.random() < WIN_CHANCE["coin"]
    set_cooldown(ctx.author.id, "coin")
    if (сторона in ["орёл", "орел"] and result == "орёл" and win) or (сторона == "решка" and result == "решка" and win):
        win_amount = ставка * 2
        await add_balance(ctx.author.id, ctx.guild.id, win_amount)
        await msg.edit(content=f"🪙 **ВЫПАЛ {result.upper()}!** {ctx.author.mention} угадал! +{win_amount} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -ставка)
        await msg.edit(content=f"🪙 **ВЫПАЛ {result.upper()}!** {ctx.author.mention} не угадал. -{ставка} 💎")


@bot.command()
async def rps(ctx, выбор: str = None, ставка: int = None):
    choices = ["камень", "ножницы", "бумага"]
    if выбор is None or ставка is None:
        await ctx.send("✊ **КНБ**\n`j.rps [камень/ножницы/бумага] [ставка]` - игра с ботом (x2)\n⏰ КД: 5 минут")
        return
    can, wait = check_cooldown(ctx.author.id, "rps")
    if not can:
        await ctx.send(f"❌ КД! Подождите {wait} секунд")
        return
    if выбор.lower() not in choices:
        await ctx.send("❌ камень/ножницы/бумага")
        return
    if ставка < 1:
        await ctx.send("❌ Укажите ставку")
        return
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal < ставка:
        await ctx.send(f"❌ Не хватает ({bal} 💎)")
        return
    игрок = выбор.lower()
    бот_выбор = random.choice(choices)
    msg = await ctx.send(f"✊ {ctx.author.mention} vs бот...")
    await asyncio.sleep(0.5)
    win = random.random() < WIN_CHANCE["rps"]
    set_cooldown(ctx.author.id, "rps")
    if игрок == бот_выбор:
        await msg.edit(content=f"✊ {игрок} vs {бот_выбор} → **НИЧЬЯ!** Ставка возвращена")
        return
    if (игрок == "камень" and бот_выбор == "ножницы") or (игрок == "ножницы" and бот_выбор == "бумага") or (игрок == "бумага" and бот_выбор == "камень"):
        if win:
            win_amount = ставка * 2
            await add_balance(ctx.author.id, ctx.guild.id, win_amount)
            await msg.edit(content=f"✊ {игрок} vs {бот_выбор} → **ВЫИГРЫШ!** +{win_amount} 💎")
        else:
            await add_balance(ctx.author.id, ctx.guild.id, -ставка)
            await msg.edit(content=f"✊ {игрок} vs {бот_выбор} → **ПРОИГРЫШ!** -{ставка} 💎")
    else:
        if win:
            win_amount = ставка * 2
            await add_balance(ctx.author.id, ctx.guild.id, win_amount)
            await msg.edit(content=f"✊ {игрок} vs {бот_выбор} → **ВЫИГРЫШ!** +{win_amount} 💎")
        else:
            await add_balance(ctx.author.id, ctx.guild.id, -ставка)
            await msg.edit(content=f"✊ {игрок} vs {бот_выбор} → **ПРОИГРЫШ!** -{ставка} 💎")


@bot.command()
async def blackjack(ctx, bet: int = None):
    if bet is None:
        await ctx.send("🃏 **Блэкджек**\n`j.blackjack [ставка]` - игра против дилера\n⏰ КД: 5 минут")
        return
    can, wait = check_cooldown(ctx.author.id, "blackjack")
    if not can:
        await ctx.send(f"❌ КД! Подождите {wait} секунд")
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

    def hand_value(hand):
        value, aces = 0, 0
        for card in hand:
            rank = card[:-2] if len(card) > 2 else card[:-1]
            if rank in ['J', 'Q', 'K']:
                value += 10
            elif rank == 'A':
                aces += 1
                value += 11
            else:
                value += int(rank)
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value

    msg = await ctx.send(f"🃏 **БЛЭКДЖЕК** | Ставка: {bet} 💎\n\nВаши карты: {' '.join(player)} ({hand_value(player)})\nКарты дилера: {dealer[0]} ?")

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
            pv = hand_value(player)
            if pv > 21:
                await interaction.response.edit_message(content=f"🃏 **БЛЭКДЖЕК**\n\nВаши карты: {' '.join(player)} ({pv})\nКарты дилера: {' '.join(dealer)} ({hand_value(dealer)})\n\n💔 **ПЕРЕБОР!** Вы проиграли!", view=None)
                self.ended = True
                set_cooldown(ctx.author.id, "blackjack")
                return
            await interaction.response.edit_message(content=f"🃏 **БЛЭКДЖЕК**\n\nВаши карты: {' '.join(player)} ({pv})\nКарты дилера: {dealer[0]} ?")

        @discord.ui.button(label="Стоп", style=discord.ButtonStyle.success)
        async def stand(self, interaction, button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Не ваша игра!", ephemeral=True)
                return
            pv = hand_value(player)
            dv = hand_value(dealer)
            while dv < 17:
                dealer.append(deck.pop())
                dv = hand_value(dealer)
            win = random.random() < WIN_CHANCE["blackjack"]
            set_cooldown(ctx.author.id, "blackjack")
            if dv > 21 or (pv > dv and win):
                win_amount = bet * 2
                await add_balance(ctx.author.id, ctx.guild.id, win_amount)
                await interaction.response.edit_message(content=f"🃏 **БЛЭКДЖЕК**\n\nВаши карты: {' '.join(player)} ({pv})\nКарты дилера: {' '.join(dealer)} ({dv})\n\n🎉 **ВЫИГРЫШ!** +{win_amount} 💎", view=None)
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
async def ttt(ctx, opponent: discord.Member = None, bet: int = None):
    if opponent is None or bet is None:
        await ctx.send("❌ **Крестики-нолики**\n`j.ttt @user [ставка]`")
        return
    if ctx.author == opponent:
        await ctx.send("❌ Нельзя с собой")
        return
    if bet < 10:
        await ctx.send("❌ Мин. ставка 10 💎")
        return
    bal1 = (await get_user(ctx.author.id, ctx.guild.id))[4]
    bal2 = (await get_user(opponent.id, ctx.guild.id))[4]
    if bal1 < bet or bal2 < bet:
        await ctx.send("❌ У кого-то не хватает")
        return
    embed = discord.Embed(title="🎮 Приглашение", description=f"{opponent.mention}, игра на {bet} 💎? ✅ / ❌", color=discord.Color.purple())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return user.id == opponent.id and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60, check=check)
        await msg.delete()
        if str(reaction.emoji) == "✅":
            ttt_games[ctx.channel.id] = {"p1": ctx.author.id, "p2": opponent.id, "bet": bet, "board": ["⬜"] * 9, "turn": ctx.author.id, "symbols": {ctx.author.id: "❌", opponent.id: "⭕"}, "msg": None}
            await draw_board(ctx)
            await ctx.send(f"🎮 Игра началась! Ставка {bet} 💎. Ход {ctx.author.mention} (❌). `j.hod 1-9`")
        else:
            await ctx.send(f"❌ {opponent.mention} отказался")
    except asyncio.TimeoutError:
        await msg.delete()
        await ctx.send(f"⏰ {opponent.mention} не ответил")


async def draw_board(ctx):
    game = ttt_games.get(ctx.channel.id)
    if not game: return
    board = game["board"]
    display = "\n".join([" ".join(board[i:i + 3]) for i in range(0, 9, 3)])
    current = await bot.fetch_user(game["turn"])
    embed = discord.Embed(title="❌⭕ Крестики-нолики", description=f"Ставка: {game['bet']} 💎\n```\n{display}\n```\nХодит: {current.mention}", color=discord.Color.purple())
    if game["msg"]:
        try:
            old = await ctx.channel.fetch_message(game["msg"])
            await old.edit(embed=embed)
        except:
            game["msg"] = (await ctx.send(embed=embed)).id
    else:
        game["msg"] = (await ctx.send(embed=embed)).id


def ttt_winner(board):
    wins = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for w in wins:
        if board[w[0]] == board[w[1]] == board[w[2]] and board[w[0]] != "⬜":
            return board[w[0]]
    return None


@bot.command()
async def hod(ctx, pos: int = None):
    if pos is None:
        await ctx.send("❌ `j.hod [1-9]`\n1 2 3\n4 5 6\n7 8 9")
        return
    game = ttt_games.get(ctx.channel.id)
    if not game:
        await ctx.send("❌ Нет игры. Создайте: `j.ttt @user 100`")
        return
    if ctx.author.id not in [game["p1"], game["p2"]]:
        await ctx.send("❌ Вы не игрок")
        return
    if game["turn"] != ctx.author.id:
        await ctx.send("❌ Не ваш ход")
        return
    if pos < 1 or pos > 9:
        await ctx.send("❌ 1-9")
        return
    idx = pos - 1
    if game["board"][idx] != "⬜":
        await ctx.send("❌ Занято")
        return
    game["board"][idx] = game["symbols"][ctx.author.id]
    winner = ttt_winner(game["board"])
    if winner:
        winner_id = game["p1"] if winner == "❌" else game["p2"]
        loser_id = game["p2"] if winner == "❌" else game["p1"]
        prize = game["bet"] * 2
        await add_balance(winner_id, ctx.guild.id, prize)
        await add_balance(loser_id, ctx.guild.id, -game["bet"])
        winner_user = await bot.fetch_user(winner_id)
        await draw_board(ctx)
        await ctx.send(f"🎉 {winner_user.mention} победил! Выигрыш: {prize} 💎")
        del ttt_games[ctx.channel.id]
        return
    if "⬜" not in game["board"]:
        await draw_board(ctx)
        await ctx.send("🤝 Ничья! Ставки возвращены")
        del ttt_games[ctx.channel.id]
        return
    game["turn"] = game["p1"] if game["turn"] == game["p2"] else game["p2"]
    await draw_board(ctx)


# ========== ТОПЫ ==========
@bot.command()
async def top(ctx, category: str = "messages", period: str = "всего"):
    if category == "messages":
        async with aiosqlite.connect("justice.db") as db:
            if period == "день":
                cur = await db.execute('SELECT user_id, today_messages FROM users WHERE guild_id=? AND today_messages > 0 ORDER BY today_messages DESC LIMIT 10', (ctx.guild.id,))
            elif period == "неделя":
                cur = await db.execute('SELECT user_id, week_messages FROM users WHERE guild_id=? AND week_messages > 0 ORDER BY week_messages DESC LIMIT 10', (ctx.guild.id,))
            elif period == "месяц":
                cur = await db.execute('SELECT user_id, month_messages FROM users WHERE guild_id=? AND month_messages > 0 ORDER BY month_messages DESC LIMIT 10', (ctx.guild.id,))
            else:
                cur = await db.execute('SELECT user_id, total_messages FROM users WHERE guild_id=? AND total_messages > 0 ORDER BY total_messages DESC LIMIT 10', (ctx.guild.id,))
            rows = await cur.fetchall()
        if not rows:
            await ctx.send("📊 Нет данных")
            return
        period_name = {"день": "сегодня", "неделя": "за неделю", "месяц": "за месяц", "всего": "за всё время"}.get(period, "за всё время")
        msg = f"**🏆 ТОП ПО СООБЩЕНИЯМ {period_name.upper()}**\n"
        for i, (uid, count) in enumerate(rows, 1):
            user = await bot.fetch_user(uid)
            if user:
                msg += f"{i}. {user.name} – {count} сообщ.\n"
        await ctx.send(msg)
    elif category == "reps":
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT user_id, reputation FROM users WHERE guild_id=? ORDER BY reputation DESC LIMIT 10', (ctx.guild.id,))
            rows = await cur.fetchall()
        if not rows:
            await ctx.send("📊 Нет данных")
            return
        msg = f"**🏆 ТОП ПО РЕПУТАЦИИ**\n"
        for i, (uid, rep) in enumerate(rows, 1):
            user = await bot.fetch_user(uid)
            if user:
                msg += f"{i}. {user.name} – {rep} ⭐\n"
        await ctx.send(msg)
    elif category == "balance":
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT user_id, balance FROM users WHERE guild_id=? ORDER BY balance DESC LIMIT 10', (ctx.guild.id,))
            rows = await cur.fetchall()
        if not rows:
            await ctx.send("📊 Нет данных")
            return
        msg = f"**🏆 ТОП ПО БАЛАНСУ**\n"
        for i, (uid, bal) in enumerate(rows, 1):
            user = await bot.fetch_user(uid)
            if user:
                msg += f"{i}. {user.name} – {bal} 💎\n"
        await ctx.send(msg)
    elif category == "level":
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT user_id, level, xp FROM users WHERE guild_id=? ORDER BY level DESC, xp DESC LIMIT 10', (ctx.guild.id,))
            rows = await cur.fetchall()
        if not rows:
            await ctx.send("📊 Нет данных")
            return
        msg = f"**🏆 ТОП ПО УРОВНЮ**\n"
        for i, (uid, lvl, xp) in enumerate(rows, 1):
            user = await bot.fetch_user(uid)
            if user:
                msg += f"{i}. {user.name} – {lvl} ур. ({xp} XP)\n"
        await ctx.send(msg)
    else:
        await ctx.send("❌ Доступные категории: messages, reps, balance, level")


# ========== ИНФОРМАЦИОННЫЕ КОМАНДЫ ==========
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = await get_user(target.id, ctx.guild.id)
    embed = discord.Embed(title=f"👤 Информация о {target.display_name}", color=discord.Color.blue())
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.add_field(name="ID", value=target.id, inline=True)
    embed.add_field(name="Уровень", value=data[3], inline=True)
    embed.add_field(name="Репутация", value=data[6] if len(data) > 6 else 0, inline=True)
    embed.add_field(name="Аккаунт создан", value=target.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="Присоединился", value=target.joined_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="Роли", value=", ".join([r.mention for r in target.roles[1:10]]), inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 Информация о сервере {guild.name}", color=discord.Color.blue())
    embed.add_field(name="👑 Владелец", value=guild.owner.mention, inline=True)
    embed.add_field(name="👥 Участников", value=guild.member_count, inline=True)
    embed.add_field(name="💬 Каналов", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Ролей", value=len(guild.roles), inline=True)
    embed.add_field(name="📅 Создан", value=guild.created_at.strftime("%d.%m.%Y"), inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)


@bot.command()
async def avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    embed = discord.Embed(title=f"🖼️ Аватар {target.display_name}", color=discord.Color.blue())
    embed.set_image(url=target.avatar.url if target.avatar else target.default_avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Понг! Задержка: **{latency} мс**")


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
    target = member or ctx.author
    invites = await ctx.guild.invites()
    count = 0
    for invite in invites:
        if invite.inviter == target:
            count += invite.uses
    await ctx.send(f"📨 {target.mention} пригласил **{count}** участников!")


@bot.command()
async def reminder(ctx, time_str: str = None, *, text: str = None):
    if time_str is None or text is None:
        await ctx.send("⏰ **Напоминание**\n`j.reminder 10м Написать отчёт` - напомнить через 10 минут\nДоступно: м, ч, д")
        return
    time_units = {"м": 60, "ч": 3600, "д": 86400}
    unit = time_str[-1]
    if unit not in time_units:
        await ctx.send("❌ Используйте: 10м, 1ч, 1д")
        return
    try:
        value = int(time_str[:-1])
        seconds = value * time_units[unit]
    except:
        await ctx.send("❌ Неверный формат времени")
        return
    await ctx.send(f"✅ Напоминание установлено! Я напомню через {time_str}")
    await asyncio.sleep(seconds)
    await ctx.author.send(f"⏰ **НАПОМИНАНИЕ!**\nВы просили напомнить: {text}")


# ========== ЦВЕТНЫЕ РОЛИ ==========
async def create_color_message():
    global color_message_id
    channel = bot.get_channel(COLOR_ROLE_CHANNEL_ID)
    if not channel:
        print(f"❌ Канал для цветных ролей {COLOR_ROLE_CHANNEL_ID} не найден!")
        return
    
    async for msg in channel.history(limit=20):
        if msg.author == bot.user:
            await msg.delete()
    
    desc = "**👇 Нажми на реакцию – получишь цветную роль!**\n\n"
    for emoji, data in COLOR_ROLES.items():
        role = channel.guild.get_role(data["id"])
        if role:
            desc += f"{emoji} - {role.mention}\n"
    desc += "\n⚠️ **Чтобы убрать роль – сними реакцию.**"
    embed = discord.Embed(title="🎨 Выбери свой цвет!", description=desc, color=discord.Color.blue())
    msg = await channel.send(embed=embed)
    for emoji in COLOR_ROLES:
        await msg.add_reaction(emoji)
    color_message_id = msg.id
    print(f"✅ Сообщение с цветными ролями отправлено в канал {channel.mention}")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id or payload.channel_id != COLOR_ROLE_CHANNEL_ID:
        return
    guild = bot.get_guild(payload.guild_id)
    if not guild: return
    member = guild.get_member(payload.user_id)
    if not member: return
    emoji = str(payload.emoji.name) if hasattr(payload.emoji, 'name') else None
    if emoji not in COLOR_ROLES: return
    role_id = COLOR_ROLES[emoji]["id"]
    role = guild.get_role(role_id)
    if not role: return
    for r in COLOR_ROLES.values():
        old_role = guild.get_role(r["id"])
        if old_role and old_role in member.roles:
            await member.remove_roles(old_role)
    await member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != COLOR_ROLE_CHANNEL_ID:
        return
    guild = bot.get_guild(payload.guild_id)
    if not guild: return
    member = guild.get_member(payload.user_id)
    if not member: return
    emoji = str(payload.emoji.name) if hasattr(payload.emoji, 'name') else None
    if emoji not in COLOR_ROLES: return
    role_id = COLOR_ROLES[emoji]["id"]
    role = guild.get_role(role_id)
    if role and role in member.roles:
        await member.remove_roles(role)


# ========== ТИКЕТЫ ==========
# ========== УЛУЧШЕННАЯ СИСТЕМА ТИКЕТОВ С ПРИНЯТИЕМ И ЛОГАМИ ==========

class AcceptTicketButton(Button):
    def __init__(self, channel_id, creator_id):
        super().__init__(label="✅ Принять тикет", style=discord.ButtonStyle.success, emoji="✅")
        self.channel_id = channel_id
        self.creator_id = creator_id

    async def callback(self, interaction: discord.Interaction):
        # Проверяем, что пользователь имеет роль поддержки
        is_support = False
        for role_id in SUPPORT_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role and role in interaction.user.roles:
                is_support = True
                break
        
        if not is_support:
            await interaction.response.send_message("❌ Только поддержка может принимать тикеты!", ephemeral=True)
            return
        
        channel = bot.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
            return
        
        # Обновляем название канала
        old_name = channel.name
        new_name = f"принят-{old_name.replace('тикет-', '')}" if old_name.startswith("тикет-") else f"принят-{old_name}"
        await channel.edit(name=new_name)
        
        # Обновляем тему канала
        old_topic = channel.topic or ""
        await channel.edit(topic=f"{old_topic}\nПринят: {interaction.user.name} (ID: {interaction.user.id}) | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Отправляем сообщение о принятии
        embed = discord.Embed(
            title="✅ ТИКЕТ ПРИНЯТ",
            description=f"Тикет принят **{interaction.user.mention}**\n\n"
                        f"Ответственный: {interaction.user.mention}\n"
                        f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                        f"Пожалуйста, опишите проблему подробно, если ещё не сделали этого.",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
        
        # Отключаем кнопку принятия (убираем старый view)
        try:
            old_msg = await channel.fetch_message(interaction.message.id)
            await old_msg.edit(view=None)
        except:
            pass
        
        await interaction.response.send_message("✅ Тикет принят!", ephemeral=True)
        
        # Логируем в канал логов
        log_embed = discord.Embed(
            title="🎫 Тикет принят",
            description=f"Канал: {channel.mention}\nПринял: {interaction.user.mention}\nСоздатель: <@{self.creator_id}>",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        await send_log(interaction.guild.id, log_embed)


class CloseTicketWithLogsButton(Button):
    def __init__(self, channel_id, creator_id):
        super().__init__(label="🔒 Закрыть тикет", style=discord.ButtonStyle.danger, emoji="🔒")
        self.channel_id = channel_id
        self.creator_id = creator_id

    async def callback(self, interaction: discord.Interaction):
        # Проверяем права
        is_support = False
        for role_id in SUPPORT_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role and role in interaction.user.roles:
                is_support = True
                break
        is_creator = interaction.user.id == self.creator_id
        
        if not (is_support or is_creator):
            await interaction.response.send_message("❌ Только создатель тикета или поддержка могут закрыть тикет!", ephemeral=True)
            return
        
        # Собираем историю тикета
        channel = bot.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
            return
        
        await interaction.response.send_message("⏳ Сбор истории тикета...")
        
        # Собираем все сообщения из канала
        messages = []
        async for msg in channel.history(limit=500, oldest_first=True):
            timestamp = msg.created_at.strftime('%d.%m.%Y %H:%M:%S')
            author = f"{msg.author.name}#{msg.author.discriminator}" if msg.author.discriminator != '0' else msg.author.name
            content = msg.content if msg.content else "[Вложение или embed]"
            messages.append(f"[{timestamp}] {author}: {content}")
        
        # Сохраняем историю в файл
        log_dir = "ticket_logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_filename = f"{log_dir}/ticket_{channel.name}_{now}.txt"
        
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(f"=== ИСТОРИЯ ТИКЕТА ===\n")
            f.write(f"Канал: {channel.name}\n")
            f.write(f"Создатель: {self.creator_id}\n")
            f.write(f"Закрыт: {interaction.user.name} (ID: {interaction.user.id})\n")
            f.write(f"Дата закрытия: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            f.write(f"Всего сообщений: {len(messages)}\n")
            f.write(f"\n=== СООБЩЕНИЯ ===\n\n")
            f.write("\n".join(messages))
        
        # Отправляем лог в канал для логов
        log_channel = bot.get_channel(LOGS_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="📋 ЗАКРЫТИЕ ТИКЕТА",
                description=f"**Канал:** {channel.mention}\n**Закрыл:** {interaction.user.mention}\n**Создатель:** <@{self.creator_id}>\n**Всего сообщений:** {len(messages)}",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            await log_channel.send(embed=embed)
            await log_channel.send(file=discord.File(log_filename))
        
        # Удаляем канал через 5 секунд
        embed = discord.Embed(
            title="🔒 Закрытие тикета",
            description="Тикет будет закрыт через 5 секунд...\nИстория сохранена в логах.",
            color=discord.Color.orange()
        )
        await interaction.edit_original_response(content=None, embed=embed, view=None)
        
        await asyncio.sleep(5)
        
        if self.channel_id in active_tickets:
            del active_tickets[self.channel_id]
        await channel.delete()
        
        # Удаляем файл лога (он уже отправлен)
        try:
            os.remove(log_filename)
        except:
            pass


class TicketButtonWithAccept(Button):
    def __init__(self):
        super().__init__(label="🎫 Создать тикет", style=discord.ButtonStyle.primary, emoji="🎫")

    async def callback(self, interaction: discord.Interaction):
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            await interaction.response.send_message("❌ Категория для тикетов не найдена!", ephemeral=True)
            return
        
        for channel in category.channels:
            if channel.topic and str(interaction.user.id) in channel.topic:
                await interaction.response.send_message("❌ У вас уже есть открытый тикет!", ephemeral=True)
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
            topic=f"Создатель: {interaction.user.id} | Создан: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        active_tickets[channel.id] = {"creator": interaction.user.id, "channel": channel}
        
        embed = discord.Embed(
            title="🎫 Тикет создан",
            description=f"{interaction.user.mention}, опишите вашу проблему.\nПоддержка ответит в ближайшее время.\n\n"
                        f"**Инструкция:**\n"
                        f"1. Опишите проблему подробно\n"
                        f"2. Приложите доказательства (скриншоты)\n"
                        f"3. Дождитесь ответа поддержки\n\n"
                        f"*История тикета будет сохранена после закрытия.*",
            color=discord.Color.green()
        )
        
        # Кнопки: принять и закрыть
        view = View()
        view.add_item(AcceptTicketButton(channel.id, interaction.user.id))
        view.add_item(CloseTicketWithLogsButton(channel.id, interaction.user.id))
        
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Тикет создан! Перейдите в {channel.mention}", ephemeral=True)


# Обновлённая функция настройки тикетов
async def setup_ticket_system():
    channel = bot.get_channel(TICKET_CREATE_CHANNEL_ID)
    if not channel:
        print(f"❌ Канал для тикетов {TICKET_CREATE_CHANNEL_ID} не найден!")
        return
    
    async for msg in channel.history(limit=30):
        if msg.author == bot.user:
            await msg.delete()
    
    rules_embed = discord.Embed(
        title="📜 **ПРАВИЛА ТИКЕТОВ**",
        color=discord.Color.gold(),
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    rules_embed.add_field(name="**1.**", value="Не открывать тикеты по абсурдной причине.", inline=False)
    rules_embed.add_field(name="**2.**", value="Если тикет уже принят модератором, то строго запрещается влезать в этот тикет.", inline=False)
    rules_embed.add_field(name="**3.**", value="Если принявший тикет модератор не отвечает в течении **20 минут**, то влезать в тикет разрешается всем выше и ниже стоящим админам.", inline=False)
    rules_embed.add_field(name="**4.**", value="В тикетах должна быть описана сама проблема.", inline=False)
    rules_embed.add_field(name="**5.**", value="История всех тикетов сохраняется и может быть проверена главным администратором.", inline=False)
    rules_embed.set_footer(text="Нажимая на кнопку, вы соглашаетесь с правилами")
    await channel.send(embed=rules_embed)
    
    main_embed = discord.Embed(
        title="🎫 **ТИКЕТЫ ПОДДЕРЖКИ**",
        description="Нажмите на кнопку ниже, чтобы создать тикет.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "📌 **Как это работает:**\n"
                    "• Нажмите на кнопку \"Создать тикет\"\n"
                    "• Опишите проблему\n"
                    "• Модератор примет тикет и ответит\n"
                    "• После решения — тикет закрывается\n"
                    "• **История тикета сохраняется в логах**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=discord.Color.blue()
    )
    view = View()
    view.add_item(TicketButtonWithAccept())
    await channel.send(embed=main_embed, view=view)
    print(f"✅ Система тикетов отправлена в канал {channel.mention}")


@bot.command()
@commands.has_permissions(administrator=True)
async def ticket_history(ctx, ticket_channel: discord.TextChannel = None):
    """📋 Показать историю тикета (только для админов)"""
    
    if ticket_channel is None:
        await ctx.send("❌ Укажите канал тикета: `j.ticket_history #канал`")
        return
    
    if not ticket_channel.name.startswith(("тикет-", "принят-")):
        await ctx.send("❌ Это не канал тикета!")
        return
    
    await ctx.send(f"⏳ Сбор истории канала {ticket_channel.mention}...")
    
    messages = []
    async for msg in ticket_channel.history(limit=500, oldest_first=True):
        timestamp = msg.created_at.strftime('%d.%m.%Y %H:%M:%S')
        author = msg.author.name
        content = msg.content if msg.content else "[Вложение или embed]"
        messages.append(f"[{timestamp}] {author}: {content}")
    
    if not messages:
        await ctx.send("📭 Нет сообщений в этом тикете.")
        return
    
    # Создаём файл с историей
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f"ticket_history_{ticket_channel.name}_{now}.txt"
    
    with open(log_filename, 'w', encoding='utf-8') as f:
        f.write(f"=== ИСТОРИЯ ТИКЕТА ===\n")
        f.write(f"Канал: {ticket_channel.name}\n")
        f.write(f"Топик: {ticket_channel.topic or 'Нет'}\n")
        f.write(f"Дата выгрузки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write(f"Всего сообщений: {len(messages)}\n")
        f.write(f"\n=== СООБЩЕНИЯ ===\n\n")
        f.write("\n".join(messages))
    
    await ctx.send(file=discord.File(log_filename))
    os.remove(log_filename)
# ========== ПРИВАТНЫЕ ГОЛОСОВЫЕ ==========
class VCControlPanel(View):
    def __init__(self, channel_id, owner_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.owner_id = owner_id

    @discord.ui.button(label="🔒 Закрыть", style=discord.ButtonStyle.danger)
    async def lock_btn(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        channel = bot.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.response.send_message("🔒 Канал закрыт", ephemeral=True)

    @discord.ui.button(label="🔓 Открыть", style=discord.ButtonStyle.success)
    async def unlock_btn(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        channel = bot.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.response.send_message("🔓 Канал открыт", ephemeral=True)

    @discord.ui.button(label="👥 Лимит", style=discord.ButtonStyle.primary)
    async def limit_btn(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        modal = LimitModal(self.channel_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📝 Название", style=discord.ButtonStyle.primary)
    async def rename_btn(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        modal = RenameModal(self.channel_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🚫 Бан", style=discord.ButtonStyle.danger)
    async def ban_btn(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        modal = BanModal(self.channel_id, self.owner_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🗑 Удалить", style=discord.ButtonStyle.danger)
    async def delete_btn(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Только владелец может управлять каналом", ephemeral=True)
            return
        channel = bot.get_channel(self.channel_id)
        if channel:
            await channel.delete()
            await interaction.response.send_message("🗑 Канал удалён", ephemeral=True)


class LimitModal(Modal):
    def __init__(self, channel_id):
        super().__init__(title="Установить лимит участников")
        self.channel_id = channel_id
        self.limit = TextInput(label="Лимит (1-99)", placeholder="10", required=True)
        self.add_item(self.limit)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.limit.value)
            if limit < 1 or limit > 99:
                await interaction.response.send_message("❌ Лимит от 1 до 99", ephemeral=True)
                return
            channel = bot.get_channel(self.channel_id)
            if channel:
                await channel.edit(user_limit=limit)
                await interaction.response.send_message(f"✅ Лимит участников: {limit}", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Введите число", ephemeral=True)


class RenameModal(Modal):
    def __init__(self, channel_id):
        super().__init__(title="Переименовать канал")
        self.channel_id = channel_id
        self.name = TextInput(label="Новое название", placeholder="Новый канал", required=True)
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(self.channel_id)
        if channel:
            await channel.edit(name=self.name.value)
            await interaction.response.send_message(f"✅ Канал переименован в {self.name.value}", ephemeral=True)


class BanModal(Modal):
    def __init__(self, channel_id, owner_id):
        super().__init__(title="Забанить пользователя в голосовом канале")
        self.channel_id = channel_id
        self.owner_id = owner_id
        self.user_input = TextInput(label="ID пользователя или @упоминание", placeholder="Введите ID или @username", required=True)
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("❌ Канал не найден", ephemeral=True)
            return
        
        user_input = self.user_input.value.strip()
        target_user = None
        
        if user_input.startswith('<@') and user_input.endswith('>'):
            user_id = int(user_input.strip('<@!>'))
            target_user = interaction.guild.get_member(user_id)
        elif user_input.isdigit():
            target_user = interaction.guild.get_member(int(user_input))
        
        if not target_user:
            await interaction.response.send_message("❌ Пользователь не найден", ephemeral=True)
            return
        
        if target_user.id == self.owner_id:
            await interaction.response.send_message("❌ Нельзя забанить владельца канала", ephemeral=True)
            return
        
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT banned_users FROM private_vc WHERE owner_id=?', (self.owner_id,))
            row = await cur.fetchone()
            banned = json.loads(row[0]) if row and row[0] else []
            if target_user.id not in banned:
                banned.append(target_user.id)
                await db.execute('UPDATE private_vc SET banned_users=? WHERE owner_id=?', (json.dumps(banned), self.owner_id))
                await db.commit()
        
        if target_user in channel.members:
            await target_user.move_to(None)
        
        await interaction.response.send_message(f"✅ {target_user.mention} забанен в голосовом канале", ephemeral=True)


# ========== СОБЫТИЯ ==========
@bot.event
async def on_voice_state_update(member, before, after):
    # Огонёк при заходе в голосовой канал
    if after.channel and (not before.channel or before.channel != after.channel):
        await update_voice_streak(member)
    
    # Проверка бана при заходе в приватный канал
    if after.channel and after.channel.id in vc_sessions:
        vc = after.channel
        owner_id = vc_sessions[vc.id]["owner"]
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT banned_users, is_locked, user_limit FROM private_vc WHERE owner_id=?', (owner_id,))
            row = await cur.fetchone()
            if row:
                banned = json.loads(row[0]) if row[0] else []
                is_locked = row[1] or 0
                user_limit = row[2] or 0
                
                if member.id in banned or (is_locked and member.id != owner_id) or (user_limit > 0 and len(vc.members) > user_limit and member.id != owner_id):
                    await member.move_to(None)
                    return

    # Создание приватного канала
    if after.channel and after.channel.id == VC_TRIGGER_CHANNEL_ID:
        category = member.guild.get_channel(VC_CREATE_CATEGORY_ID)
        if category:
            channel_name = f"👤 {member.display_name}"
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(connect=True),
                member: discord.PermissionOverwrite(connect=True, manage_channels=True)
            }
            vc = await category.create_voice_channel(name=channel_name, overwrites=overwrites)
            await member.move_to(vc)
            
            panel = VCControlPanel(vc.id, member.id)
            await vc.send(f"{member.mention}, панель управления вашим голосовым каналом:", view=panel)
            
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('INSERT OR REPLACE INTO private_vc (owner_id, guild_id, channel_name, user_limit, is_locked, banned_users, created_at) VALUES (?,?,?,?,?,?,?)',
                                (member.id, member.guild.id, channel_name, 0, 0, json.dumps([]), datetime.now().isoformat()))
                await db.commit()
            vc_sessions[vc.id] = {"owner": member.id}

    # Автоудаление пустого канала
    if before.channel and before.channel.id in vc_sessions and len(before.channel.members) == 0:
        await asyncio.sleep(10)
        if len(before.channel.members) == 0:
            await before.channel.delete()
            del vc_sessions[before.channel.id]


@bot.event
async def on_message(msg):
    if msg.author.bot:
        return
    
    # Автомодерация
    settings = guild_settings.get(msg.guild.id, {})
    exempt_roles = settings.get("automod_exempt_roles", [])
    is_exempt = False
    for role_id in exempt_roles:
        role = msg.guild.get_role(role_id)
        if role and role in msg.author.roles:
            is_exempt = True
            break
    
    if not is_exempt and settings.get("automod_enabled", True):
        is_spam, reason = await check_spam(msg)
        if is_spam:
            try:
                # Удаляем ВСЕ сообщения спамера за последние секунды
                user_id = msg.author.id
                if user_id in spam_messages_to_delete:
                    for msg_id in spam_messages_to_delete[user_id]:
                        try:
                            del_msg = await msg.channel.fetch_message(msg_id)
                            await del_msg.delete()
                        except:
                            pass
                    spam_messages_to_delete[user_id] = []
                else:
                    await msg.delete()
                
                warning_count = await add_auto_warning(msg.author, reason, msg.channel)
                try:
                    await msg.author.send(f"⚠️ **Автомодерация**\nВаши сообщения в {msg.channel.mention} были удалены.\n📝 Причина: {reason}\n⚠️ Предупреждений: {warning_count}/{ANTISPAM_MAX_WARNINGS}")
                except:
                    pass
                warn_msg = await msg.channel.send(f"⚠️ {msg.author.mention}, ваши сообщения удалены. Причина: **{reason}**")
                await asyncio.sleep(5)
                await warn_msg.delete()
            except:
                pass
            return
    
    # +rep/-rep при ответе
    if msg.reference and msg.content:
        try:
            referenced_msg = await msg.channel.fetch_message(msg.reference.message_id)
            target = referenced_msg.author
            if target != msg.author:
                content_lower = msg.content.lower().strip()
                if content_lower in ["+rep", "+реп", "++", "👍", "спасибо", "+"]:
                    can, wait = check_rep_cooldown(msg.author.id, target.id)
                    if can:
                        set_rep_cooldown(msg.author.id, target.id)
                        new_rep = await add_reputation(target.id, msg.guild.id, 1)
                        await msg.reply(f"👍 +1 репутации {target.mention}! ⭐ Теперь: {new_rep}")
                elif content_lower in ["-rep", "-реп", "--", "👎", "-"]:
                    can, wait = check_rep_cooldown(msg.author.id, target.id)
                    if can:
                        set_rep_cooldown(msg.author.id, target.id)
                        new_rep = await add_reputation(target.id, msg.guild.id, -1)
                        await msg.reply(f"👎 -1 репутации {target.mention}! ⭐ Теперь: {new_rep}")
        except:
            pass
    
    # ИИ на упоминание
    if bot.user in msg.mentions:
        clean_text = msg.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if clean_text:
            async with msg.channel.typing():
                response = await get_ai_response(clean_text, with_web=True)
            await msg.reply(response, mention_author=False)
            return
    
    # Опыт и деньги
    if random.randint(1, 3) == 1:
        xp_gain = random.randint(10, 25)
        level_up, new_level = await add_xp(msg.author.id, msg.guild.id, xp_gain)
        if level_up:
            level_ch = bot.get_channel(LEVEL_CHANNEL_ID)
            if level_ch:
                await level_ch.send(f"🎉 {msg.author.mention} достиг {new_level} уровня!")
            if new_level in LEVEL_ROLES:
                role = msg.guild.get_role(LEVEL_ROLES[new_level])
                if role and role not in msg.author.roles:
                    await msg.author.add_roles(role)
    
    earn = random.randint(MIN_EARN, MAX_EARN)
    await add_balance(msg.author.id, msg.guild.id, earn)
    
    await bot.process_commands(msg)


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


# ========== ЗАПУСК ВИКТОРИНЫ И СТО ЛОТО ==========
# ========== ЗАПУСК ВИКТОРИНЫ И СТО ЛОТО ==========

async def start_quiz():
    """Запуск викторины (первый раз через 2 часа, потом каждые 2 часа)"""
    global quiz_active, quiz_question, quiz_answer, quiz_options, quiz_message_id, quiz_answered_users
    
    # Ждём 2 часа перед ПЕРВЫМ запуском
    await asyncio.sleep(QUIZ_INTERVAL_SECONDS)
    
    while True:
        if quiz_active:
            await asyncio.sleep(60)
            continue
        
        quiz_active = True
        quiz_answered_users = set()
        
        # Запасной вопрос по умолчанию (если ИИ не сработает)
        quiz_question = "Сколько будет 2 + 2?"
        quiz_answer = "B"
        quiz_options = {"A": "3", "B": "4", "C": "5", "D": "6"}
        
        # Пытаемся получить вопрос от ИИ
        try:
            resp = ai_client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты генератор вопросов для викторины. Придумай интересный вопрос с 4 вариантами ответа (A, B, C, D). Верни в формате: ВОПРОС: ... | A: ... | B: ... | C: ... | D: ... | ОТВЕТ: буква (A/B/C/D)"},
                    {"role": "user", "content": "Сгенерируй новый вопрос для викторины. Вопрос должен быть понятным и не слишком сложным."}
                ],
                temperature=0.7,
                max_tokens=300
            )
            response = resp.choices[0].message.content
            lines = response.split("|")
            if len(lines) >= 6:
                quiz_question = lines[0].replace("ВОПРОС:", "").strip()
                quiz_options = {
                    "A": lines[1].replace("A:", "").strip(),
                    "B": lines[2].replace("B:", "").strip(),
                    "C": lines[3].replace("C:", "").strip(),
                    "D": lines[4].replace("D:", "").strip()
                }
                quiz_answer = lines[5].replace("ОТВЕТ:", "").strip().upper()[0]
                # Проверяем, что ответ действительно A/B/C/D
                if quiz_answer not in ["A", "B", "C", "D"]:
                    quiz_answer = "B"
        except Exception as e:
            print(f"Ошибка генерации вопроса для викторины: {e}")
            # Оставляем запасной вопрос
        
        # Отправляем викторину в канал
        channel = bot.get_channel(QUIZ_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="🧠 ВИКТОРИНА!",
                description=f"**{quiz_question}**\n\n"
                            f"A) {quiz_options['A']}\n"
                            f"B) {quiz_options['B']}\n"
                            f"C) {quiz_options['C']}\n"
                            f"D) {quiz_options['D']}\n\n"
                            f"⏰ У вас есть {QUIZ_ANSWER_TIME // 60} минут, чтобы ответить буквой (A/B/C/D)!\n"
                            f"💰 Награда: {QUIZ_REWARD} 💎",
                color=discord.Color.purple()
            )
            await channel.send(embed=embed)
            
            # Ждём ответы
            await asyncio.sleep(QUIZ_ANSWER_TIME)
            
            # Объявляем правильный ответ
            await channel.send(f"⏰ Время вышло! Правильный ответ: **{quiz_answer}) {quiz_options[quiz_answer]}**")
        
        quiz_active = False
        
        # Ждём 2 часа до следующей викторины
        await asyncio.sleep(QUIZ_INTERVAL_SECONDS)
# ========== НАСТРОЙКИ ==========
@bot.command()
@commands.has_permissions(administrator=True)
async def settings(ctx, module: str = None, value: str = None):
    if ctx.guild.id not in guild_settings:
        guild_settings[ctx.guild.id] = {"welcome_channel": None, "log_channel": LOGS_CHANNEL_ID, "level_channel": LEVEL_CHANNEL_ID}
    if module is None:
        embed = discord.Embed(title="⚙️ НАСТРОЙКИ СЕРВЕРА", color=discord.Color.blue())
        embed.add_field(name="Канал приветствий", value=f"<#{guild_settings[ctx.guild.id]['welcome_channel']}>" if guild_settings[ctx.guild.id]['welcome_channel'] else "Не установлен", inline=False)
        embed.add_field(name="Канал логов", value=f"<#{guild_settings[ctx.guild.id]['log_channel']}>" if guild_settings[ctx.guild.id]['log_channel'] else "Не установлен", inline=False)
        embed.add_field(name="Канал уровней", value=f"<#{guild_settings[ctx.guild.id]['level_channel']}>" if guild_settings[ctx.guild.id]['level_channel'] else "Не установлен", inline=False)
        await ctx.send(embed=embed)
        return
    if module == "welcome":
        try:
            channel_id = int(value.strip('<#>'))
            guild_settings[ctx.guild.id]["welcome_channel"] = channel_id
            await ctx.send(f"✅ Канал приветствий установлен: <#{channel_id}>")
        except:
            await ctx.send("❌ Неверный канал")
    elif module == "logs":
        try:
            channel_id = int(value.strip('<#>'))
            guild_settings[ctx.guild.id]["log_channel"] = channel_id
            await ctx.send(f"✅ Канал логов установлен: <#{channel_id}>")
        except:
            await ctx.send("❌ Неверный канал")
    elif module == "levels":
        try:
            channel_id = int(value.strip('<#>'))
            guild_settings[ctx.guild.id]["level_channel"] = channel_id
            await ctx.send(f"✅ Канал уровней установлен: <#{channel_id}>")
        except:
            await ctx.send("❌ Неверный канал")
    else:
        await ctx.send("❌ Доступные модули: welcome, logs, levels")


@bot.command()
@commands.has_permissions(administrator=True)
async def reset_user(ctx, member: discord.Member = None):
    target = member or ctx.author
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('''
            UPDATE users SET 
                xp=0, level=0, balance=100, bank=0, reputation=0,
                warning_count=0, total_messages=0, today_messages=0, 
                week_messages=0, month_messages=0, voice_streak=0, pots=0, crops='[]'
            WHERE user_id=? AND guild_id=?
        ''', (target.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"🔄 Прогресс {target.mention} полностью сброшен!")


# ========== ПОМОЩЬ ==========
@bot.command()
async def help(ctx, command: str = None):
    if command:
        embed = discord.Embed(title=f"📖 Помощь по команде j.{command}", color=discord.Color.blue())
        embed.add_field(name="Описание", value="Подробная информация о команде", inline=False)
        await ctx.send(embed)
        return
    
    embed = discord.Embed(title="🤖 JUSTICE BOT | Все команды", color=discord.Color.blue())
    embed.add_field(name="👤 ПРОФИЛЬ", value="`j.profile`, `j.bio`, `j.balance`, `j.bank`, `j.deposit`, `j.withdraw`, `j.pay`, `j.daily`, `j.weekly`, `j.monthly`, `j.timely`, `j.work`", inline=False)
    embed.add_field(name="🎲 ИГРЫ", value="`j.casino`, `j.slots`, `j.dice`, `j.coinflip`, `j.rps`, `j.blackjack`, `j.ttt`, `j.hod`, `j.poker`, `j.poker_bet`, `j.poker_check`, `j.poker_fold`", inline=False)
    embed.add_field(name="⭐ РЕПУТАЦИЯ", value="`j.rep`, `j.plusrep`, `j.minusrep`\nТакже можно ответить на сообщение: `+rep` или `-rep`", inline=False)
    embed.add_field(name="🔫 ОГРАБЛЕНИЕ", value="`j.rob` (КД 1ч, шанс 5%)", inline=False)
    embed.add_field(name="🏆 ТОПЫ", value="`j.top messages [день/неделя/месяц/всего]`, `j.top reps`, `j.top balance`, `j.top level`", inline=False)
    embed.add_field(name="🌾 ФЕРМА", value="`j.farm`, `j.buy_pot`, `j.buy_seed`, `j.plant`, `j.harvest`, `j.sell_crop`, `j.sell_all_crops`", inline=False)
    embed.add_field(name="🛍️ МАГАЗИН", value="`j.shop`, `j.buy`, `j.use`, `j.inventory`", inline=False)
    embed.add_field(name="🎭 РОЛЕВЫЕ", value="`j.hug`, `j.kiss`, `j.pat`, `j.poke`, `j.slap`, `j.punch`, `j.bite`, `j.cry`, `j.laugh`, `j.smile`, `j.blush`, `j.dance`, `j.celebrate`, `j.airkiss`, `j.handhold`, `j.tickle`, `j.run`, `j.sleep`, `j.shrug`, `j.shy`, `j.sorry`, `j.stare`, `j.wink`", inline=False)
    embed.add_field(name="🛠️ МОДЕРАЦИЯ", value="`j.warn`, `j.warns`, `j.unwarn`, `j.awarn`, `j.mywarns`, `j.mute`, `j.unmute`, `j.timeout`, `j.ban`, `j.kick`, `j.clear`", inline=False)
    embed.add_field(name="🤖 АВТОМОД", value="`j.automod status`, `j.automod enable/disable`, `j.automod words add/remove/list`, `j.automod invites on/off`, `j.automod phishing on/off`, `j.automod exempt add/remove/list`", inline=False)
    embed.add_field(name="🎟️ ТИКЕТЫ", value="`j.ticket_close`, `j.tickets_list`", inline=False)
    embed.add_field(name="🎮 STEAM", value="`j.steam set`, `j.steam profile`, `j.steam games`, `j.steam recent`", inline=False)
    embed.add_field(name="🎰 СТО ЛОТО", value="`j.loto_buy` - купить билет", inline=False)
    embed.add_field(name="🧠 ВИКТОРИНА", value="Каждые 2 часа в канале #викторина", inline=False)
    embed.add_field(name="💡 ИДЕИ", value="`j.suggest`, `j.accept`, `j.deny` (админ)", inline=False)
    embed.add_field(name="🎁 РОЗЫГРЫШИ", value="`j.giveaway create #канал приз кол-во 1д` (админ)", inline=False)
    embed.add_field(name="🎨 ЦВЕТНЫЕ РОЛИ", value=f"<#{COLOR_ROLE_CHANNEL_ID}>", inline=False)
    embed.add_field(name="🤖 ИИ", value="Упомяните бота или используйте `j.ai [вопрос]`", inline=False)
    embed.add_field(name="⚧ ГЕНДЕР", value="`j.gender male/female`", inline=False)
    embed.add_field(name="🛒 АДМИН МАГАЗИН", value="`j.add_shop_item`, `j.remove_shop_item`", inline=False)
    embed.add_field(name="🌤️ ПОГОДА", value="`j.weather <город>` - реальная погода через Яндекс", inline=False)
    embed.set_footer(text="j.help [команда] - подробнее о команде")
    await ctx.send(embed=embed)


# ========== ЗАПУСК БОТА ==========
@bot.event
async def on_ready():
    await init_db()
    await create_color_message()
    await setup_ticket_system()
    
    async def reset_loop():
        while True:
            await asyncio.sleep(60)
            await reset_activity_counters()
    
    bot.loop.create_task(reset_loop())
    
    print(f'✅ Бот {bot.user} запущен!')
    print(f'📊 На серверах: {len(bot.guilds)}')
    print(f'💡 Префикс команд: j.')
    print(f'🎨 Цветные роли отправлены')
    print(f'🎫 Тикеты настроены')
    print(f'🧠 Викторина запущена (каждые 2 часа)')
    print(f'🎰 СТО ЛОТО запущено (ежедневно в 14:00)')
    print('=' * 50)


@bot.event
async def on_member_join(member):
    role = member.guild.get_role(DEFAULT_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass
    settings = guild_settings.get(member.guild.id, {})
    welcome_channel_id = settings.get("welcome_channel", WELCOME_CHANNEL_ID)
    ch = bot.get_channel(welcome_channel_id)
    if ch:
        embed = discord.Embed(title="🎉 Добро пожаловать!", description=f"{member.mention} присоединился!", color=discord.Color.green())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await ch.send(embed=embed)

# ========== ИНДЕКСЫ ==========
@bot.command()
async def check_indexes(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    
    # Выводим все индексы
    result = "**Индексы в твоей БД:**\n"
    for i, value in enumerate(data):
        result += f"`[{i}]` = {value}\n"
    
    # Отправляем в личку, чтобы не засорять чат
    await ctx.author.send(result[:1900])
    await ctx.send("✅ Проверь личные сообщения!")

# ========== РЕЗЕРВНОЕ КОПИРОВАНИЕ БАЗЫ ДАННЫХ ==========

# ========== КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦА (ONLY OWNER) ==========

def is_owner(ctx):
    """Проверка, является ли пользователь владельцем сервера"""
    return ctx.author.id == ctx.guild.owner_id


@bot.command()
@commands.check(is_owner)
async def owner_give(ctx, member: discord.Member, amount: int):
    """👑 Выдать деньги пользователю (только владелец сервера)
    Использование: j.owner_give @user 1000"""
    
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть положительной!")
        return
    
    await add_balance(member.id, ctx.guild.id, amount)
    
    embed = discord.Embed(
        title="👑 ВЫДАЧА СРЕДСТВ (Владелец)",
        description=f"{ctx.author.mention} выдал {amount} 💎 {member.mention}",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
    
    # Лог в канал логов
    log_embed = discord.Embed(
        title="💰 Выдача средств (владелец)",
        description=f"{ctx.author.mention} выдал {amount} 💎 {member.mention}",
        color=discord.Color.green()
    )
    await send_log(ctx.guild.id, log_embed)
    
    # Уведомляем пользователя в ЛС
    try:
        await member.send(f"👑 Владелец сервера выдал вам **{amount}** 💎!")
    except:
        pass


@bot.command()
@commands.check(is_owner)
async def owner_take(ctx, member: discord.Member, amount: int):
    """👑 Забрать деньги у пользователя (только владелец сервера)
    Использование: j.owner_take @user 500"""
    
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть положительной!")
        return
    
    user_data = await get_user(member.id, ctx.guild.id)
    current_balance = user_data[4]
    
    if current_balance < amount:
        await ctx.send(f"❌ У {member.mention} недостаточно средств! Баланс: {current_balance} 💎")
        return
    
    await add_balance(member.id, ctx.guild.id, -amount)
    
    embed = discord.Embed(
        title="👑 ИЗЪЯТИЕ СРЕДСТВ (Владелец)",
        description=f"{ctx.author.mention} забрал {amount} 💎 у {member.mention}",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
    
    # Лог в канал логов
    log_embed = discord.Embed(
        title="💰 Изъятие средств (владелец)",
        description=f"{ctx.author.mention} забрал {amount} 💎 у {member.mention}",
        color=discord.Color.red()
    )
    await send_log(ctx.guild.id, log_embed)
    
    # Уведомляем пользователя в ЛС
    try:
        await member.send(f"👑 Владелец сервера забрал у вас **{amount}** 💎!")
    except:
        pass


@bot.command()
@commands.check(is_owner)
async def owner_set_balance(ctx, member: discord.Member, amount: int):
    """👑 Установить точный баланс пользователя (только владелец)
    Использование: j.owner_set_balance @user 1000"""
    
    if amount < 0:
        await ctx.send("❌ Баланс не может быть отрицательным!")
        return
    
    user_data = await get_user(member.id, ctx.guild.id)
    current_balance = user_data[4]
    difference = amount - current_balance
    
    if difference > 0:
        await add_balance(member.id, ctx.guild.id, difference)
    elif difference < 0:
        await add_balance(member.id, ctx.guild.id, difference)
    
    embed = discord.Embed(
        title="👑 УСТАНОВКА БАЛАНСА (Владелец)",
        description=f"{ctx.author.mention} установил баланс {member.mention} на **{amount}** 💎",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
    
    # Лог в канал логов
    log_embed = discord.Embed(
        title="💰 Установка баланса (владелец)",
        description=f"{member.mention} → {amount} 💎",
        color=discord.Color.blue()
    )
    await send_log(ctx.guild.id, log_embed)
    
    try:
        await member.send(f"👑 Владелец сервера установил ваш баланс на **{amount}** 💎!")
    except:
        pass


@bot.command()
@commands.check(is_owner)
async def owner_reset_user(ctx, member: discord.Member):
    """👑 Полный сброс пользователя (уровень, баланс, опыт) - только владелец
    Использование: j.owner_reset_user @user"""
    
    embed = discord.Embed(
        title="⚠️ ПОДТВЕРЖДЕНИЕ",
        description=f"Вы уверены, что хотите полностью сбросить прогресс {member.mention}?\n\n"
                    f"Будут удалены:\n"
                    f"• Уровень и опыт\n"
                    f"• Баланс и банк\n"
                    f"• Репутация\n"
                    f"• Статистика сообщений\n"
                    f"• Прогресс в ферме\n\n"
                    f"Нажмите ✅ для подтверждения.",
        color=discord.Color.red()
    )
    
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    def check(reaction, user):
        return user.id == ctx.author.id and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id
    
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30, check=check)
        
        if str(reaction.emoji) == "✅":
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('''
                    UPDATE users SET 
                        xp=0, level=0, balance=100, bank=0, reputation=0,
                        warning_count=0, total_messages=0, today_messages=0, 
                        week_messages=0, month_messages=0, voice_streak=0, 
                        pots=0, crops='[]', inventory='[]', awards='[]'
                    WHERE user_id=? AND guild_id=?
                ''', (member.id, ctx.guild.id))
                await db.commit()
            
            await ctx.send(f"✅ Прогресс {member.mention} полностью сброшен!")
            
            log_embed = discord.Embed(
                title="👑 Полный сброс пользователя",
                description=f"{ctx.author.mention} сбросил прогресс {member.mention}",
                color=discord.Color.orange()
            )
            await send_log(ctx.guild.id, log_embed)
            
            try:
                await member.send(f"👑 Владелец сервера полностью сбросил ваш прогресс!")
            except:
                pass
        else:
            await ctx.send("❌ Сброс отменён.")
            
    except asyncio.TimeoutError:
        await ctx.send("⏰ Время вышло. Сброс отменён.")
    
    await msg.delete()


@bot.command()
@commands.check(is_owner)
async def owner_stats(ctx):
    """👑 Показать статистику сервера (только владелец)"""
    
    async with aiosqlite.connect("justice.db") as db:
        # Общее количество пользователей в БД
        cur = await db.execute('SELECT COUNT(DISTINCT user_id) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_users = (await cur.fetchone())[0]
        
        # Общий баланс всех пользователей
        cur = await db.execute('SELECT SUM(balance) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_balance = (await cur.fetchone())[0] or 0
        
        # Общий опыт всех пользователей
        cur = await db.execute('SELECT SUM(xp) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_xp = (await cur.fetchone())[0] or 0
        
        # Всего сообщений
        cur = await db.execute('SELECT SUM(total_messages) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_messages = (await cur.fetchone())[0] or 0
        
        # Всего предупреждений
        cur = await db.execute('SELECT SUM(warning_count) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_warnings = (await cur.fetchone())[0] or 0
    
    embed = discord.Embed(
        title="📊 СТАТИСТИКА СЕРВЕРА",
        description=f"Статистика для **{ctx.guild.name}**",
        color=discord.Color.gold()
    )
    embed.add_field(name="👥 Пользователей в БД", value=f"{total_users}", inline=True)
    embed.add_field(name="💰 Общий баланс", value=f"{total_balance} 💎", inline=True)
    embed.add_field(name="✨ Общий опыт", value=f"{total_xp} XP", inline=True)
    embed.add_field(name="💬 Всего сообщений", value=f"{total_messages}", inline=True)
    embed.add_field(name="⚠️ Всего предупреждений", value=f"{total_warnings}", inline=True)
    embed.set_footer(text=f"Владелец: {ctx.guild.owner.name}")
    
    await ctx.send(embed=embed)

# ========== БЭКАПЫ ЧЕРЕЗ DISCORD (РАБОТАЕТ НА RAILWAY) ==========

@bot.command()
@commands.has_permissions(administrator=True)
async def backup_db(ctx):
    """💾 Создать резервную копию базы данных (только для админов)"""
    await ctx.send("⏳ Создание резервной копии...")
    
    try:
        if os.path.exists("justice.db"):
            # Создаём имя бэкапа с текущей датой
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_name = f"justice_db_backup_{now}.db"
            
            # Копируем файл
            shutil.copy2("justice.db", backup_name)
            
            # Получаем размер файла
            size = os.path.getsize(backup_name)
            size_mb = size / (1024 * 1024)
            
            embed = discord.Embed(
                title="💾 Резервная копия создана!",
                description=f"**Имя файла:** `{backup_name}`\n**Размер:** {size_mb:.2f} MB\n**Дата:** {now}\n\n📥 Используйте `j.download_backup` чтобы скачать",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
            # Удаляем временный файл (он всё равно не сохранится на Railway)
            os.remove(backup_name)
        else:
            await ctx.send("❌ База данных не найдена!")
            
    except Exception as e:
        await ctx.send(f"❌ Ошибка при создании бэкапа: {str(e)[:100]}")


@bot.command()
@commands.has_permissions(administrator=True)
async def download_backup(ctx):
    """📥 Скачать резервную копию базы данных на компьютер"""
    
    if not os.path.exists("justice.db"):
        await ctx.send("❌ База данных не найдена!")
        return
    
    await ctx.send("⏳ Подготовка файла к скачиванию...")
    
    try:
        # Создаём копию с понятным именем
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        temp_backup = f"justice_db_{now}.db"
        shutil.copy2("justice.db", temp_backup)
        
        # Отправляем файл
        await ctx.send(file=discord.File(temp_backup))
        
        # Удаляем временный файл
        os.remove(temp_backup)
        
        embed = discord.Embed(
            title="✅ Резервная копия отправлена!",
            description="Файл сохранён. Храните его в надёжном месте.\n\nДля восстановления используйте `j.upload_backup`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка при скачивании: {str(e)[:100]}")


@bot.command()
@commands.has_permissions(administrator=True)
async def upload_backup(ctx):
    """📤 Восстановить базу данных из резервной копии
    Использование: прикрепите файл .db к сообщению с командой"""
    
    if not ctx.message.attachments:
        await ctx.send("❌ Прикрепите файл с резервной копией (.db) к сообщению!\n\nПример: напишите `j.upload_backup` и прикрепите файл")
        return
    
    attachment = ctx.message.attachments[0]
    
    if not attachment.filename.endswith('.db'):
        await ctx.send("❌ Это не файл базы данных! Нужен файл с расширением `.db`")
        return
    
    # Запрашиваем подтверждение
    embed = discord.Embed(
        title="⚠️ ПОДТВЕРЖДЕНИЕ ВОССТАНОВЛЕНИЯ",
        description=f"Вы уверены, что хотите восстановить базу данных из файла **{attachment.filename}**?\n\n"
                    f"⚠️ **ВНИМАНИЕ!** Текущая база данных будет **ПОЛНОСТЬЮ ЗАМЕНЕНА**!\n\n"
                    f"✅ Нажмите для подтверждения\n"
                    f"❌ Нажмите для отмены",
        color=discord.Color.orange()
    )
    
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    def check(reaction, user):
        return user.id == ctx.author.id and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id
    
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30, check=check)
        
        if str(reaction.emoji) == "✅":
            await ctx.send("⏳ Восстановление базы данных...")
            
            # Сохраняем текущую БД как бэкап на всякий случай
            if os.path.exists("justice.db"):
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                auto_backup = f"justice_db_before_restore_{now}.db"
                shutil.copy2("justice.db", auto_backup)
                await ctx.send(f"📁 Создан бэкап текущей БД: `{auto_backup}` (скачайте его через `j.download_backup`)")
            
            # Скачиваем и сохраняем новый файл
            await attachment.save("justice.db")
            
            embed = discord.Embed(
                title="✅ База данных восстановлена!",
                description="Для применения изменений перезапустите бота.\n\nНа Railway: **Deployments → Redeploy**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        else:
            await ctx.send("❌ Восстановление отменено.")
            
    except asyncio.TimeoutError:
        await ctx.send("⏰ Время вышло. Восстановление отменено.")
    
    await msg.delete()


@bot.command()
@commands.has_permissions(administrator=True)
async def backup_info(ctx):
    """ℹ️ Информация о текущей базе данных"""
    
    if not os.path.exists("justice.db"):
        await ctx.send("❌ База данных не найдена!")
        return
    
    size = os.path.getsize("justice.db")
    size_mb = size / (1024 * 1024)
    modified = datetime.fromtimestamp(os.path.getmtime("justice.db"))
    
    # Подсчитываем количество пользователей в БД
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT COUNT(DISTINCT user_id) FROM users')
        user_count = (await cur.fetchone())[0]
        
        cur = await db.execute('SELECT COUNT(*) FROM warnings')
        warning_count = (await cur.fetchone())[0]
        
        cur = await db.execute('SELECT COUNT(*) FROM suggestions')
        suggestion_count = (await cur.fetchone())[0]
    
    embed = discord.Embed(
        title="📊 ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ",
        color=discord.Color.blue()
    )
    embed.add_field(name="📁 Файл", value="`justice.db`", inline=True)
    embed.add_field(name="📦 Размер", value=f"{size_mb:.2f} MB", inline=True)
    embed.add_field(name="🕐 Изменён", value=modified.strftime("%d.%m.%Y %H:%M:%S"), inline=True)
    embed.add_field(name="👥 Пользователей", value=user_count, inline=True)
    embed.add_field(name="⚠️ Предупреждений", value=warning_count, inline=True)
    embed.add_field(name="💡 Идей", value=suggestion_count, inline=True)
    
    embed.set_footer(text="j.download_backup - скачать | j.upload_backup - восстановить")
    
    await ctx.send(embed=embed)

# ========== ПОМОЩЬ ДЛЯ ВЛАДЕЛЬЦА ==========

def is_owner(ctx):
    """Проверка, является ли пользователь владельцем сервера"""
    return ctx.author.id == ctx.guild.owner_id


@bot.command()
@commands.check(is_owner)
async def admin_help(ctx):
    """👑 Показать все команды для владельца сервера"""
    
    embed = discord.Embed(
        title="👑 КОМАНДЫ ВЛАДЕЛЬЦА СЕРВЕРА",
        description="Только создатель сервера может использовать эти команды",
        color=discord.Color.gold()
    )
    
    # Экономика и модерация
    embed.add_field(
        name="💰 УПРАВЛЕНИЕ ЭКОНОМИКОЙ",
        value=(
            "`j.owner_give @user <сумма>` - выдать деньги\n"
            "`j.owner_take @user <сумма>` - забрать деньги\n"
            "`j.owner_set_balance @user <сумма>` - установить баланс\n"
            "`j.owner_reset_user @user` - полный сброс пользователя"
        ),
        inline=False
    )
    
    # Бэкапы
    embed.add_field(
        name="💾 УПРАВЛЕНИЕ БЭКАПАМИ",
        value=(
            "`j.backup_db` - создать резервную копию\n"
            "`j.download_backup` - скачать БД на компьютер\n"
            "`j.upload_backup` - восстановить БД из файла\n"
            "`j.backup_info` - информация о БД"
        ),
        inline=False
    )
    
    # Автомодерация
    embed.add_field(
        name="🤖 НАСТРОЙКА АВТОМОДЕРАЦИИ",
        value=(
            "`j.automod status` - текущие настройки\n"
            "`j.automod enable/disable` - вкл/выкл автомод\n"
            "`j.automod words add/remove/list` - запрещённые слова\n"
            "`j.automod invites on/off` - реклама серверов\n"
            "`j.automod phishing on/off` - фишинг\n"
            "`j.automod exempt add/remove/list` - исключённые роли"
        ),
        inline=False
    )
    
    # Настройки сервера
    embed.add_field(
        name="⚙️ НАСТРОЙКИ СЕРВЕРА",
        value=(
            "`j.settings` - показать настройки\n"
            "`j.settings welcome #канал` - канал приветствий\n"
            "`j.settings logs #канал` - канал логов\n"
            "`j.settings levels #канал` - канал уровней"
        ),
        inline=False
    )
    
    # Магазин
    embed.add_field(
        name="🛍️ УПРАВЛЕНИЕ МАГАЗИНОМ",
        value=(
            "`j.add_shop_item <название> <цена> <роль_id> [описание]` - добавить товар\n"
            "`j.remove_shop_item <название>` - удалить товар"
        ),
        inline=False
    )
    
    # Тикеты
    embed.add_field(
        name="🎟️ НАСТРОЙКА ТИКЕТОВ",
        value=(
            "`j.ticket_setup <категория> <роль1> [роль2...]` - настроить тикеты\n"
            "`j.ticket_remove_setup` - удалить кнопку тикетов\n"
            "`j.tickets_list` - список активных тикетов"
        ),
        inline=False
    )
    
    # Розыгрыши и идеи
    embed.add_field(
        name="🎁 РОЗЫГРЫШИ И ИДЕИ",
        value=(
            "`j.giveaway create #канал <приз> <кол-во> <1д/1ч/10м>` - создать розыгрыш\n"
            "`j.accept <id> [вердикт]` - принять идею\n"
            "`j.deny <id> [вердикт]` - отклонить идею"
        ),
        inline=False
    )
    
    # Статистика
    embed.add_field(
        name="📊 СТАТИСТИКА",
        value=(
            "`j.owner_stats` - статистика сервера\n"
            "`j.reset_user [@user]` - сброс пользователя (админ)"
        ),
        inline=False
    )
    
    # Команды модерации
    embed.add_field(
        name="🛠️ КОМАНДЫ МОДЕРАЦИИ",
        value=(
            "`j.warn @user [дни] [причина]` - предупреждение\n"
            "`j.warns [@user]` - список варнов\n"
            "`j.unwarn @user <номер>` - снять варн\n"
            "`j.awarn @user <причина>` - ручной варн\n"
            "`j.mywarns` - свои варны\n"
            "`j.mute @user <10м/1ч/1д> [причина]` - мут\n"
            "`j.unmute @user [причина]` - снять мут\n"
            "`j.timeout @user <минуты> [причина]` - таймаут\n"
            "`j.ban @user [время] [причина]` - бан\n"
            "`j.kick @user [причина]` - кик\n"
            "`j.clear <количество>` - очистка чата"
        ),
        inline=False
    )
    
    embed.set_footer(text="👑 Эти команды доступны только владельцу сервера")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def test_quiz(ctx):
    """🧠 Тестовая викторина (только для админов, не влияет на основную)"""
    global quiz_active, quiz_question, quiz_answer, quiz_options, quiz_message_id, quiz_answered_users
    
    # Сохраняем состояние основной викторины
    was_active = quiz_active
    old_question = quiz_question
    old_answer = quiz_answer
    old_options = quiz_options.copy() if quiz_options else {}
    
    # Временно отключаем основную викторину (если она активна)
    quiz_active = True
    
    await ctx.send("🧠 **Генерация тестовой викторины...**")
    
    try:
        # Генерируем вопрос через ИИ
        test_question = "Сколько будет 2 + 2?"
        test_answer = "B"
        test_options = {"A": "3", "B": "4", "C": "5", "D": "6"}
        
        try:
            resp = ai_client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": "Ты генератор вопросов для викторины. Придумай интересный вопрос с 4 вариантами ответа (A, B, C, D). Верни в формате: ВОПРОС: ... | A: ... | B: ... | C: ... | D: ... | ОТВЕТ: буква (A/B/C/D)"},
                    {"role": "user", "content": "Сгенерируй новый вопрос для викторины."}
                ]
            )
            response = resp.choices[0].message.content
            lines = response.split("|")
            if len(lines) >= 6:
                test_question = lines[0].replace("ВОПРОС:", "").strip()
                test_options = {
                    "A": lines[1].replace("A:", "").strip(),
                    "B": lines[2].replace("B:", "").strip(),
                    "C": lines[3].replace("C:", "").strip(),
                    "D": lines[4].replace("D:", "").strip()
                }
                test_answer = lines[5].replace("ОТВЕТ:", "").strip().upper()[0]
        except Exception as e:
            await ctx.send(f"⚠️ ИИ не сгенерировал вопрос, использую запасной. Ошибка: {str(e)[:100]}")
        
        # Отправляем тестовую викторину
        embed = discord.Embed(
            title="🧠 ТЕСТОВАЯ ВИКТОРИНА!",
            description=f"**{test_question}**\n\n"
                        f"A) {test_options['A']}\n"
                        f"B) {test_options['B']}\n"
                        f"C) {test_options['C']}\n"
                        f"D) {test_options['D']}\n\n"
                        f"⏰ У вас есть 60 секунд, чтобы ответить буквой (A/B/C/D)!\n"
                        f"*(тестовый режим, награда не выдаётся)*",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Тестовая викторина | Не влияет на основную")
        
        test_msg = await ctx.send(embed=embed)
        test_question_id = test_msg.id
        
        # Ждём ответы 60 секунд
        await ctx.send("⏳ Ожидание ответов 60 секунд...")
        
        # Собираем ответы
        answers = {}
        
        def quiz_check(m):
            return m.channel.id == ctx.channel.id and m.content.upper() in ["A", "B", "C", "D"]
        
        try:
            while True:
                resp_msg = await bot.wait_for('message', timeout=60.0, check=quiz_check)
                if resp_msg.author.id not in answers:
                    answers[resp_msg.author.id] = resp_msg.content.upper()
                    await ctx.send(f"📝 {resp_msg.author.mention} ответил: **{resp_msg.content.upper()}**")
        except asyncio.TimeoutError:
            pass
        
        # Объявляем результаты
        if not answers:
            await ctx.send("😔 **Никто не ответил на тестовую викторину!**")
        else:
            results = f"**📊 РЕЗУЛЬТАТЫ ТЕСТОВОЙ ВИКТОРИНЫ**\n\n"
            results += f"✅ **Правильный ответ: {test_answer}) {test_options[test_answer]}**\n\n"
            results += "**Ответы участников:**\n"
            
            correct_count = 0
            for user_id, answer in answers.items():
                user = await bot.fetch_user(user_id)
                status = "✅" if answer == test_answer else "❌"
                if answer == test_answer:
                    correct_count += 1
                results += f"{status} {user.name}: {answer}\n"
            
            results += f"\n📊 **Правильных ответов: {correct_count}/{len(answers)}**"
            
            await ctx.send(results)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка при создании тестовой викторины: {str(e)[:200]}")
    
    finally:
        # Восстанавливаем состояние основной викторины
        quiz_active = was_active
        quiz_question = old_question
        quiz_answer = old_answer
        quiz_options = old_options
        quiz_answered_users = set()
        
        await ctx.send("✅ Тестовая викторина завершена. Основная викторина продолжит работу в обычном режиме.")

# ========== ЗАПУСК ФОНОВЫХ ЗАДАЧ ==========
async def start_background_tasks():
    await bot.wait_until_ready()
    asyncio.create_task(start_quiz())
    asyncio.create_task(stoloto_scheduler())

# Запускаем фоновые задачи после готовности бота
@bot.event
async def on_ready():
    await init_db()
    await create_color_message()
    await setup_ticket_system()
    
    async def reset_loop():
        while True:
            await asyncio.sleep(60)
            await reset_activity_counters()
    
    bot.loop.create_task(reset_loop())
    
    # Запускаем фоновые задачи
    bot.loop.create_task(start_quiz())
    bot.loop.create_task(stoloto_scheduler())
    
    print(f'✅ Бот {bot.user} запущен!')
    print(f'📊 На серверах: {len(bot.guilds)}')
    print(f'💡 Префикс команд: j.')
    print(f'🎨 Цветные роли отправлены')
    print(f'🎫 Тикеты настроены')
    print(f'🧠 Викторина запущена (каждые 2 часа)')
    print(f'🎰 СТО ЛОТО запущено (ежедневно в 14:00)')
    print('=' * 50)

if __name__ == "__main__":
    print("🚀 Запуск бота Justice...")
    bot.run(TOKEN)
