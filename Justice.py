import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta
import re

# ----- НАСТРОЙКИ -----
TOKEN = os.getenv('DISCORD_TOKEN')

# Роли иерархии (ID)
ROLES = {
    'helper': 1512024218814910524,
    'moderator': 1507478655578673152,
    'admin': 1502637204537737306,
    'head_admin': 1507479670130741368,
    'curator': 1512520499941605618,
    'co_owner': 1502637204537737308,
    'owner': 1504402262833758228,
}

# ID
BOG_ROLE_ID = 1521944293135351829  # Боженька (роль)
OWNER_ID = 1504402262833758228     # Владелец
BOG_USER_ID = 1062336593588912199  # Пользователь за которым следим

LOG_CHANNEL_ID = 1502637205187723433
REPORT_CHANNEL_ID = 1502637205187723433

# НАСТРОЙКИ ЭКОНОМИКИ
MESSAGES_PER_SHARD = 10        # 10 сообщений = 1 осколок
VOICE_HOUR_SHARDS = 5          # 1 час в войсе = 5 осколков
COOLDOWN_SECONDS = 60          # Защита от спама (1 минута)
VOICE_CHECK_INTERVAL = 30      # Проверка голосовых каждые 30 секунд

# ----- ИНИЦИАЛИЗАЦИЯ БОТА -----
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='j.', intents=intents)
bot.remove_command('help')

# ----- ФАЙЛЫ ДЛЯ ХРАНЕНИЯ -----
DATA_FILE = 'data.json'
BACKUP_FOLDER = 'backups'
REPORT_FOLDER = 'reports'

for folder in [BACKUP_FOLDER, REPORT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'warns': {}, 
        'balance': {}, 
        'daily': {},
        'exchange_rate': 5.0,
        'messages_count': {},
        'last_message_time': {},
        'voice_time': {},
        'voice_last_check': {},
        'voice_total_time': {},
        'last_status_message_id': None
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# ----- ХРАНИЛИЩЕ СТАТУСА -----
last_status = None
bog_member = None
last_status_message = None

# ----- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ -----
async def get_role_by_hierarchy(ctx):
    roles = [ROLES['owner'], ROLES['co_owner'], ROLES['curator'],
             ROLES['head_admin'], ROLES['admin'], ROLES['moderator'], ROLES['helper']]
    for role_id in roles:
        if discord.utils.get(ctx.author.roles, id=role_id):
            return role_id
    return None

async def get_role_by_hierarchy_for_user(user):
    roles = [ROLES['owner'], ROLES['co_owner'], ROLES['curator'],
             ROLES['head_admin'], ROLES['admin'], ROLES['moderator'], ROLES['helper']]
    for role_id in roles:
        if discord.utils.get(user.roles, id=role_id):
            return role_id
    return None

async def check_hierarchy(ctx, target):
    author_role = await get_role_by_hierarchy(ctx)
    target_role = await get_role_by_hierarchy_for_user(target)
    if not author_role:
        return False
    if not target_role:
        return True
    roles_list = [ROLES['owner'], ROLES['co_owner'], ROLES['curator'],
                  ROLES['head_admin'], ROLES['admin'], ROLES['moderator'], ROLES['helper']]
    return roles_list.index(author_role) < roles_list.index(target_role)

def is_owner_or_bog(ctx):
    if ctx.author.id == OWNER_ID:
        return True
    if discord.utils.get(ctx.author.roles, id=BOG_ROLE_ID):
        return True
    return False

def is_owner_only(ctx):
    return ctx.author.id == OWNER_ID

def can_manage_economy(ctx):
    return is_owner_or_bog(ctx)

def format_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}ч {minutes}м {secs}с"
    elif minutes > 0:
        return f"{minutes}м {secs}с"
    else:
        return f"{secs}с"

