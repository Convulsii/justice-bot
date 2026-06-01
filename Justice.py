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
    TOKEN = "ВСТАВЬ_СВОЙ_ТОКЕН_СЮДА"

STEAM_API_KEY = os.getenv('STEAM_API_KEY')
YANDEX_WEATHER_API_KEY = os.getenv('YANDEX_WEATHER_API_KEY')

# ИИ
AI_API_KEY = "rk_live_G15mOokgVTN8hKFBvWVda38wZGOiXkVs"
AI_BASE_URL = "https://api.ranvik.ru/v1"
AI_MODEL = "gpt-5-nano"

AI_SYSTEM_PROMPT = """Ты дружелюбный помощник в Discord сервере.
СЕЙЧАС 2026 ГОД! Отвечай кратко и по делу.
Представься как Justice Bot AI."""

# ========== ID КАНАЛОВ (ЗАМЕНИ НА СВОИ) ==========
WELCOME_CHANNEL_ID = 0
LOGS_CHANNEL_ID = 0
LEVEL_CHANNEL_ID = 0
COLOR_ROLE_CHANNEL_ID = 0
MUTED_ROLE_ID = 0
DEFAULT_ROLE_ID = 0
VC_CREATE_CATEGORY_ID = 0
VC_TRIGGER_CHANNEL_ID = 0
TICKET_CATEGORY_ID = 0
TICKET_CREATE_CHANNEL_ID = 0
STOLOTO_CHANNEL_ID = 0
IDEA_REVIEW_CHANNEL_ID = 0

# Роли поддержки (ID)
SUPPORT_ROLE_IDS = [0, 0]

# Гендерные роли
ROLE_GIRL = 0
ROLE_BOY = 0

# Цветные роли
COLOR_ROLES = {
    "🔴": {"name": "Красный", "id": 0},
    "🔵": {"name": "Синий", "id": 0},
    "🟢": {"name": "Зелёный", "id": 0},
    "🟡": {"name": "Жёлтый", "id": 0},
    "🟣": {"name": "Фиолетовый", "id": 0},
    "🌸": {"name": "Розовый", "id": 0},
    "⚪": {"name": "Белый", "id": 0},
    "⬛": {"name": "Чёрный", "id": 0},
}

# Роли за уровни
LEVEL_ROLES = {
    5: 0,
    10: 0,
    25: 0,
    50: 0,
    100: 0,
}

# ========== НАСТРОЙКИ ЭКОНОМИКИ ==========
START_BALANCE = 100
MIN_EARN = 2
MAX_EARN = 6
BANK_INTEREST = 0.03
DAILY_AMOUNT = 100
WEEKLY_AMOUNT = 500
MONTHLY_AMOUNT = 2000
TIMELY_AMOUNT = 50

# КД (секунды)
GAME_COOLDOWN = {
    "casino": 300,
    "dice": 300,
    "coin": 300,
    "rps": 300,
    "blackjack": 300,
    "rob": 3600,
    "work": 3600,
    "rep": 3600,
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2592000,
    "timely": 3600,
}

# Шансы выигрыша
WIN_CHANCE = {
    "casino": 0.35,
    "coin": 0.45,
    "dice": 0.16,
    "rps": 0.33,
    "blackjack": 0.42,
    "rob": 0.05,
}

# Эмодзи для слотов
SLOT_EMOJIS = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎"]
DICE_EMOJIS = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]

# ========== МАГАЗИН ==========
SHOP_ITEMS = {
    "звезда": {"price": 500, "description": "⭐ Звезда в профиль", "type": "award", "role_id": None},
    "сердечко": {"price": 300, "description": "💖 Сердечко в профиль", "type": "award", "role_id": None},
    "корону": {"price": 1000, "description": "👑 Корона в профиль", "type": "award", "role_id": None},
    "радугу": {"price": 700, "description": "🌈 Радуга в профиль", "type": "award", "role_id": None},
    "бриллиант": {"price": 2000, "description": "💎 Бриллиант в профиль", "type": "award", "role_id": None},
}

CUSTOM_SHOP_ITEMS = {}

# ========== ФЕРМА ==========
SEEDS = {
    "пшеница": {"price": 50, "grow_time": 3600, "rarity_weights": {"обычный": 0.7, "редкий": 0.2, "эпический": 0.08, "легендарный": 0.02}, "base_price": 100},
    "кукуруза": {"price": 80, "grow_time": 7200, "rarity_weights": {"обычный": 0.6, "редкий": 0.25, "эпический": 0.1, "легендарный": 0.05}, "base_price": 150},
    "томат": {"price": 100, "grow_time": 10800, "rarity_weights": {"обычный": 0.5, "редкий": 0.3, "эпический": 0.15, "легендарный": 0.05}, "base_price": 200},
    "картофель": {"price": 60, "grow_time": 5400, "rarity_weights": {"обычный": 0.65, "редкий": 0.25, "эпический": 0.08, "легендарный": 0.02}, "base_price": 120},
    "морковь": {"price": 70, "grow_time": 7200, "rarity_weights": {"обычный": 0.6, "редкий": 0.3, "эпический": 0.08, "легендарный": 0.02}, "base_price": 130},
    "роза": {"price": 150, "grow_time": 14400, "rarity_weights": {"обычный": 0.5, "редкий": 0.3, "эпический": 0.15, "легендарный": 0.05}, "base_price": 300},
    "кактус": {"price": 120, "grow_time": 18000, "rarity_weights": {"обычный": 0.55, "редкий": 0.25, "эпический": 0.15, "легендарный": 0.05}, "base_price": 250},
    "подсолнух": {"price": 90, "grow_time": 9000, "rarity_weights": {"обычный": 0.6, "редкий": 0.3, "эпический": 0.08, "легендарный": 0.02}, "base_price": 180},
    "тыква": {"price": 200, "grow_time": 28800, "rarity_weights": {"обычный": 0.5, "редкий": 0.25, "эпический": 0.2, "легендарный": 0.05}, "base_price": 400},
    "арбуз": {"price": 250, "grow_time": 36000, "rarity_weights": {"обычный": 0.4, "редкий": 0.3, "эпический": 0.2, "легендарный": 0.1}, "base_price": 500},
}

RARITY_MULTIPLIERS = {
    "обычный": 1.0,
    "редкий": 2.0,
    "эпический": 4.0,
    "легендарный": 8.0,
    "мифический": 16.0,
}

# Карты для покера
CARD_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
CARD_SUITS = ['♠️', '♥️', '♣️', '♦️']
FULL_DECK = [f"{r}{s}" for r in CARD_RANKS for s in CARD_SUITS]

# Значения карт для покера
CARD_VALUES = {r: i for i, r in enumerate(CARD_RANKS, 2)}

# ========== СТО ЛОТО ==========
STOLOTO_TIME = "14:00"
STOLOTO_TICKET_PRICE = 50
STOLOTO_JACKPOT_MIN = 1000

# ========== АВТОМОДЕРАЦИЯ ==========
ANTISPAM_WINDOW_SECONDS = 8
ANTISPAM_MAX_MESSAGES = 5
ANTISPAM_MAX_WARNINGS = 3
ANTISPAM_WARNING_EXPIRE_HOURS = 24

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
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
color_message_id = None
vc_sessions = {}
user_message_timestamps = defaultdict(list)
user_warnings = defaultdict(list)
user_conversations = defaultdict(list)
spam_messages_to_delete = defaultdict(list)
daily_streaks = defaultdict(int)
last_daily_time = defaultdict(int)
fishing_cooldowns = defaultdict(int)
active_baits = defaultdict(dict)
fishing_upgrades = defaultdict(lambda: {"luck": 0, "exp": 0, "price": 0, "double_chance": 0})
fishing_experience = defaultdict(int)
fishing_levels = defaultdict(int)
active_giveaways = {}
MAX_CONTEXT_MESSAGES = 10

# ========== РОЛЕВЫЕ GIF ==========
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
    "wink": "https://media.tenor.com/tPfEQC6tWyYAAAAM/wink-anime.gif",
    "kill": "https://media.tenor.com/U6jR9mNkXkYAAAAM/anime-death.gif",
    "stab": "https://media.tenor.com/QB1DLuQwGVsAAAAM/anime-stab.gif",
    "shoot": "https://media.tenor.com/SYQkhRtA0KYAAAAM/anime-gun.gif",
    "yeet": "https://media.tenor.com/OjE6qG1rQxMAAAAM/anime-yeet.gif",
}

# Инициализация ИИ клиента
ai_client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)

# ========== СООБЩЕНИЕ 2 - БАЗА ДАННЫХ ==========

async def init_db():
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            guild_id INTEGER,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0,
            balance INTEGER DEFAULT 100,
            bank INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 0,
            join_date TEXT,
            warning_count INTEGER DEFAULT 0,
            total_messages INTEGER DEFAULT 0,
            last_daily TEXT,
            last_weekly TEXT,
            last_monthly TEXT,
            last_timely TEXT,
            last_work TEXT,
            color_role_id INTEGER DEFAULT 0,
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
            fishing_exp INTEGER DEFAULT 0,
            last_fish_time INTEGER DEFAULT 0,
            total_fish INTEGER DEFAULT 0,
            total_trash INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            guild_id INTEGER,
            moderator_id INTEGER,
            reason TEXT,
            expires_at TEXT
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            guild_id INTEGER,
            suggestion TEXT,
            status TEXT DEFAULT 'pending',
            verdict TEXT,
            date TEXT
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS private_vc (
            channel_id INTEGER PRIMARY KEY,
            owner_id INTEGER,
            guild_id INTEGER,
            channel_name TEXT,
            user_limit INTEGER DEFAULT 0,
            is_locked INTEGER DEFAULT 0,
            banned_users TEXT DEFAULT '[]',
            created_at TEXT
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER,
            message_id INTEGER,
            prize TEXT,
            winners INTEGER,
            end_time TEXT,
            entries TEXT,
            ended INTEGER DEFAULT 0
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS stoloto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            winner_id INTEGER,
            prize INTEGER,
            numbers TEXT
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS custom_shop (
            name TEXT PRIMARY KEY,
            price INTEGER,
            description TEXT,
            role_id INTEGER
        )''')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            welcome_channel INTEGER,
            log_channel INTEGER,
            levels_channel INTEGER,
            automod_enabled INTEGER DEFAULT 1,
            automod_bad_words TEXT DEFAULT '[]',
            automod_invites_enabled INTEGER DEFAULT 1,
            automod_phishing_enabled INTEGER DEFAULT 1,
            automod_exempt_roles TEXT DEFAULT '[]'
        )''')
        
        await db.commit()
    
    # Загружаем кастомный магазин
    async with aiosqlite.connect("justice.db") as db:
        async with db.execute('SELECT name, price, description, role_id FROM custom_shop') as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                CUSTOM_SHOP_ITEMS[row[0]] = {"price": row[1], "description": row[2], "type": "role", "role_id": row[3]}
    
    # Загружаем настройки гильдий
    async with aiosqlite.connect("justice.db") as db:
        async with db.execute('SELECT guild_id, welcome_channel, log_channel, levels_channel, automod_enabled, automod_bad_words, automod_invites_enabled, automod_phishing_enabled, automod_exempt_roles FROM guild_settings') as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                guild_settings[row[0]] = {
                    "welcome_channel": row[1],
                    "log_channel": row[2],
                    "levels_channel": row[3],
                    "automod_enabled": bool(row[4]),
                    "automod_bad_words": json.loads(row[5]) if row[5] else [],
                    "automod_invites_enabled": bool(row[6]),
                    "automod_phishing_enabled": bool(row[7]),
                    "automod_exempt_roles": json.loads(row[8]) if row[8] else []
                }
    
    print("✅ База данных готова")


async def get_user(user_id, guild_id):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM users WHERE user_id=? AND guild_id=?', (user_id, guild_id))
        row = await cur.fetchone()
        if not row:
            now = datetime.now().isoformat()
            await db.execute('''INSERT INTO users (
                user_id, guild_id, join_date, balance, today_messages, 
                week_messages, month_messages, total_messages, last_message_time, 
                pots, fishing_exp, last_fish_time
            ) VALUES (?,?,?,?,?,?,?,?,?,0,0,0)''', 
            (user_id, guild_id, now, START_BALANCE, 0, 0, 0, 0, now))
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
    new_xp = user[2] + amount
    new_level = int((new_xp / 200) ** 0.55)
    level_up = new_level > user[3]
    
    await update_user(
        user_id, guild_id,
        xp=new_xp,
        level=new_level,
        total_messages=user[9] + 1,
        today_messages=user[22] + 1,
        week_messages=user[23] + 1,
        month_messages=user[24] + 1,
        last_message_time=datetime.now().isoformat()
    )
    
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
# ========== СООБЩЕНИЕ 3 - ЭКОНОМИКА И БАНК ==========

@bot.command()
async def balance(ctx, member: discord.Member = None):
    """💰 Показать баланс"""
    target = member or ctx.author
    user = await get_user(target.id, ctx.guild.id)
    embed = discord.Embed(title=f"💰 БАЛАНС | {target.display_name}", color=discord.Color.gold())
    embed.add_field(name="💎 Наличные", value=f"{user[4]} 💎", inline=True)
    embed.add_field(name="🏦 В банке", value=f"{user[5]} 💎", inline=True)
    embed.add_field(name="📊 Репутация", value=f"{user[6]} ❤️", inline=True)
    embed.set_footer(text="j.deposit <сумма> | j.withdraw <сумма> | j.bank")
    await ctx.send(embed=embed)


@bot.command()
async def bank(ctx):
    """🏦 Показать банковскую информацию"""
    user = await get_user(ctx.author.id, ctx.guild.id)
    embed = discord.Embed(title=f"🏦 БАНК | {ctx.author.display_name}", color=discord.Color.blue())
    embed.add_field(name="💰 В банке", value=f"{user[5]} 💎", inline=True)
    embed.add_field(name="💎 В кошельке", value=f"{user[4]} 💎", inline=True)
    embed.add_field(name="📈 Процент", value=f"{BANK_INTEREST * 100}% в час", inline=True)
    embed.set_footer(text="j.deposit | j.withdraw | j.bank_interest")
    await ctx.send(embed=embed)


@bot.command()
async def deposit(ctx, amount: str):
    """💰 Положить деньги в банк"""
    user = await get_user(ctx.author.id, ctx.guild.id)
    
    if amount.lower() == "all":
        amount = user[4]
    else:
        amount = int(amount)
    
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    if user[4] < amount:
        await ctx.send(f"❌ У вас только {user[4]} 💎")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -amount)
    await add_bank(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"✅ Вы положили {amount} 💎 в банк!")


@bot.command()
async def withdraw(ctx, amount: str):
    """💰 Снять деньги из банка"""
    user = await get_user(ctx.author.id, ctx.guild.id)
    
    if amount.lower() == "all":
        amount = user[5]
    else:
        amount = int(amount)
    
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    if user[5] < amount:
        await ctx.send(f"❌ В банке только {user[5]} 💎")
        return
    
    await add_bank(ctx.author.id, ctx.guild.id, -amount)
    await add_balance(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"✅ Вы сняли {amount} 💎 из банка!")


@tasks.loop(hours=1)
async def bank_interest():
    """Начисление процентов каждый час"""
    async with aiosqlite.connect("justice.db") as db:
        await db.execute(f'UPDATE users SET bank = bank + CAST(bank * {BANK_INTEREST} AS INTEGER)')
        await db.commit()
    print("✅ Начислены банковские проценты")


@bot.command()
async def work(ctx):
    """💼 Работать"""
    ready, remaining = check_cooldown(ctx.author.id, "work")
    if not ready:
        await ctx.send(f"⏰ Вы устали! Отдохните {remaining // 60} минут")
        return
    
    earn = random.randint(MIN_EARN, MAX_EARN)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    set_cooldown(ctx.author.id, "work")
    
    responses = [
        f"💼 Вы поработали продавцом и получили {earn} 💎",
        f"🖥️ Вы поработали программистом и получили {earn} 💎",
        f"📚 Вы поработали репетитором и получили {earn} 💎",
        f"🚗 Вы поработали таксистом и получили {earn} 💎",
        f"🍕 Вы поработали в пиццерии и получили {earn} 💎",
    ]
    await ctx.send(random.choice(responses))


