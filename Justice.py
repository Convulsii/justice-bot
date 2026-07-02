import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta
import re

# ----- Настройки -----
TOKEN = os.getenv('DISCORD_TOKEN')  # Токен из переменных окружения

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

# ----- Файлы для хранения данных -----
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'warns': {}, 'balance': {}, 'daily': {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

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

# ----- Событие готовности -----
@bot.event
async def on_ready():
    print(f'Бот {bot.user} готов!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="за Боженькой"))
    status_check.start()
    print("Бот успешно запущен на Railway!")

# ----- Фоновая задача для отслеживания статуса -----
@tasks.loop(seconds=10)
async def status_check():
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return
    user = bot.get_user(BOG_ID)
    if not user:
        return
    
    try:
        status = user.status
        old_status = getattr(status_check, 'old_status', None)
        
        if status != old_status:
            embed = discord.Embed(title="👁️ Статус Боженьки", color=0x00ff00)
            
            status_messages = {
                discord.Status.online: ("🌅 **Боженька готов услышать ваши мольбы!**\nОн в сети и ждёт ваши просьбы.", 0x00ff00),
                discord.Status.idle: ("💤 **Боженьку лучше не тревожить!**\nОн отдыхает, иначе навлечёте на себя гнев божий.", 0xffff00),
                discord.Status.dnd: ("🔇 **Боженька занят!**\nНе тревожьте его сейчас, иначе будете наказаны.", 0xff0000),
                discord.Status.offline: ("🌆 **Боженька не в сети!**\nЕго лучше не тревожить. Похоже, он уехал в Вегас 🎰", 0x808080)
            }
            
            if status in status_messages:
                embed.description, embed.color = status_messages[status]
            else:
                embed.description, embed.color = status_messages[discord.Status.offline]
            
            embed.set_footer(text=f"ID: {user.id} | Обновлено: {datetime.now().strftime('%H:%M:%S')}")
            await channel.send(embed=embed)
            status_check.old_status = status
    except Exception as e:
        print(f"Ошибка при проверке статуса: {e}")

# ----- Административные команды -----
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

# ----- Экономические команды -----
@bot.command(name='balance', aliases=['bal'])
async def balance(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    balance = data['balance'].get(str(member.id), 0)
    embed = discord.Embed(title="💰 Баланс осколков", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Осколки", value=f"{balance} 💎", inline=True)
    embed.set_footer(text="1 осколок = 0.2 рубля")
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
    
    embed = discord.Embed(title="➕ Выдача осколков", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Количество", value=f"+{amount} 💎", inline=True)
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
    
    embed = discord.Embed(title="➖ Снятие осколков", color=0xff0000)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Количество", value=f"-{amount} 💎", inline=True)
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
    
    embed = discord.Embed(title="🎉 Ежедневный бонус", color=0xffd700)
    embed.add_field(name="Пользователь", value=ctx.author.mention, inline=True)
    embed.add_field(name="Получено", value="+5 💎", inline=True)
    embed.add_field(name="Новый баланс", value=f"{data['balance'][user_id]} 💎", inline=True)
    embed.set_footer(text="Приходите завтра за новым бонусом!")
    await ctx.send(embed=embed)

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

# ----- Запуск бота -----
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ОШИБКА: Токен не найден! Установите переменную DISCORD_TOKEN")
        exit(1)
    bot.run(TOKEN)
