import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
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
BOG_ROLE_ID = 1521944293135351829
OWNER_ROLE_ID = 1504402262833758228
BOG_USER_ID = 1062336593588912199

LOG_CHANNEL_ID = 1502637205187723433
REPORT_CHANNEL_ID = 1502637205187723433

# ПРИВАТНЫЕ ВОЙСЫ
PRIVATE_VOICE_CATEGORY_ID = 1507479787223126036
VOICE_TRIGGER_ID = 1507485728739688549

# НАСТРОЙКИ ЭКОНОМИКИ
MESSAGES_PER_SHARD = 2
SHARDS_PER_MESSAGES = 5
VOICE_HOUR_SHARDS = 15
DAILY_BONUS = 15
REFERRAL_BONUS = 100
COOLDOWN_SECONDS = 10
VOICE_CHECK_INTERVAL = 30

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
        'last_status_message_id': None,
        'referrals': {},
        'referral_count': {},
        'referral_links': {},
        'private_voice_settings': {},
        'used_referrals': {}
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# ----- ХРАНИЛИЩА -----
last_status = None
bog_member = None
last_status_message = None
private_voice_channels = {}
voice_settings = {}

# ----- КЛАСС ДЛЯ КНОПОК ПРИВАТНОГО ВОЙСА -----
class VoiceControlView(View):
    def __init__(self, channel_id, owner_id, timeout=600):
        super().__init__(timeout=timeout)
        self.channel_id = channel_id
        self.owner_id = owner_id
        self.message = None
        self.update_task = None
        
    async def start_update(self):
        async def update_loop():
            while True:
                await asyncio.sleep(20)
                if self.message:
                    try:
                        await self.update_buttons()
                    except:
                        break
        self.update_task = asyncio.create_task(update_loop())
    
    async def update_buttons(self):
        if self.message:
            new_view = VoiceControlView(self.channel_id, self.owner_id, timeout=600)
            new_view.message = self.message
            for item in self.children:
                if isinstance(item, Button):
                    new_view.add_item(item)
            await self.message.edit(view=new_view)
    
    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Вы не владелец этого канала!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="👥 Лимит", style=discord.ButtonStyle.primary)
    async def limit_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SetLimitModal(self.channel_id))

    @discord.ui.button(label="🚫 Бан", style=discord.ButtonStyle.danger)
    async def ban_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(BanUserModal(self.channel_id))

    @discord.ui.button(label="✅ Разбан", style=discord.ButtonStyle.success)
    async def unban_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(UnbanUserModal(self.channel_id))

    @discord.ui.button(label="👁️ Скрыть", style=discord.ButtonStyle.secondary)
    async def hide_button(self, interaction: discord.Interaction, button: Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await interaction.response.send_message("✅ Канал скрыт!", ephemeral=True)
            str_id = str(self.channel_id)
            if str_id in data['private_voice_settings']:
                data['private_voice_settings'][str_id]['hidden'] = True
                save_data(data)

    @discord.ui.button(label="👁️ Показать", style=discord.ButtonStyle.secondary)
    async def show_button(self, interaction: discord.Interaction, button: Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=True)
            await interaction.response.send_message("✅ Канал теперь виден!", ephemeral=True)
            str_id = str(self.channel_id)
            if str_id in data['private_voice_settings']:
                data['private_voice_settings'][str_id]['hidden'] = False
                save_data(data)

    @discord.ui.button(label="👢 Кик", style=discord.ButtonStyle.danger)
    async def kick_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(KickUserModal(self.channel_id))

    @discord.ui.button(label="🗑️ Удалить", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            other_members = [m for m in channel.members if m.id != self.owner_id]
            if other_members:
                await interaction.response.send_message("❌ В канале есть другие участники! Сначала кикните их.", ephemeral=True)
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

    @discord.ui.button(label="📊 Инфо", style=discord.ButtonStyle.secondary)
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

# ----- МОДАЛЬНЫЕ ОКНА -----
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

class BanUserModal(discord.ui.Modal):
    def __init__(self, channel_id):
        super().__init__(title="Забанить пользователя")
        self.channel_id = channel_id
        self.user_input = discord.ui.TextInput(
            label="ID пользователя",
            placeholder="Введите ID пользователя",
            required=True
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_input.value)
            member = interaction.guild.get_member(user_id)
            if not member:
                await interaction.response.send_message("❌ Пользователь не найден!", ephemeral=True)
                return
            if member.id == interaction.user.id:
                await interaction.response.send_message("❌ Нельзя забанить самого себя!", ephemeral=True)
                return
            channel = interaction.guild.get_channel(self.channel_id)
            str_id = str(self.channel_id)
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
        except ValueError:
            await interaction.response.send_message("❌ Введите корректный ID!", ephemeral=True)

class UnbanUserModal(discord.ui.Modal):
    def __init__(self, channel_id):
        super().__init__(title="Разбанить пользователя")
        self.channel_id = channel_id
        self.user_input = discord.ui.TextInput(
            label="ID пользователя",
            placeholder="Введите ID пользователя",
            required=True
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_input.value)
            member = interaction.guild.get_member(user_id)
            if not member:
                await interaction.response.send_message("❌ Пользователь не найден!", ephemeral=True)
                return
            str_id = str(self.channel_id)
            if str_id not in data['private_voice_settings']:
                await interaction.response.send_message("❌ Нет забаненных пользователей!", ephemeral=True)
                return
            if member.id not in data['private_voice_settings'][str_id]['banned_users']:
                await interaction.response.send_message(f"❌ {member.mention} не в бане!", ephemeral=True)
                return
            data['private_voice_settings'][str_id]['banned_users'].remove(member.id)
            save_data(data)
            channel = interaction.guild.get_channel(self.channel_id)
            if channel:
                await channel.set_permissions(member, connect=None)
            await interaction.response.send_message(f"✅ {member.mention} разбанен!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Введите корректный ID!", ephemeral=True)

class KickUserModal(discord.ui.Modal):
    def __init__(self, channel_id):
        super().__init__(title="Кикнуть пользователя")
        self.channel_id = channel_id
        self.user_input = discord.ui.TextInput(
            label="ID пользователя",
            placeholder="Введите ID пользователя",
            required=True
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_input.value)
            member = interaction.guild.get_member(user_id)
            if not member:
                await interaction.response.send_message("❌ Пользователь не найден!", ephemeral=True)
                return
            if member.id == interaction.user.id:
                await interaction.response.send_message("❌ Нельзя кикнуть самого себя!", ephemeral=True)
                return
            channel = interaction.guild.get_channel(self.channel_id)
            if not channel or member not in channel.members:
                await interaction.response.send_message(f"❌ {member.mention} не в этом канале!", ephemeral=True)
                return
            await member.move_to(None)
            await interaction.response.send_message(f"✅ {member.mention} кикнут из канала!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Введите корректный ID!", ephemeral=True)

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

def is_owner(ctx):
    """Проверяет, является ли пользователь владельцем (по роли или по ID)"""
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
        data['balance'][user_id] += SHARDS_PER_MESSAGES
        data['messages_count'][user_id] = 0
        save_data(data)
        try:
            embed = discord.Embed(
                title=f"💎 +{SHARDS_PER_MESSAGES} Осколков!",
                description=f"Вы получили {SHARDS_PER_MESSAGES} осколков за активность в чате!\nВсего осколков: {data['balance'][user_id]} 💎",
                color=0xffd700
            )
            await message.channel.send(f"{message.author.mention}", embed=embed, delete_after=5)
        except:
            pass
    await bot.process_commands(message)

# ----- ПРИВАТНЫЕ ВОЙСЫ -----
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == VOICE_TRIGGER_ID:
        await create_private_voice(member)
    if before.channel and before.channel.id in private_voice_channels:
        if len(before.channel.members) == 0:
            await delete_empty_voice(before.channel)

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
    view = VoiceControlView(voice_channel.id, member.id, timeout=600)
    embed = discord.Embed(
        title="🔒 Приватный войс создан!",
        description="**Управляйте своим каналом через кнопки ниже:**\n\n👥 **Лимит** - установить максимум пользователей\n🚫 **Бан** - запретить вход пользователю\n✅ **Разбан** - разрешить вход\n👁️ **Скрыть/Показать** - скрыть канал от всех\n👢 **Кик** - выгнать из канала\n🗑️ **Удалить** - удалить канал\n📊 **Инфо** - информация о канале",
        color=0x00ff00
    )
    msg = await voice_channel.send(embed=embed, view=view)
    view.message = msg
    await view.start_update()

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

# ----- РЕФЕРАЛЬНАЯ СИСТЕМА -----
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
    except Exception as e:
        await ctx.send(f"❌ Ошибка создания ссылки: {e}")

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

# ----- ОБРАБОТЧИК ВХОДА -----
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

# ----- КОМАНДА HELP -----
@bot.command(name='help', aliases=['h'])
async def custom_help(ctx, command_name: str = None):
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
        description=f"""**Префикс: `j.`**
**Курс:** 1 ₽ = {data.get('exchange_rate', 5)} 💎

💬 **{MESSAGES_PER_SHARD} сообщения = {SHARDS_PER_MESSAGES} осколков**
🎙️ **1 час в войсе = {VOICE_HOUR_SHARDS} осколков**
📅 **/daily → +{DAILY_BONUS} осколков каждый день**
👥 **Приведи друга → +{REFERRAL_BONUS} осколков**""",
        color=0x5865F2
    )
    
    embed.add_field(
        name="🛡️ Модерация",
        value="""**mute** - Замутить пользователя\n**unmute** - Размутить\n**ban** - Забанить\n**kick** - Кикнуть\n**warn** - Выдать варн\n**warns** - Просмотр варнов\n**unwarn** - Снять варн\n**clear** - Очистить канал""",
        inline=False
    )
    
    embed.add_field(
        name="💰 Экономика",
        value=f"""**balance (bal)** - Баланс\n**daily** - Ежедневный бонус\n**add** - Выдать осколки (Владелец/Боженька)\n**remove** - Снять осколки (Владелец/Боженька)\n**rate** - Курс\n**setrate** - Установить курс (Владелец/Боженька)\n**msgstats** - Статистика сообщений\n**voicestats** - Статистика голоса\n**topvoice** - Топ по голосу\n**topmsg** - Топ по сообщениям""",
        inline=False
    )
    
    embed.add_field(
        name="👥 Приглашения",
        value=f"""**referral** - Создать реферальную ссылку (+{REFERRAL_BONUS} 💎)\n**referrals** - Статистика приглашений""",
        inline=False
    )
    
    embed.add_field(
        name="🎙️ Приватные войсы",
        value="""**voice limit** - Лимит пользователей\n**voice ban** - Забанить\n**voice unban** - Разбанить\n**voice hide** - Скрыть\n**voice show** - Показать\n**voice kick** - Кикнуть\n**voice info** - Информация\n**voice delete** - Удалить""",
        inline=False
    )
    
    embed.add_field(
        name="📊 Отчеты",
        value="""**report** - Создать отчет (Владелец/Боженька)\n**backup** - Бэкап данных (Владелец)\n**restore** - Восстановить (Владелец)\n**stats** - Статистика (Владелец/Боженька)\n**find** - Найти пользователя (Владелец/Боженька)\n**profile** - Профиль пользователя""",
        inline=False
    )
    
    embed.set_footer(text=f"Запросил: {ctx.author.display_name}")
    await ctx.send(embed=embed)

# ----- КОМАНДА STATUS -----
@bot.command(name='status', aliases=['stats'])
async def bot_status(ctx):
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
    total_messages = sum(data['messages_count'].values()) if data['messages_count'] else 0
    total_referrals = sum(data['referral_count'].values()) if data['referral_count'] else 0
    rate = data.get('exchange_rate', 5)
    total_rubles = round(total_balance / rate, 2) if rate > 0 else 0
    embed.add_field(name="💰 Экономика", value=f"**Всего осколков:** {total_balance} 💎\n**Пользователей:** {len(data['balance'])}\n**Курс:** 1 ₽ = {rate} 💎", inline=False)
    embed.add_field(name="📊 Активность", value=f"**Всего сообщений:** {total_messages}\n**Всего в войсе:** {format_time(total_voice)}\n**Приглашений:** {total_referrals}\n**За сообщения:** {MESSAGES_PER_SHARD} = {SHARDS_PER_MESSAGES} 💎\n**За голос:** 1 час = {VOICE_HOUR_SHARDS} 💎", inline=False)
    await ctx.send(embed=embed)

# ----- КОМАНДА RATE -----
@bot.command(name='rate', aliases=['курс'])
async def show_rate(ctx):
    rate = data.get('exchange_rate', 5)
    embed = discord.Embed(
        title="💱 Текущий курс",
        description=f"""**1 рубль = {rate} осколков** 💎
**1 осколок = {round(1/rate, 2)} рублей**

💬 **{MESSAGES_PER_SHARD} сообщения = {SHARDS_PER_MESSAGES} осколков**
🎙️ **1 час в войсе = {VOICE_HOUR_SHARDS} осколков**
📅 **Ежедневный бонус: +{DAILY_BONUS} 💎**
👥 **За приглашение друга: +{REFERRAL_BONUS} 💎**""",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

# ----- КОМАНДА SETRATE -----
@bot.command(name='setrate', aliases=['установитькурс'])
@commands.check(is_owner_or_bog)
async def set_exchange_rate(ctx, rate: str):
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

# ----- КОМАНДА BALANCE -----
@bot.command(name='balance', aliases=['bal'])
async def balance(ctx, member: discord.Member = None):
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

# ----- КОМАНДА ADD -----
@bot.command(name='add')
@commands.check(can_manage_economy)
async def add_shards(ctx, member: discord.Member, amount: int):
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

# ----- КОМАНДА REMOVE -----
@bot.command(name='remove')
@commands.check(can_manage_economy)
async def remove_shards(ctx, member: discord.Member, amount: int):
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

# ----- КОМАНДА DAILY -----
@bot.command(name='daily')
async def daily(ctx):
    user_id = str(ctx.author.id)
    today = datetime.now().date().isoformat()
    if user_id in data['daily'] and data['daily'][user_id] == today:
        await ctx.send("❌ Вы уже получили бонус сегодня! Завтра приходите за новым.")
        return
    if user_id not in data['balance']:
        data['balance'][user_id] = 0
    data['balance'][user_id] += DAILY_BONUS
    data['daily'][user_id] = today
    save_data(data)
    rate = data.get('exchange_rate', 5)
    rubles = round(DAILY_BONUS / rate, 2)
    embed = discord.Embed(
        title="🎉 Ежедневный бонус!",
        description=f"Вы получили **+{DAILY_BONUS} осколков** 💎\n\n**Новый баланс:** {data['balance'][user_id]} 💎 ({rubles} ₽)\n\nПриходите завтра за новым бонусом!",
        color=0xffd700
    )
    embed.set_footer(text="📅 Боженька заботится о вас ✨")
    await ctx.send(embed=embed)

# ----- КОМАНДА PROFILE -----
@bot.command(name='profile', aliases=['профиль'])
async def profile(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    user_id = str(member.id)
    balance = data['balance'].get(user_id, 0)
    rate = data.get('exchange_rate', 5)
    rubles = round(balance / rate, 2) if rate > 0 else 0
    messages = data['messages_count'].get(user_id, 0)
    total_messages = messages + ((balance // SHARDS_PER_MESSAGES) * MESSAGES_PER_SHARD) if balance > 0 else messages
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
    embed.add_field(name="💰 Баланс", value=f"**Осколки:** {balance} 💎\n**Рубли:** {rubles} ₽\n**Курс:** 1 ₽ = {rate} 💎", inline=True)
    embed.add_field(name="💬 Активность", value=f"**Сообщений:** {total_messages}\n**В голосе:** {voice_hours}ч {voice_minutes}м\n**Варнов:** {warns}\n**Пригласил:** {referrals} друзей", inline=True)
    embed.add_field(name="🎖️ Роли", value=roles_text[:1024] if len(roles_text) <= 1024 else roles_text[:1021] + "...", inline=False)
    embed.set_footer(text=f"Запросил: {ctx.author.display_name}")
    await ctx.send(embed=embed)

# ----- КОМАНДА MSGSTATS -----
@bot.command(name='msgstats', aliases=['сообщения'])
async def message_stats(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    user_id = str(member.id)
    msg_count = data['messages_count'].get(user_id, 0)
    needed = MESSAGES_PER_SHARD - msg_count
    embed = discord.Embed(title="📊 Статистика сообщений", color=0x00ff00)
    embed.add_field(name="Пользователь", value=member.mention)
    embed.add_field(name="Сообщений отправлено", value=f"{msg_count} / {MESSAGES_PER_SHARD}")
    embed.add_field(name="До следующего бонуса", value=f"{needed} сообщений → +{SHARDS_PER_MESSAGES} 💎")
    embed.set_footer(text=f"За каждые {MESSAGES_PER_SHARD} сообщений вы получаете {SHARDS_PER_MESSAGES} осколков")
    await ctx.send(embed=embed)

# ----- КОМАНДА VOICESTATS -----
@bot.command(name='voicestats', aliases=['войсстат', 'voice'])
async def voice_stats(ctx, member: discord.Member = None):
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

# ----- КОМАНДА TOPVOICE -----
@bot.command(name='topvoice', aliases=['топвойс'])
async def top_voice(ctx):
    if not data['voice_total_time']:
        await ctx.send("📊 Нет данных о голосовой активности!")
        return
    sorted_users = sorted(data['voice_total_time'].items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="🎙️ Топ-10 по времени в войсе", color=0x5865F2, timestamp=datetime.now())
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
        shards = (seconds // 3600) * VOICE_HOUR_SHARDS
        medal = get_medal(i)
        text += f"{medal} **{display_name}** ({name}) - {format_time(seconds)} ({shards} 💎)\n"
    embed.description = text if text else "Нет данных"
    await ctx.send(embed=embed)

# ----- КОМАНДА TOPMSG -----
@bot.command(name='topmsg', aliases=['топсообщений'])
async def top_messages(ctx):
    if not data['messages_count']:
        await ctx.send("📊 Нет данных о сообщениях!")
        return
    sorted_users = sorted(data['messages_count'].items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="🏆 Топ-10 по активности в чате", color=0xffd700, timestamp=datetime.now())
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
        shards_earned = (count // MESSAGES_PER_SHARD) * SHARDS_PER_MESSAGES
        medal = get_medal(i)
        text += f"{medal} **{display_name}** ({name}) - {count} сообщений ({shards_earned} 💎)\n"
    embed.description = text if text else "Нет данных"
    await ctx.send(embed=embed)

# ----- КОМАНДА REPORT -----
@bot.command(name='report', aliases=['отчет'])
@commands.check(is_owner_or_bog)
async def create_report(ctx):
    await ctx.send("📊 **Создаю отчет... Ожидайте в личных сообщениях!**")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    rate = data.get('exchange_rate', 5)
    total_users = len(data['balance'])
    total_shards = sum(data['balance'].values())
    total_rubles = round(total_shards / rate, 2) if rate > 0 else 0
    total_referrals = sum(data['referral_count'].values()) if data['referral_count'] else 0
    txt_file = f"{REPORT_FOLDER}/report_{timestamp}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("📊 СТАТИСТИКА СЕРВЕРА\n")
        f.write("="*70 + "\n\n")
        f.write(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write(f"💱 Курс: 1 ₽ = {rate} 💎\n")
        f.write(f"💬 За активность: {MESSAGES_PER_SHARD} сообщений = {SHARDS_PER_MESSAGES} 💎\n")
        f.write(f"🎙️ За голос: 1 час = {VOICE_HOUR_SHARDS} 💎\n")
        f.write(f"📅 Ежедневный бонус: +{DAILY_BONUS} 💎\n")
        f.write(f"👥 За приглашение: +{REFERRAL_BONUS} 💎\n\n")
        f.write("="*70 + "\n")
        f.write("📈 ОБЩАЯ СТАТИСТИКА\n")
        f.write("="*70 + "\n")
        f.write(f"👥 Всего пользователей: {total_users}\n")
        f.write(f"💎 Всего осколков: {total_shards}\n")
        f.write(f"💰 Всего рублей: {total_rubles} ₽\n")
        f.write(f"👥 Всего приглашений: {total_referrals}\n\n")
        total_messages = sum(data['messages_count'].values()) if data['messages_count'] else 0
        total_voice = sum(data['voice_total_time'].values()) if data['voice_total_time'] else 0
        total_voice_hours = total_voice // 3600
        f.write("="*70 + "\n")
        f.write("💬 СТАТИСТИКА АКТИВНОСТИ\n")
        f.write("="*70 + "\n")
        f.write(f"📝 Всего сообщений: {total_messages}\n")
        f.write(f"💎 Заработано осколков за сообщения: {(total_messages // MESSAGES_PER_SHARD) * SHARDS_PER_MESSAGES}\n")
        f.write(f"🎙️ Всего часов в войсе: {total_voice_hours}\n")
        f.write(f"💎 Заработано осколков за голос: {total_voice_hours * VOICE_HOUR_SHARDS}\n\n")
        f.write("="*70 + "\n")
        f.write("👥 ВСЕ ПОЛЬЗОВАТЕЛИ (по убыванию баланса)\n")
        f.write("="*70 + "\n")
        f.write(f"{'ID':<20} | {'Имя':<25} | {'Осколки':<10} | {'Рубли':<10} | {'Daily':<12} | {'Варны'}\n")
        f.write("-"*70 + "\n")
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

# ----- КОМАНДА FIND -----
@bot.command(name='find', aliases=['найти'])
@commands.check(is_owner_or_bog)
async def find_user(ctx, user_id: int):
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
    referrals = data['referral_count'].get(uid, 0)
    embed = discord.Embed(title=f"👤 {name}", color=0x00ff00)
    embed.add_field(name="ID", value=user_id, inline=True)
    embed.add_field(name="💎 Баланс", value=f"{balance} ({rubles} ₽)", inline=True)
    embed.add_field(name="📅 Daily", value=daily, inline=True)
    embed.add_field(name="⚠️ Варнов", value=warns, inline=True)
    embed.add_field(name="👥 Пригласил", value=f"{referrals} друзей", inline=True)
    await ctx.send(embed=embed)

# ----- АДМИН КОМАНДЫ -----
@bot.command(name='mute', aliases=['мут'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def mute(ctx, member: discord.Member, time: str, *, reason="Не указана"):
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

@bot.command(name='unmute', aliases=['размут'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def unmute(ctx, member: discord.Member):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя размутить!")
        return
    await member.timeout(None)
    await ctx.send(f"✅ {member.mention} размучен!")

@bot.command(name='ban', aliases=['бан'])
@commands.has_any_role(*[ROLES['admin'], ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def ban(ctx, member: discord.Member, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя забанить!")
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя банить Боженьку!")
        return
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member.mention} забанен! Причина: {reason}")

@bot.command(name='kick', aliases=['кик'])
@commands.has_any_role(*[ROLES['moderator'], ROLES['admin'], ROLES['head_admin'], 
                         ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def kick(ctx, member: discord.Member, *, reason="Не указана"):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя кикнуть!")
        return
    if member.id == BOG_USER_ID:
        await ctx.send("❌ Нельзя кикать Боженьку!")
        return
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.mention} кикнут! Причина: {reason}")

@bot.command(name='warn', aliases=['варн'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def warn(ctx, member: discord.Member, time: str, *, reason="Не указана"):
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

@bot.command(name='warns', aliases=['варны'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def warns(ctx, member: discord.Member):
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

@bot.command(name='unwarn', aliases=['разварн'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def unwarn(ctx, member: discord.Member, warn_id: str):
    if not await check_hierarchy(ctx, member):
        await ctx.send("❌ Нельзя снять варн!")
        return
    if str(member.id) in data['warns'] and warn_id in data['warns'][str(member.id)]:
        del data['warns'][str(member.id)][warn_id]
        save_data(data)
        await ctx.send(f"✅ Варн снят с {member.mention}")
    else:
        await ctx.send(f"❌ Варн не найден!")

@bot.command(name='clear', aliases=['очистить', 'cls'])
@commands.has_any_role(*[ROLES['helper'], ROLES['moderator'], ROLES['admin'], 
                         ROLES['head_admin'], ROLES['curator'], ROLES['co_owner'], ROLES['owner']])
async def clear_channel(ctx, amount: int = None):
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

# ----- КОМАНДА BACKUP (ПОЛНЫЙ БЭКАП) -----
@bot.command(name='backup', aliases=['бэкап'])
async def create_backup(ctx):
    """Создать полный бэкап всех данных (Только владелец)"""
    if not is_owner(ctx):
        await ctx.send("❌ У вас нет прав для использования этой команды! Только владелец.")
        return
    
    await ctx.send("🔄 **Создаю полный бэкап всех данных...**")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Сохраняем ВСЕ данные
    backup_data = {
        'warns': data.get('warns', {}),
        'balance': data.get('balance', {}),
        'daily': data.get('daily', {}),
        'exchange_rate': data.get('exchange_rate', 5.0),
        'messages_count': data.get('messages_count', {}),
        'last_message_time': data.get('last_message_time', {}),
        'voice_time': data.get('voice_time', {}),
        'voice_last_check': data.get('voice_last_check', {}),
        'voice_total_time': data.get('voice_total_time', {}),
        'last_status_message_id': data.get('last_status_message_id', None),
        'referrals': data.get('referrals', {}),
        'referral_count': data.get('referral_count', {}),
        'referral_links': data.get('referral_links', {}),
        'private_voice_settings': data.get('private_voice_settings', {}),
        'used_referrals': data.get('used_referrals', {})
    }
    
    json_backup = f"{BACKUP_FOLDER}/backup_{timestamp}.json"
    with open(json_backup, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=4, ensure_ascii=False)
    
    channel = bot.get_channel(LOG_CHANNEL_ID) or ctx.channel
    
    embed = discord.Embed(
        title="💾 Полный бэкап создан!",
        description=f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                   f"**Размер:** {os.path.getsize(json_backup) / 1024:.2f} KB\n"
                   f"**Данные:** Все (баланс, варны, голос, рефералы, настройки)",
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
    
    await channel.send(embed=embed)
    
    with open(json_backup, 'rb') as f:
        await channel.send(file=discord.File(f, f"backup_{timestamp}.json"))
    
    await ctx.send(f"✅ **Полный бэкап создан!** Файл отправлен в канал <#{channel.id}>")

# ----- КОМАНДА RESTORE -----
@bot.command(name='restore', aliases=['восстановить'])
async def restore_backup(ctx, backup_name: str = None):
    """Восстановить данные из бэкапа (Только владелец)"""
    if not is_owner(ctx):
        await ctx.send("❌ У вас нет прав для использования этой команды! Только владелец.")
        return
    
    if backup_name is None:
        backups = sorted([f for f in os.listdir(BACKUP_FOLDER) if f.endswith('.json')])
        if not backups:
            await ctx.send("❌ Нет бэкапов!")
            return
        
        embed = discord.Embed(
            title="📋 Доступные бэкапы",
            description="Используйте `j.restore имя_файла` для восстановления",
            color=0x5865F2
        )
        for i, backup in enumerate(backups[-10:], 1):
            date_str = backup.replace('backup_', '').replace('.json', '')
            try:
                dt = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                date_formatted = dt.strftime('%d.%m.%Y %H:%M:%S')
            except:
                date_formatted = date_str
            embed.add_field(
                name=f"{i}. {date_formatted}",
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
        # Сохраняем текущие данные как резервную копию
        emergency_backup = f"{BACKUP_FOLDER}/pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(emergency_backup, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Загружаем данные из бэкапа
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Восстанавливаем ВСЕ данные
        global data
        for key in backup_data:
            data[key] = backup_data[key]
        
        save_data(data)
        
        embed = discord.Embed(
            title="✅ Данные восстановлены!",
            description=f"**Из бэкапа:** {backup_name}\n"
                       f"**Пользователей:** {len(data['balance'])}\n"
                       f"**Всего осколков:** {sum(data['balance'].values())}\n"
                       f"**Приватных войсов:** {len(data.get('private_voice_settings', {}))}",
            color=0x00ff00
        )
        embed.set_footer(text="Старые данные сохранены как резервная копия")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка при восстановлении: {e}")

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