@bot.command()
async def daily(ctx):
    """📅 Ежедневный бонус (со страйком)"""
    user = await get_user(ctx.author.id, ctx.guild.id)
    now = datetime.now()
    
    if user[10] and user[10] != "None":
        last = datetime.fromisoformat(user[10])
        diff = (now - last).days
        
        if diff == 1:
            daily_streaks[ctx.author.id] = daily_streaks.get(ctx.author.id, 0) + 1
        elif diff > 1:
            daily_streaks[ctx.author.id] = 1
        else:
            await ctx.send("⏰ Вы уже получили ежедневный бонус! Приходите завтра")
            return
    else:
        daily_streaks[ctx.author.id] = 1
    
    streak = daily_streaks[ctx.author.id]
    bonus = DAILY_AMOUNT + (streak * 10)
    await add_balance(ctx.author.id, ctx.guild.id, bonus)
    await update_user(ctx.author.id, ctx.guild.id, last_daily=now.isoformat())
    
    embed = discord.Embed(title="📅 ЕЖЕДНЕВНЫЙ БОНУС", color=discord.Color.green())
    embed.add_field(name="💰 Получено", value=f"{bonus} 💎", inline=True)
    embed.add_field(name="🔥 Страйк", value=f"{streak} дней", inline=True)
    embed.add_field(name="🎯 Следующий бонус", value=f"+{DAILY_AMOUNT + ((streak + 1) * 10)} 💎", inline=True)
    await ctx.send(embed=embed)


@bot.command()
async def weekly(ctx):
    """📆 Еженедельный бонус"""
    user = await get_user(ctx.author.id, ctx.guild.id)
    
    if user[11] and user[11] != "None":
        last = datetime.fromisoformat(user[11])
        if (datetime.now() - last).days < 7:
            await ctx.send("⏰ Еженедельный бонус можно получить раз в 7 дней!")
            return
    
    await add_balance(ctx.author.id, ctx.guild.id, WEEKLY_AMOUNT)
    await update_user(ctx.author.id, ctx.guild.id, last_weekly=datetime.now().isoformat())
    await ctx.send(f"✅ Еженедельный бонус {WEEKLY_AMOUNT} 💎!")


@bot.command()
async def monthly(ctx):
    """📅 Ежемесячный бонус"""
    user = await get_user(ctx.author.id, ctx.guild.id)
    
    if user[12] and user[12] != "None":
        last = datetime.fromisoformat(user[12])
        if (datetime.now() - last).days < 30:
            await ctx.send("⏰ Ежемесячный бонус можно получить раз в 30 дней!")
            return
    
    await add_balance(ctx.author.id, ctx.guild.id, MONTHLY_AMOUNT)
    await update_user(ctx.author.id, ctx.guild.id, last_monthly=datetime.now().isoformat())
    await ctx.send(f"✅ Ежемесячный бонус {MONTHLY_AMOUNT} 💎!")


@bot.command()
async def timely(ctx):
    """⏰ Бонус каждые 4 часа"""
    ready, remaining = check_cooldown(ctx.author.id, "timely")
    if not ready:
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        await ctx.send(f"⏰ Следующий бонус через {hours}ч {mins}мин")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, TIMELY_AMOUNT)
    set_cooldown(ctx.author.id, "timely")
    await ctx.send(f"✅ Бонус {TIMELY_AMOUNT} 💎! Возвращайтесь через 4 часа!")


@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    """💸 Перевести деньги пользователю"""
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    if member.id == ctx.author.id:
        await ctx.send("❌ Нельзя перевести самому себе")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < amount:
        await ctx.send(f"❌ Недостаточно средств! У вас {user[4]} 💎")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -amount)
    await add_balance(member.id, ctx.guild.id, amount)
    
    embed = discord.Embed(title="💸 ПЕРЕВОД", color=discord.Color.green())
    embed.add_field(name="📤 Отправитель", value=ctx.author.mention, inline=True)
    embed.add_field(name="📥 Получатель", value=member.mention, inline=True)
    embed.add_field(name="💰 Сумма", value=f"{amount} 💎", inline=True)
    await ctx.send(embed=embed)


@bot.command()
async def leaderboard(ctx):
    """🏆 Топ по балансу"""
    async with aiosqlite.connect("justice.db") as db:
        async with db.execute('SELECT user_id, balance FROM users WHERE guild_id=? ORDER BY balance DESC LIMIT 10', (ctx.guild.id,)) as cursor:
            rows = await cursor.fetchall()
    
    if not rows:
        await ctx.send("📭 Нет данных")
        return
    
    embed = discord.Embed(title=f"🏆 ТОП ПО БАЛАНСУ | {ctx.guild.name}", color=discord.Color.gold())
    for i, (user_id, balance) in enumerate(rows, 1):
        user = ctx.guild.get_member(user_id)
        name = user.display_name if user else f"ID:{user_id}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        embed.add_field(name=f"{medal} #{i} {name}", value=f"{balance} 💎", inline=False)
    
    await ctx.send(embed=embed)


@bot.command()
async def rep(ctx, member: discord.Member):
    """❤️ Дать репутацию пользователю"""
    if member.id == ctx.author.id:
        await ctx.send("❌ Нельзя дать репутацию самому себе")
        return
    
    ready, remaining = check_rep_cooldown(ctx.author.id, member.id)
    if not ready:
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        await ctx.send(f"⏰ Вы уже дали репутацию этому пользователю! Подождите {hours}ч {mins}мин")
        return
    
    await add_reputation(member.id, ctx.guild.id, 1)
    set_rep_cooldown(ctx.author.id, member.id)
    
    embed = discord.Embed(title="❤️ +1 РЕПУТАЦИЯ", color=discord.Color.pink())
    embed.add_field(name="📤 От", value=ctx.author.mention, inline=True)
    embed.add_field(name="📥 Кому", value=member.mention, inline=True)
    await ctx.send(embed=embed)


@bot.command()
async def top_rep(ctx):
    """🏆 Топ по репутации"""
    async with aiosqlite.connect("justice.db") as db:
        async with db.execute('SELECT user_id, reputation FROM users WHERE guild_id=? ORDER BY reputation DESC LIMIT 10', (ctx.guild.id,)) as cursor:
            rows = await cursor.fetchall()
    
    if not rows:
        await ctx.send("📭 Нет данных")
        return
    
    embed = discord.Embed(title=f"🏆 ТОП ПО РЕПУТАЦИИ | {ctx.guild.name}", color=discord.Color.pink())
    for i, (user_id, rep) in enumerate(rows, 1):
        user = ctx.guild.get_member(user_id)
        name = user.display_name if user else f"ID:{user_id}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        embed.add_field(name=f"{medal} #{i} {name}", value=f"{rep} ❤️", inline=False)
    
    await ctx.send(embed=embed)
# ========== СООБЩЕНИЕ 4 - МАГАЗИН И ИНВЕНТАРЬ ==========

@bot.command()
async def shop(ctx, category: str = None):
    """🛒 Магазин"""
    embed = discord.Embed(title="🛒 МАГАЗИН | Justice Bot", color=discord.Color.teal())
    
    # Обычные товары
    items_text = ""
    for name, item in SHOP_ITEMS.items():
        items_text += f"**{name}** - {item['price']} 💎 | {item['description']}\n"
    embed.add_field(name="📦 Обычные товары", value=items_text or "Нет", inline=False)
    
    # Кастомные товары
    if CUSTOM_SHOP_ITEMS:
        custom_text = ""
        for name, item in CUSTOM_SHOP_ITEMS.items():
            custom_text += f"**{name}** - {item['price']} 💎 | {item['description']}\n"
        embed.add_field(name="🎭 Кастомные товары", value=custom_text, inline=False)
    
    embed.set_footer(text="j.buy <товар> - купить | j.inventory - инвентарь")
    await ctx.send(embed=embed)


@bot.command()
async def buy(ctx, *, item_name: str = None):
    """💰 Купить товар"""
    if not item_name:
        await ctx.send("❌ Укажите товар: `j.buy звезда`")
        return
    
    item_name = item_name.lower()
    
    # Проверяем в обычном магазине
    if item_name in SHOP_ITEMS:
        item = SHOP_ITEMS[item_name]
        user = await get_user(ctx.author.id, ctx.guild.id)
        
        if user[4] < item["price"]:
            await ctx.send(f"❌ Недостаточно средств! Нужно {item['price']} 💎")
            return
        
        await add_balance(ctx.author.id, ctx.guild.id, -item["price"])
        
        # Добавляем награду в профиль
        awards = json.loads(user[18] if len(user) > 18 else "[]")
        awards.append(item_name)
        await update_user(ctx.author.id, ctx.guild.id, awards=json.dumps(awards))
        
        await ctx.send(f"✅ Вы купили **{item_name}** {SHOP_ITEMS[item_name]['description']} за {item['price']} 💎!")
        return
    
    # Проверяем в кастомном магазине
    if item_name in CUSTOM_SHOP_ITEMS:
        item = CUSTOM_SHOP_ITEMS[item_name]
        user = await get_user(ctx.author.id, ctx.guild.id)
        
        if user[4] < item["price"]:
            await ctx.send(f"❌ Недостаточно средств! Нужно {item['price']} 💎")
            return
        
        if item["type"] == "role" and item["role_id"]:
            role = ctx.guild.get_role(item["role_id"])
            if role:
                await ctx.author.add_roles(role)
                await add_balance(ctx.author.id, ctx.guild.id, -item["price"])
                await ctx.send(f"✅ Вы купили роль **{role.name}** за {item['price']} 💎!")
            else:
                await ctx.send("❌ Ошибка: роль не найдена")
        return
    
    await ctx.send("❌ Товар не найден! Используйте `j.shop` для списка")


@bot.command()
async def inventory(ctx, member: discord.Member = None):
    """📦 Инвентарь пользователя"""
    target = member or ctx.author
    user = await get_user(target.id, ctx.guild.id)
    awards = json.loads(user[18] if len(user) > 18 else "[]")
    inventory = json.loads(user[19] if len(user) > 19 else "[]")
    
    embed = discord.Embed(title=f"📦 ИНВЕНТАРЬ | {target.display_name}", color=discord.Color.green())
    
    # Награды
    if awards:
        awards_text = " ".join([SHOP_ITEMS.get(a, {}).get("description", a) for a in awards])
        embed.add_field(name="🏆 Награды", value=awards_text, inline=False)
    else:
        embed.add_field(name="🏆 Награды", value="Нет", inline=False)
    
    # Рыба и предметы
    fish_items = [i for i in inventory if i.startswith("fish_")]
    trash_items = [i for i in inventory if i.startswith("trash_")]
    bait_items = [i for i in inventory if i.startswith("bait_")]
    rod_items = [i for i in inventory if i.startswith("rod_")]
    crop_items = [i for i in inventory if i.startswith("crop_")]
    
    if fish_items:
        embed.add_field(name="🎣 Рыба", value=f"{len(fish_items)} шт.", inline=True)
    if trash_items:
        embed.add_field(name="🗑️ Мусор", value=f"{len(trash_items)} шт.", inline=True)
    if bait_items:
        embed.add_field(name="🪱 Наживки", value=f"{len(bait_items)} шт.", inline=True)
    if rod_items:
        rods = [r.replace("rod_", "") for r in rod_items]
        embed.add_field(name="🎣 Удочки", value=", ".join(rods), inline=True)
    if crop_items:
        embed.add_field(name="🌾 Посажено", value=f"{len(crop_items)} шт.", inline=True)
    
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def add_shop_item(ctx, name: str, price: int, role_id: int, *, description: str = None):
    """🛒 Добавить кастомный товар (админ)"""
    if not description:
        description = f"Роль {ctx.guild.get_role(role_id).mention if ctx.guild.get_role(role_id) else role_id}"
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT OR REPLACE INTO custom_shop (name, price, description, role_id) VALUES (?,?,?,?)',
                        (name.lower(), price, description, role_id))
        await db.commit()
    
    CUSTOM_SHOP_ITEMS[name.lower()] = {"price": price, "description": description, "type": "role", "role_id": role_id}
    await ctx.send(f"✅ Товар **{name}** добавлен в магазин за {price} 💎")


@bot.command()
@commands.has_permissions(administrator=True)
async def remove_shop_item(ctx, name: str):
    """🛒 Удалить кастомный товар (админ)"""
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('DELETE FROM custom_shop WHERE name=?', (name.lower(),))
        await db.commit()
    
    if name.lower() in CUSTOM_SHOP_ITEMS:
        del CUSTOM_SHOP_ITEMS[name.lower()]
    
    await ctx.send(f"✅ Товар **{name}** удалён из магазина")


# ========== ПРОФИЛЬ ==========
@bot.command()
async def profile(ctx, member: discord.Member = None):
    """👤 Профиль пользователя"""
    target = member or ctx.author
    user = await get_user(target.id, ctx.guild.id)
    awards = json.loads(user[18] if len(user) > 18 else "[]")
    
    # Получаем цветную роль
    color_role = None
    if user[16] and user[16] != 0:
        color_role = ctx.guild.get_role(user[16])
    
    embed = discord.Embed(title=f"👤 ПРОФИЛЬ | {target.display_name}", color=color_role.color if color_role else discord.Color.blue())
    embed.set_thumbnail(url=target.display_avatar.url)
    
    # Основная информация
    join_date = datetime.fromisoformat(user[7]) if user[7] else datetime.now()
    embed.add_field(name="📅 На сервере", value=f"<t:{int(join_date.timestamp())}:R>", inline=True)
    embed.add_field(name="📊 Уровень", value=f"{user[3]} уровень", inline=True)
    embed.add_field(name="✨ Опыт", value=f"{user[2]} XP", inline=True)
    embed.add_field(name="💎 Баланс", value=f"{user[4]} 💎", inline=True)
    embed.add_field(name="🏦 В банке", value=f"{user[5]} 💎", inline=True)
    embed.add_field(name="❤️ Репутация", value=f"{user[6]}", inline=True)
    embed.add_field(name="📨 Сообщений", value=f"{user[9]}", inline=True)
    
    # Статистика за период
    embed.add_field(name="📊 Сегодня", value=f"{user[22]} сообщ.", inline=True)
    embed.add_field(name="📊 Неделя", value=f"{user[23]} сообщ.", inline=True)
    embed.add_field(name="📊 Месяц", value=f"{user[24]} сообщ.", inline=True)
    
    # Награды
    if awards:
        awards_text = " ".join([SHOP_ITEMS.get(a, {}).get("description", a) for a in awards[:5]])
        embed.add_field(name="🏆 Награды", value=awards_text, inline=False)
    
    # Био
    if user[17] and user[17] != "":
        embed.add_field(name="📝 О себе", value=user[17][:500], inline=False)
    
    await ctx.send(embed=embed)


@bot.command()
async def set_bio(ctx, *, bio: str = None):
    """📝 Установить описание профиля"""
    if not bio:
        await ctx.send("❌ Укажите текст: `j.set_bio Привет! Я новый пользователь`")
        return
    
    if len(bio) > 500:
        await ctx.send("❌ Био не может быть длиннее 500 символов")
        return
    
    await update_user(ctx.author.id, ctx.guild.id, bio=bio)
    await ctx.send("✅ Био обновлено!")


