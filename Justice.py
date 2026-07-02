import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta
import re
import pandas as pd
from io import BytesIO
import openpyxl

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
}

BOG_ID = 1062336593588912199
LOG_CHANNEL_ID = 1502637205187723433
REPORT_CHANNEL_ID = 1502637205187723433  # Канал для отчетов

# ----- Инициализация бота -----
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='j.', intents=intents)
bot.remove_command('help')

# ----- Файлы для хранения -----
DATA_FILE = 'data.json'
BACKUP_FOLDER = 'backups'
REPORT_FOLDER = 'reports'

# Создаем папки
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
        'exchange_rate': 5
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
    return ctx.author.id == ROLES['owner'] or ctx.author.id == BOG_ID

def is_owner_only(ctx):
    return ctx.author.id == ROLES['owner']

# ----- КОМАНДА БЭКАПА (только данные для восстановления) -----
@bot.command(name='backup', aliases=['бэкап'])
@commands.check(is_owner_only)
async def create_backup(ctx):
    """Создать бэкап данных для восстановления (Только владелец)"""
    
    await ctx.send("🔄 **Создаю бэкап данных...**")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_backup = f"{BACKUP_FOLDER}/backup_{timestamp}.json"
    
    # Сохраняем полные данные
    with open(json_backup, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    # Отправляем файл в канал
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        channel = ctx.channel
    
    embed = discord.Embed(
        title="💾 Бэкап создан!",
        description=f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                   f"**Размер:** {os.path.getsize(json_backup) / 1024:.2f} KB\n"
                   f"**Данные:** Баланс, варны, daily, курс",
        color=0x00ff00
    )
    embed.set_footer(text=f"Создал: {ctx.author.display_name}")
    
    await channel.send(embed=embed)
    
    with open(json_backup, 'rb') as f:
        await channel.send(file=discord.File(f, f"backup_{timestamp}.json"))
    
    await ctx.send(f"✅ **Бэкап создан!** Файл отправлен в канал <#{channel.id}>")
    
    # Оставляем только последние 10 бэкапов
    backups = sorted([f for f in os.listdir(BACKUP_FOLDER) if f.startswith('backup_')])
    if len(backups) > 10:
        for old_file in backups[:-10]:
            os.remove(os.path.join(BACKUP_FOLDER, old_file))

# ----- КОМАНДА ВОССТАНОВЛЕНИЯ ИЗ БЭКАПА -----
@bot.command(name='restore', aliases=['восстановить'])
@commands.check(is_owner_only)
async def restore_backup(ctx, backup_name: str = None):
    """Восстановить данные из бэкапа (Только владелец)"""
    
    if backup_name is None:
        backups = sorted([f for f in os.listdir(BACKUP_FOLDER) if f.startswith('backup_') and f.endswith('.json')])
        
        if not backups:
            await ctx.send("❌ Нет доступных бэкапов!")
            return
        
        embed = discord.Embed(
            title="📋 Доступные бэкапы",
            description="Используйте `j.restore имя_файла` для восстановления",
            color=0x5865F2
        )
        
        for i, backup in enumerate(backups[-10:], 1):
            date_str = backup.replace('backup_', '').replace('.json', '')
            embed.add_field(
                name=f"{i}. {date_str}",
                value=f"`{backup}`",
                inline=False
            )
        
        await ctx.send(embed=embed)
        return
    
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)
    if not os.path.exists(backup_path):
        await ctx.send(f"❌ Бэкап `{backup_name}` не найден!")
        return
    
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Сохраняем текущие данные перед восстановлением
        current_backup = f"{BACKUP_FOLDER}/pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(current_backup, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Восстанавливаем
        global data
        data = backup_data
        save_data(data)
        
        embed = discord.Embed(
            title="✅ Данные восстановлены!",
            description=f"**Из бэкапа:** {backup_name}\n"
                       f"**Пользователей:** {len(data['balance'])}\n"
                       f"**Всего осколков:** {sum(data['balance'].values())} 💎",
            color=0x00ff00
        )
        embed.set_footer(text="Старые данные сохранены как резервная копия")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка при восстановлении: {e}")

