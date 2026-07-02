import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta
import re

# ----- Настройки -----
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
    'economy': 1521944293135351829,
}

BOG_ID = 1062336593588912199
LOG_CHANNEL_ID = 1502637205187723433

# ----- Инициализация бота -----
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='j.', intents=intents)
bot.remove_command('help')

# ----- Файлы для хранения -----
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'warns': {}, 
        'balance': {}, 
        'daily': {},
        'exchange_rate': 5  # По умолчанию 5 осколков = 1 рубль
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# ----- Хранилище последнего статуса -----
last_status = None
bog_member = None

# ----- Вспомогательные функции -----
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
    """Проверка, является ли пользователь владельцем или Боженькой"""
    return ctx.author.id == ROLES['owner'] or ctx.author.id == BOG_ID

# ----- КАСТОМНАЯ КОМАНДА HELP -----
@bot.command(name='help', aliases=['хелп', 'помощь'])
async def custom_help(ctx, command_name: str = None):
    """Показывает список всех команд с категориями"""
    
    if command_name:
        cmd = bot.get_command(command_name.lower())
        if cmd:
            embed = discord.Embed(
                title=f"📖 Команда: j.{cmd.name}",
                description=cmd.help or "Нет описания",
                color=0x00ff00
            )
            
            permissions = []
            for check in cmd.checks:
                if hasattr(check, '__closure__'):
                    if 'helper' in str(check.__closure__):
                        permissions.append("🟢 Helper+")
                    elif 'moderator' in str(check.__closure__):
                        permissions.append("🟢 Модератор+")
                    elif 'admin' in str(check.__closure__):
                        permissions.append("🟢 Админ+")
            
            if permissions:
                embed.add_field(name="🔒 Права доступа", value="\n".join(permissions), inline=False)
            
            embed.add_field(name="Использование", value=f"`j.{cmd.name} {cmd.signature}`" if cmd.signature else f"`j.{cmd.name}`", inline=False)
            embed.set_footer(text="j.help команда - подробная информация")
            await ctx.send(embed=embed)
            return
        else:
            await ctx.send(f"❌ Команда `{command_name}` не найдена. Используйте `j.help` для списка команд.")
            return
    
    embed = discord.Embed(
        title="🌟 Меню помощи бота Justice",
        description=f"**Префикс: `j.`**\nИспользуйте `j.help команда` для подробной информации\n\n**Курс:** 1 рубль = {data.get('exchange_rate', 5)} осколков 💎",
        color=0x5865F2
    )
    
    # Категория: Модерация
    mod_commands = []
    for cmd in bot.commands:
        if any(role in str(cmd.checks) for role in ['helper', 'moderator', 'admin', 'head_admin', 'curator', 'co_owner', 'owner']):
            if cmd.name not in ['help', 'add', 'remove', 'balance', 'daily', 'clear', 'setrate']:
                mod_commands.append(f"**{cmd.name}** - {cmd.help or 'Нет описания'}")
    
    if mod_commands:
        embed.add_field(
            name="🛡️ Модерация",
            value="\n".join(mod_commands[:10]) + ("\n*...и другие*" if len(mod_commands) > 10 else ""),
            inline=False
        )
    
    # Категория: Экономика
    embed.add_field(
        name="💰 Экономика",
        value=f"""**balance (bal)** - Просмотр баланса
**daily** - Ежедневный бонус (5 осколков)
**add** - Выдать осколки (Экономист+)
**remove** - Снять осколки (Экономист+)
**setrate** - Установить курс (Владелец/Боженька)
**clear** - Очистить канал (Helper+)""",
        inline=False
    )
    
    # Категория: Система
    embed.add_field(
        name="⚙️ Система",
        value="**help** - Это меню помощи\n**status** - Проверить статус бота\n**rate** - Показать текущий курс",
        inline=False
    )
    
    embed.add_field(
        name="👑 Иерархия ролей",
        value="""👑 Владелец
🤝 Со-владелец
📚 Куратор
⭐ Главный админ
🔰 Админ
🛡️ Модератор
🆘 Хелпер
💎 Экономист""",
        inline=True
    )
    
    embed.add_field(
        name="📋 Доступ к командам",
        value="""🟢 **Helper+**: мут, размут, варн, варны, разварн, clear
🟡 **Модератор+**: кик
🔴 **Админ+**: бан
💎 **Экономист+**: add, remove
👑 **Владелец/Боженька**: setrate""",
        inline=True
    )
    
    embed.set_footer(text=f"Запросил: {ctx.author.display_name} | Версия 2.0")
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    await ctx.send(embed=embed)

