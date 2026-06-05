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

# ========== ЛОГИРОВАНИЕ ==========
LOG_ACTION_CHANNEL_ID = 1502637204982206681  # ВСТАВЬ ID КАНАЛА ДЛЯ ЛОГОВ

async def log_action(guild_id, title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now())
    if LOG_ACTION_CHANNEL_ID:
        ch = bot.get_channel(LOG_ACTION_CHANNEL_ID)
        if ch:
            await ch.send(embed=embed)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {title}: {description[:100]}")

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    TOKEN = "ВСТАВЬ_СВОЙ_ТОКЕН"

STEAM_API_KEY = os.getenv('STEAM_API_KEY')
YANDEX_WEATHER_API_KEY = os.getenv('YANDEX_WEATHER_API_KEY')

AI_API_KEY = "rk_live_G15mOokgVTN8hKFBvWVda38wZGOiXkVs"
AI_BASE_URL = "https://api.ranvik.ru/v1"
AI_MODEL = "gpt-5-nano"

# ========== ДОСТИЖЕНИЯ (150+) ==========
ACHIEVEMENTS = {
    # Сообщения (0-50)
    "msg_10": {"name": "📝 Первые шаги", "desc": "Написать 10 сообщений", "reward": 100},
    "msg_50": {"name": "📝 Говорун", "desc": "Написать 50 сообщений", "reward": 500},
    "msg_100": {"name": "📝 Болтун", "desc": "Написать 100 сообщений", "reward": 1000},
    "msg_500": {"name": "📝 Оратор", "desc": "Написать 500 сообщений", "reward": 5000},
    "msg_1000": {"name": "📝 Мастер слова", "desc": "Написать 1000 сообщений", "reward": 10000},
    "msg_5000": {"name": "📝 Легенда чата", "desc": "Написать 5000 сообщений", "reward": 50000},
    "msg_10000": {"name": "📝 Живая легенда", "desc": "Написать 10000 сообщений", "reward": 100000},
    
    # Уровни (1-20)
    "lvl_5": {"name": "🎚️ Новичок", "desc": "Достичь 5 уровня", "reward": 500},
    "lvl_10": {"name": "🎚️ Опытный", "desc": "Достичь 10 уровня", "reward": 1000},
    "lvl_25": {"name": "🎚️ Мастер", "desc": "Достичь 25 уровня", "reward": 5000},
    "lvl_50": {"name": "🎚️ Эксперт", "desc": "Достичь 50 уровня", "reward": 15000},
    "lvl_100": {"name": "🎚️ Гуру", "desc": "Достичь 100 уровня", "reward": 50000},
    
    # Баланс (1-10)
    "bal_1000": {"name": "💰 Первые деньги", "desc": "Иметь 1000 💎", "reward": 100},
    "bal_10000": {"name": "💰 Состояние", "desc": "Иметь 10000 💎", "reward": 1000},
    "bal_100000": {"name": "💰 Богач", "desc": "Иметь 100000 💎", "reward": 10000},
    "bal_500000": {"name": "💰 Миллионер", "desc": "Иметь 500000 💎", "reward": 50000},
    "bal_1000000": {"name": "💰 Легенда богатства", "desc": "Иметь 1 млн 💎", "reward": 100000},
    
    # Репутация (1-6)
    "rep_10": {"name": "⭐ Народный любимчик", "desc": "Иметь 10 репутации", "reward": 500},
    "rep_50": {"name": "⭐ Уважаемый", "desc": "Иметь 50 репутации", "reward": 2500},
    "rep_100": {"name": "⭐ Звезда", "desc": "Иметь 100 репутации", "reward": 10000},
    "rep_500": {"name": "⭐ Кумир", "desc": "Иметь 500 репутации", "reward": 50000},
    "rep_1000": {"name": "⭐ Живая легенда", "desc": "Иметь 1000 репутации", "reward": 100000},
    
    # Игры (1-12)
    "win_casino_10": {"name": "🎰 Удачливый", "desc": "Выиграть 10 раз в казино", "reward": 1000},
    "win_casino_50": {"name": "🎰 Азартный", "desc": "Выиграть 50 раз в казино", "reward": 5000},
    "win_casino_100": {"name": "🎰 Король казино", "desc": "Выиграть 100 раз в казино", "reward": 20000},
    "win_blackjack_10": {"name": "🃏 Картёжник", "desc": "Выиграть 10 раз в блэкджек", "reward": 1000},
    "win_poker_5": {"name": "🃏 Профи покера", "desc": "Выиграть 5 раз в покер", "reward": 5000},
    "win_ttt_10": {"name": "❌⭕ Стратег", "desc": "Выиграть 10 раз в крестики-нолики", "reward": 2000},
    
    # Рыбалка (1-7)
    "fish_10": {"name": "🎣 Рыбак-любитель", "desc": "Поймать 10 рыб", "reward": 200},
    "fish_100": {"name": "🎣 Опытный рыбак", "desc": "Поймать 100 рыб", "reward": 2000},
    "fish_500": {"name": "🎣 Профессионал", "desc": "Поймать 500 рыб", "reward": 10000},
    "fish_1000": {"name": "🎣 Король рыбалки", "desc": "Поймать 1000 рыб", "reward": 50000},
    "fish_legendary": {"name": "🐉 Ловец легенд", "desc": "Поймать легендарную рыбу", "reward": 10000},
    "fish_mythic": {"name": "✨ Ловец мифов", "desc": "Поймать мифическую рыбу", "reward": 50000},
    
    # Ферма (1-6)
    "plant_10": {"name": "🌱 Садовод", "desc": "Посадить 10 культур", "reward": 200},
    "harvest_100": {"name": "🌾 Фермер", "desc": "Собрать 100 урожаев", "reward": 2000},
    "harvest_1000": {"name": "🌾 Аграрий", "desc": "Собрать 1000 урожаев", "reward": 20000},
    "legendary_crop": {"name": "✨ Золотой урожай", "desc": "Вырастить легендарную культуру", "reward": 10000},
    
    # Голосовой онлайн (1-7)
    "voice_1h": {"name": "🎤 Первые минуты", "desc": "Провести 1 час в голосовом канале", "reward": 100},
    "voice_24h": {"name": "🎤 Голосовой активист", "desc": "Провести 24 часа в голосовом канале", "reward": 2000},
    "voice_100h": {"name": "🎤 Войс-легенда", "desc": "Провести 100 часов в голосовом канале", "reward": 10000},
    "voice_500h": {"name": "🎤 Войс-маньяк", "desc": "Провести 500 часов в голосовом канале", "reward": 50000},
    "voice_streak_7": {"name": "🔥 Огонёк", "desc": "7 дней подряд в войсе", "reward": 1000},
    "voice_streak_30": {"name": "🔥 Неугасимый", "desc": "30 дней подряд в войсе", "reward": 10000},
    "voice_streak_100": {"name": "🔥 Вечный огонь", "desc": "100 дней подряд в войсе", "reward": 100000},
    
    # Приглашения (1-5)
    "invite_1": {"name": "📨 Приглашатель", "desc": "Пригласить 1 друга", "reward": 500},
    "invite_5": {"name": "📨 Популяризатор", "desc": "Пригласить 5 друзей", "reward": 2500},
    "invite_10": {"name": "📨 Амбассадор", "desc": "Пригласить 10 друзей", "reward": 10000},
    "invite_50": {"name": "📨 Легенда приглашений", "desc": "Пригласить 50 друзей", "reward": 100000},
    
    # Магазин (1-4)
    "shop_buy_10": {"name": "🛍️ Покупатель", "desc": "Купить 10 предметов", "reward": 500},
    "shop_spend_100k": {"name": "💎 Транжира", "desc": "Потратить 100000 💎", "reward": 10000},
    "shop_spend_1m": {"name": "💎 Мега-транжира", "desc": "Потратить 1 млн 💎", "reward": 100000},
    
    # Особые достижения
    "donate_1000": {"name": "💝 Благодетель", "desc": "Задонатить 1000 💎", "reward": 1000},
    "daily_30": {"name": "📆 Железная воля", "desc": "30 дней подряд забирать ежедневный бонус", "reward": 50000},
    "work_100": {"name": "💼 Трудоголик", "desc": "100 раз поработать", "reward": 5000},
    "rob_10": {"name": "🔫 Грабитель", "desc": "10 успешных ограблений", "reward": 2000},
    "rob_50": {"name": "🔫 Король грабежей", "desc": "50 успешных ограблений", "reward": 10000},
    
    # Сезонные
    "xmas_2025": {"name": "🎄 Санта", "desc": "Новогоднее событие 2025", "reward": 15000},
    "newyear_2026": {"name": "🎆 Новогодний", "desc": "Новогоднее событие 2026", "reward": 20000},
    "summer_2025": {"name": "☀️ Летний", "desc": "Летнее событие 2025", "reward": 10000},
}

# ========== ЕЖЕДНЕВНЫЕ ЗАДАНИЯ (200+ ШТУК, МАЛЕНЬКИЕ НАГРАДЫ) ==========
DAILY_QUESTS = {
    # Сообщения (1-10)
    "msg_5": {"name": "📝 Поболтать", "desc": "Написать 5 сообщений", "target": 5, "reward": 50, "type": "messages"},
    "msg_10": {"name": "📝 Разговорчивый", "desc": "Написать 10 сообщений", "target": 10, "reward": 75, "type": "messages"},
    "msg_15": {"name": "📝 Активный", "desc": "Написать 15 сообщений", "target": 15, "reward": 100, "type": "messages"},
    "msg_20": {"name": "📝 Общительный", "desc": "Написать 20 сообщений", "target": 20, "reward": 125, "type": "messages"},
    "msg_25": {"name": "📝 Говорун", "desc": "Написать 25 сообщений", "target": 25, "reward": 150, "type": "messages"},
    "msg_30": {"name": "📝 Болтун", "desc": "Написать 30 сообщений", "target": 30, "reward": 175, "type": "messages"},
    "msg_40": {"name": "📝 Энергичный", "desc": "Написать 40 сообщений", "target": 40, "reward": 200, "type": "messages"},
    "msg_50": {"name": "📝 Мастер диалога", "desc": "Написать 50 сообщений", "target": 50, "reward": 250, "type": "messages"},
    
    # Казино (1-8)
    "casino_1": {"name": "🎰 Испытать удачу", "desc": "Сыграть в казино 1 раз", "target": 1, "reward": 100, "type": "casino_play"},
    "casino_2": {"name": "🎰 Азартный", "desc": "Сыграть в казино 2 раза", "target": 2, "reward": 150, "type": "casino_play"},
    "casino_3": {"name": "🎰 Игрок", "desc": "Сыграть в казино 3 раза", "target": 3, "reward": 200, "type": "casino_play"},
    "casino_win_1": {"name": "🎰 Удача", "desc": "Выиграть в казино 1 раз", "target": 1, "reward": 150, "type": "casino_win"},
    "casino_win_2": {"name": "🎰 Фортуна", "desc": "Выиграть в казино 2 раза", "target": 2, "reward": 200, "type": "casino_win"},
    "casino_win_3": {"name": "🎰 Везунчик", "desc": "Выиграть в казино 3 раза", "target": 3, "reward": 300, "type": "casino_win"},
    
    # Монетка (1-8)
    "coin_1": {"name": "🪙 Подбросить", "desc": "Сыграть в монетку 1 раз", "target": 1, "reward": 50, "type": "coin_play"},
    "coin_2": {"name": "🪙 Орёл или решка", "desc": "Сыграть в монетку 2 раза", "target": 2, "reward": 75, "type": "coin_play"},
    "coin_3": {"name": "🪙 Азарт", "desc": "Сыграть в монетку 3 раза", "target": 3, "reward": 100, "type": "coin_play"},
    "coin_win_1": {"name": "🪙 Угадал", "desc": "Выиграть в монетку 1 раз", "target": 1, "reward": 75, "type": "coin_win"},
    "coin_win_2": {"name": "🪙 Ясновидящий", "desc": "Выиграть в монетку 2 раза", "target": 2, "reward": 100, "type": "coin_win"},
    
    # Кости (1-8)
    "dice_1": {"name": "🎲 Бросок", "desc": "Сыграть в кости 1 раз", "target": 1, "reward": 50, "type": "dice_play"},
    "dice_2": {"name": "🎲 Игрок в кости", "desc": "Сыграть в кости 2 раза", "target": 2, "reward": 75, "type": "dice_play"},
    "dice_3": {"name": "🎲 Кубик", "desc": "Сыграть в кости 3 раза", "target": 3, "reward": 100, "type": "dice_play"},
    "dice_win_1": {"name": "🎲 Угадал число", "desc": "Выиграть в кости 1 раз", "target": 1, "reward": 100, "type": "dice_win"},
    "dice_win_2": {"name": "🎲 Шулер", "desc": "Выиграть в кости 2 раза", "target": 2, "reward": 150, "type": "dice_win"},
    
    # КНБ (1-6)
    "rps_1": {"name": "✊ Камень", "desc": "Сыграть в КНБ 1 раз", "target": 1, "reward": 50, "type": "rps_play"},
    "rps_2": {"name": "✊ Ножницы", "desc": "Сыграть в КНБ 2 раза", "target": 2, "reward": 75, "type": "rps_play"},
    "rps_3": {"name": "✊ Бумага", "desc": "Сыграть в КНБ 3 раза", "target": 3, "reward": 100, "type": "rps_play"},
    "rps_win_1": {"name": "✊ Победитель", "desc": "Выиграть в КНБ 1 раз", "target": 1, "reward": 75, "type": "rps_win"},
    
    # Блэкджек (1-6)
    "bj_1": {"name": "🃏 Первая карта", "desc": "Сыграть в блэкджек 1 раз", "target": 1, "reward": 100, "type": "bj_play"},
    "bj_2": {"name": "🃏 Картёжник", "desc": "Сыграть в блэкджек 2 раза", "target": 2, "reward": 150, "type": "bj_play"},
    "bj_3": {"name": "🃏 Двадцать одно", "desc": "Сыграть в блэкджек 3 раза", "target": 3, "reward": 200, "type": "bj_play"},
    "bj_win_1": {"name": "🃏 Блэкджек", "desc": "Выиграть в блэкджек 1 раз", "target": 1, "reward": 150, "type": "bj_win"},
    
    # Крестики-нолики (1-5)
    "ttt_1": {"name": "❌ Крестик", "desc": "Сыграть в крестики-нолики 1 раз", "target": 1, "reward": 100, "type": "ttt_play"},
    "ttt_2": {"name": "⭕ Нолик", "desc": "Сыграть в крестики-нолики 2 раза", "target": 2, "reward": 150, "type": "ttt_play"},
    "ttt_win_1": {"name": "❌⭕ Стратег", "desc": "Выиграть в крестики-нолики 1 раз", "target": 1, "reward": 200, "type": "ttt_win"},
    
    # Покер (1-4)
    "poker_1": {"name": "🃏 Первая раздача", "desc": "Сыграть в покер 1 раз", "target": 1, "reward": 200, "type": "poker_play"},
    "poker_2": {"name": "🃏 Блеф", "desc": "Сыграть в покер 2 раза", "target": 2, "reward": 300, "type": "poker_play"},
    "poker_win_1": {"name": "🃏 Покерист", "desc": "Выиграть в покер 1 раз", "target": 1, "reward": 400, "type": "poker_win"},
    
    # Рыбалка (1-10)
    "fish_1": {"name": "🎣 Удочка", "desc": "Поймать 1 рыбу", "target": 1, "reward": 50, "type": "fish"},
    "fish_2": {"name": "🎣 Клёв", "desc": "Поймать 2 рыбы", "target": 2, "reward": 75, "type": "fish"},
    "fish_3": {"name": "🎣 Рыбак", "desc": "Поймать 3 рыбы", "target": 3, "reward": 100, "type": "fish"},
    "fish_4": {"name": "🎣 Улов", "desc": "Поймать 4 рыбы", "target": 4, "reward": 125, "type": "fish"},
    "fish_5": {"name": "🎣 Любитель рыбалки", "desc": "Поймать 5 рыб", "target": 5, "reward": 150, "type": "fish"},
    "fish_7": {"name": "🎣 Опытный рыбак", "desc": "Поймать 7 рыб", "target": 7, "reward": 175, "type": "fish"},
    "fish_10": {"name": "🎣 Профи", "desc": "Поймать 10 рыб", "target": 10, "reward": 200, "type": "fish"},
    "legendary_fish": {"name": "🐉 Ловец легенд", "desc": "Поймать легендарную рыбу", "target": 1, "reward": 300, "type": "legendary_fish"},
    "mythic_fish": {"name": "✨ Ловец мифов", "desc": "Поймать мифическую рыбу", "target": 1, "reward": 500, "type": "mythic_fish"},
    
    # Ферма (1-15)
    "plant_1": {"name": "🌱 Первая посадка", "desc": "Посадить 1 культуру", "target": 1, "reward": 50, "type": "plant"},
    "plant_2": {"name": "🌱 Садовод", "desc": "Посадить 2 культуры", "target": 2, "reward": 75, "type": "plant"},
    "plant_3": {"name": "🌱 Огородник", "desc": "Посадить 3 культуры", "target": 3, "reward": 100, "type": "plant"},
    "plant_5": {"name": "🌱 Фермер", "desc": "Посадить 5 культур", "target": 5, "reward": 150, "type": "plant"},
    "harvest_1": {"name": "🌾 Первый урожай", "desc": "Собрать 1 урожай", "target": 1, "reward": 50, "type": "harvest"},
    "harvest_2": {"name": "🌾 Урожай", "desc": "Собрать 2 урожая", "target": 2, "reward": 75, "type": "harvest"},
    "harvest_3": {"name": "🌾 Сбор", "desc": "Собрать 3 урожая", "target": 3, "reward": 100, "type": "harvest"},
    "harvest_5": {"name": "🌾 Жатва", "desc": "Собрать 5 урожаев", "target": 5, "reward": 150, "type": "harvest"},
    "sell_crop_1": {"name": "💰 Первая продажа", "desc": "Продать 1 урожай", "target": 1, "reward": 50, "type": "sell_crops"},
    "sell_crop_3": {"name": "💰 Торговец", "desc": "Продать 3 урожая", "target": 3, "reward": 100, "type": "sell_crops"},
    "sell_crop_5": {"name": "💰 Барыга", "desc": "Продать 5 урожаев", "target": 5, "reward": 150, "type": "sell_crops"},

        # Работа (1-7)
    "work_1": {"name": "💼 Первый рабочий день", "desc": "Поработать 1 раз", "target": 1, "reward": 100, "type": "work"},
    "work_2": {"name": "💼 Трудяга", "desc": "Поработать 2 раза", "target": 2, "reward": 150, "type": "work"},
    "work_3": {"name": "💼 Работник", "desc": "Поработать 3 раза", "target": 3, "reward": 200, "type": "work"},
    "work_4": {"name": "💼 Усердный", "desc": "Поработать 4 раза", "target": 4, "reward": 250, "type": "work"},
    "work_5": {"name": "💼 Трудоголик", "desc": "Поработать 5 раз", "target": 5, "reward": 300, "type": "work"},
    
    # Ограбления (1-5)
    "rob_1": {"name": "🔫 Первое ограбление", "desc": "Ограбить 1 раз", "target": 1, "reward": 150, "type": "rob"},
    "rob_2": {"name": "🔫 Грабёж", "desc": "Ограбить 2 раза", "target": 2, "reward": 200, "type": "rob"},
    "rob_3": {"name": "🔫 Вор", "desc": "Ограбить 3 раза", "target": 3, "reward": 250, "type": "rob"},
    "rob_success_1": {"name": "🔫 Удачное ограбление", "desc": "Успешно ограбить 1 раз", "target": 1, "reward": 200, "type": "rob_success"},
    "rob_success_2": {"name": "🔫 Профи", "desc": "Успешно ограбить 2 раза", "target": 2, "reward": 300, "type": "rob_success"},
    
    # Голосовой онлайн (1-10)
    "voice_5min": {"name": "🎤 Первые минуты", "desc": "Провести 5 минут в голосовом канале", "target": 5, "reward": 50, "type": "voice_minutes"},
    "voice_10min": {"name": "🎤 Разговор", "desc": "Провести 10 минут в голосовом канале", "target": 10, "reward": 75, "type": "voice_minutes"},
    "voice_15min": {"name": "🎤 Болтовня", "desc": "Провести 15 минут в голосовом канале", "target": 15, "reward": 100, "type": "voice_minutes"},
    "voice_30min": {"name": "🎤 Беседа", "desc": "Провести 30 минут в голосовом канале", "target": 30, "reward": 150, "type": "voice_minutes"},
    "voice_1h": {"name": "🎤 Час в эфире", "desc": "Провести 1 час в голосовом канале", "target": 60, "reward": 200, "type": "voice_minutes"},
    "voice_2h": {"name": "🎤 Два часа", "desc": "Провести 2 часа в голосовом канале", "target": 120, "reward": 300, "type": "voice_minutes"},
    "voice_3h": {"name": "🎤 Три часа", "desc": "Провести 3 часа в голосовом канале", "target": 180, "reward": 400, "type": "voice_minutes"},
    
    # Репутация (1-6)
    "give_rep_1": {"name": "❤️ Первое спасибо", "desc": "Дать репутацию 1 раз", "target": 1, "reward": 100, "type": "give_rep"},
    "give_rep_2": {"name": "❤️ Благодарность", "desc": "Дать репутацию 2 раза", "target": 2, "reward": 150, "type": "give_rep"},
    "give_rep_3": {"name": "❤️ Добряк", "desc": "Дать репутацию 3 раза", "target": 3, "reward": 200, "type": "give_rep"},
    "receive_rep_1": {"name": "❤️ Первая репутация", "desc": "Получить репутацию 1 раз", "target": 1, "reward": 100, "type": "receive_rep"},
    "receive_rep_3": {"name": "❤️ Уважаемый", "desc": "Получить репутацию 3 раза", "target": 3, "reward": 200, "type": "receive_rep"},
    
    # Магазин (1-7)
    "buy_1": {"name": "🛍️ Первая покупка", "desc": "Купить 1 предмет", "target": 1, "reward": 50, "type": "buy"},
    "buy_2": {"name": "🛍️ Шопинг", "desc": "Купить 2 предмета", "target": 2, "reward": 75, "type": "buy"},
    "buy_3": {"name": "🛍️ Покупатель", "desc": "Купить 3 предмета", "target": 3, "reward": 100, "type": "buy"},
    "buy_5": {"name": "🛍️ Транжира", "desc": "Купить 5 предметов", "target": 5, "reward": 150, "type": "buy"},
    "spend_1000": {"name": "💰 Потратить", "desc": "Потратить 1000 💎", "target": 1000, "reward": 100, "type": "spend"},
    "spend_5000": {"name": "💰 Крупная трата", "desc": "Потратить 5000 💎", "target": 5000, "reward": 200, "type": "spend"},
    "spend_10000": {"name": "💰 Миллионер", "desc": "Потратить 10000 💎", "target": 10000, "reward": 300, "type": "spend"},
    
    # Прогресс (1-12)
    "daily_1": {"name": "📅 Ежедневный ритуал", "desc": "Забрать ежедневный бонус 1 раз", "target": 1, "reward": 100, "type": "daily"},
    "daily_3": {"name": "📅 Три дня", "desc": "Забрать ежедневный бонус 3 раза", "target": 3, "reward": 200, "type": "daily"},
    "daily_5": {"name": "📅 Пятый день", "desc": "Забрать ежедневный бонус 5 раз", "target": 5, "reward": 300, "type": "daily"},
    "daily_7": {"name": "📅 Неделя", "desc": "Забрать ежедневный бонус 7 раз", "target": 7, "reward": 500, "type": "daily"},
    "daily_14": {"name": "📅 Две недели", "desc": "Забрать ежедневный бонус 14 раз", "target": 14, "reward": 700, "type": "daily"},
    "daily_30": {"name": "📅 Месяц", "desc": "Забрать ежедневный бонус 30 раз", "target": 30, "reward": 1000, "type": "daily"},
    "level_up_1": {"name": "📈 Первый уровень", "desc": "Повысить уровень 1 раз", "target": 1, "reward": 200, "type": "level_up"},
    "level_up_3": {"name": "📈 Рост", "desc": "Повысить уровень 3 раза", "target": 3, "reward": 300, "type": "level_up"},
    "level_up_5": {"name": "📈 Развитие", "desc": "Повысить уровень 5 раз", "target": 5, "reward": 500, "type": "level_up"},
    
    # Активность (1-8)
    "login_1": {"name": "👋 Зашёл", "desc": "Зайти на сервер 1 раз", "target": 1, "reward": 50, "type": "login"},
    "login_3": {"name": "👋 Постоянный", "desc": "Зайти на сервер 3 раза", "target": 3, "reward": 100, "type": "login"},
    "login_5": {"name": "👋 Завсегдатай", "desc": "Зайти на сервер 5 раз", "target": 5, "reward": 150, "type": "login"},
    "login_7": {"name": "👋 Активный", "desc": "Зайти на сервер 7 раз", "target": 7, "reward": 200, "type": "login"},
    
    # Слоты (1-6)
    "slots_1": {"name": "🎰 Первый спин", "desc": "Сыграть в слоты 1 раз", "target": 1, "reward": 75, "type": "slots_play"},
    "slots_3": {"name": "🎰 Джекпот охотник", "desc": "Сыграть в слоты 3 раза", "target": 3, "reward": 150, "type": "slots_play"},
    "slots_5": {"name": "🎰 Азартный игрок", "desc": "Сыграть в слоты 5 раз", "target": 5, "reward": 200, "type": "slots_play"},
    "slots_jackpot": {"name": "🎰 ДЖЕКПОТ", "desc": "Сорвать джекпот в слотах", "target": 1, "reward": 500, "type": "slots_jackpot"},
    
    # Крафт (1-5)
    "craft_1": {"name": "🔨 Первая поделка", "desc": "Скрафтить 1 предмет", "target": 1, "reward": 100, "type": "craft"},
    "craft_3": {"name": "🔨 Кустарное производство", "desc": "Скрафтить 3 предмета", "target": 3, "reward": 200, "type": "craft"},
    "craft_5": {"name": "🔨 Мастер на все руки", "desc": "Скрафтить 5 предметов", "target": 5, "reward": 300, "type": "craft"},
    
    # Животные (1-6)
    "buy_animal_1": {"name": "🐔 Первый питомец", "desc": "Купить 1 животное", "target": 1, "reward": 150, "type": "buy_animal"},
    "buy_animal_3": {"name": "🐔 Фермер", "desc": "Купить 3 животных", "target": 3, "reward": 300, "type": "buy_animal"},
    "feed_animal_1": {"name": "🌾 Покормить", "desc": "Покормить животное 1 раз", "target": 1, "reward": 50, "type": "feed_animal"},
    "feed_animal_5": {"name": "🌾 Заботливый", "desc": "Покормить животное 5 раз", "target": 5, "reward": 150, "type": "feed_animal"},
    "collect_animal_1": {"name": "🥚 Собрать продукцию", "desc": "Собрать продукцию с животного 1 раз", "target": 1, "reward": 75, "type": "collect_animal"},
    "collect_animal_5": {"name": "🥚 Продуктивный", "desc": "Собрать продукцию 5 раз", "target": 5, "reward": 200, "type": "collect_animal"},
    
    # Инвестиции (1-4)
    "invest_1": {"name": "📊 Первый вклад", "desc": "Сделать инвестицию 1 раз", "target": 1, "reward": 200, "type": "invest"},
    "invest_3": {"name": "📊 Инвестор", "desc": "Сделать инвестицию 3 раза", "target": 3, "reward": 400, "type": "invest"},
    "invest_50000": {"name": "📊 Крупный вклад", "desc": "Инвестировать 50000 💎", "target": 50000, "reward": 500, "type": "invest_amount"},
    "invest_100000": {"name": "📊 Магнат", "desc": "Инвестировать 100000 💎", "target": 100000, "reward": 1000, "type": "invest_amount"},
    
    # Сложные задания (1-5)
    "all_games": {"name": "🎮 Игроман", "desc": "Сыграть во все игры по 1 разу", "target": 1, "reward": 500, "type": "all_games"},
    "complete_3_quests": {"name": "✅ Три задания", "desc": "Выполнить 3 ежедневных задания", "target": 3, "reward": 300, "type": "quest_complete"},
    "complete_5_quests": {"name": "✅ Пять заданий", "desc": "Выполнить 5 ежедневных заданий", "target": 5, "reward": 500, "type": "quest_complete"},
    "complete_all_quests": {"name": "✅ Перфекционист", "desc": "Выполнить ВСЕ ежедневные задания", "target": 1, "reward": 1000, "type": "all_quests"},
    
    # Секретные задания (редкие)
    "secret_win_10_in_row": {"name": "🤫 Победная серия", "desc": "Выиграть 10 раз подряд в любой игре", "target": 10, "reward": 2000, "type": "secret"},
    "secret_million": {"name": "🤫 Миллионер", "desc": "Накопить 1 млн 💎", "target": 1, "type": "secret"},
    "secret_max_level": {"name": "🤫 Бог", "desc": "Достичь 100 уровня", "target": 100, "type": "secret"},
    "secret_fish_all": {"name": "🤫 Ихтиолог", "desc": "Поймать все виды рыб", "target": 1, "type": "secret"},
    "secret_craft_master": {"name": "🤫 Мастер крафта", "desc": "Скрафтить все предметы", "target": 1, "type": "secret"},
}

