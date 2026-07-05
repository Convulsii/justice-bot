import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
import asyncio
import json
import os
from datetime import datetime, timedelta
import re
import pytz

# ----- НАСТРОЙКИ -----
TOKEN = os.getenv('DISCORD_TOKEN')

# Часовой пояс МСК (UTC+3)
MSK = pytz.timezone('Europe/Moscow')

ROLES = {
    'helper': 1512024218814910524,
    'moderator': 1507478655578673152,
    'admin': 1502637204537737306,
    'head_admin': 1507479670130741368,
    'curator': 1512520499941605618,
    'co_owner': 1502637204537737308,
    'owner': 1504402262833758228,
}

BOG_ROLE_ID = 1521944293135351829
OWNER_ROLE_ID = 1504402262833758228
BOG_USER_ID = 1062336593588912199

LOG_CHANNEL_ID = 1502637205187723433
REPORT_CHANNEL_ID = 1502637205187723433
STATS_LOG_CHANNEL_ID = 1502637204982206681

PRIVATE_VOICE_CATEGORY_ID = 1507479787223126036
VOICE_TRIGGER_ID = 1507485728739688549

MESSAGES_PER_SHARD = 10
SHARDS_PER_MESSAGES = 1
VOICE_HOUR_SHARDS = 15
DAILY_BONUS = 15
REFERRAL_BONUS = 100
COOLDOWN_SECONDS = 10
VOICE_CHECK_INTERVAL = 30
BUTTON_TIMEOUT = 31536000

# ----- ИНИЦИАЛИЗАЦИЯ БОТА (case_insensitive=True - команды работают в любом регистре) -----
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='j.', intents=intents, case_insensitive=True)
bot.remove_command('help')

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
        'messages_history': {},
        'last_message_time': {},
        'voice_time': {},
        'voice_last_check': {},
        'voice_total_time': {},
        'voice_history': {},
        'last_status_message_id': None,
        'referrals': {},
        'referral_count': {},
        'referral_links': {},
        'private_voice_settings': {},
        'used_referrals': {},
        'daily_stats': {
            'date': None,
            'messages': {},
            'voice_time': {}
        },
        'weekly_stats': {
            'week_start': None,
            'messages': {},
            'voice_time': {}
        },
        'monthly_stats': {
            'month': None,
            'messages': {},
            'voice_time': {}
        }
    }


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


data = load_data()

last_status = None
bog_member = None
last_status_message = None
private_voice_channels = {}
voice_settings = {}


