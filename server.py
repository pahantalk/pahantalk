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

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>ПАХАНТАЛК — Telegram Web</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #0e1621;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 10px;
        }
        .tg-container {
            display: flex;
            width: 1400px;
            max-width: 100%;
            height: 95vh;
            background: #17212b;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        .left-panel {
            width: 70px;
            background: #1e2a36;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px 0;
            border-right: 1px solid #253441;
        }
        .avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: #2b7ad0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 20px;
            margin-bottom: 30px;
            cursor: pointer;
            overflow: hidden;
        }
        .avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .nav-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #7f91a4;
            font-size: 24px;
            margin: 8px 0;
            cursor: pointer;
        }
        .nav-icon:hover {
            background: #253441;
            color: white;
        }
        .nav-icon.active {
            background: #2b7ad0;
            color: white;
        }
        .chats-panel {
            width: 320px;
            background: #17212b;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #253441;
        }
        .chats-header {
            padding: 16px;
            border-bottom: 1px solid #253441;
        }
        .chats-header h2 {
            color: white;
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 12px;
        }
        .search-box {
            background: #1e2a36;
            border: 1px solid #253441;
            border-radius: 8px;
            padding: 10px 12px;
            color: white;
            width: 100%;
            font-size: 14px;
            outline: none;
        }
        .chats-list {
            flex: 1;
            overflow-y: auto;
        }
        .chat-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid #1e2a36;
        }
        .chat-item:hover {
            background: #1e2a36;
        }
        .chat-item.active {
            background: #2b5278;
        }
        .chat-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: #2b7ad0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            margin-right: 12px;
            overflow: hidden;
        }
        .chat-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .chat-info {
            flex: 1;
            min-width: 0;
        }
        .chat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
        }
        .chat-name {
            color: white;
            font-weight: 500;
            font-size: 15px;
        }
        .chat-time {
            color: #7f91a4;
            font-size: 11px;
        }
        .chat-last-msg {
            color: #7f91a4;
            font-size: 13px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .dialog-panel {
            flex: 1;
            background: #17212b;
            display: flex;
            flex-direction: column;
        }
        .dialog-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
            border-bottom: 1px solid #253441;
            background: #1e2a36;
        }
        .dialog-header-left {
            display: flex;
            align-items: center;
            cursor: pointer;
        }
        .dialog-avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: #2b7ad0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            margin-right: 14px;
            overflow: hidden;
        }
        .dialog-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .dialog-info {
            line-height: 1.3;
        }
        .dialog-name {
            color: white;
            font-weight: 600;
            font-size: 16px;
        }
        .dialog-status {
            color: #4CAF50;
            font-size: 13px;
            display: flex;
            align-items: center;
        }
        .dialog-status::before {
            content: '';
            width: 8px;
            height: 8px;
            background: #4CAF50;
            border-radius: 50%;
            margin-right: 6px;
        }
        .dialog-header-icons {
            display: flex;
            gap: 16px;
            color: #7f91a4;
            font-size: 20px;
        }
        .messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: #17212b;
        }
        .message {
            max-width: 65%;
            padding: 10px 14px;
            border-radius: 18px;
            word-wrap: break-word;
            font-size: 14px;
            line-height: 1.5;
        }
        .message.own {
            background: #2b5278;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 6px;
        }
        .message.other {
            background: #1e2a36;
            color: #e0e0e0;
            align-self: flex-start;
            border-bottom-left-radius: 6px;
        }
        .message img {
            max-width: 100%;
            border-radius: 12px;
            margin-top: 5px;
            cursor: pointer;
        }
        .message small {
            display: block;
            font-size: 11px;
            color: #7f91a4;
            margin-top: 4px;
            text-align: right;
        }
        .input-area {
            padding: 12px 20px;
            background: #1e2a36;
            border-top: 1px solid #253441;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .input-area input {
            flex: 1;
            background: #17212b;
            border: 1px solid #253441;
            border-radius: 24px;
            padding: 12px 16px;
            color: white;
            font-size: 14px;
            outline: none;
        }
        .send-btn {
            background: #2b7ad0;
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
            cursor: pointer;
        }
        .hidden {
            display: none;
        }
        .logout-btn {
            background: #d32f2f;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 13px;
            cursor: pointer;
            margin-left: 10px;
        }
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background: #17212b;
            padding: 30px;
            border-radius: 16px;
            width: 400px;
            max-width: 90%;
        }
    </style>