@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """🖼️ Показать аватар пользователя"""
    target = member or ctx.author
    embed = discord.Embed(title=f"🖼️ АВАТАР | {target.display_name}", color=discord.Color.blue())
    embed.set_image(url=target.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def server(ctx):
    """📊 Информация о сервере"""
    embed = discord.Embed(title=f"📊 ИНФОРМАЦИЯ | {ctx.guild.name}", color=discord.Color.gold())
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    
    embed.add_field(name="👑 Владелец", value=ctx.guild.owner.mention, inline=True)
    embed.add_field(name="👥 Участников", value=f"{ctx.guild.member_count}", inline=True)
    embed.add_field(name="💬 Каналов", value=f"{len(ctx.guild.channels)}", inline=True)
    embed.add_field(name="🎭 Ролей", value=f"{len(ctx.guild.roles)}", inline=True)
    embed.add_field(name="📅 Создан", value=f"<t:{int(ctx.guild.created_at.timestamp())}:R>", inline=True)
    
    await ctx.send(embed=embed)
# ========== СООБЩЕНИЕ 5 - ИГРЫ (КАЗИНО, СЛОТЫ, КОСТИ, МОНЕТКА, КНБ, БЛЕКДЖЕК) ==========

@bot.command()
async def casino(ctx, amount: int):
    """🎰 Казино (шанс 35%)"""
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    
    ready, remaining = check_cooldown(ctx.author.id, "casino")
    if not ready:
        await ctx.send(f"⏰ Подождите {remaining // 60} минут")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < amount:
        await ctx.send(f"❌ Недостаточно средств! У вас {user[4]} 💎")
        return
    
    win = random.random() < WIN_CHANCE["casino"]
    set_cooldown(ctx.author.id, "casino")
    
    if win:
        win_amount = int(amount * 1.5)
        await add_balance(ctx.author.id, ctx.guild.id, win_amount)
        embed = discord.Embed(title="🎰 КАЗИНО", description=f"**ВЫ ВЫИГРАЛИ!**", color=discord.Color.green())
        embed.add_field(name="💰 Ставка", value=f"{amount} 💎", inline=True)
        embed.add_field(name="🏆 Выигрыш", value=f"{win_amount} 💎", inline=True)
        await ctx.send(embed=embed)
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        embed = discord.Embed(title="🎰 КАЗИНО", description=f"**ВЫ ПРОИГРАЛИ!**", color=discord.Color.red())
        embed.add_field(name="💰 Потеряно", value=f"{amount} 💎", inline=True)
        await ctx.send(embed=embed)


@bot.command()
async def slots(ctx, amount: int):
    """🎰 Слоты (3 эмодзи)"""
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < amount:
        await ctx.send(f"❌ Недостаточно средств! У вас {user[4]} 💎")
        return
    
    emoji = SLOT_EMOJIS
    a, b, c = random.choice(emoji), random.choice(emoji), random.choice(emoji)
    
    if a == b == c:
        win = amount * 5
        await add_balance(ctx.author.id, ctx.guild.id, win)
        result = f"🎰 [{a}] [{b}] [{c}]\n✨ **ДЖЕКПОТ! +{win} 💎** ✨"
    elif a == b or b == c or a == c:
        win = amount * 2
        await add_balance(ctx.author.id, ctx.guild.id, win)
        result = f"🎰 [{a}] [{b}] [{c}]\n✅ **ВЫИГРЫШ! +{win} 💎**"
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        result = f"🎰 [{a}] [{b}] [{c}]\n❌ **ПРОИГРЫШ! -{amount} 💎**"
    
    await ctx.send(result)


@bot.command()
async def dice(ctx, amount: int = None, guess: int = None):
    """🎲 Кости (угадай число 1-6)"""
    if amount is None:
        roll = random.randint(1, 6)
        await ctx.send(f"🎲 {DICE_EMOJIS[roll-1]} Выпало: **{roll}**")
        return
    
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    if guess and (guess < 1 or guess > 6):
        await ctx.send("❌ Угадывайте число от 1 до 6")
        return
    
    ready, remaining = check_cooldown(ctx.author.id, "dice")
    if not ready:
        await ctx.send(f"⏰ Подождите {remaining // 60} минут")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < amount:
        await ctx.send(f"❌ Недостаточно средств! У вас {user[4]} 💎")
        return
    
    roll = random.randint(1, 6)
    set_cooldown(ctx.author.id, "dice")
    
    if guess:
        if roll == guess:
            win = amount * 3
            await add_balance(ctx.author.id, ctx.guild.id, win)
            await ctx.send(f"🎲 {DICE_EMOJIS[roll-1]} **{roll}**! ВЫ УГАДАЛИ! +{win} 💎")
        else:
            await add_balance(ctx.author.id, ctx.guild.id, -amount)
            await ctx.send(f"🎲 {DICE_EMOJIS[roll-1]} **{roll}**! ВЫ НЕ УГАДАЛИ! -{amount} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await ctx.send(f"🎲 {DICE_EMOJIS[roll-1]} Выпало: **{roll}** | -{amount} 💎")


@bot.command()
async def coin(ctx, amount: int = None, choice: str = None):
    """🪙 Монетка (орел/решка)"""
    if amount is None:
        result = random.choice(["Орел", "Решка"])
        await ctx.send(f"🪙 Выпало: **{result}**")
        return
    
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    
    ready, remaining = check_cooldown(ctx.author.id, "coin")
    if not ready:
        await ctx.send(f"⏰ Подождите {remaining // 60} минут")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < amount:
        await ctx.send(f"❌ Недостаточно средств! У вас {user[4]} 💎")
        return
    
    if not choice:
        choice = random.choice(["орел", "решка"])
    else:
        choice = choice.lower()
        if choice not in ["орел", "решка"]:
            await ctx.send("❌ Выбирайте: орел или решка")
            return
    
    result = random.choice(["орел", "решка"])
    set_cooldown(ctx.author.id, "coin")
    
    if choice == result:
        await add_balance(ctx.author.id, ctx.guild.id, amount)
        await ctx.send(f"🪙 Выпал **{result}**! ВЫ ВЫИГРАЛИ +{amount} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await ctx.send(f"🪙 Выпал **{result}**! ВЫ ПРОИГРАЛИ -{amount} 💎")


@bot.command()
async def rps(ctx, amount: int, choice: str):
    """✊ Камень-ножницы-бумага"""
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    
    ready, remaining = check_cooldown(ctx.author.id, "rps")
    if not ready:
        await ctx.send(f"⏰ Подождите {remaining // 60} минут")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < amount:
        await ctx.send(f"❌ Недостаточно средств! У вас {user[4]} 💎")
        return
    
    choices = ["камень", "ножницы", "бумага"]
    choice = choice.lower()
    if choice not in choices:
        await ctx.send("❌ Выбирайте: камень, ножницы или бумага")
        return
    
    bot_choice = random.choice(choices)
    set_cooldown(ctx.author.id, "rps")
    
    if choice == bot_choice:
        await add_balance(ctx.author.id, ctx.guild.id, amount)
        result = f"🔄 Ничья! {choice} vs {bot_choice} +{amount} 💎"
    elif (choice == "камень" and bot_choice == "ножницы") or \
         (choice == "ножницы" and bot_choice == "бумага") or \
         (choice == "бумага" and bot_choice == "камень"):
        win = int(amount * 1.5)
        await add_balance(ctx.author.id, ctx.guild.id, win)
        result = f"✅ Вы победили! {choice} vs {bot_choice} +{win} 💎"
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        result = f"❌ Вы проиграли! {choice} vs {bot_choice} -{amount} 💎"
    
    await ctx.send(result)


@bot.command()
async def blackjack(ctx, amount: int):
    """🃏 Блэкджек против бота"""
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    
    ready, remaining = check_cooldown(ctx.author.id, "blackjack")
    if not ready:
        await ctx.send(f"⏰ Подождите {remaining // 60} минут")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < amount:
        await ctx.send(f"❌ Недостаточно средств! У вас {user[4]} 💎")
        return
    
    set_cooldown(ctx.author.id, "blackjack")
    
    def card_value(card):
        rank = card[:-1]
        if rank in ['J', 'Q', 'K']:
            return 10
        elif rank == 'A':
            return 11
        else:
            return int(rank)
    
    deck = FULL_DECK.copy()
    random.shuffle(deck)
    
    player_cards = [deck.pop(), deck.pop()]
    dealer_cards = [deck.pop(), deck.pop()]
    
    player_sum = sum(card_value(c) for c in player_cards)
    dealer_sum = sum(card_value(c) for c in dealer_cards)
    
    # Проверка блэкджека
    if player_sum == 21:
        win = int(amount * 2.5)
        await add_balance(ctx.author.id, ctx.guild.id, win)
        await ctx.send(f"🃏 **БЛЭКДЖЕК!** Ваши карты: {', '.join(player_cards)} = 21\n+{win} 💎")
        return
    
    # Простая логика: бот тянет до 17
    while dealer_sum < 17:
        dealer_cards.append(deck.pop())
        dealer_sum = sum(card_value(c) for c in dealer_cards)
        if dealer_sum > 21:
            for i, c in enumerate(dealer_cards):
                if c.endswith('A') and dealer_sum > 21:
                    dealer_sum -= 10
    
    # Проверка перебора у игрока
    if player_sum > 21:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await ctx.send(f"🃏 **ПЕРЕБОР!** Ваши карты: {', '.join(player_cards)} = {player_sum}\n-{amount} 💎")
        return
    
    # Определение победителя
    if dealer_sum > 21 or player_sum > dealer_sum:
        win = int(amount * 1.5)
        await add_balance(ctx.author.id, ctx.guild.id, win)
        result = f"✅ **ВЫ ПОБЕДИЛИ!**\nВаши карты: {', '.join(player_cards)} = {player_sum}\nКарты дилера: {', '.join(dealer_cards)} = {dealer_sum}\n+{win} 💎"
    elif player_sum < dealer_sum:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        result = f"❌ **ВЫ ПРОИГРАЛИ!**\nВаши карты: {', '.join(player_cards)} = {player_sum}\nКарты дилера: {', '.join(dealer_cards)} = {dealer_sum}\n-{amount} 💎"
    else:
        result = f"🔄 **НИЧЬЯ!**\nВаши карты: {', '.join(player_cards)} = {player_sum}\nКарты дилера: {', '.join(dealer_cards)} = {dealer_sum}"
    
    await ctx.send(result)


@bot.command()
async def rob(ctx, member: discord.Member):
    """🔫 Ограбить пользователя"""
    if member.id == ctx.author.id:
        await ctx.send("❌ Нельзя ограбить себя")
        return
    
    ready, remaining = check_cooldown(ctx.author.id, "rob")
    if not ready:
        await ctx.send(f"⏰ Подождите {remaining // 3600} часов")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    target = await get_user(member.id, ctx.guild.id)
    
    if target[4] < 10:
        await ctx.send(f"❌ У {member.mention} слишком мало денег для грабежа!")
        return
    
    set_cooldown(ctx.author.id, "rob")
    
    if random.random() < WIN_CHANCE["rob"]:
        stolen = min(random.randint(10, int(target[4] * 0.3)), 500)
        await add_balance(ctx.author.id, ctx.guild.id, stolen)
        await add_balance(member.id, ctx.guild.id, -stolen)
        await ctx.send(f"✅ Вы ограбили {member.mention} и украли {stolen} 💎!")
    else:
        caught_penalty = random.randint(50, 200)
        await add_balance(ctx.author.id, ctx.guild.id, -caught_penalty)
        await ctx.send(f"❌ Вас поймали! Штраф {caught_penalty} 💎")
# ========== СООБЩЕНИЕ 6 - ФЕРМА (ПОЛНОСТЬЮ) ==========

@bot.command()
async def farm(ctx):
    """🌾 Показать ферму"""
    user = await get_user(ctx.author.id, ctx.guild.id)
    crops = json.loads(user[29] if len(user) > 29 else "[]")
    
    if not crops:
        embed = discord.Embed(title="🌾 ФЕРМА", description="У вас ничего не посажено!", color=discord.Color.green())
        embed.add_field(name="📋 Как играть", value="`j.plant <культура>` - посадить\n`j.harvest <культура>` - собрать\n`j.shop` - купить семена", inline=False)
        embed.add_field(name="🌱 Доступные культуры", value="пшеница, кукуруза, томат, картофель, морковь, роза, кактус, подсолнух, тыква, арбуз", inline=False)
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(title=f"🌾 ФЕРМА | {ctx.author.display_name}", color=discord.Color.green())
    now = time.time()
    
    ready_to_harvest = []
    growing = []
    
    for crop_data in crops:
        name, plant_time, rarity = crop_data.split("|")
        plant_time = float(plant_time)
        grow_time = SEEDS[name]["grow_time"]
        remaining = grow_time - (now - plant_time)
        
        if remaining <= 0:
            ready_to_harvest.append((name, rarity))
        else:
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            growing.append(f"{SEEDS[name].get('emoji', '🌱')} {name} ({rarity}) - {hours}ч {mins}мин")
    
    if ready_to_harvest:
        harvest_text = "\n".join([f"✅ {SEEDS[n].get('emoji', '🌾')} {n} ({r}) - ГОТОВО! `j.harvest {n}`" for n, r in ready_to_harvest[:10]])
        embed.add_field(name="🌾 ГОТОВО К СБОРУ", value=harvest_text, inline=False)
    
    if growing:
        grow_text = "\n".join(growing[:10])
        embed.add_field(name="🌱 РАСТЁТ", value=grow_text, inline=False)
    
    if len(crops) > 10:
        embed.set_footer(text=f"Всего культур: {len(crops)}")
    
    await ctx.send(embed=embed)


@bot.command()
async def plant(ctx, crop: str = None, amount: int = 1):
    """🌱 Посадить культуру"""
    if not crop or crop not in SEEDS:
        await ctx.send(f"❌ Культура не найдена! Доступно: {', '.join(SEEDS.keys())}")
        return
    
    if amount < 1 or amount > 10:
        await ctx.send("❌ Можно посадить от 1 до 10 культур за раз")
        return
    
    crop_data = SEEDS[crop]
    total_price = crop_data["price"] * amount
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < total_price:
        await ctx.send(f"❌ Недостаточно средств! Нужно {total_price} 💎")
        return
    
    # Проверяем лимит грядок (максимум 25)
    crops = json.loads(user[29] if len(user) > 29 else "[]")
    if len(crops) + amount > 25:
        await ctx.send("❌ У вас максимум 25 грядок! Соберите урожай, чтобы освободить место")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -total_price)
    
    # Определяем редкость для каждой посадки
    for _ in range(amount):
        weights = crop_data["rarity_weights"]
        rarity = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        crops.append(f"{crop}|{time.time()}|{rarity}")
    
    await update_user(ctx.author.id, ctx.guild.id, crops=json.dumps(crops))
    
    rarity_emoji = {"обычный": "🟢", "редкий": "🔵", "эпический": "🟣", "легендарный": "🟠"}
    await ctx.send(f"✅ Посажено **{amount}** {crop} {rarity_emoji.get(rarity, '')} за {total_price} 💎!")


@bot.command()
async def harvest(ctx, crop: str = None):
    """🌾 Собрать урожай"""
    if not crop or crop not in SEEDS:
        await ctx.send(f"❌ Культура не найдена! Доступно: {', '.join(SEEDS.keys())}")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    crops = json.loads(user[29] if len(user) > 29 else "[]")
    
    now = time.time()
    harvested = []
    total_earn = 0
    remaining_crops = []
    
    for crop_data in crops:
        name, plant_time, rarity = crop_data.split("|")
        plant_time = float(plant_time)
        
        if name == crop:
            grow_time = SEEDS[name]["grow_time"]
            if now - plant_time >= grow_time:
                # Собираем
                base_price = SEEDS[name]["base_price"]
                multiplier = RARITY_MULTIPLIERS.get(rarity, 1.0)
                earn = int(base_price * multiplier)
                total_earn += earn
                harvested.append((name, rarity, earn))
            else:
                remaining_crops.append(crop_data)
        else:
            remaining_crops.append(crop_data)
    
    if not harvested:
        await ctx.send(f"❌ Нет готового урожая {crop}! Используйте `j.farm` для проверки")
        return
    
    await update_user(ctx.author.id, ctx.guild.id, crops=json.dumps(remaining_crops))
    await add_balance(ctx.author.id, ctx.guild.id, total_earn)
    
    rarity_emoji = {"обычный": "🟢", "редкий": "🔵", "эпический": "🟣", "легендарный": "🟠"}
    harvest_text = "\n".join([f"{rarity_emoji.get(r, '')} {n} ({r}) +{e} 💎" for n, r, e in harvested[:10]])
    
    embed = discord.Embed(title="🌾 СБОР УРОЖАЯ", color=discord.Color.gold())
    embed.add_field(name="📦 Собрано", value=harvest_text, inline=False)
    embed.add_field(name="💰 Всего", value=f"{total_earn} 💎", inline=True)
    await ctx.send(embed=embed)


@bot.command()
async def sell_crop(ctx, crop: str = None, amount: str = "all"):
    """💰 Продать урожай из инвентаря"""
    if not crop or crop not in SEEDS:
        await ctx.send(f"❌ Культура не найдена!")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    inventory = json.loads(user[19] if len(user) > 19 else "[]")
    
    crop_items = [i for i in inventory if i.startswith(f"harvest_{crop}")]
    if not crop_items:
        await ctx.send(f"❌ У вас нет {crop} в инвентаре!")
        return
    
    if amount == "all":
        sell_count = len(crop_items)
    else:
        sell_count = min(int(amount), len(crop_items))
    
    total_price = 0
    for _ in range(sell_count):
        item = crop_items.pop(0)
        _, _, rarity = item.split("|")
        multiplier = RARITY_MULTIPLIERS.get(rarity, 1.0)
        price = int(SEEDS[crop]["base_price"] * multiplier)
        total_price += price
        inventory.remove(item)
    
    await add_balance(ctx.author.id, ctx.guild.id, total_price)
    await update_user(ctx.author.id, ctx.guild.id, inventory=json.dumps(inventory))
    
    await ctx.send(f"✅ Продано {sell_count} {crop} за {total_price} 💎!")


@bot.command()
async def craft_pot(ctx):
    """🏺 Скрафтить горшок для фермы (нужно 100 💎)"""
    user = await get_user(ctx.author.id, ctx.guild.id)
    
    if user[4] < 100:
        await ctx.send("❌ Для крафта горшка нужно 100 💎")
        return
    
    pots = user[28] if len(user) > 28 else 0
    if pots >= 25:
        await ctx.send("❌ У вас уже максимум горшков (25)!")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -100)
    await update_user(ctx.author.id, ctx.guild.id, pots=pots + 1)
    
    await ctx.send(f"✅ Вы скрафтили горшок! Теперь у вас {pots + 1}/25 горшков")


@bot.command()
async def pots(ctx):
    """🏺 Показать количество горшков"""
    user = await get_user(ctx.author.id, ctx.guild.id)
    pots = user[28] if len(user) > 28 else 0
    await ctx.send(f"🏺 У вас {pots}/25 горшков для фермы")

# ========== СООБЩЕНИЕ 7 - ТИКЕТЫ (ПОЛНОСТЬЮ) ==========

class CreateTicketButton(Button):
    def __init__(self):
        super().__init__(label="🎫 Создать тикет", style=discord.ButtonStyle.primary, emoji="🎫")
    
    async def callback(self, interaction: discord.Interaction):
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            return await interaction.response.send_message("❌ Категория для тикетов не настроена!", ephemeral=True)
        
        # Проверка на существующий тикет
        for channel in category.channels:
            if channel.topic and f"owner:{interaction.user.id}" in channel.topic:
                return await interaction.response.send_message("❌ У вас уже есть открытый тикет!", ephemeral=True)
        
        # Права доступа
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True)
        }
        
        for role_id in SUPPORT_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True, manage_channels=True)
        
        # Создание канала
        ticket_num = len([c for c in category.channels if c.name.startswith("тикет-")]) + 1
        channel = await category.create_text_channel(
            name=f"тикет-{ticket_num}",
            overwrites=overwrites,
            topic=f"owner:{interaction.user.id}|created:{int(time.time())}"
        )
        
        active_tickets[channel.id] = {"creator": interaction.user.id, "created_at": time.time()}
        
        # Приветственное сообщение
        embed = discord.Embed(
            title="🎫 ТИКЕТ СОЗДАН",
            description=f"{interaction.user.mention}, опишите вашу проблему.\n\nПоддержка скоро ответит.",
            color=discord.Color.green()
        )
        embed.add_field(name="📌 Правила", value="1. Опишите проблему подробно\n2. Не спамьте\n3. Дождитесь ответа", inline=False)
        
        view = View()
        view.add_item(CloseTicketButton(channel.id, interaction.user.id))
        view.add_item(ClaimTicketButton(channel.id, interaction.user.id))
        
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Тикет создан! Перейдите в {channel.mention}", ephemeral=True)


