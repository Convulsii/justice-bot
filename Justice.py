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
    "win_casino_10": {"name": "🎰 Удачливый", "desc": "Выиграть 10 раз в казино", "reward": 1000},
    "win_casino_50": {"name": "🎰 Азартный", "desc": "Выиграть 50 раз в казино", "reward": 5000},
    "win_blackjack_10": {"name": "🃏 Картёжник", "desc": "Выиграть 10 раз в блэкджек", "reward": 1000},
    "win_ttt_10": {"name": "❌⭕ Стратег", "desc": "Выиграть 10 раз в крестики-нолики", "reward": 2000},
    "fish_10": {"name": "🎣 Рыбак-любитель", "desc": "Поймать 10 рыб", "reward": 200},
    "fish_100": {"name": "🎣 Опытный рыбак", "desc": "Поймать 100 рыб", "reward": 2000},
    "fish_500": {"name": "🎣 Профессионал", "desc": "Поймать 500 рыб", "reward": 10000},
    "fish_legendary": {"name": "🐉 Ловец легенд", "desc": "Поймать легендарную рыбу", "reward": 10000},
    "plant_10": {"name": "🌱 Садовод", "desc": "Посадить 10 культур", "reward": 200},
    "harvest_100": {"name": "🌾 Фермер", "desc": "Собрать 100 урожаев", "reward": 2000},
    "voice_1h": {"name": "🎤 Первые минуты", "desc": "Провести 1 час в голосовом канале", "reward": 100},
    "voice_24h": {"name": "🎤 Голосовой активист", "desc": "Провести 24 часа в голосовом канале", "reward": 2000},
    "voice_100h": {"name": "🎤 Войс-легенда", "desc": "Провести 100 часов в голосовом канале", "reward": 10000},
    "invite_1": {"name": "📨 Приглашатель", "desc": "Пригласить 1 друга", "reward": 500},
    "invite_5": {"name": "📨 Популяризатор", "desc": "Пригласить 5 друзей", "reward": 2500},
    "invite_10": {"name": "📨 Амбассадор", "desc": "Пригласить 10 друзей", "reward": 10000},
    "shop_buy_10": {"name": "🛍️ Покупатель", "desc": "Купить 10 предметов", "reward": 500},
    "work_100": {"name": "💼 Трудоголик", "desc": "100 раз поработать", "reward": 5000},
    "rob_10": {"name": "🔫 Грабитель", "desc": "10 успешных ограблений", "reward": 2000},
}

# ========== ЕЖЕДНЕВНЫЕ ЗАДАНИЯ ==========
DAILY_QUESTS = {
    "msg_10": {"name": "📝 Написать 10 сообщений", "target": 10, "reward": 50, "type": "messages"},
    "msg_25": {"name": "📝 Написать 25 сообщений", "target": 25, "reward": 100, "type": "messages"},
    "msg_50": {"name": "📝 Написать 50 сообщений", "target": 50, "reward": 200, "type": "messages"},
    "casino_win_1": {"name": "🎰 Выиграть в казино", "target": 1, "reward": 150, "type": "casino_win"},
    "casino_win_3": {"name": "🎰 Выиграть 3 раза в казино", "target": 3, "reward": 300, "type": "casino_win"},
    "coin_win_2": {"name": "🪙 Выиграть в монетку 2 раза", "target": 2, "reward": 100, "type": "coin_win"},
    "dice_win_2": {"name": "🎲 Выиграть в кости 2 раза", "target": 2, "reward": 100, "type": "dice_win"},
    "rps_win_2": {"name": "✊ Выиграть в КНБ 2 раза", "target": 2, "reward": 100, "type": "rps_win"},
    "bj_win_1": {"name": "🃏 Выиграть в блэкджек", "target": 1, "reward": 200, "type": "bj_win"},
    "ttt_win_1": {"name": "❌⭕ Выиграть в крестики-нолики", "target": 1, "reward": 200, "type": "ttt_win"},
    "fish_5": {"name": "🎣 Поймать 5 рыб", "target": 5, "reward": 100, "type": "fish"},
    "fish_10": {"name": "🎣 Поймать 10 рыб", "target": 10, "reward": 200, "type": "fish"},
    "work_1": {"name": "💼 Поработать", "target": 1, "reward": 100, "type": "work"},
    "work_3": {"name": "💼 Поработать 3 раза", "target": 3, "reward": 200, "type": "work"},
    "rob_1": {"name": "🔫 Ограбить", "target": 1, "reward": 150, "type": "rob"},
    "plant_3": {"name": "🌱 Посадить 3 культуры", "target": 3, "reward": 100, "type": "plant"},
    "harvest_3": {"name": "🌾 Собрать 3 урожая", "target": 3, "reward": 100, "type": "harvest"},
    "buy_item": {"name": "🛍️ Купить предмет", "target": 1, "reward": 50, "type": "buy"},
    "give_rep": {"name": "❤️ Дать репутацию", "target": 1, "reward": 100, "type": "give_rep"},
    "voice_30min": {"name": "🎤 Побыть в войсе 30 минут", "target": 30, "reward": 100, "type": "voice_minutes"},
    "voice_1h": {"name": "🎤 Побыть в войсе 1 час", "target": 60, "reward": 200, "type": "voice_minutes"},
    "daily_bonus": {"name": "📅 Забрать ежедневный бонус", "target": 1, "reward": 100, "type": "daily"},
}

# ========== РЕЦЕПТЫ КРАФТА ==========
RECIPES = {
    "золотой слиток": {"name": "🪙 Золотой слиток", "desc": "Слиток золота", "ingredients": {"золотая руда": 5, "уголь": 2}, "result": "золотой слиток", "count": 1, "xp": 50},
    "алмаз": {"name": "💎 Алмаз", "desc": "Драгоценный камень", "ingredients": {"алмазная руда": 3, "золотой слиток": 1}, "result": "алмаз", "count": 1, "xp": 100},
    "суперудочка": {"name": "🎣✨ Супер-удочка", "desc": "+50% к шансу редкой рыбы", "ingredients": {"золотая удочка": 1, "алмаз": 2, "магическая нить": 3}, "result": "super_rod", "count": 1, "xp": 200},
    "эликсир опыта": {"name": "🧪 Эликсир опыта", "desc": "x2 опыт на 1 час", "ingredients": {"магическая пыль": 5, "золотой слиток": 2}, "result": "exp_potion", "count": 1, "xp": 75},
    "золотая монета": {"name": "🪙 Золотая монета", "desc": "Можно продать за 500 💎", "ingredients": {"золотой слиток": 1}, "result": "gold_coin", "count": 5, "xp": 30},
    "корм для животных": {"name": "🌾 Корм", "desc": "Ускоряет рост животных", "ingredients": {"пшеница": 5, "кукуруза": 3}, "result": "animal_feed", "count": 10, "xp": 20},
}

# ========== ЖИВОТНЫЕ ==========
FARM_ANIMALS = {
    "курица": {"name": "🐔 Курица", "price": 1000, "produce": "яйцо", "produce_price": 50, "produce_time": 3600, "feed": "пшеница", "feed_amount": 2},
    "корова": {"name": "🐄 Корова", "price": 5000, "produce": "молоко", "produce_price": 200, "produce_time": 7200, "feed": "кукуруза", "feed_amount": 3},
    "овца": {"name": "🐑 Овца", "price": 4000, "produce": "шерсть", "produce_price": 150, "produce_time": 5400, "feed": "трава", "feed_amount": 2},
    "свинья": {"name": "🐷 Свинья", "price": 3000, "produce": "мясо", "produce_price": 100, "produce_time": 7200, "feed": "картофель", "feed_amount": 3},
    "лошадь": {"name": "🐴 Лошадь", "price": 10000, "produce": "навоз", "produce_price": 300, "produce_time": 10800, "feed": "морковь", "feed_amount": 4},
}

# ========== УЛУЧШЕНИЯ ФЕРМЫ ==========
FARM_UPGRADES = {
    "grow_speed": {"name": "🌱 Скорость роста", "base_cost": 5000, "multiplier": 0.05, "max_level": 10},
    "animal_speed": {"name": "🐄 Скорость животных", "base_cost": 5000, "multiplier": 0.05, "max_level": 10},
    "crop_yield": {"name": "🌾 Урожайность", "base_cost": 10000, "multiplier": 0.1, "max_level": 5},
    "animal_yield": {"name": "🥚 Продуктивность", "base_cost": 10000, "multiplier": 0.1, "max_level": 5},
    "max_animals": {"name": "🏠 Вместимость", "base_cost": 20000, "multiplier": 2, "max_level": 5},
}

# ========== ИНВЕСТИЦИИ ==========
INVESTMENTS = {
    "надёжный": {"min": 10000, "max": 100000, "days": 7, "rate": 0.05, "name": "🔒 Надёжный"},
    "средний": {"min": 50000, "max": 500000, "days": 14, "rate": 0.08, "name": "📊 Средний"},
    "рисковый": {"min": 100000, "max": 1000000, "days": 30, "rate": 0.12, "name": "⚡ Рисковый"},
    "премиум": {"min": 500000, "max": 5000000, "days": 60, "rate": 0.18, "name": "💎 Премиум"},
}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
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
    
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('UPDATE users SET xp=?, level=?, total_messages=?, today_messages=?, week_messages=?, month_messages=?, last_message_time=? WHERE user_id=? AND guild_id=?',
                        (new_xp, new_level, (user[9] if len(user) > 9 else 0) + 1, 
                         (user[21] if len(user) > 21 else 0) + 1, 
                         (user[22] if len(user) > 22 else 0) + 1, 
                         (user[23] if len(user) > 23 else 0) + 1, 
                         datetime.now().isoformat(), user_id, guild_id))
        await db.commit()
    
    if level_up:
        guild = bot.get_guild(guild_id)
        if guild:
            for lvl, role_id in LEVEL_ROLES.items():
                if new_level >= lvl:
                    role = guild.get_role(role_id)
                    if role:
                        member = guild.get_member(user_id)
                        if member and role not in member.roles:
                            await member.add_roles(role)
        await check_achievement(user_id, guild_id, "level", new_level)
    
    return level_up, new_level

async def check_achievement(user_id, guild_id, ach_type, value):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT achievement_id FROM achievements WHERE user_id=? AND guild_id=?', (user_id, guild_id))
        earned = set(row[0] for row in await cur.fetchall())
    
    for ach_id, ach_data in ACHIEVEMENTS.items():
        if ach_id in earned:
            continue
        
        should_unlock = False
        if ach_type == "messages" and ach_id.startswith("msg_"):
            target = int(ach_id.split("_")[1])
            if value >= target:
                should_unlock = True
        elif ach_type == "level" and ach_id.startswith("lvl_"):
            target = int(ach_id.split("_")[1])
            if value >= target:
                should_unlock = True
        
        if should_unlock:
            async with aiosqlite.connect("justice.db") as db2:
                await add_balance(user_id, guild_id, ach_data["reward"])
                await db2.execute('INSERT INTO achievements (user_id, guild_id, achievement_id, achieved_at) VALUES (?,?,?,?)', 
                                 (user_id, guild_id, ach_id, datetime.now().isoformat()))
                await db2.commit()
            
            user = bot.get_user(user_id)
            if user:
                await user.send(f"🏆 **ДОСТИЖЕНИЕ!**\n{ach_data['name']}\n💰 +{ach_data['reward']} 💎")

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
            if completed[i]:
                continue
            qdata = DAILY_QUESTS.get(qid)
            if not qdata or qdata["type"] != quest_type:
                continue
            new_progress = progresses[i] + progress_add
            if new_progress >= qdata["target"]:
                new_progress = qdata["target"]
                completed[i] = 1
                rewards += qdata["reward"]
                user = bot.get_user(user_id)
                if user:
                    await user.send(f"✅ **ЗАДАНИЕ ВЫПОЛНЕНО!**\n{qdata['name']}\n💰 +{qdata['reward']} 💎")
            await db.execute(f'UPDATE daily_quests SET quest{i+1}_progress=?, quest{i+1}_completed=? WHERE user_id=? AND guild_id=? AND quest_date=?', 
                           (new_progress, completed[i], user_id, guild_id, today))
        
        if rewards > 0:
            await add_balance(user_id, guild_id, rewards)

async def update_weekly_stats(user_id, guild_id, stat_type, value=1):
    week_start = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM weekly_stats WHERE user_id=? AND guild_id=? AND week_start=?', (user_id, guild_id, week_start))
        exists = await cur.fetchone()
        if exists:
            if stat_type == "messages":
                await db.execute('UPDATE weekly_stats SET messages=messages+? WHERE user_id=? AND guild_id=? AND week_start=?', (value, user_id, guild_id, week_start))
            elif stat_type == "casino_wins":
                await db.execute('UPDATE weekly_stats SET casino_wins=casino_wins+? WHERE user_id=? AND guild_id=? AND week_start=?', (value, user_id, guild_id, week_start))
            elif stat_type == "work_count":
                await db.execute('UPDATE weekly_stats SET work_count=work_count+? WHERE user_id=? AND guild_id=? AND week_start=?', (value, user_id, guild_id, week_start))
            elif stat_type == "fish_caught":
                await db.execute('UPDATE weekly_stats SET fish_caught=fish_caught+? WHERE user_id=? AND guild_id=? AND week_start=?', (value, user_id, guild_id, week_start))
            elif stat_type == "crops_harvested":
                await db.execute('UPDATE weekly_stats SET crops_harvested=crops_harvested+? WHERE user_id=? AND guild_id=? AND week_start=?', (value, user_id, guild_id, week_start))
        else:
            fields = {"messages":0, "casino_wins":0, "work_count":0, "fish_caught":0, "crops_harvested":0}
            fields[stat_type] = value
            await db.execute('INSERT INTO weekly_stats (user_id, guild_id, week_start, messages, casino_wins, work_count, fish_caught, crops_harvested) VALUES (?,?,?,?,?,?,?,?)',
                            (user_id, guild_id, week_start, fields["messages"], fields["casino_wins"], fields["work_count"], fields["fish_caught"], fields["crops_harvested"]))
        await db.commit()

async def update_user_stats(user_id, guild_id, stat_type, value=1):
    if stat_type == "casino_win":
        await update_user(user_id, guild_id, total_casino_wins=value)
        await update_weekly_stats(user_id, guild_id, "casino_wins", value)
    elif stat_type == "blackjack_win":
        await update_user(user_id, guild_id, total_blackjack_wins=value)
    elif stat_type == "ttt_win":
        await update_user(user_id, guild_id, total_ttt_wins=value)
    elif stat_type == "fish":
        await update_user(user_id, guild_id, total_fish_caught=value)
        await update_weekly_stats(user_id, guild_id, "fish_caught", value)
    elif stat_type == "legendary_fish":
        await update_user(user_id, guild_id, total_legendary_fish=value)
    elif stat_type == "mythic_fish":
        await update_user(user_id, guild_id, total_mythic_fish=value)
    elif stat_type == "harvest":
        await update_user(user_id, guild_id, total_harvests=value)
        await update_weekly_stats(user_id, guild_id, "crops_harvested", value)
    elif stat_type == "plant":
        await update_user(user_id, guild_id, total_plants=value)
    elif stat_type == "work":
        await update_user(user_id, guild_id, total_work=value)
        await update_weekly_stats(user_id, guild_id, "work_count", value)
    elif stat_type == "rob_success":
        await update_user(user_id, guild_id, total_rob_success=value)
    elif stat_type == "shop_buy":
        await update_user(user_id, guild_id, total_shop_buys=value)
    elif stat_type == "shop_spend":
        await update_user(user_id, guild_id, total_shop_spent=value)