# ----- КЛАССЫ ДЛЯ КНОПОК -----
class VoiceControlView(View):
    def __init__(self, channel_id, owner_id):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.channel_id = channel_id
        self.owner_id = owner_id
        self.message = None

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Вы не владелец этого канала!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="👥 Лимит", style=discord.ButtonStyle.primary, custom_id="voice_limit")
    async def limit_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SetLimitModal(self.channel_id))

    @discord.ui.button(label="🚫 Бан", style=discord.ButtonStyle.danger, custom_id="voice_ban")
    async def ban_button(self, interaction: discord.Interaction, button: Button):
        await show_user_select(interaction, self.channel_id, "ban")

    @discord.ui.button(label="✅ Разбан", style=discord.ButtonStyle.success, custom_id="voice_unban")
    async def unban_button(self, interaction: discord.Interaction, button: Button):
        await show_user_select(interaction, self.channel_id, "unban")

    @discord.ui.button(label="👁️ Скрыть", style=discord.ButtonStyle.secondary, custom_id="voice_hide")
    async def hide_button(self, interaction: discord.Interaction, button: Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await interaction.response.send_message("✅ Канал скрыт!", ephemeral=True)
            str_id = str(self.channel_id)
            if str_id in data['private_voice_settings']:
                data['private_voice_settings'][str_id]['hidden'] = True
                save_data(data)

    @discord.ui.button(label="👁️ Показать", style=discord.ButtonStyle.secondary, custom_id="voice_show")
    async def show_button(self, interaction: discord.Interaction, button: Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=True)
            await interaction.response.send_message("✅ Канал теперь виден!", ephemeral=True)
            str_id = str(self.channel_id)
            if str_id in data['private_voice_settings']:
                data['private_voice_settings'][str_id]['hidden'] = False
                save_data(data)

    @discord.ui.button(label="👢 Кик", style=discord.ButtonStyle.danger, custom_id="voice_kick")
    async def kick_button(self, interaction: discord.Interaction, button: Button):
        await show_user_select(interaction, self.channel_id, "kick")

    @discord.ui.button(label="🗑️ Удалить", style=discord.ButtonStyle.danger, custom_id="voice_delete")
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            other_members = [m for m in channel.members if m.id != self.owner_id]
            if other_members:
                await interaction.response.send_message("❌ В канале есть другие участники! Сначала кикните их.",
                                                        ephemeral=True)
                return
            try:
                str_id = str(self.channel_id)
                if str_id in data['private_voice_settings']:
                    del data['private_voice_settings'][str_id]
                    save_data(data)
                if self.channel_id in private_voice_channels:
                    del private_voice_channels[self.channel_id]
                if self.channel_id in voice_settings:
                    del voice_settings[self.channel_id]
                await channel.delete()
                await interaction.response.send_message("✅ Канал удален!", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @discord.ui.button(label="📊 Инфо", style=discord.ButtonStyle.secondary, custom_id="voice_info")
    async def info_button(self, interaction: discord.Interaction, button: Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
            return
        str_id = str(self.channel_id)
        settings = data['private_voice_settings'].get(str_id, {})
        owner = interaction.guild.get_member(settings.get('owner_id', 0))
        owner_name = owner.mention if owner else "Неизвестен"
        max_users = settings.get('max_users', 0)
        banned_users = settings.get('banned_users', [])
        hidden = settings.get('hidden', False)
        banned_list = []
        for uid in banned_users[:5]:
            user = interaction.guild.get_member(uid)
            banned_list.append(user.mention if user else f"`{uid}`")
        banned_text = ", ".join(banned_list) if banned_list else "Нет забаненных"
        if len(banned_users) > 5:
            banned_text += f" и еще {len(banned_users) - 5}..."
        embed = discord.Embed(title=f"📊 Информация о канале", color=0x5865F2)
        embed.add_field(name="Канал", value=channel.mention)
        embed.add_field(name="Владелец", value=owner_name)
        embed.add_field(name="Максимум пользователей", value=max_users if max_users > 0 else "Безлимит")
        embed.add_field(name="Скрыт", value="Да 🔒" if hidden else "Нет 👁️")
        embed.add_field(name="Забаненные", value=banned_text, inline=False)
        embed.add_field(name="Сейчас в канале", value=f"{len(channel.members)} участников")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class UserSelectView(View):
    def __init__(self, channel_id, action, users):
        super().__init__(timeout=60)
        self.channel_id = channel_id
        self.action = action

        select = Select(
            placeholder="Выберите пользователя...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=user.name[:100],
                    value=str(user.id),
                    emoji="👤"
                ) for user in users[:25]
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        user_id = int(interaction.data['values'][0])
        member = interaction.guild.get_member(user_id)

        if not member:
            await interaction.response.send_message("❌ Пользователь не найден!", ephemeral=True)
            return

        channel = interaction.guild.get_channel(self.channel_id)

        if self.action == "ban":
            await handle_ban(interaction, member, channel)
        elif self.action == "unban":
            await handle_unban(interaction, member, channel)
        elif self.action == "kick":
            await handle_kick(interaction, member, channel)


class SetLimitModal(discord.ui.Modal):
    def __init__(self, channel_id):
        super().__init__(title="Установить лимит")
        self.channel_id = channel_id
        self.limit_input = discord.ui.TextInput(
            label="Максимум пользователей (0 = безлимит)",
            placeholder="Введите число от 0 до 99",
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.limit_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.limit_input.value)
            if limit < 0 or limit > 99:
                await interaction.response.send_message("❌ Лимит должен быть от 0 до 99!", ephemeral=True)
                return
            channel = interaction.guild.get_channel(self.channel_id)
            if channel:
                await channel.edit(user_limit=limit)
                str_id = str(self.channel_id)
                if str_id in data['private_voice_settings']:
                    data['private_voice_settings'][str_id]['max_users'] = limit
                    save_data(data)
                await interaction.response.send_message(f"✅ Лимит установлен: **{limit}**", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Введите число!", ephemeral=True)


# ----- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ -----
def is_owner(ctx):
    if ctx.author.id == 1504402262833758228:
        return True
    if discord.utils.get(ctx.author.roles, id=OWNER_ROLE_ID):
        return True
    return False


def is_owner_or_bog(ctx):
    if ctx.author.id == 1504402262833758228:
        return True
    if discord.utils.get(ctx.author.roles, id=OWNER_ROLE_ID):
        return True
    if discord.utils.get(ctx.author.roles, id=BOG_ROLE_ID):
        return True
    return False


def can_manage_economy(ctx):
    return is_owner_or_bog(ctx)


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


def get_medal(position):
    if position == 1:
        return "🥇"
    elif position == 2:
        return "🥈"
    elif position == 3:
        return "🥉"
    else:
        return f"#{position}"


def get_week_start(date):
    return date - timedelta(days=date.weekday())


def get_time_filter(times, period):
    now = datetime.now(MSK)
    if period == "day":
        cutoff = now - timedelta(days=1)
    elif period == "week":
        cutoff = now - timedelta(days=7)
    elif period == "month":
        cutoff = now - timedelta(days=30)
    elif period == "year":
        cutoff = now - timedelta(days=365)
    else:
        return times
    return [t for t in times if t > cutoff.timestamp()]


# ----- СБРОС СТАТИСТИКИ -----
def reset_daily_stats():
    today = datetime.now(MSK).date().isoformat()

    if data['daily_stats']['date'] != today:
        old_stats = data['daily_stats']

        data['daily_stats'] = {
            'date': today,
            'messages': {},
            'voice_time': {}
        }
        save_data(data)

        print(f"🔄 Дневная статистика сброшена для {today}")

        channel = bot.get_channel(STATS_LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="📊 Дневная статистика сброшена",
                description=f"Начался новый день **{today}**!\nВсе топы за день обнулены.",
                color=0x00ff00,
                timestamp=datetime.now(MSK)
            )
            if old_stats.get('date'):
                total_msgs = sum(old_stats.get('messages', {}).values())
                total_voice = sum(old_stats.get('voice_time', {}).values())
                embed.add_field(
                    name="📈 Итоги прошлого дня",
                    value=f"💬 Сообщений: {total_msgs}\n🎙️ В голосе: {format_time(total_voice)}",
                    inline=False
                )
            asyncio.create_task(channel.send(embed=embed))


def reset_weekly_stats():
    now = datetime.now(MSK)
    week_start = get_week_start(now).date().isoformat()

    if data['weekly_stats']['week_start'] != week_start:
        old_stats = data['weekly_stats']

        data['weekly_stats'] = {
            'week_start': week_start,
            'messages': {},
            'voice_time': {}
        }
        save_data(data)

        print(f"🔄 Недельная статистика сброшена (неделя начинается с {week_start})")

        channel = bot.get_channel(STATS_LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="📊 Недельная статистика сброшена",
                description=f"Началась новая неделя **{week_start}**!\nВсе топы за неделю обнулены.",
                color=0x00ff00,
                timestamp=datetime.now(MSK)
            )
            if old_stats.get('week_start'):
                total_msgs = sum(old_stats.get('messages', {}).values())
                total_voice = sum(old_stats.get('voice_time', {}).values())
                embed.add_field(
                    name="📈 Итоги прошлой недели",
                    value=f"💬 Сообщений: {total_msgs}\n🎙️ В голосе: {format_time(total_voice)}",
                    inline=False
                )
            asyncio.create_task(channel.send(embed=embed))


def reset_monthly_stats():
    now = datetime.now(MSK)
    month = now.strftime('%Y-%m')

    if data['monthly_stats']['month'] != month:
        old_stats = data['monthly_stats']

        data['monthly_stats'] = {
            'month': month,
            'messages': {},
            'voice_time': {}
        }
        save_data(data)

        print(f"🔄 Месячная статистика сброшена для {month}")

        channel = bot.get_channel(STATS_LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="📊 Месячная статистика сброшена",
                description=f"Начался новый месяц **{month}**!\nВсе топы за месяц обнулены.",
                color=0x00ff00,
                timestamp=datetime.now(MSK)
            )
            if old_stats.get('month'):
                total_msgs = sum(old_stats.get('messages', {}).values())
                total_voice = sum(old_stats.get('voice_time', {}).values())
                embed.add_field(
                    name="📈 Итоги прошлого месяца",
                    value=f"💬 Сообщений: {total_msgs}\n🎙️ В голосе: {format_time(total_voice)}",
                    inline=False
                )
            asyncio.create_task(channel.send(embed=embed))


@tasks.loop(minutes=1)
async def stats_reset_check():
    now = datetime.now(MSK)

    if now.hour == 0 and now.minute == 0:
        reset_daily_stats()
        await asyncio.sleep(1)

    if now.weekday() == 0 and now.hour == 0 and now.minute == 0:
        reset_weekly_stats()
        await asyncio.sleep(1)

    if now.day == 1 and now.hour == 0 and now.minute == 0:
        reset_monthly_stats()
        await asyncio.sleep(1)


# ----- ФУНКЦИИ ДЛЯ ДОБАВЛЕНИЯ В СТАТИСТИКУ -----
def add_daily_message(user_id):
    today = datetime.now(MSK).date().isoformat()

    if data['daily_stats']['date'] != today:
        reset_daily_stats()

    user_id = str(user_id)
    if user_id not in data['daily_stats']['messages']:
        data['daily_stats']['messages'][user_id] = 0
    data['daily_stats']['messages'][user_id] += 1
    save_data(data)


def add_weekly_message(user_id):
    now = datetime.now(MSK)
    week_start = get_week_start(now).date().isoformat()

    if data['weekly_stats']['week_start'] != week_start:
        reset_weekly_stats()

    user_id = str(user_id)
    if user_id not in data['weekly_stats']['messages']:
        data['weekly_stats']['messages'][user_id] = 0
    data['weekly_stats']['messages'][user_id] += 1
    save_data(data)


def add_monthly_message(user_id):
    now = datetime.now(MSK)
    month = now.strftime('%Y-%m')

    if data['monthly_stats']['month'] != month:
        reset_monthly_stats()

    user_id = str(user_id)
    if user_id not in data['monthly_stats']['messages']:
        data['monthly_stats']['messages'][user_id] = 0
    data['monthly_stats']['messages'][user_id] += 1
    save_data(data)


def add_daily_voice(user_id, seconds):
    today = datetime.now(MSK).date().isoformat()

    if data['daily_stats']['date'] != today:
        reset_daily_stats()

    user_id = str(user_id)
    if user_id not in data['daily_stats']['voice_time']:
        data['daily_stats']['voice_time'][user_id] = 0
    data['daily_stats']['voice_time'][user_id] += seconds
    save_data(data)


def add_weekly_voice(user_id, seconds):
    now = datetime.now(MSK)
    week_start = get_week_start(now).date().isoformat()

    if data['weekly_stats']['week_start'] != week_start:
        reset_weekly_stats()

    user_id = str(user_id)
    if user_id not in data['weekly_stats']['voice_time']:
        data['weekly_stats']['voice_time'][user_id] = 0
    data['weekly_stats']['voice_time'][user_id] += seconds
    save_data(data)


def add_monthly_voice(user_id, seconds):
    now = datetime.now(MSK)
    month = now.strftime('%Y-%m')

    if data['monthly_stats']['month'] != month:
        reset_monthly_stats()

    user_id = str(user_id)
    if user_id not in data['monthly_stats']['voice_time']:
        data['monthly_stats']['voice_time'][user_id] = 0
    data['monthly_stats']['voice_time'][user_id] += seconds
    save_data(data)


# ----- КОМАНДА HELP (ОБНОВЛЕНА) -----
@bot.command(name='help', aliases=['h', 'помощь', 'HELP'])
async def custom_help(ctx, command_name: str = None):
    """Показать список всех команд"""
    if command_name:
        cmd = bot.get_command(command_name.lower())
        if cmd:
            embed = discord.Embed(
                title=f"📖 Команда: j.{cmd.name}",
                description=cmd.help or "Нет описания",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
            await ctx.message.delete()
            return
        else:
            await ctx.send(f"❌ Команда `{command_name}` не найдена.")
            await ctx.message.delete()
            return

    embed = discord.Embed(
        title="🌟 Меню помощи бота Justice",
        description=f"""**Префикс: `j.`** (работает в любом регистре: `J.`, `j.`)

💬 **{MESSAGES_PER_SHARD} сообщений = {SHARDS_PER_MESSAGES} осколок**
🎙️ **1 час в войсе = {VOICE_HOUR_SHARDS} осколков**
📅 **/daily → +{DAILY_BONUS} осколков каждый день**
👥 **Приведи друга → +{REFERRAL_BONUS} осколков**

📊 **Сброс статистики:**
• Дневная: 00:00 каждый день
• Недельная: Понедельник 00:00
• Месячная: 1-е число 00:00""",
        color=0x5865F2
    )

    embed.add_field(
        name="🛡️ Модерация",
        value="""**mute** - Замутить\n**unmute** - Размутить\n**ban** - Забанить\n**kick** - Кикнуть\n**warn** - Выдать варн\n**warns** - Просмотр варнов\n**unwarn** - Снять варн\n**clear** - Очистить (до 1000)\n**clearall** - Очистить всё (кроме закрепленных)""",
        inline=False
    )

    embed.add_field(
        name="💰 Экономика",
        value=f"""**balance (bal)** - Баланс\n**daily** - Ежедневный бонус\n**add** - Выдать осколки\n**remove** - Снять осколки\n**rate** - Курс\n**setrate** - Установить курс""",
        inline=False
    )

    embed.add_field(
        name="📊 Статистика",
        value="""**top** - Выбор топа (сообщения/голос)\n**topmsg [day/week/month/year/all]** - Топ сообщений\n**topvoice [day/week/month/year/all]** - Топ голоса\n**daystats** - Дневная статистика\n**weekstats** - Недельная статистика\n**monthstats** - Месячная статистика\n**mystats [day/week/month/year/all]** - Моя статистика\n**msgstats** - Прогресс сообщений\n**voicestats** - Прогресс голоса\n**profile** - Профиль пользователя""",
        inline=False
    )

    embed.add_field(
        name="👥 Приглашения",
        value=f"""**referral** - Создать ссылку (+{REFERRAL_BONUS} 💎)\n**referrals** - Статистика приглашений""",
        inline=False
    )

    embed.add_field(
        name="🎙️ Приватные войсы",
        value="""**voice limit** - Лимит\n**voice ban** - Забанить\n**voice unban** - Разбанить\n**voice hide** - Скрыть\n**voice show** - Показать\n**voice kick** - Кикнуть\n**voice info** - Информация\n**voice delete** - Удалить""",
        inline=False
    )

    embed.add_field(
        name="📊 Отчеты",
        value="""**report** - Отчет (ЛС)\n**backup** - Бэкап (ЛС)\n**restore** - Восстановить\n**backups** - Список бэкапов\n**stats** - Статус бота\n**find** - Найти пользователя""",
        inline=False
    )

    embed.set_footer(text=f"Запросил: {ctx.author.display_name}")
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


# ----- КОМАНДА TOP (ИНТЕРАКТИВНОЕ МЕНЮ) -----
@bot.command(name='top', aliases=['топ'])
async def top_menu(ctx):
    """Выбор типа топа (сообщения или голос) с выбором периода"""
    
    # Создаем выбор типа
    select_type = Select(
        placeholder="Выберите тип топа...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="💬 Топ сообщений", value="msg", emoji="💬"),
            discord.SelectOption(label="🎙️ Топ голоса", value="voice", emoji="🎙️")
        ]
    )
    
    async def type_callback(interaction):
        if interaction.user.id != ctx.author.id:
            await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
            return
        
        top_type = interaction.data['values'][0]
        
        # Создаем выбор периода
        select_period = Select(
            placeholder="Выберите период...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="📅 За сегодня", value="day", emoji="📅"),
                discord.SelectOption(label="📅 За неделю", value="week", emoji="📅"),
                discord.SelectOption(label="📅 За месяц", value="month", emoji="📅"),
                discord.SelectOption(label="📅 За год", value="year", emoji="📅"),
                discord.SelectOption(label="📅 За всё время", value="all", emoji="📅")
            ]
        )
        
        async def period_callback(interaction2):
            if interaction2.user.id != ctx.author.id:
                await interaction2.response.send_message("❌ Это не ваше меню!", ephemeral=True)
                return
            
            period = interaction2.data['values'][0]
            
            # Закрываем меню
            await interaction2.response.defer()
            await interaction2.message.delete()
            
            # Вызываем соответствующую команду
            if top_type == "msg":
                await top_messages(ctx, period)
            else:
                await top_voice(ctx, period)
        
        select_period.callback = period_callback
        
        view = View()
        view.add_item(select_period)
        
        await interaction.response.edit_message(content="📊 **Выберите период:**", view=view)
    
    select_type.callback = type_callback
    
    view = View()
    view.add_item(select_type)
    
    msg = await ctx.send("📊 **Выберите тип топа:**", view=view)
    await ctx.message.delete()
    
    # Таймаут через 60 секунд
    await asyncio.sleep(60)
    try:
        await msg.delete()
    except:
        pass


# ----- КОМАНДЫ ТОПОВ -----
@bot.command(name='topmsg', aliases=['топсообщений'])
async def top_messages(ctx, period: str = None):
    """Топ пользователей по сообщениям. Периоды: day, week, month, year, all"""
    
    periods = {
        "day": "за сегодня",
        "week": "за неделю",
        "month": "за месяц",
        "year": "за год",
        "all": "за всё время"
    }
    
    # Если период не указан - показываем меню выбора
    if period is None:
        await top_menu(ctx)
        return
    
    if period not in periods:
        await ctx.send(f"❌ Неверный период! Доступны: `day`, `week`, `month`, `year`, `all`")
        await ctx.message.delete()
        return

    if not data['messages_history']:
        await ctx.send("📊 Нет данных о сообщениях!")
        await ctx.message.delete()
        return

    stats = {}
    for user_id, timestamps in data['messages_history'].items():
        filtered = get_time_filter(timestamps, period)
        if filtered:
            stats[user_id] = len(filtered)

    if not stats:
        await ctx.send(f"📊 Нет сообщений {periods[period]}!")
        await ctx.message.delete()
        return

    sorted_users = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]

    embed = discord.Embed(
        title=f"🏆 Топ-10 по сообщениям {periods[period]}",
        color=0xffd700,
        timestamp=datetime.now()
    )

    text = ""
    for i, (user_id, count) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            if user:
                guild = ctx.guild
                member = guild.get_member(int(user_id))
                display_name = member.display_name if member else user.name
                name = user.name
            else:
                display_name = "Неизвестный"
                name = "Неизвестный"
        except:
            display_name = "Неизвестный"
            name = "Неизвестный"

        medal = get_medal(i)
        text += f"{medal} **{display_name}** ({name}) - {count} сообщений\n"

    embed.description = text if text else "Нет данных"
    embed.set_footer(text=f"Всего пользователей: {len(stats)}")
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='topvoice', aliases=['топвойс'])
async def top_voice(ctx, period: str = None):
    """Топ пользователей по времени в голосе. Периоды: day, week, month, year, all"""
    
    periods = {
        "day": "за сегодня",
        "week": "за неделю",
        "month": "за месяц",
        "year": "за год",
        "all": "за всё время"
    }
    
    # Если период не указан - показываем меню выбора
    if period is None:
        await top_menu(ctx)
        return

    if period not in periods:
        await ctx.send(f"❌ Неверный период! Доступны: `day`, `week`, `month`, `year`, `all`")
        await ctx.message.delete()
        return

    if not data['voice_history']:
        await ctx.send("📊 Нет данных о голосовой активности!")
        await ctx.message.delete()
        return

    stats = {}
    for user_id, seconds_list in data['voice_history'].items():
        filtered = get_time_filter(seconds_list, period)
        if filtered:
            stats[user_id] = sum(filtered)

    if not stats:
        await ctx.send(f"📊 Нет голосовой активности {periods[period]}!")
        await ctx.message.delete()
        return

    sorted_users = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]

    embed = discord.Embed(
        title=f"🎙️ Топ-10 по времени в войсе {periods[period]}",
        color=0x5865F2,
        timestamp=datetime.now()
    )

    text = ""
    for i, (user_id, seconds) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            if user:
                guild = ctx.guild
                member = guild.get_member(int(user_id))
                display_name = member.display_name if member else user.name
                name = user.name
            else:
                display_name = "Неизвестный"
                name = "Неизвестный"
        except:
            display_name = "Неизвестный"
            name = "Неизвестный"

        medal = get_medal(i)
        text += f"{medal} **{display_name}** ({name}) - {format_time(seconds)}\n"

    embed.description = text if text else "Нет данных"
    embed.set_footer(text=f"Всего пользователей: {len(stats)}")
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