# ----- ГОЛОСОВОЙ ТРЕКЕР -----
@tasks.loop(seconds=VOICE_CHECK_INTERVAL)
async def voice_tracker():
    for guild in bot.guilds:
        for voice_channel in guild.voice_channels:
            for member in voice_channel.members:
                if member.bot:
                    continue
                
                user_id = str(member.id)
                current_time = datetime.now().timestamp()
                
                if user_id not in data['voice_time']:
                    data['voice_time'][user_id] = 0
                if user_id not in data['voice_total_time']:
                    data['voice_total_time'][user_id] = 0
                if user_id not in data['voice_last_check']:
                    data['voice_last_check'][user_id] = current_time
                
                time_delta = current_time - data['voice_last_check'][user_id]
                
                if time_delta >= VOICE_CHECK_INTERVAL:
                    data['voice_time'][user_id] += time_delta
                    data['voice_total_time'][user_id] += time_delta
                    data['voice_last_check'][user_id] = current_time
                    
                    if data['voice_time'][user_id] >= 3600:
                        shards_earned = int(data['voice_time'][user_id] // 3600) * VOICE_HOUR_SHARDS
                        if shards_earned > 0:
                            if user_id not in data['balance']:
                                data['balance'][user_id] = 0
                            data['balance'][user_id] += shards_earned
                            data['voice_time'][user_id] = data['voice_time'][user_id] % 3600
                            
                            save_data(data)
                            
                            try:
                                embed = discord.Embed(
                                    title=f"🎙️ +{shards_earned} Осколков за голос!",
                                    description=f"Вы получили {shards_earned} осколков за {shards_earned // VOICE_HOUR_SHARDS} час(ов) в голосовом канале!\nВсего осколков: {data['balance'][user_id]} 💎",
                                    color=0x00ff00
                                )
                                await member.send(embed=embed)
                            except:
                                pass
                            
                            save_data(data)

# ----- ОБРАБОТЧИК СООБЩЕНИЙ -----
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if not message.guild:
        return
    
    user_id = str(message.author.id)
    current_time = datetime.now().timestamp()
    
    last_time = data['last_message_time'].get(user_id, 0)
    if current_time - last_time < COOLDOWN_SECONDS:
        await bot.process_commands(message)
        return
    
    data['last_message_time'][user_id] = current_time
    
    if user_id not in data['messages_count']:
        data['messages_count'][user_id] = 0
    data['messages_count'][user_id] += 1
    
    if data['messages_count'][user_id] >= MESSAGES_PER_SHARD:
        if user_id not in data['balance']:
            data['balance'][user_id] = 0
        data['balance'][user_id] += 1
        data['messages_count'][user_id] = 0
        save_data(data)
        
        try:
            embed = discord.Embed(
                title="💎 +1 Осколок!",
                description=f"Вы получили 1 осколок за активность!\nВсего осколков: {data['balance'][user_id]} 💎",
                color=0xffd700
            )
            await message.channel.send(f"{message.author.mention}", embed=embed, delete_after=5)
        except:
            pass
    
    await bot.process_commands(message)

# ----- СОБЫТИЕ ПРИ ВХОДЕ/ВЫХОДЕ ИЗ ГОЛОСОВОГО КАНАЛА -----
@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    user_id = str(member.id)
    current_time = datetime.now().timestamp()
    
    if after.channel is not None and before.channel is None:
        data['voice_last_check'][user_id] = current_time
        if user_id not in data['voice_time']:
            data['voice_time'][user_id] = 0
        if user_id not in data['voice_total_time']:
            data['voice_total_time'][user_id] = 0
        save_data(data)
    
    elif before.channel is not None and after.channel is None:
        if user_id in data['voice_last_check']:
            time_delta = current_time - data['voice_last_check'][user_id]
            if time_delta > 0:
                data['voice_time'][user_id] = data['voice_time'].get(user_id, 0) + time_delta
                data['voice_total_time'][user_id] = data['voice_total_time'].get(user_id, 0) + time_delta
                
                if data['voice_time'][user_id] >= 3600:
                    shards_earned = int(data['voice_time'][user_id] // 3600) * VOICE_HOUR_SHARDS
                    if shards_earned > 0:
                        if user_id not in data['balance']:
                            data['balance'][user_id] = 0
                        data['balance'][user_id] += shards_earned
                        data['voice_time'][user_id] = data['voice_time'][user_id] % 3600
                        
                        save_data(data)
                        
                        try:
                            embed = discord.Embed(
                                title=f"🎙️ +{shards_earned} Осколков за голос!",
                                description=f"Вы получили {shards_earned} осколков за голосовую активность!\nВсего осколков: {data['balance'][user_id]} 💎",
                                color=0x00ff00
                            )
                            await member.send(embed=embed)
                        except:
                            pass
            save_data(data)

# ----- КОМАНДЫ (ВСЕ НА АНГЛИЙСКОМ) -----

# HELP
@bot.command(name='help', aliases=['h'])
async def custom_help(ctx, command_name: str = None):
    """Показать список команд"""
    if command_name:
        cmd = bot.get_command(command_name.lower())
        if cmd:
            embed = discord.Embed(
                title=f"📖 Команда: j.{cmd.name}",
                description=cmd.help or "Нет описания",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
            return
        else:
            await ctx.send(f"❌ Команда `{command_name}` не найдена.")
            return
    
    embed = discord.Embed(
        title="🌟 Меню помощи бота Justice",
        description=f"**Префикс: `j.`**\n**Курс:** 1 ₽ = {data.get('exchange_rate', 5)} 💎\n\n💬 **{MESSAGES_PER_SHARD} сообщений = 1 осколок**\n🎙️ **1 час в войсе = {VOICE_HOUR_SHARDS} осколков**",
        color=0x5865F2
    )
    
    embed.add_field(
        name="🛡️ Модерация",
        value="""**mute** - Замутить пользователя\n**unmute** - Размутить\n**ban** - Забанить\n**kick** - Кикнуть\n**warn** - Выдать варн\n**warns** - Просмотр варнов\n**unwarn** - Снять варн\n**clear** - Очистить канал""",
        inline=False
    )
    
    embed.add_field(
        name="💰 Экономика",
        value=f"""**balance (bal)** - Баланс\n**daily** - Ежедневный бонус\n**add** - Выдать осколки (Владелец/Боженька)\n**remove** - Снять осколки (Владелец/Боженька)\n**rate** - Курс\n**setrate** - Установить курс (Владелец/Боженька)\n**msgstats** - Статистика сообщений\n**voicestats** - Статистика голоса\n**topvoice** - Топ по голосу (Владелец/Боженька)\n**topmsg** - Топ по сообщениям (Владелец/Боженька)""",
        inline=False
    )
    
    embed.add_field(
        name="📊 Отчеты",
        value="""**report** - Создать отчет (Владелец/Боженька) - придет в ЛС\n**backup** - Бэкап данных (Владелец)\n**restore** - Восстановить (Владелец)\n**stats** - Статистика (Владелец/Боженька)\n**find** - Найти пользователя (Владелец/Боженька)""",
        inline=False
    )
    
    embed.set_footer(text=f"Запросил: {ctx.author.display_name}")
    await ctx.send(embed=embed)

# STATUS
@bot.command(name='status', aliases=['stats'])
async def bot_status(ctx):
    global bog_member
    
    embed = discord.Embed(
        title="📊 Статус бота",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="🤖 Бот",
        value=f"**Пинг:** {round(bot.latency * 1000)}ms\n**Серверов:** {len(bot.guilds)}",
        inline=False
    )
    
    if bog_member:
        status_text = {
            discord.Status.online: "🟢 В сети",
            discord.Status.idle: "🟡 Отошел",
            discord.Status.dnd: "🔴 Не беспокоить",
            discord.Status.offline: "⚫ Не в сети"
        }
        embed.add_field(
            name="👁️ Боженька",
            value=status_text.get(bog_member.status, "❓ Неизвестно"),
            inline=False
        )
    
    total_balance = sum(data['balance'].values()) if data['balance'] else 0
    total_voice = sum(data['voice_total_time'].values()) if data['voice_total_time'] else 0
    total_messages = sum(data['messages_count'].values()) if data['messages_count'] else 0
    rate = data.get('exchange_rate', 5)
    total_rubles = round(total_balance / rate, 2) if rate > 0 else 0
    
    embed.add_field(
        name="💰 Экономика",
        value=f"**Всего осколков:** {total_balance} 💎\n**Пользователей:** {len(data['balance'])}\n**Курс:** 1 ₽ = {rate} 💎",
        inline=False
    )
    
    embed.add_field(
        name="📊 Активность",
        value=f"**Всего сообщений:** {total_messages}\n**Всего в войсе:** {format_time(total_voice)}\n**За сообщения:** {MESSAGES_PER_SHARD} = 1 💎\n**За голос:** 1 час = {VOICE_HOUR_SHARDS} 💎",
        inline=False
    )
    
    await ctx.send(embed=embed)

# RATE
@bot.command(name='rate', aliases=['курс'])
async def show_rate(ctx):
    rate = data.get('exchange_rate', 5)
    embed = discord.Embed(
        title="💱 Текущий курс",
        description=f"**1 рубль = {rate} осколков** 💎\n**1 осколок = {round(1/rate, 2)} рублей**\n\n💬 **{MESSAGES_PER_SHARD} сообщений = 1 осколок**\n🎙️ **1 час в войсе = {VOICE_HOUR_SHARDS} осколков**",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

# SETRATE
@bot.command(name='setrate', aliases=['установитькурс'])
@commands.check(is_owner_or_bog)
async def set_exchange_rate(ctx, rate: str):
    """Установить курс (можно дробный, например: 0.5 или 2.5)"""
    try:
        rate = float(rate.replace(',', '.'))
    except ValueError:
        await ctx.send("❌ Неверный формат! Используйте число, например: `0.5`, `2`, `3.5`")
        return
    
    if rate <= 0:
        await ctx.send("❌ Курс должен быть положительным!")
        return
    
    old_rate = data.get('exchange_rate', 5)
    data['exchange_rate'] = rate
    save_data(data)
    
    embed = discord.Embed(
        title="💱 Курс обновлен!",
        description=f"**Был:** 1 ₽ = {old_rate} 💎\n**Стал:** 1 ₽ = {rate} 💎",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

# BALANCE
@bot.command(name='balance', aliases=['bal'])
async def balance(ctx, member: discord.Member = None):
    """Показать баланс пользователя"""
    if member is None:
        member = ctx.author
    
    balance = data['balance'].get(str(member.id), 0)
    rate = data.get('exchange_rate', 5)
    rubles = round(balance / rate, 2) if rate > 0 else 0
    
    embed = discord.Embed(title="💰 Баланс", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Осколки", value=f"{balance} 💎")
    embed.add_field(name="Рубли", value=f"{rubles} ₽")
    embed.set_footer(text=f"Курс: 1 ₽ = {rate} 💎")
    await ctx.send(embed=embed)

# ADD
@bot.command(name='add')
@commands.check(can_manage_economy)
async def add_shards(ctx, member: discord.Member, amount: int):
    """Выдать осколки (Владелец/Боженька)"""
    if amount <= 0:
        await ctx.send("❌ Количество должно быть положительным!")
        return
    
    if str(member.id) not in data['balance']:
        data['balance'][str(member.id)] = 0
    data['balance'][str(member.id)] += amount
    save_data(data)
    
    rate = data.get('exchange_rate', 5)
    rubles = round(amount / rate, 2)
    
    embed = discord.Embed(title="➕ Выдача осколков", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Получено", value=f"+{amount} 💎 ({rubles} ₽)")
    embed.add_field(name="Новый баланс", value=f"{data['balance'][str(member.id)]} 💎")
    embed.set_footer(text=f"Выдал: {ctx.author.display_name}")
    await ctx.send(embed=embed)

# REMOVE
@bot.command(name='remove')
@commands.check(can_manage_economy)
async def remove_shards(ctx, member: discord.Member, amount: int):
    """Снять осколки (Владелец/Боженька)"""
    if amount <= 0:
        await ctx.send("❌ Количество должно быть положительным!")
        return
    
    if str(member.id) not in data['balance']:
        data['balance'][str(member.id)] = 0
    
    if data['balance'][str(member.id)] < amount:
        await ctx.send(f"❌ У {member.mention} недостаточно осколков!")
        return
    
    data['balance'][str(member.id)] -= amount
    save_data(data)
    
    rate = data.get('exchange_rate', 5)
    rubles = round(amount / rate, 2)
    
    embed = discord.Embed(title="➖ Снятие осколков", color=0xff0000)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Снято", value=f"-{amount} 💎 ({rubles} ₽)")
    embed.add_field(name="Новый баланс", value=f"{data['balance'][str(member.id)]} 💎")
    embed.set_footer(text=f"Снял: {ctx.author.display_name}")
    await ctx.send(embed=embed)

# DAILY
@bot.command(name='daily')
async def daily(ctx):
    """Ежедневный бонус"""
    user_id = str(ctx.author.id)
    today = datetime.now().date().isoformat()
    
    if user_id in data['daily'] and data['daily'][user_id] == today:
        await ctx.send("❌ Вы уже получили бонус сегодня!")
        return
    
    if user_id not in data['balance']:
        data['balance'][user_id] = 0
    data['balance'][user_id] += 5
    data['daily'][user_id] = today
    save_data(data)
    
    rate = data.get('exchange_rate', 5)
    rubles = round(5 / rate, 2)
    
    embed = discord.Embed(title="🎉 Ежедневный бонус", color=0xffd700)
    embed.add_field(name="Получено", value=f"+5 💎 ({rubles} ₽)")
    embed.add_field(name="Новый баланс", value=f"{data['balance'][user_id]} 💎")
    await ctx.send(embed=embed)

# MSGSTATS
@bot.command(name='msgstats', aliases=['сообщения'])
async def message_stats(ctx, member: discord.Member = None):
    """Показать сколько сообщений до следующего осколка"""
    if member is None:
        member = ctx.author
    
    user_id = str(member.id)
    msg_count = data['messages_count'].get(user_id, 0)
    needed = MESSAGES_PER_SHARD - msg_count
    
    embed = discord.Embed(
        title="📊 Статистика сообщений",
        color=0x00ff00
    )
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Сообщений отправлено", value=f"{msg_count} / {MESSAGES_PER_SHARD}")
    embed.add_field(name="До следующего осколка", value=f"{needed} сообщений")
    embed.set_footer(text=f"1 осколок за каждые {MESSAGES_PER_SHARD} сообщений")
    await ctx.send(embed=embed)

# VOICESTATS
@bot.command(name='voicestats', aliases=['войсстат', 'voice'])
async def voice_stats(ctx, member: discord.Member = None):
    """Показать статистику в голосовых каналах"""
    if member is None:
        member = ctx.author
    
    user_id = str(member.id)
    voice_seconds = data['voice_time'].get(user_id, 0)
    total_seconds = data['voice_total_time'].get(user_id, 0)
    
    if member.voice and member.voice.channel:
        current_time = datetime.now().timestamp()
        last_check = data['voice_last_check'].get(user_id, current_time)
        current_session = current_time - last_check
        voice_seconds += current_session
    
    shards_earned = (total_seconds // 3600) * VOICE_HOUR_SHARDS
    
    embed = discord.Embed(
        title="🎙️ Статистика голосовых каналов",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="Пользователь", value=member.mention, inline=False)
    embed.add_field(name="⏱️ Текущая сессия", value=format_time(voice_seconds), inline=True)
    embed.add_field(name="📊 Всего времени", value=format_time(total_seconds + voice_seconds), inline=True)
    embed.add_field(name="💎 Заработано осколков", value=f"{shards_earned} 💎", inline=True)
    embed.add_field(name="📈 Прогресс до следующего осколка", value=f"{format_time(voice_seconds % 3600)} / 1ч", inline=False)
    embed.set_footer(text=f"1 час в войсе = {VOICE_HOUR_SHARDS} осколков")
    
    await ctx.send(embed=embed)

# TOPVOICE
@bot.command(name='topvoice', aliases=['топвойс'])
@commands.check(is_owner_or_bog)
async def top_voice(ctx):
    """Топ пользователей по времени в голосовых каналах (Владелец/Боженька)"""
    
    if not data['voice_total_time']:
        await ctx.send("📊 Нет данных о голосовой активности!")
        return
    
    sorted_users = sorted(data['voice_total_time'].items(), key=lambda x: x[1], reverse=True)[:10]
    
    embed = discord.Embed(
        title="🎙️ Топ-10 по времени в войсе",
        color=0x5865F2,
        timestamp=datetime.now()
    )
    
    text = ""
    for i, (user_id, seconds) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.name
        except Exception:
            name = "Неизвестный"
        
        shards = (seconds // 3600) * VOICE_HOUR_SHARDS
        text += f"{i}. **{name}** - {format_time(seconds)} ({shards} 💎)\n"
    
    embed.description = text if text else "Нет данных"
    await ctx.send(embed=embed)

# TOPMSG
@bot.command(name='topmsg', aliases=['топсообщений'])
@commands.check(is_owner_or_bog)
async def top_messages(ctx):
    """Топ пользователей по количеству сообщений (Владелец/Боженька)"""
    
    if not data['messages_count']:
        await ctx.send("📊 Нет данных о сообщениях!")
        return
    
    sorted_users = sorted(data['messages_count'].items(), key=lambda x: x[1], reverse=True)[:10]
    
    embed = discord.Embed(
        title="🏆 Топ-10 по активности в чате",
        color=0xffd700,
        timestamp=datetime.now()
    )
    
    text = ""
    for i, (user_id, count) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.name
        except Exception:
            name = "Неизвестный"
        
        shards_earned = count // MESSAGES_PER_SHARD
        text += f"{i}. **{name}** - {count} сообщений ({shards_earned} 💎)\n"
    
    embed.description = text if text else "Нет данных"
    await ctx.send(embed=embed)

# REPORT
@bot.command(name='report', aliases=['отчет'])
@commands.check(is_owner_or_bog)
async def create_report(ctx):
    """Создать отчет в TXT - отправляется в ЛС (Владелец/Боженька)"""
    
    await ctx.send("📊 **Создаю отчет... Ожидайте в личных сообщениях!**")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    rate = data.get('exchange_rate', 5)
    
    total_users = len(data['balance'])
    total_shards = sum(data['balance'].values())
    total_rubles = round(total_shards / rate, 2) if rate > 0 else 0
    
    txt_file = f"{REPORT_FOLDER}/report_{timestamp}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("📊 СТАТИСТИКА СЕРВЕРА\n")
        f.write("="*70 + "\n\n")
        f.write(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write(f"💱 Курс: 1 ₽ = {rate} 💎\n")
        f.write(f"💬 За активность: {MESSAGES_PER_SHARD} сообщений = 1 💎\n")
        f.write(f"🎙️ За голос: 1 час = {VOICE_HOUR_SHARDS} 💎\n\n")
        f.write("="*70 + "\n")
        f.write("📈 ОБЩАЯ СТАТИСТИКА\n")
        f.write("="*70 + "\n")
        f.write(f"👥 Всего пользователей: {total_users}\n")
        f.write(f"💎 Всего осколков: {total_shards}\n")
        f.write(f"💰 Всего рублей: {total_rubles} ₽\n\n")
        
        total_messages = sum(data['messages_count'].values()) if data['messages_count'] else 0
        total_voice = sum(data['voice_total_time'].values()) if data['voice_total_time'] else 0
        total_voice_hours = total_voice // 3600
        
        f.write("="*70 + "\n")
        f.write("💬 СТАТИСТИКА АКТИВНОСТИ\n")
        f.write("="*70 + "\n")
        f.write(f"📝 Всего сообщений: {total_messages}\n")
        f.write(f"💎 Заработано осколков за сообщения: {total_messages // MESSAGES_PER_SHARD}\n")
        f.write(f"🎙️ Всего часов в войсе: {total_voice_hours}\n")
        f.write(f"💎 Заработано осколков за голос: {total_voice_hours * VOICE_HOUR_SHARDS}\n\n")
        
        f.write("="*70 + "\n")
        f.write("👥 ВСЕ ПОЛЬЗОВАТЕЛИ (по убыванию баланса)\n")
        f.write("="*70 + "\n")
        f.write(f"{'ID':<20} | {'Имя':<25} | {'Осколки':<10} | {'Рубли':<10} | {'Daily':<12} | {'Варны'}\n")
        f.write("-"*70 + "\n")
        
        for user_id, balance in sorted(data['balance'].items(), key=lambda x: x[1], reverse=True):
            try:
                user = bot.get_user(int(user_id)) or await bot.fetch_user(int(user_id))
                username = user.name if user else "Неизвестный"
            except Exception:
                username = "Неизвестный"
            
            rubles = round(balance / rate, 2) if rate > 0 else 0
            daily_date = data['daily'].get(str(user_id), 'Нет')
            warns_count = len(data['warns'].get(str(user_id), {}))
            f.write(f"{user_id:<20} | {username[:24]:<25} | {balance:<10} | {rubles:<10} | {daily_date:<12} | {warns_count}\n")
    
    try:
        embed = discord.Embed(
            title="📊 Отчет готов!",
            description=f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n**Пользователей:** {total_users}\n**Всего осколков:** {total_shards} 💎",
            color=0x5865F2
        )
        
        await ctx.author.send(embed=embed)
        
        with open(txt_file, 'rb') as f:
            await ctx.author.send(file=discord.File(f, f"report_{timestamp}.txt"))
        
        await ctx.send(f"✅ **Отчет отправлен в личные сообщения!**")
        
    except discord.Forbidden:
        await ctx.send("❌ **Не могу отправить отчет в ЛС!** Включите личные сообщения от участников сервера в настройках Discord.")
    except Exception as e:
        await ctx.send(f"❌ Ошибка при отправке: {e}")

# FIND
@bot.command(name='find', aliases=['найти'])
@commands.check(is_owner_or_bog)
async def find_user(ctx, user_id: int):
    """Найти пользователя по ID (Владелец/Боженька)"""
    uid = str(user_id)
    if uid not in data['balance']:
        await ctx.send(f"❌ Пользователь {user_id} не найден!")
        return
    
    try:
        user = await bot.fetch_user(user_id)
        name = user.name
    except Exception:
        name = "Неизвестный"
    
    balance = data['balance'][uid]
    rate = data.get('exchange_rate', 5)
    rubles = round(balance / rate, 2) if rate > 0 else 0
    daily = data['daily'].get(uid, 'Нет')
    warns = len(data['warns'].get(uid, {}))
    
    embed = discord.Embed(title=f"👤 {name}", color=0x00ff00)
    embed.add_field(name="ID", value=user_id, inline=True)
    embed.add_field(name="💎 Баланс", value=f"{balance} ({rubles} ₽)", inline=True)
    embed.add_field(name="📅 Daily", value=daily, inline=True)
    embed.add_field(name="⚠️ Варнов", value=warns, inline=True)
    await ctx.send(embed=embed)

# ----- АДМИН КОМАНДЫ (ВСЕ НА АНГЛИЙСКОМ) -----

# MUTE
@bot.command(name='mute', aliases=['мут'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def mute(ctx, member: discord.Member, time: str, *, reason="Не указана"):
    """Замутить пользователя"""
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя замутить этого пользователя!")
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя мутить Боженьку!")
        return
    
    time_seconds = 0
    match = re.match(r'(\d+)([smhd])', time)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if unit == 's': time_seconds = value
        elif unit == 'm': time_seconds = value * 60
        elif unit == 'h': time_seconds = value * 3600
        elif unit == 'd': time_seconds = value * 86400
    else:
        await ctx.send("❌ Формат: 10s, 5m, 2h, 1d")
        return
    
    await member.timeout(timedelta(seconds=time_seconds), reason=reason)
    embed = discord.Embed(title="🔇 Мут", color=0xff0000)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Время", value=time)
    embed.add_field(name="Причина", value=reason)
    await ctx.send(embed=embed)

# UNMUTE
@bot.command(name='unmute', aliases=['размут'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def unmute(ctx, member: discord.Member):
    """Размутить пользователя"""
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя размутить!")
        return
    await member.timeout(None)
    await ctx.send(f"✅ {member.mention} размучен!")

# BAN
@bot.command(name='ban', aliases=['бан'])
@commands.has_any_role(*[ROLES['admin'], ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def ban(ctx, member: discord.Member, *, reason="Не указана"):
    """Забанить пользователя"""
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя забанить!")
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя банить Боженьку!")
        return
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member.mention} забанен! Причина: {reason}")

# KICK
@bot.command(name='kick', aliases=['кик'])
@commands.has_any_role(*[ROLES['moderator'], ROLES['admin'], ROLES['head_admin'], 
                         ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def kick(ctx, member: discord.Member, *, reason="Не указана"):
    """Кикнуть пользователя"""
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя кикнуть!")
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя кикать Боженьку!")
        return
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.mention} кикнут! Причина: {reason}")

# WARN
@bot.command(name='warn', aliases=['варн'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def warn(ctx, member: discord.Member, time: str, *, reason="Не указана"):
    """Выдать варн пользователю"""
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя выдать варн!")
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя варнить Боженьку!")
        return
    
    time_seconds = 0
    match = re.match(r'(\d+)([smhd])', time)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if unit == 's': time_seconds = value
        elif unit == 'm': time_seconds = value * 60
        elif unit == 'h': time_seconds = value * 3600
        elif unit == 'd': time_seconds = value * 86400
    else:
        await ctx.send("❌ Формат: 10s, 5m, 2h, 1d")
        return
    
    warn_id = str(int(datetime.now().timestamp()))
    warn_data = {
        'reason': reason,
        'moderator': ctx.author.id,
        'time': time,
        'expires': (datetime.now() + timedelta(seconds=time_seconds)).isoformat()
    }
    
    if str(member.id) not in data['warns']:
        data['warns'][str(member.id)] = {}
    data['warns'][str(member.id)][warn_id] = warn_data
    save_data(data)
    
    embed = discord.Embed(title="⚠️ Варн", color=0xffff00)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Время", value=time)
    embed.add_field(name="Причина", value=reason)
    await ctx.send(embed=embed)

# WARNS
@bot.command(name='warns', aliases=['варны'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def warns(ctx, member: discord.Member):
    """Просмотр варнов пользователя"""
    if str(member.id) not in data['warns'] or not data['warns'][str(member.id)]:
        await ctx.send(f"✅ У {member.mention} нет варнов.")
        return
    
    embed = discord.Embed(title=f"📋 Варны {member.display_name}", color=0xffff00)
    for warn_id, warn in data['warns'][str(member.id)].items():
        expires = datetime.fromisoformat(warn['expires'])
        if expires > datetime.now():
            embed.add_field(
                name=f"ID: {warn_id[:6]}",
                value=f"Причина: {warn['reason']}\nИстекает: {expires.strftime('%d.%m.%Y %H:%M')}",
                inline=False
            )
    
    if not embed.fields:
        await ctx.send(f"✅ У {member.mention} нет активных варнов.")
    else:
        await ctx.send(embed=embed)

# UNWARN
@bot.command(name='unwarn', aliases=['разварн'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def unwarn(ctx, member: discord.Member, warn_id: str):
    """Снять варн с пользователя"""
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя снять варн!")
        return
    
    if str(member.id) in data['warns'] and warn_id in data['warns'][str(member.id)]:
        del data['warns'][str(member.id)][warn_id]
        save_data(data)
        await ctx.send(f"✅ Варн снят с {member.mention}")
    else:
        await ctx.send(f"❌ Варн не найден!")

# CLEAR
@bot.command(name='clear', aliases=['очистить', 'cls'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def clear_channel(ctx, amount: int = None):
    """Очистить канал (удалить сообщения)"""
    if amount is None:
        await ctx.send("❌ Укажите количество. Пример: `j.clear 50`")
        return
    
    if amount < 1 or amount > 100:
        await ctx.send("❌ Можно удалить от 1 до 100 сообщений!")
        return
    
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ Удалено {len(deleted) - 1} сообщений!", delete_after=3)
    except Exception:
        await ctx.send("❌ Ошибка при удалении!")

# BACKUP
@bot.command(name='backup', aliases=['бэкап'])
@commands.check(is_owner_only)
async def create_backup(ctx):
    """Создать бэкап данных (Только владелец)"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_backup = f"{BACKUP_FOLDER}/backup_{timestamp}.json"
    
    with open(json_backup, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    channel = bot.get_channel(LOG_CHANNEL_ID) or ctx.channel
    
    embed = discord.Embed(
        title="💾 Бэкап создан!",
        description=f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
        color=0x00ff00
    )
    await channel.send(embed=embed)
    
    with open(json_backup, 'rb') as f:
        await channel.send(file=discord.File(f, f"backup_{timestamp}.json"))
    
    await ctx.send(f"✅ **Бэкап создан!**")

# RESTORE
@bot.command(name='restore', aliases=['восстановить'])
@commands.check(is_owner_only)
async def restore_backup(ctx, backup_name: str = None):
    """Восстановить данные из бэкапа (Только владелец)"""
    if backup_name is None:
        backups = sorted([f for f in os.listdir(BACKUP_FOLDER) if f.endswith('.json')])
        if not backups:
            await ctx.send("❌ Нет бэкапов!")
            return
        
        embed = discord.Embed(title="📋 Бэкапы", color=0x5865F2)
        for i, backup in enumerate(backups[-5:], 1):
            embed.add_field(name=f"{i}. {backup}", value=f"`{backup}`", inline=False)
        await ctx.send(embed=embed)
        return
    
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)
    if not os.path.exists(backup_path):
        await ctx.send(f"❌ Бэкап {backup_name} не найден!")
        return
    
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        global data
        data = backup_data
        save_data(data)
        
        embed = discord.Embed(
            title="✅ Данные восстановлены!",
            description=f"**Из бэкапа:** {backup_name}\n**Пользователей:** {len(data['balance'])}",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

# ----- СЛЕЖЕНИЕ ЗА СТАТУСОМ -----
@tasks.loop(seconds=5)
async def status_check():
    global last_status, bog_member, last_status_message
    
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return
    
    if not bog_member:
        if bot.guilds:
            guild = bot.guilds[0]
            bog_member = guild.get_member(BOG_USER_ID)
            if bog_member:
                last_status = bog_member.status
                msg = await send_status_update(channel, bog_member.status)
                if msg:
                    last_status_message = msg
                    data['last_status_message_id'] = msg.id
                    save_data(data)
        return
    
    try:
        current_status = bog_member.status
        if current_status != last_status:
            if last_status_message:
                try:
                    await last_status_message.delete()
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            
            msg = await send_status_update(channel, current_status)
            if msg:
                last_status_message = msg
                data['last_status_message_id'] = msg.id
                save_data(data)
            
            last_status = current_status
    except Exception as e:
        print(f"Ошибка: {e}")

async def send_status_update(channel, status):
    embed = discord.Embed(title="👁️ Статус Боженьки")
    
    if status == discord.Status.online:
        embed.description = "🌅 **Боженька готов услышать ваши мольбы!**\nОн в сети и ждёт ваши просьбы."
        embed.color = 0x00ff00
    elif status == discord.Status.idle:
        embed.description = "💤 **Боженьку лучше не тревожить!**\nОн отдыхает, иначе навлечёте на себя гнев божий."
        embed.color = 0xffff00
    elif status == discord.Status.dnd:
        embed.description = "🔇 **Боженька занят!**\nНе тревожьте его сейчас, иначе будете наказаны."
        embed.color = 0xff0000
    else:
        embed.description = "🌆 **Боженька не в сети!**\nЕго лучше не тревожить. Похоже, он уехал в Вегас 🎰"
        embed.color = 0x808080
    
    embed.set_footer(text=f"🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}")
    
    if bog_member:
        embed.set_thumbnail(url=bog_member.display_avatar.url)
    
    return await channel.send(embed=embed)

# ----- ОБРАБОТЧИК ОШИБОК -----
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("❌ У вас нет прав для использования этой команды.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ У вас недостаточно прав.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Неверный аргумент. Проверьте ввод.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ У вас нет прав для этой команды.")
    else:
        await ctx.send(f"❌ Ошибка: {error}")
        print(f"Ошибка: {error}")

# ----- СОБЫТИЕ ГОТОВНОСТИ -----
@bot.event
async def on_ready():
    global bog_member, last_status, last_status_message
    
    print(f'✅ Бот {bot.user} готов!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="за Боженькой"))
    
    if bot.guilds:
        guild = bot.guilds[0]
        bog_member = guild.get_member(BOG_USER_ID)
        
        if bog_member:
            last_status = bog_member.status
            print(f"📊 Начальный статус Боженьки: {last_status}")
            
            channel = bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                saved_msg_id = data.get('last_status_message_id')
                if saved_msg_id:
                    try:
                        old_msg = await channel.fetch_message(saved_msg_id)
                        if old_msg:
                            last_status_message = old_msg
                            await send_status_update(channel, last_status)
                            print("✅ Восстановлено предыдущее сообщение о статусе")
                    except Exception as e:
                        print(f"Не удалось восстановить сообщение: {e}")
                        msg = await send_status_update(channel, last_status)
                        if msg:
                            last_status_message = msg
                            data['last_status_message_id'] = msg.id
                            save_data(data)
                else:
                    msg = await send_status_update(channel, last_status)
                    if msg:
                        last_status_message = msg
                        data['last_status_message_id'] = msg.id
                        save_data(data)
    
    voice_tracker.start()
    status_check.start()
    print("✅ Статус-трекер и войс-трекер запущены!")

# ----- ЗАПУСК -----
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ОШИБКА: Токен не найден! Установите переменную DISCORD_TOKEN")
        exit(1)
    bot.run(TOKEN)