# ========== РЕЦЕПТЫ КРАФТА ==========
RECIPES = {
    "золотой слиток": {
        "name": "🪙 Золотой слиток",
        "description": "Слиток золота для продажи",
        "ingredients": {"золотая руда": 5, "уголь": 2},
        "result": "золотой слиток",
        "result_count": 1,
        "xp": 50
    },
    "алмаз": {
        "name": "💎 Алмаз",
        "description": "Драгоценный камень",
        "ingredients": {"алмазная руда": 3, "золотой слиток": 1},
        "result": "алмаз",
        "result_count": 1,
        "xp": 100
    },
    "суперудочка": {
        "name": "🎣✨ Супер-удочка",
        "description": "+50% к шансу редкой рыбы",
        "ingredients": {"золотая удочка": 1, "алмаз": 2, "магическая нить": 3},
        "result": "super_rod",
        "result_count": 1,
        "xp": 200
    },
    "эликсир опыта": {
        "name": "🧪 Эликсир опыта",
        "description": "x2 опыт на 1 час",
        "ingredients": {"магическая пыль": 5, "золотой слиток": 2},
        "result": "exp_potion",
        "result_count": 1,
        "xp": 75
    },
    "золотая монета": {
        "name": "🪙 Золотая монета",
        "description": "Можно продать за 500 💎",
        "ingredients": {"золотой слиток": 1},
        "result": "gold_coin",
        "result_count": 5,
        "xp": 30
    },
    "улучшенное семя": {
        "name": "🌱✨ Улучшенное семя",
        "description": "Повышает шанс на редкий урожай",
        "ingredients": {"обычное семя": 3, "магическая пыль": 2},
        "result": "upgraded_seed",
        "result_count": 3,
        "xp": 40
    },
    "корм для животных": {
        "name": "🌾 Корм для животных",
        "description": "Ускоряет рост животных",
        "ingredients": {"пшеница": 5, "кукуруза": 3},
        "result": "animal_feed",
        "result_count": 10,
        "xp": 20
    },
}

# ========== ЖИВОТНЫЕ ДЛЯ ФЕРМЫ ==========
FARM_ANIMALS = {
    "курица": {
        "name": "🐔 Курица",
        "price": 1000,
        "produce": "яйцо",
        "produce_price": 50,
        "produce_time": 3600,  # 1 час
        "feed": "пшеница",
        "feed_amount": 2
    },
    "корова": {
        "name": "🐄 Корова",
        "price": 5000,
        "produce": "молоко",
        "produce_price": 200,
        "produce_time": 7200,  # 2 часа
        "feed": "кукуруза",
        "feed_amount": 3
    },
    "овца": {
        "name": "🐑 Овца",
        "price": 4000,
        "produce": "шерсть",
        "produce_price": 150,
        "produce_time": 5400,  # 1.5 часа
        "feed": "трава",
        "feed_amount": 2
    },
    "свинья": {
        "name": "🐷 Свинья",
        "price": 3000,
        "produce": "мясо",
        "produce_price": 100,
        "produce_time": 7200,
        "feed": "картофель",
        "feed_amount": 3
    },
    "лошадь": {
        "name": "🐴 Лошадь",
        "price": 10000,
        "produce": "навоз",
        "produce_price": 300,
        "produce_time": 10800,  # 3 часа
        "feed": "морковь",
        "feed_amount": 4
    },
}

# ========== ФЕРМЕРСКИЕ УЛУЧШЕНИЯ ==========
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

# ========== СЕЗОННЫЕ СОБЫТИЯ ==========
SEASONAL_EVENTS = {
    "newyear": {"name": "🎄 Новый год", "start": "2026-01-01", "end": "2026-01-15", "multiplier": 2.0},
    "summer": {"name": "☀️ Лето", "start": "2026-06-01", "end": "2026-08-31", "multiplier": 1.5},
    "halloween": {"name": "🎃 Хэллоуин", "start": "2026-10-25", "end": "2026-11-05", "multiplier": 1.5},
}



# ID каналов (ТВОИ)
WELCOME_CHANNEL_ID = 1502637204982206686
LOGS_CHANNEL_ID = 1502637204982206681
LEVEL_CHANNEL_ID = 1502682125730578522
MUTED_ROLE_ID = 1502637204072169540
DEFAULT_ROLE_ID = 1502637204487278744
VC_CREATE_CATEGORY_ID = 1507479787223126036
VC_TRIGGER_CHANNEL_ID = 1507485728739688549
TICKET_CATEGORY_ID = 1507503146744938506
TICKET_CREATE_CHANNEL_ID = 1510991265154601111
STOLOTO_CHANNEL_ID = 1509190455106211840
IDEA_REVIEW_CHANNEL_ID = 1502637204982206679

SUPPORT_ROLE_IDS = [1502637204537737308, 1507479670130741368, 1502637204537737306, 1507478655578673152]
ROLE_GIRL = 1506343912594477247
ROLE_BOY = 1506343782637896011

# Роли за уровни
LEVEL_ROLES = {5: 1502637204487278752, 10: 1502637204487278753, 25: 1502637204504051712, 50: 1502637204504051713, 100: 1502637204504051714}

START_BALANCE = 5000  # УВЕЛИЧЕНО
MIN_EARN = 50   # УВЕЛИЧЕНО
MAX_EARN = 150  # УВЕЛИЧЕНО
BANK_INTEREST = 0.05  # УВЕЛИЧЕНО

GAME_COOLDOWN = {"casino": 300, "dice": 300, "coin": 300, "rps": 300, "blackjack": 300, "rob": 3600, "work": 3600, "rep": 3600}
WIN_CHANCE = {"casino": 0.35, "coin": 0.45, "dice": 0.16, "rps": 0.33, "blackjack": 0.42, "rob": 0.05}

SLOT_EMOJIS = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎"]
DICE_EMOJIS = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]

