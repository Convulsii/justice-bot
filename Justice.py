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
import openmeteo_requests
import requests_cache
from retry_requests import retry
import hashlib

# ========== ИНИЦИАЛИЗАЦИЯ OPEN-METEO ==========
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# ========== ЛОГИРОВАНИЕ ==========
LOG_ACTION_CHANNEL_ID = 0

async def log_action(guild_id, title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now())
    if LOG_ACTION_CHANNEL_ID:
        ch = bot.get_channel(LOG_ACTION_CHANNEL_ID)
        if ch:
            await ch.send(embed=embed)

async def send_log(guild_id, embed):
    ch = bot.get_channel(LOGS_CHANNEL_ID)
    if ch:
        await ch.send(embed=embed)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv('DISCORD_TOKEN')

STEAM_API_KEY = os.getenv('STEAM_API_KEY')
YANDEX_WEATHER_API_KEY = os.getenv('YANDEX_WEATHER_API_KEY')

AI_API_KEY = "rk_live_G15mOokgVTN8hKFBvWVda38wZGOiXkVs"
AI_BASE_URL = "https://api.ranvik.ru/v1"
AI_MODEL = "gpt-5-nano"

# Инициализация AI клиента
ai_client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)

# ID каналов
WELCOME_CHANNEL_ID = 1502637204982206686
LOGS_CHANNEL_ID = 1502637204982206681
LEVEL_CHANNEL_ID = 1502682125730578522
MUTED_ROLE_ID = 0
DEFAULT_ROLE_ID = 1502637204487278744
VC_CREATE_CATEGORY_ID = 1507479787223126036
VC_TRIGGER_CHANNEL_ID = 1507485728739688549
TICKET_CATEGORY_ID = 1507503146744938506
TICKET_CREATE_CHANNEL_ID = 1510991265154601111
STOLOTO_CHANNEL_ID = 1502637205187723433
IDEA_REVIEW_CHANNEL_ID = 1502637204982206679

SUPPORT_ROLE_IDS = [
    1512024218814910524,
    1507478655578673152,
    1502637204537737306,
    1507479670130741368,
    1512520499941605618,
    1502637204537737308,
    1504402262833758228
]
ROLE_GIRL = 1506343912594477247
ROLE_BOY = 1506343782637896011

LEVEL_ROLES = {
    5: 1502637204487278752,
    10: 1502637204487278753,
    25: 1502637204504051712,
    50: 1502637204504051713,
    100: 1502637204504051714
}

START_BALANCE = 5000
MIN_EARN = 50
MAX_EARN = 150
BANK_INTEREST = 0.05

GAME_COOLDOWN = {"casino": 300, "dice": 300, "coin": 300, "rps": 300, "blackjack": 300, "rob": 3600, "work": 3600, "rep": 3600, "hourly": 3600}
WIN_CHANCE = {"casino": 0.35, "coin": 0.45, "dice": 0.16, "rps": 0.33, "blackjack": 0.42, "rob": 0.05}

SLOT_EMOJIS = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎"]
DICE_EMOJIS = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]

STOLOTO_TICKET_PRICE = 500
ANTISPAM_WINDOW_SECONDS = 8
ANTISPAM_MAX_MESSAGES = 5
ANTISPAM_MAX_WARNINGS = 3
ANTISPAM_WARNING_EXPIRE_HOURS = 24

# ========== КОЛОДА ДЛЯ БЛЭКДЖЕКА И ПОКЕРА ==========
FULL_DECK = []
for rank in ['2','3','4','5','6','7','8','9','10','J','Q','K','A']:
    for suit in ['♠️','♥️','♣️','♦️']:
        FULL_DECK.append(rank+suit)

# ========== СЕМЕНА ==========
SEEDS = {
    "пшеница": {"price": 50, "grow_time": 3600, "base_price": 100, "rarity_weights": {"обычное": 70, "редкое": 20, "эпическое": 8, "легендарное": 2}},
    "кукуруза": {"price": 80, "grow_time": 5400, "base_price": 150, "rarity_weights": {"обычное": 65, "редкое": 22, "эпическое": 10, "легендарное": 3}},
    "морковь": {"price": 60, "grow_time": 4500, "base_price": 120, "rarity_weights": {"обычное": 68, "редкое": 20, "эпическое": 9, "легендарное": 3}},
    "картофель": {"price": 70, "grow_time": 4800, "base_price": 130, "rarity_weights": {"обычное": 67, "редкое": 21, "эпическое": 9, "легендарное": 3}},
    "трава": {"price": 40, "grow_time": 3000, "base_price": 80, "rarity_weights": {"обычное": 75, "редкое": 18, "эпическое": 6, "легендарное": 1}},
}
RARITY_MULTIPLIERS = {"обычное": 1.0, "редкое": 2.0, "эпическое": 5.0, "легендарное": 15.0}

# ========== РЫБАЛКА ==========
FISHING_ITEMS = {
    "окунь": {"price": 80, "exp": 15, "emoji": "🐟"},
    "карп": {"price": 100, "exp": 20, "emoji": "🐠"},
    "щука": {"price": 150, "exp": 30, "emoji": "🐡"},
    "осётр": {"price": 500, "exp": 80, "emoji": "🐋"},
    "золотая рыбка": {"price": 1000, "exp": 150, "emoji": "🐠✨"},
    "сом": {"price": 300, "exp": 50, "emoji": "🐟"},
    "форель": {"price": 200, "exp": 40, "emoji": "🐟"},
    "белуга": {"price": 800, "exp": 120, "emoji": "🐋"},
    "сазан": {"price": 400, "exp": 60, "emoji": "🐟"},
    "морской царь": {"price": 5000, "exp": 500, "emoji": "👑🐟"},
}

FISHING_RODS = {
    "простая": {"price": 500, "emoji": "🎣", "multiplier": 1.0},
    "улучшенная": {"price": 2000, "emoji": "🎣⭐", "multiplier": 1.5},
    "золотая": {"price": 10000, "emoji": "🎣✨", "multiplier": 2.0},
}

fishing_cooldowns = {}

# ========== МАГАЗИН ==========
SHOP_ITEMS = {
    "лотерейный билет": {"price": 100, "desc": "🎫 Шанс выиграть до 100000 💎", "type": "lottery"},
    "золотой слиток": {"price": 500, "desc": "🪙 Можно продать за 250 💎", "type": "consumable", "sell_price": 250},
    "бустер x2 опыта": {"price": 5000, "desc": "🔥 x2 опыт на 1 час", "type": "booster", "duration": 3600},
    "бустер x2 денег": {"price": 5000, "desc": "💰 x2 деньги на 1 час", "type": "booster", "duration": 3600},
}

CUSTOM_SHOP_ITEMS = {}

# ========== ПОГОДА ==========
WEATHER_CODES = {
    0: ("☀️ Ясно", 0xFFD700),
    1: ("🌤️ Преимущественно ясно", 0xFFA500),
    2: ("⛅ Переменная облачность", 0x87CEEB),
    3: ("☁️ Пасмурно", 0x808080),
    45: ("🌫️ Туман", 0xA9A9A9),
    51: ("🌧️ Лёгкий дождь", 0x4682B4),
    61: ("🌧️ Дождь", 0x4169E1),
    71: ("❄️ Снег", 0xE0FFFF),
    80: ("🌧️ Ливень", 0x0000CD),
    95: ("⛈️ Гроза", 0x8B008B),
}

# ========== РЕАКЦИИ ==========
REACTION_GIFS = {
    "hug": "https://i.imgur.com/ANJgqUv.gif",
    "kiss": "https://i.imgur.com/K6QJkZR.gif",
    "pat": "https://i.imgur.com/K7eQ9jL.gif",
    "poke": "https://i.imgur.com/MQvVJ9J.gif",
    "slap": "https://i.imgur.com/fpXxQ7K.gif",
    "punch": "https://i.imgur.com/8hYjHkL.gif",
    "bite": "https://i.imgur.com/NQ7JwKM.gif",
    "cry": "https://i.imgur.com/tPZ7qQK.gif",
    "laugh": "https://i.imgur.com/RvG9yXg.gif",
    "smile": "https://i.imgur.com/H9fGxLc.gif",
    "blush": "https://i.imgur.com/Q5Q5gZm.gif",
    "dance": "https://i.imgur.com/JYVq0sS.gif",
    "celebrate": "https://i.imgur.com/QJkH9pL.gif",
    "airkiss": "https://i.imgur.com/5wZJtYc.gif",
    "handhold": "https://i.imgur.com/NQfLxqM.gif",
    "tickle": "https://i.imgur.com/VvTgKpP.gif",
    "run": "https://i.imgur.com/LpY8XcC.gif",
    "sleep": "https://i.imgur.com/yRvJ8Lf.gif",
    "shrug": "https://i.imgur.com/Kp8VJ7X.gif",
    "shy": "https://i.imgur.com/NQ7JwKM.gif",
    "sorry": "https://i.imgur.com/RvG9yXg.gif",
    "stare": "https://i.imgur.com/H9fGxLc.gif",
    "wink": "https://i.imgur.com/Q5Q5gZm.gif",
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='j.', intents=intents)
bot.remove_command('help')