# ----- КОМАНДА СТАТУС БОТА -----
@bot.command(name='status', aliases=['статус'])
async def bot_status(ctx):
    """Показывает статус бота и отслеживаемого пользователя"""
    global bog_member, last_status
    
    embed = discord.Embed(
        title="📊 Статус бота",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="🤖 Бот",
        value=f"**Статус:** 🟢 Онлайн\n**Пинг:** {round(bot.latency * 1000)}ms\n**Серверов:** {len(bot.guilds)}",
        inline=False
    )
    
    if bog_member:
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        status_text = {
            discord.Status.online: "В сети",
            discord.Status.idle: "Отошел",
            discord.Status.dnd: "Не беспокоить",
            discord.Status.offline: "Не в сети"
        }
        
        embed.add_field(
            name="👁️ Боженька",
            value=f"{status_emoji.get(bog_member.status, '❓')} **{status_text.get(bog_member.status, 'Неизвестно')}**\nПоследнее обновление: {datetime.now().strftime('%H:%M:%S')}",
            inline=False
        )
    
    total_balance = sum(data['balance'].values()) if data['balance'] else 0
    embed.add_field(
        name="💰 Экономика",
        value=f"**Всего осколков:** {total_balance} 💎\n**Пользователей:** {len(data['balance'])}\n**Курс:** 1 рубль = {data.get('exchange_rate', 5)} осколков",
        inline=False
    )
    
    await ctx.send(embed=embed)

# ----- КОМАНДА КУРСА -----
@bot.command(name='rate', aliases=['курс'])
async def show_rate(ctx):
    """Показывает текущий курс осколков к рублю"""
    rate = data.get('exchange_rate', 5)
    embed = discord.Embed(
        title="💱 Текущий курс",
        description=f"**1 рубль = {rate} осколков** 💎\n**1 осколок = {round(1/rate, 2)} рублей**" if rate > 0 else "Курс не установлен",
        color=0x00ff00
    )
    embed.set_footer(text=f"Установлен: {'по умолчанию' if rate == 5 else 'администрацией'}")
    await ctx.send(embed=embed)

@bot.command(name='setrate', aliases=['установитькурс'])
@commands.check(is_owner_or_bog)
async def set_exchange_rate(ctx, rate: int):
    """Установить курс осколков к рублю (Только владелец/Боженька)"""
    if rate <= 0:
        await ctx.send("❌ Курс должен быть положительным числом!")
        return
    
    old_rate = data.get('exchange_rate', 5)
    data['exchange_rate'] = rate
    save_data(data)
    
    embed = discord.Embed(
        title="💱 Курс обновлен!",
        description=f"**Был:** 1 рубль = {old_rate} осколков\n**Стал:** 1 рубль = {rate} осколков",
        color=0x00ff00
    )
    embed.set_footer(text=f"Обновил: {ctx.author.display_name}")
    await ctx.send(embed=embed)