# ========== НОВЫЙ МАГАЗИН (ДОРОГИЕ ЦЕНЫ) ==========
SHOP_ITEMS = {
    # ====== АЛКОГОЛЬ ======
    "пиво": {"price": 500, "description": "🍺 Банка пива", "type": "consumable", "emoji": "🍺", "effect": "all_ stats"},
    "сигареты": {"price": 800, "description": "🚬 Пачка сигарет", "type": "consumable", "emoji": "🚬", "effect": "energy_boost"},
    "вино": {"price": 2500, "description": "🍷 Бутылка красного вина", "type": "consumable", "emoji": "🍷", "effect": "romance"},
    "шампанское": {"price": 3500, "description": "🍾 Бутылка шампанского", "type": "consumable", "emoji": "🍾", "effect": "celebration"},
    "водка": {"price": 4000, "description": "🍸 Бутылка водки", "type": "consumable", "emoji": "🍸", "effect": "courage"},
    "виски": {"price": 6000, "description": "🥃 Бутылка виски", "type": "consumable", "emoji": "🥃", "effect": "premium"},
    "коньяк": {"price": 8000, "description": "🥃 Бутылка коньяка XO", "type": "consumable", "emoji": "🥃", "effect": "luxury"},
    "ром": {"price": 5500, "description": "🏴‍☠️ Бутылка рома", "type": "consumable", "emoji": "🏴‍☠️", "effect": "pirate"},
    "текила": {"price": 4500, "description": "🌵 Бутылка текилы", "type": "consumable", "emoji": "🌵", "effect": "party"},
    "ликёр": {"price": 3000, "description": "🍹 Бутылка ликёра", "type": "consumable", "emoji": "🍹", "effect": "sweet"},
    
    # ====== УКРАШЕНИЯ НА ПРОФИЛЬ ======
    "золотая звезда": {"price": 15000, "description": "⭐ Золотая звезда в профиль", "type": "award", "emoji": "⭐"},
    "бриллиант": {"price": 25000, "description": "💎 Бриллиант в профиль", "type": "award", "emoji": "💎"},
    "золотая корона": {"price": 50000, "description": "👑 Золотая корона в профиль", "type": "award", "emoji": "👑"},
    "радуга": {"price": 10000, "description": "🌈 Радуга в профиль", "type": "award", "emoji": "🌈"},
    "алмазное сердце": {"price": 30000, "description": "💖 Алмазное сердечко", "type": "award", "emoji": "💖"},
    "платиновая звезда": {"price": 35000, "description": "🌟 Платиновая звезда", "type": "award", "emoji": "🌟"},
    "золотой кубок": {"price": 40000, "description": "🏆 Золотой кубок победителя", "type": "award", "emoji": "🏆"},
    "императорская корона": {"price": 100000, "description": "👑 Императорская корона", "type": "award", "emoji": "👑"},
    "крылья ангела": {"price": 45000, "description": "😇 Крылья ангела в профиль", "type": "award", "emoji": "😇"},
    "крылья демона": {"price": 45000, "description": "😈 Крылья демона в профиль", "type": "award", "emoji": "😈"},
    
    # ====== ЦВЕТА ПРОФИЛЯ ======
    "красный цвет": {"price": 8000, "description": "🔴 Красный цвет профиля", "type": "color", "emoji": "🔴", "color_code": 0xFF0000},
    "синий цвет": {"price": 8000, "description": "🔵 Синий цвет профиля", "type": "color", "emoji": "🔵", "color_code": 0x0000FF},
    "зелёный цвет": {"price": 8000, "description": "🟢 Зелёный цвет профиля", "type": "color", "emoji": "🟢", "color_code": 0x00FF00},
    "золотой цвет": {"price": 15000, "description": "🟡 Золотой цвет профиля", "type": "color", "emoji": "🟡", "color_code": 0xFFD700},
    "фиолетовый цвет": {"price": 10000, "description": "🟣 Фиолетовый цвет профиля", "type": "color", "emoji": "🟣", "color_code": 0x800080},
    "розовый цвет": {"price": 10000, "description": "🌸 Розовый цвет профиля", "type": "color", "emoji": "🌸", "color_code": 0xFF69B4},
    "чёрный цвет": {"price": 12000, "description": "⬛ Чёрный цвет профиля", "type": "color", "emoji": "⬛", "color_code": 0x000000},
    "белый цвет": {"price": 12000, "description": "⬜ Белый цвет профиля", "type": "color", "emoji": "⬜", "color_code": 0xFFFFFF},
    "неоновый зелёный": {"price": 20000, "description": "💚 Неоновый зелёный профиль", "type": "color", "emoji": "💚", "color_code": 0x39FF14},
    "неоновый розовый": {"price": 20000, "description": "💗 Неоновый розовый профиль", "type": "color", "emoji": "💗", "color_code": 0xFF1493},
    
    # ====== БУСТЕРЫ ======
    "бустер опыта x2": {"price": 5000, "description": "✨ x2 опыт на 1 час", "type": "booster", "emoji": "✨", "duration": 3600},
    "бустер опыта x5": {"price": 20000, "description": "🌟 x5 опыт на 1 час", "type": "booster", "emoji": "🌟", "duration": 3600},
    "бустер денег x2": {"price": 5000, "description": "💰 x2 деньги на 1 час", "type": "booster", "emoji": "💰", "duration": 3600},
    "бустер денег x5": {"price": 20000, "description": "💎 x5 деньги на 1 час", "type": "booster", "emoji": "💎", "duration": 3600},
    "бустер удачи": {"price": 10000, "description": "🍀 +20% к шансу выигрыша (1 час)", "type": "booster", "emoji": "🍀", "duration": 3600},
    
    # ====== ПРЕМИУМ РОЛИ ======
    "VIP роль": {"price": 50000, "description": "👑 VIP статус на сервере", "type": "role", "role_id": None},
    "PREMIUM роль": {"price": 100000, "description": "💎 PREMIUM статус", "type": "role", "role_id": None},
    "LEGEND роль": {"price": 250000, "description": "⭐ LEGEND статус", "type": "role", "role_id": None},
    
    # ====== ДОРОГИЕ ПРЕДМЕТЫ ======
    "золотой слиток": {"price": 15000, "description": "🪙 Золотой слиток (можно продать)", "type": "investment", "emoji": "🪙", "sell_price": 12000},
    "алмаз": {"price": 30000, "description": "💎 Алмаз (можно продать)", "type": "investment", "emoji": "💎", "sell_price": 25000},
    "рубин": {"price": 25000, "description": "🔴 Рубин (можно продать)", "type": "investment", "emoji": "🔴", "sell_price": 20000},
    "сапфир": {"price": 25000, "description": "🔵 Сапфир (можно продать)", "type": "investment", "emoji": "🔵", "sell_price": 20000},
    "изумруд": {"price": 25000, "description": "🟢 Изумруд (можно продать)", "type": "investment", "emoji": "🟢", "sell_price": 20000},
    
    # ====== СЕКРЕТНЫЕ ПРЕДМЕТЫ ======
    "лотерейный билет": {"price": 1000, "description": "🎫 Лотерейный билет (шанс выиграть до 100к)", "type": "lottery", "emoji": "🎫"},
    "золотой лотерейный билет": {"price": 10000, "description": "✨ Золотой лотерейный билет (шанс выиграть до 1 млн)", "type": "lottery", "emoji": "✨"},
    "ключ от сейфа": {"price": 50000, "description": "🔑 Ключ от секретного сейфа", "type": "mystery", "emoji": "🔑"},
}

CUSTOM_SHOP_ITEMS = {}

# Семена для фермы (цены увеличены)
SEEDS = {
    "пшеница": {"price": 500, "grow_time": 3600, "rarity_weights": {"обычный": 0.7, "редкий": 0.2, "эпический": 0.08, "легендарный": 0.02}, "base_price": 1000},
    "кукуруза": {"price": 800, "grow_time": 7200, "rarity_weights": {"обычный": 0.6, "редкий": 0.25, "эпический": 0.1, "легендарный": 0.05}, "base_price": 1500},
    "томат": {"price": 1000, "grow_time": 10800, "rarity_weights": {"обычный": 0.5, "редкий": 0.3, "эпический": 0.15, "легендарный": 0.05}, "base_price": 2000},
    "картофель": {"price": 600, "grow_time": 5400, "rarity_weights": {"обычный": 0.65, "редкий": 0.25, "эпический": 0.08, "легендарный": 0.02}, "base_price": 1200},
    "морковь": {"price": 700, "grow_time": 7200, "rarity_weights": {"обычный": 0.6, "редкий": 0.3, "эпический": 0.08, "легендарный": 0.02}, "base_price": 1300},
    "мефедрон": {"price": 5000, "grow_time": 43200, "rarity_weights": {"обычный": 0.3, "редкий": 0.3, "эпический": 0.25, "легендарный": 0.15}, "base_price": 10000},
    "роза": {"price": 1500, "grow_time": 14400, "rarity_weights": {"обычный": 0.5, "редкий": 0.3, "эпический": 0.15, "легендарный": 0.05}, "base_price": 3000},
    "кактус": {"price": 1200, "grow_time": 18000, "rarity_weights": {"обычный": 0.55, "редкий": 0.25, "эпический": 0.15, "легендарный": 0.05}, "base_price": 2500},
    "подсолнух": {"price": 900, "grow_time": 9000, "rarity_weights": {"обычный": 0.6, "редкий": 0.3, "эпический": 0.08, "легендарный": 0.02}, "base_price": 1800},
    "тыква": {"price": 2000, "grow_time": 28800, "rarity_weights": {"обычный": 0.5, "редкий": 0.25, "эпический": 0.2, "легендарный": 0.05}, "base_price": 4000},
    "арбуз": {"price": 3000, "grow_time": 36000, "rarity_weights": {"обычный": 0.4, "редкий": 0.3, "эпический": 0.2, "легендарный": 0.1}, "base_price": 6000},
    "ананас": {"price": 4000, "grow_time": 50400, "rarity_weights": {"обычный": 0.35, "редкий": 0.3, "эпический": 0.25, "легендарный": 0.1}, "base_price": 8000},
}

RARITY_MULTIPLIERS = {"обычный": 1.0, "редкий": 2.0, "эпический": 4.0, "легендарный": 8.0, "мифический": 16.0}

# Карты для покера
CARD_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
CARD_SUITS = ['♠️', '♥️', '♣️', '♦️']
FULL_DECK = [f"{r}{s}" for r in CARD_RANKS for s in CARD_SUITS]

STOLOTO_TIME = "14:00"
STOLOTO_TICKET_PRICE = 500  # УВЕЛИЧЕНО

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
vc_sessions = {}
user_message_timestamps = defaultdict(list)
user_warnings = defaultdict(list)
user_conversations = defaultdict(list)
spam_messages_to_delete = defaultdict(list)
active_boosters = defaultdict(dict)
profile_colors = defaultdict(int)
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

# Настройка Open-Meteo
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# WMO коды погоды
WEATHER_CODES = {
    0: ("☀️ Ясно", 0x87CEEB), 1: ("🌤️ В основном ясно", 0x89CFF0), 2: ("⛅ Переменная облачность", 0xADD8E6),
    3: ("☁️ Пасмурно", 0x778899), 45: ("🌫️ Туман", 0xB0C4DE), 48: ("🌫️ Туман с изморозью", 0xB0C4DE),
    51: ("🌧️ Морось слабая", 0x4682B4), 53: ("🌧️ Морось умеренная", 0x4682B4), 55: ("🌧️ Морось сильная", 0x4682B4),
    56: ("❄️ Ледяная морось", 0x87CEEB), 57: ("❄️ Ледяная морось сильная", 0x87CEEB),
    61: ("🌧️ Дождь слабый", 0x4169E1), 63: ("🌧️ Дождь умеренный", 0x4169E1), 65: ("🌧️ Дождь сильный", 0x4169E1),
    66: ("❄️ Ледяной дождь", 0x87CEEB), 67: ("❄️ Ледяной дождь сильный", 0x87CEEB),
    71: ("❄️ Снег слабый", 0xFFFFFF), 73: ("❄️ Снег умеренный", 0xFFFFFF), 75: ("❄️ Снег сильный", 0xFFFFFF),
    77: ("❄️ Снежные зёрна", 0xFFFFFF), 80: ("🌧️ Ливень слабый", 0x4169E1), 81: ("🌧️ Ливень умеренный", 0x4169E1),
    82: ("🌧️ Ливень сильный", 0x4169E1), 85: ("❄️ Снегопад слабый", 0xFFFFFF), 86: ("❄️ Снегопад сильный", 0xFFFFFF),
    95: ("⛈️ Гроза", 0x8B4513), 96: ("⛈️ Гроза с градом", 0x8B4513), 99: ("⛈️ Гроза с градом сильная", 0x8B4513),
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='j.', intents=intents)
bot.remove_command('help')

