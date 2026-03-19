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
                  status TEXT DEFAULT 'в сети')''')
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

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>ПАХАНТАЛК</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:Arial,sans-serif; background:#0e1621; color:white; display:flex; justify-content:center; align-items:center; min-height:100vh; padding:20px; }
        .container { width:100%; max-width:400px; background:#17212b; border-radius:16px; padding:30px; }
        h1 { color:#2b7ad0; text-align:center; margin-bottom:30px; }
        input { width:100%; padding:12px; margin:10px 0; background:#1e2a36; border:1px solid #253441; border-radius:8px; color:white; }
        button { width:100%; padding:12px; background:#2b7ad0; border:none; border-radius:8px; color:white; font-weight:bold; cursor:pointer; margin:5px 0; }
        button:hover { background:#1f6abc; }
        .hidden { display:none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>💬 ПАХАНТАЛК</h1>
        <div id="loginScreen">
            <input type="text" id="loginUser" placeholder="Логин" value="2kenta">
            <input type="password" id="loginPass" placeholder="Пароль" value="123">
            <button onclick="login()">Войти</button>
            <button onclick="register()">Регистрация</button>
        </div>
        <div id="chatScreen" class="hidden">
            <p>Чат загружается...</p>
        </div>
    </div>
    <script>
        async function apiCall(url, data) {
            const res = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
            return res.json();
        }
        async function register() {
            const u = document.getElementById('loginUser').value;
            const p = document.getElementById('loginPass').value;
            const res = await apiCall('/register', {username:u, password:p});
            alert(res.success ? 'OK' : 'Ошибка');
        }
        async function login() {
            const u = document.getElementById('loginUser').value;
            const p = document.getElementById('loginPass').value;
            const res = await apiCall('/login', {username:u, password:p});
            if(res.success) {
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('chatScreen').style.display = 'block';
                document.getElementById('chatScreen').innerHTML = '<p>✅ Вход выполнен</p>';
            } else alert('Неверный логин/пароль');
        }
        if(localStorage.getItem('pahantalk_user')) login();
    </script>
</body>
</html>'''

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