# ========== ХРАНИЛИЩА ==========
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
vc_sessions = {}
user_message_timestamps = defaultdict(list)
user_warnings = defaultdict(list)
user_conversations = defaultdict(list)
spam_messages_to_delete = defaultdict(list)
active_boosters = defaultdict(dict)
profile_colors = defaultdict(int)
hangman_games = {}
short_urls = {}
MAX_CONTEXT_MESSAGES = 10

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КУЛДАУНОВ ==========
def check_cooldown(user_id, command):
    if command not in GAME_COOLDOWN:
        return True, 0
    last = cooldowns[user_id].get(command, 0)
    now = time.time()
    if now - last < GAME_COOLDOWN[command]:
        return False, int(GAME_COOLDOWN[command] - (now - last))
    return True, 0

def set_cooldown(user_id, command):
    cooldowns[user_id][command] = time.time()

def check_rep_cooldown(user_id, target_id):
    key = f"{user_id}_{target_id}"
    last = rep_cooldowns[key].get("last", 0)
    now = time.time()
    if now - last < GAME_COOLDOWN["rep"]:
        return False, int(GAME_COOLDOWN["rep"] - (now - last))
    return True, 0

def set_rep_cooldown(user_id, target_id):
    key = f"{user_id}_{target_id}"
    rep_cooldowns[key]["last"] = time.time()