# ----- КОМАНДЫ СТАТИСТИКИ -----
@bot.command(name='daystats', aliases=['день'])
async def day_stats(ctx):
    """Дневная статистика"""
    stats = data['daily_stats']

    if stats['date'] is None or (not stats['messages'] and not stats['voice_time']):
        await ctx.send(f"📊 **Статистика за сегодня ({datetime.now(MSK).date().isoformat()})**\nПока нет данных!")
        await ctx.message.delete()
        return

    embed = discord.Embed(
        title=f"📊 Дневная статистика",
        description=f"**Дата:** {stats['date']}",
        color=0x00ff00,
        timestamp=datetime.now(MSK)
    )

    if stats['messages']:
        sorted_msgs = sorted(stats['messages'].items(), key=lambda x: x[1], reverse=True)[:5]
        msgs_text = ""
        for i, (user_id, count) in enumerate(sorted_msgs, 1):
            try:
                user = await bot.fetch_user(int(user_id))
                name = user.name if user else "Неизвестный"
            except:
                name = "Неизвестный"
            msgs_text += f"{get_medal(i)} {name} - {count} сообщений\n"
        embed.add_field(name="💬 Топ сообщений", value=msgs_text, inline=True)

    if stats['voice_time']:
        sorted_voice = sorted(stats['voice_time'].items(), key=lambda x: x[1], reverse=True)[:5]
        voice_text = ""
        for i, (user_id, seconds) in enumerate(sorted_voice, 1):
            try:
                user = await bot.fetch_user(int(user_id))
                name = user.name if user else "Неизвестный"
            except:
                name = "Неизвестный"
            voice_text += f"{get_medal(i)} {name} - {format_time(seconds)}\n"
        embed.add_field(name="🎙️ Топ голоса", value=voice_text, inline=True)

    total_msgs = sum(stats['messages'].values())
    total_voice = sum(stats['voice_time'].values())
    embed.add_field(
        name="📈 Итого за день",
        value=f"💬 Всего сообщений: {total_msgs}\n🎙️ Всего в голосе: {format_time(total_voice)}",
        inline=False
    )
    embed.set_footer(text="Обнуляется в 00:00 по МСК")
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='weekstats', aliases=['неделя'])
async def week_stats(ctx):
    """Недельная статистика"""
    stats = data['weekly_stats']

    if stats['week_start'] is None or (not stats['messages'] and not stats['voice_time']):
        await ctx.send(f"📊 **Статистика за эту неделю (с {stats['week_start']})**\nПока нет данных!")
        await ctx.message.delete()
        return

    embed = discord.Embed(
        title=f"📊 Недельная статистика",
        description=f"**Неделя начинается:** {stats['week_start']}",
        color=0x00ff00,
        timestamp=datetime.now(MSK)
    )

    if stats['messages']:
        sorted_msgs = sorted(stats['messages'].items(), key=lambda x: x[1], reverse=True)[:5]
        msgs_text = ""
        for i, (user_id, count) in enumerate(sorted_msgs, 1):
            try:
                user = await bot.fetch_user(int(user_id))
                name = user.name if user else "Неизвестный"
            except:
                name = "Неизвестный"
            msgs_text += f"{get_medal(i)} {name} - {count} сообщений\n"
        embed.add_field(name="💬 Топ сообщений", value=msgs_text, inline=True)

    if stats['voice_time']:
        sorted_voice = sorted(stats['voice_time'].items(), key=lambda x: x[1], reverse=True)[:5]
        voice_text = ""
        for i, (user_id, seconds) in enumerate(sorted_voice, 1):
            try:
                user = await bot.fetch_user(int(user_id))
                name = user.name if user else "Неизвестный"
            except:
                name = "Неизвестный"
            voice_text += f"{get_medal(i)} {name} - {format_time(seconds)}\n"
        embed.add_field(name="🎙️ Топ голоса", value=voice_text, inline=True)

    total_msgs = sum(stats['messages'].values())
    total_voice = sum(stats['voice_time'].values())
    embed.add_field(
        name="📈 Итого за неделю",
        value=f"💬 Всего сообщений: {total_msgs}\n🎙️ Всего в голосе: {format_time(total_voice)}",
        inline=False
    )
    embed.set_footer(text="Обнуляется в понедельник 00:00 по МСК")
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='monthstats', aliases=['месяц'])
async def month_stats(ctx):
    """Месячная статистика"""
    stats = data['monthly_stats']

    if stats['month'] is None or (not stats['messages'] and not stats['voice_time']):
        await ctx.send(f"📊 **Статистика за {stats['month']}**\nПока нет данных!")
        await ctx.message.delete()
        return

    embed = discord.Embed(
        title=f"📊 Месячная статистика",
        description=f"**Месяц:** {stats['month']}",
        color=0x00ff00,
        timestamp=datetime.now(MSK)
    )

    if stats['messages']:
        sorted_msgs = sorted(stats['messages'].items(), key=lambda x: x[1], reverse=True)[:5]
        msgs_text = ""
        for i, (user_id, count) in enumerate(sorted_msgs, 1):
            try:
                user = await bot.fetch_user(int(user_id))
                name = user.name if user else "Неизвестный"
            except:
                name = "Неизвестный"
            msgs_text += f"{get_medal(i)} {name} - {count} сообщений\n"
        embed.add_field(name="💬 Топ сообщений", value=msgs_text, inline=True)

    if stats['voice_time']:
        sorted_voice = sorted(stats['voice_time'].items(), key=lambda x: x[1], reverse=True)[:5]
        voice_text = ""
        for i, (user_id, seconds) in enumerate(sorted_voice, 1):
            try:
                user = await bot.fetch_user(int(user_id))
                name = user.name if user else "Неизвестный"
            except:
                name = "Неизвестный"
            voice_text += f"{get_medal(i)} {name} - {format_time(seconds)}\n"
        embed.add_field(name="🎙️ Топ голоса", value=voice_text, inline=True)

    total_msgs = sum(stats['messages'].values())
    total_voice = sum(stats['voice_time'].values())
    embed.add_field(
        name="📈 Итого за месяц",
        value=f"💬 Всего сообщений: {total_msgs}\n🎙️ Всего в голосе: {format_time(total_voice)}",
        inline=False
    )
    embed.set_footer(text="Обнуляется 1-го числа каждого месяца в 00:00 по МСК")
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


