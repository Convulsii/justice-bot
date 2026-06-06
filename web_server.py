from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_dance.contrib.discord import make_discord_blueprint, discord
import requests
import sqlite3
import json
import secrets
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ========== ТВОИ КЛЮЧИ ==========
app.config["DISCORD_CLIENT_ID"] = "1502642822967459912"
app.config["DISCORD_CLIENT_SECRET"] = "KsAy53aZXkZyh7_DiGz7ltNRIvz601py"
app.config["DISCORD_REDIRECT_URI"] = "https://justice-bot-production.up.railway.app/callback"

discord_bp = make_discord_blueprint(
    client_id=app.config["DISCORD_CLIENT_ID"],
    client_secret=app.config["DISCORD_CLIENT_SECRET"],
    redirect_to="callback"
)
app.register_blueprint(discord_bp, url_prefix="/login")

# ========== БАЗА ДАННЫХ ==========
DB_PATH = "justice.db"

def init_web_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS web_users (
        discord_id INTEGER PRIMARY KEY,
        username TEXT,
        avatar TEXT,
        is_admin INTEGER DEFAULT 0,
        last_login TEXT
    )''')
    conn.commit()
    conn.close()
    print("✅ База данных готова")

# ========== МАРШРУТЫ ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('dashboard.html',
                          username=session.get('username'),
                          avatar=session.get('avatar'),
                          is_admin=session.get('is_admin', False))

@app.route('/login')
def login():
    return redirect(url_for('discord.login'))

@app.route('/callback')
def callback():
    if not discord.authorized:
        return redirect(url_for('login'))
    
    resp = discord.get("/users/@me")
    user_data = resp.json()
    
    # Получаем сервера пользователя
    guilds_resp = discord.get("/users/@me/guilds")
    guilds = guilds_resp.json()
    
    is_admin = False
    for guild in guilds:
        if guild.get('permissions', 0) & 0x8:  # Администратор
            is_admin = True
            break
    
    # Сохраняем в БД
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO web_users 
        (discord_id, username, avatar, is_admin, last_login)
        VALUES (?, ?, ?, ?, ?)''',
        (user_data['id'], user_data['username'], user_data.get('avatar'), 
         1 if is_admin else 0, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    session['avatar'] = user_data.get('avatar')
    session['is_admin'] = is_admin
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ========== API ==========
@app.route('/api/user/guilds')
def api_user_guilds():
    if not session.get('user_id'):
        return jsonify({"error": "Unauthorized"}), 401
    
    if not discord.authorized:
        return jsonify([])
    
    try:
        resp = discord.get("/users/@me/guilds")
        guilds = resp.json()
        result = []
        for guild in guilds:
            result.append({
                "id": guild['id'],
                "name": guild['name'],
                "icon": guild.get('icon'),
                "is_admin": guild.get('permissions', 0) & 0x8
            })
        return jsonify(result)
    except:
        return jsonify([])

@app.route('/api/stats')
def api_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(DISTINCT guild_id) FROM users")
    total_servers = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    total_users = c.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        "total_servers": total_servers,
        "total_users": total_users
    })

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    init_web_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Веб-сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