# ----- КОМАНДА CLEAR (ОЧИСТКА КАНАЛА) -----
@bot.command(name='clear', aliases=['очистить', 'cls'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def clear_channel(ctx, amount: int = None):
    """Очищает указанное количество сообщений в канале (Helper+)"""
    
    # Проверка лимита
    if amount is None:
        await ctx.send("❌ Укажите количество сообщений для удаления. Пример: `j.clear 50`")
        return
    
    if amount < 1:
        await ctx.send("❌ Количество должно быть больше 0!")
        return
    
    if amount > 100:
        await ctx.send("❌ Нельзя удалить больше 100 сообщений за раз!")
        return
    
    # Удаляем сообщения
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 для команды
        await ctx.send(f"✅ Удалено {len(deleted) - 1} сообщений!", delete_after=3)
    except discord.Forbidden:
        await ctx.send("❌ У меня нет прав на удаление сообщений в этом канале!")
    except discord.HTTPException as e:
        await ctx.send(f"❌ Ошибка при удалении: {e}")

# ----- КОМАНДА CLEAR ПО ID -----
@bot.command(name='clearbot', aliases=['очиститьбота'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def clear_bot_messages(ctx, amount: int = 10):
    """Очищает только сообщения бота в канале (Helper+)"""
    
    if amount < 1:
        await ctx.send("❌ Количество должно быть больше 0!")
        return
    
    if amount > 50:
        await ctx.send("❌ Нельзя удалить больше 50 сообщений за раз!")
        return
    
    def is_bot_message(msg):
        return msg.author == bot.user
    
    try:
        deleted = await ctx.channel.purge(limit=amount, check=is_bot_message)
        await ctx.send(f"✅ Удалено {len(deleted)} сообщений бота!", delete_after=3)
    except discord.Forbidden:
        await ctx.send("❌ У меня нет прав на удаление сообщений в этом канале!")

# ----- ВСЕ АДМИН КОМАНДЫ (мут, бан, кик, варн, и т.д.) -----
@bot.command(name='мут')
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def mute(ctx, member: discord.Member, time: str, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Вы не можете замутить этого пользователя (выше/равная роль).")
        return
    
    if member.id == BOG_ID:
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
        await ctx.send("❌ Неверный формат времени. Используйте: 10s, 5m, 2h, 1d")
        return
    
    await member.timeout(timedelta(seconds=time_seconds), reason=reason)
    
    embed = discord.Embed(title="🔇 Мут", color=0xff0000)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)
    embed.add_field(name="Время", value=time, inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='размут')
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def unmute(ctx, member: discord.Member):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Вы не можете размутить этого пользователя.")
        return
    
    await member.timeout(None)
    embed = discord.Embed(title="🔊 Размут", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)

@bot.command(name='бан')
@commands.has_any_role(*[ROLES['admin'], ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def ban(ctx, member: discord.Member, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Вы не можете забанить этого пользователя.")
        return
    
    if member.id == BOG_ID:
        await ctx.send("❌ Нельзя банить Боженьку!")
        return
    
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 Бан", color=0xff0000)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='кик')
@commands.has_any_role(*[ROLES['moderator'], ROLES['admin'], ROLES['head_admin'], 
                         ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def kick(ctx, member: discord.Member, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Вы не можете кикнуть этого пользователя.")
        return
    
    if member.id == BOG_ID:
        await ctx.send("❌ Нельзя кикать Боженьку!")
        return
    
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Кик", color=0xffa500)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='варн')
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def warn(ctx, member: discord.Member, time: str, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Вы не можете выдать варн этому пользователю.")
        return
    
    if member.id == BOG_ID:
        await ctx.send("❌ Нельзя выдавать варн Боженьке!")
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
        await ctx.send("❌ Неверный формат времени. Используйте: 10s, 5m, 2h, 1d")
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
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)
    embed.add_field(name="Время", value=time, inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='варны')
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def warns(ctx, member: discord.Member):
    if str(member.id) not in data['warns'] or not data['warns'][str(member.id)]:
        await ctx.send(f"✅ У {member.mention} нет активных варнов.")
        return
    
    embed = discord.Embed(title=f"📋 Варны {member.display_name}", color=0xffff00)
    active_warns = 0
    for warn_id, warn in data['warns'][str(member.id)].items():
        expires = datetime.fromisoformat(warn['expires'])
        if expires > datetime.now():
            embed.add_field(
                name=f"ID: {warn_id[:6]}",
                value=f"Причина: {warn['reason']}\nВыдал: <@{warn['moderator']}>\nИстекает: {expires.strftime('%d.%m.%Y %H:%M')}",
                inline=False
            )
            active_warns += 1
    
    if active_warns == 0:
        await ctx.send(f"✅ У {member.mention} нет активных варнов.")
    else:
        await ctx.send(embed=embed)

@bot.command(name='разварн')
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def unwarn(ctx, member: discord.Member, warn_id: str):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Вы не можете снять варн у этого пользователя.")
        return
    
    if str(member.id) in data['warns'] and warn_id in data['warns'][str(member.id)]:
        del data['warns'][str(member.id)][warn_id]
        save_data(data)
        await ctx.send(f"✅ Варн `{warn_id}` снят с {member.mention}")
    else:
        await ctx.send(f"❌ Варн с ID `{warn_id}` не найден у {member.mention}")

# ----- ЭКОНОМИЧЕСКИЕ КОМАНДЫ -----
@bot.command(name='balance', aliases=['bal'])
async def balance(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    balance = data['balance'].get(str(member.id), 0)
    rate = data.get('exchange_rate', 5)
    rubles = round(balance / rate, 2) if rate > 0 else 0
    
    embed = discord.Embed(title="💰 Баланс осколков", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Осколки", value=f"{balance} 💎", inline=True)
    embed.add_field(name="Рубли", value=f"{rubles} ₽", inline=True)
    embed.set_footer(text=f"Курс: 1 ₽ = {rate} 💎")
    await ctx.send(embed=embed)

@bot.command(name='add')
@commands.has_any_role(ROLES['economy'], ROLES['owner'])
async def add_shards(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Количество должно быть положительным.")
        return
    
    if str(member.id) not in data['balance']:
        data['balance'][str(member.id)] = 0
    data['balance'][str(member.id)] += amount
    save_data(data)
    
    rate = data.get('exchange_rate', 5)
    rubles = round(amount / rate, 2)
    
    embed = discord.Embed(title="➕ Выдача осколков", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Количество", value=f"+{amount} 💎 ({rubles} ₽)", inline=True)
    embed.add_field(name="Новый баланс", value=f"{data['balance'][str(member.id)]} 💎", inline=True)
    embed.set_footer(text=f"Выдал: {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command(name='remove')
@commands.has_any_role(ROLES['economy'], ROLES['owner'])
async def remove_shards(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Количество должно быть положительным.")
        return
    
    if str(member.id) not in data['balance']:
        data['balance'][str(member.id)] = 0
    
    if data['balance'][str(member.id)] < amount:
        await ctx.send(f"❌ У {member.mention} недостаточно осколков. Баланс: {data['balance'][str(member.id)]} 💎")
        return
    
    data['balance'][str(member.id)] -= amount
    save_data(data)
    
    rate = data.get('exchange_rate', 5)
    rubles = round(amount / rate, 2)
    
    embed = discord.Embed(title="➖ Снятие осколков", color=0xff0000)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Количество", value=f"-{amount} 💎 ({rubles} ₽)", inline=True)
    embed.add_field(name="Новый баланс", value=f"{data['balance'][str(member.id)]} 💎", inline=True)
    embed.set_footer(text=f"Снял: {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command(name='daily')
async def daily(ctx):
    user_id = str(ctx.author.id)
    today = datetime.now().date().isoformat()
    
    if user_id in data['daily'] and data['daily'][user_id] == today:
        await ctx.send("❌ Вы уже получили ежедневный бонус сегодня! Приходите завтра.")
        return
    
    if user_id not in data['balance']:
        data['balance'][user_id] = 0
    data['balance'][user_id] += 5
    data['daily'][user_id] = today
    save_data(data)
    
    rate = data.get('exchange_rate', 5)
    rubles = round(5 / rate, 2)
    
    embed = discord.Embed(title="🎉 Ежедневный бонус", color=0xffd700)
    embed.add_field(name="Пользователь", value=ctx.author.mention, inline=True)
    embed.add_field(name="Получено", value=f"+5 💎 ({rubles} ₽)", inline=True)
    embed.add_field(name="Новый баланс", value=f"{data['balance'][user_id]} 💎", inline=True)
    embed.set_footer(text="Приходите завтра за новым бонусом!")
    await ctx.send(embed=embed)

# ----- Фоновая задача для отслеживания статуса -----
@tasks.loop(seconds=5)
async def status_check():
    global last_status, bog_member
    
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return
    
    if not bog_member:
        if bot.guilds:
            guild = bot.guilds[0]
            bog_member = guild.get_member(BOG_ID)
            if bog_member:
                last_status = bog_member.status
                await send_status_update(channel, bog_member.status)
            return
        return
    
    try:
        current_status = bog_member.status
        
        if current_status != last_status:
            print(f"🔄 Статус изменился: {last_status} -> {current_status}")
            await send_status_update(channel, current_status)
            last_status = current_status
            
    except Exception as e:
        print(f"❌ Ошибка при проверке статуса: {e}")

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
    
    await channel.send(embed=embed)

# ----- Событие готовности -----
@bot.event
async def on_ready():
    global bog_member, last_status
    
    print(f'✅ Бот {bot.user} готов!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="за Боженькой"))
    
    if bot.guilds:
        guild = bot.guilds[0]
        bog_member = guild.get_member(BOG_ID)
        
        if bog_member:
            last_status = bog_member.status
            print(f"📊 Начальный статус Боженьки: {last_status}")
            
            channel = bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🟢 Бот запущен!",
                    description=f"👁️ Начинаю следить за Боженькой <@{BOG_ID}>\nТекущий статус: **{last_status}**\nКурс: 1 ₽ = {data.get('exchange_rate', 5)} 💎",
                    color=0x00ff00
                )
                await channel.send(embed=embed)
                await send_status_update(channel, last_status)
    
    status_check.start()
    print("✅ Статус-трекер запущен!")

# ----- Обработчик ошибок -----
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("❌ У вас нет прав для использования этой команды.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ У вас недостаточно прав.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Неверный аргумент. Проверьте ввод.")
    else:
        await ctx.send(f"❌ Произошла ошибка: {error}")
        print(f"Ошибка: {error}")

# ----- Запуск -----
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ОШИБКА: Токен не найден! Установите переменную DISCORD_TOKEN")
        exit(1)
    bot.run(TOKEN)