class CloseTicketButton(Button):
    def __init__(self, channel_id, creator_id):
        super().__init__(label="🔒 Закрыть тикет", style=discord.ButtonStyle.danger, emoji="🔒")
        self.channel_id = channel_id
        self.creator_id = creator_id
    
    async def callback(self, interaction: discord.Interaction):
        # Проверка прав
        is_support = any(
            interaction.guild.get_role(rid) in interaction.user.roles 
            for rid in SUPPORT_ROLE_IDS if interaction.guild.get_role(rid)
        )
        is_creator = interaction.user.id == self.creator_id
        
        if not (is_support or is_creator):
            return await interaction.response.send_message("❌ Только создатель тикета или поддержка могут закрыть тикет!", ephemeral=True)
        
        channel = interaction.channel
        await interaction.response.send_message("⏳ Закрытие тикета...", ephemeral=True)
        
        # Сбор истории
        messages = []
        async for msg in channel.history(limit=500, oldest_first=True):
            if msg.author.bot and "тикет" in msg.content.lower():
                continue
            timestamp = msg.created_at.strftime("%d.%m.%Y %H:%M:%S")
            attachments = " [📎]" if msg.attachments else ""
            messages.append(f"[{timestamp}] {msg.author.name}: {msg.content[:200]}{attachments}")
        
        # Сохранение лога
        os.makedirs("ticket_logs", exist_ok=True)
        filename = f"ticket_logs/ticket_{channel.name}_{int(time.time())}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"=== ТИКЕТ {channel.name} ===\n")
            f.write(f"Создатель: {self.creator_id}\n")
            f.write(f"Закрыл: {interaction.user.name} (ID: {interaction.user.id})\n")
            f.write(f"Дата закрытия: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            f.write(f"Всего сообщений: {len(messages)}\n\n")
            f.write("\n".join(messages))
        
        # Отправка лога в канал логов
        log_channel = bot.get_channel(LOGS_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="📋 ЗАКРЫТ ТИКЕТ", color=discord.Color.red())
            embed.add_field(name="📌 Канал", value=channel.mention, inline=True)
            embed.add_field(name="👤 Закрыл", value=interaction.user.mention, inline=True)
            embed.add_field(name="📊 Сообщений", value=str(len(messages)), inline=True)
            await log_channel.send(embed=embed)
            await log_channel.send(file=discord.File(filename))
        
        # Удаление канала
        await channel.delete()
        os.remove(filename)


class ClaimTicketButton(Button):
    def __init__(self, channel_id, creator_id):
        super().__init__(label="✅ Принять тикет", style=discord.ButtonStyle.success, emoji="✅")
        self.channel_id = channel_id
        self.creator_id = creator_id
    
    async def callback(self, interaction: discord.Interaction):
        is_support = any(
            interaction.guild.get_role(rid) in interaction.user.roles 
            for rid in SUPPORT_ROLE_IDS if interaction.guild.get_role(rid)
        )
        
        if not is_support:
            return await interaction.response.send_message("❌ Только поддержка может принимать тикеты!", ephemeral=True)
        
        channel = bot.get_channel(self.channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
        
        # Меняем название канала
        new_name = f"принят-{channel.name.replace('тикет-', '')}"
        await channel.edit(name=new_name)
        
        embed = discord.Embed(
            title="✅ ТИКЕТ ПРИНЯТ",
            description=f"Тикет принят {interaction.user.mention}\nОтветственный: {interaction.user.display_name}",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
        
        # Обновляем кнопки - убираем кнопку "Принять"
        view = View()
        view.add_item(CloseTicketButton(self.channel_id, self.creator_id))
        
        async for msg in channel.history(limit=10):
            if msg.author == bot.user and msg.components:
                await msg.edit(view=view)
                break
        
        await interaction.response.send_message("✅ Тикет принят!", ephemeral=True)


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    """🎫 Настроить систему тикетов (админ)"""
    channel = ctx.channel
    
    # Удаляем старые сообщения бота
    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            await msg.delete()
    
    embed = discord.Embed(
        title="🎫 СИСТЕМА ТИКЕТОВ",
        description="Нажмите на кнопку ниже, чтобы создать тикет.\n\n"
                    "Поддержка ответит вам в личном канале.\n"
                    "Не создавайте тикеты по пустякам!",
        color=discord.Color.blue()
    )
    
    view = View()
    view.add_item(CreateTicketButton())
    
    await channel.send(embed=embed, view=view)
    await ctx.send("✅ Система тикетов настроена!", delete_after=5)


@bot.command()
async def close(ctx):
    """🔒 Закрыть текущий тикет"""
    if not ctx.channel.category or ctx.channel.category.id != TICKET_CATEGORY_ID:
        return await ctx.send("❌ Эта команда доступна только в каналах тикетов!")
    
    if not ctx.channel.name.startswith(("тикет-", "принят-")):
        return await ctx.send("❌ Это не канал тикета!")
    
    # Определяем создателя
    creator_id = None
    if ctx.channel.topic:
        for part in ctx.channel.topic.split("|"):
            if part.startswith("owner:"):
                creator_id = int(part.split(":")[1])
                break
    
    is_support = any(
        ctx.guild.get_role(rid) in ctx.author.roles 
        for rid in SUPPORT_ROLE_IDS if ctx.guild.get_role(rid)
    )
    is_creator = ctx.author.id == creator_id
    
    if not (is_support or is_creator):
        return await ctx.send("❌ Только создатель тикета или поддержка могут закрыть тикет!")
    
    # Подтверждение
    await ctx.send("⚠️ Вы уверены? Напишите `да` в течение 10 секунд")
    
    def check(m):
        return m.author == ctx.author and m.content.lower() == "да" and m.channel == ctx.channel
    
    try:
        await bot.wait_for('message', timeout=10, check=check)
    except asyncio.TimeoutError:
        return await ctx.send("❌ Отменено")
    
    # Сбор истории
    messages = []
    async for msg in ctx.channel.history(limit=500, oldest_first=True):
        if msg.author.bot and "тикет" in msg.content.lower():
            continue
        messages.append(f"[{msg.created_at.strftime('%d.%m.%Y %H:%M:%S')}] {msg.author.name}: {msg.content[:200]}")
    
    os.makedirs("ticket_logs", exist_ok=True)
    filename = f"ticket_logs/ticket_{ctx.channel.name}_{int(time.time())}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"=== ТИКЕТ {ctx.channel.name} ===\n")
        f.write(f"Создатель: {creator_id}\n")
        f.write(f"Закрыл: {ctx.author.name}\n")
        f.write(f"Всего сообщений: {len(messages)}\n\n")
        f.write("\n".join(messages))
    
    log_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if log_channel:
        await log_channel.send(file=discord.File(filename))
    
    await ctx.channel.delete()
    os.remove(filename)


@bot.command()
async def tickets(ctx):
    """📋 Список активных тикетов (только поддержка)"""
    is_support = any(
        ctx.guild.get_role(rid) in ctx.author.roles 
        for rid in SUPPORT_ROLE_IDS if ctx.guild.get_role(rid)
    )
    
    if not is_support:
        return await ctx.send("❌ Только поддержка может просматривать список тикетов!")
    
    category = ctx.guild.get_channel(TICKET_CATEGORY_ID)
    if not category:
        return await ctx.send("❌ Категория тикетов не найдена!")
    
    tickets_list = []
    for channel in category.channels:
        if channel.name.startswith(("тикет-", "принят-")):
            creator_id = None
            if channel.topic:
                for part in channel.topic.split("|"):
                    if part.startswith("owner:"):
                        creator_id = int(part.split(":")[1])
                        break
            
            creator = ctx.guild.get_member(creator_id) if creator_id else None
            tickets_list.append(f"{channel.mention} - Создатель: {creator.mention if creator else 'Неизвестен'}")
    
    if not tickets_list:
        await ctx.send("📭 Нет активных тикетов")
        return
    
    embed = discord.Embed(title="📋 АКТИВНЫЕ ТИКЕТЫ", color=discord.Color.blue())
    embed.add_field(name=f"Всего: {len(tickets_list)}", value="\n".join(tickets_list[:25]), inline=False)
    await ctx.send(embed=embed)
# ========== СООБЩЕНИЕ 8 - РОЗЫГРЫШИ (GIVEAWAY) ==========

@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx, duration: str, winners: int, *, prize: str):
    """🎁 Создать розыгрыш (админ)
    Пример: j.giveaway 1ч 5 NITRO"""
    
    # Парсим время
    time_units = {"s": 1, "м": 60, "ч": 3600, "д": 86400}
    duration_seconds = 0
    current_num = ""
    
    for char in duration:
        if char.isdigit():
            current_num += char
        elif char in time_units:
            if current_num:
                duration_seconds += int(current_num) * time_units[char]
                current_num = ""
    
    if duration_seconds <= 0:
        await ctx.send("❌ Неверный формат времени! Пример: 1ч, 30м, 2д")
        return
    
    if winners < 1 or winners > 10:
        await ctx.send("❌ Количество победителей от 1 до 10")
        return
    
    end_time = datetime.now() + timedelta(seconds=duration_seconds)
    
    embed = discord.Embed(
        title="🎁 РОЗЫГРЫШ!",
        description=f"**Приз:** {prize}\n"
                    f"**Победителей:** {winners}\n"
                    f"**Окончание:** <t:{int(end_time.timestamp())}:R>\n\n"
                    f"Нажмите на 🎉 для участия!",
        color=discord.Color.gold()
    )
    
    message = await ctx.send(embed=embed)
    await message.add_reaction("🎉")
    
    # Сохраняем в базу
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('''INSERT INTO giveaways (channel_id, message_id, prize, winners, end_time, entries)
                           VALUES (?,?,?,?,?,?)''',
                         (ctx.channel.id, message.id, prize, winners, end_time.isoformat(), json.dumps([])))
        await db.commit()
    
    await ctx.send(f"✅ Розыгрыш создан! Окончание <t:{int(end_time.timestamp())}:R>", delete_after=5)


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    # Проверка на розыгрыш
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM giveaways WHERE message_id=? AND ended=0', (payload.message_id,))
        giveaway = await cur.fetchone()
        
        if not giveaway:
            return
        
        if str(payload.emoji) != "🎉":
            return
        
        entries = json.loads(giveaway[6])
        if payload.user_id not in entries:
            entries.append(payload.user_id)
            await db.execute('UPDATE giveaways SET entries=? WHERE message_id=?', (json.dumps(entries), payload.message_id))
            await db.commit()


@tasks.loop(seconds=10)
async def check_giveaways():
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM giveaways WHERE ended=0')
        giveaways = await cur.fetchall()
        
        now = datetime.now()
        
        for g in giveaways:
            end_time = datetime.fromisoformat(g[5])
            if now >= end_time:
                # Завершаем розыгрыш
                channel = bot.get_channel(g[1])
                if not channel:
                    continue
                
                try:
                    message = await channel.fetch_message(g[2])
                except:
                    continue
                
                entries = json.loads(g[6])
                winners_count = min(g[4], len(entries))
                
                if winners_count > 0 and entries:
                    winners = random.sample(entries, winners_count)
                    winner_mentions = [f"<@{w}>" for w in winners]
                    
                    embed = discord.Embed(
                        title="🏆 РОЗЫГРЫШ ЗАВЕРШЁН!",
                        description=f"**Приз:** {g[3]}\n"
                                    f"**Победители:** {', '.join(winner_mentions)}\n\n"
                                    f"Поздравляем!",
                        color=discord.Color.green()
                    )
                    
                    await message.edit(embed=embed)
                    await channel.send(f"🎉 Поздравляем {', '.join(winner_mentions)}! Вы выиграли **{g[3]}**!")
                else:
                    embed = discord.Embed(
                        title="❌ РОЗЫГРЫШ ЗАВЕРШЁН",
                        description=f"**Приз:** {g[3]}\n"
                                    f"Недостаточно участников!",
                        color=discord.Color.red()
                    )
                    await message.edit(embed=embed)
                
                await db.execute('UPDATE giveaways SET ended=1 WHERE message_id=?', (g[2],))
                await db.commit()


@bot.command()
@commands.has_permissions(administrator=True)
async def reroll(ctx, message_id: int):
    """🎲 Перетянуть победителя в розыгрыше"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM giveaways WHERE message_id=? AND ended=1', (message_id,))
        giveaway = await cur.fetchone()
        
        if not giveaway:
            await ctx.send("❌ Розыгрыш не найден или ещё активен")
            return
        
        entries = json.loads(giveaway[6])
        if len(entries) < 1:
            await ctx.send("❌ Нет участников для перетягивания")
            return
        
        new_winner = random.choice(entries)
        await ctx.send(f"🎉 Новый победитель: <@{new_winner}>! Приз: **{giveaway[3]}**")


@bot.command()
@commands.has_permissions(administrator=True)
async def end_giveaway(ctx, message_id: int):
    """🏁 Принудительно завершить розыгрыш"""
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE giveaways SET end_time=? WHERE message_id=?', 
                        (datetime.now().isoformat(), message_id))
        await db.commit()
    
    await ctx.send(f"✅ Розыгрыш {message_id} будет завершён в ближайшее время")

# ========== СООБЩЕНИЕ 9 - ИДЕИ И ПРЕДЛОЖЕНИЯ ==========

class SuggestionModal(Modal):
    def __init__(self):
        super().__init__(title="📝 Отправить идею")
        
        self.title_input = TextInput(
            label="Заголовок идеи",
            placeholder="Краткое описание...",
            required=True,
            max_length=100
        )
        self.add_item(self.title_input)
        
        self.desc_input = TextInput(
            label="Описание",
            placeholder="Подробно опишите вашу идею...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.desc_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('INSERT INTO suggestions (user_id, guild_id, suggestion, date) VALUES (?,?,?,?)',
                                  (interaction.user.id, interaction.guild.id, f"{self.title_input.value}\n\n{self.desc_input.value}", 
                                   datetime.now().isoformat()))
            await db.commit()
            suggestion_id = cur.lastrowid
        
        # Отправляем в канал ревью
        review_channel = bot.get_channel(IDEA_REVIEW_CHANNEL_ID)
        if review_channel:
            embed = discord.Embed(
                title=f"💡 НОВАЯ ИДЕЯ #{suggestion_id}",
                description=f"**{self.title_input.value}**\n\n{self.desc_input.value}",
                color=discord.Color.blue()
            )
            embed.add_field(name="👤 Автор", value=interaction.user.mention, inline=True)
            embed.add_field(name="📅 Дата", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
            
            view = View()
            view.add_item(AcceptIdeaButton(suggestion_id))
            view.add_item(DenyIdeaButton(suggestion_id))
            
            await review_channel.send(embed=embed, view=view)
        
        await interaction.response.send_message("✅ Ваша идея отправлена на рассмотрение!", ephemeral=True)


class AcceptIdeaButton(Button):
    def __init__(self, suggestion_id):
        super().__init__(label="✅ Принять", style=discord.ButtonStyle.success)
        self.suggestion_id = suggestion_id
    
    async def callback(self, interaction: discord.Interaction):
        is_support = any(
            interaction.guild.get_role(rid) in interaction.user.roles 
            for rid in SUPPORT_ROLE_IDS if interaction.guild.get_role(rid)
        )
        
        if not is_support:
            return await interaction.response.send_message("❌ Нет прав!", ephemeral=True)
        
        async with aiosqlite.connect("justice.db") as db:
            await db.execute('UPDATE suggestions SET status="accepted", verdict=? WHERE id=?', 
                            (f"Принято {interaction.user.name}", self.suggestion_id))
            await db.commit()
            
            cur = await db.execute('SELECT user_id, suggestion FROM suggestions WHERE id=?', (self.suggestion_id,))
            suggestion = await cur.fetchone()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="✅ Вердикт", value=f"Принято {interaction.user.mention}", inline=False)
        await interaction.message.edit(embed=embed, view=None)
        
        # Уведомляем автора
        user = await bot.fetch_user(suggestion[0])
        if user:
            await user.send(f"✅ Ваша идея **#{self.suggestion_id}** была принята!")
        
        await interaction.response.send_message("✅ Идея принята!", ephemeral=True)


class DenyIdeaButton(Button):
    def __init__(self, suggestion_id):
        super().__init__(label="❌ Отклонить", style=discord.ButtonStyle.danger)
        self.suggestion_id = suggestion_id
    
    async def callback(self, interaction: discord.Interaction):
        is_support = any(
            interaction.guild.get_role(rid) in interaction.user.roles 
            for rid in SUPPORT_ROLE_IDS if interaction.guild.get_role(rid)
        )
        
        if not is_support:
            return await interaction.response.send_message("❌ Нет прав!", ephemeral=True)
        
        # Модальное окно для причины
        modal = DenyReasonModal(self.suggestion_id)
        await interaction.response.send_modal(modal)


class DenyReasonModal(Modal):
    def __init__(self, suggestion_id):
        super().__init__(title="❌ Причина отклонения")
        self.suggestion_id = suggestion_id
        
        self.reason_input = TextInput(
            label="Причина",
            placeholder="Почему идея отклонена?",
            required=True,
            max_length=500
        )
        self.add_item(self.reason_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        async with aiosqlite.connect("justice.db") as db:
            await db.execute('UPDATE suggestions SET status="denied", verdict=? WHERE id=?', 
                            (self.reason_input.value, self.suggestion_id))
            await db.commit()
            
            cur = await db.execute('SELECT user_id, suggestion FROM suggestions WHERE id=?', (self.suggestion_id,))
            suggestion = await cur.fetchone()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="❌ Вердикт", value=f"Отклонено {interaction.user.mention}\nПричина: {self.reason_input.value}", inline=False)
        await interaction.message.edit(embed=embed, view=None)
        
        # Уведомляем автора
        user = await bot.fetch_user(suggestion[0])
        if user:
            await user.send(f"❌ Ваша идея **#{self.suggestion_id}** была отклонена.\nПричина: {self.reason_input.value}")
        
        await interaction.response.send_message("❌ Идея отклонена!", ephemeral=True)


@bot.command()
async def suggest(ctx):
    """💡 Предложить идею"""
    modal = SuggestionModal()
    await ctx.send("📝 Отправьте вашу идею:", view=modal)


@bot.command()
async def ideas(ctx, status: str = "pending"):
    """📋 Список идей (pending/accepted/denied)"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT id, suggestion, status FROM suggestions WHERE guild_id=? AND status=? LIMIT 20', 
                              (ctx.guild.id, status))
        suggestions = await cur.fetchall()
    
    if not suggestions:
        await ctx.send(f"📭 Нет идей со статусом **{status}**")
        return
    
    embed = discord.Embed(title=f"💡 ИДЕИ | {status.upper()}", color=discord.Color.blue())
    for sid, suggestion, _ in suggestions:
        title = suggestion.split("\n")[0][:50]
        embed.add_field(name=f"#{sid}", value=title, inline=True)
    
    embed.set_footer(text="j.idea <id> - посмотреть детали")
    await ctx.send(embed=embed)


@bot.command()
async def idea(ctx, idea_id: int):
    """🔍 Посмотреть идею по ID"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM suggestions WHERE id=? AND guild_id=?', (idea_id, ctx.guild.id))
        idea = await cur.fetchone()
    
    if not idea:
        await ctx.send(f"❌ Идея #{idea_id} не найдена")
        return
    
    embed = discord.Embed(title=f"💡 ИДЕЯ #{idea_id}", description=idea[3], color=discord.Color.blue())
    embed.add_field(name="👤 Автор", value=f"<@{idea[1]}>", inline=True)
    embed.add_field(name="📊 Статус", value=idea[4], inline=True)
    if idea[5]:
        embed.add_field(name="📝 Вердикт", value=idea[5], inline=False)
    embed.add_field(name="📅 Дата", value=f"<t:{int(datetime.fromisoformat(idea[6]).timestamp())}:R>", inline=True)
    
    await ctx.send(embed=embed)

# ========== СООБЩЕНИЕ 10 - СТО ЛОТО ==========

stoloto_active = False
stoloto_tickets = []
stoloto_numbers = []
stoloto_jackpot = STOLOTO_JACKPOT_MIN
stoloto_end_time = None


@bot.command()
async def stoloto_buy(ctx, numbers: str = None):
    """🎫 Купить билет Столото (50 💎)"""
    global stoloto_tickets
    
    if not stoloto_active:
        await ctx.send("❌ Розыгрыш Столото не активен! Используйте `j.stoloto_start` чтобы начать")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < STOLOTO_TICKET_PRICE:
        await ctx.send(f"❌ Недостаточно средств! Билет стоит {STOLOTO_TICKET_PRICE} 💎")
        return
    
    # Проверяем, есть ли уже билет
    if any(t["user_id"] == ctx.author.id for t in stoloto_tickets):
        await ctx.send("❌ У вас уже есть билет на этот розыгрыш!")
        return
    
    # Генерируем числа если не указаны
    if numbers:
        try:
            nums = [int(x.strip()) for x in numbers.split(",")]
            if len(nums) != 6:
                await ctx.send("❌ Нужно указать 6 чисел через запятую! Пример: `j.stoloto_buy 1,2,3,4,5,6`")
                return
            if any(n < 1 or n > 49 for n in nums):
                await ctx.send("❌ Числа должны быть от 1 до 49")
                return
            if len(set(nums)) != 6:
                await ctx.send("❌ Числа не должны повторяться")
                return
            ticket_numbers = nums
        except:
            await ctx.send("❌ Неверный формат! Пример: `j.stoloto_buy 1,2,3,4,5,6`")
            return
    else:
        ticket_numbers = sorted(random.sample(range(1, 50), 6))
    
    await add_balance(ctx.author.id, ctx.guild.id, -STOLOTO_TICKET_PRICE)
    
    stoloto_tickets.append({
        "user_id": ctx.author.id,
        "numbers": ticket_numbers,
        "buy_time": time.time()
    })
    
    embed = discord.Embed(title="🎫 БИЛЕТ СТОЛОТО", color=discord.Color.green())
    embed.add_field(name="📊 Ваши числа", value=", ".join(map(str, ticket_numbers)), inline=False)
    embed.add_field(name="💰 Стоимость", value=f"{STOLOTO_TICKET_PRICE} 💎", inline=True)
    embed.add_field(name="🏆 Джекпот", value=f"{stoloto_jackpot} 💎", inline=True)
    embed.set_footer(text=f"Всего билетов: {len(stoloto_tickets)}")
    
    await ctx.send(embed=embed)


@bot.command()
async def stoloto_jackpot(ctx):
    """🏆 Показать текущий джекпот Столото"""
    embed = discord.Embed(title="🎫 СТОЛОТО ДЖЕКПОТ", color=discord.Color.gold())
    embed.add_field(name="💰 Текущий джекпот", value=f"{stoloto_jackpot} 💎", inline=True)
    embed.add_field(name="🎫 Билетов продано", value=f"{len(stoloto_tickets)}", inline=True)
    
    if stoloto_end_time:
        embed.add_field(name="⏰ Розыгрыш", value=f"<t:{int(stoloto_end_time)}:R>", inline=True)
    
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def stoloto_start(ctx, duration_minutes: int = 60):
    """🎫 Запустить розыгрыш Столото (админ)"""
    global stoloto_active, stoloto_tickets, stoloto_end_time
    
    if stoloto_active:
        await ctx.send("❌ Розыгрыш уже активен! Используйте `j.stoloto_draw` для розыгрыша")
        return
    
    stoloto_active = True
    stoloto_tickets = []
    stoloto_end_time = time.time() + (duration_minutes * 60)
    
    embed = discord.Embed(
        title="🎫 СТОЛОТО ЗАПУЩЕНО!",
        description=f"Розыгрыш состоится через **{duration_minutes}** минут!\n"
                    f"Билет стоит **{STOLOTO_TICKET_PRICE}** 💎\n"
                    f"Джекпот: **{stoloto_jackpot}** 💎\n\n"
                    f"**Как играть:**\n"
                    f"`j.stoloto_buy` - купить билет со случайными числами\n"
                    f"`j.stoloto_buy 1,2,3,4,5,6` - купить билет с указанными числами\n"
                    f"`j.stoloto_tickets` - посмотреть свои билеты",
        color=discord.Color.gold()
    )
    embed.add_field(name="⏰ Розыгрыш", value=f"<t:{int(stoloto_end_time)}:R>", inline=False)
    
    await ctx.send(embed=embed)
    
    # Автоматический розыгрыш через N минут
    await asyncio.sleep(duration_minutes * 60)
    if stoloto_active:
        await stoloto_draw(ctx)


@bot.command()
@commands.has_permissions(administrator=True)
async def stoloto_draw(ctx):
    """🎲 Провести розыгрыш Столото (админ)"""
    global stoloto_active, stoloto_tickets, stoloto_jackpot
    
    if not stoloto_active:
        await ctx.send("❌ Нет активного розыгрыша")
        return
    
    if len(stoloto_tickets) == 0:
        await ctx.send("❌ Нет билетов! Джекпот переносится на следующий розыгрыш")
        stoloto_active = False
        return
    
    # Генерируем выигрышные числа
    winning_numbers = sorted(random.sample(range(1, 50), 6))
    
    # Ищем победителей
    winners = []
    for ticket in stoloto_tickets:
        matches = len(set(ticket["numbers"]) & set(winning_numbers))
        if matches >= 3:
            winners.append({
                "user_id": ticket["user_id"],
                "matches": matches,
                "numbers": ticket["numbers"]
            })
    
    # Рассчитываем призы
    if winners:
        # Сортируем по количеству совпадений
        winners.sort(key=lambda x: x["matches"], reverse=True)
        top_winner = winners[0]
        
        # Главный приз (джекпот) за 6 совпадений
        if top_winner["matches"] == 6:
            prize = stoloto_jackpot
            await add_balance(top_winner["user_id"], ctx.guild.id, prize)
            
            result_embed = discord.Embed(
                title="🎉 ДЖЕКПОТ! 🎉",
                description=f"Победитель: <@{top_winner['user_id']}>\n"
                            f"**Выигрыш: {prize} 💎**",
                color=discord.Color.gold()
            )
        else:
            # Утешительные призы
            prize = 100 * top_winner["matches"]
            await add_balance(top_winner["user_id"], ctx.guild.id, prize)
            
            result_embed = discord.Embed(
                title="🎫 СТОЛОТО - РЕЗУЛЬТАТЫ",
                description=f"**Выигрышные числа:** {', '.join(map(str, winning_numbers))}\n\n"
                            f"**Победитель:** <@{top_winner['user_id']}>\n"
                            f"**Совпадений:** {top_winner['matches']}\n"
                            f"**Выигрыш:** {prize} 💎",
                color=discord.Color.green()
            )
        
        # Сохраняем в историю
        async with aiosqlite.connect("justice.db") as db:
            await db.execute('INSERT INTO stoloto (date, winner_id, prize, numbers) VALUES (?,?,?,?)',
                            (datetime.now().isoformat(), top_winner["user_id"], prize, json.dumps(winning_numbers)))
            await db.commit()
        
        # Сбрасываем джекпот
        stoloto_jackpot = STOLOTO_JACKPOT_MIN
        
    else:
        result_embed = discord.Embed(
            title="😔 СТОЛОТО - НЕТ ПОБЕДИТЕЛЯ",
            description=f"**Выигрышные числа:** {', '.join(map(str, winning_numbers))}\n\n"
                        f"Никто не угадал 3 и более чисел!\n"
                        f"Джекпот увеличивается на {STOLOTO_TICKET_PRICE * len(stoloto_tickets)} 💎",
            color=discord.Color.red()
        )
        stoloto_jackpot += STOLOTO_TICKET_PRICE * len(stoloto_tickets)
    
    result_embed.add_field(name="🎫 Всего билетов", value=str(len(stoloto_tickets)), inline=True)
    result_embed.add_field(name="💰 Новый джекпот", value=f"{stoloto_jackpot} 💎", inline=True)
    
    await ctx.send(embed=result_embed)
    
    stoloto_active = False
    stoloto_tickets = []


@bot.command()
async def stoloto_tickets(ctx):
    """🎫 Показать свои билеты Столото"""
    if not stoloto_active:
        await ctx.send("❌ Нет активного розыгрыша")
        return
    
    user_tickets = [t for t in stoloto_tickets if t["user_id"] == ctx.author.id]
    
    if not user_tickets:
        await ctx.send(f"❌ У вас нет билетов! Купите: `j.stoloto_buy`")
        return
    
    embed = discord.Embed(title=f"🎫 ВАШИ БИЛЕТЫ | {ctx.author.display_name}", color=discord.Color.blue())
    for ticket in user_tickets:
        embed.add_field(name=f"Билет", value=f"Числа: {', '.join(map(str, ticket['numbers']))}", inline=False)
    
    await ctx.send(embed=embed)


@bot.command()
async def stoloto_history(ctx, limit: int = 5):
    """📜 История розыгрышей Столото"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT date, winner_id, prize, numbers FROM stoloto ORDER BY id DESC LIMIT ?', (limit,))
        history = await cur.fetchall()
    
    if not history:
        await ctx.send("📭 История розыгрышей пуста")
        return
    
    embed = discord.Embed(title="📜 ИСТОРИЯ СТОЛОТО", color=discord.Color.gold())
    for date, winner_id, prize, numbers in history:
        winner = ctx.guild.get_member(winner_id)
        winner_name = winner.display_name if winner else f"ID:{winner_id}"
        nums = json.loads(numbers)
        embed.add_field(
            name=f"📅 {datetime.fromisoformat(date).strftime('%d.%m.%Y')}",
            value=f"Победитель: {winner_name}\nПриз: {prize} 💎\nЧисла: {', '.join(map(str, nums))}",
            inline=False
        )
    
    await ctx.send(embed=embed)

# ========== СООБЩЕНИЕ 11 - МОДЕРАЦИЯ ==========

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, days: int = 7, *, reason: str = "Не указана"):
    """⚠️ Выдать предупреждение"""
    expires_at = (datetime.now() + timedelta(days=days)).isoformat()
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT INTO warnings (user_id, guild_id, moderator_id, reason, expires_at) VALUES (?,?,?,?,?)',
                        (member.id, ctx.guild.id, ctx.author.id, reason, expires_at))
        
        cur = await db.execute('SELECT COUNT(*) FROM warnings WHERE user_id=? AND guild_id=? AND datetime(expires_at) > datetime(?)',
                              (member.id, ctx.guild.id, datetime.now().isoformat()))
        count = (await cur.fetchone())[0]
        
        await db.commit()
    
    embed = discord.Embed(title="⚠️ ПРЕДУПРЕЖДЕНИЕ", color=discord.Color.orange())
    embed.add_field(name="👤 Пользователь", value=member.mention, inline=True)
    embed.add_field(name="🛡️ Модератор", value=ctx.author.mention, inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=False)
    embed.add_field(name="📊 Всего предупреждений", value=str(count), inline=True)
    embed.add_field(name="⏰ Истекает", value=f"<t:{int(datetime.fromisoformat(expires_at).timestamp())}:R>", inline=True)
    
    await ctx.send(embed=embed)
    
    # Логирование
    log_embed = discord.Embed(title="⚠️ ВЫДАНО ПРЕДУПРЕЖДЕНИЕ", color=discord.Color.orange())
    log_embed.add_field(name="👤 Пользователь", value=f"{member} ({member.id})", inline=True)
    log_embed.add_field(name="🛡️ Модератор", value=f"{ctx.author}", inline=True)
    log_embed.add_field(name="📝 Причина", value=reason, inline=True)
    await send_log(ctx.guild.id, log_embed)
    
    # Уведомление пользователя
    try:
        await member.send(f"⚠️ Вы получили предупреждение на сервере **{ctx.guild.name}**\nПричина: {reason}\nПредупреждений: {count}")
    except:
        pass


