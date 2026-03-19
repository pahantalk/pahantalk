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

# ==================== КРАСИВЫЙ HTML ====================
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ПАХАНТАЛК</title>
    <meta charset="utf-8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: Arial, sans-serif;
            background: #1e1e1e;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 600px;
            background: #2a2a2a;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.5);
        }
        h1 {
            color: gold;
            text-align: center;
            margin-bottom: 20px;
        }
        input, button, textarea {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: none;
            border-radius: 8px;
            background: #1a1a1a;
            color: white;
            border: 1px solid #3a3a3a;
        }
        button {
            background: gold;
            color: black;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover {
            background: #ffd700;
        }
        #messages {
            height: 300px;
            overflow-y: auto;
            background: #1a1a1a;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .message {
            margin: 8px 0;
            padding: 8px 12px;
            border-radius: 12px;
            max-width: 80%;
        }
        .my-message {
            background: #2b5278;
            margin-left: auto;
        }
        .other-message {
            background: #3a3a3a;
        }
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💬 ПАХАНТАЛК</h1>
        
        <div id="loginScreen">
            <input type="text" id="loginUser" placeholder="Логин">
            <input type="password" id="loginPass" placeholder="Пароль">
            <button onclick="login()">Войти</button>
            <button onclick="register()">Регистрация</button>
        </div>

        <div id="chatScreen" class="hidden">
            <div style="display: flex; justify-content: space-between;">
                <span id="currentUser"></span>
                <button onclick="logout()" style="width: auto;">Выйти</button>
            </div>
            <input type="text" id="toUser" placeholder="Кому (ник)">
            <div style="display: flex; gap: 10px;">
                <input type="text" id="messageInput" placeholder="Сообщение" style="flex: 1;">
                <button onclick="sendMessage()" style="width: auto;">➤</button>
            </div>
            <div id="messages"></div>
        </div>
    </div>

    <script>
        let currentUser = null;

        async function apiCall(url, data) {
            const res = await fetch(url, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            return res.json();
        }

        async function register() {
            const u = document.getElementById('loginUser').value;
            const p = document.getElementById('loginPass').value;
            const res = await apiCall('/register', {username: u, password: p});
            alert(res.success ? 'Регистрация успешна' : 'Ошибка');
        }

        async function login() {
            const u = document.getElementById('loginUser').value;
            const p = document.getElementById('loginPass').value;
            const res = await apiCall('/login', {username: u, password: p});
            if (res.success) {
                currentUser = u;
                document.getElementById('loginScreen').classList.add('hidden');
                document.getElementById('chatScreen').classList.remove('hidden');
                document.getElementById('currentUser').innerText = u;
                loadMessages();
            } else {
                alert('Неверный логин/пароль');
            }
        }

        function logout() {
            currentUser = null;
            document.getElementById('loginScreen').classList.remove('hidden');
            document.getElementById('chatScreen').classList.add('hidden');
        }

        async function sendMessage() {
            if (!currentUser) return;
            const to = document.getElementById('toUser').value;
            const text = document.getElementById('messageInput').value;
            if (!to || !text) return;
            await apiCall('/send', {from: currentUser, to, text});
            document.getElementById('messageInput').value = '';
            loadMessages();
        }

        async function loadMessages() {
            if (!currentUser) return;
            const res = await fetch('/messages/' + currentUser);
            const msgs = await res.json();
            const container = document.getElementById('messages');
            container.innerHTML = msgs.reverse().map(m => 
                `<div class="message ${m.from === currentUser ? 'my-message' : 'other-message'}">
                    <b>${m.from}</b>: ${m.text}
                    <small>${m.time || ''}</small>
                </div>`
            ).join('');
            container.scrollTop = container.scrollHeight;
        }

        setInterval(() => { if (currentUser) loadMessages(); }, 3000);
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