# ----- КОМАНДА ОТЧЕТА (Excel + TXT для просмотра) -----
@bot.command(name='report', aliases=['отчет', 'stat'])
@commands.check(is_owner_or_bog)
async def create_report(ctx):
    """Создать отчет со статистикой в Excel и TXT (Владелец/Боженька)"""
    
    await ctx.send("📊 **Создаю отчет со статистикой...**")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    rate = data.get('exchange_rate', 5)
    
    # ----- СОЗДАЕМ EXCEL -----
    excel_data = []
    
    # Заголовок
    excel_data.append(['📊 СТАТИСТИКА СЕРВЕРА'])
    excel_data.append([f'Дата: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'])
    excel_data.append([f'Курс: 1 ₽ = {rate} 💎'])
    excel_data.append([])
    
    # Общая статистика
    total_users = len(data['balance'])
    total_shards = sum(data['balance'].values())
    total_rubles = round(total_shards / rate, 2) if rate > 0 else 0
    total_warns = sum(len(warns) for warns in data['warns'].values())
    
    excel_data.append(['📈 ОБЩАЯ СТАТИСТИКА'])
    excel_data.append(['Всего пользователей:', total_users])
    excel_data.append(['Всего осколков:', f'{total_shards} 💎'])
    excel_data.append(['Всего рублей:', f'{total_rubles} ₽'])
    excel_data.append(['Всего варнов:', total_warns])
    excel_data.append([])
    
    # Топ-10 богачей
    excel_data.append(['🏆 ТОП-10 БОГАТЕЙ'])
    excel_data.append(['Место', 'Пользователь', 'Осколки 💎', 'Рубли ₽'])
    
    sorted_users = sorted(data['balance'].items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (user_id, balance) in enumerate(sorted_users, 1):
        try:
            user = bot.get_user(int(user_id)) or await bot.fetch_user(int(user_id))
            username = user.name if user else "Неизвестный"
        except:
            username = "Неизвестный"
        
        rubles = round(balance / rate, 2) if rate > 0 else 0
        excel_data.append([i, username, balance, rubles])
    
    excel_data.append([])
    
    # Все пользователи с балансом
    excel_data.append(['👥 ВСЕ ПОЛЬЗОВАТЕЛИ'])
    excel_data.append(['ID', 'Имя пользователя', 'Осколки 💎', 'Рубли ₽', 'Daily', 'Варнов'])
    
    for user_id, balance in sorted(data['balance'].items(), key=lambda x: x[1], reverse=True):
        try:
            user = bot.get_user(int(user_id)) or await bot.fetch_user(int(user_id))
            username = user.name if user else "Неизвестный"
        except:
            username = "Неизвестный"
        
        rubles = round(balance / rate, 2) if rate > 0 else 0
        daily_date = data['daily'].get(str(user_id), 'Нет')
        warns_count = len(data['warns'].get(str(user_id), {}))
        
        excel_data.append([user_id, username, balance, rubles, daily_date, warns_count])
    
    # Создаем Excel файл
    df = pd.DataFrame(excel_data)
    excel_file = f"{REPORT_FOLDER}/report_{timestamp}.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=False)
        
        # Настраиваем ширину колонок
        worksheet = writer.sheets['Sheet1']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # ----- СОЗДАЕМ TXT -----
    txt_file = f"{REPORT_FOLDER}/report_{timestamp}.txt"
    
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("📊 СТАТИСТИКА СЕРВЕРА\n")
        f.write("="*70 + "\n\n")
        f.write(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write(f"💱 Курс: 1 ₽ = {rate} 💎\n\n")
        
        f.write("="*70 + "\n")
        f.write("📈 ОБЩАЯ СТАТИСТИКА\n")
        f.write("="*70 + "\n")
        f.write(f"👥 Всего пользователей: {total_users}\n")
        f.write(f"💎 Всего осколков: {total_shards}\n")
        f.write(f"💰 Всего рублей: {total_rubles} ₽\n")
        f.write(f"⚠️ Всего варнов: {total_warns}\n\n")
        
        f.write("="*70 + "\n")
        f.write("🏆 ТОП-10 БОГАТЕЙ\n")
        f.write("="*70 + "\n")
        for i, (user_id, balance) in enumerate(sorted_users, 1):
            try:
                user = bot.get_user(int(user_id)) or await bot.fetch_user(int(user_id))
                username = user.name if user else "Неизвестный"
            except:
                username = "Неизвестный"
            rubles = round(balance / rate, 2) if rate > 0 else 0
            f.write(f"{i:2}. {username:25} | 💎 {balance:6} | ₽ {rubles:8}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("👥 ВСЕ ПОЛЬЗОВАТЕЛИ\n")
        f.write("="*70 + "\n")
        f.write(f"{'ID':<20} | {'Имя':<25} | {'Осколки':<10} | {'Рубли':<10} | {'Daily':<12} | {'Варны'}\n")
        f.write("-"*70 + "\n")
        
        for user_id, balance in sorted(data['balance'].items(), key=lambda x: x[1], reverse=True):
            try:
                user = bot.get_user(int(user_id)) or await bot.fetch_user(int(user_id))
                username = user.name if user else "Неизвестный"
            except:
                username = "Неизвестный"
            
            rubles = round(balance / rate, 2) if rate > 0 else 0
            daily_date = data['daily'].get(str(user_id), 'Нет')
            warns_count = len(data['warns'].get(str(user_id), {}))
            
            f.write(f"{user_id:<20} | {username[:24]:<25} | {balance:<10} | {rubles:<10} | {daily_date:<12} | {warns_count}\n")
    
    # Отправляем отчеты
    channel = bot.get_channel(REPORT_CHANNEL_ID)
    if not channel:
        channel = ctx.channel
    
    embed = discord.Embed(
        title="📊 Отчет создан!",
        description=f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                   f"**Пользователей:** {total_users}\n"
                   f"**Всего осколков:** {total_shards} 💎\n"
                   f"**Курс:** 1 ₽ = {rate} 💎",
        color=0x5865F2
    )
    embed.set_footer(text=f"Запросил: {ctx.author.display_name}")
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/123456789.png" if False else None)
    
    await channel.send(embed=embed)
    
    # Отправляем файлы
    with open(excel_file, 'rb') as f:
        await channel.send(file=discord.File(f, f"report_{timestamp}.xlsx"))
    
    with open(txt_file, 'rb') as f:
        await channel.send(file=discord.File(f, f"report_{timestamp}.txt"))
    
    await ctx.send(f"✅ **Отчет создан!** Файлы отправлены в канал <#{channel.id}>")
    
    # Оставляем только последние 10 отчетов
    reports = sorted([f for f in os.listdir(REPORT_FOLDER) if f.startswith('report_')])
    if len(reports) > 10:
        for old_file in reports[:-10]:
            os.remove(os.path.join(REPORT_FOLDER, old_file))

# ----- ОСТАЛЬНЫЕ КОМАНДЫ (справка, статус, модерация, экономика) -----
# [ВСТАВЬТЕ ВСЕ ОСТАЛЬНЫЕ КОМАНДЫ ИЗ ПРЕДЫДУЩЕГО КОДА]
# (команды help, status, rate, setrate, clear, мут, бан, кик, варн, balance, add, remove, daily и т.д.)

# ----- ЗАПУСК БОТА -----
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ОШИБКА: Токен не найден! Установите переменную DISCORD_TOKEN")
        exit(1)
    
    # Создаем папки
    for folder in [BACKUP_FOLDER, REPORT_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    bot.run(TOKEN)