@bot.command()
async def warns(ctx, member: discord.Member = None):
    """📋 Список предупреждений"""
    target = member or ctx.author
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT id, moderator_id, reason, expires_at FROM warnings WHERE user_id=? AND guild_id=? AND datetime(expires_at) > datetime(?) ORDER BY id DESC',
                              (target.id, ctx.guild.id, datetime.now().isoformat()))
        warnings = await cur.fetchall()
    
    if not warnings:
        await ctx.send(f"📭 У {target.mention} нет активных предупреждений")
        return
    
    embed = discord.Embed(title=f"⚠️ ПРЕДУПРЕЖДЕНИЯ | {target.display_name}", color=discord.Color.orange())
    for wid, mod_id, reason, expires in warnings[:10]:
        mod = ctx.guild.get_member(mod_id)
        mod_name = mod.display_name if mod else f"ID:{mod_id}"
        embed.add_field(
            name=f"#{wid}",
            value=f"Модератор: {mod_name}\nПричина: {reason}\nИстекает: <t:{int(datetime.fromisoformat(expires).timestamp())}:R>",
            inline=False
        )
    
    if len(warnings) > 10:
        embed.set_footer(text=f"Всего предупреждений: {len(warnings)}")
    
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(kick_members=True)
async def unwarn(ctx, member: discord.Member, warn_id: int):
    """🔓 Снять предупреждение"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT id FROM warnings WHERE id=? AND user_id=? AND guild_id=?', (warn_id, member.id, ctx.guild.id))
        if not await cur.fetchone():
            await ctx.send(f"❌ Предупреждение #{warn_id} не найдено у {member.mention}")
            return
        
        await db.execute('DELETE FROM warnings WHERE id=?', (warn_id,))
        await db.commit()
    
    await ctx.send(f"✅ Снято предупреждение #{warn_id} у {member.mention}")
    
    log_embed = discord.Embed(title="🔓 СНЯТО ПРЕДУПРЕЖДЕНИЕ", color=discord.Color.green())
    log_embed.add_field(name="👤 Пользователь", value=f"{member}", inline=True)
    log_embed.add_field(name="🛡️ Модератор", value=f"{ctx.author}", inline=True)
    log_embed.add_field(name="🆔 ID варна", value=str(warn_id), inline=True)
    await send_log(ctx.guild.id, log_embed)


@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: str, *, reason: str = "Не указана"):
    """🔇 Замутить пользователя (10м, 1ч, 1д)"""
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
        await ctx.send("❌ Пример: `j.mute @user 10м` или `j.mute @user 1ч`")
        return
    
    until = datetime.now() + timedelta(seconds=seconds)
    
    await member.timeout(until, reason=reason)
    
    embed = discord.Embed(title="🔇 МУТ", color=discord.Color.red())
    embed.add_field(name="👤 Пользователь", value=member.mention, inline=True)
    embed.add_field(name="🛡️ Модератор", value=ctx.author.mention, inline=True)
    embed.add_field(name="⏰ Длительность", value=duration, inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=False)
    embed.add_field(name="⏳ До", value=f"<t:{int(until.timestamp())}:R>", inline=True)
    
    await ctx.send(embed=embed)
    
    try:
        await member.send(f"🔇 Вы были замучены на сервере **{ctx.guild.name}**\nПричина: {reason}\nДо: <t:{int(until.timestamp())}:R>")
    except:
        pass


@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member, *, reason: str = "Не указана"):
    """🔊 Снять мут"""
    await member.timeout(None, reason=reason)
    
    embed = discord.Embed(title="🔊 СНЯТ МУТ", color=discord.Color.green())
    embed.add_field(name="👤 Пользователь", value=member.mention, inline=True)
    embed.add_field(name="🛡️ Модератор", value=ctx.author.mention, inline=True)
    
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, duration: str = None, *, reason: str = "Не указана"):
    """🔨 Забанить пользователя"""
    if duration:
        time_map = {"м": 60, "ч": 3600, "д": 86400}
        seconds = 0
        num = ""
        for char in duration:
            if char.isdigit():
                num += char
            elif char in time_map and num:
                seconds += int(num) * time_map[char]
                num = ""
        
        if seconds > 0:
            await member.ban(reason=reason)
            # Авторазбан через N секунд
            async def unban_later():
                await asyncio.sleep(seconds)
                await ctx.guild.unban(member, reason="Автоматический разбан")
            asyncio.create_task(unban_later())
    else:
        await member.ban(reason=reason)
    
    embed = discord.Embed(title="🔨 БАН", color=discord.Color.dark_red())
    embed.add_field(name="👤 Пользователь", value=f"{member} ({member.id})", inline=True)
    embed.add_field(name="🛡️ Модератор", value=ctx.author.mention, inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=False)
    
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: str = "Не указана"):
    """👢 Кикнуть пользователя"""
    await member.kick(reason=reason)
    
    embed = discord.Embed(title="👢 КИК", color=discord.Color.orange())
    embed.add_field(name="👤 Пользователь", value=f"{member} ({member.id})", inline=True)
    embed.add_field(name="🛡️ Модератор", value=ctx.author.mention, inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=True)
    
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    """🗑️ Очистить чат"""
    if amount < 1 or amount > 100:
        await ctx.send("❌ Можно удалить от 1 до 100 сообщений")
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"✅ Удалено {len(deleted) - 1} сообщений")
    await asyncio.sleep(3)
    await msg.delete()


@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nickname(ctx, member: discord.Member, *, nickname: str = None):
    """✏️ Сменить никнейм пользователя"""
    old_name = member.display_name
    await member.edit(nick=nickname)
    
    if nickname:
        await ctx.send(f"✅ Никнейм {old_name} изменён на {nickname}")
    else:
        await ctx.send(f"✅ Никнейм {old_name} сброшен")

# ========== СООБЩЕНИЕ 12 - РОЛЕВЫЕ КОМАНДЫ ==========

@bot.command()
async def hug(ctx, member: discord.Member):
    """🤗 Обнять пользователя"""
    gif = REACTION_GIFS.get("hug", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** обнимает **{member.name}** 🤗", color=discord.Color.pink())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


@bot.command()
async def kiss(ctx, member: discord.Member):
    """😘 Поцеловать пользователя"""
    gif = REACTION_GIFS.get("kiss", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** целует **{member.name}** 😘", color=discord.Color.red())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


@bot.command()
async def pat(ctx, member: discord.Member):
    """🫳 Погладить пользователя"""
    gif = REACTION_GIFS.get("pat", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** гладит **{member.name}** 🫳", color=discord.Color.blue())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


@bot.command()
async def slap(ctx, member: discord.Member):
    """👋 Дать пощёчину"""
    gif = REACTION_GIFS.get("slap", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** даёт пощёчину **{member.name}** 👋", color=discord.Color.dark_red())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


@bot.command()
async def punch(ctx, member: discord.Member):
    """👊 Ударить"""
    gif = REACTION_GIFS.get("punch", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** бьёт **{member.name}** 👊", color=discord.Color.dark_red())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


@bot.command()
async def bite(ctx, member: discord.Member):
    """🦷 Укусить"""
    gif = REACTION_GIFS.get("bite", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** кусает **{member.name}** 🦷", color=discord.Color.orange())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


@bot.command()
async def cry(ctx):
    """😭 Плакать"""
    gif = REACTION_GIFS.get("cry", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** плачет 😭", color=discord.Color.blue())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


@bot.command()
async def laugh(ctx):
    """😆 Смеяться"""
    gif = REACTION_GIFS.get("laugh", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** смеётся 😆", color=discord.Color.gold())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


@bot.command()
async def dance(ctx):
    """💃 Танцевать"""
    gif = REACTION_GIFS.get("dance", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** танцует 💃", color=discord.Color.purple())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


@bot.command()
async def kill(ctx, member: discord.Member):
    """💀 Убить (шутка)"""
    gif = REACTION_GIFS.get("kill", "")
    embed = discord.Embed(description=f"**{ctx.author.name}** убил **{member.name}** 💀", color=discord.Color.dark_red())
    if gif:
        embed.set_image(url=gif)
    await ctx.send(embed=embed)


# ========== ГЕНДЕРНЫЕ РОЛИ ==========
@bot.command()
async def gender(ctx, choice: str = None):
    """🚻 Выбрать гендер (девушка/парень)"""
    if not choice:
        await ctx.send("🚻 **Выберите гендер:**\n`j.gender девушка` - получить роль девочки\n`j.gender парень` - получить роль мальчика\n`j.gender remove` - убрать гендерную роль")
        return
    
    boy_role = ctx.guild.get_role(ROLE_BOY)
    girl_role = ctx.guild.get_role(ROLE_GIRL)
    
    if not boy_role or not girl_role:
        await ctx.send("❌ Гендерные роли не настроены! Обратитесь к администратору")
        return
    
    if choice.lower() == "remove":
        await ctx.author.remove_roles(boy_role, girl_role)
        await ctx.send("✅ Гендерная роль убрана")
        return
    
    if choice.lower() in ["девушка", "девочка", "girl", "female"]:
        await ctx.author.remove_roles(boy_role)
        await ctx.author.add_roles(girl_role)
        await ctx.send("✅ Вы выбрали роль **Девочка** 🌸")
    elif choice.lower() in ["парень", "мальчик", "boy", "male"]:
        await ctx.author.remove_roles(girl_role)
        await ctx.author.add_roles(boy_role)
        await ctx.send("✅ Вы выбрали роль **Мальчик** 💪")
    else:
        await ctx.send("❌ Используйте: девушка, парень или remove")


# ========== ЦВЕТНЫЕ РОЛИ ==========
@bot.command()
async def color(ctx, emoji: str = None):
    """🎨 Выбрать цветную роль"""
    if not emoji:
        colors = "\n".join([f"{e} - {c['name']}" for e, c in COLOR_ROLES.items()])
        await ctx.send(f"🎨 **Доступные цвета:**\n{colors}\n\nИспользуйте: `j.color 🔴`")
        return
    
    if emoji not in COLOR_ROLES:
        await ctx.send("❌ Неверный эмодзи! Используйте: 🔴 🔵 🟢 🟡 🟣 🌸 ⚪ ⬛")
        return
    
    color_data = COLOR_ROLES[emoji]
    role = ctx.guild.get_role(color_data["id"])
    
    if not role:
        await ctx.send("❌ Роль не найдена! Обратитесь к администратору")
        return
    
    # Убираем другие цветные роли
    for e, c in COLOR_ROLES.items():
        old_role = ctx.guild.get_role(c["id"])
        if old_role and old_role in ctx.author.roles:
            await ctx.author.remove_roles(old_role)
    
    await ctx.author.add_roles(role)
    await ctx.send(f"✅ Вы выбрали цвет **{color_data['name']}** {emoji}")


# ========== НАСТРОЙКИ КАНАЛОВ ==========
@bot.command()
@commands.has_permissions(administrator=True)
async def settings(ctx, setting: str = None, channel: discord.TextChannel = None):
    """⚙️ Настройка каналов (welcome/logs/levels)"""
    if not setting:
        await ctx.send("⚙️ **Настройки:**\n`j.settings welcome #канал` - канал приветствий\n`j.settings logs #канал` - канал логов\n`j.settings levels #канал` - канал уровней")
        return
    
    if not channel:
        await ctx.send(f"❌ Укажите канал: `j.settings {setting} #канал`")
        return
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('''INSERT OR REPLACE INTO guild_settings (guild_id, welcome_channel, log_channel, levels_channel) 
                           VALUES (?, COALESCE((SELECT welcome_channel FROM guild_settings WHERE guild_id=?), ?),
                                   COALESCE((SELECT log_channel FROM guild_settings WHERE guild_id=?), ?),
                                   COALESCE((SELECT levels_channel FROM guild_settings WHERE guild_id=?), ?))''',
                        (ctx.guild.id, ctx.guild.id, channel.id if setting == "welcome" else None,
                         ctx.guild.id, channel.id if setting == "logs" else None,
                         ctx.guild.id, channel.id if setting == "levels" else None))
        await db.commit()
    
    if ctx.guild.id not in guild_settings:
        guild_settings[ctx.guild.id] = {}
    
    if setting == "welcome":
        guild_settings[ctx.guild.id]["welcome_channel"] = channel.id
        await ctx.send(f"✅ Канал приветствий: {channel.mention}")
    elif setting == "logs":
        guild_settings[ctx.guild.id]["log_channel"] = channel.id
        await ctx.send(f"✅ Канал логов: {channel.mention}")
    elif setting == "levels":
        guild_settings[ctx.guild.id]["levels_channel"] = channel.id
        await ctx.send(f"✅ Канал уровней: {channel.mention}")
    else:
        await ctx.send("❌ Доступно: welcome, logs, levels")

# ========== СООБЩЕНИЕ 13 - АВТОМОДЕРАЦИЯ ==========

@bot.command()
@commands.has_permissions(administrator=True)
async def automod(ctx, action: str = None, module: str = None, *, arg: str = None):
    """🛡️ Настройка автомодерации"""
    
    # Инициализация настроек для сервера
    if ctx.guild.id not in guild_settings:
        guild_settings[ctx.guild.id] = {}
    
    settings = guild_settings[ctx.guild.id]
    
    if "automod_enabled" not in settings:
        settings.update({
            "automod_enabled": True,
            "automod_bad_words": [],
            "automod_invites_enabled": True,
            "automod_phishing_enabled": True,
            "automod_exempt_roles": []
        })
    
    if action is None or action == "status":
        embed = discord.Embed(title="🛡️ НАСТРОЙКИ АВТОМОДЕРАЦИИ", color=discord.Color.blue())
        embed.add_field(name="📊 Общий статус", value="✅ ВКЛЮЧЁН" if settings["automod_enabled"] else "❌ ВЫКЛЮЧЕН", inline=False)
        embed.add_field(name="📝 Запрещённые слова", value=f"Слов в списке: {len(settings['automod_bad_words'])}", inline=True)
        embed.add_field(name="🚫 Реклама серверов", value="✅ ВКЛ" if settings["automod_invites_enabled"] else "❌ ВЫКЛ", inline=True)
        embed.add_field(name="🎣 Фишинг", value="✅ ВКЛ" if settings["automod_phishing_enabled"] else "❌ ВЫКЛ", inline=True)
        
        roles = [ctx.guild.get_role(rid).mention for rid in settings["automod_exempt_roles"] if ctx.guild.get_role(rid)]
        embed.add_field(name="👑 Исключённые роли", value=", ".join(roles) if roles else "Нет", inline=False)
        
        await ctx.send(embed=embed)
        return
    
    if action == "enable":
        settings["automod_enabled"] = True
        await ctx.send("✅ Автомодерация ВКЛЮЧЕНА")
    
    elif action == "disable":
        settings["automod_enabled"] = False
        await ctx.send("❌ Автомодерация ВЫКЛЮЧЕНА")
    
    elif action == "words":
        if module == "add":
            if not arg:
                await ctx.send("❌ Укажите слово: `j.automod words add плохое_слово`")
                return
            word = arg.lower()
            if word not in settings["automod_bad_words"]:
                settings["automod_bad_words"].append(word)
                await ctx.send(f"✅ Добавлено слово: `{word}`")
            else:
                await ctx.send(f"❌ Слово `{word}` уже в списке")
        
        elif module == "remove":
            if not arg:
                await ctx.send("❌ Укажите слово: `j.automod words remove плохое_слово`")
                return
            word = arg.lower()
            if word in settings["automod_bad_words"]:
                settings["automod_bad_words"].remove(word)
                await ctx.send(f"✅ Удалено слово: `{word}`")
            else:
                await ctx.send(f"❌ Слово `{word}` не найдено")
        
        elif module == "list":
            if settings["automod_bad_words"]:
                words = ", ".join(settings["automod_bad_words"])
                await ctx.send(f"📝 **Запрещённые слова:**\n{words}")
            else:
                await ctx.send("📝 Список запрещённых слов пуст")
        
        elif module == "clear":
            settings["automod_bad_words"] = []
            await ctx.send("✅ Список запрещённых слов очищен")
        
        else:
            await ctx.send("❌ Доступно: add, remove, list, clear")
    
    elif action == "invites":
        if module == "on":
            settings["automod_invites_enabled"] = True
            await ctx.send("✅ Проверка рекламы серверов ВКЛЮЧЕНА")
        elif module == "off":
            settings["automod_invites_enabled"] = False
            await ctx.send("❌ Проверка рекламы серверов ВЫКЛЮЧЕНА")
        else:
            await ctx.send("❌ Используйте: `j.automod invites on/off`")
    
    elif action == "phishing":
        if module == "on":
            settings["automod_phishing_enabled"] = True
            await ctx.send("✅ Проверка фишинга ВКЛЮЧЕНА")
        elif module == "off":
            settings["automod_phishing_enabled"] = False
            await ctx.send("❌ Проверка фишинга ВЫКЛЮЧЕНА")
        else:
            await ctx.send("❌ Используйте: `j.automod phishing on/off`")
    
    elif action == "exempt":
        if module == "add":
            if not arg:
                await ctx.send("❌ Укажите роль: `j.automod exempt add @роль`")
                return
            # Парсим роль
            role_id = None
            if arg.isdigit():
                role_id = int(arg)
            elif arg.startswith("<@&"):
                role_id = int(arg.strip("<@&>"))
            
            if role_id and ctx.guild.get_role(role_id):
                if role_id not in settings["automod_exempt_roles"]:
                    settings["automod_exempt_roles"].append(role_id)
                    await ctx.send(f"✅ Роль {ctx.guild.get_role(role_id).mention} добавлена в исключения")
                else:
                    await ctx.send("❌ Роль уже в исключениях")
            else:
                await ctx.send("❌ Роль не найдена")
        
        elif module == "remove":
            if not arg:
                await ctx.send("❌ Укажите роль: `j.automod exempt remove @роль`")
                return
            role_id = None
            if arg.isdigit():
                role_id = int(arg)
            elif arg.startswith("<@&"):
                role_id = int(arg.strip("<@&>"))
            
            if role_id in settings["automod_exempt_roles"]:
                settings["automod_exempt_roles"].remove(role_id)
                await ctx.send(f"✅ Роль удалена из исключений")
            else:
                await ctx.send("❌ Роль не найдена в исключениях")
        
        elif module == "list":
            roles = [ctx.guild.get_role(rid).mention for rid in settings["automod_exempt_roles"] if ctx.guild.get_role(rid)]
            await ctx.send(f"👑 **Исключённые роли:**\n{', '.join(roles) if roles else 'Нет'}")
        
        else:
            await ctx.send("❌ Доступно: add, remove, list")
    
    else:
        await ctx.send("❌ Доступные действия: enable, disable, status, words, invites, phishing, exempt")


# ========== ФУНКЦИИ АВТОМОДЕРАЦИИ ==========
async def check_automod(message):
    """Проверка сообщения на нарушение правил автомодерации"""
    if message.author.guild_permissions.administrator:
        return False, None
    
    settings = guild_settings.get(message.guild.id, {})
    
    if not settings.get("automod_enabled", True):
        return False, None
    
    # Проверка на исключённые роли
    for role_id in settings.get("automod_exempt_roles", []):
        role = message.guild.get_role(role_id)
        if role and role in message.author.roles:
            return False, None
    
    content = message.content.lower()
    
    # Проверка запрещённых слов
    for word in settings.get("automod_bad_words", []):
        if word in content:
            return True, f"запрещённое слово: {word}"
    
    # Проверка рекламы серверов
    if settings.get("automod_invites_enabled", True):
        invite_patterns = [
            r"discord\.gg\/\S+",
            r"discord\.com\/invite\/\S+",
            r"dsc\.gg\/\S+",
            r"discordapp\.com\/invite\/\S+"
        ]
        for pattern in invite_patterns:
            if re.search(pattern, content):
                return True, "реклама Discord сервера"
    
    # Проверка фишинга
    if settings.get("automod_phishing_enabled", True):
        phishing_patterns = [
            r"free.*nitro",
            r"steam.*giveaway",
            r"пополни.*баланс.*http",
            r"бесплатно.*голосование"
        ]
        for pattern in phishing_patterns:
            if re.search(pattern, content):
                return True, "подозрение на фишинг"
    
    return False, None

# ========== СООБЩЕНИЕ 14 - ПРИВАТНЫЕ ГОЛОСОВЫЕ КАНАЛЫ ==========

@bot.event
async def on_voice_state_update(member, before, after):
    """Создание приватного голосового канала"""
    
    if after.channel and after.channel.id == VC_TRIGGER_CHANNEL_ID:
        # Создаём новый приватный канал
        category = member.guild.get_channel(VC_CREATE_CATEGORY_ID)
        if not category:
            return
        
        # Находим свободный номер
        existing = [c for c in category.voice_channels if c.name.startswith("Приватный")]
        num = len(existing) + 1
        
        # Права доступа
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(connect=False),
            member: discord.PermissionOverwrite(connect=True, manage_channels=True, mute_members=True, deafen_members=True, move_members=True),
            member.guild.me: discord.PermissionOverwrite(connect=True, manage_channels=True)
        }
        
        # Добавляем права для поддержки
        for role_id in SUPPORT_ROLE_IDS:
            role = member.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(connect=True)
        
        channel = await category.create_voice_channel(
            name=f"Приватный #{num}",
            overwrites=overwrites
        )
        
        # Перемещаем пользователя
        await member.move_to(channel)
        
        # Сохраняем в базу
        async with aiosqlite.connect("justice.db") as db:
            await db.execute('''INSERT INTO private_vc (channel_id, owner_id, guild_id, channel_name, created_at)
                               VALUES (?,?,?,?,?)''',
                            (channel.id, member.id, member.guild.id, channel.name, datetime.now().isoformat()))
            await db.commit()
        
        # Отправляем сообщение в канал
        embed = discord.Embed(
            title="🔊 ПРИВАТНЫЙ КАНАЛ СОЗДАН",
            description=f"Добро пожаловать в ваш приватный канал!\n\n"
                        f"**Команды управления:**\n"
                        f"`j vc_name <название>` - изменить название\n"
                        f"`j vc_limit <число>` - установить лимит участников (0 - без лимита)\n"
                        f"`j vc_lock` - закрыть канал\n"
                        f"`j vc_unlock` - открыть канал\n"
                        f"`j vc_ban @user` - забанить пользователя\n"
                        f"`j vc_unban @user` - разбанить\n"
                        f"`j vc_claim` - передать права другому\n"
                        f"`j vc_delete` - удалить канал",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
    
    # Удаляем пустые приватные каналы
    if before.channel and before.channel.category and before.channel.category.id == VC_CREATE_CATEGORY_ID:
        if len(before.channel.members) == 0:
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('DELETE FROM private_vc WHERE channel_id=?', (before.channel.id,))
                await db.commit()
            
            try:
                await before.channel.delete()
            except:
                pass


@bot.command()
async def vc_name(ctx, *, name: str):
    """✏️ Изменить название приватного канала"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Вы должны находиться в голосовом канале")
        return
    
    channel = ctx.author.voice.channel
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT owner_id FROM private_vc WHERE channel_id=?', (channel.id,))
        vc_data = await cur.fetchone()
    
    if not vc_data:
        await ctx.send("❌ Это не приватный канал")
        return
    
    if vc_data[0] != ctx.author.id and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Только владелец канала может менять название")
        return
    
    if len(name) > 50:
        await ctx.send("❌ Название слишком длинное (макс 50 символов)")
        return
    
    await channel.edit(name=name)
    await ctx.send(f"✅ Название канала изменено на **{name}**")


