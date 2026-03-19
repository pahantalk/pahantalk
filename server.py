# server.py - ПАХАНТАЛК с профилями (исправленная версия)
from flask import Flask, request, jsonify, send_file
import sqlite3
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
AVATAR_FOLDER = 'avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AVATAR_FOLDER'] = AVATAR_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  display_name TEXT,
                  avatar TEXT,
                  status TEXT DEFAULT 'в сети',
                  bio TEXT DEFAULT '')''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  from_user TEXT NOT NULL,
                  to_user TEXT NOT NULL,
                  text TEXT,
                  image TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    try:
        c.execute("INSERT OR IGNORE INTO users (username, password, display_name) VALUES (?, ?, ?)",
                  ("2kenta", "123", "Кента"))
        c.execute("INSERT OR IGNORE INTO users (username, password, display_name) VALUES (?, ?, ?)",
                  ("pahan", "123", "Пахан"))
    except:
        pass
    conn.commit()
    conn.close()

init_db()

# ==================== HTML (простая строка) ====================
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ПАХАНТАЛК</title>
    <meta charset="utf-8">
    <style>
        body { background: #111; color: gold; font-family: Arial; padding:20px; }
        .container { max-width:600px; margin:0 auto; background:#222; padding:20px; border-radius:10px; }
        input, button { padding:10px; margin:5px; width:100%; }
        #messages { height:300px; overflow-y:auto; background:#1a1a1a; padding:10px; }
        .my-message { background:#2b5278; color:white; }
        .other-message { background:#2a2a2a; color:white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ПАХАНТАЛК</h1>
        <div id="login">
            <input id="loginUser" placeholder="Логин">
            <input id="loginPass" type="password" placeholder="Пароль">
            <button onclick="login()">Войти</button>
            <button onclick="register()">Регистрация</button>
        </div>
        <div id="chat" style="display:none;">
            <div><span id="currentUser"></span> <button onclick="logout()">Выйти</button></div>
            <input id="toUser" placeholder="Кому">
            <input id="message" placeholder="Сообщение">
            <button onclick="send()">Отправить</button>
            <div id="messages"></div>
        </div>
    </div>
    <script>
        let user = null;
        async function api(url, data) {
            const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
            return r.json();
        }
        async function register() {
            const u = document.getElementById('loginUser').value;
            const p = document.getElementById('loginPass').value;
            await api('/register', {username:u, password:p});
            alert('Регистрация, теперь войди');
        }
        async function login() {
            const u = document.getElementById('loginUser').value;
            const p = document.getElementById('loginPass').value;
            const res = await api('/login', {username:u, password:p});
            if(res.success) {
                user = u;
                document.getElementById('login').style.display = 'none';
                document.getElementById('chat').style.display = 'block';
                document.getElementById('currentUser').innerText = user;
                load();
            } else alert('Ошибка');
        }
        function logout() { user = null; location.reload(); }
        async function send() {
            const to = document.getElementById('toUser').value;
            const text = document.getElementById('message').value;
            await api('/send', {from:user, to:to, text:text});
            document.getElementById('message').value = '';
            load();
        }
        async function load() {
            const r = await fetch('/messages/' + user);
            const msgs = await r.json();
            const html = msgs.map(m => 
                `<div class="${m.from === user ? 'my-message' : 'other-message'}">
                    <b>${m.from}</b>: ${m.text}
                </div>`
            ).join('');
            document.getElementById('messages').innerHTML = html;
        }
        setInterval(() => { if(user) load(); }, 3000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (data['username'], data['password']))
        conn.commit()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (data['username'], data['password']))
    user = c.fetchone()
    conn.close()
    return jsonify({'success': bool(user)})

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (from_user, to_user, text) VALUES (?, ?, ?)",
              (data['from'], data['to'], data['text']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/messages/<username>')
def get_messages(username):
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("""SELECT from_user, to_user, text, 
                 strftime('%H:%M', timestamp) as time 
                 FROM messages 
                 WHERE from_user=? OR to_user=?
                 ORDER BY timestamp DESC LIMIT 50""",
              (username, username))
    msgs = [{'from': row[0], 'to': row[1], 'text': row[2], 'time': row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(msgs)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
