from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import requests
import sqlite3
import json
import secrets
import asyncio
import threading
import os
from datetime import datetime
from discord_oauth import DiscordOAuth2Session

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ========== DISCORD OAuth2 НАСТРОЙКИ (ТВОИ КЛЮЧИ) ==========
app.config["DISCORD_CLIENT_ID"] = "1358784569331224726"
app.config["DISCORD_CLIENT_SECRET"] = "AoP1a5geUr3fq0OzUvwHJDPgEClF6jqb"
app.config["DISCORD_REDIRECT_URI"] = "http://localhost:5000/callback"
app.config["DISCORD_BOT_TOKEN"] = os.getenv('DISCORD_TOKEN')

discord = DiscordOAuth2Session(app)

# Путь к БД
DB_PATH = "justice.db"

# ========== ИНИЦИАЛИЗАЦИЯ БД ==========
def init_web_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Таблица для Discord авторизации
    c.execute('''CREATE TABLE IF NOT EXISTS web_users (
        discord_id INTEGER PRIMARY KEY,
        username TEXT,
        avatar TEXT,
        access_token TEXT,
        refresh_token TEXT,
        token_expires REAL,
        is_admin INTEGER DEFAULT 0,
        last_login TEXT
    )''')
    
    # Таблица для логов действий
    c.execute('''CREATE TABLE IF NOT EXISTS web_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id INTEGER,
        action TEXT,
        ip TEXT,
        timestamp TEXT
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Веб-база данных готова")

# ========== МАРШРУТЫ ==========
@app.route('/')
def index():
    """Главная страница (лендинг)"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Вход через Discord"""
    return discord.create_session(scope=["identify", "guilds"])

@app.route('/callback')
def callback():
    """Колбэк после авторизации в Discord"""
    try:
        discord.callback()
        user = discord.fetch_user()
        
        # Получаем сервера пользователя
        guilds = discord.fetch_guilds()
        is_admin = False
        
        # Проверяем, является ли пользователь администратором хотя бы одного сервера с ботом
        for guild in guilds:
            if guild.permissions.administrator:
                is_admin = True
                break
        
        # Сохраняем пользователя в БД
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO web_users 
            (discord_id, username, avatar, access_token, refresh_token, token_expires, is_admin, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (user.id, user.name, user.avatar, 
             discord.access_token, discord.refresh_token, 
             discord.token_expires, 1 if is_admin else 0, 
             datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        session['user_id'] = user.id
        session['username'] = user.name
        session['avatar'] = user.avatar
        session['is_admin'] = is_admin
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Выход"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Панель управления"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', 
                          username=session.get('username'),
                          avatar=session.get('avatar'),
                          is_admin=session.get('is_admin', False))

@app.route('/embed-builder')
def embed_builder():
    """Конструктор embed сообщений"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('embed_builder.html',
                          username=session.get('username'),
                          avatar=session.get('avatar'),
                          is_admin=session.get('is_admin', False))

# ========== API ЭНДПОИНТЫ ==========
@app.route('/api/user/guilds')
def api_user_guilds():
    """Получить список серверов пользователя"""
    if not session.get('user_id'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        guilds = discord.fetch_guilds()
        result = []
        for guild in guilds:
            if guild.permissions.administrator:
                result.append({
                    "id": guild.id,
                    "name": guild.name,
                    "icon": guild.icon,
                    "member_count": getattr(guild, 'approximate_member_count', 0)
                })
        return jsonify(result)
    except:
        return jsonify([])

@app.route('/api/guild/<int:guild_id>/settings')
def api_guild_settings(guild_id):
    """Получить настройки сервера"""
    if not session.get('user_id'):
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT welcome_channel, log_channel, levels_channel, automod_enabled FROM guild_settings WHERE guild_id = ?", (guild_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            "welcome_channel": row[0],
            "log_channel": row[1],
            "levels_channel": row[2],
            "automod_enabled": bool(row[3])
        })
    return jsonify({})

@app.route('/api/guild/<int:guild_id>/settings', methods=['POST'])
def api_update_guild_settings(guild_id):
    """Обновить настройки сервера"""
    if not session.get('user_id') or not session.get('is_admin'):
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.json
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO guild_settings 
        (guild_id, welcome_channel, log_channel, levels_channel, automod_enabled)
        VALUES (?, ?, ?, ?, ?)''',
        (guild_id, data.get('welcome_channel'), data.get('log_channel'), 
         data.get('levels_channel'), 1 if data.get('automod_enabled') else 0))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/api/stats')
def api_stats():
    """Общая статистика бота"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(DISTINCT guild_id) FROM users")
    total_servers = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    total_users = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(total_messages) FROM users")
    total_messages = c.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        "total_servers": total_servers,
        "total_users": total_users,
        "total_messages": total_messages
    })

def log_web_action(discord_id, action, ip):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO web_logs (discord_id, action, ip, timestamp) VALUES (?, ?, ?, ?)",
              (discord_id, action, ip, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    init_web_db()
    print("🚀 Веб-сервер запущен на http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