# ----- ОБРАБОТЧИКИ -----
@tasks.loop(seconds=VOICE_CHECK_INTERVAL)
async def voice_tracker():
    for guild in bot.guilds:
        for voice_channel in guild.voice_channels:
            for member in voice_channel.members:
                if member.bot:
                    continue
                
                user_id = str(member.id)
                current_time = datetime.now().timestamp()
                
                if not member.voice or not member.voice.channel:
                    continue
                
                if user_id not in data['voice_time']:
                    data['voice_time'][user_id] = 0
                if user_id not in data['voice_total_time']:
                    data['voice_total_time'][user_id] = 0
                if user_id not in data['voice_history']:
                    data['voice_history'][user_id] = []
                if user_id not in data['voice_last_check']:
                    data['voice_last_check'][user_id] = current_time
                
                time_delta = current_time - data['voice_last_check'][user_id]
                if time_delta >= VOICE_CHECK_INTERVAL:
                    data['voice_time'][user_id] += time_delta
                    data['voice_total_time'][user_id] += time_delta
                    data['voice_history'][user_id].append(time_delta)
                    data['voice_last_check'][user_id] = current_time
                    
                    add_daily_voice(user_id, time_delta)
                    add_weekly_voice(user_id, time_delta)
                    add_monthly_voice(user_id, time_delta)
                    
                    if data['voice_time'][user_id] >= 3600:
                        hours_earned = int(data['voice_time'][user_id] // 3600)
                        shards_earned = hours_earned * VOICE_HOUR_SHARDS
                        
                        if shards_earned > 0:
                            if user_id not in data['balance']:
                                data['balance'][user_id] = 0
                            data['balance'][user_id] += shards_earned
                            data['voice_time'][user_id] = data['voice_time'][user_id] % 3600
                            save_data(data)
                            
                            try:
                                embed = discord.Embed(
                                    title=f"🎙️ +{shards_earned} Осколков за голос!",
                                    description=f"Вы получили {shards_earned} осколков за {hours_earned} час(ов) в голосовом канале!\nВсего осколков: {data['balance'][user_id]} 💎",
                                    color=0x00ff00
                                )
                                await member.send(embed=embed)
                            except:
                                pass
                            save_data(data)


@bot.event
async def on_message(message):
    # Игнорируем сообщения бота
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

    if user_id not in data['messages_history']:
        data['messages_history'][user_id] = []
    data['messages_history'][user_id].append(current_time)

    add_daily_message(user_id)
    add_weekly_message(user_id)
    add_monthly_message(user_id)

    if user_id not in data['messages_count']:
        data['messages_count'][user_id] = 0
    data['messages_count'][user_id] += 1

    if data['messages_count'][user_id] >= MESSAGES_PER_SHARD:
        if user_id not in data['balance']:
            data['balance'][user_id] = 0
        data['balance'][user_id] += SHARDS_PER_MESSAGES
        data['messages_count'][user_id] = 0
        save_data(data)

        try:
            embed = discord.Embed(
                title=f"💎 +{SHARDS_PER_MESSAGES} Осколок!",
                description=f"Вы получили {SHARDS_PER_MESSAGES} осколок за {MESSAGES_PER_SHARD} сообщений!\nВсего осколков: {data['balance'][user_id]} 💎",
                color=0xffd700
            )
            await message.channel.send(f"{message.author.mention}", embed=embed, delete_after=5)
        except:
            pass

    await bot.process_commands(message)


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == VOICE_TRIGGER_ID:
        await create_private_voice(member)
    
    if before.channel and before.channel.id in private_voice_channels:
        if len(before.channel.members) == 0:
            await delete_empty_voice(before.channel)
    
    user_id = str(member.id)
    current_time = datetime.now().timestamp()
    
    if before.channel is not None and after.channel is None:
        if user_id in data['voice_last_check'] and data['voice_last_check'][user_id] > 0:
            time_delta = current_time - data['voice_last_check'][user_id]
            if time_delta > 0:
                data['voice_time'][user_id] = data['voice_time'].get(user_id, 0) + time_delta
                data['voice_total_time'][user_id] = data['voice_total_time'].get(user_id, 0) + time_delta
                data['voice_history'][user_id].append(time_delta)
                
                add_daily_voice(user_id, time_delta)
                add_weekly_voice(user_id, time_delta)
                add_monthly_voice(user_id, time_delta)
                
                if data['voice_time'][user_id] >= 3600:
                    hours_earned = int(data['voice_time'][user_id] // 3600)
                    shards_earned = hours_earned * VOICE_HOUR_SHARDS
                    
                    if shards_earned > 0:
                        if user_id not in data['balance']:
                            data['balance'][user_id] = 0
                        data['balance'][user_id] += shards_earned
                        data['voice_time'][user_id] = data['voice_time'][user_id] % 3600
                        save_data(data)
                        
                        try:
                            embed = discord.Embed(
                                title=f"🎙️ +{shards_earned} Осколков за голос!",
                                description=f"Вы получили {shards_earned} осколков за {hours_earned} час(ов) в голосовом канале!\nВсего осколков: {data['balance'][user_id]} 💎",
                                color=0x00ff00
                            )
                            await member.send(embed=embed)
                        except:
                            pass
                        save_data(data)
            
            data['voice_last_check'][user_id] = 0
            save_data(data)
    
    elif after.channel is not None and before.channel is None:
        data['voice_last_check'][user_id] = current_time
        if user_id not in data['voice_time']:
            data['voice_time'][user_id] = 0
        if user_id not in data['voice_total_time']:
            data['voice_total_time'][user_id] = 0
        if user_id not in data['voice_history']:
            data['voice_history'][user_id] = []
        save_data(data)
    
    elif before.channel is not None and after.channel is not None:
        if user_id in data['voice_last_check'] and data['voice_last_check'][user_id] > 0:
            time_delta = current_time - data['voice_last_check'][user_id]
            if time_delta > 0:
                data['voice_time'][user_id] = data['voice_time'].get(user_id, 0) + time_delta
                data['voice_total_time'][user_id] = data['voice_total_time'].get(user_id, 0) + time_delta
                data['voice_history'][user_id].append(time_delta)
                
                add_daily_voice(user_id, time_delta)
                add_weekly_voice(user_id, time_delta)
                add_monthly_voice(user_id, time_delta)
                
                if data['voice_time'][user_id] >= 3600:
                    hours_earned = int(data['voice_time'][user_id] // 3600)
                    shards_earned = hours_earned * VOICE_HOUR_SHARDS
                    
                    if shards_earned > 0:
                        if user_id not in data['balance']:
                            data['balance'][user_id] = 0
                        data['balance'][user_id] += shards_earned
                        data['voice_time'][user_id] = data['voice_time'][user_id] % 3600
                        save_data(data)
                        
                        try:
                            embed = discord.Embed(
                                title=f"🎙️ +{shards_earned} Осколков за голос!",
                                description=f"Вы получили {shards_earned} осколков за {hours_earned} час(ов) в голосовом канале!\nВсего осколков: {data['balance'][user_id]} 💎",
                                color=0x00ff00
                            )
                            await member.send(embed=embed)
                        except:
                            pass
                        save_data(data)
        
        data['voice_last_check'][user_id] = current_time
        save_data(data)


async def create_private_voice(member):
    guild = member.guild
    category = guild.get_channel(PRIVATE_VOICE_CATEGORY_ID)
    if not category:
        return

    voice_channel = await guild.create_voice_channel(
        name=f"🔒 {member.display_name}'s Voice",
        category=category,
        user_limit=0
    )

    await voice_channel.set_permissions(member, connect=True, manage_channels=True, mute_members=True, deafen_members=True)
    await voice_channel.set_permissions(guild.default_role, connect=False, view_channel=False)

    private_voice_channels[voice_channel.id] = member.id
    voice_settings[voice_channel.id] = {
        'owner_id': member.id,
        'max_users': 0,
        'banned_users': [],
        'hidden': False,
        'created_at': datetime.now().timestamp()
    }

    str_id = str(voice_channel.id)
    data['private_voice_settings'][str_id] = {
        'owner_id': member.id,
        'max_users': 0,
        'banned_users': [],
        'hidden': False,
        'created_at': datetime.now().timestamp()
    }
    save_data(data)

    await member.move_to(voice_channel)

    view = VoiceControlView(voice_channel.id, member.id)
    embed = discord.Embed(
        title="🔒 Приватный войс создан!",
        description="**Управляйте своим каналом через кнопки ниже:**\n\n👥 **Лимит** - установить максимум пользователей\n🚫 **Бан** - запретить вход пользователю\n✅ **Разбан** - разрешить вход\n👁️ **Скрыть/Показать** - скрыть канал от всех\n👢 **Кик** - выгнать из канала\n🗑️ **Удалить** - удалить канал\n📊 **Инфо** - информация о канале",
        color=0x00ff00
    )

    msg = await voice_channel.send(embed=embed, view=view)
    view.message = msg


async def delete_empty_voice(channel):
    await asyncio.sleep(10)
    if channel.id in private_voice_channels and len(channel.members) == 0:
        try:
            str_id = str(channel.id)
            if str_id in data['private_voice_settings']:
                del data['private_voice_settings'][str_id]
                save_data(data)
            del private_voice_channels[channel.id]
            if channel.id in voice_settings:
                del voice_settings[channel.id]
            await channel.delete()
        except:
            pass


async def handle_ban(interaction, member, channel):
    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ Нельзя забанить самого себя!", ephemeral=True)
        return

    str_id = str(channel.id)
    if str_id not in data['private_voice_settings']:
        data['private_voice_settings'][str_id] = {'banned_users': []}

    if member.id in data['private_voice_settings'][str_id]['banned_users']:
        await interaction.response.send_message(f"❌ {member.mention} уже забанен!", ephemeral=True)
        return

    data['private_voice_settings'][str_id]['banned_users'].append(member.id)
    save_data(data)

    if channel and member in channel.members:
        await member.move_to(None)

    await channel.set_permissions(member, connect=False)
    await interaction.response.send_message(f"✅ {member.mention} забанен в этом канале!", ephemeral=True)


async def handle_unban(interaction, member, channel):
    str_id = str(channel.id)
    if str_id not in data['private_voice_settings']:
        await interaction.response.send_message("❌ Нет забаненных пользователей!", ephemeral=True)
        return

    if member.id not in data['private_voice_settings'][str_id]['banned_users']:
        await interaction.response.send_message(f"❌ {member.mention} не в бане!", ephemeral=True)
        return

    data['private_voice_settings'][str_id]['banned_users'].remove(member.id)
    save_data(data)

    if channel:
        await channel.set_permissions(member, connect=None)

    await interaction.response.send_message(f"✅ {member.mention} разбанен!", ephemeral=True)


async def handle_kick(interaction, member, channel):
    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ Нельзя кикнуть самого себя!", ephemeral=True)
        return

    if not channel or member not in channel.members:
        await interaction.response.send_message(f"❌ {member.mention} не в этом канале!", ephemeral=True)
        return

    await member.move_to(None)
    await interaction.response.send_message(f"✅ {member.mention} кикнут из канала!", ephemeral=True)


async def show_user_select(interaction, channel_id, action):
    channel = interaction.guild.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
        return

    if action == "kick":
        users = [m for m in channel.members if m.id != interaction.user.id]
        if not users:
            await interaction.response.send_message("❌ В канале нет других пользователей!", ephemeral=True)
            return
    elif action == "ban":
        users = [m for m in interaction.guild.members if not m.bot and m.id != interaction.user.id]
        if not users:
            await interaction.response.send_message("❌ Нет пользователей для бана!", ephemeral=True)
            return
    else:
        str_id = str(channel_id)
        banned_ids = data['private_voice_settings'].get(str_id, {}).get('banned_users', [])
        users = []
        for uid in banned_ids:
            m = interaction.guild.get_member(uid)
            if m:
                users.append(m)
        if not users:
            await interaction.response.send_message("❌ Нет забаненных пользователей!", ephemeral=True)
            return

    view = UserSelectView(channel_id, action, users)
    await interaction.response.send_message("👤 **Выберите пользователя:**", view=view, ephemeral=True)


# ----- КОМАНДА DAILY -----
@bot.command(name='daily')
async def daily_bonus(ctx):
    """Ежедневный бонус"""
    user_id = str(ctx.author.id)
    today = datetime.now(MSK).date().isoformat()

    if user_id in data['daily'] and data['daily'][user_id] == today:
        await ctx.send("❌ Вы уже получили бонус сегодня! Приходите завтра в 00:00 по МСК.")
        await ctx.message.delete()
        return

    if user_id not in data['balance']:
        data['balance'][user_id] = 0
    data['balance'][user_id] += DAILY_BONUS
    data['daily'][user_id] = today
    save_data(data)

    embed = discord.Embed(
        title="🎉 Ежедневный бонус!",
        description=f"Вы получили **+{DAILY_BONUS} осколков** 💎\n\n**Новый баланс:** {data['balance'][user_id]} 💎\n\nБонус доступен раз в день, сброс в 00:00 по МСК!",
        color=0xffd700
    )
    embed.set_footer(text="📅 Боженька заботится о вас ✨")
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


# ----- ОСТАЛЬНЫЕ КОМАНДЫ (С УДАЛЕНИЕМ СООБЩЕНИЙ) -----
@bot.command(name='status', aliases=['stats'])
async def bot_status(ctx):
    """Статус бота"""
    global bog_member
    embed = discord.Embed(title="📊 Статус бота", color=0x00ff00, timestamp=datetime.now())
    embed.add_field(name="🤖 Бот", value=f"**Пинг:** {round(bot.latency * 1000)}ms\n**Серверов:** {len(bot.guilds)}", inline=False)
    if bog_member:
        status_text = {
            discord.Status.online: "🟢 В сети",
            discord.Status.idle: "🟡 Отошел",
            discord.Status.dnd: "🔴 Не беспокоить",
            discord.Status.offline: "⚫ Не в сети"
        }
        embed.add_field(name="👁️ Боженька", value=status_text.get(bog_member.status, "❓ Неизвестно"), inline=False)
    total_balance = sum(data['balance'].values()) if data['balance'] else 0
    total_voice = sum(data['voice_total_time'].values()) if data['voice_total_time'] else 0
    total_messages = sum(len(msgs) for msgs in data['messages_history'].values()) if data['messages_history'] else 0
    total_referrals = sum(data['referral_count'].values()) if data['referral_count'] else 0
    rate = data.get('exchange_rate', 5)
    total_rubles = round(total_balance / rate, 2) if rate > 0 else 0
    embed.add_field(name="💰 Экономика", value=f"**Всего осколков:** {total_balance} 💎\n**Пользователей:** {len(data['balance'])}\n**Курс:** 1 ₽ = {rate} 💎", inline=False)
    embed.add_field(name="📊 Активность", value=f"**Всего сообщений:** {total_messages}\n**Всего в войсе:** {format_time(total_voice)}\n**Приглашений:** {total_referrals}", inline=False)
    
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='rate', aliases=['курс'])
async def show_rate(ctx):
    """Показать текущий курс"""
    rate = data.get('exchange_rate', 5)
    embed = discord.Embed(
        title="💱 Текущий курс",
        description=f"""**1 рубль = {rate} осколков** 💎
**1 осколок = {round(1/rate, 2)} рублей**

💬 **{MESSAGES_PER_SHARD} сообщений = {SHARDS_PER_MESSAGES} осколок**
🎙️ **1 час в войсе = {VOICE_HOUR_SHARDS} осколков**
📅 **Ежедневный бонус: +{DAILY_BONUS} 💎**
👥 **За приглашение друга: +{REFERRAL_BONUS} 💎**""",
        color=0x00ff00
    )
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='setrate', aliases=['установитькурс'])
@commands.check(is_owner_or_bog)
async def set_exchange_rate(ctx, rate: str):
    """Установить курс (Владелец/Боженька)"""
    try:
        rate = float(rate.replace(',', '.'))
    except ValueError:
        await ctx.send("❌ Неверный формат! Используйте число, например: `0.5`, `2`, `3.5`")
        await ctx.message.delete()
        return
    if rate <= 0:
        await ctx.send("❌ Курс должен быть положительным!")
        await ctx.message.delete()
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
    try:
        await ctx.message.delete()
    except:
        pass


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
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='profile', aliases=['профиль'])
async def profile(ctx, member: discord.Member = None):
    """Профиль пользователя"""
    if member is None:
        member = ctx.author
    user_id = str(member.id)
    balance = data['balance'].get(user_id, 0)
    messages = len(data['messages_history'].get(user_id, []))
    voice_seconds = data['voice_total_time'].get(user_id, 0)
    voice_hours = voice_seconds // 3600
    voice_minutes = (voice_seconds % 3600) // 60
    warns = len(data['warns'].get(user_id, {}))
    referrals = data['referral_count'].get(user_id, 0)
    roles = [role.mention for role in member.roles if role.name != "@everyone"]
    roles_text = ", ".join(roles) if roles else "Нет ролей"
    embed = discord.Embed(title=f"👤 Профиль {member.display_name}", color=member.color or 0x5865F2, timestamp=datetime.now())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="📋 Основная информация", value=f"**ID:** {member.id}\n**Имя:** {member.name}\n**Отображаемое имя:** {member.display_name}\n**Аккаунт создан:** {member.created_at.strftime('%d.%m.%Y')}", inline=False)
    embed.add_field(name="💰 Баланс", value=f"**Осколки:** {balance} 💎", inline=True)
    embed.add_field(name="💬 Активность", value=f"**Сообщений:** {messages}\n**В голосе:** {voice_hours}ч {voice_minutes}м\n**Варнов:** {warns}\n**Пригласил:** {referrals} друзей", inline=True)
    embed.add_field(name="🎖️ Роли", value=roles_text[:1024] if len(roles_text) <= 1024 else roles_text[:1021] + "...", inline=False)
    embed.set_footer(text=f"Запросил: {ctx.author.display_name}")
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='mystats', aliases=['моястата'])
async def my_stats(ctx, period: str = "all"):
    """Моя статистика за период"""
    periods = {
        "day": "за день",
        "week": "за неделю",
        "month": "за месяц",
        "year": "за год",
        "all": "за всё время"
    }

    if period not in periods:
        await ctx.send(f"❌ Неверный период! Доступны: `day`, `week`, `month`, `year`, `all`")
        await ctx.message.delete()
        return

    user_id = str(ctx.author.id)

    msgs = data['messages_history'].get(user_id, [])
    msg_count = len(get_time_filter(msgs, period))

    voice = data['voice_history'].get(user_id, [])
    voice_seconds = sum(get_time_filter(voice, period))

    balance = data['balance'].get(user_id, 0)

    embed = discord.Embed(
        title=f"📊 Моя статистика {periods[period]}",
        color=ctx.author.color or 0x5865F2,
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)

    embed.add_field(name="💬 Сообщений", value=f"{msg_count}", inline=True)
    embed.add_field(name="🎙️ В голосе", value=format_time(voice_seconds), inline=True)
    embed.add_field(name="💎 Баланс", value=f"{balance} 💎", inline=True)

    current_msgs = data['messages_count'].get(user_id, 0)
    needed = MESSAGES_PER_SHARD - current_msgs
    embed.add_field(name="📈 До следующего осколка", value=f"{needed} сообщений", inline=False)

    embed.set_footer(text=f"Запросил: {ctx.author.display_name}")
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='msgstats', aliases=['сообщения'])
async def message_stats(ctx, member: discord.Member = None):
    """Статистика сообщений пользователя"""
    if member is None:
        member = ctx.author
    user_id = str(member.id)
    msg_count = data['messages_count'].get(user_id, 0)
    needed = MESSAGES_PER_SHARD - msg_count
    total = len(data['messages_history'].get(user_id, []))

    embed = discord.Embed(title="📊 Статистика сообщений", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Всего сообщений", value=f"{total}")
    embed.add_field(name="Текущий прогресс", value=f"{msg_count} / {MESSAGES_PER_SHARD}")
    embed.add_field(name="До следующего бонуса", value=f"{needed} сообщений → +{SHARDS_PER_MESSAGES} 💎")
    embed.set_footer(text=f"За каждые {MESSAGES_PER_SHARD} сообщений вы получаете {SHARDS_PER_MESSAGES} осколок")
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='voicestats', aliases=['войсстат', 'voice'])
async def voice_stats(ctx, member: discord.Member = None):
    """Статистика голосовых каналов пользователя"""
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

    embed = discord.Embed(title="🎙️ Статистика голосовых каналов", color=0x00ff00, timestamp=datetime.now())
    embed.add_field(name="Пользователь", value=member.mention, inline=False)
    embed.add_field(name="⏱️ Текущая сессия", value=format_time(voice_seconds), inline=True)
    embed.add_field(name="📊 Всего времени", value=format_time(total_seconds + voice_seconds), inline=True)
    embed.add_field(name="💎 Заработано осколков", value=f"{shards_earned} 💎", inline=True)
    embed.add_field(name="📈 Прогресс до следующего бонуса", value=f"{format_time(voice_seconds % 3600)} / 1ч → +{VOICE_HOUR_SHARDS} 💎", inline=False)
    embed.set_footer(text=f"1 час в войсе = {VOICE_HOUR_SHARDS} осколков")
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