@bot.command()
async def vc_limit(ctx, limit: int):
    """🔢 Установить лимит участников"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Вы должны находиться в голосовом канале")
        return
    
    channel = ctx.author.voice.channel
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT owner_id FROM private_vc WHERE channel_id=?', (channel.id,))
        vc_data = await cur.fetchone()
    
    if not vc_data:
        await ctx.send("❌ Это не приватный канал")
        return
    
    if vc_data[0] != ctx.author.id and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Только владелец канала может менять лимит")
        return
    
    if limit < 0 or limit > 99:
        await ctx.send("❌ Лимит должен быть от 0 до 99 (0 - без лимита)")
        return
    
    await channel.edit(user_limit=limit if limit > 0 else None)
    await ctx.send(f"✅ Лимит участников установлен: {limit if limit > 0 else 'без лимита'}")


@bot.command()
async def vc_lock(ctx):
    """🔒 Закрыть канал (только владелец)"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Вы должны находиться в голосовом канале")
        return
    
    channel = ctx.author.voice.channel
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT owner_id FROM private_vc WHERE channel_id=?', (channel.id,))
        vc_data = await cur.fetchone()
    
    if not vc_data:
        await ctx.send("❌ Это не приватный канал")
        return
    
    if vc_data[0] != ctx.author.id and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Только владелец канала может его закрыть")
        return
    
    await channel.set_permissions(ctx.guild.default_role, connect=False)
    await ctx.send("🔒 Канал закрыт. Только вы и поддержка могут заходить.")


