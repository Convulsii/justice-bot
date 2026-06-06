from flask import Flask, session, redirect, url_for, render_template
from flask_dance.contrib.discord import make_discord_blueprint, discord

app = Flask(__name__)
app.secret_key = "секретный_ключ"

app.config["DISCORD_CLIENT_ID"] = "1502642822967459912"
app.config["DISCORD_CLIENT_SECRET"] = "KsAy53aZXkZyh7_DiGz7ltNRIvz601py"
app.config["DISCORD_REDIRECT_URI"] = "https://justice-bot-production.up.railway.app/callback"

discord_bp = make_discord_blueprint(
    client_id=app.config["DISCORD_CLIENT_ID"],
    client_secret=app.config["DISCORD_CLIENT_SECRET"],
    redirect_to="callback"
)
app.register_blueprint(discord_bp, url_prefix="/login")

@app.route('/')
def index():
    return "Главная страница"

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('discord.login'))
    return f"Добро пожаловать, {session.get('username')}!"

@app.route('/callback')
def callback():
    if not discord.authorized:
        return redirect(url_for('discord.login'))
    
    resp = discord.get("/users/@me")
    user_data = resp.json()
    
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    
    return redirect(url_for('dashboard'))

@app.route('/login')
def login():
    return redirect(url_for('discord.login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