# ----- МОДЕРАЦИЯ (С УДАЛЕНИЕМ КОМАНД) -----
@bot.command(name='mute', aliases=['мут'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'],
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def mute(ctx, member: discord.Member, time: str, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя замутить этого пользователя!")
        await ctx.message.delete()
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя мутить Боженьку!")
        await ctx.message.delete()
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
        await ctx.message.delete()
        return
    await member.timeout(timedelta(seconds=time_seconds), reason=reason)
    embed = discord.Embed(title="🔇 Мут", color=0xff0000)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Время", value=time)
    embed.add_field(name="Причина", value=reason)
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='unmute', aliases=['размут'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'],
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def unmute(ctx, member: discord.Member):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя размутить!")
        await ctx.message.delete()
        return
    await member.timeout(None)
    await ctx.send(f"✅ {member.mention} размучен!")
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='ban', aliases=['бан'])
@commands.has_any_role(*[ROLES['admin'], ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def ban(ctx, member: discord.Member, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя забанить!")
        await ctx.message.delete()
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя банить Боженьку!")
        await ctx.message.delete()
        return
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member.mention} забанен! Причина: {reason}")
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='kick', aliases=['кик'])
@commands.has_any_role(*[ROLES['moderator'], ROLES['admin'], ROLES['head_admin'],
                         ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def kick(ctx, member: discord.Member, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя кикнуть!")
        await ctx.message.delete()
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя кикать Боженьку!")
        await ctx.message.delete()
        return
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.mention} кикнут! Причина: {reason}")
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='warn', aliases=['варн'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'],
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def warn(ctx, member: discord.Member, time: str, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя выдать варн!")
        await ctx.message.delete()
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя варнить Боженьку!")
        await ctx.message.delete()
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
        await ctx.message.delete()
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
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='warns', aliases=['варны'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'],
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def warns(ctx, member: discord.Member):
    if str(member.id) not in data['warns'] or not data['warns'][str(member.id)]:
        await ctx.send(f"✅ У {member.mention} нет варнов.")
        await ctx.message.delete()
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
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='unwarn', aliases=['разварн'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'],
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def unwarn(ctx, member: discord.Member, warn_id: str):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя снять варн!")
        await ctx.message.delete()
        return
    if str(member.id) in data['warns'] and warn_id in data['warns'][str(member.id)]:
        del data['warns'][str(member.id)][warn_id]
        save_data(data)
        await ctx.send(f"✅ Варн снят с {member.mention}")
    else:
        await ctx.send(f"❌ Варн не найден!")
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='clear', aliases=['очистить', 'cls'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'],
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def clear_channel(ctx, amount: int = None):
    if amount is None:
        await ctx.send("❌ Укажите количество. Пример: `j.clear 50`")
        await ctx.message.delete()
        return
    if amount < 1 or amount > 1000:
        await ctx.send("❌ Можно удалить от 1 до 1000 сообщений!")
        await ctx.message.delete()
        return
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ Удалено {len(deleted) - 1} сообщений!", delete_after=3)
        await ctx.message.delete()
    except Exception:
        await ctx.send("❌ Ошибка при удалении!")
        await ctx.message.delete()


@bot.command(name='clearall', aliases=['очиститьвсе'])
@commands.has_any_role(*[ROLES['admin'], ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def clear_all(ctx):
    confirm_msg = await ctx.send(
        "⚠️ **ВНИМАНИЕ!** Вы уверены, что хотите удалить **ВСЕ** сообщения в этом канале?\nЗакрепленные сообщения **НЕ будут** удалены.\n\nНапишите `да` в течение 10 секунд для подтверждения.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "да"

    try:
        await bot.wait_for('message', timeout=10.0, check=check)
        await ctx.message.delete()
    except asyncio.TimeoutError:
        await confirm_msg.edit(content="❌ Операция отменена (таймаут).")
        await ctx.message.delete()
        return

    status_msg = await confirm_msg.edit(content="🔄 **Начинаю очистку канала...**")

    try:
        pinned_messages = await ctx.channel.pins()
        pinned_ids = [msg.id for msg in pinned_messages]

        def is_not_pinned(msg):
            return msg.id not in pinned_ids

        deleted = await ctx.channel.purge(
            limit=None,
            check=is_not_pinned,
            bulk=True
        )

        embed = discord.Embed(
            title="✅ Канал очищен!",
            description=f"**Удалено:** {len(deleted)} сообщений\n**Закрепленных сохранено:** {len(pinned_ids)}",
            color=0x00ff00
        )
        await ctx.send(embed=embed, delete_after=10)
        await ctx.message.delete()

    except discord.Forbidden:
        await status_msg.edit(content="❌ У меня нет прав на удаление сообщений в этом канале!")
        await ctx.message.delete()
    except discord.HTTPException as e:
        if "14 days" in str(e) or "Bulk delete" in str(e):
            await status_msg.edit(content="⚠️ **Есть сообщения старше 14 дней, удаляю по одному...**")
            await ctx.message.delete()

            deleted_count = 0
            async for message in ctx.channel.history(limit=None):
                if message.id in pinned_ids:
                    continue
                try:
                    await message.delete()
                    deleted_count += 1
                    if deleted_count % 50 == 0:
                        await status_msg.edit(content=f"🔄 **Удалено {deleted_count} сообщений...**")
                    await asyncio.sleep(0.2)
                except:
                    pass

            embed = discord.Embed(
                title="✅ Канал очищен!",
                description=f"**Удалено:** {deleted_count} сообщений\n**Закрепленных сохранено:** {len(pinned_ids)}",
                color=0x00ff00
            )
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete()
        else:
            await status_msg.edit(content=f"❌ Ошибка: {e}")
            await ctx.message.delete()
    except Exception as e:
        await status_msg.edit(content=f"❌ Ошибка: {e}")
        await ctx.message.delete()


# ----- ЭКОНОМИКА -----
@bot.command(name='add')
@commands.check(can_manage_economy)
async def add_shards(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Количество должно быть положительным!")
        await ctx.message.delete()
        return
    if str(member.id) not in data['balance']:
        data['balance'][str(member.id)] = 0
    data['balance'][str(member.id)] += amount
    save_data(data)
    embed = discord.Embed(title="➕ Выдача осколков", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Получено", value=f"+{amount} 💎")
    embed.add_field(name="Новый баланс", value=f"{data['balance'][str(member.id)]} 💎")
    embed.set_footer(text=f"Выдал: {ctx.author.display_name}")
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='remove')
@commands.check(can_manage_economy)
async def remove_shards(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Количество должно быть положительным!")
        await ctx.message.delete()
        return
    if str(member.id) not in data['balance']:
        data['balance'][str(member.id)] = 0
    if data['balance'][str(member.id)] < amount:
        await ctx.send(f"❌ У {member.mention} недостаточно осколков!")
        await ctx.message.delete()
        return
    data['balance'][str(member.id)] -= amount
    save_data(data)
    embed = discord.Embed(title="➖ Снятие осколков", color=0xff0000)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Снято", value=f"-{amount} 💎")
    embed.add_field(name="Новый баланс", value=f"{data['balance'][str(member.id)]} 💎")
    embed.set_footer(text=f"Снял: {ctx.author.display_name}")
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


# ----- РЕФЕРАЛЫ -----
@bot.command(name='referral', aliases=['реферал', 'invite'])
async def create_referral(ctx):
    user_id = str(ctx.author.id)
    if user_id in data['referral_links']:
        code = data['referral_links'][user_id]
        invite_link = f"https://discord.gg/{code}"
        embed = discord.Embed(
            title="👥 Ваша реферальная ссылка",
            description=f"**Ссылка:** {invite_link}\n\nЗа каждого пришедшего по вашей ссылке вы получите **{REFERRAL_BONUS} осколков**!",
            color=0x00ff00
        )
        embed.set_footer(text="Поделитесь ссылкой с друзьями!")
        await ctx.send(embed=embed)
        await ctx.message.delete()
        return
    try:
        channel = ctx.guild.text_channels[0]
        invite = await channel.create_invite(max_age=0, max_uses=0, unique=True)
        code = invite.code
        data['referral_links'][user_id] = code
        save_data(data)
        embed = discord.Embed(
            title="👥 Реферальная ссылка создана!",
            description=f"**Ссылка:** {invite.url}\n\nЗа каждого пришедшего по вашей ссылке вы получите **{REFERRAL_BONUS} осколков**!",
            color=0x00ff00
        )
        embed.set_footer(text="Поделитесь ссылкой с друзьями!")
        await ctx.send(embed=embed)
        await ctx.message.delete()
    except Exception as e:
        await ctx.send(f"❌ Ошибка создания ссылки: {e}")
        await ctx.message.delete()


@bot.command(name='referrals', aliases=['рефералы'])
async def show_referrals(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    user_id = str(member.id)
    count = data['referral_count'].get(user_id, 0)
    embed = discord.Embed(title="👥 Реферальная статистика", color=0x5865F2)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Приглашено друзей", value=f"{count} человек")
    embed.add_field(name="Заработано осколков", value=f"{count * REFERRAL_BONUS} 💎")
    if user_id in data['referral_links']:
        code = data['referral_links'][user_id]
        embed.add_field(name="Ваша ссылка", value=f"https://discord.gg/{code}", inline=False)
    embed.set_footer(text=f"За каждого друга вы получаете {REFERRAL_BONUS} осколков")
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.event
async def on_member_join(member):
    invites = await member.guild.invites()
    for invite in invites:
        for user_id, code in data['referral_links'].items():
            if invite.code == code:
                if user_id not in data['balance']:
                    data['balance'][user_id] = 0
                data['balance'][user_id] += REFERRAL_BONUS
                if user_id not in data['referral_count']:
                    data['referral_count'][user_id] = 0
                data['referral_count'][user_id] += 1
                data['used_referrals'][str(member.id)] = user_id
                save_data(data)
                try:
                    inviter = await bot.fetch_user(int(user_id))
                    if inviter:
                        embed = discord.Embed(
                            title="👥 Новый реферал!",
                            description=f"По вашей ссылке зашел **{member.name}**!\nВы получили **{REFERRAL_BONUS} осколков**!",
                            color=0x00ff00
                        )
                        await inviter.send(embed=embed)
                except:
                    pass
                channel = bot.get_channel(LOG_CHANNEL_ID)
                if channel:
                    embed = discord.Embed(
                        title="👥 Новый участник по реферальной ссылке!",
                        description=f"**{member.mention}** зашел по ссылке **{member.name}**!\nПригласивший получил **{REFERRAL_BONUS} осколков**! 🎉",
                        color=0xffd700
                    )
                    await channel.send(embed=embed)
                break


# ----- ОТЧЕТЫ И БЭКАПЫ -----
@bot.command(name='report', aliases=['отчет'])
@commands.check(is_owner_or_bog)
async def create_report(ctx):
    await ctx.send("📊 **Создаю отчет... Ожидайте в личных сообщениях!**")
    await ctx.message.delete()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    rate = data.get('exchange_rate', 5)
    total_users = len(data['balance'])
    total_shards = sum(data['balance'].values())
    total_rubles = round(total_shards / rate, 2) if rate > 0 else 0
    total_referrals = sum(data['referral_count'].values()) if data['referral_count'] else 0
    txt_file = f"{REPORT_FOLDER}/report_{timestamp}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("📊 СТАТИСТИКА СЕРВЕРА\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write(f"💱 Курс: 1 ₽ = {rate} 💎\n")
        f.write(f"💬 За активность: {MESSAGES_PER_SHARD} сообщений = {SHARDS_PER_MESSAGES} 💎\n")
        f.write(f"🎙️ За голос: 1 час = {VOICE_HOUR_SHARDS} 💎\n")
        f.write(f"📅 Ежедневный бонус: +{DAILY_BONUS} 💎\n")
        f.write(f"👥 За приглашение: +{REFERRAL_BONUS} 💎\n\n")
        f.write("=" * 70 + "\n")
        f.write("📈 ОБЩАЯ СТАТИСТИКА\n")
        f.write("=" * 70 + "\n")
        f.write(f"👥 Всего пользователей: {total_users}\n")
        f.write(f"💎 Всего осколков: {total_shards}\n")
        f.write(f"💰 Всего рублей: {total_rubles} ₽\n")
        f.write(f"👥 Всего приглашений: {total_referrals}\n\n")
        total_messages = sum(len(msgs) for msgs in data['messages_history'].values()) if data['messages_history'] else 0
        total_voice = sum(data['voice_total_time'].values()) if data['voice_total_time'] else 0
        total_voice_hours = total_voice // 3600
        f.write("=" * 70 + "\n")
        f.write("💬 СТАТИСТИКА АКТИВНОСТИ\n")
        f.write("=" * 70 + "\n")
        f.write(f"📝 Всего сообщений: {total_messages}\n")
        f.write(f"💎 Заработано осколков за сообщения: {(total_messages // MESSAGES_PER_SHARD) * SHARDS_PER_MESSAGES}\n")
        f.write(f"🎙️ Всего часов в войсе: {total_voice_hours}\n")
        f.write(f"💎 Заработано осколков за голос: {total_voice_hours * VOICE_HOUR_SHARDS}\n\n")
        f.write("=" * 70 + "\n")
        f.write("👥 ВСЕ ПОЛЬЗОВАТЕЛИ (по убыванию баланса)\n")
        f.write("=" * 70 + "\n")
        f.write(f"{'ID':<20} | {'Имя':<25} | {'Осколки':<10} | {'Рубли':<10} | {'Daily':<12} | {'Варны'}\n")
        f.write("-" * 70 + "\n")
        for user_id, balance in sorted(data['balance'].items(), key=lambda x: x[1], reverse=True):
            try:
                user = await bot.fetch_user(int(user_id))
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


@bot.command(name='find', aliases=['найти'])
@commands.check(is_owner_or_bog)
async def find_user(ctx, user_id: int):
    uid = str(user_id)
    if uid not in data['balance']:
        await ctx.send(f"❌ Пользователь {user_id} не найден!")
        await ctx.message.delete()
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
    referrals = data['referral_count'].get(uid, 0)
    embed = discord.Embed(title=f"👤 {name}", color=0x00ff00)
    embed.add_field(name="ID", value=user_id, inline=True)
    embed.add_field(name="💎 Баланс", value=f"{balance} ({rubles} ₽)", inline=True)
    embed.add_field(name="📅 Daily", value=daily, inline=True)
    embed.add_field(name="⚠️ Варнов", value=warns, inline=True)
    embed.add_field(name="👥 Пригласил", value=f"{referrals} друзей", inline=True)
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


@bot.command(name='backup', aliases=['бэкап'])
async def create_backup(ctx):
    if not is_owner(ctx):
        await ctx.send("❌ У вас нет прав для использования этой команды! Только владелец.")
        await ctx.message.delete()
        return

    await ctx.send("🔄 **Создаю полный бэкап... Ожидайте в личных сообщениях!**")
    await ctx.message.delete()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    backup_data = {
        'warns': data.get('warns', {}),
        'balance': data.get('balance', {}),
        'daily': data.get('daily', {}),
        'exchange_rate': data.get('exchange_rate', 5.0),
        'messages_count': data.get('messages_count', {}),
        'messages_history': data.get('messages_history', {}),
        'last_message_time': data.get('last_message_time', {}),
        'voice_time': data.get('voice_time', {}),
        'voice_last_check': data.get('voice_last_check', {}),
        'voice_total_time': data.get('voice_total_time', {}),
        'voice_history': data.get('voice_history', {}),
        'last_status_message_id': data.get('last_status_message_id', None),
        'referrals': data.get('referrals', {}),
        'referral_count': data.get('referral_count', {}),
        'referral_links': data.get('referral_links', {}),
        'private_voice_settings': data.get('private_voice_settings', {}),
        'used_referrals': data.get('used_referrals', {}),
        'daily_stats': data.get('daily_stats', {}),
        'weekly_stats': data.get('weekly_stats', {}),
        'monthly_stats': data.get('monthly_stats', {})
    }

    json_backup = f"{BACKUP_FOLDER}/backup_{timestamp}.json"
    with open(json_backup, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=4, ensure_ascii=False)

    try:
        embed = discord.Embed(
            title="💾 Полный бэкап создан!",
            description=f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                        f"**Размер:** {os.path.getsize(json_backup) / 1024:.2f} KB",
            color=0x00ff00
        )

        stats = []
        stats.append(f"👥 Пользователей: {len(backup_data['balance'])}")
        stats.append(f"💎 Всего осколков: {sum(backup_data['balance'].values())}")
        stats.append(f"⚠️ Варнов: {sum(len(w) for w in backup_data['warns'].values())}")
        stats.append(f"👥 Рефералов: {sum(backup_data['referral_count'].values())}")
        stats.append(f"🎙️ Приватных войсов: {len(backup_data['private_voice_settings'])}")
        embed.add_field(name="📊 Статистика", value="\n".join(stats), inline=False)
        embed.set_footer(text=f"Создал: {ctx.author.display_name}")

        await ctx.author.send(embed=embed)

        with open(json_backup, 'rb') as f:
            await ctx.author.send(file=discord.File(f, f"backup_{timestamp}.json"))

        await ctx.send(f"✅ **Полный бэкап создан и отправлен в личные сообщения!**")

    except discord.Forbidden:
        await ctx.send("❌ **Не могу отправить бэкап в ЛС!** Включите личные сообщения от участников сервера в настройках Discord.")
    except Exception as e:
        await ctx.send(f"❌ Ошибка при отправке: {e}")


@bot.command(name='restore', aliases=['восстановить'])
async def restore_backup(ctx, backup_name: str = None):
    if not is_owner(ctx):
        await ctx.send("❌ У вас нет прав для использования этой команды! Только владелец.")
        await ctx.message.delete()
        return

    if backup_name:
        backup_path = os.path.join(BACKUP_FOLDER, backup_name)
        if not os.path.exists(backup_path):
            await ctx.send(f"❌ Бэкап `{backup_name}` не найден в папке бэкапов!")
            await ctx.message.delete()
            return

        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            emergency_backup = f"{BACKUP_FOLDER}/pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(emergency_backup, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            for key in backup_data:
                data[key] = backup_data[key]

            save_data(data)

            embed = discord.Embed(
                title="✅ Данные восстановлены!",
                description=f"**Из бэкапа:** {backup_name}\n"
                            f"**Пользователей:** {len(data['balance'])}\n"
                            f"**Всего осколков:** {sum(data['balance'].values())}",
                color=0x00ff00
            )
            embed.set_footer(text="Старые данные сохранены как резервная копия")
            await ctx.send(embed=embed)
            await ctx.message.delete()
            return
        except Exception as e:
            await ctx.send(f"❌ Ошибка при восстановлении: {e}")
            await ctx.message.delete()
            return

    await ctx.send("📤 **Загрузите файл бэкапа (.json) в этот чат**\nИли используйте `j.restore имя_файла`")
    await ctx.message.delete()

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and len(msg.attachments) > 0

    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
        attachment = msg.attachments[0]

        if not attachment.filename.endswith('.json'):
            await ctx.send("❌ Файл должен быть в формате `.json`!")
            return

        file_content = await attachment.read()
        backup_data = json.loads(file_content.decode('utf-8'))

        required_keys = ['balance', 'warns', 'daily', 'exchange_rate']
        if not all(key in backup_data for key in required_keys):
            await ctx.send("❌ Это невалидный файл бэкапа!")
            return

        emergency_backup = f"{BACKUP_FOLDER}/pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(emergency_backup, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        backup_path = f"{BACKUP_FOLDER}/{attachment.filename}"
        with open(backup_path, 'wb') as f:
            f.write(file_content)

        for key in backup_data:
            data[key] = backup_data[key]

        save_data(data)

        embed = discord.Embed(
            title="✅ Данные восстановлены из файла!",
            description=f"**Файл:** {attachment.filename}\n"
                        f"**Пользователей:** {len(data['balance'])}\n"
                        f"**Всего осколков:** {sum(data['balance'].values())}",
            color=0x00ff00
        )
        embed.set_footer(text="Старые данные сохранены как резервная копия")
        await ctx.send(embed=embed)

    except asyncio.TimeoutError:
        await ctx.send("❌ Время ожидания истекло. Отмена.")
    except json.JSONDecodeError:
        await ctx.send("❌ Это невалидный JSON файл!")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")


@bot.command(name='backups', aliases=['бэкапы', 'списокбэкапов'])
async def list_backups(ctx):
    if not is_owner(ctx):
        await ctx.send("❌ У вас нет прав для использования этой команды! Только владелец.")
        await ctx.message.delete()
        return

    backups = sorted([f for f in os.listdir(BACKUP_FOLDER) if f.endswith('.json')])

    if not backups:
        await ctx.send("📁 **В папке бэкапов нет файлов!**")
        await ctx.message.delete()
        return

    embed = discord.Embed(
        title="📋 Список бэкапов",
        description=f"Всего: {len(backups)} файлов",
        color=0x5865F2
    )

    for i, backup in enumerate(backups[-20:], 1):
        date_str = backup.replace('backup_', '').replace('.json', '')
        try:
            dt = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
            date_formatted = dt.strftime('%d.%m.%Y %H:%M:%S')
        except:
            date_formatted = date_str

        size = os.path.getsize(os.path.join(BACKUP_FOLDER, backup)) / 1024
        size_str = f"{size:.1f} KB"

        embed.add_field(
            name=f"{i}. {date_formatted}",
            value=f"`{backup}` ({size_str})",
            inline=False
        )

    embed.set_footer(text="Используйте j.restore имя_файла для восстановления")
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass


# ----- СТАТУС ТРЕКЕР -----
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
    try:
        await ctx.message.delete()
    except:
        pass


@bot.event
async def on_ready():
    global bog_member, last_status, last_status_message
    print(f'✅ Бот {bot.user} готов!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="за Боженькой"))

    reset_daily_stats()
    reset_weekly_stats()
    reset_monthly_stats()

    stats_reset_check.start()

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
    print("✅ Дневная статистика активна, сброс в 00:00 по МСК")
    print("✅ Недельная статистика активна, сброс в понедельник 00:00 по МСК")
    print("✅ Месячная статистика активна, сброс 1-го числа 00:00 по МСК")


if __name__ == "__main__":
    if not TOKEN:
        print("❌ ОШИБКА: Токен не найден! Установите переменную DISCORD_TOKEN")
        exit(1)
    bot.run(TOKEN)