@bot.command()
async def vc_unlock(ctx):
    """🔓 Открыть канал"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Вы должны находиться в голосовом канале")
        return
    
    channel = ctx.author.voice.channel
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT owner_id FROM private_vc WHERE channel_id=?', (channel.id,))
        vc_data = await cur.fetchone()
    
    if not vc_data:
        await ctx.send("❌ Это не приватный канал")
        return
    
    if vc_data[0] != ctx.author.id and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Только владелец канала может его открыть")
        return
    
    await channel.set_permissions(ctx.guild.default_role, connect=None)
    await ctx.send("🔓 Канал открыт. Все могут заходить.")


@bot.command()
async def vc_ban(ctx, member: discord.Member):
    """🚫 Забанить пользователя в приватном канале"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Вы должны находиться в голосовом канале")
        return
    
    channel = ctx.author.voice.channel
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT owner_id, banned_users FROM private_vc WHERE channel_id=?', (channel.id,))
        vc_data = await cur.fetchone()
    
    if not vc_data:
        await ctx.send("❌ Это не приватный канал")
        return
    
    if vc_data[0] != ctx.author.id and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Только владелец канала может банить")
        return
    
    banned = json.loads(vc_data[1]) if vc_data[1] else []
    if member.id not in banned:
        banned.append(member.id)
    
    await channel.set_permissions(member, connect=False)
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE private_vc SET banned_users=? WHERE channel_id=?', (json.dumps(banned), channel.id))
        await db.commit()
    
    # Выгоняем если в канале
    if member in channel.members:
        await member.move_to(None)
    
    await ctx.send(f"🚫 {member.mention} забанен в вашем канале")