</head>
<body>
    <div class="tg-container">
        <div class="left-panel">
            <div class="avatar" id="myAvatar" onclick="openMyProfile()"></div>
            <div class="nav-icon active">💬</div>
            <div class="nav-icon">👥</div>
            <div class="nav-icon">📞</div>
            <div class="nav-icon">⚙️</div>
        </div>
        <div class="chats-panel">
            <div class="chats-header">
                <h2>Чаты</h2>
                <input class="search-box" id="searchInput" placeholder="Поиск">
            </div>
            <div class="chats-list" id="chatsList"></div>
        </div>
        <div class="dialog-panel">
            <div class="dialog-header" id="dialogHeader">
                <div class="dialog-header-left" onclick="openProfile(currentChat)">
                    <div class="dialog-avatar" id="dialogAvatar"></div>
                    <div class="dialog-info">
                        <div class="dialog-name" id="dialogName">Выберите чат</div>
                        <div class="dialog-status" id="dialogStatus"></div>
                    </div>
                </div>
                <div class="dialog-header-icons">
                    <span>🔍</span>
                    <span>⋮</span>
                    <button class="logout-btn" onclick="logout()">Выйти</button>
                </div>
            </div>
            <div class="messages-area" id="messagesArea"></div>
            <div class="input-area" id="inputArea">
                <input type="text" id="messageInput" placeholder="Сообщение">
                <button class="send-btn" onclick="sendMessage()">➤</button>
            </div>
        </div>
    </div>
    <div id="loginScreen" class="modal">
        <div class="modal-content">
            <h2 style="color:white;">Вход</h2>
            <input type="text" id="loginUser" placeholder="Логин">
            <input type="password" id="loginPass" placeholder="Пароль">
            <button onclick="login()">Войти</button>
            <button onclick="register()">Регистрация</button>
        </div>
    </div>
    <script>
        let currentUser = localStorage.getItem('pahantalk_user');
        let currentChat = null;

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
            alert(res.success ? 'OK' : 'Ошибка');
        }

        async function login() {
            const u = document.getElementById('loginUser').value;
            const p = document.getElementById('loginPass').value;
            const res = await apiCall('/login', {username: u, password: p});
            if (res.success) {
                currentUser = u;
                localStorage.setItem('pahantalk_user', u);
                document.getElementById('loginScreen').style.display = 'none';
                loadProfile();
                loadChats();
            } else {
                alert('Неверный логин/пароль');
            }
        }

        function logout() {
            currentUser = null;
            localStorage.removeItem('pahantalk_user');
            location.reload();
        }

        async function loadProfile() {
            const res = await fetch('/user/' + currentUser);
            const user = await res.json();
            const avatar = document.getElementById('myAvatar');
            avatar.innerHTML = user.avatar ? `<img src="${user.avatar}">` : (currentUser[0] || '').toUpperCase();
        }

        async function loadChats() {
            const res = await fetch('/chats/' + currentUser);
            const chats = await res.json();
            const list = document.getElementById('chatsList');
            list.innerHTML = '';
            for (let chat of chats) {
                const u = await (await fetch('/user/' + chat.username)).json();
                list.innerHTML += `
                    <div class="chat-item ${chat.username === currentChat ? 'active' : ''}" onclick="selectChat('${chat.username}')">
                        <div class="chat-avatar">${u.avatar ? `<img src="${u.avatar}">` : chat.username[0]}</div>
                        <div class="chat-info">
                            <div class="chat-row">
                                <span class="chat-name">${u.display_name || chat.username}</span>
                                <span class="chat-time">${chat.last_time || ''}</span>
                            </div>
                            <div class="chat-last-msg">${chat.last_msg || ''}</div>
                        </div>
                    </div>
                `;
            }
        }

        async function selectChat(username) {
            currentChat = username;
            document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
            event.currentTarget.classList.add('active');
            const u = await (await fetch('/user/' + username)).json();
            document.getElementById('dialogName').innerText = u.display_name || username;
            document.getElementById('dialogStatus').innerText = u.status || 'в сети';
            const avatar = document.getElementById('dialogAvatar');
            avatar.innerHTML = u.avatar ? `<img src="${u.avatar}">` : (username[0] || '').toUpperCase();
            loadMessages();
        }

        async function sendMessage() {
            if (!currentChat) return;
            const input = document.getElementById('messageInput');
            const text = input.value;
            if (!text) return;
            await apiCall('/send', {from: currentUser, to: currentChat, text});
            input.value = '';
            loadMessages();
        }

        async function loadMessages() {
            if (!currentChat) return;
            const res = await fetch('/messages/' + currentUser + '?with=' + currentChat);
            const msgs = await res.json();
            const area = document.getElementById('messagesArea');
            area.innerHTML = msgs.reverse().map(m => {
                const own = m.from === currentUser;
                return `<div class="message ${own ? 'own' : 'other'}">
                    ${!own ? '<b>' + m.from + '</b> ' : ''}${m.text}
                    <small>${m.time || ''}</small>
                </div>`;
            }).join('');
            area.scrollTop = area.scrollHeight;
        }

        if (currentUser) {
            document.getElementById('loginScreen').style.display = 'none';
            loadProfile();
            loadChats();
        }

        setInterval(() => { if (currentChat) loadMessages(); }, 3000);
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
    with_user = request.args.get('with', '')
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    if with_user:
        c.execute("""SELECT from_user, to_user, text, 
                     strftime('%H:%M', timestamp) as time 
                     FROM messages 
                     WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?)
                     ORDER BY timestamp DESC LIMIT 50""",
                  (username, with_user, with_user, username))
    else:
        c.execute("""SELECT from_user, to_user, text, 
                     strftime('%H:%M', timestamp) as time 
                     FROM messages 
                     WHERE from_user=? OR to_user=?
                     ORDER BY timestamp DESC LIMIT 50""",
                  (username, username))
    msgs = [{'from': r[0], 'to': r[1], 'text': r[2], 'time': r[3]} for r in c.fetchall()]
    conn.close()
    return jsonify(msgs)

@app.route('/chats/<username>')
def get_chats(username):
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("""SELECT DISTINCT 
                    CASE WHEN from_user=? THEN to_user ELSE from_user END
                 FROM messages 
                 WHERE from_user=? OR to_user=?""",
              (username, username, username))
    chats = []
    for row in c.fetchall():
        chat_user = row[0]
        if not chat_user or chat_user == username:
            continue
        c2 = conn.cursor()
        c2.execute("""SELECT text, strftime('%H:%M', timestamp) 
                      FROM messages 
                      WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?)
                      ORDER BY timestamp DESC LIMIT 1""",
                   (username, chat_user, chat_user, username))
        last = c2.fetchone()
        chats.append({
            'username': chat_user,
            'last_msg': last[0] if last else '',
            'last_time': last[1] if last else ''
        })
    conn.close()
    return jsonify(chats)

@app.route('/user/<username>')
def get_user(username):
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("SELECT username, display_name, avatar, status FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({
            'username': row[0],
            'display_name': row[1],
            'avatar': row[2],
            'status': row[3]
        })
    return jsonify({})

@app.route('/users')
def get_users():
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    return jsonify(users)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