# ========== БАЗА ДАННЫХ ==========
async def init_db():
    async with aiosqlite.connect("justice.db") as db:
        # Основная таблица пользователей (ДОБАВЛЕНЫ НОВЫЕ ПОЛЯ)
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER, guild_id INTEGER,
            xp INTEGER DEFAULT 0, level INTEGER DEFAULT 0,
            balance INTEGER DEFAULT 5000, bank INTEGER DEFAULT 0,
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
            profile_color INTEGER DEFAULT 0,
            -- НОВЫЕ ПОЛЯ --
            voice_total_seconds INTEGER DEFAULT 0,
            voice_join_time TEXT,
            total_invites INTEGER DEFAULT 0,
            total_casino_wins INTEGER DEFAULT 0,
            total_blackjack_wins INTEGER DEFAULT 0,
            total_poker_wins INTEGER DEFAULT 0,
            total_ttt_wins INTEGER DEFAULT 0,
            total_fish_caught INTEGER DEFAULT 0,
            total_legendary_fish INTEGER DEFAULT 0,
            total_mythic_fish INTEGER DEFAULT 0,
            total_harvests INTEGER DEFAULT 0,
            total_plants INTEGER DEFAULT 0,
            total_work INTEGER DEFAULT 0,
            total_rob_success INTEGER DEFAULT 0,
            total_daily_streak INTEGER DEFAULT 0,
            total_shop_buys INTEGER DEFAULT 0,
            total_shop_spent INTEGER DEFAULT 0,
            total_donated INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )''')
        
        # Таблица предупреждений
        await db.execute('''CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, guild_id INTEGER,
            moderator_id INTEGER, reason TEXT, expires_at TEXT
        )''')
        
        # Таблица идей
        await db.execute('''CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, guild_id INTEGER,
            suggestion TEXT, status TEXT DEFAULT 'pending',
            verdict TEXT, date TEXT
        )''')
        
        # Таблица приватных войсов
        await db.execute('''CREATE TABLE IF NOT EXISTS private_vc (
            channel_id INTEGER PRIMARY KEY,
            owner_id INTEGER, guild_id INTEGER,
            channel_name TEXT, user_limit INTEGER DEFAULT 0,
            is_locked INTEGER DEFAULT 0,
            banned_users TEXT DEFAULT '[]',
            created_at TEXT
        )''')
        
        # Таблица розыгрышей
        await db.execute('''CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER, message_id INTEGER,
            prize TEXT, winners INTEGER, end_time TEXT,
            entries TEXT, ended INTEGER DEFAULT 0
        )''')
        
        # Таблица Столото
        await db.execute('''CREATE TABLE IF NOT EXISTS stoloto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, winner_id INTEGER, prize INTEGER
        )''')
        
        # Таблица кастомного магазина
        await db.execute('''CREATE TABLE IF NOT EXISTS custom_shop (
            name TEXT PRIMARY KEY,
            price INTEGER,
            description TEXT,
            role_id INTEGER
        )''')
        
        # Таблица настроек гильдии
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
        
        # ========== НОВЫЕ ТАБЛИЦЫ ==========
        
        # Достижения
        await db.execute('''CREATE TABLE IF NOT EXISTS achievements (
            user_id INTEGER, guild_id INTEGER,
            achievement_id TEXT,
            achieved_at TEXT,
            PRIMARY KEY (user_id, guild_id, achievement_id)
        )''')
        
        # Ежедневные задания
        await db.execute('''CREATE TABLE IF NOT EXISTS daily_quests (
            user_id INTEGER, guild_id INTEGER,
            quest_date TEXT,
            quest1_id TEXT, quest1_progress INTEGER, quest1_completed INTEGER,
            quest2_id TEXT, quest2_progress INTEGER, quest2_completed INTEGER,
            quest3_id TEXT, quest3_progress INTEGER, quest3_completed INTEGER,
            PRIMARY KEY (user_id, guild_id, quest_date)
        )''')
        
        # Инвестиции
        await db.execute('''CREATE TABLE IF NOT EXISTS investments (
            user_id INTEGER, guild_id INTEGER,
            invest_type TEXT,
            amount INTEGER,
            invest_date TEXT,
            days INTEGER,
            interest_rate REAL,
            claimed INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )''')
        
        # Фермерские улучшения
        await db.execute('''CREATE TABLE IF NOT EXISTS farm_upgrades (
            user_id INTEGER, guild_id INTEGER,
            upgrade_type TEXT,
            level INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id, upgrade_type)
        )''')
        
        # Животные на ферме
        await db.execute('''CREATE TABLE IF NOT EXISTS farm_animals (
            user_id INTEGER, guild_id INTEGER,
            animal_type TEXT,
            count INTEGER DEFAULT 0,
            last_produce TEXT,
            last_fed TEXT,
            PRIMARY KEY (user_id, guild_id, animal_type)
        )''')
        
        # Рецепты (крафт)
        await db.execute('''CREATE TABLE IF NOT EXISTS recipes (
            user_id INTEGER, guild_id INTEGER,
            recipe_id TEXT,
            learned INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id, recipe_id)
        )''')
        
        # Приглашения
        await db.execute('''CREATE TABLE IF NOT EXISTS invites (
            inviter_id INTEGER, invited_id INTEGER,
            guild_id INTEGER, invite_date TEXT,
            PRIMARY KEY (invited_id, guild_id)
        )''')
        
        # Еженедельная статистика
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
    
    # Загрузка кастомного магазина
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
    
    # Проверка на двойной опыт по выходным
    boost_mult = 1
    if datetime.now().weekday() in [5, 6]:  # Суббота или воскресенье
        boost_mult = 2
    
    # Проверка на бустеры
    if user_id in active_boosters and "exp" in active_boosters[user_id]:
        if time.time() < active_boosters[user_id]["exp"]["end"]:
            boost_mult *= active_boosters[user_id]["exp"]["mult"]
    
    amount = int(amount * boost_mult)
    new_xp = user[2] + amount
    new_level = int((new_xp / 200) ** 0.55)
    level_up = new_level > user[3]
    
    await update_user(user_id, guild_id, xp=new_xp, level=new_level,
                     total_messages=user[9] + 1, today_messages=user[21] + 1,
                     week_messages=user[22] + 1, month_messages=user[23] + 1,
                     last_message_time=datetime.now().isoformat())
    
    # Проверка достижений за уровень
    await check_achievement(user_id, guild_id, "level", new_level)
    
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

# ========== ФУНКЦИЯ ПРОВЕРКИ ДОСТИЖЕНИЙ ==========
async def check_achievement(user_id, guild_id, ach_type, value):
    """Проверка и выдача достижений"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT achievement_id FROM achievements WHERE user_id=? AND guild_id=?', (user_id, guild_id))
        earned = set(row[0] for row in await cur.fetchall())
    
    new_achievements = []
    
    for ach_id, ach_data in ACHIEVEMENTS.items():
        if ach_id in earned:
            continue
        
        ach_type_check = ach_id.split("_")[0]
        
        if ach_type == "messages" and ach_type_check == "msg":
            target = int(ach_id.split("_")[1])
            if value >= target:
                new_achievements.append(ach_id)
        
        elif ach_type == "level" and ach_type_check == "lvl":
            target = int(ach_id.split("_")[1])
            if value >= target:
                new_achievements.append(ach_id)
        
        elif ach_type == "balance" and ach_type_check == "bal":
            target = int(ach_id.split("_")[1])
            if value >= target:
                new_achievements.append(ach_id)
        
        elif ach_type == "reputation" and ach_type_check == "rep":
            target = int(ach_id.split("_")[1])
            if value >= target:
                new_achievements.append(ach_id)
    
    for ach_id in new_achievements:
        ach_data = ACHIEVEMENTS[ach_id]
        await add_balance(user_id, guild_id, ach_data["reward"])
        
        async with aiosqlite.connect("justice.db") as db:
            await db.execute('INSERT INTO achievements (user_id, guild_id, achievement_id, achieved_at) VALUES (?,?,?,?)',
                            (user_id, guild_id, ach_id, datetime.now().isoformat()))
            await db.commit()
        
        # Отправка уведомления
        user = bot.get_user(user_id)
        if user:
            await user.send(f"🏆 **ДОСТИЖЕНИЕ ПОЛУЧЕНО!**\n📛 {ach_data['name']}\n📝 {ach_data['desc']}\n💰 Награда: {ach_data['reward']} 💎")
        
        guild = bot.get_guild(guild_id)
        if guild:
            channel = guild.get_channel(LEVEL_CHANNEL_ID)
            if channel:
                await channel.send(f"🏆 {user.mention if user else 'Игрок'} получил достижение **{ach_data['name']}** и {ach_data['reward']} 💎!")
# ========== ПОГОДА (Open-Meteo) ==========
async def get_weather_data(lat, lon, forecast_days=7):
    params = {
        "latitude": lat, "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day", "precipitation", "surface_pressure", "cloud_cover", "weather_code", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation_probability", "weather_code", "wind_speed_10m"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min", "precipitation_sum", "precipitation_probability_max", "sunrise", "sunset", "uv_index_max"],
        "timezone": "auto", "forecast_days": forecast_days
    }
    try:
        responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
        return responses[0]
    except Exception as e:
        return None

@bot.command()
async def weather(ctx, *, city: str = None):
    """🌤️ Погода (сегодня, завтра, 3 дня, 7 дней, почасовой прогноз)"""
    if not city:
        await ctx.send("🌤️ **Погода**\n`j.weather <город>` - показать погоду\nПример: `j.weather Москва`\n\n"
                      "**Дополнительные команды:**\n"
                      "`j.weather_today <город>` - только сегодня\n"
                      "`j.weather_3days <город>` - прогноз на 3 дня\n"
                      "`j.weather_7days <город>` - прогноз на 7 дней\n"
                      "`j.weather_hourly <город>` - почасовой прогноз")
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
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                city_name = data[0].get('display_name', city).split(',')[0]
        except Exception as e:
            await ctx.send(f"❌ Ошибка поиска: {str(e)[:100]}")
            return
    
    response = await get_weather_data(lat, lon, 7)
    if not response:
        await ctx.send("❌ Ошибка получения данных о погоде")
        return
    
    current = response.Current()
    current_temp = current.Variables(0).Value()
    current_humidity = current.Variables(1).Value()
    current_feels = current.Variables(2).Value()
    is_day = current.Variables(3).Value()
    current_precip = current.Variables(4).Value()
    current_pressure = current.Variables(5).Value() / 1.333
    current_clouds = current.Variables(6).Value()
    weather_code = int(current.Variables(7).Value())
    wind_speed = current.Variables(8).Value()
    wind_dir = current.Variables(9).Value()
    wind_gust = current.Variables(10).Value()
    
    wind_directions = ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
    wind_dir_text = wind_directions[int((wind_dir + 22.5) // 45) % 8] if wind_dir else "?"
    weather_text, weather_color = WEATHER_CODES.get(weather_code, ("🌡️ Неизвестно", 0x808080))
    
    daily = response.Daily()
    daily_times = daily.Time()
    daily_weather = daily.Variables(0).ValuesAsNumpy()
    daily_temp_max = daily.Variables(1).ValuesAsNumpy()
    daily_temp_min = daily.Variables(2).ValuesAsNumpy()
    daily_precip = daily.Variables(5).ValuesAsNumpy()
    daily_precip_prob = daily.Variables(6).ValuesAsNumpy()
    
    embed = discord.Embed(title=f"🌤️ ПОГОДА | {city_name}", description=f"*{weather_text}*", color=weather_color, timestamp=datetime.now())
    embed.add_field(name="🌡️ Сейчас", value=f"**{current_temp:.1f}°C**\nОщущается: {current_feels:.1f}°C", inline=True)
    embed.add_field(name="💨 Ветер", value=f"{wind_speed:.1f} м/с, {wind_dir_text}\nПорывы: {wind_gust:.1f} м/с", inline=True)
    embed.add_field(name="💧 Влажность", value=f"{current_humidity:.0f}%", inline=True)
    embed.add_field(name="☁️ Облачность", value=f"{current_clouds:.0f}%", inline=True)
    embed.add_field(name="📊 Давление", value=f"{current_pressure:.0f} мм рт. ст.", inline=True)
    embed.add_field(name="🌧️ Осадки", value=f"{current_precip:.1f} мм", inline=True)
    
    forecast_text = ""
    for i in range(min(7, len(daily_times))):
        date = datetime.fromtimestamp(daily_times[i]).strftime("%d.%m")
        code = int(daily_weather[i])
        weather_icon, _ = WEATHER_CODES.get(code, ("🌡️", 0))
        temp_max, temp_min = daily_temp_max[i], daily_temp_min[i]
        precip, prob = daily_precip[i], daily_precip_prob[i]
        forecast_text += f"**{date}** {weather_icon} {temp_min:.0f}°…{temp_max:.0f}° | 💧{precip:.1f}мм | ☔{prob:.0f}%\n"
    embed.add_field(name="📅 Прогноз на 7 дней", value=forecast_text[:1024], inline=False)
    embed.set_footer(text=f"ID: {response.Latitude():.2f}°N {response.Longitude():.2f}°E | Open-Meteo")
    await ctx.send(embed=embed)
    await log_action(ctx.guild.id, "🌤️ ПОГОДА", f"{ctx.author.mention} запросил погоду для **{city_name}**")

@bot.command()
async def weather_today(ctx, *, city: str = None):
    """🌤️ Погода на сегодня"""
    if not city:
        await ctx.send("❌ Укажите город: `j.weather_today Москва`")
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
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                city_name = data[0].get('display_name', city).split(',')[0]
        except: return await ctx.send("❌ Ошибка поиска")
    response = await get_weather_data(lat, lon, 1)
    if not response: return await ctx.send("❌ Ошибка данных")
    daily = response.Daily()
    code = int(daily.Variables(0).ValuesAsNumpy()[0])
    weather_icon, weather_color = WEATHER_CODES.get(code, ("🌡️", 0x808080))
    temp_max = daily.Variables(1).ValuesAsNumpy()[0]
    temp_min = daily.Variables(2).ValuesAsNumpy()[0]
    precip = daily.Variables(5).ValuesAsNumpy()[0]
    prob = daily.Variables(6).ValuesAsNumpy()[0]
    embed = discord.Embed(title=f"🌤️ ПОГОДА НА СЕГОДНЯ | {city_name}", description=f"{weather_icon} {weather_icon[2:]}", color=weather_color)
    embed.add_field(name="🌡️ Температура", value=f"мин: {temp_min:.0f}°C\nмакс: {temp_max:.0f}°C", inline=True)
    embed.add_field(name="🌧️ Осадки", value=f"{precip:.1f} мм\nВероятность: {prob:.0f}%", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def weather_3days(ctx, *, city: str = None):
    """🌤️ Прогноз на 3 дня"""
    if not city:
        await ctx.send("❌ Укажите город: `j.weather_3days Москва`")
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
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                city_name = data[0].get('display_name', city).split(',')[0]
        except: return await ctx.send("❌ Ошибка поиска")
    response = await get_weather_data(lat, lon, 3)
    if not response: return await ctx.send("❌ Ошибка данных")
    daily = response.Daily()
    times = daily.Time()
    weather_codes = daily.Variables(0).ValuesAsNumpy()
    temp_max = daily.Variables(1).ValuesAsNumpy()
    temp_min = daily.Variables(2).ValuesAsNumpy()
    precip = daily.Variables(5).ValuesAsNumpy()
    embed = discord.Embed(title=f"🌤️ ПРОГНОЗ НА 3 ДНЯ | {city_name}", color=discord.Color.blue())
    for i in range(min(3, len(times))):
        date = datetime.fromtimestamp(times[i]).strftime("%d.%m")
        code = int(weather_codes[i])
        weather_icon, _ = WEATHER_CODES.get(code, ("🌡️", 0))
        embed.add_field(name=f"**{date}** {weather_icon}", value=f"{temp_min[i]:.0f}°…{temp_max[i]:.0f}° | 💧{precip[i]:.1f}мм", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def weather_7days(ctx, *, city: str = None):
    """🌤️ Прогноз на 7 дней"""
    if not city:
        await ctx.send("❌ Укажите город: `j.weather_7days Москва`")
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
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                city_name = data[0].get('display_name', city).split(',')[0]
        except: return await ctx.send("❌ Ошибка поиска")
    response = await get_weather_data(lat, lon, 7)
    if not response: return await ctx.send("❌ Ошибка данных")
    daily = response.Daily()
    times = daily.Time()
    weather_codes = daily.Variables(0).ValuesAsNumpy()
    temp_max = daily.Variables(1).ValuesAsNumpy()
    temp_min = daily.Variables(2).ValuesAsNumpy()
    precip = daily.Variables(5).ValuesAsNumpy()
    embed = discord.Embed(title=f"🌤️ ПРОГНОЗ НА 7 ДНЕЙ | {city_name}", color=discord.Color.blue())
    forecast_text = ""
    for i in range(len(times)):
        date = datetime.fromtimestamp(times[i]).strftime("%d.%m")
        code = int(weather_codes[i])
        weather_icon, _ = WEATHER_CODES.get(code, ("🌡️", 0))
        forecast_text += f"**{date}** {weather_icon} {temp_min[i]:.0f}°…{temp_max[i]:.0f}° | 💧{precip[i]:.1f}мм\n"
    embed.description = forecast_text
    await ctx.send(embed=embed)

@bot.command()
async def weather_hourly(ctx, *, city: str = None):
    """🌤️ Почасовой прогноз на сегодня"""
    if not city:
        await ctx.send("❌ Укажите город: `j.weather_hourly Москва`")
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
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                city_name = data[0].get('display_name', city).split(',')[0]
        except: return await ctx.send("❌ Ошибка поиска")
    
    params = {"latitude": lat, "longitude": lon, "hourly": ["temperature_2m", "apparent_temperature", "precipitation_probability", "weather_code"], "timezone": "auto", "forecast_days": 1}
    try:
        responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
        response = responses[0]
        hourly = response.Hourly()
        times = hourly.Time()
        temps = hourly.Variables(0).ValuesAsNumpy()
        feels = hourly.Variables(1).ValuesAsNumpy()
        probs = hourly.Variables(2).ValuesAsNumpy()
        codes = hourly.Variables(3).ValuesAsNumpy()
        
        embed = discord.Embed(title=f"🌤️ ПОЧАСОВОЙ ПРОГНОЗ | {city_name}", color=discord.Color.blue())
        text = ""
        now = datetime.now()
        for i in range(24):
            if i >= len(times): break
            hour = datetime.fromtimestamp(times[i]).hour
            code = int(codes[i])
            weather_icon, _ = WEATHER_CODES.get(code, ("🌡️", 0))
            temp, feel, prob = temps[i], feels[i], probs[i]
            marker = "🔴" if hour == now.hour else ""
            text += f"{marker} **{hour}:00** {weather_icon} {temp:.0f}°C (ощущ.{feel:.0f}°) ☔{prob:.0f}%\n"
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
    if any(x in lower_msg for x in ["дата", "сегодня", "число"]): return f"📅 Сегодня {datetime.now().strftime('%d.%m.%Y')}"
    if any(x in lower_msg for x in ["время", "который час"]): return f"🕐 Сейчас {datetime.now().strftime('%H:%M:%S')}"
    if "погода" in lower_msg: return "🌤️ Используй `j.weather <город>`"
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
    except: return "⏳ Попробуй ещё раз."

@bot.command()
async def ai(ctx, *, question: str = None):
    if not question: return await ctx.send("❌ Напиши вопрос: `j.ai Как дела?`")
    if len(question) > 500: return await ctx.send("❌ Вопрос слишком длинный!")
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
        if "discord.gg/" in content or "discord.com/invite/" in content or "dsc.gg/" in content:
            spam_messages_to_delete[user_id].append(message.id)
            return True, "реклама Discord сервера"
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
    embed.add_field(name="📍 Канал", value=channel.mention, inline=True)
    await send_log(user.guild.id, embed)
    if warning_count >= ANTISPAM_MAX_WARNINGS:
        alert = discord.Embed(title="🚨 ПРЕВЫШЕН ЛИМИТ ПРЕДУПРЕЖДЕНИЙ", description=f"Пользователь {user.mention} получил {warning_count} предупреждений за 24 часа.", color=discord.Color.red())
        await send_log(user.guild.id, alert)
    return warning_count

async def send_warning_dm(user, reason, wc, channel):
    try:
        await user.send(f"⚠️ **Автомодерация**\nВаши сообщения в {channel.mention} были удалены.\n📝 Причина: {reason}\n⚠️ Предупреждений: {wc}/{ANTISPAM_MAX_WARNINGS}")
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

@bot.command()
async def mywarns(ctx):
    user_id = ctx.author.id
    now = time.time()
    user_warnings[user_id] = [w for w in user_warnings[user_id] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    if not user_warnings[user_id]: return await ctx.send(f"✅ {ctx.author.mention}, у вас нет предупреждений")
    embed = discord.Embed(title=f"⚠️ Ваши предупреждения", color=discord.Color.orange())
    for i, w in enumerate(user_warnings[user_id], 1):
        left = ANTISPAM_WARNING_EXPIRE_HOURS * 3600 - (now - w["time"])
        embed.add_field(name=f"#{i}", value=f"📝 {w['reason']}\n⏰ {int(left//3600)}ч {int((left%3600)//60)}мин", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def warns(ctx, member: discord.Member = None):
    target = member or ctx.author
    uid = target.id
    now = time.time()
    if uid in user_warnings: user_warnings[uid] = [w for w in user_warnings[uid] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    if not user_warnings.get(uid, []): return await ctx.send(f"✅ У {target.mention} нет предупреждений")
    embed = discord.Embed(title=f"⚠️ Предупреждения {target.display_name}", color=discord.Color.orange())
    for i, w in enumerate(user_warnings[uid], 1):
        left = ANTISPAM_WARNING_EXPIRE_HOURS * 3600 - (now - w["time"])
        embed.add_field(name=f"#{i}", value=f"📝 {w['reason']}\n👮 {w.get('moderator','Automod')}\n⏰ {int(left//3600)}ч {int((left%3600)//60)}мин", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unwarn(ctx, member: discord.Member, num: int = None):
    uid = member.id
    now = time.time()
    if uid in user_warnings: user_warnings[uid] = [w for w in user_warnings[uid] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    if not user_warnings.get(uid, []): return await ctx.send(f"✅ У {member.mention} нет предупреждений")
    if not num or num<1 or num>len(user_warnings[uid]): return await ctx.send(f"❌ Номер от 1 до {len(user_warnings[uid])}")
    removed = user_warnings[uid].pop(num-1)
    await ctx.send(f"✅ Снят варн #{num} у {member.mention} (причина: {removed['reason']})")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def awarn(ctx, member: discord.Member, *, reason: str = "Не указана"):
    uid = member.id
    now = time.time()
    if uid in user_warnings: user_warnings[uid] = [w for w in user_warnings[uid] if now - w["time"] < ANTISPAM_WARNING_EXPIRE_HOURS * 3600]
    else: user_warnings[uid] = []
    user_warnings[uid].append({"reason": reason, "time": now, "moderator": ctx.author.name})
    await ctx.send(f"⚠️ {member.mention} выдано предупреждение: {reason} (всего: {len(user_warnings[uid])})")

# ========== ОГОНЁК ==========
async def update_voice_streak(member):
    today = datetime.now().date()
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT voice_streak, last_voice_join FROM users WHERE user_id=? AND guild_id=?', (member.id, member.guild.id))
        row = await cur.fetchone()
        if not row: streak = 1
        else:
            current, last = row[0] or 0, row[1]
            if last:
                last_date = datetime.fromisoformat(last).date() if isinstance(last, str) else last
                if last_date == today: return current
                elif last_date == today - timedelta(days=1): streak = current + 1
                else: streak = 1
            else: streak = 1
        await db.execute('UPDATE users SET voice_streak=?, last_voice_join=? WHERE user_id=? AND guild_id=?', (streak, datetime.now().isoformat(), member.id, member.guild.id))
        await db.commit()
        await add_balance(member.id, member.guild.id, streak * 50)
        return streak

# ========== ФЕРМА ==========
@bot.command()
async def farm(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    pots = data[28] if len(data)>28 else 0
    crops = json.loads(data[29] if len(data)>29 else "[]")
    embed = discord.Embed(title="🌾 ФЕРМА", color=discord.Color.green())
    embed.add_field(name="🏺 Горшки", value=f"{pots}/10", inline=True)
    embed.add_field(name="🌱 Посажено", value=f"{len(crops)} культур", inline=True)
    if crops:
        text = ""
        for i, c in enumerate(crops[:10]):
            if c:
                planted = datetime.fromisoformat(c["planted_at"])
                left = (planted + timedelta(seconds=SEEDS[c["seed"]]["grow_time"]) - datetime.now())
                if left.total_seconds() > 0: status = f"🌱 {int(left.total_seconds()//3600)}ч {int((left.total_seconds()%3600)//60)}мин"
                else: status = "✅ ГОТОВО!"
                text += f"**{i+1}.** {c['seed'].capitalize()} ({c['rarity']}) - {status}\n"
        embed.add_field(name="📋 Посевы", value=text[:1024], inline=False)
    embed.set_footer(text="j.buy_pot | j.buy_seed | j.plant | j.harvest")
    await ctx.send(embed=embed)

@bot.command()
async def buy_pot(ctx):
    data = await get_user(ctx.author.id, ctx.guild.id)
    pots = data[28] if len(data)>28 else 0
    if pots >= 10: return await ctx.send("❌ Максимум 10 горшков!")
    price = 2000 * (pots + 1)
    if data[4] < price: return await ctx.send(f"❌ Нужно {price} 💎")
    await add_balance(ctx.author.id, ctx.guild.id, -price)
    await update_user(ctx.author.id, ctx.guild.id, pots=pots+1)
    await ctx.send(f"✅ Куплен горшок №{pots+1} за {price} 💎")

@bot.command()
async def buy_seed(ctx, seed: str = None):
    if not seed or seed.lower() not in SEEDS: return await ctx.send(f"🌱 Семена: {', '.join(SEEDS.keys())}")
    seed = seed.lower()
    price = SEEDS[seed]["price"]
    if (await get_user(ctx.author.id, ctx.guild.id))[4] < price: return await ctx.send(f"❌ Нужно {price} 💎")
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
    pots = data[28] if len(data)>28 else 0
    if pot<1 or pot>pots: return await ctx.send(f"❌ Нет горшка №{pot}")
    crops = json.loads(data[29] if len(data)>29 else "[]")
    if pot-1 < len(crops) and crops[pot-1] and crops[pot-1].get("planted_at"): return await ctx.send(f"❌ Горшок №{pot} занят!")
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

@bot.command()
async def harvest(ctx, pot: int = None):
    if not pot: return await ctx.send("❌ j.harvest <номер>")
    data = await get_user(ctx.author.id, ctx.guild.id)
    if pot<1 or pot>(data[28] if len(data)>28 else 0): return await ctx.send(f"❌ Нет горшка №{pot}")
    crops = json.loads(data[29] if len(data)>29 else "[]")
    if pot-1 >= len(crops) or not crops[pot-1]: return await ctx.send(f"❌ Горшок №{pot} пуст")
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

# ========== ПРОФИЛЬ ==========
@bot.command()
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = await get_user(target.id, ctx.guild.id)
    level, xp, bal = data[3], data[2], data[4]
    bank = data[5] if len(data)>5 else 0
    rep = data[6] if len(data)>6 else 0
    total_msgs = data[9] if len(data)>9 else 0
    today_msgs = data[21] if len(data)>21 else 0
    voice_streak = data[26] if len(data)>26 else 0
    bio = data[17] if len(data)>17 and data[17] else "Нет"
    gender = data[20] if len(data)>20 else ""
    awards = json.loads(data[18] if len(data)>18 else "[]")
    profile_color = data[31] if len(data)>31 else 0x5865F2
    xp_for_next = 200 * ((level+1)**2)
    xp_for_current = 200 * (level**2)
    percent = min(100, int((xp - xp_for_current) / (xp_for_next - xp_for_current) * 100)) if xp_for_next > xp_for_current else 0
    bar = "█" * (percent//5) + "░" * (20 - (percent//5))
    gender_text = "👨 Мужчина" if gender=="male" else "👩 Женщина" if gender=="female" else "❓ Не указан"
    embed = discord.Embed(title=f"📊 ПРОФИЛЬ | {target.display_name}", color=profile_color)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="🎚️ УРОВЕНЬ", value=f"**{level}** ур\n`{bar}` {percent}%\n✨ {xp} XP", inline=False)
    embed.add_field(name="💰 ЭКОНОМИКА", value=f"💎 {bal}\n🏦 {bank}\n⭐ {rep}", inline=False)
    embed.add_field(name="📆 АКТИВНОСТЬ", value=f"📅 Сегодня: {today_msgs}\n💬 Всего: {total_msgs}\n🔥 Огонёк: {voice_streak} дн", inline=False)
    embed.add_field(name="⚧ ПОЛ", value=gender_text, inline=True)
    if awards: embed.add_field(name="🏆 НАГРАДЫ", value=" ".join([f"«{a}»" for a in awards[:5]]), inline=False)
    embed.add_field(name="📝 БИО", value=bio[:500], inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def bio(ctx, *, text: str = None):
    if not text: return await ctx.send("❌ j.bio <текст>")
    if len(text) > 500: return await ctx.send("❌ Максимум 500 символов")
    await update_user(ctx.author.id, ctx.guild.id, bio=text)
    await ctx.send("✅ Био обновлено")

# ========== МАГАЗИН И ИНВЕНТАРЬ ==========
@bot.command()
async def shop(ctx, category: str = None):
    embed = discord.Embed(title="🛍️ МАГАЗИН", color=discord.Color.gold())
    if not category or category == "алкоголь":
        text = ""
        for n, d in SHOP_ITEMS.items():
            if d.get("type") == "consumable":
                text += f"**{n}** - {d['price']} 💎 | {d['description']}\n"
        embed.add_field(name="🍺 АЛКОГОЛЬ И СИГАРЕТЫ", value=text or "Нет", inline=False)
    if not category or category == "украшения":
        text = ""
        for n, d in SHOP_ITEMS.items():
            if d.get("type") == "award":
                text += f"**{n}** - {d['price']} 💎 | {d['description']}\n"
        embed.add_field(name="✨ УКРАШЕНИЯ ПРОФИЛЯ", value=text or "Нет", inline=False)
    if not category or category == "цвета":
        text = ""
        for n, d in SHOP_ITEMS.items():
            if d.get("type") == "color":
                text += f"**{n}** - {d['price']} 💎 | {d['description']}\n"
        embed.add_field(name="🎨 ЦВЕТА ПРОФИЛЯ", value=text or "Нет", inline=False)
    if not category or category == "бустеры":
        text = ""
        for n, d in SHOP_ITEMS.items():
            if d.get("type") == "booster":
                text += f"**{n}** - {d['price']} 💎 | {d['description']}\n"
        embed.add_field(name="⚡ БУСТЕРЫ", value=text or "Нет", inline=False)
    if not category or category == "роли":
        text = ""
        for n, d in SHOP_ITEMS.items():
            if d.get("type") == "role":
                text += f"**{n}** - {d['price']} 💎 | {d['description']}\n"
        embed.add_field(name="👑 ПРЕМИУМ РОЛИ", value=text or "Нет", inline=False)
    if not category or category == "инвестиции":
        text = ""
        for n, d in SHOP_ITEMS.items():
            if d.get("type") == "investment":
                text += f"**{n}** - {d['price']} 💎 | {d['description']}\n"
        embed.add_field(name="💎 ИНВЕСТИЦИИ", value=text or "Нет", inline=False)
    if not category or category == "лотерея":
        text = ""
        for n, d in SHOP_ITEMS.items():
            if d.get("type") == "lottery":
                text += f"**{n}** - {d['price']} 💎 | {d['description']}\n"
        embed.add_field(name="🎫 ЛОТЕРЕЯ", value=text or "Нет", inline=False)
    if CUSTOM_SHOP_ITEMS:
        text = ""
        for n, d in CUSTOM_SHOP_ITEMS.items():
            text += f"**{n}** - {d['price']} 💎 | {d['description']}\n"
        embed.add_field(name="📦 КАСТОМНЫЕ", value=text, inline=False)
    embed.set_footer(text="j.buy <товар> | j.shop <категория> | категории: алкоголь, украшения, цвета, бустеры, роли, инвестиции, лотерея")
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, *, item: str = None):
    if not item: return await ctx.send("❌ j.buy <товар>")
    item = item.lower()
    if item not in SHOP_ITEMS and item not in CUSTOM_SHOP_ITEMS: return await ctx.send("❌ Нет такого товара")
    data = SHOP_ITEMS.get(item) or CUSTOM_SHOP_ITEMS.get(item)
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < data["price"]: return await ctx.send(f"❌ Нужно {data['price']} 💎")
    await add_balance(ctx.author.id, ctx.guild.id, -data["price"])
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        inv.append(item)
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        # Если это цвет профиля
        if data.get("type") == "color" and "color_code" in data:
            await db.execute('UPDATE users SET profile_color=? WHERE user_id=? AND guild_id=?', (data["color_code"], ctx.author.id, ctx.guild.id))
        # Если это роль
        if data.get("type") == "role" and data.get("role_id"):
            role = ctx.guild.get_role(data["role_id"])
            if role: await ctx.author.add_roles(role)
        # Если это бустер
        if data.get("type") == "booster":
            if "exp" in item.lower():
                active_boosters[ctx.author.id]["exp"] = {"mult": 2 if "x2" in item else 5, "end": time.time() + data["duration"]}
            elif "денег" in item.lower():
                active_boosters[ctx.author.id]["money"] = {"mult": 2 if "x2" in item else 5, "end": time.time() + data["duration"]}
            elif "удачи" in item.lower():
                active_boosters[ctx.author.id]["luck"] = {"mult": 1.2, "end": time.time() + data["duration"]}
        await db.commit()
    await ctx.send(f"✅ {ctx.author.mention} купил **{item}** за {data['price']} 💎!")

@bot.command()
async def use(ctx, *, item: str = None):
    if not item: return await ctx.send("❌ j.use <предмет>")
    item = item.lower()
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        if item not in inv: return await ctx.send(f"❌ Нет {item} в инвентаре")
        inv.remove(item)
        # Лотерейные билеты
        if item == "лотерейный билет":
            win = random.randint(0, 100)
            if win < 10: prize = random.randint(1000, 100000)
            elif win < 30: prize = random.randint(500, 5000)
            else: prize = 0
            if prize > 0:
                await add_balance(ctx.author.id, ctx.guild.id, prize)
                await ctx.send(f"🎫 Вы выиграли {prize} 💎!")
            else:
                await ctx.send(f"🎫 К сожалению, ничего не выиграно")
        elif item == "золотой лотерейный билет":
            win = random.randint(0, 100)
            if win < 5: prize = random.randint(100000, 1000000)
            elif win < 20: prize = random.randint(10000, 100000)
            elif win < 50: prize = random.randint(1000, 10000)
            else: prize = 0
            if prize > 0:
                await add_balance(ctx.author.id, ctx.guild.id, prize)
                await ctx.send(f"✨ Вы выиграли {prize} 💎!")
            else:
                await ctx.send(f"✨ К сожалению, ничего не выиграно")
        # Инвестиции (продажа)
        elif item in ["золотой слиток", "алмаз", "рубин", "сапфир", "изумруд"]:
            sell_price = SHOP_ITEMS[item].get("sell_price", SHOP_ITEMS[item]["price"] // 2)
            await add_balance(ctx.author.id, ctx.guild.id, sell_price)
            await ctx.send(f"💰 Вы продали {item} за {sell_price} 💎")
        # Обычные предметы
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

@bot.command()
@commands.has_permissions(administrator=True)
async def add_shop_item(ctx, name: str, price: int, role_id: int, *, desc: str = "Кастомный товар"):
    if name.lower() in SHOP_ITEMS or name.lower() in CUSTOM_SHOP_ITEMS: return await ctx.send("❌ Товар уже есть")
    CUSTOM_SHOP_ITEMS[name.lower()] = {"price": price, "description": desc, "type": "role", "role_id": role_id}
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('INSERT OR REPLACE INTO custom_shop VALUES (?,?,?,?)', (name.lower(), price, desc, role_id))
        await db.commit()
    await ctx.send(f"✅ Добавлен {name} за {price} 💎")

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_shop_item(ctx, *, name: str):
    name = name.lower()
    if name not in CUSTOM_SHOP_ITEMS: return await ctx.send("❌ Нет такого товара")
    del CUSTOM_SHOP_ITEMS[name]
    async with aiosqlite.connect("justice.db") as db:
        await db.execute('DELETE FROM custom_shop WHERE name=?', (name,))
        await db.commit()
    await ctx.send(f"✅ Удалён {name}")

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
    else: await ctx.send(f"{ctx.author.mention} целует воздух! 💋")
@bot.command()
async def pat(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} гладит {member.mention}! 🖐️", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["pat"])
        await ctx.send(embed=embed)
    else: await ctx.send(f"{ctx.author.mention} гладит себя! 🖐️")
@bot.command()
async def poke(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} тыкает {member.mention}! 👉", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["poke"])
        await ctx.send(embed=embed)
    else: await ctx.send(f"{ctx.author.mention} тыкает в воздух! 👉")
@bot.command()
async def slap(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} шлёпает {member.mention}! 👋", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["slap"])
        await ctx.send(embed=embed)
    else: await ctx.send(f"{ctx.author.mention} шлёпает воздух! 👋")
@bot.command()
async def punch(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} бьёт {member.mention}! 👊", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["punch"])
        await ctx.send(embed=embed)
    else: await ctx.send(f"{ctx.author.mention} бьёт воздух! 👊")
@bot.command()
async def bite(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} кусает {member.mention}! 🦷", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["bite"])
        await ctx.send(embed=embed)
    else: await ctx.send(f"{ctx.author.mention} кусает воздух! 🦷")
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
    else: await ctx.send(f"{ctx.author.mention} посылает воздушный поцелуй! 💋")
@bot.command()
async def handhold(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} держит за руку {member.mention}! 👫", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["handhold"])
        await ctx.send(embed=embed)
    else: await ctx.send(f"{ctx.author.mention} держит себя за руку! 👫")
@bot.command()
async def tickle(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} щекочет {member.mention}! 😂", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["tickle"])
        await ctx.send(embed=embed)
    else: await ctx.send(f"{ctx.author.mention} щекочет себя! 😂")
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
    else: await ctx.send(f"{ctx.author.mention} извиняется! 🙏")
@bot.command()
async def stare(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} смотрит на {member.mention}! 👀", color=discord.Color.blue())
        embed.set_image(url=REACTION_GIFS["stare"])
        await ctx.send(embed=embed)
    else: await ctx.send(f"{ctx.author.mention} смотрит в пустоту! 👀")
@bot.command()
async def wink(ctx, member: discord.Member = None):
    if member:
        embed = discord.Embed(description=f"{ctx.author.mention} подмигивает {member.mention}! 😉", color=discord.Color.pink())
        embed.set_image(url=REACTION_GIFS["wink"])
        await ctx.send(embed=embed)
    else: await ctx.send(f"{ctx.author.mention} подмигивает! 😉")

# ========== ГЕНДЕР ==========
@bot.command()
async def gender(ctx, choice: str = None):
    if not choice: return await ctx.send("⚧ j.gender male/female")
    choice = choice.lower()
    male = ctx.guild.get_role(ROLE_BOY)
    female = ctx.guild.get_role(ROLE_GIRL)
    if choice in ["male","мужчина","м"]:
        if male:
            if female in ctx.author.roles: await ctx.author.remove_roles(female)
            await ctx.author.add_roles(male)
            await update_user(ctx.author.id, ctx.guild.id, gender="male")
            await ctx.send(f"✅ {ctx.author.mention} выбрал мужской пол")
    elif choice in ["female","девушка","ж"]:
        if female:
            if male in ctx.author.roles: await ctx.author.remove_roles(male)
            await ctx.author.add_roles(female)
            await update_user(ctx.author.id, ctx.guild.id, gender="female")
            await ctx.send(f"✅ {ctx.author.mention} выбрал женский пол")
    else: await ctx.send("❌ male/female")

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

# ========== ЭКОНОМИКА ==========
@bot.command()
async def balance(ctx, member: discord.Member = None):
    t = member or ctx.author
    d = await get_user(t.id, ctx.guild.id)
    await ctx.send(f"💰 {t.mention}: {d[4]} 💎 | 🏦 {d[5] if len(d)>5 else 0} 💎")

@bot.command()
async def bank(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    await ctx.send(f"🏦 **Банк** {ctx.author.mention}\n💰 {d[5] if len(d)>5 else 0} 💎\n📈 {BANK_INTEREST*100}% в день")

@bot.command()
async def deposit(ctx, amount: int):
    if amount<10: return await ctx.send("❌ Мин. 10 💎")
    d = await get_user(ctx.author.id, ctx.guild.id)
    if d[4] < amount: return await ctx.send(f"❌ Не хватает ({d[4]} 💎)")
    await add_balance(ctx.author.id, ctx.guild.id, -amount)
    await add_bank(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"🏦 Внесено {amount} 💎 в банк")

@bot.command()
async def withdraw(ctx, amount: int):
    d = await get_user(ctx.author.id, ctx.guild.id)
    bank = d[5] if len(d)>5 else 0
    if bank < amount: return await ctx.send(f"❌ В банке {bank} 💎")
    await add_bank(ctx.author.id, ctx.guild.id, -amount)
    await add_balance(ctx.author.id, ctx.guild.id, amount)
    await ctx.send(f"🏦 Выведено {amount} 💎 из банка")

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
            return await ctx.send(f"⏰ Через {rem//3600}ч {(rem%3600)//60}мин")
    earn = random.randint(500, 1500)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    await update_user(ctx.author.id, ctx.guild.id, last_daily=datetime.now().isoformat())
    await ctx.send(f"🎁 Ежедневный бонус +{earn} 💎")

@bot.command()
async def weekly(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    last = d[11] if len(d)>11 else None
    if last:
        ld = datetime.fromisoformat(last)
        if (datetime.now()-ld).days < 7:
            rem = 604800 - (datetime.now()-ld).seconds
            return await ctx.send(f"⏰ Через {rem//86400}д")
    earn = random.randint(3000, 6000)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    await update_user(ctx.author.id, ctx.guild.id, last_weekly=datetime.now().isoformat())
    await ctx.send(f"🎁 Еженедельный бонус +{earn} 💎")

@bot.command()
async def monthly(ctx):
    d = await get_user(ctx.author.id, ctx.guild.id)
    last = d[12] if len(d)>12 else None
    if last:
        ld = datetime.fromisoformat(last)
        if (datetime.now()-ld).days < 30:
            rem = 2592000 - (datetime.now()-ld).seconds
            return await ctx.send(f"⏰ Через {rem//86400}д")
    earn = random.randint(10000, 20000)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    await update_user(ctx.author.id, ctx.guild.id, last_monthly=datetime.now().isoformat())
    await ctx.send(f"🎁 Ежемесячный бонус +{earn} 💎")

@bot.command()
async def timely(ctx):
    ready, rem = check_cooldown(ctx.author.id, "timely")
    if not ready: return await ctx.send(f"⏰ Через {rem//60}мин")
    earn = random.randint(200, 500)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    set_cooldown(ctx.author.id, "timely")
    await ctx.send(f"🎁 Бонус +{earn} 💎")

@bot.command()
async def work(ctx):
    can, w = check_cooldown(ctx.author.id, "work")
    if not can: return await ctx.send(f"❌ КД {w//60}мин")
    earn = random.randint(300, 800)
    await add_balance(ctx.author.id, ctx.guild.id, earn)
    set_cooldown(ctx.author.id, "work")
    await ctx.send(f"💼 Работа +{earn} 💎")

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
async def plusrep(ctx, member: discord.Member, *, reason: str = "Нет"):
    if member==ctx.author: return await ctx.send("❌ Себе нельзя")
    can, w = check_rep_cooldown(ctx.author.id, member.id)
    if not can: return await ctx.send(f"❌ КД {w//60}мин")
    set_rep_cooldown(ctx.author.id, member.id)
    nr = await add_reputation(member.id, ctx.guild.id, 1)
    await ctx.send(f"👍 +1 репутации {member.mention}! Теперь {nr}")

@bot.command()
async def minusrep(ctx, member: discord.Member, *, reason: str = "Нет"):
    if member==ctx.author: return await ctx.send("❌ Себе нельзя")
    can, w = check_rep_cooldown(ctx.author.id, member.id)
    if not can: return await ctx.send(f"❌ КД {w//60}мин")
    set_rep_cooldown(ctx.author.id, member.id)
    nr = await add_reputation(member.id, ctx.guild.id, -1)
    await ctx.send(f"👎 -1 репутации {member.mention}! Теперь {nr}")

# ========== ИГРЫ ==========
@bot.command()
async def casino(ctx, amount: int = None):
    if not amount: return await ctx.send("🎰 j.casino <ставка>")
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
        await msg.edit(content=f"🎰 **ВЫИГРЫШ!** +{wa} 💎")
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await msg.edit(content=f"🎰 **ПРОИГРЫШ!** -{amount} 💎")

@bot.command()
async def slots(ctx, bet: int = None):
    if not bet: return await ctx.send("🎰 j.slots <ставка>")
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
    if not num or not bet: return await ctx.send("🎲 j.dice <1-6> <ставка>")
    can, w = check_cooldown(ctx.author.id, "dice")
    if not can: return await ctx.send(f"⏰ {w}сек")
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
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🎲 **{roll}!** НЕ УГАДАЛ! -{bet} 💎")

@bot.command()
async def coinflip(ctx, side: str = None, bet: int = None):
    if not side or not bet: return await ctx.send("🪙 j.coinflip <орёл/решка> <ставка>")
    can, w = check_cooldown(ctx.author.id, "coin")
    if not can: return await ctx.send(f"⏰ {w}сек")
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
    else:
        await add_balance(ctx.author.id, ctx.guild.id, -bet)
        await msg.edit(content=f"🪙 {res.upper()}! НЕ УГАДАЛ! -{bet} 💎")

@bot.command()
async def rps(ctx, choice: str = None, bet: int = None):
    if not choice or not bet: return await ctx.send("✊ j.rps <камень/ножницы/бумага> <ставка>")
    can, w = check_cooldown(ctx.author.id, "rps")
    if not can: return await ctx.send(f"⏰ {w}сек")
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
        await msg.edit(content=f"✊ {choice} vs {botc} → НИЧЬЯ! Ставка возвращена")
        return
    if (choice=="камень" and botc=="ножницы") or (choice=="ножницы" and botc=="бумага") or (choice=="бумага" and botc=="камень"):
        if win:
            wa = bet * 2
            await add_balance(ctx.author.id, ctx.guild.id, wa)
            await msg.edit(content=f"✊ {choice} vs {botc} → ВЫИГРЫШ! +{wa} 💎")
        else:
            await add_balance(ctx.author.id, ctx.guild.id, -bet)
            await msg.edit(content=f"✊ {choice} vs {botc} → ПРОИГРЫШ! -{bet} 💎")
    else:
        if win:
            wa = bet * 2
            await add_balance(ctx.author.id, ctx.guild.id, wa)
            await msg.edit(content=f"✊ {choice} vs {botc} → ВЫИГРЫШ! +{wa} 💎")
        else:
            await add_balance(ctx.author.id, ctx.guild.id, -bet)
            await msg.edit(content=f"✊ {choice} vs {botc} → ПРОИГРЫШ! -{bet} 💎")

@bot.command()
async def blackjack(ctx, bet: int = None):
    if not bet: return await ctx.send("🃏 j.blackjack <ставка>")
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
    msg = await ctx.send(f"🃏 БЛЭКДЖЕК | Ставка: {bet} 💎\n\nВаши: {' '.join(player)} ({hv(player)})\nДилер: {dealer[0]} ?")
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
                await i.response.edit_message(content=f"🃏 **ПЕРЕБОР!**\nВаши: {' '.join(player)} ({pv})\nДилер: {' '.join(dealer)} ({hv(dealer)})\n-{bet} 💎", view=None)
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
            elif pv==dv:
                await add_balance(ctx.author.id, ctx.guild.id, bet)
                await i.response.edit_message(content=f"🃏 **НИЧЬЯ!**\nВаши: {' '.join(player)} ({pv})\nДилер: {' '.join(dealer)} ({dv})\nСтавка возвращена", view=None)
            else:
                await i.response.edit_message(content=f"🃏 **ПРОИГРЫШ!**\nВаши: {' '.join(player)} ({pv})\nДилер: {' '.join(dealer)} ({dv})\n-{bet} 💎", view=None)
            self.ended=True
        async def on_timeout(self):
            if not self.ended:
                await msg.edit(content="⏰ Время вышло! Ставка возвращена", view=None)
                await add_balance(ctx.author.id, ctx.guild.id, bet)
    view = BJView()
    await msg.edit(view=view)

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
    for i, (uid, val, *extra) in enumerate(rows, 1):
        u = await bot.fetch_user(uid)
        if u:
            if category == "level":
                xp = extra[0] if extra else 0
                msg += f"{i}. {u.name} – {val} ур. ({xp} XP)\n"
            elif category == "balance":
                msg += f"{i}. {u.name} – {val} 💎\n"
            elif category == "reputation":
                msg += f"{i}. {u.name} – {val} ⭐\n"
            elif category == "messages":
                msg += f"{i}. {u.name} – {val} сообщ.\n"
    await ctx.send(msg[:1900])

# ========== ПРИВАТНЫЕ ГОЛОСОВЫЕ КАНАЛЫ ==========
@bot.event
async def on_voice_state_update(member, before, after):
    # Создание приватного канала
    if after.channel and after.channel.id == VC_TRIGGER_CHANNEL_ID:
        category = member.guild.get_channel(VC_CREATE_CATEGORY_ID)
        if category:
            existing = [c for c in category.voice_channels if c.name.startswith("Приватный")]
            num = len(existing) + 1
            
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(connect=False),
                member: discord.PermissionOverwrite(connect=True, manage_channels=True, mute_members=True, deafen_members=True, move_members=True),
                member.guild.me: discord.PermissionOverwrite(connect=True, manage_channels=True)
            }
            for rid in SUPPORT_ROLE_IDS:
                role = member.guild.get_role(rid)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(connect=True)
            
            channel = await category.create_voice_channel(name=f"Приватный #{num}", overwrites=overwrites)
            await member.move_to(channel)
            
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('INSERT INTO private_vc (channel_id, owner_id, guild_id, channel_name, created_at) VALUES (?,?,?,?,?)',
                                (channel.id, member.id, member.guild.id, channel.name, datetime.now().isoformat()))
                await db.commit()
            
            await log_action(member.guild.id, "🔊 ПРИВАТНЫЙ КАНАЛ", f"{member.mention} создал {channel.mention}")
    
    # Удаление пустого приватного канала
    if before.channel and before.channel.category and before.channel.category.id == VC_CREATE_CATEGORY_ID:
        if len(before.channel.members) == 0:
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('DELETE FROM private_vc WHERE channel_id=?', (before.channel.id,))
                await db.commit()
            try:
                await before.channel.delete()
            except:
                pass

# ========== НАСТРОЙКИ ==========
@bot.command()
@commands.has_permissions(administrator=True)
async def settings(ctx, module: str = None, channel: discord.TextChannel = None):
    if ctx.guild.id not in guild_settings:
        guild_settings[ctx.guild.id] = {}
    if not module:
        s = guild_settings[ctx.guild.id]
        embed = discord.Embed(title="⚙️ НАСТРОЙКИ", color=discord.Color.blue())
        embed.add_field(name="📢 Приветствия", value=f"<#{s.get('welcome_channel', 0)}>" if s.get('welcome_channel') else "❌ Не установлен", inline=False)
        embed.add_field(name="📝 Логи", value=f"<#{s.get('log_channel', 0)}>" if s.get('log_channel') else "❌ Не установлен", inline=False)
        embed.add_field(name="📊 Уровни", value=f"<#{s.get('levels_channel', 0)}>" if s.get('levels_channel') else "❌ Не установлен", inline=False)
        await ctx.send(embed=embed)
        return
    if not channel:
        return await ctx.send(f"❌ Укажите канал: `j.settings {module} #канал`")
    if module == "welcome":
        guild_settings[ctx.guild.id]["welcome_channel"] = channel.id
        await ctx.send(f"✅ Канал приветствий: {channel.mention}")
    elif module == "logs":
        guild_settings[ctx.guild.id]["log_channel"] = channel.id
        await ctx.send(f"✅ Канал логов: {channel.mention}")
    elif module == "levels":
        guild_settings[ctx.guild.id]["levels_channel"] = channel.id
        await ctx.send(f"✅ Канал уровней: {channel.mention}")
    else:
        await ctx.send("❌ Доступно: welcome, logs, levels")

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
    embed.add_field(name="🤖 Автомод", value="`j.automod status/enable/disable`\n`j.automod words add/remove/list`\n`j.automod invites on/off`\n`j.automod phishing on/off`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.check(is_owner)
async def owner_give(ctx, member: discord.Member, amount: int):
    if amount <= 0: return await ctx.send("❌ Сумма > 0")
    await add_balance(member.id, ctx.guild.id, amount)
    await ctx.send(f"✅ Выдано {amount} 💎 {member.mention}")
    await log_action(ctx.guild.id, "👑 ВЫДАЧА", f"{ctx.author.mention} выдал {amount} 💎 {member.mention}")

@bot.command()
@commands.check(is_owner)
async def owner_take(ctx, member: discord.Member, amount: int):
    if amount <= 0: return await ctx.send("❌ Сумма > 0")
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
    size = os.path.getsize(backup) / (1024 * 1024)
    await ctx.send(f"💾 Резервная копия: {backup} ({size:.2f} MB)")
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
    modified = datetime.fromtimestamp(os.path.getmtime("justice.db"))
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT COUNT(*) FROM users')
        users = (await cur.fetchone())[0]
    embed = discord.Embed(title="📊 ИНФО БД", color=discord.Color.blue())
    embed.add_field(name="📁 Файл", value="justice.db", inline=True)
    embed.add_field(name="📦 Размер", value=f"{size:.2f} MB", inline=True)
    embed.add_field(name="🕐 Изменена", value=modified.strftime("%d.%m.%Y %H:%M"), inline=True)
    embed.add_field(name="👥 Пользователей", value=users, inline=True)
    await ctx.send(embed=embed)

# ========== СОБЫТИЯ ==========
async def reset_activity_counters():
    now = datetime.now()
    async with aiosqlite.connect("justice.db") as db:
        if now.hour == 0 and now.minute < 5:
            await db.execute('UPDATE users SET today_messages = 0')
            print("✅ Дневные счётчики сброшены")
        if now.weekday() == 0 and now.hour == 0 and now.minute < 5:
            await db.execute('UPDATE users SET week_messages = 0')
            print("✅ Недельные счётчики сброшены")
        if now.day == 1 and now.hour == 0 and now.minute < 5:
            await db.execute('UPDATE users SET month_messages = 0')
            print("✅ Месячные счётчики сброшены")
        await db.commit()

@bot.event
async def on_ready():
    await init_db()
    print(f"✅ {bot.user} запущен!")
    print(f"📊 На {len(bot.guilds)} серверах")
    
    # Запуск фоновых задач
    bot.loop.create_task(stoloto_scheduler())
    async def reset_loop():
        while True:
            await asyncio.sleep(60)
            await reset_activity_counters()
    bot.loop.create_task(reset_loop())
    
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="j.help | Justice Bot"))
    print("✅ Бот готов!")

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    if message.guild:
        await get_user(message.author.id, message.guild.id)
        
        # Автомодерация
        sett = guild_settings.get(message.guild.id, {})
        exempt = any(message.guild.get_role(rid) in message.author.roles for rid in sett.get("automod_exempt_roles", []))
        if not exempt and sett.get("automod_enabled", True):
            is_spam, reason = await check_spam(message)
            if is_spam:
                try:
                    uid = message.author.id
                    if uid in spam_messages_to_delete and spam_messages_to_delete[uid]:
                        for mid in spam_messages_to_delete[uid]:
                            try:
                                dmsg = await message.channel.fetch_message(mid)
                                await dmsg.delete()
                            except: pass
                        spam_messages_to_delete[uid] = []
                    else:
                        await message.delete()
                    wc = await add_auto_warning(message.author, reason, message.channel)
                    asyncio.create_task(send_warning_dm(message.author, reason, wc, message.channel))
                except: pass
                return
        
        # Опыт за сообщение
        level_up, new_level = await add_xp(message.author.id, message.guild.id, random.randint(5, 15))
        if level_up:
            ch = bot.get_channel(LEVEL_CHANNEL_ID)
            if ch:
                await ch.send(f"🎉 {message.author.mention} достиг {new_level} уровня!")
    
    # Ответ на упоминание
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
        embed = discord.Embed(title="🎉 ДОБРО ПОЖАЛОВАТЬ!", description=f"{member.mention} присоединился к серверу!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        await ch.send(embed=embed)
        await log_action(member.guild.id, "👋 НОВЫЙ УЧАСТНИК", f"{member.mention} присоединился к серверу")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    await ctx.send(f"❌ Ошибка: {str(error)[:100]}")


# ========== ДОНАТ ==========
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
        value="https://www.donationalerts.com/r/primera_espada",
        inline=False
    )
    embed.add_field(
        name="📱 СБП",
        value="Доступен перевод по номеру телефона через СБП (уточняйте у администратора)",
        inline=False
    )
    embed.set_footer(text="Все средства идут на развитие бота и оплату серверов")
    await ctx.send(embed=embed)

# ========== КРЕСТИКИ-НОЛИКИ ==========
class TicTacToeButton(Button):
    def __init__(self, x, y, user_id, bet):
        super().__init__(style=discord.ButtonStyle.secondary, label="⬜", row=y, custom_id=f"ttt_{x}_{y}")
        self.x = x
        self.y = y
        self.user_id = user_id
        self.bet = bet
        self.clicked = False

    async def callback(self, interaction: discord.Interaction):
        game = ttt_games.get(interaction.channel.id)
        if not game:
            return await interaction.response.send_message("❌ Игра не найдена!", ephemeral=True)
        if interaction.user.id not in [game["p1"], game["p2"]]:
            return await interaction.response.send_message("❌ Вы не участник!", ephemeral=True)
        if game["turn"] != interaction.user.id:
            return await interaction.response.send_message("❌ Сейчас не ваш ход!", ephemeral=True)
        if self.clicked:
            return await interaction.response.send_message("❌ Эта клетка уже занята!", ephemeral=True)
        
        # Ход
        symbol = "❌" if interaction.user.id == game["p1"] else "⭕"
        self.label = symbol
        self.style = discord.ButtonStyle.danger if symbol == "❌" else discord.ButtonStyle.success
        self.clicked = True
        game["board"][self.y][self.x] = symbol
        game["turn"] = game["p2"] if game["turn"] == game["p1"] else game["p1"]
        
        # Проверка победы
        winner = game.get("winner", None)
        if not winner:
            winner = check_ttt_winner(game["board"])
        
        if winner:
            prize = game["bet"] * 2
            if winner == "❌":
                await add_balance(game["p1"], interaction.guild.id, prize)
                await add_balance(game["p2"], interaction.guild.id, -game["bet"])
                winner_mention = f"<@{game['p1']}>"
            elif winner == "⭕":
                await add_balance(game["p2"], interaction.guild.id, prize)
                await add_balance(game["p1"], interaction.guild.id, -game["bet"])
                winner_mention = f"<@{game['p2']}>"
            else:
                winner_mention = "Ничья! Ставки возвращены"
                await add_balance(game["p1"], interaction.guild.id, game["bet"])
                await add_balance(game["p2"], interaction.guild.id, game["bet"])
            
            embed = discord.Embed(title="❌⭕ КРЕСТИКИ-НОЛИКИ", color=discord.Color.gold())
            embed.add_field(name="🏆 РЕЗУЛЬТАТ", value=f"{winner_mention} победил!\n💰 Выигрыш: {prize} 💎" if winner != "Ничья" else winner_mention, inline=False)
            await interaction.response.edit_message(embed=embed, view=None)
            del ttt_games[interaction.channel.id]
            return
        
        # Проверка ничьи
        all_filled = all(cell != "⬜" for row in game["board"] for cell in row)
        if all_filled:
            await add_balance(game["p1"], interaction.guild.id, game["bet"])
            await add_balance(game["p2"], interaction.guild.id, game["bet"])
            embed = discord.Embed(title="❌⭕ КРЕСТИКИ-НОЛИКИ", color=discord.Color.blue())
            embed.add_field(name="🤝 НИЧЬЯ!", value="Ставки возвращены", inline=False)
            await interaction.response.edit_message(embed=embed, view=None)
            del ttt_games[interaction.channel.id]
            return
        
        # Обновляем доску
        view = TicTacToeView(game["p1"], game["p2"], game["bet"], game["board"])
        embed = discord.Embed(title="❌⭕ КРЕСТИКИ-НОЛИКИ", color=discord.Color.blue())
        embed.add_field(name="💰 Ставка", value=f"{game['bet']} 💎", inline=True)
        embed.add_field(name="🎲 Ход", value=f"<@{game['turn']}>", inline=True)
        await interaction.response.edit_message(embed=embed, view=view)

class TicTacToeView(View):
    def __init__(self, p1, p2, bet, board=None):
        super().__init__(timeout=180)
        self.p1 = p1
        self.p2 = p2
        self.bet = bet
        if board:
            self.board = board
        else:
            self.board = [["⬜", "⬜", "⬜"] for _ in range(3)]
        for y in range(3):
            for x in range(3):
                btn = TicTacToeButton(x, y, p1, bet)
                if self.board[y][x] != "⬜":
                    btn.label = self.board[y][x]
                    btn.style = discord.ButtonStyle.danger if self.board[y][x] == "❌" else discord.ButtonStyle.success
                    btn.clicked = True
                self.add_item(btn)

def check_ttt_winner(board):
    for row in board:
        if row[0] == row[1] == row[2] and row[0] != "⬜":
            return row[0]
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != "⬜":
            return board[0][col]
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != "⬜":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != "⬜":
        return board[0][2]
    return None

@bot.command()
async def ttt(ctx, member: discord.Member = None, bet: int = None):
    """❌⭕ Крестики-нолики на деньги"""
    if not member or not bet:
        return await ctx.send("❌ Использование: `j.ttt @user <ставка>`")
    if member == ctx.author:
        return await ctx.send("❌ Нельзя играть с собой")
    if bet < 100:
        return await ctx.send("❌ Минимальная ставка 100 💎")
    
    bal1 = (await get_user(ctx.author.id, ctx.guild.id))[4]
    bal2 = (await get_user(member.id, ctx.guild.id))[4]
    if bal1 < bet or bal2 < bet:
        return await ctx.send("❌ У кого-то не хватает денег")
    
    embed = discord.Embed(title="🎮 ПРИГЛАШЕНИЕ", description=f"{member.mention}, игра на **{bet}** 💎?\nКрестики-нолики", color=discord.Color.purple())
    view = View()
    view.add_item(AcceptTTTButton(member.id, ctx.author.id, bet, ctx.channel.id))
    view.add_item(DenyTTTButton(member.id))
    await ctx.send(embed=embed, view=view)

class AcceptTTTButton(Button):
    def __init__(self, opponent, inviter, bet, channel_id):
        super().__init__(label="✅ Принять", style=discord.ButtonStyle.success)
        self.opponent = opponent
        self.inviter = inviter
        self.bet = bet
        self.channel_id = channel_id
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.opponent:
            return await interaction.response.send_message("❌ Не вы!", ephemeral=True)
        
        bal1 = (await get_user(self.inviter, interaction.guild.id))[4]
        bal2 = (await get_user(self.opponent, interaction.guild.id))[4]
        if bal1 < self.bet or bal2 < self.bet:
            return await interaction.response.edit_message(content="❌ У кого-то не хватает денег!", view=None)
        
        await add_balance(self.inviter, interaction.guild.id, -self.bet)
        await add_balance(self.opponent, interaction.guild.id, -self.bet)
        
        view = TicTacToeView(self.inviter, self.opponent, self.bet)
        embed = discord.Embed(title="❌⭕ КРЕСТИКИ-НОЛИКИ", color=discord.Color.blue())
        embed.add_field(name="💰 Ставка", value=f"{self.bet} 💎", inline=True)
        embed.add_field(name="🎲 Ход", value=f"<@{self.inviter}> (❌)", inline=True)
        
        ttt_games[interaction.channel.id] = {
            "p1": self.inviter, "p2": self.opponent, "bet": self.bet,
            "board": [["⬜", "⬜", "⬜"] for _ in range(3)], "turn": self.inviter
        }
        
        await interaction.response.edit_message(content=None, embed=embed, view=view)

class DenyTTTButton(Button):
    def __init__(self, opponent):
        super().__init__(label="❌ Отказать", style=discord.ButtonStyle.danger)
        self.opponent = opponent
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.opponent:
            return await interaction.response.send_message("❌ Не вы!", ephemeral=True)
        await interaction.response.edit_message(content=f"❌ {interaction.user.mention} отказался", view=None)

# ========== ПОКЕР (ПОЛНОЦЕННАЯ ИГРА) ==========
class PokerGame:
    def __init__(self, players, bets, channel_id):
        self.players = players  # list of user_ids
        self.bets = bets  # dict {user_id: bet}
        self.hands = {}  # dict {user_id: [cards]}
        self.community = []  # общие карты
        self.current_bet = 0
        self.pot = sum(bets.values())
        self.folded = []
        self.current_player_index = 0
        self.channel_id = channel_id
        self.status = "waiting"  # waiting, flop, turn, river, showdown
        self.last_raiser = None
        self.stage = "preflop"
    
    def deal(self, deck):
        for uid in self.players:
            self.hands[uid] = [deck.pop(), deck.pop()]
    
    def get_card_value(self, card):
        rank = card[:-1]
        values = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14}
        return values.get(rank, 0)
    
    def get_hand_rank(self, cards):
        # cards = 2 свои + 5 общих = 7 карт
        ranks = sorted([self.get_card_value(c) for c in cards], reverse=True)
        suits = [c[-1] for c in cards]
        # Проверка на флеш
        flush_suit = None
        for suit in ['♠️','♥️','♣️','♦️']:
            if suits.count(suit) >= 5:
                flush_suit = suit
                break
        # Проверка на стрит
        unique_ranks = sorted(set(ranks), reverse=True)
        straight_high = None
        for i in range(len(unique_ranks)-4):
            if unique_ranks[i] - unique_ranks[i+4] == 4:
                straight_high = unique_ranks[i]
                break
        if straight_high is None and set([14,2,3,4,5]).issubset(set(ranks)):
            straight_high = 5
        # Проверка на флеш-рояль и стрит-флеш
        if flush_suit and straight_high:
            flush_cards = [c for c in cards if c.endswith(flush_suit)]
            flush_ranks = sorted([self.get_card_value(c) for c in flush_cards], reverse=True)
            for i in range(len(flush_ranks)-4):
                if flush_ranks[i] - flush_ranks[i+4] == 4:
                    if flush_ranks[i] == 14:
                        return (9, flush_ranks[i])  # флеш-рояль
                    return (8, flush_ranks[i])  # стрит-флеш
        # Проверка на каре, фулл-хаус, сет, две пары, пара
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        counts = sorted(rank_counts.values(), reverse=True)
        if counts[0] == 4:
            return (7, max([r for r,c in rank_counts.items() if c==4]))
        if counts[0] == 3 and counts[1] >= 2:
            return (6, max([r for r,c in rank_counts.items() if c==3]))
        if flush_suit:
            flush_ranks = sorted([self.get_card_value(c) for c in cards if c.endswith(flush_suit)], reverse=True)[:5]
            return (5, flush_ranks[0])
        if straight_high:
            return (4, straight_high)
        if counts[0] == 3:
            return (3, max([r for r,c in rank_counts.items() if c==3]))
        if counts[0] == 2 and counts[1] == 2:
            pairs = sorted([r for r,c in rank_counts.items() if c==2], reverse=True)
            return (2, pairs[0], pairs[1])
        if counts[0] == 2:
            return (1, max([r for r,c in rank_counts.items() if c==2]))
        return (0, max(ranks))

poker_games = {}  # channel_id -> PokerGame

class PokerButton(Button):
    def __init__(self, label, style, action, amount=None):
        super().__init__(label=label, style=style)
        self.action = action
        self.amount = amount

    async def callback(self, interaction: discord.Interaction):
        game = poker_games.get(interaction.channel.id)
        if not game:
            return await interaction.response.send_message("❌ Игра не найдена!", ephemeral=True)
        if interaction.user.id not in game.players:
            return await interaction.response.send_message("❌ Вы не в игре!", ephemeral=True)
        if interaction.user.id in game.folded:
            return await interaction.response.send_message("❌ Вы уже сбросили карты!", ephemeral=True)
        if game.players[game.current_player_index] != interaction.user.id:
            return await interaction.response.send_message("❌ Сейчас не ваш ход!", ephemeral=True)
        
        user = await get_user(interaction.user.id, interaction.guild.id)
        
        if self.action == "check":
            if game.current_bet > game.bets.get(interaction.user.id, 0):
                return await interaction.response.send_message("❌ Сначала нужно уравнять ставку!", ephemeral=True)
            await interaction.response.send_message(f"✅ {interaction.user.mention} чекает", ephemeral=False)
        
        elif self.action == "call":
            need = game.current_bet - game.bets.get(interaction.user.id, 0)
            if need > user[4]:
                return await interaction.response.send_message(f"❌ Не хватает {need} 💎!", ephemeral=True)
            await add_balance(interaction.user.id, interaction.guild.id, -need)
            game.bets[interaction.user.id] = game.bets.get(interaction.user.id, 0) + need
            game.pot += need
            await interaction.response.send_message(f"✅ {interaction.user.mention} уравнял ставку (+{need} 💎)", ephemeral=False)
        
        elif self.action == "raise":
            if not self.amount:
                modal = RaiseModal(game, interaction.user.id)
                await interaction.response.send_modal(modal)
                return
            amount = self.amount
            need = game.current_bet - game.bets.get(interaction.user.id, 0) + amount
            if need > user[4]:
                return await interaction.response.send_message(f"❌ Не хватает {need} 💎!", ephemeral=True)
            await add_balance(interaction.user.id, interaction.guild.id, -need)
            game.bets[interaction.user.id] = game.bets.get(interaction.user.id, 0) + need
            game.pot += need
            game.current_bet = game.bets[interaction.user.id]
            game.last_raiser = interaction.user.id
            await interaction.response.send_message(f"✅ {interaction.user.mention} поднял до {game.current_bet} 💎 (+{need})", ephemeral=False)
        
        elif self.action == "fold":
            game.folded.append(interaction.user.id)
            await interaction.response.send_message(f"❌ {interaction.user.mention} сбросил карты", ephemeral=False)
        
        # Переход к следующему игроку
        next_player = None
        for i in range(len(game.players)):
            idx = (game.current_player_index + 1 + i) % len(game.players)
            if game.players[idx] not in game.folded:
                next_player = idx
                break
        
        if next_player is None:
            # Все сбросили - определяем победителя
            await finish_poker_game(interaction.channel, game)
            return
        
        game.current_player_index = next_player
        
        # Проверка: все ли уравняли ставку
        all_in = all(game.bets.get(p, 0) == game.current_bet or p in game.folded for p in game.players)
        if all_in:
            await next_poker_stage(interaction.channel, game)
        else:
            await update_poker_display(interaction.channel, game)

class RaiseModal(Modal):
    def __init__(self, game, user_id):
        super().__init__(title="Повысить ставку")
        self.game = game
        self.user_id = user_id
        self.amount_input = TextInput(label="Сумма повышения", placeholder="Минимум 50", required=True)
        self.add_item(self.amount_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
        except:
            return await interaction.response.send_message("❌ Введите число!", ephemeral=True)
        if amount < 50:
            return await interaction.response.send_message("❌ Минимальное повышение 50 💎", ephemeral=True)
        
        user = await get_user(self.user_id, interaction.guild.id)
        need = self.game.current_bet - self.game.bets.get(self.user_id, 0) + amount
        
        if need > user[4]:
            return await interaction.response.send_message(f"❌ Не хватает {need} 💎!", ephemeral=True)
        
        await add_balance(self.user_id, interaction.guild.id, -need)
        self.game.bets[self.user_id] = self.game.bets.get(self.user_id, 0) + need
        self.game.pot += need
        self.game.current_bet = self.game.bets[self.user_id]
        self.game.last_raiser = self.user_id
        
        await interaction.response.send_message(f"✅ {interaction.user.mention} поднял до {self.game.current_bet} 💎", ephemeral=False)
        
        # Сброс индекса для следующего раунда
        self.game.current_player_index = 0
        await update_poker_display(interaction.channel, self.game)

async def next_poker_stage(channel, game):
    deck = FULL_DECK.copy()
    random.shuffle(deck)
    
    if game.stage == "preflop":
        # Флоп - 3 карты
        game.community = [deck.pop(), deck.pop(), deck.pop()]
        game.stage = "flop"
        game.current_bet = 0
        game.bets = {p: 0 for p in game.players}
        game.last_raiser = None
    elif game.stage == "flop":
        # Тёрн - 1 карта
        game.community.append(deck.pop())
        game.stage = "turn"
        game.current_bet = 0
        game.bets = {p: 0 for p in game.players}
        game.last_raiser = None
    elif game.stage == "turn":
        # Ривер - 1 карта
        game.community.append(deck.pop())
        game.stage = "river"
        game.current_bet = 0
        game.bets = {p: 0 for p in game.players}
        game.last_raiser = None
    elif game.stage == "river":
        await finish_poker_game(channel, game)
        return
    
    game.current_player_index = 0
    while game.current_player_index < len(game.players) and game.players[game.current_player_index] in game.folded:
        game.current_player_index += 1
    
    await update_poker_display(channel, game)

async def finish_poker_game(channel, game):
    # Определяем победителя
    best_rank = (-1,)
    winner = None
    for uid in game.players:
        if uid in game.folded:
            continue
        all_cards = game.hands[uid] + game.community
        rank = game.get_hand_rank(all_cards)
        if rank > best_rank:
            best_rank = rank
            winner = uid
    
    if winner:
        await add_balance(winner, channel.guild.id, game.pot)
        embed = discord.Embed(title="🃏 ПОКЕР", color=discord.Color.gold())
        embed.add_field(name="🏆 ПОБЕДИТЕЛЬ", value=f"<@{winner}>", inline=True)
        embed.add_field(name="💰 ВЫИГРЫШ", value=f"{game.pot} 💎", inline=True)
        
        # Показываем карты победителя
        winner_cards = ' '.join(game.hands[winner])
        community_cards = ' '.join(game.community)
        embed.add_field(name="🎴 КАРТЫ", value=f"Ваши: {winner_cards}\nОбщие: {community_cards}", inline=False)
        await channel.send(embed=embed)
    else:
        await channel.send("❌ Ошибка определения победителя")
    
    del poker_games[channel.id]

async def update_poker_display(channel, game):
    # Показываем только общие карты (для всех)
    community_str = ' '.join(game.community) if game.community else "❌"
    embed = discord.Embed(title="🃏 ПОКЕР", color=discord.Color.blue())
    embed.add_field(name="🎴 ОБЩИЕ КАРТЫ", value=community_str, inline=False)
    embed.add_field(name="💰 БАНК", value=f"{game.pot} 💎", inline=True)
    embed.add_field(name="📊 СТАВКА", value=f"{game.current_bet} 💎", inline=True)
    embed.add_field(name="🎲 ЭТАП", value=game.stage.upper(), inline=True)
    embed.add_field(name="🎯 ХОД", value=f"<@{game.players[game.current_player_index]}>", inline=False)
    
    # Кнопки для текущего игрока
    view = View()
    view.add_item(PokerButton("✅ Чек", discord.ButtonStyle.secondary, "check"))
    view.add_item(PokerButton("📞 Уравнять", discord.ButtonStyle.primary, "call"))
    view.add_item(PokerButton("📈 Поднять", discord.ButtonStyle.success, "raise"))
    view.add_item(PokerButton("❌ Сброс", discord.ButtonStyle.danger, "fold"))
    
    await channel.send(embed=embed, view=view)

@bot.command()
async def poker(ctx, member1: discord.Member = None, member2: discord.Member = None, bet: int = None):
    """🃏 Покер (2 игрока, Техасский Холдем)"""
    if not member1 or not member2 or not bet:
        return await ctx.send("❌ Использование: `j.poker @игрок1 @игрок2 <ставка>`")
    
    players = [ctx.author.id, member1.id, member2.id]
    if len(set(players)) != 3:
        return await ctx.send("❌ Игроки должны быть разными")
    if bet < 100:
        return await ctx.send("❌ Минимальная ставка 100 💎")
    
    # Проверка балансов
    for uid in players:
        bal = (await get_user(uid, ctx.guild.id))[4]
        if bal < bet:
            user = await bot.fetch_user(uid)
            return await ctx.send(f"❌ У {user.name} не хватает {bet} 💎")
    
    # Списываем ставки
    for uid in players:
        await add_balance(uid, ctx.guild.id, -bet)
    
    # Создаём игру
    deck = FULL_DECK.copy()
    random.shuffle(deck)
    
    game = PokerGame(players, {uid: bet for uid in players}, ctx.channel.id)
    game.deal(deck)
    poker_games[ctx.channel.id] = game
    
    # Показываем карты каждому игроку в ЛС
    for uid in players:
        user = ctx.guild.get_member(uid)
        if user:
            cards = ' '.join(game.hands[uid])
            try:
                await user.send(f"🃏 **Ваши карты в покере:** {cards}\nКанал: {ctx.channel.mention}")
            except:
                pass
    
    embed = discord.Embed(title="🃏 ПОКЕР", description=f"Игра началась!\nУчастники: <@{players[0]}>, <@{players[1]}>, <@{players[2]}>\n💰 Ставка: {bet} 💎\n🎲 Первый ход: <@{players[0]}>", color=discord.Color.green())
    await ctx.send(embed=embed)
    
    # Начинаем игру
    game.current_player_index = 0
    await update_poker_display(ctx.channel, game)    

# ========== ИНВЕСТИЦИИ ==========
@bot.command()
async def invest(ctx, invest_type: str = None, amount: int = None):
    """📊 Инвестировать деньги"""
    if not invest_type or not amount:
        types = "\n".join([f"• {k} - {v['name']}: {v['min']}-{v['max']} 💎, {v['days']} дней, +{v['rate']*100}%" for k, v in INVESTMENTS.items()])
        await ctx.send(f"📊 **Инвестиции**\n{types}\n\nПример: `j.invest надёжный 50000`")
        return
    
    invest_type = invest_type.lower()
    if invest_type not in INVESTMENTS:
        await ctx.send("❌ Неверный тип инвестиций! Доступно: надёжный, средний, рисковый, премиум")
        return
    
    inv_data = INVESTMENTS[invest_type]
    if amount < inv_data["min"] or amount > inv_data["max"]:
        await ctx.send(f"❌ Сумма от {inv_data['min']} до {inv_data['max']} 💎")
        return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < amount:
        await ctx.send(f"❌ Не хватает {amount} 💎")
        return
    
    # Проверка, есть ли уже активная инвестиция
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM investments WHERE user_id=? AND guild_id=? AND claimed=0', (ctx.author.id, ctx.guild.id))
        existing = await cur.fetchone()
        if existing:
            await ctx.send("❌ У вас уже есть активная инвестиция! Дождитесь её завершения.")
            return
        
        await add_balance(ctx.author.id, ctx.guild.id, -amount)
        await db.execute('INSERT INTO investments (user_id, guild_id, invest_type, amount, invest_date, days, interest_rate, claimed) VALUES (?,?,?,?,?,?,?,0)',
                        (ctx.author.id, ctx.guild.id, invest_type, amount, datetime.now().isoformat(), inv_data["days"], inv_data["rate"]))
        await db.commit()
    
    await ctx.send(f"✅ Вы инвестировали {amount} 💎 в **{inv_data['name']}** на {inv_data['days']} дней!\n💰 По окончании вы получите {int(amount * (1 + inv_data['rate']))} 💎")

@bot.command()
async def claim_invest(ctx):
    """💰 Забрать инвестицию"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT * FROM investments WHERE user_id=? AND guild_id=? AND claimed=0', (ctx.author.id, ctx.guild.id))
        inv = await cur.fetchone()
        if not inv:
            await ctx.send("❌ У вас нет активных инвестиций!")
            return
        
        _, _, _, inv_type, amount, inv_date, days, rate, claimed = inv
        inv_date_obj = datetime.fromisoformat(inv_date)
        end_date = inv_date_obj + timedelta(days=days)
        
        if datetime.now() < end_date:
            left = (end_date - datetime.now()).days
            await ctx.send(f"⏰ Инвестиция ещё не завершена! Осталось {left} дней.")
            return
        
        profit = int(amount * (1 + rate))
        await add_balance(ctx.author.id, ctx.guild.id, profit)
        await db.execute('UPDATE investments SET claimed=1 WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        await db.commit()
    
    await ctx.send(f"💰 Вы получили {profit} 💎 (вложено {amount} 💎, прибыль {profit - amount} 💎)")

# ========== ЖИВОТНЫЕ НА ФЕРМЕ ==========
@bot.command()
async def buy_animal(ctx, animal_type: str = None):
    """🐔 Купить животное для фермы"""
    if not animal_type or animal_type.lower() not in FARM_ANIMALS:
        animals = "\n".join([f"• {a} - {data['price']} 💎 | Даёт: {data['produce']} ({data['produce_price']} 💎)" for a, data in FARM_ANIMALS.items()])
        await ctx.send(f"🐔 **Животные для фермы**\n{animals}\n\nПример: `j.buy_animal курица`")
        return
    
    animal = animal_type.lower()
    animal_data = FARM_ANIMALS[animal]
    
    # Проверка на максимальное количество (улучшения)
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT level FROM farm_upgrades WHERE user_id=? AND guild_id=? AND upgrade_type="max_animals"', (ctx.author.id, ctx.guild.id))
        upgrade = await cur.fetchone()
        max_animals = 5 + (upgrade[0] * 2 if upgrade else 0)
        
        cur = await db.execute('SELECT count FROM farm_animals WHERE user_id=? AND guild_id=? AND animal_type=?', (ctx.author.id, ctx.guild.id, animal))
        current = await cur.fetchone()
        current_count = current[0] if current else 0
        
        if current_count >= max_animals:
            await ctx.send(f"❌ У вас уже максимальное количество {animal} ({max_animals})! Улучшите вместимость.")
            return
    
    user = await get_user(ctx.author.id, ctx.guild.id)
    if user[4] < animal_data["price"]:
        await ctx.send(f"❌ Не хватает {animal_data['price']} 💎")
        return
    
    await add_balance(ctx.author.id, ctx.guild.id, -animal_data["price"])
    
    async with aiosqlite.connect("justice.db") as db:
        if current:
            await db.execute('UPDATE farm_animals SET count=? WHERE user_id=? AND guild_id=? AND animal_type=?', (current_count + 1, ctx.author.id, ctx.guild.id, animal))
        else:
            await db.execute('INSERT INTO farm_animals (user_id, guild_id, animal_type, count, last_produce, last_fed) VALUES (?,?,?,1,?,?)',
                            (ctx.author.id, ctx.guild.id, animal, datetime.now().isoformat(), datetime.now().isoformat()))
        await db.commit()
    
    await ctx.send(f"✅ Вы купили {animal_data['name']} за {animal_data['price']} 💎!")

@bot.command()
async def feed_animals(ctx):
    """🌾 Покормить всех животных"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT animal_type, count FROM farm_animals WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        animals = await cur.fetchall()
        
        if not animals:
            await ctx.send("❌ У вас нет животных!")
            return
        
        # Проверка улучшения скорости
        cur2 = await db.execute('SELECT level FROM farm_upgrades WHERE user_id=? AND guild_id=? AND upgrade_type="animal_speed"', (ctx.author.id, ctx.guild.id))
        speed_upgrade = await cur2.fetchone()
        speed_mult = 1 - (speed_upgrade[0] * 0.05 if speed_upgrade else 0)
        
        total_feed = 0
        for animal, count in animals:
            animal_data = FARM_ANIMALS[animal]
            feed_needed = animal_data["feed_amount"] * count
            
            # Проверяем наличие корма в инвентаре
            cur3 = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
            inv = json.loads((await cur3.fetchone())[0] or "[]")
            feed_count = inv.count(f"crop_{animal_data['feed']}")
            
            if feed_count >= feed_needed:
                for _ in range(feed_needed):
                    inv.remove(f"crop_{animal_data['feed']}")
                total_feed += feed_needed
                
                # Обновляем время последнего кормления
                new_time = datetime.now().isoformat()
                await db.execute('UPDATE farm_animals SET last_fed=? WHERE user_id=? AND guild_id=? AND animal_type=?', (new_time, ctx.author.id, ctx.guild.id, animal))
            else:
                await ctx.send(f"⚠️ Не хватает {animal_data['feed']} для {animal} (нужно {feed_needed}, есть {feed_count})")
        
        if total_feed > 0:
            await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
            await db.commit()
            await ctx.send(f"✅ Вы покормили животных! Потрачено {total_feed} еды.")
            await check_achievement(ctx.author.id, ctx.guild.id, "feed_animal", total_feed)
        else:
            await ctx.send("❌ Нет еды для кормления!")

@bot.command()
async def collect_products(ctx):
    """🥚 Собрать продукцию с животных"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT animal_type, count, last_produce FROM farm_animals WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        animals = await cur.fetchall()
        
        if not animals:
            await ctx.send("❌ У вас нет животных!")
            return
        
        # Проверка улучшения продуктивности
        cur2 = await db.execute('SELECT level FROM farm_upgrades WHERE user_id=? AND guild_id=? AND upgrade_type="animal_yield"', (ctx.author.id, ctx.guild.id))
        yield_upgrade = await cur2.fetchone()
        yield_mult = 1 + (yield_upgrade[0] * 0.1 if yield_upgrade else 0)
        
        total_earn = 0
        collected = []
        
        for animal, count, last_produce in animals:
            animal_data = FARM_ANIMALS[animal]
            last_time = datetime.fromisoformat(last_produce)
            time_passed = (datetime.now() - last_time).total_seconds()
            
            # Улучшение скорости
            cur3 = await db.execute('SELECT level FROM farm_upgrades WHERE user_id=? AND guild_id=? AND upgrade_type="animal_speed"', (ctx.author.id, ctx.guild.id))
            speed_upgrade = await cur3.fetchone()
            speed_mult = 1 - (speed_upgrade[0] * 0.05 if speed_upgrade else 0)
            produce_time = animal_data["produce_time"] * speed_mult
            
            if time_passed >= produce_time:
                cycles = int(time_passed // produce_time)
                if cycles > 0:
                    produced = int(count * cycles * yield_mult)
                    earn = produced * animal_data["produce_price"]
                    total_earn += earn
                    collected.append(f"{animal_data['name']} x{produced} (+{earn} 💎)")
                    
                    new_time = last_time + timedelta(seconds=produce_time * cycles)
                    await db.execute('UPDATE farm_animals SET last_produce=? WHERE user_id=? AND guild_id=? AND animal_type=?', (new_time.isoformat(), ctx.author.id, ctx.guild.id, animal))
        
        if total_earn > 0:
            # Добавляем продукцию в инвентарь
            cur4 = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
            inv = json.loads((await cur4.fetchone())[0] or "[]")
            for item in collected:
                product = item.split(" x")[0]
                inv.append(f"product_{product}")
            await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
            await add_balance(ctx.author.id, ctx.guild.id, total_earn)
            await db.commit()
            
            await ctx.send(f"✅ Собрано:\n" + "\n".join(collected[:10]) + f"\n💰 Всего: {total_earn} 💎")
            await check_achievement(ctx.author.id, ctx.guild.id, "collect_animal", len(collected))
        else:
            await ctx.send("❌ Продукция ещё не готова! Подождите.")

@bot.command()
async def my_animals(ctx):
    """🐔 Показать всех животных"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT animal_type, count, last_fed FROM farm_animals WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        animals = await cur.fetchall()
        
        if not animals:
            await ctx.send("🐔 У вас нет животных! Купите: `j.buy_animal курица`")
            return
        
        embed = discord.Embed(title=f"🐔 ЖИВОТНЫЕ | {ctx.author.display_name}", color=discord.Color.green())
        for animal, count, last_fed in animals:
            animal_data = FARM_ANIMALS[animal]
            last_fed_time = datetime.fromisoformat(last_fed)
            hungry = (datetime.now() - last_fed_time).total_seconds() > 43200  # 12 часов
            status = "😋 Сытые" if not hungry else "🍽️ Голодные!"
            embed.add_field(name=f"{animal_data['name']} x{count}", value=f"📦 Даёт: {animal_data['produce']}\n💎 Цена: {animal_data['produce_price']}\n{status}", inline=True)
        
        await ctx.send(embed=embed)

# ========== КРАФТ ==========
@bot.command()
async def craft(ctx, recipe_id: str = None):
    """🔨 Скрафтить предмет"""
    if not recipe_id or recipe_id.lower() not in RECIPES:
        recipes = "\n".join([f"• {rid} - {data['name']} | {data['description']}" for rid, data in RECIPES.items()])
        await ctx.send(f"🔨 **Доступные рецепты**\n{recipes}\n\nПример: `j.craft золотой слиток`")
        return
    
    recipe = RECIPES[recipe_id.lower()]
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT inventory FROM users WHERE user_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        inv = json.loads((await cur.fetchone())[0] or "[]")
        
        # Проверка ингредиентов
        missing = []
        for ing, amount in recipe["ingredients"].items():
            count = inv.count(f"crop_{ing}") + inv.count(f"product_{ing}") + inv.count(ing)
            if count < amount:
                missing.append(f"{ing} ({count}/{amount})")
        
        if missing:
            await ctx.send(f"❌ Не хватает ингредиентов:\n" + "\n".join(missing))
            return
        
        # Удаление ингредиентов
        for ing, amount in recipe["ingredients"].items():
            for _ in range(amount):
                if f"crop_{ing}" in inv:
                    inv.remove(f"crop_{ing}")
                elif f"product_{ing}" in inv:
                    inv.remove(f"product_{ing}")
                else:
                    inv.remove(ing)
        
        # Добавление результата
        for _ in range(recipe["result_count"]):
            inv.append(recipe["result"])
        
        await db.execute('UPDATE users SET inventory=? WHERE user_id=? AND guild_id=?', (json.dumps(inv), ctx.author.id, ctx.guild.id))
        await add_xp(ctx.author.id, ctx.guild.id, recipe["xp"])
        await db.commit()
    
    await ctx.send(f"✅ Вы скрафтили {recipe['name']} x{recipe['result_count']}!\n✨ +{recipe['xp']} XP")
    await check_achievement(ctx.author.id, ctx.guild.id, "craft", 1)

@bot.command()
async def recipes(ctx):
    """📖 Показать выученные рецепты"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT recipe_id FROM recipes WHERE user_id=? AND guild_id=? AND learned=1', (ctx.author.id, ctx.guild.id))
        learned = [row[0] for row in await cur.fetchall()]
    
    embed = discord.Embed(title=f"🔨 РЕЦЕПТЫ | {ctx.author.display_name}", color=discord.Color.blue())
    learned_text = "\n".join([f"• {rid} - {RECIPES[rid]['name']}" for rid in learned if rid in RECIPES]) or "Нет выученных рецептов"
    all_text = "\n".join([f"• {rid} - {data['name']} | Нужно: {', '.join([f'{k} x{v}' for k,v in data['ingredients'].items()])}" for rid, data in RECIPES.items()])
    
    embed.add_field(name="📚 Выученные", value=learned_text[:1024], inline=False)
    embed.add_field(name="🔓 Все рецепты", value=all_text[:1024], inline=False)
    await ctx.send(embed=embed)

# ========== ФЕРМЕРСКИЕ УЛУЧШЕНИЯ ==========
@bot.command()
async def upgrade_farm(ctx, upgrade_type: str = None):
    """📈 Улучшить ферму"""
    if not upgrade_type or upgrade_type.lower() not in FARM_UPGRADES:
        upgrades = "\n".join([f"• {ut} - {data['name']} | Уровень {data['max_level']} | Старт: {data['base_cost']} 💎" for ut, data in FARM_UPGRADES.items()])
        await ctx.send(f"📈 **Улучшения фермы**\n{upgrades}\n\nПример: `j.upgrade_farm grow_speed`")
        return
    
    upgrade = upgrade_type.lower()
    upgrade_data = FARM_UPGRADES[upgrade]
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT level FROM farm_upgrades WHERE user_id=? AND guild_id=? AND upgrade_type=?', (ctx.author.id, ctx.guild.id, upgrade))
        current = await cur.fetchone()
        current_level = current[0] if current else 0
        
        if current_level >= upgrade_data["max_level"]:
            await ctx.send(f"❌ Максимальный уровень {upgrade_data['max_level']} достигнут!")
            return
        
        cost = upgrade_data["base_cost"] * (current_level + 1)
        user = await get_user(ctx.author.id, ctx.guild.id)
        
        if user[4] < cost:
            await ctx.send(f"❌ Не хватает {cost} 💎")
            return
        
        await add_balance(ctx.author.id, ctx.guild.id, -cost)
        
        if current:
            await db.execute('UPDATE farm_upgrades SET level=? WHERE user_id=? AND guild_id=? AND upgrade_type=?', (current_level + 1, ctx.author.id, ctx.guild.id, upgrade))
        else:
            await db.execute('INSERT INTO farm_upgrades (user_id, guild_id, upgrade_type, level) VALUES (?,?,?,1)', (ctx.author.id, ctx.guild.id, upgrade))
        await db.commit()
    
    await ctx.send(f"✅ {upgrade_data['name']} улучшен до {current_level + 1} уровня за {cost} 💎!")

# ========== БОНУС ЗА ПРИГЛАШЕНИЯ ==========
@bot.command()
async def bonus_invite(ctx):
    """📨 Получить бонус за приглашения"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT COUNT(*) FROM invites WHERE inviter_id=? AND guild_id=?', (ctx.author.id, ctx.guild.id))
        count = (await cur.fetchone())[0]
        
        if count == 0:
            await ctx.send("❌ Вы никого не пригласили!")
            return
        
        # 500 💎 за каждого приглашённого
        bonus = count * 500
        await add_balance(ctx.author.id, ctx.guild.id, bonus)
        await ctx.send(f"📨 Вы пригласили {count} человек!\n💰 Бонус: {bonus} 💎")
        await check_achievement(ctx.author.id, ctx.guild.id, "invite", count)

@bot.event
async def on_member_join(member):
    # Отслеживание приглашений
    invites = await member.guild.invites()
    for inv in invites:
        if inv.uses > 0:
            async with aiosqlite.connect("justice.db") as db:
                await db.execute('INSERT OR IGNORE INTO invites (inviter_id, invited_id, guild_id, invite_date) VALUES (?,?,?,?)',
                                (inv.inviter.id, member.id, member.guild.id, datetime.now().isoformat()))
                await db.commit()
            break
    
    # Остальной код приветствия
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

# ========== ТОП ПО ГОЛОСОВОМУ ОНЛАЙНУ ==========
@bot.command()
async def top_voice(ctx):
    """🎤 Топ по голосовому онлайну"""
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT user_id, voice_total_seconds FROM users WHERE guild_id=? AND voice_total_seconds>0 ORDER BY voice_total_seconds DESC LIMIT 10', (ctx.guild.id,))
        rows = await cur.fetchall()
    
    if not rows:
        await ctx.send("📊 Нет данных по голосовому онлайну")
        return
    
    msg = "**🏆 ТОП ПО ГОЛОСОВОМУ ОНЛАЙНУ**\n"
    for i, (uid, seconds) in enumerate(rows, 1):
        user = ctx.guild.get_member(uid)
        name = user.display_name if user else f"ID:{uid}"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        msg += f"{medal} {i}. {name} – {hours}ч {minutes}мин\n"
    await ctx.send(msg)

# ========== ВИСЕЛИЦА ==========
class HangmanGame:
    def __init__(self, word):
        self.word = word.upper()
        self.guessed = set()
        self.wrong = []
        self.max_wrong = 6
        self.hangman_pics = [
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

hangman_words = ["ПИТОН", "ДИСКОРД", "БОТ", "СЕРВЕР", "ПРОГРАММИРОВАНИЕ", "РАЗРАБОТЧИК", "КОМАНДА", "ИГРА", "ПОБЕДА", "УДАЧА"]
hangman_games = {}

@bot.command()
async def hangman(ctx):
    """🔤 Виселица (угадай слово)"""
    if ctx.channel.id in hangman_games:
        await ctx.send("❌ Игра уже идёт в этом канале!")
        return
    
    word = random.choice(hangman_words)
    game = HangmanGame(word)
    hangman_games[ctx.channel.id] = game
    
    embed = discord.Embed(title="🔤 ВИСЕЛИЦА", description=f"{game.hangman_pics[0]}\n\nСлово: {game.get_display()}\n\nОшибок: 0/{game.max_wrong}\nУгадайте букву!", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
async def guess(ctx, letter: str = None):
    """🔤 Угадать букву"""
    if ctx.channel.id not in hangman_games:
        await ctx.send("❌ Нет активной игры! Начните: `j.hangman`")
        return
    
    if not letter or len(letter) != 1:
        await ctx.send("❌ Введите одну букву!")
        return
    
    game = hangman_games[ctx.channel.id]
    result, status = game.guess(letter)
    
    if status == "already":
        await ctx.send(f"❌ Буква '{letter.upper()}' уже была!")
        return
    
    embed = discord.Embed(title="🔤 ВИСЕЛИЦА", color=discord.Color.blue())
    
    if game.is_won():
        embed.description = f"{game.hangman_pics[len(game.wrong)]}\n\nСлово: {game.get_display()}\n\n🎉 **ПОБЕДА!** Вы угадали слово {game.word}!"
        embed.color = discord.Color.green()
        await ctx.send(embed=embed)
        del hangman_games[ctx.channel.id]
        return
    
    if game.is_lost():
        embed.description = f"{game.hangman_pics[game.max_wrong]}\n\n💀 **ПОРАЖЕНИЕ!** Было загадано слово: {game.word}"
        embed.color = discord.Color.red()
        await ctx.send(embed=embed)
        del hangman_games[ctx.channel.id]
        return
    
    embed.description = f"{game.hangman_pics[len(game.wrong)]}\n\nСлово: {game.get_display()}\n\nОшибок: {len(game.wrong)}/{game.max_wrong}\nНеправильные буквы: {', '.join(game.wrong) if game.wrong else 'нет'}"
    await ctx.send(embed=embed)

# ========== КОРОТКИЕ ССЫЛКИ ==========
short_urls = {}

@bot.command()
async def short(ctx, *, url: str = None):
    """🔗 Сократить ссылку"""
    if not url:
        await ctx.send("❌ Введите ссылку: `j.short https://example.com`")
        return
    
    if not url.startswith("http"):
        url = "https://" + url
    
    short_code = str(hash(url))[:6]
    short_urls[short_code] = url
    
    await ctx.send(f"🔗 Короткая ссылка: `j.get {short_code}`")

@bot.command()
async def get(ctx, code: str = None):
    """🔗 Перейти по короткой ссылке"""
    if not code or code not in short_urls:
        await ctx.send("❌ Ссылка не найдена!")
        return
    
    await ctx.send(f"🔗 Ссылка: {short_urls[code]}")

# ========== КУРСЫ ВАЛЮТ ==========
@bot.command()
async def currency(ctx):
    """💱 Курсы валют (доллар, евро, юань)"""
    async with aiohttp.ClientSession() as session:
        try:
            # Центробанк РФ
            url = "https://www.cbr-xml-daily.ru/daily_json.js"
            async with session.get(url) as resp:
                data = await resp.json()
                
                usd = data["Valute"]["USD"]["Value"]
                eur = data["Valute"]["EUR"]["Value"]
                cny = data["Valute"]["CNY"]["Value"]
                
                embed = discord.Embed(title="💱 КУРСЫ ВАЛЮТ", color=discord.Color.gold())
                embed.add_field(name="🇺🇸 Доллар (USD)", value=f"{usd:.2f} ₽", inline=True)
                embed.add_field(name="🇪🇺 Евро (EUR)", value=f"{eur:.2f} ₽", inline=True)
                embed.add_field(name="🇨🇳 Юань (CNY)", value=f"{cny:.2f} ₽", inline=True)
                embed.set_footer(text="По данным ЦБ РФ")
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Ошибка получения курсов: {str(e)[:100]}")

# ========== ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ ==========
@tasks.loop(hours=168)  # Каждые 7 дней
async def weekly_report():
    """Еженедельный отчёт по активности"""
    for guild in bot.guilds:
        channel = guild.get_channel(LOGS_CHANNEL_ID)
        if not channel:
            continue
        
        week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        async with aiosqlite.connect("justice.db") as db:
            cur = await db.execute('SELECT user_id, messages, voice_minutes, casino_wins, work_count, fish_caught, crops_harvested FROM weekly_stats WHERE guild_id=? AND week_start=? ORDER BY messages DESC LIMIT 10', (guild.id, week_start))
            stats = await cur.fetchall()
        
        if not stats:
            continue
        
        embed = discord.Embed(title="📊 ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ", description=f"Статистика за неделю (с {week_start})", color=discord.Color.blue())
        
        msg_text = ""
        for i, (uid, msgs, voice, casino, work, fish, crops) in enumerate(stats[:5], 1):
            user = guild.get_member(uid)
            name = user.display_name if user else f"ID:{uid}"
            msg_text += f"{i}. {name} – {msgs} сообщ., {voice} мин в войсе, {casino} побед в казино\n"
        
        embed.add_field(name="🏆 ТОП АКТИВНОСТИ", value=msg_text or "Нет данных", inline=False)
        await channel.send(embed=embed)

# ========== ЕЖЕДНЕВНЫЕ ЗАДАНИЯ (СИСТЕМА) ==========
async def check_daily_quest(user_id, guild_id, quest_type, progress_add=1):
    """Проверка и обновление ежедневных заданий"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT quest1_id, quest1_progress, quest1_completed, quest2_id, quest2_progress, quest2_completed, quest3_id, quest3_progress, quest3_completed FROM daily_quests WHERE user_id=? AND guild_id=? AND quest_date=?', (user_id, guild_id, today))
        quests = await cur.fetchone()
        
        if not quests:
            # Выдаём 3 случайных задания
            available = list(DAILY_QUESTS.keys())
            selected = random.sample(available, min(3, len(available)))
            await db.execute('INSERT INTO daily_quests (user_id, guild_id, quest_date, quest1_id, quest2_id, quest3_id) VALUES (?,?,?,?,?,?)',
                            (user_id, guild_id, today, selected[0], selected[1], selected[2]))
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
                
                # Уведомление
                user = bot.get_user(user_id)
                if user:
                    await user.send(f"✅ **Задание выполнено!**\n{qdata['name']}\n💰 Награда: {qdata['reward']} 💎")
            
            # Обновляем прогресс
            await db.execute(f'UPDATE daily_quests SET quest{i+1}_progress=?, quest{i+1}_completed=? WHERE user_id=? AND guild_id=? AND quest_date=?',
                            (new_progress, completed[i], user_id, guild_id, today))
        
        if rewards > 0:
            await add_balance(user_id, guild_id, rewards)
        
        # Проверка на выполнение всех заданий
        if all(completed):
            user = bot.get_user(user_id)
            if user:
                await user.send("🏆 **ВЫ ВЫПОЛНИЛИ ВСЕ ЕЖЕДНЕВНЫЕ ЗАДАНИЯ!** 🏆")

@bot.command()
async def daily_quests(ctx):
    """📋 Показать ежедневные задания"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    async with aiosqlite.connect("justice.db") as db:
        cur = await db.execute('SELECT quest1_id, quest1_progress, quest1_completed, quest2_id, quest2_progress, quest2_completed, quest3_id, quest3_progress, quest3_completed FROM daily_quests WHERE user_id=? AND guild_id=? AND quest_date=?', (ctx.author.id, ctx.guild.id, today))
        quests = await cur.fetchone()
        
        if not quests:
            await ctx.send("📋 Сегодняшние задания ещё не сгенерированы! Напишите что-нибудь в чат, и они появятся.")
            return
        
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
    if TOKEN == "ВСТАВЬ_СВОЙ_ТОКЕН":
        print("❌ ВСТАВЬ ТОКЕН В ПЕРЕМЕННУЮ TOKEN!")
        exit(1)
    bot.run(TOKEN)