# ========== БАЗА ДАННЫХ ==========
async def init_db():
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER, guild_id INTEGER,
            xp INTEGER DEFAULT 0, level INTEGER DEFAULT 0,
            balance INTEGER DEFAULT 5000, bank INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 0, join_date TEXT,
            warning_count INTEGER DEFAULT 0, total_messages INTEGER DEFAULT 0,
            last_daily TEXT, last_weekly TEXT, last_monthly TEXT, last_timely TEXT,
            last_work TEXT, color_role_id INTEGER DEFAULT 0,
            description TEXT DEFAULT '', bio TEXT DEFAULT '',
            awards TEXT DEFAULT '[]', inventory TEXT DEFAULT '[]',
            gender TEXT DEFAULT '',
            today_messages INTEGER DEFAULT 0, week_messages INTEGER DEFAULT 0,
            month_messages INTEGER DEFAULT 0, last_message_time TEXT,
            steam_id TEXT DEFAULT '', voice_streak INTEGER DEFAULT 0,
            last_voice_join TEXT, pots INTEGER DEFAULT 0,
            crops TEXT DEFAULT '[]', profile_color INTEGER DEFAULT 0,
            voice_total_seconds INTEGER DEFAULT 0, voice_join_time TEXT,
            total_invites INTEGER DEFAULT 0,
            total_casino_wins INTEGER DEFAULT 0, total_blackjack_wins INTEGER DEFAULT 0,
            total_poker_wins INTEGER DEFAULT 0, total_ttt_wins INTEGER DEFAULT 0,
            total_fish_caught INTEGER DEFAULT 0, total_legendary_fish INTEGER DEFAULT 0,
            total_mythic_fish INTEGER DEFAULT 0, total_harvests INTEGER DEFAULT 0,
            total_plants INTEGER DEFAULT 0, total_work INTEGER DEFAULT 0,
            total_rob_success INTEGER DEFAULT 0, total_daily_streak INTEGER DEFAULT 0,
            total_shop_buys INTEGER DEFAULT 0, total_shop_spent INTEGER DEFAULT 0,
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
            channel_id INTEGER PRIMARY KEY,
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
            date TEXT, winner_id INTEGER, prize INTEGER
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS custom_shop (
            name TEXT PRIMARY KEY,
            price INTEGER, description TEXT, role_id INTEGER
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            welcome_channel INTEGER, log_channel INTEGER,
            levels_channel INTEGER, automod_enabled INTEGER DEFAULT 1,
            automod_bad_words TEXT DEFAULT '[]',
            automod_invites_enabled INTEGER DEFAULT 1,
            automod_phishing_enabled INTEGER DEFAULT 1,
            automod_exempt_roles TEXT DEFAULT '[]'
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS achievements (
            user_id INTEGER, guild_id INTEGER,
            achievement_id TEXT, achieved_at TEXT,
            PRIMARY KEY (user_id, guild_id, achievement_id)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS daily_quests (
            user_id INTEGER, guild_id INTEGER,
            quest_date TEXT,
            quest1_id TEXT, quest1_progress INTEGER, quest1_completed INTEGER,
            quest2_id TEXT, quest2_progress INTEGER, quest2_completed INTEGER,
            quest3_id TEXT, quest3_progress INTEGER, quest3_completed INTEGER,
            PRIMARY KEY (user_id, guild_id, quest_date)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS investments (
            user_id INTEGER, guild_id INTEGER,
            invest_type TEXT, amount INTEGER,
            invest_date TEXT, days INTEGER,
            interest_rate REAL, claimed INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS farm_upgrades (
            user_id INTEGER, guild_id INTEGER,
            upgrade_type TEXT, level INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id, upgrade_type)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS farm_animals (
            user_id INTEGER, guild_id INTEGER,
            animal_type TEXT, count INTEGER DEFAULT 0,
            last_produce TEXT, last_fed TEXT,
            PRIMARY KEY (user_id, guild_id, animal_type)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS recipes (
            user_id INTEGER, guild_id INTEGER,
            recipe_id TEXT, learned INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id, recipe_id)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS invites (
            inviter_id INTEGER, invited_id INTEGER,
            guild_id INTEGER, invite_date TEXT,
            PRIMARY KEY (invited_id, guild_id)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS weekly_stats (
            user_id INTEGER, guild_id INTEGER,
            week_start TEXT,
            messages INTEGER DEFAULT 0,
            voice_minutes INTEGER DEFAULT 0,
            casino_wins INTEGER DEFAULT 0,
            work_count INTEGER DEFAULT 0,
            fish_caught INTEGER DEFAULT 0,
            crops_harvested INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id, week_start)
        )''')
        await db.commit()
    print("✅ База данных готова")

async def get_user(user_id, guild_id):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM users WHERE user_id=? AND guild_id=?', (user_id, guild_id))
        row = await cur.fetchone()
        if not row:
            now = datetime.now().isoformat()
            await db.execute('INSERT INTO users (user_id, guild_id, join_date, balance, today_messages, week_messages, month_messages, total_messages, last_message_time, pots) VALUES (?,?,?,?,?,?,?,?,?,0)', (user_id, guild_id, now, START_BALANCE, 0, 0, 0, 0, now))
            await db.commit()
            return await get_user(user_id, guild_id)
        return row

async def update_user(user_id, guild_id, **kwargs):
    async with aiosqlite.connect("justice.db") as db:
        for key, value in kwargs.items():
            await db.execute(f'UPDATE users SET {key}=? WHERE user_id=? AND guild_id=?', (value, user_id, guild_id))
        await db.commit()

async def add_balance(user_id, guild_id, amount):
    user = await get_user(user_id, guild_id)
    new_bal = user[4] + amount
    await update_user(user_id, guild_id, balance=new_bal)
    return new_bal

async def add_bank(user_id, guild_id, amount):
    user = await get_user(user_id, guild_id)
    new_bank = (user[5] if len(user) > 5 else 0) + amount
    await update_user(user_id, guild_id, bank=new_bank)
    return new_bank

async def add_reputation(user_id, guild_id, amount):
    user = await get_user(user_id, guild_id)
    new_rep = (user[6] if len(user) > 6 else 0) + amount
    await update_user(user_id, guild_id, reputation=new_rep)
    return new_rep

async def add_xp(user_id, guild_id, amount):
    user = await get_user(user_id, guild_id)
    boost_mult = 2 if datetime.now().weekday() in [5, 6] else 1
    if user_id in active_boosters and "exp" in active_boosters[user_id]:
        if time.time() < active_boosters[user_id]["exp"]["end"]:
            boost_mult *= active_boosters[user_id]["exp"]["mult"]
    amount = int(amount * boost_mult)
    new_xp = user[2] + amount
    new_level = int((new_xp / 200) ** 0.55)
    level_up = new_level > user[3]
    await update_user(user_id, guild_id, xp=new_xp, level=new_level, total_messages=user[9]+1, today_messages=user[21]+1, week_messages=user[22]+1, month_messages=user[23]+1, last_message_time=datetime.now().isoformat())
    if level_up:
        for lvl, role_id in LEVEL_ROLES.items():
            if new_level >= lvl:
                role = bot.get_guild(guild_id).get_role(role_id) if bot.get_guild(guild_id) else None
                if role:
                    member = bot.get_guild(guild_id).get_member(user_id) if bot.get_guild(guild_id) else None
                    if member and role not in member.roles:
                        await member.add_roles(role)
        await check_achievement(user_id, guild_id, "level", new_level)
    return level_up, new_level

# ========== ДОСТИЖЕНИЯ ==========
ACHIEVEMENTS = {
    "msg_10": {"name": "📝 Первые шаги", "desc": "Написать 10 сообщений", "reward": 100},
    "msg_50": {"name": "📝 Говорун", "desc": "Написать 50 сообщений", "reward": 500},
    "msg_100": {"name": "📝 Болтун", "desc": "Написать 100 сообщений", "reward": 1000},
    "msg_500": {"name": "📝 Оратор", "desc": "Написать 500 сообщений", "reward": 5000},
    "msg_1000": {"name": "📝 Мастер слова", "desc": "Написать 1000 сообщений", "reward": 10000},
    "msg_5000": {"name": "📝 Легенда чата", "desc": "Написать 5000 сообщений", "reward": 50000},
    "lvl_5": {"name": "🎚️ Новичок", "desc": "Достичь 5 уровня", "reward": 500},
    "lvl_10": {"name": "🎚️ Опытный", "desc": "Достичь 10 уровня", "reward": 1000},
    "lvl_25": {"name": "🎚️ Мастер", "desc": "Достичь 25 уровня", "reward": 5000},
    "lvl_50": {"name": "🎚️ Эксперт", "desc": "Достичь 50 уровня", "reward": 15000},
    "lvl_100": {"name": "🎚️ Гуру", "desc": "Достичь 100 уровня", "reward": 50000},
    "bal_1000": {"name": "💰 Первые деньги", "desc": "Иметь 1000 💎", "reward": 100},
    "bal_10000": {"name": "💰 Состояние", "desc": "Иметь 10000 💎", "reward": 1000},
    "bal_100000": {"name": "💰 Богач", "desc": "Иметь 100000 💎", "reward": 10000},
    "bal_1000000": {"name": "💰 Легенда богатства", "desc": "Иметь 1 млн 💎", "reward": 100000},
    "rep_10": {"name": "⭐ Народный любимчик", "desc": "Иметь 10 репутации", "reward": 500},
    "rep_50": {"name": "⭐ Уважаемый", "desc": "Иметь 50 репутации", "reward": 2500},
    "rep_100": {"name": "⭐ Звезда", "desc": "Иметь 100 репутации", "reward": 10000},
    "rep_500": {"name": "⭐ Кумир", "desc": "Иметь 500 репутации", "reward": 50000},
}

async def check_achievement(user_id, guild_id, ach_type, value):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT achievement_id FROM achievements WHERE user_id=? AND guild_id=?', (user_id, guild_id))
        earned = set(row[0] for row in await cur.fetchall())
    for ach_id, ach_data in ACHIEVEMENTS.items():
        if ach_id in earned: continue
        if ach_type == "messages" and ach_id.startswith("msg_"):
            if value >= int(ach_id.split("_")[1]):
                await add_balance(user_id, guild_id, ach_data["reward"])
                await db.execute('INSERT INTO achievements (user_id, guild_id, achievement_id, achieved_at) VALUES (?,?,?,?)', (user_id, guild_id, ach_id, datetime.now().isoformat()))
                await db.commit()
                user = bot.get_user(user_id)
                if user:
                    await user.send(f"🏆 **ДОСТИЖЕНИЕ!**\n{ach_data['name']}\n💰 +{ach_data['reward']} 💎")
        elif ach_type == "level" and ach_id.startswith("lvl_"):
            if value >= int(ach_id.split("_")[1]):
                await add_balance(user_id, guild_id, ach_data["reward"])
                await db.execute('INSERT INTO achievements (user_id, guild_id, achievement_id, achieved_at) VALUES (?,?,?,?)', (user_id, guild_id, ach_id, datetime.now().isoformat()))
                await db.commit()
                user = bot.get_user(user_id)
                if user:
                    await user.send(f"🏆 **ДОСТИЖЕНИЕ!**\n{ach_data['name']}\n💰 +{ach_data['reward']} 💎")

# ========== ЕЖЕДНЕВНЫЕ ЗАДАНИЯ ==========
DAILY_QUESTS = {
    "msg_10": {"name": "📝 Написать 10 сообщений", "target": 10, "reward": 50, "type": "messages"},
    "msg_25": {"name": "📝 Написать 25 сообщений", "target": 25, "reward": 100, "type": "messages"},
    "casino_win_1": {"name": "🎰 Выиграть в казино", "target": 1, "reward": 150, "type": "casino_win"},
    "work_1": {"name": "💼 Поработать", "target": 1, "reward": 100, "type": "work"},
    "fish_5": {"name": "🎣 Поймать 5 рыб", "target": 5, "reward": 100, "type": "fish"},
    "daily_bonus": {"name": "📅 Забрать ежедневный бонус", "target": 1, "reward": 100, "type": "daily"},
}

async def check_daily_quest(user_id, guild_id, quest_type, progress_add=1):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT quest1_id, quest1_progress, quest1_completed, quest2_id, quest2_progress, quest2_completed, quest3_id, quest3_progress, quest3_completed FROM daily_quests WHERE user_id=? AND guild_id=? AND quest_date=?', (user_id, guild_id, today))
        quests = await cur.fetchone()
        if not quests:
            available = list(DAILY_QUESTS.keys())
            selected = random.sample(available, min(3, len(available)))
            await db.execute('INSERT INTO daily_quests (user_id, guild_id, quest_date, quest1_id, quest2_id, quest3_id) VALUES (?,?,?,?,?,?)', (user_id, guild_id, today, selected[0], selected[1], selected[2]))
            quests = (selected[0], 0, 0, selected[1], 0, 0, selected[2], 0, 0)
        quest_ids = [quests[0], quests[3], quests[6]]
        progresses = [quests[1], quests[4], quests[7]]
        completed = [quests[2], quests[5], quests[8]]
        rewards = 0
        for i, qid in enumerate(quest_ids):
            if completed[i]: continue
            qdata = DAILY_QUESTS.get(qid)
            if not qdata or qdata["type"] != quest_type: continue
            new_progress = progresses[i] + progress_add
            if new_progress >= qdata["target"]:
                new_progress = qdata["target"]
                completed[i] = 1
                rewards += qdata["reward"]
                user = bot.get_user(user_id)
                if user:
                    await user.send(f"✅ **ЗАДАНИЕ ВЫПОЛНЕНО!**\n{qdata['name']}\n💰 +{qdata['reward']} 💎")
            await db.execute(f'UPDATE daily_quests SET quest{i+1}_progress=?, quest{i+1}_completed=? WHERE user_id=? AND guild_id=? AND quest_date=?', (new_progress, completed[i], user_id, guild_id, today))
        if rewards > 0:
            await add_balance(user_id, guild_id, rewards)

# ========== РЕЦЕПТЫ КРАФТА ==========
RECIPES = {
    "золотой слиток": {"name": "🪙 Золотой слиток", "desc": "Слиток золота", "ingredients": {"золотая руда": 5, "уголь": 2}, "result": "золотой слиток", "count": 1, "xp": 50},
    "алмаз": {"name": "💎 Алмаз", "desc": "Драгоценный камень", "ingredients": {"алмазная руда": 3, "золотой слиток": 1}, "result": "алмаз", "count": 1, "xp": 100},
    "золотая монета": {"name": "🪙 Золотая монета", "desc": "Можно продать за 500 💎", "ingredients": {"золотой слиток": 1}, "result": "gold_coin", "count": 5, "xp": 30},
}

# ========== ЖИВОТНЫЕ ==========
FARM_ANIMALS = {
    "курица": {"name": "🐔 Курица", "price": 1000, "produce": "яйцо", "produce_price": 50, "produce_time": 3600, "feed": "пшеница", "feed_amount": 2},
    "корова": {"name": "🐄 Корова", "price": 5000, "produce": "молоко", "produce_price": 200, "produce_time": 7200, "feed": "кукуруза", "feed_amount": 3},
    "овца": {"name": "🐑 Овца", "price": 4000, "produce": "шерсть", "produce_price": 150, "produce_time": 5400, "feed": "трава", "feed_amount": 2},
    "свинья": {"name": "🐷 Свинья", "price": 3000, "produce": "мясо", "produce_price": 100, "produce_time": 7200, "feed": "картофель", "feed_amount": 3},
}

# ========== УЛУЧШЕНИЯ ФЕРМЫ ==========
FARM_UPGRADES = {
    "grow_speed": {"name": "🌱 Скорость роста", "base_cost": 5000, "multiplier": 0.05, "max_level": 10},
    "animal_speed": {"name": "🐄 Скорость животных", "base_cost": 5000, "multiplier": 0.05, "max_level": 10},
    "max_animals": {"name": "🏠 Вместимость", "base_cost": 20000, "multiplier": 2, "max_level": 5},
}

# ========== ИНВЕСТИЦИИ ==========
INVESTMENTS = {
    "надёжный": {"min": 10000, "max": 100000, "days": 7, "rate": 0.05, "name": "🔒 Надёжный"},
    "средний": {"min": 50000, "max": 500000, "days": 14, "rate": 0.08, "name": "📊 Средний"},
    "рисковый": {"min": 100000, "max": 1000000, "days": 30, "rate": 0.12, "name": "⚡ Рисковый"},
}

# ========== ПОГОДА ==========
async def get_weather_data(lat, lon, forecast_days=7):
    params = {"latitude": lat, "longitude": lon, "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "weather_code", "wind_speed_10m"], "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"], "timezone": "auto", "forecast_days": forecast_days}
    try:
        responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
        return responses[0]
    except: return None

@bot.command()
async def weather(ctx, *, city: str = None):
    if not city: return await ctx.send("🌤️ `j.weather Москва`")
    async with aiohttp.ClientSession() as session:
        geo_url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
        headers = {'User-Agent': 'JusticeBot/1.0'}
        try:
            async with session.get(geo_url, headers=headers) as resp:
                data = await resp.json()
                if not data: return await ctx.send(f"❌ Город {city} не найден")
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                city_name = data[0].get('display_name', city).split(',')[0]
        except: return await ctx.send("❌ Ошибка поиска")
    response = await get_weather_data(lat, lon, 7)
    if not response: return await ctx.send("❌ Ошибка погоды")
    daily = response.Daily()
    daily_times = daily.Time()
    daily_weather = daily.Variables(0).ValuesAsNumpy()
    daily_temp_max = daily.Variables(1).ValuesAsNumpy()
    daily_temp_min = daily.Variables(2).ValuesAsNumpy()
    daily_precip = daily.Variables(3).ValuesAsNumpy()
    embed = discord.Embed(title=f"🌤️ ПОГОДА | {city_name}", color=discord.Color.blue())
    forecast_text = ""
    for i in range(min(7, len(daily_times))):
        date = datetime.fromtimestamp(daily_times[i]).strftime("%d.%m")
        icon, _ = WEATHER_CODES.get(int(daily_weather[i]), ("🌡️", 0))
        forecast_text += f"**{date}** {icon} {daily_temp_min[i]:.0f}°…{daily_temp_max[i]:.0f}° | 💧{daily_precip[i]:.1f}мм\n"
    embed.add_field(name="📅 ПРОГНОЗ НА 7 ДНЕЙ", value=forecast_text[:1024], inline=False)
    await ctx.send(embed=embed)

# ========== ИИ ==========
async def get_ai_response(user_id, user_message):
    global user_conversations
    lower_msg = user_message.lower()
    if any(x in lower_msg for x in ["привет", "здравствуй"]): return "👋 Привет!"
    if "как дела" in lower_msg: return "😊 Всё отлично!"
    if "спасибо" in lower_msg: return "🙏 Пожалуйста!"
    conv = user_conversations.get(user_id, [])
    messages = [{"role": "system", "content": f"Ты помощник. Сегодня {datetime.now().strftime('%d.%m.%Y')}. Отвечай кратко."}]
    messages.extend(conv[-MAX_CONTEXT_MESSAGES:])
    messages.append({"role": "user", "content": user_message})
    try:
        resp = await asyncio.wait_for(asyncio.get_event_loop().run_in_executor(None, lambda: ai_client.chat.completions.create(model=AI_MODEL, messages=messages, max_tokens=500)), timeout=10.0)
        answer = resp.choices[0].message.content
        user_conversations[user_id].append({"role": "user", "content": user_message})
        user_conversations[user_id].append({"role": "assistant", "content": answer})
        return answer if answer else "😊 Понял!"
    except: return "⏳ Попробуй ещё раз"

@bot.command()
async def ai(ctx, *, question: str = None):
    if not question: return await ctx.send("❌ j.ai Как дела?")
    msg = await ctx.send("💭 Думаю...")
    async with ctx.typing():
        response = await get_ai_response(ctx.author.id, question)
    await msg.edit(content=response)

# ========== ЭКОНОМИКА ==========
@bot.command()
async def balance(ctx, member: discord.Member = None):
    t = member or ctx.author
    d = await get_user(t.id, ctx.guild.id)
    await ctx.send(f"💰 {t.mention}: {d[4]} 💎 | 🏦 {d[5] if len(d)>5 else 0} 💎")

@bot.command()
async def bank(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    await ctx.send(f"🏦 {ctx.author.mention}: {d[5] if len(d)>5 else 0} 💎 | {BANK_INTEREST*100}% в день")

@bot.command()
async def deposit(ctx, amount: int):
    if amount<10: return await ctx.send("❌ Мин. 10 💎")
    d = await get_user(ctx.author.id, ctx.guild.id)
    if d[4] < amount: return await ctx.send(f"❌ Не хватает ({d[4]} 💎)")
    await add_balance(ctx.author.id, ctx.guild.id, -amount)
    await add_bank(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"🏦 +{amount} 💎 в банк")

@bot.command()
async def withdraw(ctx, amount: int):
    d = await get_user(ctx.author.id, ctx.guild.id)
    bank = d[5] if len(d)>5 else 0
    if bank < amount: return await ctx.send(f"❌ В банке {bank} 💎")
    await add_bank(ctx.author.id, ctx.guild.id, -amount)
    await add_balance(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"🏦 Выведено {amount} 💎")

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    if amount<=0 or member==ctx.author: return await ctx.send("❌ Неверно")
    s = await get_user(ctx.author.id, ctx.guild.id)
    if s[4] < amount: return await ctx.send(f"❌ Не хватает ({s[4]} 💎)")
    await add_balance(ctx.author.id, ctx.guild.id, -amount)
    await add_balance(member.id, ctx.guild.id, amount)
    await ctx.send(f"💸 {ctx.author.mention} перевёл {amount} 💎 {member.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def give(ctx, member: discord.Member, amount: int):
    await add_balance(member.id, ctx.guild.id, amount)
    await ctx.send(f"✅ Выдано {amount} 💎 {member.mention}")

@bot.command()
async def daily(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    last = d[10] if len(d)>10 else None
    if last:
        ld = datetime.fromisoformat(last)
        if (datetime.now()-ld).days < 1:
            rem = 86400 - (datetime.now()-ld).seconds
            return await ctx.send(f"⏰ Через {rem//3600}ч")
    earn = random.randint(500, 1500)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    await update_user(ctx.author.id, ctx.guild.id, last_daily=datetime.now().isoformat())
    await ctx.send(f"🎁 +{earn} 💎")
    await check_daily_quest(ctx.author.id, ctx.guild.id, "daily", 1)

@bot.command()
async def work(ctx):
    can, w = check_cooldown(ctx.author.id, "work")
    if not can: return await ctx.send(f"❌ КД {w//60}мин")
    earn = random.randint(300, 800)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    set_cooldown(ctx.author.id, "work")
    await ctx.send(f"💼 +{earn} 💎")
    await check_daily_quest(ctx.author.id, ctx.guild.id, "work", 1)

@bot.command()
async def rob(ctx, member: discord.Member):
    if member==ctx.author: return await ctx.send("❌ Себя нельзя")
    can, w = check_cooldown(ctx.author.id, "rob")
    if not can: return await ctx.send(f"❌ КД {w//60}мин")
    td = await get_user(member.id, ctx.guild.id)
    if td[4] < 500: return await ctx.send(f"❌ У {member.mention} мало денег")
    success = random.random() < WIN_CHANCE["rob"]
    set_cooldown(ctx.author.id, "rob")
    if success:
        steal = random.randint(100, int(td[4] * 0.3))
        await add_balance(ctx.author.id, ctx.guild.id, steal)
        await add_balance(member.id, ctx.guild.id, -steal)
        await ctx.send(f"🔫 Ограбление удалось! +{steal} 💎")
    else:
        await ctx.send(f"🔫 Не удалось ограбить {member.mention}")

@bot.command()
async def rep(ctx, member: discord.Member = None):
    t = member or ctx.author
    d = await get_user(t.id, ctx.guild.id)
    await ctx.send(f"⭐ {t.mention}: {d[6] if len(d)>6 else 0}")

@bot.command()
async def plusrep(ctx, member: discord.Member):
    if member==ctx.author: return await ctx.send("❌ Себе нельзя")
    can, w = check_rep_cooldown(ctx.author.id, member.id)
    if not can: return await ctx.send(f"❌ КД {w//60}мин")
    set_rep_cooldown(ctx.author.id, member.id)
    nr = await add_reputation(member.id, ctx.guild.id, 1)
    await ctx.send(f"👍 +1 репутации {member.mention}! Теперь {nr}")

# ========== ИГРЫ ==========
@bot.command()
async def casino(ctx, amount: int = None):
    if not amount: return await ctx.send("🎰 j.casino 100")
    can, w = check_cooldown(ctx.author.id, "casino")
    if not can: return await ctx.send(f"⏰ {w}сек")
    if amount<100: return await ctx.send("❌ Мин. 100 💎")
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal<amount: return await ctx.send(f"❌ Не хватает")
    msg = await ctx.send(f"🎰 {ctx.author.mention} крутит...")
    for _ in range(3):
        await asyncio.sleep(0.3)
        await msg.edit(content=f"🎰 {' '.join(random.choices(SLOT_EMOJIS, k=3))}")
    win = random.random() < WIN_CHANCE["casino"]
    set_cooldown(ctx.author.id, "casino")
    if win:
        wa = amount * 2
        await add_balance(ctx.author.id, ctx.guild.id, wa)
        await msg.edit(content=f"🎰 **ВЫИГРЫШ! +{wa} 💎**")
        await check_daily_quest(ctx.author.id, ctx.guild.id, "casino_win", 1)
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await msg.edit(content=f"🎰 **ПРОИГРЫШ! -{amount} 💎**")

@bot.command()
async def slots(ctx, bet: int = None):
    if not bet: return await ctx.send("🎰 j.slots 100")
    can, w = check_cooldown(ctx.author.id, "casino")
    if not can: return await ctx.send(f"⏰ {w}сек")
    if bet<100: return await ctx.send("❌ Мин. 100 💎")
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal<bet: return await ctx.send(f"❌ Не хватает")
    msg = await ctx.send(f"🎰 {ctx.author.mention} крутит...")
    for _ in range(3):
        await asyncio.sleep(0.3)
        await msg.edit(content=f"🎰 {' '.join(random.choices(SLOT_EMOJIS, k=3))}")
    res = random.choices(SLOT_EMOJIS, k=3)
    mul = 10 if res[0]==res[1]==res[2] else 2 if res[0]==res[1] or res[1]==res[2] or res[0]==res[2] else 0
    set_cooldown(ctx.author.id, "casino")
    if mul:
        win = bet * mul
        await add_balance(ctx.author.id, ctx.guild.id, win)
        await msg.edit(content=f"🎰 **{' '.join(res)}**\n🎉 ВЫИГРЫШ! +{win} 💎 (x{mul})")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🎰 **{' '.join(res)}**\n💔 ПРОИГРЫШ! -{bet} 💎")

@bot.command()
async def dice(ctx, num: int = None, bet: int = None):
    if not num or not bet: return await ctx.send("🎲 j.dice 3 100")
    can, w = check_cooldown(ctx.author.id, "dice")
    if not can: return await ctx.send(f"⏰ {w}сек")
    if num<1 or num>6: return await ctx.send("❌ 1-6")
    if bet<100: return await ctx.send("❌ Мин. 100 💎")
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal<bet: return await ctx.send(f"❌ Не хватает")
    msg = await ctx.send(f"🎲 {ctx.author.mention} бросает...")
    await asyncio.sleep(0.5)
    roll = random.randint(1,6)
    set_cooldown(ctx.author.id, "dice")
    if roll == num:
        win = bet * 6
        await add_balance(ctx.author.id, ctx.guild.id, win)
        await msg.edit(content=f"🎲 **{roll}!** УГАДАЛ! +{win} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🎲 **{roll}!** НЕ УГАДАЛ! -{bet} 💎")

@bot.command()
async def blackjack(ctx, bet: int = None):
    if not bet: return await ctx.send("🃏 j.blackjack 100")
    can, w = check_cooldown(ctx.author.id, "blackjack")
    if not can: return await ctx.send(f"⏰ {w}сек")
    if bet<100: return await ctx.send("❌ Мин. 100 💎")
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal<bet: return await ctx.send(f"❌ Не хватает")
    await add_balance(ctx.author.id, ctx.guild.id, -bet)
    deck = FULL_DECK.copy()
    random.shuffle(deck)
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    def hv(h):
        v,a=0,0
        for c in h:
            r=c[:-2] if len(c)>2 else c[:-1]
            if r in ['J','Q','K']: v+=10
            elif r=='A': a+=1; v+=11
            else: v+=int(r)
        while v>21 and a>0: v-=10; a-=1
        return v
    msg = await ctx.send(f"🃏 БЛЭКДЖЕК | Ставка: {bet} 💎\nВаши: {' '.join(player)} ({hv(player)})\nДилер: {dealer[0]} ?")
    class BJView(View):
        def __init__(self):
            super().__init__(timeout=30)
            self.ended=False
        @discord.ui.button(label="Ещё", style=discord.ButtonStyle.primary)
        async def hit(self, i, b):
            if i.user.id!=ctx.author.id: return await i.response.send_message("❌ Не ваша игра!", ephemeral=True)
            player.append(deck.pop())
            pv=hv(player)
            if pv>21:
                await i.response.edit_message(content=f"🃏 **ПЕРЕБОР!**\n-{bet} 💎", view=None)
                self.ended=True
                set_cooldown(ctx.author.id, "blackjack")
                return
            await i.response.edit_message(content=f"🃏 БЛЭКДЖЕК\nВаши: {' '.join(player)} ({pv})\nДилер: {dealer[0]} ?")
        @discord.ui.button(label="Стоп", style=discord.ButtonStyle.success)
        async def stand(self, i, b):
            if i.user.id!=ctx.author.id: return await i.response.send_message("❌ Не ваша игра!", ephemeral=True)
            pv=hv(player); dv=hv(dealer)
            while dv<17: dealer.append(deck.pop()); dv=hv(dealer)
            set_cooldown(ctx.author.id, "blackjack")
            if dv>21 or pv>dv:
                wa=bet*2
                await add_balance(ctx.author.id, ctx.guild.id, wa)
                await i.response.edit_message(content=f"🃏 **ВЫИГРЫШ!**\n+{wa} 💎", view=None)
            elif pv==dv:
                await add_balance(ctx.author.id, ctx.guild.id, bet)
                await i.response.edit_message(content=f"🃏 **НИЧЬЯ!**", view=None)
            else:
                await i.response.edit_message(content=f"🃏 **ПРОИГРЫШ!**", view=None)
            self.ended=True
        async def on_timeout(self):
            if not self.ended:
                await msg.edit(content="⏰ Время вышло! Ставка возвращена", view=None)
                await add_balance(ctx.author.id, ctx.guild.id, bet)
    view = BJView()
    await msg.edit(view=view)

# ========== РЫБАЛКА ==========
class FishingView(View):
    def __init__(self, user_id):
        super().__init__(timeout=5)
        self.user_id = user_id
        self.clicked = False
        self.start = time.time()
    @discord.ui.button(label="🎣 ТЯНУТЬ!", style=discord.ButtonStyle.success)
    async def pull(self, i, b):
        if i.user.id != self.user_id: return await i.response.send_message("❌ Не вы!", ephemeral=True)
        self.clicked = True
        self.reaction_time = time.time() - self.start
        await i.response.edit_message(content=f"✅ {self.reaction_time:.1f} сек!", view=None)
        self.stop()

@bot.command()
async def fish(ctx):
    user_id = ctx.author.id
    now = time.time()
    if now - fishing_cooldowns.get(user_id, 0) < 300:
        remaining = int(300 - (now - fishing_cooldowns.get(user_id, 0)))
        return await ctx.send(f"⏰ Подождите {remaining//60} минут")
    fishing_cooldowns[user_id] = now
    msg = await ctx.send(f"🎣 Заброс...")
    await asyncio.sleep(2)
    fish = random.choice(list(FISHING_ITEMS.keys()))
    fd = FISHING_ITEMS[fish]
    await msg.edit(content=f"🎣 **КЛЮНУЛО!** {fish} {fd['emoji']}\nНАЖМИ КНОПКУ! 5 СЕКУНД")
    view = FishingView(user_id)
    game_msg = await ctx.send("🎣 ТЯНИ!", view=view)
    await view.wait()
    if not view.clicked: return await game_msg.edit(content=f"💔 Леска порвалась! {fish} уплыл!")
    mult = 1.5 if view.reaction_time < 1.5 else 1.2 if view.reaction_time < 3 else 1.0
    price = int(fd["price"] * mult)
    exp = int(fd["exp"] * mult)
    await add_balance(user_id, ctx.guild.id, price)
    await add_xp(user_id, ctx.guild.id, exp)
    embed = discord.Embed(title=f"{fd['emoji']} {fish}!", color=discord.Color.gold())
    embed.add_field(name="💰 Цена", value=f"{price} 💎", inline=True)
    embed.add_field(name="✨ Опыт", value=f"+{exp} XP", inline=True)
    await msg.edit(content=None, embed=embed)
    await check_daily_quest(ctx.author.id, ctx.guild.id, "fish", 1)

@bot.command()
async def sell_all(ctx):
    await ctx.send("✅ Продажа всей рыбы (функция в разработке)")

# ========== ПРОФИЛЬ ==========
@bot.command()
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = await get_user(target.id, ctx.guild.id)
    level, xp, bal = data[3], data[2], data[4]
    bank = data[5] if len(data) > 5 else 0
    rep = data[6] if len(data) > 6 else 0
    total_msgs = data[9] if len(data) > 9 else 0
    embed = discord.Embed(title=f"📊 ПРОФИЛЬ | {target.display_name}", color=discord.Color.blue())
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="🎚️ УРОВЕНЬ", value=f"**{level}** уровень\n✨ {xp} XP", inline=False)
    embed.add_field(name="💰 ЭКОНОМИКА", value=f"💎 {bal} 💎\n🏦 {bank} 💎\n⭐ {rep}", inline=False)
    embed.add_field(name="💬 СТАТИСТИКА", value=f"Сообщений: {total_msgs}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def bio(ctx, *, text: str = None):
    if not text: return await ctx.send("❌ j.bio <текст>")
    if len(text) > 500: return await ctx.send("❌ Максимум 500 символов")
    await update_user(ctx.author.id, ctx.guild.id, bio=text)
    await ctx.send("✅ Био обновлено")

# ========== ТИКЕТЫ ==========
class PersistentTicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Создать тикет", style=discord.ButtonStyle.primary, custom_id="persistent_ticket", emoji="🎫")
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            return await interaction.response.send_message("❌ Категория не найдена!", ephemeral=True)
        for channel in category.channels:
            if channel.topic and str(interaction.user.id) in channel.topic:
                return await interaction.response.send_message("❌ У вас уже есть тикет!", ephemeral=True)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        for rid in SUPPORT_ROLE_IDS:
            role = interaction.guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        num = len([c for c in category.channels if c.name.startswith("тикет-")]) + 1
        channel = await category.create_text_channel(name=f"тикет-{num}", overwrites=overwrites, topic=f"Создатель: {interaction.user.id}")
        active_tickets[channel.id] = {"creator": interaction.user.id}
        embed = discord.Embed(title="🎫 ТИКЕТ СОЗДАН", description=f"{interaction.user.mention}, опишите проблему\n\nДля закрытия используйте кнопку", color=discord.Color.green())
        view = View()
        view.add_item(CloseTicketButton(channel.id, interaction.user.id))
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Тикет создан: {channel.mention}", ephemeral=True)

class CloseTicketButton(Button):
    def __init__(self, channel_id, creator_id):
        super().__init__(label="🔒 Закрыть", style=discord.ButtonStyle.danger, emoji="🔒")
        self.channel_id = channel_id
        self.creator_id = creator_id
    async def callback(self, interaction: discord.Interaction):
        channel = bot.get_channel(self.channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
        is_support = any(interaction.guild.get_role(rid) in interaction.user.roles for rid in SUPPORT_ROLE_IDS if interaction.guild.get_role(rid))
        is_creator = interaction.user.id == self.creator_id
        if not (is_support or is_creator):
            return await interaction.response.send_message("❌ Нет прав!", ephemeral=True)
        await interaction.response.send_message("⏳ Закрытие...", ephemeral=True)
        await channel.delete()
        del active_tickets[channel.id]

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    view = PersistentTicketButton()
    embed = discord.Embed(title="🎫 ТИКЕТЫ", description="Нажми на кнопку для создания тикета", color=discord.Color.blue())
    await ctx.send(embed=embed, view=view)
    await ctx.send("✅ Готово!")

# ========== ПРИВАТНЫЕ ГОЛОСОВЫЕ ==========
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == VC_TRIGGER_CHANNEL_ID:
        cat = member.guild.get_channel(VC_CREATE_CATEGORY_ID)
        if cat:
            existing = [c for c in cat.voice_channels if c.name.startswith("Приватный")]
            num = len(existing) + 1
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(connect=False),
                member: discord.PermissionOverwrite(connect=True, manage_channels=True),
                member.guild.me: discord.PermissionOverwrite(connect=True, manage_channels=True)
            }
            channel = await cat.create_voice_channel(name=f"Приватный #{num}", overwrites=overwrites)
            await member.move_to(channel)
            vc_sessions[channel.id] = {"owner": member.id}
    if before.channel and before.channel.id in vc_sessions and len(before.channel.members) == 0:
        await asyncio.sleep(10)
        if len(before.channel.members) == 0:
            await before.channel.delete()
            del vc_sessions[before.channel.id]

# ========== КРЕСТИКИ-НОЛИКИ ==========
class TicTacToeButton(Button):
    def __init__(self, x, y, p1, p2, bet):
        super().__init__(style=discord.ButtonStyle.secondary, label="⬜", row=y)
        self.x, self.y, self.p1, self.p2, self.bet = x, y, p1, p2, bet
        self.clicked = False
    async def callback(self, i):
        game = ttt_games.get(i.channel.id)
        if not game: return await i.response.send_message("❌ Игра не найдена", ephemeral=True)
        if i.user.id not in [game["p1"], game["p2"]]: return await i.response.send_message("❌ Вы не участник", ephemeral=True)
        if game["turn"] != i.user.id: return await i.response.send_message("❌ Не ваш ход", ephemeral=True)
        if self.clicked: return await i.response.send_message("❌ Занято", ephemeral=True)
        symbol = "❌" if i.user.id == game["p1"] else "⭕"
        self.label, self.style, self.clicked = symbol, discord.ButtonStyle.danger if symbol=="❌" else discord.ButtonStyle.success, True
        game["board"][self.y][self.x] = symbol
        game["turn"] = game["p2"] if game["turn"]==game["p1"] else game["p1"]
        winner = self.check_winner(game["board"])
        if winner:
            prize = game["bet"]*2
            if winner=="❌":
                await add_balance(game["p1"], i.guild.id, prize)
                await add_balance(game["p2"], i.guild.id, -game["bet"])
                winner_mention = f"<@{game['p1']}>"
            elif winner=="⭕":
                await add_balance(game["p2"], i.guild.id, prize)
                await add_balance(game["p1"], i.guild.id, -game["bet"])
                winner_mention = f"<@{game['p2']}>"
            else:
                winner_mention = "Ничья"
                await add_balance(game["p1"], i.guild.id, game["bet"])
                await add_balance(game["p2"], i.guild.id, game["bet"])
            embed = discord.Embed(title="❌⭕ КРЕСТИКИ-НОЛИКИ", color=discord.Color.gold())
            embed.add_field(name="🏆 РЕЗУЛЬТАТ", value=f"{winner_mention} победил!\n💰 Выигрыш: {prize} 💎" if winner!="Ничья" else "Ничья!", inline=False)
            await i.response.edit_message(embed=embed, view=None)
            del ttt_games[i.channel.id]
            return
        view = TicTacToeView(game["p1"], game["p2"], game["bet"], game["board"])
        embed = discord.Embed(title="❌⭕ КРЕСТИКИ-НОЛИКИ", color=discord.Color.blue())
        embed.add_field(name="💰 Ставка", value=f"{game['bet']} 💎", inline=True)
        embed.add_field(name="🎲 Ход", value=f"<@{game['turn']}>", inline=True)
        await i.response.edit_message(embed=embed, view=view)
    def check_winner(self, board):
        for row in board:
            if row[0]==row[1]==row[2] and row[0]!="⬜": return row[0]
        for col in range(3):
            if board[0][col]==board[1][col]==board[2][col] and board[0][col]!="⬜": return board[0][col]
        if board[0][0]==board[1][1]==board[2][2] and board[0][0]!="⬜": return board[0][0]
        if board[0][2]==board[1][1]==board[2][0] and board[0][2]!="⬜": return board[0][2]
        return None

class TicTacToeView(View):
    def __init__(self, p1, p2, bet, board=None):
        super().__init__(timeout=180)
        self.board = board if board else [["⬜","⬜","⬜"] for _ in range(3)]
        for y in range(3):
            for x in range(3):
                btn = TicTacToeButton(x, y, p1, p2, bet)
                if self.board[y][x]!="⬜":
                    btn.label = self.board[y][x]
                    btn.style = discord.ButtonStyle.danger if self.board[y][x]=="❌" else discord.ButtonStyle.success
                    btn.clicked = True
                self.add_item(btn)

@bot.command()
async def ttt(ctx, member: discord.Member = None, bet: int = None):
    if not member or not bet: return await ctx.send("❌ j.ttt @user 100")
    if member==ctx.author: return await ctx.send("❌ Нельзя с собой")
    if bet<100: return await ctx.send("❌ Мин. 100 💎")
    bal1 = (await get_user(ctx.author.id, ctx.guild.id))[4]
    bal2 = (await get_user(member.id, ctx.guild.id))[4]
    if bal1<bet or bal2<bet: return await ctx.send("❌ У кого-то не хватает")
    await add_balance(ctx.author.id, ctx.guild.id, -bet)
    await add_balance(member.id, ctx.guild.id, -bet)
    view = TicTacToeView(ctx.author.id, member.id, bet)
    embed = discord.Embed(title="❌⭕ КРЕСТИКИ-НОЛИКИ", color=discord.Color.blue())
    embed.add_field(name="💰 Ставка", value=f"{bet} 💎", inline=True)
    embed.add_field(name="🎲 Ход", value=f"{ctx.author.mention} (❌)", inline=True)
    ttt_games[ctx.channel.id] = {"p1": ctx.author.id, "p2": member.id, "bet": bet, "board": [["⬜","⬜","⬜"] for _ in range(3)], "turn": ctx.author.id}
    await ctx.send(embed=embed, view=view)

# ========== ВИСЕЛИЦА ==========
class HangmanGame:
    def __init__(self, word):
        self.word = word.upper()
        self.guessed = set()
        self.wrong = []
        self.max_wrong = 6
        self.pics = [
            "```\n   +---+\n       |\n       |\n       |\n      ===",
            "```\n   +---+\n   O   |\n       |\n       |\n      ===",
            "```\n   +---+\n   O   |\n   |   |\n       |\n      ===",
            "```\n   +---+\n   O   |\n  /|   |\n       |\n      ===",
            "```\n   +---+\n   O   |\n  /|\\  |\n       |\n      ===",
            "```\n   +---+\n   O   |\n  /|\\  |\n  /    |\n      ===",
            "```\n   +---+\n   O   |\n  /|\\  |\n  / \\  |\n      ==="
        ]
    def get_display(self):
        return " ".join([c if c in self.guessed else "_" for c in self.word])
    def guess(self, letter):
        letter = letter.upper()
        if letter in self.guessed or letter in self.wrong:
            return False, "already"
        if letter in self.word:
            self.guessed.add(letter)
            return True, "correct"
        else:
            self.wrong.append(letter)
            return False, "wrong"
    def is_won(self):
        return all(c in self.guessed for c in self.word)
    def is_lost(self):
        return len(self.wrong) >= self.max_wrong

hangman_words = ["ПИТОН", "ДИСКОРД", "БОТ", "СЕРВЕР", "ПРОГРАММИРОВАНИЕ", "РАЗРАБОТЧИК"]
hangman_games = {}

@bot.command()
async def hangman(ctx):
    if ctx.channel.id in hangman_games:
        return await ctx.send("❌ Игра уже идёт!")
    word = random.choice(hangman_words)
    game = HangmanGame(word)
    hangman_games[ctx.channel.id] = game
    embed = discord.Embed(title="🔤 ВИСЕЛИЦА", description=f"{game.pics[0]}\n\nСлово: {game.get_display()}\nОшибок: 0/{game.max_wrong}", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
async def guess(ctx, letter: str = None):
    if ctx.channel.id not in hangman_games:
        return await ctx.send("❌ Нет игры! `j.hangman`")
    if not letter or len(letter) != 1:
        return await ctx.send("❌ Введите одну букву!")
    game = hangman_games[ctx.channel.id]
    result, status = game.guess(letter)
    if status == "already":
        return await ctx.send(f"❌ Буква '{letter.upper()}' уже была!")
    embed = discord.Embed(title="🔤 ВИСЕЛИЦА", color=discord.Color.blue())
    if game.is_won():
        embed.description = f"{game.pics[len(game.wrong)]}\n\nСлово: {game.get_display()}\n\n🎉 ПОБЕДА!"
        embed.color = discord.Color.green()
        await ctx.send(embed=embed)
        del hangman_games[ctx.channel.id]
        return
    if game.is_lost():
        embed.description = f"{game.pics[game.max_wrong]}\n\n💀 ПОРАЖЕНИЕ! Слово: {game.word}"
        embed.color = discord.Color.red()
        await ctx.send(embed=embed)
        del hangman_games[ctx.channel.id]
        return
    embed.description = f"{game.pics[len(game.wrong)]}\n\nСлово: {game.get_display()}\nОшибок: {len(game.wrong)}/{game.max_wrong}\nНеправильные: {', '.join(game.wrong) if game.wrong else 'нет'}"
    await ctx.send(embed=embed)

# ========== СТОЛОТО ==========
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
    if not ch:
        return
    stoloto_active = True
    stoloto_tickets = []
    stoloto_end_time = datetime.now() + timedelta(days=1)
    embed = discord.Embed(
        title="🎰 СТО ЛОТО",
        description=f"**Новый розыгрыш!**\n⏰ До: <t:{int(stoloto_end_time.timestamp())}:R>\n💰 Джекпот: **{STOLOTO_TICKET_PRICE * 10}** 💎\n🎫 `j.loto_buy` - купить билет ({STOLOTO_TICKET_PRICE}💎)",
        color=discord.Color.gold()
    )
    await ch.send(embed=embed)
    await asyncio.sleep(86400)
    if not stoloto_tickets:
        await ch.send("😔 Никто не купил билеты")
    else:
        winner = random.choice(stoloto_tickets)
        prize = len(stoloto_tickets) * STOLOTO_TICKET_PRICE
        await add_balance(winner, ch.guild.id, prize)
        w = await bot.fetch_user(winner)
        await ch.send(f"🎉 **ПОБЕДИТЕЛЬ:** {w.mention}\n💰 **ПРИЗ:** {prize} 💎")
    stoloto_active = False

@bot.command()
async def loto_buy(ctx):
    global stoloto_tickets, stoloto_active, stoloto_end_time
    if not stoloto_active:
        return await ctx.send("❌ Розыгрыш не активен! Новый каждый день в 14:00 МСК")
    if datetime.now() >= stoloto_end_time:
        return await ctx.send("❌ Продажа билетов закончена!")
    if ctx.author.id in stoloto_tickets:
        return await ctx.send("❌ У вас уже есть билет!")
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < STOLOTO_TICKET_PRICE:
        return await ctx.send(f"❌ Не хватает {STOLOTO_TICKET_PRICE} 💎")
    await add_balance(ctx.author.id, ctx.guild.id, -STOLOTO_TICKET_PRICE)
    stoloto_tickets.append(ctx.author.id)
    await ctx.send(f"✅ Билет куплен! Участников: {len(stoloto_tickets)}")

# ========== ТОПЫ ==========
@bot.command()
async def top(ctx, category: str = "balance"):
    async with aiosqlite.connect("justice.db") as db:
        if category == "balance":
            cur = await db.execute('SELECT user_id, balance FROM users WHERE guild_id=? ORDER BY balance DESC LIMIT 10', (ctx.guild.id,))
        elif category == "reputation":
            cur = await db.execute('SELECT user_id, reputation FROM users WHERE guild_id=? ORDER BY reputation DESC LIMIT 10', (ctx.guild.id,))
        elif category == "level":
            cur = await db.execute('SELECT user_id, level, xp FROM users WHERE guild_id=? ORDER BY level DESC, xp DESC LIMIT 10', (ctx.guild.id,))
        elif category == "messages":
            cur = await db.execute('SELECT user_id, total_messages FROM users WHERE guild_id=? ORDER BY total_messages DESC LIMIT 10', (ctx.guild.id,))
        else: return await ctx.send("❌ balance, reputation, level, messages")
        rows = await cur.fetchall()
    if not rows: return await ctx.send("📊 Нет данных")
    msg = f"🏆 **ТОП {category.upper()}**\n"
    for i, row in enumerate(rows, 1):
        uid = row[0]
        user = ctx.guild.get_member(uid)
        name = user.display_name if user else f"ID:{uid}"
        if category == "balance":
            msg += f"{i}. {name} – {row[1]} 💎\n"
        elif category == "reputation":
            msg += f"{i}. {name} – {row[1]} ⭐\n"
        elif category == "level":
            msg += f"{i}. {name} – {row[1]} ур. ({row[2]} XP)\n"
        elif category == "messages":
            msg += f"{i}. {name} – {row[1]} сообщ.\n"
    await ctx.send(msg[:1900])

# ========== HELP ==========
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📖 ПОМОЩЬ", color=discord.Color.blue())
    embed.add_field(name="📊 ОСНОВНЫЕ", value="`j.profile` `j.balance` `j.work` `j.daily` `j.pay @user сумма`", inline=False)
    embed.add_field(name="🎮 ИГРЫ", value="`j.casino сумма` `j.slots сумма` `j.dice число сумма` `j.blackjack сумма` `j.ttt @user сумма`", inline=False)
    embed.add_field(name="🎣 РЫБАЛКА", value="`j.fish` `j.sell_all`", inline=False)
    embed.add_field(name="🎫 ТИКЕТЫ", value="`j.setup_ticket` (админ) – настройка кнопки", inline=False)
    embed.add_field(name="🎰 ЛОТО", value="`j.loto_buy` – купить билет (розыгрыш в 14:00 МСК)", inline=False)
    embed.add_field(name="⚙️ ДРУГИЕ", value="`j.weather город` `j.ai вопрос` `j.top balance` `j.hangman`", inline=False)
    await ctx.send(embed=embed)

# ========== МОДЕРАЦИЯ ==========
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason: str = "Не указана"):
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT INTO warnings (user_id, guild_id, moderator_id, reason, expires_at) VALUES (?,?,?,?,?)',
                        (member.id, ctx.guild.id, ctx.author.id, reason, expires_at))
        await db.commit()
    embed = discord.Embed(title="⚠️ ПРЕДУПРЕЖДЕНИЕ", color=discord.Color.orange())
    embed.add_field(name="👤 Пользователь", value=member.mention, inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: str, *, reason: str = "Не указана"):
    time_map = {"м": 60, "ч": 3600, "д": 86400}
    seconds = 0
    num = ""
    for char in duration:
        if char.isdigit():
            num += char
        elif char in time_map and num:
            seconds += int(num) * time_map[char]
            num = ""
    if seconds <= 0:
        return await ctx.send("❌ Пример: `j.mute @user 10м`")
    until = datetime.now() + timedelta(seconds=seconds)
    await member.timeout(until, reason=reason)
    await ctx.send(f"🔇 {member.mention} замучен на {duration}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"🔊 {member.mention} размучен")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = "Не указана"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} забанен")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: str = "Не указана"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} кикнут")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    if amount < 1 or amount > 100:
        return await ctx.send("❌ Можно удалить от 1 до 100 сообщений")
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ Удалено {len(deleted)-1} сообщений", delete_after=3)

# ========== ИНФО КОМАНДЫ ==========
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    t = member or ctx.author
    embed = discord.Embed(title=f"👤 ИНФОРМАЦИЯ | {t.display_name}", color=discord.Color.blue())
    embed.set_thumbnail(url=t.display_avatar.url)
    embed.add_field(name="🆔 ID", value=t.id, inline=True)
    embed.add_field(name="📅 Аккаунт создан", value=t.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="📅 Присоединился", value=t.joined_at.strftime("%d.%m.%Y"), inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    embed = discord.Embed(title=f"📊 ИНФОРМАЦИЯ | {g.name}", color=discord.Color.blue())
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="👑 Владелец", value=g.owner.mention, inline=True)
    embed.add_field(name="👥 Участников", value=g.member_count, inline=True)
    embed.add_field(name="📅 Создан", value=g.created_at.strftime("%d.%m.%Y"), inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Понг! Задержка: **{round(bot.latency * 1000)} мс**")

@bot.command()
async def about(ctx):
    embed = discord.Embed(title="🤖 JUSTICE BOT", color=discord.Color.blue())
    embed.add_field(name="📦 Версия", value="5.0", inline=True)
    embed.add_field(name="🖥️ Серверов", value=len(bot.guilds), inline=True)
    embed.add_field(name="🔤 Префикс", value="j.", inline=True)
    await ctx.send(embed=embed)

# ========== ЗАПУСК ==========
@bot.event
async def on_ready():
    await init_db()
    print(f"✅ {bot.user} запущен!")
    print(f"📊 На {len(bot.guilds)} серверах")
    bot.loop.create_task(stoloto_scheduler())
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="j.help | Justice Bot"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.guild:
        await get_user(message.author.id, message.guild.id)
        level_up, new_level = await add_xp(message.author.id, message.guild.id, random.randint(5, 15))
        if level_up:
            ch = bot.get_channel(LEVEL_CHANNEL_ID)
            if ch:
                await ch.send(f"🎉 {message.author.mention} достиг {new_level} уровня!")
        await check_achievement(message.author.id, message.guild.id, "messages", message.author.id)
        await check_daily_quest(message.author.id, message.guild.id, "messages", 1)
    if bot.user in message.mentions and not message.mention_everyone:
        await message.channel.send(f"👋 Привет, {message.author.mention}! Используй `j.help`")
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    role = member.guild.get_role(DEFAULT_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if ch:
        embed = discord.Embed(title="🎉 ДОБРО ПОЖАЛОВАТЬ!", description=f"{member.mention} присоединился!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        await ch.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"❌ Ошибка: {str(error)[:100]}")

# ========== ГЕНДЕР ==========
@bot.command()
async def gender(ctx, choice: str = None):
    if not choice:
        return await ctx.send("⚧ **Выбор гендера**\n`j.gender male` - мужчина\n`j.gender female` - девушка\n`j.gender remove` - убрать роль")
    choice = choice.lower()
    male = ctx.guild.get_role(ROLE_BOY)
    female = ctx.guild.get_role(ROLE_GIRL)
    if not male or not female:
        return await ctx.send("❌ Гендерные роли не настроены!")
    
    if choice in ["male", "мужчина", "м", "man"]:
        if female in ctx.author.roles:
            await ctx.author.remove_roles(female)
        await ctx.author.add_roles(male)
        await update_user(ctx.author.id, ctx.guild.id, gender="male")
        await ctx.send(f"✅ {ctx.author.mention} выбрал гендер: Мужчина 👨")
    
    elif choice in ["female", "девушка", "ж", "woman", "girl"]:
        if male in ctx.author.roles:
            await ctx.author.remove_roles(male)
        await ctx.author.add_roles(female)
        await update_user(ctx.author.id, ctx.guild.id, gender="female")
        await ctx.send(f"✅ {ctx.author.mention} выбрал гендер: Девушка 👩")
    
    elif choice in ["remove", "убрать", "снять"]:
        if male in ctx.author.roles:
            await ctx.author.remove_roles(male)
        if female in ctx.author.roles:
            await ctx.author.remove_roles(female)
        await update_user(ctx.author.id, ctx.guild.id, gender="")
        await ctx.send(f"✅ {ctx.author.mention} убрал гендерную роль")
    
    else:
        await ctx.send("❌ Доступные варианты: male, female, remove")

# ========== ЗАПУСК БОТА ==========
if __name__ == "__main__":
    print("🚀 Запуск Justice Bot...")
    if TOKEN == "ВСТАВЬ_СВОЙ_ТОКЕН" or not TOKEN:
        print("❌ ВСТАВЬ ТОКЕН В ПЕРЕМЕННУЮ ОКРУЖЕНИЯ DISCORD_TOKEN!")
        exit(1)
    bot.run(TOKEN)