# ========== ПОГОДА ==========
async def get_weather_data(lat, lon, forecast_days=7):
    params = {"latitude": lat, "longitude": lon, "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "weather_code", "wind_speed_10m"], "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"], "timezone": "auto", "forecast_days": forecast_days}
    try:
        responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
        return responses[0]
    except: return None

@bot.command()
async def weather(ctx, *, city: str = None):
    if not city: return await ctx.send("🌤️ `j.weather Москва`\n`j.weather_today` `j.weather_3days` `j.weather_7days` `j.weather_hourly`")
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
    current = response.Current()
    weather_code = int(current.Variables(4).Value())
    weather_text, weather_color = WEATHER_CODES.get(weather_code, ("🌡️", 0x808080))
    daily = response.Daily()
    daily_times = daily.Time()
    daily_weather = daily.Variables(0).ValuesAsNumpy()
    daily_temp_max = daily.Variables(1).ValuesAsNumpy()
    daily_temp_min = daily.Variables(2).ValuesAsNumpy()
    daily_precip = daily.Variables(3).ValuesAsNumpy()
    embed = discord.Embed(title=f"🌤️ ПОГОДА | {city_name}", description=weather_text, color=weather_color)
    forecast_text = ""
    for i in range(min(7, len(daily_times))):
        date = datetime.fromtimestamp(daily_times[i]).strftime("%d.%m")
        icon, _ = WEATHER_CODES.get(int(daily_weather[i]), ("🌡️", 0))
        forecast_text += f"**{date}** {icon} {daily_temp_min[i]:.0f}°…{daily_temp_max[i]:.0f}° | 💧{daily_precip[i]:.1f}мм\n"
    embed.add_field(name="📅 ПРОГНОЗ НА 7 ДНЕЙ", value=forecast_text[:1024], inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def weather_today(ctx, *, city: str = None):
    if not city: return await ctx.send("❌ Укажите город")
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
    response = await get_weather_data(lat, lon, 1)
    if not response: return await ctx.send("❌ Ошибка данных")
    daily = response.Daily()
    icon, _ = WEATHER_CODES.get(int(daily.Variables(0).ValuesAsNumpy()[0]), ("🌡️", 0))
    temp_max = daily.Variables(1).ValuesAsNumpy()[0]
    temp_min = daily.Variables(2).ValuesAsNumpy()[0]
    precip = daily.Variables(3).ValuesAsNumpy()[0]
    embed = discord.Embed(title=f"🌤️ ПОГОДА НА СЕГОДНЯ | {city_name}", description=icon, color=discord.Color.blue())
    embed.add_field(name="🌡️ Температура", value=f"{temp_min:.0f}°…{temp_max:.0f}°C", inline=True)
    embed.add_field(name="🌧️ Осадки", value=f"{precip:.1f} мм", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def weather_3days(ctx, *, city: str = None):
    if not city: return await ctx.send("❌ Укажите город")
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
    response = await get_weather_data(lat, lon, 3)
    if not response: return await ctx.send("❌ Ошибка данных")
    daily = response.Daily()
    times = daily.Time()
    codes = daily.Variables(0).ValuesAsNumpy()
    temp_max = daily.Variables(1).ValuesAsNumpy()
    temp_min = daily.Variables(2).ValuesAsNumpy()
    precip = daily.Variables(3).ValuesAsNumpy()
    embed = discord.Embed(title=f"🌤️ ПРОГНОЗ НА 3 ДНЯ | {city_name}", color=discord.Color.blue())
    for i in range(3):
        date = datetime.fromtimestamp(times[i]).strftime("%d.%m")
        icon, _ = WEATHER_CODES.get(int(codes[i]), ("🌡️", 0))
        embed.add_field(name=f"{date} {icon}", value=f"{temp_min[i]:.0f}°…{temp_max[i]:.0f}° | 💧{precip[i]:.1f}мм", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def weather_7days(ctx, *, city: str = None):
    if not city: return await ctx.send("❌ Укажите город")
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
    if not response: return await ctx.send("❌ Ошибка данных")
    daily = response.Daily()
    times = daily.Time()
    codes = daily.Variables(0).ValuesAsNumpy()
    temp_max = daily.Variables(1).ValuesAsNumpy()
    temp_min = daily.Variables(2).ValuesAsNumpy()
    precip = daily.Variables(3).ValuesAsNumpy()
    embed = discord.Embed(title=f"🌤️ ПРОГНОЗ НА 7 ДНЕЙ | {city_name}", color=discord.Color.blue())
    text = ""
    for i in range(len(times)):
        date = datetime.fromtimestamp(times[i]).strftime("%d.%m")
        icon, _ = WEATHER_CODES.get(int(codes[i]), ("🌡️", 0))
        text += f"**{date}** {icon} {temp_min[i]:.0f}°…{temp_max[i]:.0f}° | 💧{precip[i]:.1f}мм\n"
    embed.description = text[:2000]
    await ctx.send(embed=embed)

@bot.command()
async def weather_hourly(ctx, *, city: str = None):
    if not city: return await ctx.send("❌ Укажите город")
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
    params = {"latitude": lat, "longitude": lon, "hourly": ["temperature_2m", "precipitation_probability", "weather_code"], "timezone": "auto", "forecast_days": 1}
    try:
        responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
        response = responses[0]
        hourly = response.Hourly()
        times = hourly.Time()
        temps = hourly.Variables(0).ValuesAsNumpy()
        probs = hourly.Variables(1).ValuesAsNumpy()
        codes = hourly.Variables(2).ValuesAsNumpy()
        embed = discord.Embed(title=f"🌤️ ПОЧАСОВОЙ ПРОГНОЗ | {city_name}", color=discord.Color.blue())
        text = ""
        for i in range(24):
            if i >= len(times): break
            hour = datetime.fromtimestamp(times[i]).hour
            icon, _ = WEATHER_CODES.get(int(codes[i]), ("🌡️", 0))
            text += f"**{hour}:00** {icon} {temps[i]:.0f}°C ☔{probs[i]:.0f}%\n"
        embed.description = text[:2000]
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {str(e)[:200]}")

# ========== ИИ ==========
async def get_ai_response(user_id, user_message):
    global user_conversations
    lower_msg = user_message.lower()
    if any(x in lower_msg for x in ["привет", "здравствуй"]): return "👋 Привет!"
    if "как дела" in lower_msg: return "😊 Всё отлично!"
    if "спасибо" in lower_msg: return "🙏 Пожалуйста!"
    if any(x in lower_msg for x in ["дата", "сегодня"]): return f"📅 Сегодня {datetime.now().strftime('%d.%m.%Y')}"
    if any(x in lower_msg for x in ["время", "который час"]): return f"🕐 Сейчас {datetime.now().strftime('%H:%M:%S')}"
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

# ========== АВТОМОДЕРАЦИЯ ==========
async def check_spam(message):
    user_id = message.author.id
    content = message.content.strip().lower()
    now = time.time()
    settings = guild_settings.get(message.guild.id, {})
    for word in settings.get("automod_bad_words", []):
        if word in content:
            spam_messages_to_delete[user_id].append(message.id)
            return True, f"запрещённое слово: {word}"
    if settings.get("automod_invites_enabled", True):
        if "discord.gg/" in content or "discord.com/invite/" in content:
            spam_messages_to_delete[user_id].append(message.id)
            return True, "реклама сервера"
    if settings.get("automod_phishing_enabled", True):
        if ("free" in content or "giveaway" in content) and ("nitro" in content or "steam" in content):
            spam_messages_to_delete[user_id].append(message.id)
            return True, "подозрение на фишинг"
    if user_id not in user_message_timestamps: user_message_timestamps[user_id] = []
    user_message_timestamps[user_id].append(now)
    spam_messages_to_delete[user_id].append(message.id)
    cutoff = now - ANTISPAM_WINDOW_SECONDS
    old_indices = [i for i, t in enumerate(user_message_timestamps[user_id]) if t < cutoff]
    for i in sorted(old_indices, reverse=True):
        user_message_timestamps[user_id].pop(i)
        spam_messages_to_delete[user_id].pop(i)
    if len(user_message_timestamps[user_id]) > ANTISPAM_MAX_MESSAGES:
        return True, f"флуд ({len(user_message_timestamps[user_id])} сообщений)"
    return False, None

async def add_auto_warning(user, reason, channel):
    user_id = user.id
    now = time.time()
    user_warnings[user_id] = [w for w in user_warnings[user_id] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    user_warnings[user_id].append({"reason": reason, "time": now, "moderator": "Automod"})
    warning_count = len(user_warnings[user_id])
    embed = discord.Embed(title="⚠️ АВТОМАТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ", color=discord.Color.orange(), timestamp=datetime.now())
    embed.add_field(name="👤 Пользователь", value=f"{user.mention}\n{user.name}", inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=True)
    embed.add_field(name="📊 Всего варнов", value=f"{warning_count}/{ANTISPAM_MAX_WARNINGS}", inline=True)
    await send_log(user.guild.id, embed)
    if warning_count >= ANTISPAM_MAX_WARNINGS:
        alert = discord.Embed(title="🚨 ПРЕВЫШЕН ЛИМИТ ПРЕДУПРЕЖДЕНИЙ", description=f"{user.mention} получил {warning_count} предупреждений за 24 часа", color=discord.Color.red())
        await send_log(user.guild.id, alert)
    return warning_count

async def send_warning_dm(user, reason, wc, channel):
    try:
        await user.send(f"⚠️ **Автомодерация**\nВаши сообщения в {channel.mention} удалены\nПричина: {reason}\nПредупреждений: {wc}/{ANTISPAM_MAX_WARNINGS}")
    except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def automod(ctx, action: str = None, module: str = None, *args):
    if ctx.guild.id not in guild_settings: guild_settings[ctx.guild.id] = {}
    settings = guild_settings[ctx.guild.id]
    if "automod_enabled" not in settings:
        settings.update({"automod_enabled": True, "automod_bad_words": [], "automod_invites_enabled": True, "automod_phishing_enabled": True, "automod_exempt_roles": []})
    if action is None or action == "status":
        embed = discord.Embed(title="⚙️ АВТОМОДЕРАЦИЯ", color=discord.Color.blue())
        embed.add_field(name="📊 Статус", value="✅ ВКЛ" if settings["automod_enabled"] else "❌ ВЫКЛ", inline=False)
        embed.add_field(name="📝 Запрещённые слова", value=f"{len(settings['automod_bad_words'])} слов", inline=True)
        embed.add_field(name="🚫 Реклама", value="✅ ВКЛ" if settings["automod_invites_enabled"] else "❌ ВЫКЛ", inline=True)
        embed.add_field(name="🎣 Фишинг", value="✅ ВКЛ" if settings["automod_phishing_enabled"] else "❌ ВЫКЛ", inline=True)
        roles = [ctx.guild.get_role(rid).mention for rid in settings["automod_exempt_roles"] if ctx.guild.get_role(rid)]
        embed.add_field(name="👑 Исключённые", value=", ".join(roles) if roles else "Нет", inline=False)
        await ctx.send(embed=embed)
        return
    if action == "enable": settings["automod_enabled"] = True; await ctx.send("✅ Автомод ВКЛ")
    elif action == "disable": settings["automod_enabled"] = False; await ctx.send("❌ Автомод ВЫКЛ")
    elif action == "words":
        if module == "add" and len(args)>=2:
            word = " ".join(args[1:]).lower()
            if word not in settings["automod_bad_words"]: settings["automod_bad_words"].append(word); await ctx.send(f"✅ Добавлено: {word}")
        elif module == "remove" and len(args)>=2:
            word = " ".join(args[1:]).lower()
            if word in settings["automod_bad_words"]: settings["automod_bad_words"].remove(word); await ctx.send(f"✅ Удалено: {word}")
        elif module == "list": await ctx.send(f"📝 Слова: {', '.join(settings['automod_bad_words']) if settings['automod_bad_words'] else 'пусто'}")
        elif module == "clear": settings["automod_bad_words"] = []; await ctx.send("✅ Очищено")
    elif action == "invites":
        if args[0]=="on": settings["automod_invites_enabled"]=True; await ctx.send("✅ Реклама включена")
        elif args[0]=="off": settings["automod_invites_enabled"]=False; await ctx.send("❌ Реклама выключена")
    elif action == "phishing":
        if args[0]=="on": settings["automod_phishing_enabled"]=True; await ctx.send("✅ Фишинг включён")
        elif args[0]=="off": settings["automod_phishing_enabled"]=False; await ctx.send("❌ Фишинг выключен")
    elif action == "exempt":
        if module == "add" and ctx.message.role_mentions:
            role = ctx.message.role_mentions[0]
            if role.id not in settings["automod_exempt_roles"]: settings["automod_exempt_roles"].append(role.id); await ctx.send(f"✅ {role.mention} исключена")
        elif module == "remove" and ctx.message.role_mentions:
            role = ctx.message.role_mentions[0]
            if role.id in settings["automod_exempt_roles"]: settings["automod_exempt_roles"].remove(role.id); await ctx.send(f"✅ {role.mention} удалена")
        elif module == "list": await ctx.send(f"👑 Исключённые: {', '.join([ctx.guild.get_role(rid).mention for rid in settings['automod_exempt_roles'] if ctx.guild.get_role(rid)]) or 'Нет'}")

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
@commands.has_permissions(administrator=True)
async def take(ctx, member: discord.Member, amount: int):
    await add_balance(member.id, ctx.guild.id, -amount)
    await ctx.send(f"✅ Забрано {amount} 💎 у {member.mention}")

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
async def weekly(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    last = d[11] if len(d)>11 else None
    if last:
        ld = datetime.fromisoformat(last)
        if (datetime.now()-ld).days < 7:
            return await ctx.send("⏰ Через неделю")
    earn = random.randint(3000, 6000)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    await update_user(ctx.author.id, ctx.guild.id, last_weekly=datetime.now().isoformat())
    await ctx.send(f"🎁 +{earn} 💎")

@bot.command()
async def monthly(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    last = d[12] if len(d)>12 else None
    if last:
        ld = datetime.fromisoformat(last)
        if (datetime.now()-ld).days < 30:
            return await ctx.send("⏰ Через месяц")
    earn = random.randint(10000, 20000)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    await update_user(ctx.author.id, ctx.guild.id, last_monthly=datetime.now().isoformat())
    await ctx.send(f"🎁 +{earn} 💎")

@bot.command()
async def work(ctx):
    can, w = check_cooldown(ctx.author.id, "work")
    if not can: 
        if w is not None:
            return await ctx.send(f"❌ КД {w//60}мин")
        return await ctx.send("❌ Подождите немного")
    earn = random.randint(300, 800)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    set_cooldown(ctx.author.id, "work")
    await ctx.send(f"💼 +{earn} 💎")
    await check_daily_quest(ctx.author.id, ctx.guild.id, "work", 1)
    await update_user_stats(ctx.author.id, ctx.guild.id, "work", 1)

@bot.command()
async def rob(ctx, member: discord.Member):
    if member==ctx.author: return await ctx.send("❌ Себя нельзя")
    can, w = check_cooldown(ctx.author.id, "rob")
    if not can: 
        if w is not None:
            return await ctx.send(f"❌ КД {w//60}мин")
        return await ctx.send("❌ Подождите немного")
    td = await get_user(member.id, ctx.guild.id)
    if td[4] < 500: return await ctx.send(f"❌ У {member.mention} мало денег")
    success = random.random() < WIN_CHANCE["rob"]
    set_cooldown(ctx.author.id, "rob")
    if success:
        steal = random.randint(100, int(td[4] * 0.3))
        await add_balance(ctx.author.id, ctx.guild.id, steal)
        await add_balance(member.id, ctx.guild.id, -steal)
        await ctx.send(f"🔫 Ограбление удалось! +{steal} 💎")
        await check_daily_quest(ctx.author.id, ctx.guild.id, "rob", 1)
        await update_user_stats(ctx.author.id, ctx.guild.id, "rob_success", 1)
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
    if not can: 
        if w is not None:
            return await ctx.send(f"❌ КД {w//60}мин")
        return await ctx.send("❌ Подождите немного")
    set_rep_cooldown(ctx.author.id, member.id)
    nr = await add_reputation(member.id, ctx.guild.id, 1)
    await ctx.send(f"👍 +1 репутации {member.mention}! Теперь {nr}")
    await check_daily_quest(ctx.author.id, ctx.guild.id, "give_rep", 1)

@bot.command()
async def minusrep(ctx, member: discord.Member):
    if member==ctx.author: return await ctx.send("❌ Себе нельзя")
    can, w = check_rep_cooldown(ctx.author.id, member.id)
    if not can: 
        if w is not None:
            return await ctx.send(f"❌ КД {w//60}мин")
        return await ctx.send("❌ Подождите немного")
    set_rep_cooldown(ctx.author.id, member.id)
    nr = await add_reputation(member.id, ctx.guild.id, -1)
    await ctx.send(f"👎 -1 репутации {member.mention}! Теперь {nr}")

# ========== ИГРЫ ==========
@bot.command()
async def casino(ctx, amount: int = None):
    if not amount: return await ctx.send("🎰 j.casino 100")
    can, w = check_cooldown(ctx.author.id, "casino")
    if not can: 
        if w is not None:
            return await ctx.send(f"⏰ {w}сек")
        return await ctx.send("⏰ Подождите немного")
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
        await update_user_stats(ctx.author.id, ctx.guild.id, "casino_win", 1)
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await msg.edit(content=f"🎰 **ПРОИГРЫШ! -{amount} 💎**")

@bot.command()
async def slots(ctx, bet: int = None):
    if not bet: return await ctx.send("🎰 j.slots 100")
    can, w = check_cooldown(ctx.author.id, "casino")
    if not can: 
        if w is not None:
            return await ctx.send(f"⏰ {w}сек")
        return await ctx.send("⏰ Подождите немного")
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
    if not can: 
        if w is not None:
            return await ctx.send(f"⏰ {w}сек")
        return await ctx.send("⏰ Подождите немного")
    if num<1 or num>6: return await ctx.send("❌ 1-6")
    if bet<100: return await ctx.send("❌ Мин. 100 💎")
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal<bet: return await ctx.send(f"❌ Не хватает")
    msg = await ctx.send(f"🎲 {ctx.author.mention} бросает...")
    for _ in range(2):
        await asyncio.sleep(0.3)
        await msg.edit(content=f"🎲 {random.choice(DICE_EMOJIS)}")
    roll = random.randint(1,6)
    set_cooldown(ctx.author.id, "dice")
    if roll == num:
        win = bet * 6
        await add_balance(ctx.author.id, ctx.guild.id, win)
        await msg.edit(content=f"🎲 **{roll}!** УГАДАЛ! +{win} 💎")
        await check_daily_quest(ctx.author.id, ctx.guild.id, "dice_win", 1)
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🎲 **{roll}!** НЕ УГАДАЛ! -{bet} 💎")

@bot.command()
async def coinflip(ctx, side: str = None, bet: int = None):
    if not side or not bet: return await ctx.send("🪙 j.coinflip орёл 100")
    can, w = check_cooldown(ctx.author.id, "coin")
    if not can: 
        if w is not None:
            return await ctx.send(f"⏰ {w}сек")
        return await ctx.send("⏰ Подождите немного")
    side=side.lower()
    if side not in ["орёл","орел","решка"]: return await ctx.send("❌ орёл/решка")
    if bet<100: return await ctx.send("❌ Мин. 100 💎")
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal<bet: return await ctx.send(f"❌ Не хватает")
    msg = await ctx.send(f"🪙 {ctx.author.mention} подбрасывает...")
    await asyncio.sleep(0.5)
    res = random.choice(["орёл","решка"])
    win = random.random() < WIN_CHANCE["coin"]
    set_cooldown(ctx.author.id, "coin")
    if (side in ["орёл","орел"] and res=="орёл" and win) or (side=="решка" and res=="решка" and win):
        wa = bet * 2
        await add_balance(ctx.author.id, ctx.guild.id, wa)
        await msg.edit(content=f"🪙 {res.upper()}! УГАДАЛ! +{wa} 💎")
        await check_daily_quest(ctx.author.id, ctx.guild.id, "coin_win", 1)
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🪙 {res.upper()}! НЕ УГАДАЛ! -{bet} 💎")

@bot.command()
async def rps(ctx, choice: str = None, bet: int = None):
    if not choice or not bet: return await ctx.send("✊ j.rps камень 100")
    can, w = check_cooldown(ctx.author.id, "rps")
    if not can: 
        if w is not None:
            return await ctx.send(f"⏰ {w}сек")
        return await ctx.send("⏰ Подождите немного")
    choice=choice.lower()
    if choice not in ["камень","ножницы","бумага"]: return await ctx.send("❌ камень/ножницы/бумага")
    if bet<100: return await ctx.send("❌ Мин. 100 💎")
    bal = (await get_user(ctx.author.id, ctx.guild.id))[4]
    if bal<bet: return await ctx.send(f"❌ Не хватает")
    botc = random.choice(["камень","ножницы","бумага"])
    msg = await ctx.send(f"✊ {ctx.author.mention} vs бот...")
    await asyncio.sleep(0.5)
    win = random.random() < WIN_CHANCE["rps"]
    set_cooldown(ctx.author.id, "rps")
    if choice == botc:
        await msg.edit(content=f"✊ {choice} vs {botc} → НИЧЬЯ!")
        return
    if (choice=="камень" and botc=="ножницы") or (choice=="ножницы" and botc=="бумага") or (choice=="бумага" and botc=="камень"):
        if win:
            wa = bet * 2
            await add_balance(ctx.author.id, ctx.guild.id, wa)
            await msg.edit(content=f"✊ {choice} vs {botc} → ВЫИГРЫШ! +{wa} 💎")
            await check_daily_quest(ctx.author.id, ctx.guild.id, "rps_win", 1)
        else:
            await add_balance(ctx.author.id, ctx.guild.id, -bet)
            await msg.edit(content=f"✊ {choice} vs {botc} → ПРОИГРЫШ! -{bet} 💎")
    else:
        if win:
            wa = bet * 2
            await add_balance(ctx.author.id, ctx.guild.id, wa)
            await msg.edit(content=f"✊ {choice} vs {botc} → ВЫИГРЫШ! +{wa} 💎")
            await check_daily_quest(ctx.author.id, ctx.guild.id, "rps_win", 1)
        else:
            await add_balance(ctx.author.id, ctx.guild.id, -bet)
            await msg.edit(content=f"✊ {choice} vs {botc} → ПРОИГРЫШ! -{bet} 💎")

@bot.command()
async def blackjack(ctx, bet: int = None):
    if not bet: return await ctx.send("🃏 j.blackjack 100")
    can, w = check_cooldown(ctx.author.id, "blackjack")
    if not can: 
        if w is not None:
            return await ctx.send(f"⏰ {w}сек")
        return await ctx.send("⏰ Подождите немного")
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
                await i.response.edit_message(content=f"🃏 **ПЕРЕБОР!**\n{' '.join(player)} ({pv})\nДилер: {' '.join(dealer)} ({hv(dealer)})\n-{bet} 💎", view=None)
                self.ended=True
                set_cooldown(ctx.author.id, "blackjack")
                return
            await i.response.edit_message(content=f"🃏 БЛЭКДЖЕК\nВаши: {' '.join(player)} ({pv})\nДилер: {dealer[0]} ?")
        @discord.ui.button(label="Стоп", style=discord.ButtonStyle.success)
        async def stand(self, i, b):
            if i.user.id!=ctx.author.id: return await i.response.send_message("❌ Не ваша игра!", ephemeral=True)
            pv=hv(player); dv=hv(dealer)
            while dv<17: dealer.append(deck.pop()); dv=hv(dealer)
            win=random.random()<WIN_CHANCE["blackjack"]
            set_cooldown(ctx.author.id, "blackjack")
            if dv>21 or (pv>dv and win):
                wa=bet*2
                await add_balance(ctx.author.id, ctx.guild.id, wa)
                await i.response.edit_message(content=f"🃏 **ВЫИГРЫШ!**\nВаши: {' '.join(player)} ({pv})\nДилер: {' '.join(dealer)} ({dv})\n+{wa} 💎", view=None)
                await check_daily_quest(ctx.author.id, ctx.guild.id, "bj_win", 1)
                await update_user_stats(ctx.author.id, ctx.guild.id, "blackjack_win", 1)
            elif pv==dv:
                await add_balance(ctx.author.id, ctx.guild.id, bet)
                await i.response.edit_message(content=f"🃏 **НИЧЬЯ!**\n{' '.join(player)} ({pv})\n{' '.join(dealer)} ({dv})", view=None)
            else:
                await i.response.edit_message(content=f"🃏 **ПРОИГРЫШ!**\n{' '.join(player)} ({pv})\n{' '.join(dealer)} ({dv})", view=None)
            self.ended=True
        async def on_timeout(self):
            if not self.ended:
                await msg.edit(content="⏰ Время вышло! Ставка возвращена", view=None)
                await add_balance(ctx.author.id, ctx.guild.id, bet)
    view = BJView()
    await msg.edit(view=view)

# ========== ФЕРМА ==========
@bot.command()
async def farm(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    pots = data[28] if len(data) > 28 else 0
    crops = json.loads(data[29] if len(data) > 29 else "[]")
    embed = discord.Embed(title="🌾 ФЕРМА", color=discord.Color.green())
    embed.add_field(name="🏺 Горшки", value=f"{pots}/10", inline=True)
    embed.add_field(name="🌱 Посажено", value=f"{len(crops)} культур", inline=True)
    if crops:
        text = ""
        for i, c in enumerate(crops[:10]):
            if c:
                planted = datetime.fromisoformat(c["planted_at"])
                left = (planted + timedelta(seconds=SEEDS[c["seed"]]["grow_time"]) - datetime.now())
                status = f"🌱 {int(left.total_seconds()//3600)}ч {int((left.total_seconds()%3600)//60)}мин" if left.total_seconds() > 0 else "✅ ГОТОВО!"
                text += f"**{i+1}.** {c['seed'].capitalize()} ({c['rarity']}) - {status}\n"
        embed.add_field(name="📋 Посевы", value=text[:1024], inline=False)
    embed.set_footer(text="j.buy_pot | j.buy_seed | j.plant | j.harvest | j.sell_crop")
    await ctx.send(embed=embed)

@bot.command()
async def buy_pot(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    pots = data[28] if len(data) > 28 else 0
    if pots >= 10: return await ctx.send("❌ Максимум 10 горшков!")
    price = 2000 * (pots + 1)
    if data[4] < price: return await ctx.send(f"❌ Нужно {price} 💎")
    await add_balance(ctx.author.id, ctx.guild.id, -price)
    await update_user(ctx.author.id, ctx.guild.id, pots=pots + 1)
    await ctx.send(f"✅ Куплен горшок №{pots+1} за {price} 💎")

@bot.command()
async def buy_seed(ctx, seed: str = None):
    if not seed or seed.lower() not in SEEDS:
        return await ctx.send(f"🌱 Семена: {', '.join(SEEDS.keys())}")
    seed = seed.lower()
    price = SEEDS[seed]["price"]
    if (await get_user(ctx.author.id, ctx.guild.id))[4] < price:
        return await ctx.send(f"❌ Нужно {price} 💎")
    await add_balance(ctx.author.id, ctx.guild.id, -price)
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        inv.append(f"seed_{seed}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"✅ Куплены семена {seed.capitalize()} за {price} 💎")

@bot.command()
async def plant(ctx, pot: int = None, seed: str = None):
    if not pot or not seed: return await ctx.send("❌ j.plant <номер> <семя>")
    data = await get_user(ctx.author.id, ctx.guild.id)
    pots = data[28] if len(data) > 28 else 0
    if pot < 1 or pot > pots: return await ctx.send(f"❌ Нет горшка №{pot}")
    crops = json.loads(data[29] if len(data) > 29 else "[]")
    if pot-1 < len(crops) and crops[pot-1] and crops[pot-1].get("planted_at"):
        return await ctx.send(f"❌ Горшок №{pot} занят!")
    seed = seed.lower()
    if seed not in SEEDS: return await ctx.send("❌ Нет такого семени")
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        if f"seed_{seed}" not in inv: return await ctx.send(f"❌ Нет семян {seed}")
        inv.remove(f"seed_{seed}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
    weights = SEEDS[seed]["rarity_weights"]
    rarity = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    while len(crops) < pot: crops.append(None)
    crops[pot-1] = {"seed": seed, "planted_at": datetime.now().isoformat(), "rarity": rarity}
    await update_user(ctx.author.id, ctx.guild.id, crops=json.dumps(crops))
    await ctx.send(f"✅ Посажен {seed} ({rarity}) в горшок №{pot}!")
    await check_daily_quest(ctx.author.id, ctx.guild.id, "plant", 1)
    await update_user_stats(ctx.author.id, ctx.guild.id, "plant", 1)

@bot.command()
async def harvest(ctx, pot: int = None):
    if not pot: return await ctx.send("❌ j.harvest <номер>")
    data = await get_user(ctx.author.id, ctx.guild.id)
    if pot < 1 or pot > (data[28] if len(data) > 28 else 0):
        return await ctx.send(f"❌ Нет горшка №{pot}")
    crops = json.loads(data[29] if len(data) > 29 else "[]")
    if pot-1 >= len(crops) or not crops[pot-1]:
        return await ctx.send(f"❌ Горшок №{pot} пуст")
    crop = crops[pot-1]
    planted = datetime.fromisoformat(crop["planted_at"])
    ready = planted + timedelta(seconds=SEEDS[crop["seed"]]["grow_time"])
    if datetime.now() < ready:
        left = ready - datetime.now()
        return await ctx.send(f"❌ Осталось {int(left.total_seconds()//3600)}ч {int((left.total_seconds()%3600)//60)}мин")
    price = int(SEEDS[crop["seed"]]["base_price"] * RARITY_MULTIPLIERS.get(crop["rarity"], 1.0))
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        inv.append(f"crop_{crop['seed']}_{crop['rarity']}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
    crops[pot-1] = None
    await update_user(ctx.author.id, ctx.guild.id, crops=json.dumps(crops))
    await add_balance(ctx.author.id, ctx.guild.id, price)
    await ctx.send(f"✅ Собран {crop['seed']} ({crop['rarity']}) с горшка №{pot}!\n💰 +{price} 💎")
    await check_daily_quest(ctx.author.id, ctx.guild.id, "harvest", 1)
    await update_user_stats(ctx.author.id, ctx.guild.id, "harvest", 1)

@bot.command()
async def sell_crop(ctx, crop: str = None, rarity: str = None):
    if not crop or not rarity: return await ctx.send("❌ j.sell_crop <культура> <редкость>")
    crop = crop.lower()
    if crop not in SEEDS: return await ctx.send("❌ Нет такой культуры")
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        item = f"crop_{crop}_{rarity}"
        if item not in inv: return await ctx.send(f"❌ Нет {crop} ({rarity})")
        inv.remove(item)
        price = int(SEEDS[crop]["base_price"] * RARITY_MULTIPLIERS.get(rarity, 1.0))
        await add_balance(ctx.author.id, ctx.guild.id, price)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"💰 Продано {crop} ({rarity}) за {price} 💎")

@bot.command()
async def sell_all_crops(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        crops = [i for i in inv if i.startswith("crop_")]
        if not crops: return await ctx.send("❌ Нет урожая")
        total = 0
        for item in crops:
            parts = item.split("_")
            if len(parts) >= 3:
                total += int(SEEDS.get(parts[1], {}).get("base_price", 100) * RARITY_MULTIPLIERS.get(parts[2], 1.0))
                inv.remove(item)
        await add_balance(ctx.author.id, ctx.guild.id, total)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"💰 Продано всё за {total} 💎")

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
    data = await get_user(user_id, ctx.guild.id)
    inv = json.loads(data[19] if len(data) > 19 else "[]")
    rod = "простая"
    for r in FISHING_RODS:
        if f"rod_{r}" in inv: rod = r
    fishing_cooldowns[user_id] = now
    msg = await ctx.send(f"🎣 Заброс... {FISHING_RODS[rod]['emoji']}")
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
    inv.append(f"fish_{fish}")
    await update_user(user_id, ctx.guild.id, inventory=json.dumps(inv))
    await add_xp(user_id, ctx.guild.id, exp)
    embed = discord.Embed(title=f"{fd['emoji']} {fish}!", color=discord.Color.gold())
    embed.add_field(name="💰 Цена", value=f"{price} 💎", inline=True)
    embed.add_field(name="✨ Опыт", value=f"+{exp} XP", inline=True)
    await msg.edit(content=None, embed=embed)
    await check_daily_quest(ctx.author.id, ctx.guild.id, "fish", 1)
    await update_user_stats(ctx.author.id, ctx.guild.id, "fish", 1)
    if fish in ["осётр", "белуга", "сазан"]:
        await update_user_stats(ctx.author.id, ctx.guild.id, "legendary_fish", 1)
    if fish in ["золотая рыбка", "морской царь"]:
        await update_user_stats(ctx.author.id, ctx.guild.id, "mythic_fish", 1)

@bot.command()
async def buy_rod(ctx, rod_name: str = None):
    if not rod_name: return await ctx.send("Удочки: простая, улучшенная, золотая")
    rod_name = rod_name.lower()
    if rod_name not in FISHING_RODS: return await ctx.send("Нет такой удочки")
    rod = FISHING_RODS[rod_name]
    data = await get_user(ctx.author.id, ctx.guild.id)
    if data[4] < rod["price"]: return await ctx.send(f"❌ Нужно {rod['price']} 💎")
    inv = json.loads(data[19] if len(data) > 19 else "[]")
    if f"rod_{rod_name}" in inv: return await ctx.send("Уже есть")
    inv.append(f"rod_{rod_name}")
    await add_balance(ctx.author.id, ctx.guild.id, -rod["price"])
    await update_user(ctx.author.id, ctx.guild.id, inventory=json.dumps(inv))
    await ctx.send(f"✅ Куплена {rod_name} {rod['emoji']}")

@bot.command()
async def sell_all(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    inv = json.loads(data[19] if len(data) > 19 else "[]")
    fish = [i for i in inv if i.startswith("fish_")]
    if not fish: return await ctx.send("Нет рыбы")
    total = sum(FISHING_ITEMS[f.replace("fish_", "")]["price"] for f in fish)
    inv = [i for i in inv if not i.startswith("fish_")]
    await add_balance(ctx.author.id, ctx.guild.id, total)
    await update_user(ctx.author.id, ctx.guild.id, inventory=json.dumps(inv))
    await ctx.send(f"✅ Продано за {total} 💎")

# ========== МАГАЗИН ==========
@bot.command()
async def shop(ctx, category: str = None):
    embed = discord.Embed(title="🛍️ МАГАЗИН", color=discord.Color.gold())
    if not category or category == "алкоголь":
        text = "\n".join([f"**{n}** - {d['price']} 💎 | {d['desc']}" for n, d in SHOP_ITEMS.items() if d.get("type") == "consumable"])
        embed.add_field(name="🍺 АЛКОГОЛЬ", value=text or "Нет", inline=False)
    if not category or category == "украшения":
        text = "\n".join([f"**{n}** - {d['price']} 💎 | {d['desc']}" for n, d in SHOP_ITEMS.items() if d.get("type") == "award"])
        embed.add_field(name="✨ УКРАШЕНИЯ", value=text or "Нет", inline=False)
    if not category or category == "цвета":
        text = "\n".join([f"**{n}** - {d['price']} 💎 | {d['desc']}" for n, d in SHOP_ITEMS.items() if d.get("type") == "color"])
        embed.add_field(name="🎨 ЦВЕТА", value=text or "Нет", inline=False)
    if not category or category == "бустеры":
        text = "\n".join([f"**{n}** - {d['price']} 💎 | {d['desc']}" for n, d in SHOP_ITEMS.items() if d.get("type") == "booster"])
        embed.add_field(name="⚡ БУСТЕРЫ", value=text or "Нет", inline=False)
    if not category or category == "роли":
        text = "\n".join([f"**{n}** - {d['price']} 💎 | {d['desc']}" for n, d in SHOP_ITEMS.items() if d.get("type") == "role"])
        embed.add_field(name="👑 РОЛИ", value=text or "Нет", inline=False)
    if not category or category == "лотерея":
        text = "\n".join([f"**{n}** - {d['price']} 💎 | {d['desc']}" for n, d in SHOP_ITEMS.items() if d.get("type") == "lottery"])
        embed.add_field(name="🎫 ЛОТЕРЕЯ", value=text or "Нет", inline=False)
    if CUSTOM_SHOP_ITEMS:
        text = "\n".join([f"**{n}** - {d['price']} 💎 | {d['desc']}" for n, d in CUSTOM_SHOP_ITEMS.items()])
        embed.add_field(name="📦 КАСТОМНЫЕ", value=text, inline=False)
    embed.set_footer(text="j.buy <товар> | j.use <предмет> | j.inventory")
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, *, item: str = None):
    if not item: return await ctx.send("❌ j.buy <товар>")
    item = item.lower()
    if item not in SHOP_ITEMS and item not in CUSTOM_SHOP_ITEMS:
        return await ctx.send("❌ Нет такого товара")
    data = SHOP_ITEMS.get(item) or CUSTOM_SHOP_ITEMS.get(item)
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < data["price"]: return await ctx.send(f"❌ Нужно {data['price']} 💎")
    await add_balance(ctx.author.id, ctx.guild.id, -data["price"])
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        inv.append(item)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        if data.get("type") == "color" and "color_code" in data:
            await db.execute('UPDATE users SET profile_color=? WHERE user_id=? AND guild_id=?', (data["color_code"], ctx.author.id, ctx.guild.id))
        if data.get("type") == "role" and data.get("role_id"):
            role = ctx.guild.get_role(data["role_id"])
            if role: await ctx.author.add_roles(role)
        if data.get("type") == "booster":
            if "exp" in item.lower():
                active_boosters[ctx.author.id]["exp"] = {"mult": 2 if "x2" in item else 5, "end": time.time() + data["duration"]}
            elif "денег" in item.lower():
                active_boosters[ctx.author.id]["money"] = {"mult": 2 if "x2" in item else 5, "end": time.time() + data["duration"]}
        await db.commit()
    await ctx.send(f"✅ {ctx.author.mention} купил **{item}** за {data['price']} 💎!")
    await check_daily_quest(ctx.author.id, ctx.guild.id, "buy", 1)
    await update_user_stats(ctx.author.id, ctx.guild.id, "shop_buy", 1)
    await update_user_stats(ctx.author.id, ctx.guild.id, "shop_spend", data["price"])

@bot.command()
async def use(ctx, *, item: str = None):
    if not item: return await ctx.send("❌ j.use <предмет>")
    item = item.lower()
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        if item not in inv: return await ctx.send(f"❌ Нет {item} в инвентаре")
        inv.remove(item)
        if item == "лотерейный билет":
            win = random.randint(0, 100)
            if win < 10:
                prize = random.randint(1000, 100000)
                await add_balance(ctx.author.id, ctx.guild.id, prize)
                await ctx.send(f"🎫 Вы выиграли {prize} 💎!")
            else:
                await ctx.send(f"🎫 К сожалению, ничего не выиграно")
        elif item in ["золотой слиток"]:
            sell_price = SHOP_ITEMS[item].get("sell_price", SHOP_ITEMS[item]["price"] // 2)
            await add_balance(ctx.author.id, ctx.guild.id, sell_price)
            await ctx.send(f"💰 Вы продали {item} за {sell_price} 💎")
        else:
            await ctx.send(f"✅ Использован {item}")
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await db.commit()

@bot.command()
async def inventory(ctx, member: discord.Member = None):
    target = member or ctx.author
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (target.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
    if not inv: return await ctx.send(f"📦 У {target.mention} пусто")
    items = {}
    for i in inv: items[i] = items.get(i, 0) + 1
    embed = discord.Embed(title=f"📦 Инвентарь {target.display_name}", color=discord.Color.blue())
    for i, c in list(items.items())[:20]:
        embed.add_field(name=f"🔹 {i}", value=f"Кол-во: {c}\n`j.use {i}`", inline=True)
    await ctx.send(embed=embed)

# ========== ПРОФИЛЬ ==========
@bot.command()
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = await get_user(target.id, ctx.guild.id)
    level, xp, bal = data[3], data[2], data[4]
    bank = data[5] if len(data) > 5 else 0
    rep = data[6] if len(data) > 6 else 0
    total_msgs = data[9] if len(data) > 9 else 0
    today_msgs = data[21] if len(data) > 21 else 0
    week_msgs = data[22] if len(data) > 22 else 0
    month_msgs = data[23] if len(data) > 23 else 0
    voice_streak = data[26] if len(data) > 26 else 0
    voice_seconds = data[32] if len(data) > 32 else 0
    bio = data[17] if len(data) > 17 and data[17] else "Нет биографии"
    gender = data[20] if len(data) > 20 else ""
    awards = json.loads(data[18] if len(data) > 18 else "[]")
    profile_color = data[31] if len(data) > 31 else 0x5865F2
    total_plants = data[40] if len(data) > 40 else 0
    total_harvests = data[39] if len(data) > 39 else 0
    total_fish = data[36] if len(data) > 36 else 0
    total_legendary_fish = data[37] if len(data) > 37 else 0
    total_mythic_fish = data[38] if len(data) > 38 else 0
    total_casino_wins = data[33] if len(data) > 33 else 0
    total_blackjack_wins = data[34] if len(data) > 34 else 0
    total_work = data[41] if len(data) > 41 else 0
    total_rob = data[42] if len(data) > 42 else 0
    voice_hours = voice_seconds // 3600
    voice_minutes = (voice_seconds % 3600) // 60
    xp_for_next = 200 * ((level + 1) ** 2)
    xp_for_current = 200 * (level ** 2)
    percent = min(100, int((xp - xp_for_current) / (xp_for_next - xp_for_current) * 100)) if xp_for_next > xp_for_current else 0
    bar = "█" * (percent // 5) + "░" * (20 - (percent // 5))
    gender_text = "👨 Мужчина" if gender == "male" else "👩 Женщина" if gender == "female" else "❓ Не указан"
    boosters_text = "Нет"
    if target.id in active_boosters:
        boosters = []
        if "exp" in active_boosters[target.id]:
            left = int(active_boosters[target.id]["exp"]["end"] - time.time())
            if left > 0:
                boosters.append(f"🔥 x{active_boosters[target.id]['exp']['mult']} ОПЫТ - {left//60}мин")
        if "money" in active_boosters[target.id]:
            left = int(active_boosters[target.id]["money"]["end"] - time.time())
            if left > 0:
                boosters.append(f"💰 x{active_boosters[target.id]['money']['mult']} ДЕНЬГИ - {left//60}мин")
        if boosters:
            boosters_text = "\n".join(boosters)
    invest_text = "Нет"
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT amount, invest_date, days, interest_rate FROM investments WHERE user_id=? AND guild_id=? AND claimed=0', (target.id, ctx.guild.id))
        invest = await cur.fetchone()
        if invest:
            amount, inv_date, days, rate = invest
            end = datetime.fromisoformat(inv_date) + timedelta(days=days)
            left = (end - datetime.now()).days
            if left > 0:
                invest_text = f"{amount} 💎 | доход: {int(amount * (1 + rate))} 💎 | через {left} дн"
            else:
                invest_text = f"{amount} 💎 | ГОТОВО К ЗАБОРУ!"
    embed = discord.Embed(title=f"📊 ПРОФИЛЬ | {target.display_name}", color=profile_color)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━\n🎚️ УРОВЕНЬ", value=f"**{level}** уровень\n`{bar}` {percent}%\n✨ {xp} XP", inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━\n💰 ЭКОНОМИКА", value=f"💎 {bal} 💎\n🏦 {bank} 💎\n⭐ {rep}\n📈 Инвестиции: {invest_text}", inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━\n📊 СТАТИСТИКА", value=f"💬 Сообщений: {total_msgs}\n🎤 Голосовой онлайн: {voice_hours}ч {voice_minutes}мин\n🌱 Посажено: {total_plants}\n🌾 Собрано: {total_harvests}\n🎣 Рыбы: {total_fish} (легенд: {total_legendary_fish}, миф: {total_mythic_fish})\n🎰 Побед в казино: {total_casino_wins}\n🃏 Побед в блэкджек: {total_blackjack_wins}\n💼 Работ: {total_work}\n🔫 Ограблений: {total_rob}\n📅 Сегодня: {today_msgs} | Неделя: {week_msgs} | Месяц: {month_msgs}", inline=False)
    
    # Получаем количество достижений
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT COUNT(*) FROM achievements WHERE user_id=? AND guild_id=?', (target.id, ctx.guild.id))
        ach_count = (await cur.fetchone())[0]
    
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━\n🏆 ДОСТИЖЕНИЯ", value=f"{ach_count}/{len(ACHIEVEMENTS)} получено", inline=True)
    embed.add_field(name="⚡ БУСТЕРЫ", value=boosters_text, inline=True)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━\n⚧ ПОЛ", value=gender_text, inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━\n📝 БИОГРАФИЯ", value=bio[:500], inline=False)
    embed.set_footer(text=f"🎨 Цвет профиля | 🆔 ID: {target.id}")
    await ctx.send(embed=embed)

@bot.command()
async def bio(ctx, *, text: str = None):
    if not text: return await ctx.send("❌ j.bio <текст>")
    if len(text) > 500: return await ctx.send("❌ Максимум 500 символов")
    await update_user(ctx.author.id, ctx.guild.id, bio=text)
    await ctx.send("✅ Био обновлено")

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    t = member or ctx.author
    embed = discord.Embed(title=f"🖼️ Аватар {t.display_name}", color=discord.Color.blue())
    embed.set_image(url=t.display_avatar.url)
    await ctx.send(embed=embed)

# ========== ТИКЕТЫ (ВЕЧНЫЕ КНОПКИ) ==========
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
        view.add_item(AcceptTicketButton(channel.id, interaction.user.id))
        view.add_item(CloseTicketButton(channel.id, interaction.user.id))
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Тикет создан: {channel.mention}", ephemeral=True)

class AcceptTicketButton(Button):
    def __init__(self, channel_id, creator_id):
        super().__init__(label="✅ Принять тикет", style=discord.ButtonStyle.success, emoji="✅")
        self.channel_id = channel_id
        self.creator_id = creator_id
    async def callback(self, interaction: discord.Interaction):
        is_support = any(interaction.guild.get_role(rid) in interaction.user.roles for rid in SUPPORT_ROLE_IDS if interaction.guild.get_role(rid))
        if not is_support:
            return await interaction.response.send_message("❌ Только поддержка!", ephemeral=True)
        channel = bot.get_channel(self.channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
        await channel.edit(name=f"принят-{channel.name.replace('тикет-', '')}")
        embed = discord.Embed(title="✅ ТИКЕТ ПРИНЯТ", description=f"Принял {interaction.user.mention}", color=discord.Color.green())
        await channel.send(embed=embed)
        async for msg in channel.history(limit=10):
            if msg.author == bot.user and msg.components:
                new_view = View()
                new_view.add_item(CloseTicketButton(self.channel_id, self.creator_id))
                await msg.edit(view=new_view)
                break
        await interaction.response.send_message("✅ Тикет принят!", ephemeral=True)

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
        messages = []
        async for m in channel.history(limit=200, oldest_first=True):
            messages.append(f"[{m.created_at.strftime('%d.%m.%Y %H:%M:%S')}] {m.author.name}: {m.content[:100] if m.content else ''}")
        os.makedirs("ticket_logs", exist_ok=True)
        filename = f"ticket_logs/ticket_{channel.name}_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"=== ТИКЕТ {channel.name} ===\nСоздатель: {self.creator_id}\nЗакрыл: {interaction.user.name}\nСообщений: {len(messages)}\n\n" + "\n".join(messages))
        log_ch = interaction.guild.get_channel(LOGS_CHANNEL_ID)
        if log_ch:
            await log_ch.send(file=discord.File(filename))
        await channel.delete()
        os.remove(filename)

@bot.command()
async def ticket(ctx):
    category = ctx.guild.get_channel(TICKET_CATEGORY_ID)
    if not category:
        return await ctx.send("❌ Категория не настроена!")
    for ch in category.channels:
        if ch.topic and str(ctx.author.id) in ch.topic:
            return await ctx.send("❌ У вас уже есть тикет!")
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
    }
    for rid in SUPPORT_ROLE_IDS:
        role = ctx.guild.get_role(rid)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
    num = len([c for c in category.channels if c.name.startswith("тикет-")]) + 1
    channel = await category.create_text_channel(name=f"тикет-{num}", overwrites=overwrites, topic=f"Создатель: {ctx.author.id}")
    active_tickets[channel.id] = {"creator": ctx.author.id}
    embed = discord.Embed(title="🎫 ТИКЕТ СОЗДАН", description=f"{ctx.author.mention}, опишите проблему", color=discord.Color.green())
    view = View()
    view.add_item(AcceptTicketButton(channel.id, ctx.author.id))
    view.add_item(CloseTicketButton(channel.id, ctx.author.id))
    await channel.send(embed=embed, view=view)
    await ctx.send(f"✅ Тикет создан: {channel.mention}")

@bot.command()
async def close_ticket(ctx):
    if not ctx.channel.category or ctx.channel.category.id != TICKET_CATEGORY_ID:
        return await ctx.send("❌ Только в каналах тикетов!")
    creator_id = None
    if ctx.channel.id in active_tickets:
        creator_id = active_tickets[ctx.channel.id]["creator"]
    elif ctx.channel.topic and "Создатель:" in ctx.channel.topic:
        try:
            creator_id = int(ctx.channel.topic.split("Создатель:")[1].strip().split()[0])
        except:
            pass
    is_support = any(ctx.guild.get_role(rid) in ctx.author.roles for rid in SUPPORT_ROLE_IDS if ctx.guild.get_role(rid))
    if not (is_support or ctx.author.id == creator_id):
        return await ctx.send("❌ Нет прав!")
    embed = discord.Embed(title="⚠️ ПОДТВЕРЖДЕНИЕ", description="Закрыть тикет?", color=discord.Color.orange())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    def check(r, u):
        return u.id == ctx.author.id and str(r.emoji) in ["✅", "❌"] and r.message.id == msg.id
    try:
        r, u = await bot.wait_for('reaction_add', timeout=30, check=check)
        if str(r.emoji) == "❌":
            return await ctx.send("❌ Отменено")
        messages = []
        async for m in ctx.channel.history(limit=200, oldest_first=True):
            messages.append(f"[{m.created_at.strftime('%d.%m.%Y %H:%M:%S')}] {m.author.name}: {m.content[:100] if m.content else ''}")
        os.makedirs("ticket_logs", exist_ok=True)
        filename = f"ticket_logs/ticket_{ctx.channel.name}_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"=== ТИКЕТ {ctx.channel.name} ===\nСоздатель: {creator_id}\nЗакрыл: {ctx.author.name}\nСообщений: {len(messages)}\n\n" + "\n".join(messages))
        log_ch = ctx.guild.get_channel(LOGS_CHANNEL_ID)
        if log_ch:
            await log_ch.send(file=discord.File(filename))
        await ctx.channel.delete()
        os.remove(filename)
    except asyncio.TimeoutError:
        await ctx.send("⏰ Время вышло")

@bot.command()
async def tickets_list(ctx):
    if not any(ctx.guild.get_role(rid) in ctx.author.roles for rid in SUPPORT_ROLE_IDS):
        return await ctx.send("❌ Только поддержка!")
    if not active_tickets:
        return await ctx.send("📭 Нет активных тикетов")
    embed = discord.Embed(title="📋 Активные тикеты", color=discord.Color.blue())
    for cid, data in active_tickets.items():
        ch = ctx.guild.get_channel(cid)
        if ch:
            creator = await bot.fetch_user(data["creator"])
            embed.add_field(name=f"#{ch.name}", value=f"Создатель: {creator.mention}\n{ch.mention}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    view = PersistentTicketButton()
    embed = discord.Embed(title="🎫 ТИКЕТЫ", description="Нажми на кнопку для создания тикета\n⚠️ Кнопка работает постоянно!", color=discord.Color.blue())
    await ctx.send(embed=embed, view=view)
    await ctx.send("✅ Готово!")

# ========== КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦА ==========
def is_owner(ctx):
    return ctx.author.id == ctx.guild.owner_id

@bot.command()
@commands.check(is_owner)
async def admin_help(ctx):
    embed = discord.Embed(title="👑 КОМАНДЫ ВЛАДЕЛЬЦА", color=discord.Color.gold())
    embed.add_field(name="💰 Экономика", value="`j.owner_give @user <сумма>`\n`j.owner_take @user <сумма>`\n`j.owner_set_balance @user <сумма>`\n`j.owner_reset_user @user`", inline=False)
    embed.add_field(name="💾 Бэкапы", value="`j.backup_db`\n`j.download_backup`\n`j.upload_backup`\n`j.backup_info`", inline=False)
    embed.add_field(name="🛍️ Магазин", value="`j.add_shop_item <название> <цена> <роль_id> [описание]`\n`j.remove_shop_item <название>`", inline=False)
    embed.add_field(name="⚙️ Настройки", value="`j.settings welcome/logs/levels #канал`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.check(is_owner)
async def owner_give(ctx, member: discord.Member, amount: int):
    if amount <= 0: return await ctx.send("❌ Сумма > 0")
    await add_balance(member.id, ctx.guild.id, amount)
    await ctx.send(f"✅ Выдано {amount} 💎 {member.mention}")

@bot.command()
@commands.check(is_owner)
async def owner_take(ctx, member: discord.Member, amount: int):
    if amount <= 0: return await ctx.send("❌ Сумма > 0")
    user = await get_user(member.id, ctx.guild.id)
    if user[4] < amount: return await ctx.send(f"❌ У {member.mention} только {user[4]} 💎")
    await add_balance(member.id, ctx.guild.id, -amount)
    await ctx.send(f"✅ Забрано {amount} 💎 у {member.mention}")

@bot.command()
@commands.check(is_owner)
async def owner_set_balance(ctx, member: discord.Member, amount: int):
    if amount < 0: return await ctx.send("❌ Баланс не может быть отрицательным")
    await update_user(member.id, ctx.guild.id, balance=amount)
    await ctx.send(f"✅ Баланс {member.mention} = {amount} 💎")

@bot.command()
@commands.check(is_owner)
async def owner_reset_user(ctx, member: discord.Member):
    await update_user(member.id, ctx.guild.id, xp=0, level=0, balance=START_BALANCE, bank=0, reputation=0, total_messages=0, today_messages=0, week_messages=0, month_messages=0, voice_streak=0, pots=0, crops="[]", inventory="[]", awards="[]")
    await ctx.send(f"✅ {member.mention} полностью сброшен")

@bot.command()
@commands.check(is_owner)
async def backup_db(ctx):
    if not os.path.exists("justice.db"): return await ctx.send("❌ БД не найдена")
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup = f"justice_db_backup_{now}.db"
    shutil.copy2("justice.db", backup)
    await ctx.send(f"💾 Резервная копия: {backup}")
    os.remove(backup)

@bot.command()
@commands.check(is_owner)
async def download_backup(ctx):
    if not os.path.exists("justice.db"): return await ctx.send("❌ БД не найдена")
    await ctx.send(file=discord.File("justice.db"))

@bot.command()
@commands.check(is_owner)
async def upload_backup(ctx):
    if not ctx.message.attachments: return await ctx.send("❌ Прикрепите файл .db")
    att = ctx.message.attachments[0]
    if not att.filename.endswith('.db'): return await ctx.send("❌ Нужен .db файл")
    await att.save("justice.db")
    await ctx.send("✅ База данных восстановлена! Перезапустите бота")

@bot.command()
@commands.check(is_owner)
async def backup_info(ctx):
    if not os.path.exists("justice.db"): return await ctx.send("❌ БД не найдена")
    size = os.path.getsize("justice.db") / (1024 * 1024)
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT COUNT(*) FROM users')
        users = (await cur.fetchone())[0]
    embed = discord.Embed(title="📊 ИНФО БД", color=discord.Color.blue())
    embed.add_field(name="📁 Файл", value="justice.db", inline=True)
    embed.add_field(name="📦 Размер", value=f"{size:.2f} MB", inline=True)
    embed.add_field(name="👥 Пользователей", value=users, inline=True)
    await ctx.send(embed=embed)

# ========== ПРИВАТНЫЕ ГОЛОСОВЫЕ ==========
class VCControlPanel(View):
    def __init__(self, cid, oid):
        super().__init__(timeout=None)
        self.cid, self.oid = cid, oid
    @discord.ui.button(label="🔒 Закрыть", style=discord.ButtonStyle.danger)
    async def lock(self, i, b):
        if i.user.id != self.oid: return await i.response.send_message("❌ Не владелец!", ephemeral=True)
        ch = bot.get_channel(self.cid)
        if ch: await ch.set_permissions(i.guild.default_role, connect=False)
        await i.response.send_message("🔒 Канал закрыт", ephemeral=True)
    @discord.ui.button(label="🔓 Открыть", style=discord.ButtonStyle.success)
    async def unlock(self, i, b):
        if i.user.id != self.oid: return await i.response.send_message("❌ Не владелец!", ephemeral=True)
        ch = bot.get_channel(self.cid)
        if ch: await ch.set_permissions(i.guild.default_role, connect=True)
        await i.response.send_message("🔓 Канал открыт", ephemeral=True)
    @discord.ui.button(label="👥 Лимит", style=discord.ButtonStyle.primary)
    async def limit(self, i, b):
        if i.user.id != self.oid: return await i.response.send_message("❌ Не владелец!", ephemeral=True)
        modal = LimitModal(self.cid)
        await i.response.send_modal(modal)
    @discord.ui.button(label="📝 Название", style=discord.ButtonStyle.primary)
    async def rename(self, i, b):
        if i.user.id != self.oid: return await i.response.send_message("❌ Не владелец!", ephemeral=True)
        modal = RenameModal(self.cid)
        await i.response.send_modal(modal)
    @discord.ui.button(label="🗑 Удалить", style=discord.ButtonStyle.danger)
    async def delete(self, i, b):
        if i.user.id != self.oid: return await i.response.send_message("❌ Не владелец!", ephemeral=True)
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
            if lim < 1 or lim > 99: return await i.response.send_message("❌ 1-99", ephemeral=True)
            ch = bot.get_channel(self.cid)
            if ch: await ch.edit(user_limit=lim)
            await i.response.send_message(f"✅ Лимит: {lim}", ephemeral=True)
        except: await i.response.send_message("❌ Введите число", ephemeral=True)

class RenameModal(Modal):
    def __init__(self, cid):
        super().__init__(title="Переименовать")
        self.cid = cid
        self.n = TextInput(label="Новое название", required=True)
        self.add_item(self.n)
    async def on_submit(self, i):
        ch = bot.get_channel(self.cid)
        if ch: await ch.edit(name=self.n.value)
        await i.response.send_message(f"✅ Переименован в {self.n.value}", ephemeral=True)

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
            for rid in SUPPORT_ROLE_IDS:
                role = member.guild.get_role(rid)
                if role: overwrites[role] = discord.PermissionOverwrite(connect=True)
            channel = await cat.create_voice_channel(name=f"Приватный #{num}", overwrites=overwrites)
            await member.move_to(channel)
            panel = VCControlPanel(channel.id, member.id)
            await channel.send(f"{member.mention}, панель управления:", view=panel)
            vc_sessions[channel.id] = {"owner": member.id}
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('INSERT OR REPLACE INTO private_vc (channel_id, owner_id, guild_id, channel_name, created_at) VALUES (?,?,?,?,?)', (channel.id, member.id, member.guild.id, channel.name, datetime.now().isoformat()))
                await db.commit()
    if before.channel and before.channel.id in vc_sessions and len(before.channel.members) == 0:
        await asyncio.sleep(10)
        if len(before.channel.members) == 0:
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('DELETE FROM private_vc WHERE channel_id=?', (before.channel.id,))
                await db.commit()
            await before.channel.delete()
            del vc_sessions[before.channel.id]

# ========== ЖИВОТНЫЕ ==========
@bot.command()
async def buy_animal(ctx, animal_type: str = None):
    if not animal_type or animal_type.lower() not in FARM_ANIMALS:
        animals = "\n".join([f"• {a} - {data['price']} 💎 | Даёт: {data['produce']} ({data['produce_price']} 💎)" for a, data in FARM_ANIMALS.items()])
        return await ctx.send(f"🐔 **Животные**\n{animals}\nПример: `j.buy_animal курица`")
    animal = animal_type.lower()
    animal_data = FARM_ANIMALS[animal]
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT level FROM farm_upgrades WHERE user_id=? AND guild_id=? AND upgrade_type="max_animals"', (ctx.author.id, ctx.guild.id))
        upgrade = await cur.fetchone()
        max_animals = 5 + (upgrade[0] * 2 if upgrade else 0)
        cur = await db.execute('SELECT count FROM farm_animals WHERE user_id=? AND guild_id=? AND animal_type=?', (ctx.author.id, ctx.guild.id, animal))
        current = await cur.fetchone()
        current_count = current[0] if current else 0
        if current_count >= max_animals: return await ctx.send(f"❌ Максимум {max_animals} {animal}")
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < animal_data["price"]: return await ctx.send(f"❌ Нужно {animal_data['price']} 💎")
    await add_balance(ctx.author.id, ctx.guild.id, -animal_data["price"])
    async with aiosqlite.connect("justice.db") as db:
        if current:
            await db.execute('UPDATE farm_animals SET count=? WHERE user_id=? AND guild_id=? AND animal_type=?', (current_count+1, ctx.author.id, ctx.guild.id, animal))
        else:
            await db.execute('INSERT INTO farm_animals (user_id, guild_id, animal_type, count, last_produce, last_fed) VALUES (?,?,?,1,?,?)', (ctx.author.id, ctx.guild.id, animal, datetime.now().isoformat(), datetime.now().isoformat()))
        await db.commit()
    await ctx.send(f"✅ Куплен {animal_data['name']} за {animal_data['price']} 💎!")

@bot.command()
async def feed_animals(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT animal_type, count FROM farm_animals WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        animals = await cur.fetchall()
        if not animals: return await ctx.send("❌ Нет животных")
        total_feed = 0
        for animal, count in animals:
            animal_data = FARM_ANIMALS[animal]
            feed_needed = animal_data["feed_amount"] * count
            cur3 = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
            inv = json.loads((await cur3.fetchone())[0] or "[]")
            feed_count = inv.count(f"crop_{animal_data['feed']}")
            if feed_count >= feed_needed:
                for _ in range(feed_needed): inv.remove(f"crop_{animal_data['feed']}")
                total_feed += feed_needed
                await db.execute('UPDATE farm_animals SET last_fed=? WHERE user_id=? AND guild_id=? AND animal_type=?', (datetime.now().isoformat(), ctx.author.id, ctx.guild.id, animal))
            else:
                await ctx.send(f"⚠️ Не хватает {animal_data['feed']} для {animal} (нужно {feed_needed}, есть {feed_count})")
        if total_feed > 0:
            await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
            await db.commit()
            await ctx.send(f"✅ Потрачено {total_feed} еды")
        else:
            await ctx.send("❌ Нет еды")

@bot.command()
async def collect_products(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT animal_type, count, last_produce FROM farm_animals WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        animals = await cur.fetchall()
        if not animals: return await ctx.send("❌ Нет животных")
        total_earn = 0
        collected = []
        for animal, count, last_produce in animals:
            animal_data = FARM_ANIMALS[animal]
            last_time = datetime.fromisoformat(last_produce)
            time_passed = (datetime.now() - last_time).total_seconds()
            produce_time = animal_data["produce_time"]
            if time_passed >= produce_time:
                cycles = int(time_passed // produce_time)
                if cycles > 0:
                    produced = count * cycles
                    earn = produced * animal_data["produce_price"]
                    total_earn += earn
                    collected.append(f"{animal_data['name']} x{produced} (+{earn} 💎)")
                    new_time = last_time + timedelta(seconds=produce_time * cycles)
                    await db.execute('UPDATE farm_animals SET last_produce=? WHERE user_id=? AND guild_id=? AND animal_type=?', (new_time.isoformat(), ctx.author.id, ctx.guild.id, animal))
        if total_earn > 0:
            cur4 = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
            inv = json.loads((await cur4.fetchone())[0] or "[]")
            for item in collected: inv.append(f"product_{item.split(' x')[0]}")
            await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
            await add_balance(ctx.author.id, ctx.guild.id, total_earn)
            await db.commit()
            await ctx.send(f"✅ Собрано:\n" + "\n".join(collected[:10]) + f"\n💰 Всего: {total_earn} 💎")
        else:
            await ctx.send("❌ Продукция не готова")

@bot.command()
async def my_animals(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT animal_type, count, last_fed FROM farm_animals WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        animals = await cur.fetchall()
        if not animals: return await ctx.send("🐔 Нет животных. `j.buy_animal курица`")
        embed = discord.Embed(title=f"🐔 ЖИВОТНЫЕ | {ctx.author.display_name}", color=discord.Color.green())
        for animal, count, last_fed in animals:
            animal_data = FARM_ANIMALS[animal]
            last_fed_time = datetime.fromisoformat(last_fed)
            hungry = (datetime.now() - last_fed_time).total_seconds() > 43200
            status = "😋 Сытые" if not hungry else "🍽️ Голодные!"
            embed.add_field(name=f"{animal_data['name']} x{count}", value=f"📦 Даёт: {animal_data['produce']}\n💎 Цена: {animal_data['produce_price']}\n{status}", inline=True)
        await ctx.send(embed=embed)

# ========== КРАФТ ==========
@bot.command()
async def craft(ctx, recipe_id: str = None):
    if not recipe_id or recipe_id.lower() not in RECIPES:
        recipes = "\n".join([f"• {rid} - {data['name']} | {data['desc']}" for rid, data in RECIPES.items()])
        return await ctx.send(f"🔨 **Рецепты**\n{recipes}\nПример: `j.craft золотой слиток`")
    recipe = RECIPES[recipe_id.lower()]
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        missing = []
        for ing, amount in recipe["ingredients"].items():
            count = inv.count(f"crop_{ing}") + inv.count(f"product_{ing}") + inv.count(ing)
            if count < amount: missing.append(f"{ing} ({count}/{amount})")
        if missing: return await ctx.send("❌ Не хватает:\n" + "\n".join(missing))
        for ing, amount in recipe["ingredients"].items():
            for _ in range(amount):
                if f"crop_{ing}" in inv: inv.remove(f"crop_{ing}")
                elif f"product_{ing}" in inv: inv.remove(f"product_{ing}")
                else: inv.remove(ing)
        for _ in range(recipe["count"]): inv.append(recipe["result"])
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await add_xp(ctx.author.id, ctx.guild.id, recipe["xp"])
        await db.commit()
    await ctx.send(f"✅ Скрафтил {recipe['name']} x{recipe['count']}!\n✨ +{recipe['xp']} XP")

@bot.command()
async def recipes(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT recipe_id FROM recipes WHERE user_id=? AND guild_id=? AND learned=1', (ctx.author.id, ctx.guild.id))
        learned = [row[0] for row in await cur.fetchall()]
    embed = discord.Embed(title=f"🔨 РЕЦЕПТЫ | {ctx.author.display_name}", color=discord.Color.blue())
    learned_text = "\n".join([f"• {rid} - {RECIPES[rid]['name']}" for rid in learned if rid in RECIPES]) or "Нет"
    all_text = "\n".join([f"• {rid} - {data['name']} | Нужно: {', '.join([f'{k} x{v}' for k,v in data['ingredients'].items()])}" for rid, data in RECIPES.items()])
    embed.add_field(name="📚 Выученные", value=learned_text[:1024], inline=False)
    embed.add_field(name="🔓 Все рецепты", value=all_text[:1024], inline=False)
    await ctx.send(embed=embed)

# ========== ИНВЕСТИЦИИ ==========
@bot.command()
async def invest(ctx, invest_type: str = None, amount: int = None):
    if not invest_type or not amount:
        types = "\n".join([f"• {k} - {v['name']}: {v['min']}-{v['max']} 💎, {v['days']} дн, +{v['rate']*100}%" for k, v in INVESTMENTS.items()])
        return await ctx.send(f"📊 **Инвестиции**\n{types}\nПример: `j.invest надёжный 50000`")
    invest_type = invest_type.lower()
    if invest_type not in INVESTMENTS: return await ctx.send("❌ Типы: надёжный, средний, рисковый, премиум")
    inv_data = INVESTMENTS[invest_type]
    if amount < inv_data["min"] or amount > inv_data["max"]: return await ctx.send(f"❌ Сумма от {inv_data['min']} до {inv_data['max']}")
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < amount: return await ctx.send(f"❌ Не хватает {amount} 💎")
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM investments WHERE user_id=? AND guild_id=? AND claimed=0', (ctx.author.id, ctx.guild.id))
        if await cur.fetchone(): return await ctx.send("❌ У вас уже есть активная инвестиция!")
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await db.execute('INSERT INTO investments (user_id, guild_id, invest_type, amount, invest_date, days, interest_rate, claimed) VALUES (?,?,?,?,?,?,?,0)', (ctx.author.id, ctx.guild.id, invest_type, amount, datetime.now().isoformat(), inv_data["days"], inv_data["rate"]))
        await db.commit()
    await ctx.send(f"✅ Инвестировано {amount} 💎 в {inv_data['name']} на {inv_data['days']} дней!\n💰 Получите {int(amount*(1+inv_data['rate']))} 💎")

@bot.command()
async def claim_invest(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM investments WHERE user_id=? AND guild_id=? AND claimed=0', (ctx.author.id, ctx.guild.id))
        inv = await cur.fetchone()
        if not inv: return await ctx.send("❌ Нет активных инвестиций")
        _, _, _, inv_type, amount, inv_date, days, rate, claimed = inv
        end_date = datetime.fromisoformat(inv_date) + timedelta(days=days)
        if datetime.now() < end_date:
            left = (end_date - datetime.now()).days
            return await ctx.send(f"⏰ Осталось {left} дней")
        profit = int(amount * (1 + rate))
        await add_balance(ctx.author.id, ctx.guild.id, profit)
        await db.execute('UPDATE investments SET claimed=1 WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        await db.commit()
    await ctx.send(f"💰 Получено {profit} 💎 (вложено {amount}, прибыль {profit-amount})")

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
                await update_user_stats(game["p1"], i.guild.id, "ttt_win", 1)
            elif winner=="⭕":
                await add_balance(game["p2"], i.guild.id, prize)
                await add_balance(game["p1"], i.guild.id, -game["bet"])
                winner_mention = f"<@{game['p2']}>"
                await update_user_stats(game["p2"], i.guild.id, "ttt_win", 1)
            else:
                winner_mention = "Ничья"
                await add_balance(game["p1"], i.guild.id, game["bet"])
                await add_balance(game["p2"], i.guild.id, game["bet"])
            embed = discord.Embed(title="❌⭕ КРЕСТИКИ-НОЛИКИ", color=discord.Color.gold())
            embed.add_field(name="🏆 РЕЗУЛЬТАТ", value=f"{winner_mention} победил!\n💰 Выигрыш: {prize} 💎" if winner!="Ничья" else "Ничья!", inline=False)
            await i.response.edit_message(embed=embed, view=None)
            del ttt_games[i.channel.id]
            return
        if all(cell!="⬜" for row in game["board"] for cell in row):
            await add_balance(game["p1"], i.guild.id, game["bet"])
            await add_balance(game["p2"], i.guild.id, game["bet"])
            embed = discord.Embed(title="❌⭕ КРЕСТИКИ-НОЛИКИ", color=discord.Color.blue())
            embed.add_field(name="🤝 НИЧЬЯ!", value="Ставки возвращены", inline=False)
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

# ========== ПОКЕР ==========
class PokerGame:
    def __init__(self, players, bets, channel_id):
        self.players = players; self.bets = bets; self.hands = {}; self.community = []
        self.current_bet = 0; self.pot = sum(bets.values()); self.folded = []
        self.current_player_index = 0; self.channel_id = channel_id; self.stage = "preflop"
    def deal(self, deck):
        for uid in self.players: self.hands[uid] = [deck.pop(), deck.pop()]
    def get_card_value(self, card):
        rank = card[:-1]; values = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14}
        return values.get(rank,0)
    def get_hand_rank(self, cards):
        ranks = sorted([self.get_card_value(c) for c in cards], reverse=True)
        suits = [c[-1] for c in cards]
        flush_suit = None
        for suit in ['♠️','♥️','♣️','♦️']:
            if suits.count(suit)>=5: flush_suit = suit; break
        unique_ranks = sorted(set(ranks), reverse=True)
        straight_high = None
        for i in range(len(unique_ranks)-4):
            if unique_ranks[i]-unique_ranks[i+4]==4: straight_high = unique_ranks[i]; break
        if straight_high is None and set([14,2,3,4,5]).issubset(set(ranks)): straight_high = 5
        if flush_suit and straight_high:
            flush_cards = [c for c in cards if c.endswith(flush_suit)]
            flush_ranks = sorted([self.get_card_value(c) for c in flush_cards], reverse=True)
            for i in range(len(flush_ranks)-4):
                if flush_ranks[i]-flush_ranks[i+4]==4:
                    return (9, flush_ranks[i]) if flush_ranks[i]==14 else (8, flush_ranks[i])
        rank_counts = {}
        for r in ranks: rank_counts[r] = rank_counts.get(r,0)+1
        counts = sorted(rank_counts.values(), reverse=True)
        if counts[0]==4: return (7, max([r for r,c in rank_counts.items() if c==4]))
        if counts[0]==3 and counts[1]>=2: return (6, max([r for r,c in rank_counts.items() if c==3]))
        if flush_suit:
            flush_ranks = sorted([self.get_card_value(c) for c in cards if c.endswith(flush_suit)], reverse=True)[:5]
            return (5, flush_ranks[0])
        if straight_high: return (4, straight_high)
        if counts[0]==3: return (3, max([r for r,c in rank_counts.items() if c==3]))
        if counts[0]==2 and counts[1]==2:
            pairs = sorted([r for r,c in rank_counts.items() if c==2], reverse=True)
            return (2, pairs[0], pairs[1])
        if counts[0]==2: return (1, max([r for r,c in rank_counts.items() if c==2]))
        return (0, max(ranks))

poker_games = {}

class PokerButton(Button):
    def __init__(self, label, style, action, amount=None):
        super().__init__(label=label, style=style); self.action = action; self.amount = amount
    async def callback(self, i):
        game = poker_games.get(i.channel.id)
        if not game: return await i.response.send_message("❌ Игра не найдена", ephemeral=True)
        if i.user.id not in game.players: return await i.response.send_message("❌ Вы не в игре", ephemeral=True)
        if i.user.id in game.folded: return await i.response.send_message("❌ Вы сбросили", ephemeral=True)
        if game.players[game.current_player_index]!=i.user.id: return await i.response.send_message("❌ Не ваш ход", ephemeral=True)
        user = await get_user(i.user.id, i.guild.id)
        if self.action=="check":
            if game.current_bet>game.bets.get(i.user.id,0): return await i.response.send_message("❌ Нужно уравнять", ephemeral=True)
            await i.response.send_message(f"✅ {i.user.mention} чекает", ephemeral=False)
        elif self.action=="call":
            need = game.current_bet - game.bets.get(i.user.id,0)
            if need>user[4]: return await i.response.send_message(f"❌ Не хватает {need} 💎", ephemeral=True)
            await add_balance(i.user.id, i.guild.id, -need)
            game.bets[i.user.id] = game.bets.get(i.user.id,0)+need
            game.pot += need
            await i.response.send_message(f"✅ {i.user.mention} уравнял (+{need} 💎)", ephemeral=False)
        elif self.action=="raise":
            if not self.amount:
                modal = RaiseModal(game, i.user.id)
                await i.response.send_modal(modal); return
            amount = self.amount
            need = game.current_bet - game.bets.get(i.user.id,0) + amount
            if need>user[4]: return await i.response.send_message(f"❌ Не хватает {need} 💎", ephemeral=True)
            await add_balance(i.user.id, i.guild.id, -need)
            game.bets[i.user.id] = game.bets.get(i.user.id,0)+need
            game.pot += need; game.current_bet = game.bets[i.user.id]; game.last_raiser = i.user.id
            await i.response.send_message(f"✅ {i.user.mention} поднял до {game.current_bet} 💎", ephemeral=False)
        elif self.action=="fold":
            game.folded.append(i.user.id)
            await i.response.send_message(f"❌ {i.user.mention} сбросил", ephemeral=False)
        next_player = None
        for idx in range(len(game.players)):
            idx2 = (game.current_player_index+1+idx)%len(game.players)
            if game.players[idx2] not in game.folded: next_player = idx2; break
        if next_player is None:
            await finish_poker_game(i.channel, game); return
        game.current_player_index = next_player
        all_in = all(game.bets.get(p,0)==game.current_bet or p in game.folded for p in game.players)
        if all_in: await next_poker_stage(i.channel, game)
        else: await update_poker_display(i.channel, game)

class RaiseModal(Modal):
    def __init__(self, game, user_id):
        super().__init__(title="Повысить ставку")
        self.game = game; self.user_id = user_id
        self.amount_input = TextInput(label="Сумма повышения", placeholder="Минимум 50", required=True)
        self.add_item(self.amount_input)
    async def on_submit(self, i):
        try: amount = int(self.amount_input.value)
        except: return await i.response.send_message("❌ Введите число", ephemeral=True)
        if amount<50: return await i.response.send_message("❌ Мин. 50 💎", ephemeral=True)
        user = await get_user(self.user_id, i.guild.id)
        need = self.game.current_bet - self.game.bets.get(self.user_id,0) + amount
        if need>user[4]: return await i.response.send_message(f"❌ Не хватает {need} 💎", ephemeral=True)
        await add_balance(self.user_id, i.guild.id, -need)
        self.game.bets[self.user_id] = self.game.bets.get(self.user_id,0)+need
        self.game.pot += need; self.game.current_bet = self.game.bets[self.user_id]; self.game.last_raiser = self.user_id
        await i.response.send_message(f"✅ {i.user.mention} поднял до {self.game.current_bet} 💎", ephemeral=False)
        self.game.current_player_index = 0
        await update_poker_display(i.channel, self.game)

async def next_poker_stage(channel, game):
    deck = FULL_DECK.copy(); random.shuffle(deck)
    if game.stage=="preflop":
        game.community = [deck.pop(), deck.pop(), deck.pop()]; game.stage="flop"
        game.current_bet = 0; game.bets = {p:0 for p in game.players}; game.last_raiser = None
    elif game.stage=="flop":
        game.community.append(deck.pop()); game.stage="turn"
        game.current_bet = 0; game.bets = {p:0 for p in game.players}; game.last_raiser = None
    elif game.stage=="turn":
        game.community.append(deck.pop()); game.stage="river"
        game.current_bet = 0; game.bets = {p:0 for p in game.players}; game.last_raiser = None
    elif game.stage=="river":
        await finish_poker_game(channel, game); return
    game.current_player_index = 0
    while game.current_player_index < len(game.players) and game.players[game.current_player_index] in game.folded:
        game.current_player_index += 1
    await update_poker_display(channel, game)

async def finish_poker_game(channel, game):
    best_rank = (-1,); winner = None
    for uid in game.players:
        if uid in game.folded: continue
        all_cards = game.hands[uid] + game.community
        rank = game.get_hand_rank(all_cards)
        if rank > best_rank: best_rank = rank; winner = uid
    if winner:
        await add_balance(winner, channel.guild.id, game.pot)
        embed = discord.Embed(title="🃏 ПОКЕР", color=discord.Color.gold())
        embed.add_field(name="🏆 ПОБЕДИТЕЛЬ", value=f"<@{winner}>", inline=True)
        embed.add_field(name="💰 ВЫИГРЫШ", value=f"{game.pot} 💎", inline=True)
        embed.add_field(name="🎴 КАРТЫ", value=f"Ваши: {' '.join(game.hands[winner])}\nОбщие: {' '.join(game.community)}", inline=False)
        await channel.send(embed=embed)
    del poker_games[channel.id]

async def update_poker_display(channel, game):
    community_str = ' '.join(game.community) if game.community else "❌"
    embed = discord.Embed(title="🃏 ПОКЕР", color=discord.Color.blue())
    embed.add_field(name="🎴 ОБЩИЕ КАРТЫ", value=community_str, inline=False)
    embed.add_field(name="💰 БАНК", value=f"{game.pot} 💎", inline=True)
    embed.add_field(name="📊 СТАВКА", value=f"{game.current_bet} 💎", inline=True)
    embed.add_field(name="🎲 ЭТАП", value=game.stage.upper(), inline=True)
    embed.add_field(name="🎯 ХОД", value=f"<@{game.players[game.current_player_index]}>", inline=False)
    view = View()
    view.add_item(PokerButton("✅ Чек", discord.ButtonStyle.secondary, "check"))
    view.add_item(PokerButton("📞 Уравнять", discord.ButtonStyle.primary, "call"))
    view.add_item(PokerButton("📈 Поднять", discord.ButtonStyle.success, "raise"))
    view.add_item(PokerButton("❌ Сброс", discord.ButtonStyle.danger, "fold"))
    await channel.send(embed=embed, view=view)

@bot.command()
async def poker(ctx, member1: discord.Member = None, member2: discord.Member = None, bet: int = None):
    if not member1 or not member2 or not bet: return await ctx.send("❌ j.poker @игрок1 @игрок2 100")
    players = [ctx.author.id, member1.id, member2.id]
    if len(set(players))!=3: return await ctx.send("❌ Игроки должны быть разными")
    if bet<100: return await ctx.send("❌ Мин. 100 💎")
    for uid in players:
        bal = (await get_user(uid, ctx.guild.id))[4]
        if bal<bet: return await ctx.send(f"❌ У <@{uid}> не хватает {bet} 💎")
    for uid in players: await add_balance(uid, ctx.guild.id, -bet)
    deck = FULL_DECK.copy(); random.shuffle(deck)
    game = PokerGame(players, {uid:bet for uid in players}, ctx.channel.id)
    game.deal(deck)
    poker_games[ctx.channel.id] = game
    for uid in players:
        user = ctx.guild.get_member(uid)
        if user:
            try: await user.send(f"🃏 Ваши карты: {' '.join(game.hands[uid])}\nКанал: {ctx.channel.mention}")
            except: pass
    embed = discord.Embed(title="🃏 ПОКЕР", description=f"Игра началась!\nУчастники: <@{players[0]}>, <@{players[1]}>, <@{players[2]}>\n💰 Ставка: {bet} 💎\n🎲 Первый ход: <@{players[0]}>", color=discord.Color.green())
    await ctx.send(embed=embed)
    game.current_player_index = 0
    await update_poker_display(ctx.channel, game)

# ========== ВИСЕЛИЦА ==========
class HangmanGame:
    def __init__(self, word):
        self.word = word.upper(); self.guessed = set(); self.wrong = []; self.max_wrong = 6
        self.pics = [
            "```\n   +---+\n       |\n       |\n       |\n      ===",
            "```\n   +---+\n   O   |\n       |\n       |\n      ===",
            "```\n   +---+\n   O   |\n   |   |\n       |\n      ===",
            "```\n   +---+\n   O   |\n  /|   |\n       |\n      ===",
            "```\n   +---+\n   O   |\n  /|\\  |\n       |\n      ===",
            "```\n   +---+\n   O   |\n  /|\\  |\n  /    |\n      ===",
            "```\n   +---+\n   O   |\n  /|\\  |\n  / \\  |\n      ==="
        ]
    def get_display(self): return " ".join([c if c in self.guessed else "_" for c in self.word])
    def guess(self, letter):
        letter = letter.upper()
        if letter in self.guessed or letter in self.wrong: return False, "already"
        if letter in self.word: self.guessed.add(letter); return True, "correct"
        else: self.wrong.append(letter); return False, "wrong"
    def is_won(self): return all(c in self.guessed for c in self.word)
    def is_lost(self): return len(self.wrong) >= self.max_wrong

hangman_words = ["ПИТОН", "ДИСКОРД", "БОТ", "СЕРВЕР", "ПРОГРАММИРОВАНИЕ", "РАЗРАБОТЧИК", "КОМАНДА", "ИГРА", "ПОБЕДА", "УДАЧА"]
hangman_games = {}

@bot.command()
async def hangman(ctx):
    if ctx.channel.id in hangman_games: return await ctx.send("❌ Игра уже идёт!")
    word = random.choice(hangman_words)
    game = HangmanGame(word)
    hangman_games[ctx.channel.id] = game
    embed = discord.Embed(title="🔤 ВИСЕЛИЦА", description=f"{game.pics[0]}\n\nСлово: {game.get_display()}\nОшибок: 0/{game.max_wrong}", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
async def guess(ctx, letter: str = None):
    if ctx.channel.id not in hangman_games: return await ctx.send("❌ Нет игры! `j.hangman`")
    if not letter or len(letter)!=1: return await ctx.send("❌ Введите одну букву!")
    game = hangman_games[ctx.channel.id]
    result, status = game.guess(letter)
    if status=="already": return await ctx.send(f"❌ Буква '{letter.upper()}' уже была!")
    embed = discord.Embed(title="🔤 ВИСЕЛИЦА", color=discord.Color.blue())
    if game.is_won():
        embed.description = f"{game.pics[len(game.wrong)]}\n\nСлово: {game.get_display()}\n\n🎉 ПОБЕДА!"
        embed.color = discord.Color.green()
        await ctx.send(embed=embed)
        del hangman_games[ctx.channel.id]; return
    if game.is_lost():
        embed.description = f"{game.pics[game.max_wrong]}\n\n💀 ПОРАЖЕНИЕ! Слово: {game.word}"
        embed.color = discord.Color.red()
        await ctx.send(embed=embed)
        del hangman_games[ctx.channel.id]; return
    embed.description = f"{game.pics[len(game.wrong)]}\n\nСлово: {game.get_display()}\nОшибок: {len(game.wrong)}/{game.max_wrong}\nНеправильные: {', '.join(game.wrong) if game.wrong else 'нет'}"
    await ctx.send(embed=embed)

# ========== КОРОТКИЕ ССЫЛКИ ==========
short_urls = {}
@bot.command()
async def short(ctx, *, url: str = None):
    if not url: return await ctx.send("❌ j.short https://example.com")
    if not url.startswith("http"): url = "https://"+url
    code = str(hash(url))[:6]
    short_urls[code] = url
    await ctx.send(f"🔗 Короткая ссылка: `j.get {code}`")
@bot.command()
async def get(ctx, code: str = None):
    if not code or code not in short_urls: return await ctx.send("❌ Ссылка не найдена!")
    await ctx.send(f"🔗 {short_urls[code]}")

# ========== КУРСЫ ВАЛЮТ ==========
@bot.command()
async def currency(ctx):
    async with aiohttp.ClientSession() as session:
        try:
            url = "https://www.cbr-xml-daily.ru/daily_json.js"
            async with session.get(url) as resp:
                data = await resp.json()
                usd = data["Valute"]["USD"]["Value"]
                eur = data["Valute"]["EUR"]["Value"]
                cny = data["Valute"]["CNY"]["Value"]
                embed = discord.Embed(title="💱 КУРСЫ ВАЛЮТ", color=discord.Color.gold())
                embed.add_field(name="🇺🇸 Доллар", value=f"{usd:.2f} ₽", inline=True)
                embed.add_field(name="🇪🇺 Евро", value=f"{eur:.2f} ₽", inline=True)
                embed.add_field(name="🇨🇳 Юань", value=f"{cny:.2f} ₽", inline=True)
                await ctx.send(embed=embed)
        except: await ctx.send("❌ Ошибка получения курсов")

# ========== ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ ==========
@tasks.loop(hours=168)
async def weekly_report():
    for guild in bot.guilds:
        channel = guild.get_channel(LOGS_CHANNEL_ID)
        if not channel: continue
        week_start = (datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d")
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT user_id, messages, voice_minutes, casino_wins, work_count, fish_caught, crops_harvested FROM weekly_stats WHERE guild_id=? AND week_start=? ORDER BY messages DESC LIMIT 10', (guild.id, week_start))
            stats = await cur.fetchall()
        if not stats: continue
        embed = discord.Embed(title="📊 ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ", description=f"Статистика за неделю (с {week_start})", color=discord.Color.blue())
        text = ""
        for i, (uid, msgs, voice, casino, work, fish, crops) in enumerate(stats[:5],1):
            user = guild.get_member(uid)
            name = user.display_name if user else f"ID:{uid}"
            text += f"{i}. {name} – {msgs} сообщ., {voice} мин в войсе, {casino} побед в казино\n"
        embed.add_field(name="🏆 ТОП АКТИВНОСТИ", value=text or "Нет данных", inline=False)
        await channel.send(embed=embed)

# ========== STEAM ==========
class SteamProfileView(discord.ui.View):
    def __init__(self, target_user, steam_id):
        super().__init__(timeout=120)
        self.target_user = target_user
        self.steam_id = steam_id
        self.add_item(discord.ui.Button(label="Открыть в Steam", style=discord.ButtonStyle.link, url=f"https://steamcommunity.com/profiles/{steam_id}"))
    async def fetch_steam_data(self, action):
        if not STEAM_API_KEY: return None, "❌ Steam API не настроен"
        async with aiohttp.ClientSession() as session:
            if action == "profile":
                url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={self.steam_id}"
                async with session.get(url) as resp:
                    data = await resp.json()
                    players = data.get('response',{}).get('players',[])
                    if not players: return None, "❌ Профиль не найден"
                    p = players[0]
                    status_map = {0:"Офлайн",1:"В сети",2:"Занят",3:"Нет на месте",4:"Спит",5:"Ищет игру",6:"Играет"}
                    embed = discord.Embed(title=f"🎮 Steam | {self.target_user.display_name}", description=p.get('personaname','Неизвестно'), color=discord.Color.blue())
                    if p.get('avatarfull'): embed.set_thumbnail(url=p['avatarfull'])
                    embed.add_field(name="🆔 Steam ID", value=self.steam_id, inline=True)
                    embed.add_field(name="🎮 Статус", value=status_map.get(p.get('personastate',0),"Неизвестно"), inline=True)
                    games_url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={self.steam_id}&include_appinfo=true"
                    async with session.get(games_url) as gr:
                        games_data = await gr.json()
                        if games_data.get('response',{}).get('games'):
                            games_list = games_data['response']['games']
                            embed.add_field(name="📚 Игр", value=len(games_list), inline=True)
                            total_hours = sum(g.get('playtime_forever',0) for g in games_list)/60
                            embed.add_field(name="⏱️ Часов", value=f"{total_hours:.0f}ч", inline=True)
                    return embed, None
            return None, "❌ Неизвестно"

@bot.command()
async def steam(ctx, action: str = None, *, arg: str = None):
    if not action: return await ctx.send("🎮 `j.steam set <steam_id>`\n`j.steam profile [@user]`")
    if action == "set":
        if not arg: return await ctx.send("❌ j.steam set <steam_id>")
        await update_user(ctx.author.id, ctx.guild.id, steam_id=arg)
        return await ctx.send(f"✅ Steam ID привязан: {arg}")
    if action == "profile":
        target = ctx.author
        if arg:
            match = re.match(r'<@!?(\d+)>', arg)
            if match: target = ctx.guild.get_member(int(match.group(1))) or await bot.fetch_user(int(match.group(1)))
            else: return await ctx.send("❌ Укажите пользователя через @")
        user_data = await get_user(target.id, ctx.guild.id)
        steam_id = user_data[25] if len(user_data)>25 else None
        if not steam_id: return await ctx.send(f"❌ У {target.mention} не привязан Steam ID")
        view = SteamProfileView(target, steam_id)
        embed, _ = await view.fetch_steam_data("profile")
        if embed: await ctx.send(embed=embed, view=view)
        else: await ctx.send("❌ Не удалось загрузить профиль")

# ========== СТОЛОТО ==========
async def stoloto_scheduler():
    while True:
        now = datetime.now()
        target = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if now >= target: target += timedelta(days=1)
        await asyncio.sleep((target-now).total_seconds())
        await run_stoloto()

async def run_stoloto():
    global stoloto_active, stoloto_tickets, stoloto_end_time
    ch = bot.get_channel(STOLOTO_CHANNEL_ID)
    if not ch: return
    stoloto_active = True
    stoloto_tickets = []
    stoloto_end_time = datetime.now().replace(hour=14, minute=0, second=0) + timedelta(days=1)
    embed = discord.Embed(title="🎰 СТО ЛОТО", description=f"**Новый розыгрыш!**\n⏰ До: <t:{int(stoloto_end_time.timestamp())}:R>\n💰 Джекпот: **{STOLOTO_TICKET_PRICE*10}** 💎\n🎫 `j.loto_buy` - купить билет ({STOLOTO_TICKET_PRICE}💎)", color=discord.Color.gold())
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
    if not stoloto_active: return await ctx.send("❌ Розыгрыш не активен! Новый каждый день в 14:00 МСК")
    if datetime.now() >= stoloto_end_time: return await ctx.send("❌ Продажа билетов закончена!")
    if ctx.author.id in stoloto_tickets: return await ctx.send("❌ У вас уже есть билет!")
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < STOLOTO_TICKET_PRICE: return await ctx.send(f"❌ Нужно {STOLOTO_TICKET_PRICE} 💎")
    await add_balance(ctx.author.id, ctx.guild.id, -STOLOTO_TICKET_PRICE)
    stoloto_tickets.append(ctx.author.id)
    await ctx.send(f"✅ Билет куплен! Участников: {len(stoloto_tickets)}")

# ========== ИДЕИ ==========
@bot.command()
async def suggest(ctx, *, suggestion: str):
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT INTO suggestions (user_id, guild_id, suggestion, date) VALUES (?,?,?,?)', (ctx.author.id, ctx.guild.id, suggestion, datetime.now().isoformat()))
        await db.commit()
        cur = await db.execute('SELECT last_insert_rowid()')
        sid = (await cur.fetchone())[0]
    embed = discord.Embed(title="💡 Новая идея", description=suggestion, color=discord.Color.blue())
    embed.add_field(name="ID", value=sid, inline=True)
    embed.add_field(name="Автор", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    admin_ch = bot.get_channel(IDEA_REVIEW_CHANNEL_ID)
    if admin_ch:
        await admin_ch.send(f"💡 **Идея #{sid}** от {ctx.author.mention}\n{suggestion}\n\n`j.accept {sid}` | `j.deny {sid}`")

@bot.command()
@commands.has_permissions(administrator=True)
async def accept(ctx, sid: int, *, verdict: str = "Принято"):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT user_id, suggestion FROM suggestions WHERE id=? AND guild_id=?', (sid, ctx.guild.id))
        row = await cur.fetchone()
        if not row: return await ctx.send(f"❌ Идея #{sid} не найдена")
        uid, sug = row
        await db.execute('UPDATE suggestions SET status="accepted", verdict=? WHERE id=?', (verdict, sid))
        await db.commit()
    await ctx.send(f"✅ Идея #{sid} принята: {verdict}")
    try:
        author = await bot.fetch_user(uid)
        await author.send(f"✅ Идея #{sid} принята! Вердикт: {verdict}")
    except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def deny(ctx, sid: int, *, verdict: str = "Отклонено"):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT user_id, suggestion FROM suggestions WHERE id=? AND guild_id=?', (sid, ctx.guild.id))
        row = await cur.fetchone()
        if not row: return await ctx.send(f"❌ Идея #{sid} не найдена")
        uid, sug = row
        await db.execute('UPDATE suggestions SET status="denied", verdict=? WHERE id=?', (verdict, sid))
        await db.commit()
    await ctx.send(f"❌ Идея #{sid} отклонена: {verdict}")
    try:
        author = await bot.fetch_user(uid)
        await author.send(f"❌ Идея #{sid} отклонена. Причина: {verdict}")
    except: pass

# ========== РОЗЫГРЫШИ ==========
@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx, action: str, channel: discord.TextChannel = None, prize: str = None, winners: int = None, duration: str = None):
    if action != "create": return await ctx.send("Доступно: create")
    if not channel or not prize or not winners or not duration: return await ctx.send("❌ j.giveaway create #канал приз кол-во 1д/1ч/10м")
    units = {"м":60,"ч":3600,"д":86400}
    unit = duration[-1]
    if unit not in units: return await ctx.send("❌ м, ч, д")
    try: sec = int(duration[:-1]) * units[unit]
    except: return await ctx.send("❌ Неверный формат")
    end = datetime.now() + timedelta(seconds=sec)
    embed = discord.Embed(title="🎉 РОЗЫГРЫШ", description=f"**Приз:** {prize}\n**Победителей:** {winners}\n**До:** <t:{int(end.timestamp())}:R>", color=discord.Color.gold())
    msg = await channel.send(embed=embed)
    await msg.add_reaction("🎉")
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT INTO giveaways (channel_id, message_id, prize, winners, end_time, entries) VALUES (?,?,?,?,?,?)', (channel.id, msg.id, prize, winners, end.isoformat(), '[]'))
        await db.commit()
    await ctx.send(f"✅ Розыгрыш создан в {channel.mention}")
    await asyncio.sleep(sec)
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT prize, winners, entries FROM giveaways WHERE message_id=? AND ended=0', (msg.id,))
        row = await cur.fetchone()
        if not row: return
        prize, wcount, entries_json = row
        entries = json.loads(entries_json)
        await db.execute('UPDATE giveaways SET ended=1 WHERE message_id=?', (msg.id,))
        await db.commit()
    if not entries: await channel.send("😔 Никто не участвовал")
    else:
        selected = random.sample(entries, min(wcount, len(entries)))
        await channel.send(f"🏆 **ПОБЕДИТЕЛИ:** {', '.join(f'<@{uid}>' for uid in selected)}\n🎁 **Приз:** {prize}")

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
    for i, row in enumerate(rows,1):
        uid = row[0]
        user = ctx.guild.get_member(uid)
        name = user.display_name if user else f"ID:{uid}"
        if category == "balance": msg += f"{i}. {name} – {row[1]} 💎\n"
        elif category == "reputation": msg += f"{i}. {name} – {row[1]} ⭐\n"
        elif category == "level": msg += f"{i}. {name} – {row[1]} ур. ({row[2]} XP)\n"
        elif category == "messages": msg += f"{i}. {name} – {row[1]} сообщ.\n"
    await ctx.send(msg[:1900])

@bot.command()
async def top_voice(ctx):
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT user_id, voice_total_seconds FROM users WHERE guild_id=? AND voice_total_seconds>0 ORDER BY voice_total_seconds DESC LIMIT 10', (ctx.guild.id,))
        rows = await cur.fetchall()
    if not rows: return await ctx.send("📊 Нет данных")
    msg = "**🏆 ТОП ПО ГОЛОСОВОМУ ОНЛАЙНУ**\n"
    for i, (uid, sec) in enumerate(rows,1):
        user = ctx.guild.get_member(uid)
        name = user.display_name if user else f"ID:{uid}"
        hours = sec//3600
        minutes = (sec%3600)//60
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "🔹"
        msg += f"{medal} {i}. {name} – {hours}ч {minutes}мин\n"
    await ctx.send(msg)

# ========== НАСТРОЙКИ ==========
@bot.command()
@commands.has_permissions(administrator=True)
async def settings(ctx, module: str = None, channel: discord.TextChannel = None):
    if ctx.guild.id not in guild_settings: guild_settings[ctx.guild.id] = {}
    if not module:
        s = guild_settings[ctx.guild.id]
        embed = discord.Embed(title="⚙️ НАСТРОЙКИ", color=discord.Color.blue())
        embed.add_field(name="📢 Приветствия", value=f"<#{s.get('welcome_channel',0)}>" if s.get('welcome_channel') else "❌ Не установлен", inline=False)
        embed.add_field(name="📝 Логи", value=f"<#{s.get('log_channel',0)}>" if s.get('log_channel') else "❌ Не установлен", inline=False)
        embed.add_field(name="📊 Уровни", value=f"<#{s.get('levels_channel',0)}>" if s.get('levels_channel') else "❌ Не установлен", inline=False)
        await ctx.send(embed=embed)
        return
    if not channel: return await ctx.send(f"❌ Укажите канал: `j.settings {module} #канал`")
    if module == "welcome": guild_settings[ctx.guild.id]["welcome_channel"] = channel.id; await ctx.send(f"✅ Канал приветствий: {channel.mention}")
    elif module == "logs": guild_settings[ctx.guild.id]["log_channel"] = channel.id; await ctx.send(f"✅ Канал логов: {channel.mention}")
    elif module == "levels": guild_settings[ctx.guild.id]["levels_channel"] = channel.id; await ctx.send(f"✅ Канал уровней: {channel.mention}")
    else: await ctx.send("❌ welcome, logs, levels")

# ========== HELP С ВЕЧНЫМИ КНОПКАМИ ==========
class HelpView(View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.page = 0
        self.pages = [
            {"name": "📖 ОСНОВНЫЕ", "content": "`j.profile` - профиль\n`j.balance` - баланс\n`j.work` - работа\n`j.daily` - бонус\n`j.pay @user сумма` - перевод\n`j.bank` - банк\n`j.deposit сумма` - вклад\n`j.withdraw сумма` - вывод\n`j.invest тип сумма` - инвестиции"},
            {"name": "🎮 ИГРЫ", "content": "`j.casino сумма` - казино\n`j.slots сумма` - слоты\n`j.dice число сумма` - кости\n`j.coinflip сторона сумма` - монетка\n`j.rps выбор сумма` - КНБ\n`j.blackjack сумма` - блэкджек\n`j.ttt @user сумма` - крестики\n`j.poker @иг1 @иг2 сумма` - покер\n`j.hangman` - виселица"},
            {"name": "🌾 ФЕРМА", "content": "`j.farm` - ферма\n`j.buy_pot` - горшок\n`j.buy_seed семя` - семена\n`j.plant номер семя` - посадка\n`j.harvest номер` - сбор\n`j.buy_animal животное` - животные\n`j.feed_animals` - кормление\n`j.collect_products` - сбор продукции\n`j.craft рецепт` - крафт"},
            {"name": "🎣 РЫБАЛКА", "content": "`j.fish` - рыбалка\n`j.buy_rod удочка` - удочка\n`j.sell_all` - продать всё"},
            {"name": "🛍️ МАГАЗИН", "content": "`j.shop` - магазин\n`j.buy товар` - купить\n`j.use предмет` - использовать\n`j.inventory` - инвентарь"},
            {"name": "🎫 ТИКЕТЫ", "content": "`j.ticket` - создать тикет\n`j.close_ticket` - закрыть\n`j.tickets_list` - список\n`j.setup_ticket` - настройка (админ)"},
            {"name": "🛡️ МОДЕРАЦИЯ", "content": "`j.warn @user причина` - варн\n`j.mute @user время` - мут\n`j.ban @user причина` - бан\n`j.kick @user причина` - кик\n`j.clear кол-во` - очистка"},
            {"name": "🌤️ РАЗНОЕ", "content": "`j.weather город` - погода\n`j.ai вопрос` - ИИ\n`j.top balance/reps/level` - топы\n`j.top_voice` - топ войс\n`j.daily_quests` - задания\n`j.donate` - поддержка\n`j.reminder время текст` - напоминание\n`j.currency` - курсы валют"}
        ]
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, custom_id="help_prev")
    async def prev(self, i, b):
        if i.user.id != self.author_id: return await i.response.send_message("❌ Не ваша панель!", ephemeral=True)
        self.page = (self.page-1)%len(self.pages)
        embed = discord.Embed(title=self.pages[self.page]["name"], description=self.pages[self.page]["content"], color=discord.Color.blue())
        await i.response.edit_message(embed=embed, view=self)
    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, custom_id="help_next")
    async def nxt(self, i, b):
        if i.user.id != self.author_id: return await i.response.send_message("❌ Не ваша панель!", ephemeral=True)
        self.page = (self.page+1)%len(self.pages)
        embed = discord.Embed(title=self.pages[self.page]["name"], description=self.pages[self.page]["content"], color=discord.Color.blue())
        await i.response.edit_message(embed=embed, view=self)
    @discord.ui.button(label="🔒 Закрыть", style=discord.ButtonStyle.danger, custom_id="help_close")
    async def close(self, i, b):
        if i.user.id != self.author_id: return await i.response.send_message("❌ Не ваша панель!", ephemeral=True)
        await i.response.delete_message()
        self.stop()

@bot.command()
async def help(ctx):
    view = HelpView(ctx.author.id)
    embed = discord.Embed(title=view.pages[0]["name"], description=view.pages[0]["content"], color=discord.Color.blue())
    embed.set_footer(text="Justice Bot | Стрелки для навигации")
    await ctx.send(embed=embed, view=view)

# ========== ЗАПУСК ==========
@bot.event
async def on_ready():
    await init_db()
    print(f"✅ {bot.user} запущен!")
    print(f"📊 На {len(bot.guilds)} серверах")
    bot.loop.create_task(stoloto_scheduler())
    weekly_report.start()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="j.help | Justice Bot"))
    print("✅ Бот готов!")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.guild:
        user_data = await get_user(message.author.id, message.guild.id)
        
        # Автомодерация
        sett = guild_settings.get(message.guild.id, {})
        exempt = any(message.guild.get_role(rid) in message.author.roles for rid in sett.get("automod_exempt_roles",[]))
        if not exempt and sett.get("automod_enabled", True):
            is_spam, reason = await check_spam(message)
            if is_spam:
                try:
                    uid = message.author.id
                    if uid in spam_messages_to_delete and spam_messages_to_delete[uid]:
                        for mid in spam_messages_to_delete[uid]:
                            try: await message.channel.fetch_message(mid).delete()
                            except: pass
                        spam_messages_to_delete[uid] = []
                    else: await message.delete()
                    wc = await add_auto_warning(message.author, reason, message.channel)
                    asyncio.create_task(send_warning_dm(message.author, reason, wc, message.channel))
                except: pass
                return
        
        # Опыт
        level_up, new_level = await add_xp(message.author.id, message.guild.id, random.randint(5,15))
        if level_up:
            ch = bot.get_channel(LEVEL_CHANNEL_ID)
            if ch: await ch.send(f"🎉 {message.author.mention} достиг {new_level} уровня!")
        
        # Достижения за сообщения - ПЕРЕДАЁМ КОЛИЧЕСТВО СООБЩЕНИЙ
        total_msgs = user_data[9] if len(user_data) > 9 else 0
        await check_achievement(message.author.id, message.guild.id, "messages", total_msgs)
        
        # Ежедневные задания
        await check_daily_quest(message.author.id, message.guild.id, "messages", 1)
    
    if bot.user in message.mentions and not message.mention_everyone:
        await message.channel.send(f"👋 Привет, {message.author.mention}! Используй `j.help`")
    await bot.process_commands(message)

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
        embed = discord.Embed(title="🎉 ДОБРО ПОЖАЛОВАТЬ!", description=f"{member.mention} присоединился!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        await ch.send(embed=embed)
    await log_action(member.guild.id, "👋 НОВЫЙ УЧАСТНИК", f"{member.mention} присоединился")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    await ctx.send(f"❌ Ошибка: {str(error)[:100]}")

# ========== ДОНАТ ==========
@bot.command()
async def donate(ctx):
    embed = discord.Embed(title="💝 ПОДДЕРЖАТЬ ПРОЕКТ", description="Спасибо, что помогаете развитию бота!", color=discord.Color.gold())
    embed.add_field(name="💳 Банковские карты", value="Visa / Mastercard / Мир / Maestro / СБП", inline=False)
    embed.add_field(name="🇷🇺 Российские карты", value="Сбербанк / Тинькофф / ВТБ / Альфа-Банк", inline=False)
    embed.add_field(name="🔗 Ссылка", value="https://www.donationalerts.com/r/primera_espada", inline=False)
    await ctx.send(embed=embed)

# ========== ГЕНДЕР ==========
@bot.command()
async def gender(ctx, choice: str = None):
    if not choice:
        return await ctx.send("⚧ **Выбор гендера**\n`j.gender male` - мужчина\n`j.gender female` - девушка\n`j.gender remove` - убрать роль")
    choice = choice.lower()
    male = ctx.guild.get_role(ROLE_BOY)
    female = ctx.guild.get_role(ROLE_GIRL)
    if not male or not female:
        return await ctx.send("❌ Гендерные роли не настроены! Обратитесь к администратору")
    
    if choice in ["male", "мужчина", "мужской", "м", "man"]:
        if female in ctx.author.roles:
            await ctx.author.remove_roles(female)
        await ctx.author.add_roles(male)
        await update_user(ctx.author.id, ctx.guild.id, gender="male")
        await ctx.send(f"✅ {ctx.author.mention} выбрал гендер: Мужчина 👨")
    
    elif choice in ["female", "девушка", "женский", "ж", "woman", "girl"]:
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

# ========== РОЛЕВЫЕ КОМАНДЫ ==========
@bot.command()
async def hug(ctx, member: discord.Member = None):
    if not member:
        embed = discord.Embed(description=f"{ctx.author.mention} обнимает себя! 🤗", color=discord.Color.pink())
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} обнимает {member.mention}! 🤗", color=discord.Color.pink())
    embed.set_image(url=REACTION_GIFS.get("hug", ""))
    await ctx.send(embed=embed)

@bot.command()
async def kiss(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} целует воздух! 💋")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} целует {member.mention}! 💋", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("kiss", ""))
        await ctx.send(embed=embed)

@bot.command()
async def pat(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} гладит себя! 🖐️")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} гладит {member.mention}! 🖐️", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("pat", ""))
        await ctx.send(embed=embed)

@bot.command()
async def poke(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} тыкает в воздух! 👉")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} тыкает {member.mention}! 👉", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("poke", ""))
        await ctx.send(embed=embed)

@bot.command()
async def slap(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} шлёпает воздух! 👋")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} шлёпает {member.mention}! 👋", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("slap", ""))
        await ctx.send(embed=embed)

@bot.command()
async def punch(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} бьёт воздух! 👊")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} бьёт {member.mention}! 👊", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("punch", ""))
        await ctx.send(embed=embed)

@bot.command()
async def bite(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} кусает воздух! 🦷")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} кусает {member.mention}! 🦷", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("bite", ""))
        await ctx.send(embed=embed)

@bot.command()
async def cry(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} плачет! 😢", color=discord.Color.blue())
    embed.set_image(url=REACTION_GIFS.get("cry", ""))
    await ctx.send(embed=embed)

@bot.command()
async def laugh(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} смеётся! 😂", color=discord.Color.green())
    embed.set_image(url=REACTION_GIFS.get("laugh", ""))
    await ctx.send(embed=embed)

@bot.command()
async def smile(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} улыбается! 😊", color=discord.Color.yellow())
    embed.set_image(url=REACTION_GIFS.get("smile", ""))
    await ctx.send(embed=embed)

@bot.command()
async def blush(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} краснеет! 😊", color=discord.Color.pink())
    embed.set_image(url=REACTION_GIFS.get("blush", ""))
    await ctx.send(embed=embed)

@bot.command()
async def dance(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} танцует! 💃", color=discord.Color.purple())
    embed.set_image(url=REACTION_GIFS.get("dance", ""))
    await ctx.send(embed=embed)

@bot.command()
async def celebrate(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} празднует! 🎉", color=discord.Color.gold())
    embed.set_image(url=REACTION_GIFS.get("celebrate", ""))
    await ctx.send(embed=embed)

@bot.command()
async def airkiss(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} посылает воздушный поцелуй! 💋")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} посылает воздушный поцелуй {member.mention}! 💋", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("airkiss", ""))
        await ctx.send(embed=embed)

@bot.command()
async def handhold(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} держит себя за руку! 👫")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} держит за руку {member.mention}! 👫", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("handhold", ""))
        await ctx.send(embed=embed)

@bot.command()
async def tickle(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} щекочет себя! 😂")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} щекочет {member.mention}! 😂", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("tickle", ""))
        await ctx.send(embed=embed)

@bot.command()
async def run(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} бежит! 🏃", color=discord.Color.blue())
    embed.set_image(url=REACTION_GIFS.get("run", ""))
    await ctx.send(embed=embed)

@bot.command()
async def sleep(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} спит! 😴", color=discord.Color.dark_blue())
    embed.set_image(url=REACTION_GIFS.get("sleep", ""))
    await ctx.send(embed=embed)

@bot.command()
async def shrug(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} пожимает плечами! 🤷", color=discord.Color.orange())
    embed.set_image(url=REACTION_GIFS.get("shrug", ""))
    await ctx.send(embed=embed)

@bot.command()
async def shy(ctx):
    embed = discord.Embed(description=f"{ctx.author.mention} стесняется! 😊", color=discord.Color.pink())
    embed.set_image(url=REACTION_GIFS.get("shy", ""))
    await ctx.send(embed=embed)

@bot.command()
async def sorry(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} извиняется! 🙏")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} извиняется перед {member.mention}! 🙏", color=discord.Color.blue())
        embed.set_image(url=REACTION_GIFS.get("sorry", ""))
        await ctx.send(embed=embed)

@bot.command()
async def stare(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} смотрит в пустоту! 👀")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} смотрит на {member.mention}! 👀", color=discord.Color.blue())
        embed.set_image(url=REACTION_GIFS.get("stare", ""))
        await ctx.send(embed=embed)

@bot.command()
async def wink(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"{ctx.author.mention} подмигивает! 😉")
    else:
        embed = discord.Embed(description=f"{ctx.author.mention} подмигивает {member.mention}! 😉", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS.get("wink", ""))
        await ctx.send(embed=embed)

# ========== ИНФО КОМАНДЫ ==========
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    t = member or ctx.author
    d = await get_user(t.id, ctx.guild.id)
    embed = discord.Embed(title=f"👤 ИНФОРМАЦИЯ | {t.display_name}", color=discord.Color.blue())
    embed.set_thumbnail(url=t.display_avatar.url)
    embed.add_field(name="🆔 ID", value=t.id, inline=True)
    embed.add_field(name="📊 Уровень", value=d[3], inline=True)
    embed.add_field(name="⭐ Репутация", value=d[6] if len(d)>6 else 0, inline=True)
    embed.add_field(name="📅 Аккаунт создан", value=t.created_at.strftime("%d.%m.%Y %H:%M"), inline=True)
    embed.add_field(name="📅 Присоединился", value=t.joined_at.strftime("%d.%m.%Y %H:%M"), inline=True)
    embed.add_field(name="🎭 Роли", value=", ".join([r.mention for r in t.roles[1:8]]) or "Нет", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    embed = discord.Embed(title=f"📊 ИНФОРМАЦИЯ | {g.name}", color=discord.Color.blue())
    if g.icon: embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="👑 Владелец", value=g.owner.mention, inline=True)
    embed.add_field(name="👥 Участников", value=g.member_count, inline=True)
    embed.add_field(name="💬 Текстовых", value=len(g.text_channels), inline=True)
    embed.add_field(name="🎤 Голосовых", value=len(g.voice_channels), inline=True)
    embed.add_field(name="🎭 Ролей", value=len(g.roles), inline=True)
    embed.add_field(name="📅 Создан", value=g.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="🔒 Уровень верификации", value=str(g.verification_level), inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Понг! Задержка: **{round(bot.latency*1000)} мс**")

@bot.command()
async def about(ctx):
    embed = discord.Embed(title="🤖 JUSTICE BOT", color=discord.Color.blue())
    embed.add_field(name="📦 Версия", value="5.0", inline=True)
    embed.add_field(name="📚 Библиотека", value="discord.py", inline=True)
    embed.add_field(name="🖥️ Серверов", value=len(bot.guilds), inline=True)
    embed.add_field(name="⚙️ Команд", value="250+", inline=True)
    embed.add_field(name="🔤 Префикс", value="j.", inline=True)
    embed.set_footer(text="Разработан для Justice Server")
    await ctx.send(embed=embed)

@bot.command()
async def invite(ctx):
    inv_link = f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands"
    embed = discord.Embed(title="🔗 ПРИГЛАСИТЬ БОТА", description=f"[Нажмите сюда]({inv_link})", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
async def reminder(ctx, time_str: str = None, *, text: str = None):
    if not time_str or not text:
        return await ctx.send("⏰ **Напоминание**\n`j.reminder 10м Написать отчёт`\nДоступно: м, ч, д")
    units = {"м":60, "ч":3600, "д":86400}
    u = time_str[-1]
    if u not in units:
        return await ctx.send("❌ Используйте: 10м, 1ч, 1д")
    try:
        sec = int(time_str[:-1]) * units[u]
    except:
        return await ctx.send("❌ Неверный формат времени")
    await ctx.send(f"✅ Напоминание установлено! Я напомню через {time_str}")
    await asyncio.sleep(sec)
    await ctx.author.send(f"⏰ **НАПОМИНАНИЕ!**\nВы просили напомнить: {text}")

@bot.command()
async def daily_quests(ctx):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT quest1_id, quest1_progress, quest1_completed, quest2_id, quest2_progress, quest2_completed, quest3_id, quest3_progress, quest3_completed FROM daily_quests WHERE user_id=? AND guild_id=? AND quest_date=?', (ctx.author.id, ctx.guild.id, today))
        quests = await cur.fetchone()
        if not quests:
            return await ctx.send("📋 Сегодняшние задания ещё не сгенерированы! Напишите что-нибудь в чат, и они появятся.")
    embed = discord.Embed(title="📋 ЕЖЕДНЕВНЫЕ ЗАДАНИЯ", description=f"Задания на {today}", color=discord.Color.blue())
    for i in range(3):
        qid = quests[i*3]
        progress = quests[i*3+1]
        completed = quests[i*3+2]
        qdata = DAILY_QUESTS.get(qid, {})
        status = "✅" if completed else "⏳"
        embed.add_field(name=f"{status} {qdata.get('name', '???')}", value=f"Прогресс: {progress}/{qdata.get('target', 0)} | Награда: {qdata.get('reward', 0)} 💎", inline=False)
    await ctx.send(embed=embed)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Запуск Justice Bot...")
    if not TOKEN or TOKEN == "ВСТАВЬ_СВОЙ_ТОКЕН":
        print("❌ ВСТАВЬ ТОКЕН В ПЕРЕМЕННУЮ ОКРУЖЕНИЯ DISCORD_TOKEN!")
        exit(1)
    bot.run(TOKEN)