@bot.command()
async def vc_unban(ctx, member: discord.Member):
    """✅ Разбанить пользователя"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Вы должны находиться в голосовом канале")
        return
    
    channel = ctx.author.voice.channel
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT owner_id, banned_users FROM private_vc WHERE channel_id=?', (channel.id,))
        vc_data = await cur.fetchone()
    
    if not vc_data:
        await ctx.send("❌ Это не приватный канал")
        return
    
    if vc_data[0] != ctx.author.id and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Только владелец канала может разбанить")
        return
    
    banned = json.loads(vc_data[1]) if vc_data[1] else []
    if member.id in banned:
        banned.remove(member.id)
    
    await channel.set_permissions(member, connect=None)
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE private_vc SET banned_users=? WHERE channel_id=?', (json.dumps(banned), channel.id))
        await db.commit()
    
    await ctx.send(f"✅ {member.mention} разбанен в вашем канале")


@bot.command()
async def vc_claim(ctx):
    """👑 Передать права владельца (нужно быть в канате)"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Вы должны находиться в голосовом канале")
        return
    
    channel = ctx.author.voice.channel
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT owner_id FROM private_vc WHERE channel_id=?', (channel.id,))
        vc_data = await cur.fetchone()
    
    if not vc_data:
        await ctx.send("❌ Это не приватный канал")
        return
    
    if vc_data[0] != ctx.author.id:
        await ctx.send("❌ Вы уже не владелец?")
        return
    
    # Ищем другого участника
    other_members = [m for m in channel.members if m.id != ctx.author.id and not m.bot]
    if not other_members:
        await ctx.send("❌ В канале нет других участников для передачи прав")
        return
    
    new_owner = other_members[0]
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE private_vc SET owner_id=? WHERE channel_id=?', (new_owner.id, channel.id))
        await db.commit()
    
    await ctx.send(f"👑 Права владельца переданы {new_owner.mention}")


@bot.command()
async def vc_delete(ctx):
    """🗑️ Удалить приватный канал (только владелец)"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Вы должны находиться в голосовом канале")
        return
    
    channel = ctx.author.voice.channel
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT owner_id FROM private_vc WHERE channel_id=?', (channel.id,))
        vc_data = await cur.fetchone()
    
    if not vc_data:
        await ctx.send("❌ Это не приватный канал")
        return
    
    if vc_data[0] != ctx.author.id and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Только владелец канала может его удалить")
        return
    
    await ctx.send("⚠️ Канал будет удалён через 5 секунд...")
    await asyncio.sleep(5)
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('DELETE FROM private_vc WHERE channel_id=?', (channel.id,))
        await db.commit()
    
    try:
        await channel.delete()
    except:
        pass

# ========== СООБЩЕНИЕ 15 - КОМАНДЫ ВЛАДЕЛЬЦА ==========

OWNER_ID = 1123205411999330466  # ЗАМЕНИ НА СВОЙ DISCORD ID


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)


@bot.command()
@is_owner()
async def admin_help(ctx):
    """👑 Показать все команды владельца"""
    embed = discord.Embed(title="👑 КОМАНДЫ ВЛАДЕЛЬЦА", color=discord.Color.purple())
    
    commands_list = [
        ("j.owner_give @user <сумма>", "Выдать деньги"),
        ("j.owner_take @user <сумма>", "Забрать деньги"),
        ("j.owner_set_balance @user <сумма>", "Установить баланс"),
        ("j.owner_reset_user @user", "Полный сброс пользователя"),
        ("j.owner_stats", "Статистика сервера"),
        ("j.reset_user [@user]", "Сброс пользователя"),
        ("j.reset_db confirm", "ПОЛНОЕ УДАЛЕНИЕ БД"),
        ("j.backup_db", "Создать резервную копию"),
        ("j.download_backup", "Скачать БД"),
        ("j.upload_backup", "Восстановить БД"),
        ("j.backup_info", "Информация о БД"),
        ("j.add_shop_item <название> <цена> <роль_id> [описание]", "Добавить товар"),
        ("j.remove_shop_item <название>", "Удалить товар"),
        ("j.settings welcome/logs/levels #канал", "Настроить каналы"),
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="⚠️ Будьте осторожны с командами!")
    await ctx.send(embed=embed)


@bot.command()
@is_owner()
async def owner_give(ctx, member: discord.Member, amount: int):
    """👑 Выдать деньги пользователю"""
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    
    await add_balance(member.id, ctx.guild.id, amount)
    await ctx.send(f"✅ Выдано {amount} 💎 {member.mention}")


@bot.command()
@is_owner()
async def owner_take(ctx, member: discord.Member, amount: int):
    """👑 Забрать деньги у пользователя"""
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть больше 0")
        return
    
    user = await get_user(member.id, ctx.guild.id)
    if user[4] < amount:
        await ctx.send(f"❌ У {member.mention} только {user[4]} 💎")
        return
    
    await add_balance(member.id, ctx.guild.id, -amount)
    await ctx.send(f"✅ Забрано {amount} 💎 у {member.mention}")


@bot.command()
@is_owner()
async def owner_set_balance(ctx, member: discord.Member, amount: int):
    """👑 Установить точный баланс"""
    if amount < 0:
        await ctx.send("❌ Баланс не может быть отрицательным")
        return
    
    await update_user(member.id, ctx.guild.id, balance=amount)
    await ctx.send(f"✅ Баланс {member.mention} установлен на {amount} 💎")


@bot.command()
@is_owner()
async def owner_reset_user(ctx, member: discord.Member):
    """👑 Полный сброс пользователя"""
    await update_user(
        member.id, ctx.guild.id,
        xp=0, level=0, balance=START_BALANCE, bank=0,
        reputation=0, warning_count=0, total_messages=0,
        today_messages=0, week_messages=0, month_messages=0,
        inventory="[]", crops="[]", fishing_exp=0
    )
    await ctx.send(f"✅ Пользователь {member.mention} полностью сброшен")


@bot.command()
@is_owner()
async def owner_stats(ctx):
    """👑 Статистика сервера"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT COUNT(*) FROM users WHERE guild_id=?', (ctx.guild.id,))
        users_count = (await cur.fetchone())[0]
        
        cur = await db.execute('SELECT SUM(balance) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_balance = (await cur.fetchone())[0] or 0
        
        cur = await db.execute('SELECT SUM(bank) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_bank = (await cur.fetchone())[0] or 0
        
        cur = await db.execute('SELECT SUM(total_messages) FROM users WHERE guild_id=?', (ctx.guild.id,))
        total_messages = (await cur.fetchone())[0] or 0
    
    embed = discord.Embed(title=f"📊 СТАТИСТИКА СЕРВЕРА | {ctx.guild.name}", color=discord.Color.gold())
    embed.add_field(name="👥 Пользователей в БД", value=str(users_count), inline=True)
    embed.add_field(name="💰 Всего денег", value=f"{total_balance + total_bank} 💎", inline=True)
    embed.add_field(name="💬 Всего сообщений", value=str(total_messages), inline=True)
    embed.add_field(name="🏦 В банках", value=f"{total_bank} 💎", inline=True)
    embed.add_field(name="💎 В кошельках", value=f"{total_balance} 💎", inline=True)
    
    await ctx.send(embed=embed)


@bot.command()
@is_owner()
async def reset_user(ctx, member: discord.Member = None):
    """👑 Сброс пользователя (админ/владелец)"""
    if not member:
        await ctx.send("❌ Укажите пользователя: `j.reset_user @user`")
        return
    
    await owner_reset_user(ctx, member)


@bot.command()
@is_owner()
async def reset_db(ctx, confirm: str = None):
    """👑 ПОЛНОЕ УДАЛЕНИЕ БД"""
    if confirm != "confirm":
        await ctx.send("⚠️ Это удалит ВСЮ базу данных! Для подтверждения: `j.reset_db confirm`")
        return
    
    async with aiosqlite.connect("justice.db") as db:
        tables = ['users', 'warnings', 'suggestions', 'private_vc', 'giveaways', 'stoloto', 'custom_shop', 'guild_settings']
        for table in tables:
            await db.execute(f'DROP TABLE IF EXISTS {table}')
        await db.commit()
    
    await init_db()
    await ctx.send("✅ База данных полностью сброшена и пересоздана")


@bot.command()
@is_owner()
async def backup_db(ctx):
    """👑 Создать резервную копию БД"""
    backup_file = f"justice_backup_{int(time.time())}.db"
    
    async with aiosqlite.connect("justice.db") as src:
        async with aiosqlite.connect(backup_file) as dst:
            await src.backup(dst)
    
    await ctx.send(f"✅ Резервная копия создана: {backup_file}")
    os.remove(backup_file)  # Удаляем после отправки


@bot.command()
@is_owner()
async def download_backup(ctx):
    """👑 Скачать БД на компьютер"""
    await ctx.send(file=discord.File("justice.db"))

# ========== СООБЩЕНИЕ 16 - ЗАВЕРШАЮЩАЯ ЧАСТЬ (ЗАПУСК) ==========

# ========== ПРОЧИЕ КОМАНДЫ ==========

@bot.command()
async def ping(ctx):
    """🏓 Пинг бота"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Понг! {latency}ms")


@bot.command()
async def uptime(ctx):
    """⏰ Время работы бота"""
    delta = datetime.now() - bot.start_time
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    seconds = delta.seconds % 60
    
    await ctx.send(f"⏰ Бот работает: {days}д {hours}ч {minutes}м {seconds}с")


@bot.command()
async def invite(ctx):
    """🔗 Пригласить бота на сервер"""
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands"
    embed = discord.Embed(title="🔗 ПРИГЛАСИТЬ БОТА", description=f"[Нажмите сюда]({invite_url})", color=discord.Color.blue())
    await ctx.send(embed=embed)


@bot.command()
async def support(ctx):
    """🆘 Получить ссылку на поддержку"""
    embed = discord.Embed(
        title="🆘 ПОДДЕРЖКА",
        description="По всем вопросам обращайтесь в тикеты или к администрации!",
        color=discord.Color.blue()
    )
    embed.add_field(name="📌 Ссылка", value="https://www.donationalerts.com/dashboard/payouts/settings", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def donate(ctx):
    """💝 Поддержать проект"""
    embed = discord.Embed(
        title="💝 ПОДДЕРЖАТЬ ПРОЕКТ",
        description="Спасибо, что помогаете развитию бота!",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="💳 Банковские карты",
        value="• Visa / Mastercard / Мир\n• Maestro\n• СБП (Система Быстрых Платежей)\n• Доллары (USD)\n• Евро (EUR)",
        inline=False
    )
    embed.add_field(
        name="🇷🇺 Российские карты",
        value="• Сбербанк\n• Тинькофф\n• ВТБ\n• Альфа-Банк\n• Газпромбанк\n• Открытие\n• МТС Банк\n• Почта Банк",
        inline=False
    )
    embed.add_field(
        name="🔗 Ссылка для доната",
        value="https://www.donationalerts.com/dashboard/payouts/settings",
        inline=False
    )
    embed.add_field(
        name="📱 СБП",
        value="Доступен перевод по номеру телефона через СБП (уточняйте у администратора)",
        inline=False
    )
    embed.set_footer(text="Все средства идут на развитие бота и оплату серверов")
    await ctx.send(embed=embed)


# ========== ВЕБХУКИ ==========
@bot.event
async def on_member_join(member):
    """Приветствие нового участника"""
    settings = guild_settings.get(member.guild.id, {})
    welcome_channel_id = settings.get("welcome_channel", WELCOME_CHANNEL_ID)
    channel = bot.get_channel(welcome_channel_id)
    
    if channel:
        embed = discord.Embed(
            title="👋 ДОБРО ПОЖАЛОВАТЬ!",
            description=f"{member.mention}, добро пожаловать на сервер **{member.guild.name}**!\n"
                        f"Ты наш {member.guild.member_count} участник!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📚 Полезные команды", value="`j.help` - помощь\n`j.profile` - профиль\n`j.rules` - правила", inline=False)
        await channel.send(embed=embed)
    
    # Выдаём стандартную роль
    default_role = member.guild.get_role(DEFAULT_ROLE_ID)
    if default_role:
        await member.add_roles(default_role)


@bot.event
async def on_member_remove(member):
    """Прощание"""
    settings = guild_settings.get(member.guild.id, {})
    welcome_channel_id = settings.get("welcome_channel", WELCOME_CHANNEL_ID)
    channel = bot.get_channel(welcome_channel_id)
    
    if channel:
        embed = discord.Embed(
            title="👋 ПОКА!",
            description=f"{member.display_name} покинул сервер...",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)


# ========== ОБРАБОТКА СООБЩЕНИЙ ==========
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.guild:
        # Добавляем опыт
        await get_user(message.author.id, message.guild.id)
        
        # Проверка автомодерации
        is_violation, reason = await check_automod(message)
        if is_violation:
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, нарушение: {reason}", delete_after=5)
                
                # Добавляем предупреждение
                await add_auto_warning(message.author, reason, message.channel)
            except:
                pass
            return
        
        # Добавляем опыт за сообщение
        level_up, new_level = await add_xp(message.author.id, message.guild.id, random.randint(5, 15))
        
        if level_up:
            # Отправка в канал уровней
            level_channel_id = guild_settings.get(message.guild.id, {}).get("levels_channel", LEVEL_CHANNEL_ID)
            level_channel = bot.get_channel(level_channel_id)
            if level_channel:
                embed = discord.Embed(
                    title="🎉 ПОВЫШЕНИЕ УРОВНЯ!",
                    description=f"{message.author.mention} достиг **{new_level}** уровня!",
                    color=discord.Color.gold()
                )
                await level_channel.send(embed=embed)
            
            # Выдача ролей за уровни
            for level, role_id in LEVEL_ROLES.items():
                if new_level >= level:
                    role = message.guild.get_role(role_id)
                    if role and role not in message.author.roles:
                        await message.author.add_roles(role)
                        await message.channel.send(f"🎉 {message.author.mention}, вам выдана роль {role.mention} за {level} уровень!")
    
    # Ответ на упоминание
    if bot.user.mentioned_in(message) and not message.mention_everyone and len(message.mentions) == 1:
        await message.channel.send(f"👋 Привет, {message.author.mention}! Используй `j.help` для списка команд.")
    
    await bot.process_commands(message)


# ========== ЗАПУСК ==========
@bot.event
async def on_ready():
    global bot_start_time
    bot_start_time = datetime.now()
    
    print(f"✅ {bot.user} запущен!")
    print(f"📊 На {len(bot.guilds)} серверах")
    print(f"👥 Всего пользователей в БД: {len(await get_all_users_count())}")
    
    await init_db()
    
    # Запускаем фоновые задачи
    bank_interest.start()
    check_giveaways.start()
    
    # Устанавливаем статус
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="j.help | Justice Bot"
        )
    )
    
    # Отправка в канал логов
    log_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="✅ БОТ ЗАПУЩЕН",
            description=f"Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            color=discord.Color.green()
        )
        await log_channel.send(embed=embed)


async def get_all_users_count():
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT COUNT(DISTINCT user_id) FROM users')
        return (await cur.fetchone())[0]


# ========== ОБРАБОТКА ОШИБОК ==========
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ Недостаточно прав! {error}")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Не хватает аргументов. Используй `j.help {ctx.command.name}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Неверный аргумент: {error}")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ Подождите {error.retry_after:.0f} секунд")
    else:
        print(f"❌ Ошибка: {error}")
        await ctx.send(f"❌ Произошла ошибка: {str(error)[:100]}")


# ========== ЗАПУСК БОТА ==========
if __name__ == "__main__":
    if TOKEN == "ВСТАВЬ_СВОЙ_ТОКЕН_СЮДА":
        print("❌ ВСТАВЬ СВОЙ ТОКЕН В ПЕРЕМЕННУЮ TOKEN!")
        exit(1)
    
    bot.run(TOKEN)
