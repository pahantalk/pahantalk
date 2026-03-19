# server.py - ПАХАНТАЛК с профилями (рабочая версия)
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

# ==================== HTML (вынесен отдельно) ====================
HTML_HEAD = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ПАХАНТАЛК — Telegram Style</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', 'Roboto', system-ui, -apple-system, sans-serif;
            background: #1e1e1e;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 16px;
        }

        .tg-container {
            display: flex;
            width: 1400px;
            max-width: 100%;
            height: 90vh;
            background: #1f1f1f;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.8);
        }

        .left-panel {
            width: 72px;
            background: #1a1a1a;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px 0;
            border-right: 1px solid #2f2f2f;
        }

        .avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2a7ad0, #4e9bef);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 20px;
            margin-bottom: 30px;
            cursor: pointer;
            border: 2px solid transparent;
            object-fit: cover;
        }

        .avatar:hover {
            border-color: #4e9bef;
        }

        .avatar img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
        }

        .nav-icon {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #8e959f;
            font-size: 24px;
            margin: 8px 0;
            cursor: pointer;
        }

        .nav-icon:hover {
            background: #2a2a2a;
            color: #ffffff;
        }

        .nav-icon.active {
            background: #2b5278;
            color: #ffffff;
        }

        .chats-panel {
            width: 320px;
            background: #1a1a1a;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #2f2f2f;
        }

        .chats-header {
            padding: 16px;
            border-bottom: 1px solid #2f2f2f;
        }

        .chats-header h2 {
            color: #ffffff;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 12px;
        }

        .search-box {
            background: #2a2a2a;
            border: 1px solid #3a3a3a;
            border-radius: 24px;
            padding: 10px 16px;
            color: #ffffff;
            width: 100%;
            font-size: 14px;
            outline: none;
        }

        .search-box:focus {
            border-color: #2a7ad0;
        }

        .chats-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px 0;
        }

        .chat-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid #2a2a2a;
        }

        .chat-item:hover {
            background: #2a2a2a;
        }

        .chat-item.active {
            background: #2b5278;
        }

        .chat-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2a7ad0, #4e9bef);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            margin-right: 12px;
            font-size: 18px;
            object-fit: cover;
        }

        .chat-avatar img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
        }

        .chat-info {
            flex: 1;
            min-width: 0;
        }

        .chat-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 4px;
        }

        .chat-name {
            color: #ffffff;
            font-weight: 600;
            font-size: 15px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .chat-time {
            color: #8e959f;
            font-size: 11px;
            margin-left: 8px;
        }

        .chat-last-msg {
            color: #8e959f;
            font-size: 13px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .dialog-panel {
            flex: 1;
            background: #1a1a1a;
            display: flex;
            flex-direction: column;
        }

        .dialog-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
            border-bottom: 1px solid #2f2f2f;
            background: #1f1f1f;
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
            background: linear-gradient(135deg, #2a7ad0, #4e9bef);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            margin-right: 14px;
            font-size: 18px;
            object-fit: cover;
        }

        .dialog-avatar img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
        }

        .dialog-info {
            line-height: 1.3;
        }

        .dialog-name {
            color: #ffffff;
            font-weight: 600;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
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
            color: #8e959f;
            font-size: 22px;
        }

        .dialog-header-icons span {
            cursor: pointer;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        .dialog-header-icons span:hover {
            background: #2a2a2a;
        }

        .messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: #1a1a1a;
        }

        .message {
            max-width: 65%;
            padding: 10px 14px;
            border-radius: 18px;
            word-wrap: break-word;
            font-size: 14px;
            line-height: 1.5;
            position: relative;
        }

        .message.own {
            background: #2b5278;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 6px;
        }

        .message.other {
            background: #2a2a2a;
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
            color: rgba(255, 255, 255, 0.5);
            margin-top: 4px;
            text-align: right;
        }

        .input-area {
            padding: 12px 20px;
            background: #1f1f1f;
            border-top: 1px solid #2f2f2f;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .attach-icon, .emoji-icon {
            color: #8e959f;
            font-size: 24px;
            cursor: pointer;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        .attach-icon:hover, .emoji-icon:hover {
            background: #2a2a2a;
        }

        .input-area input {
            flex: 1;
            background: #2a2a2a;
            border: 1px solid #3a3a3a;
            border-radius: 24px;
            padding: 12px 16px;
            color: #ffffff;
            font-size: 14px;
            outline: none;
        }

        .input-area input:focus {
            border-color: #2a7ad0;
        }

        .send-btn {
            background: #2a7ad0;
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

        .send-btn:hover {
            background: #1f6abc;
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

        .logout-btn:hover {
            background: #b71c1c;
        }

        .emoji-picker {
            position: absolute;
            bottom: 80px;
            right: 20px;
            background: #2a2a2a;
            border-radius: 12px;
            padding: 10px;
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            border: 1px solid #3a3a3a;
            z-index: 100;
        }

        .emoji-picker span {
            font-size: 24px;
            cursor: pointer;
            text-align: center;
            padding: 5px;
            border-radius: 8px;
        }

        .emoji-picker span:hover {
            background: #3a3a3a;
        }

        .search-results {
            background: #2a2a2a;
            border-radius: 8px;
            margin-top: 5px;
            max-height: 200px;
            overflow-y: auto;
            position: absolute;
            width: calc(100% - 32px);
            z-index: 10;
        }

        .search-result-item {
            padding: 10px;
            cursor: pointer;
            color: white;
            border-bottom: 1px solid #3a3a3a;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .search-result-item:hover {
            background: #3a3a3a;
        }

        .profile-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .profile-content {
            background: #2a2a2a;
            border-radius: 16px;
            padding: 30px;
            width: 400px;
            max-width: 90%;
            border: 1px solid #3a3a3a;
        }

        .profile-content h3 {
            color: white;
            margin-bottom: 20px;
        }

        .profile-avatar {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            margin: 0 auto 20px;
            background: #2a7ad0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 40px;
            cursor: pointer;
            overflow: hidden;
        }

        .profile-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .profile-input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: #1a1a1a;
            border: 1px solid #3a3a3a;
            border-radius: 8px;
            color: white;
        }

        .profile-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        .profile-buttons button {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }

        .save-btn {
            background: #2a7ad0;
            color: white;
        }

        .cancel-btn {
            background: #3a3a3a;
            color: white;
        }

        #file-input, #avatar-input {
            display: none;
        }
    </style>
</head>
<body>
    <div class="tg-container">
        <div class="left-panel">
            <div class="avatar" id="myAvatar" onclick="openMyProfile()">
                <img src="" style="display: none;" id="myAvatarImg">
                <span id="myAvatarText">2K</span>
            </div>
            <div class="nav-icon active">💬</div>
            <div class="nav-icon">👥</div>
            <div class="nav-icon">📞</div>
            <div class="nav-icon" onclick="openSettings()">⚙️</div>
        </div>

        <div class="chats-panel">
            <div class="chats-header">
                <h2>Чаты</h2>
                <input class="search-box" id="userSearch" type="text" placeholder="Поиск..." oninput="searchUsers()">
                <div id="searchResults" class="search-results" style="display: none;"></div>
            </div>
            <div class="chats-list" id="chatsList"></div>
        </div>

        <div class="dialog-panel">
            <div class="dialog-header" id="dialogHeader" style="display: none;">
                <div class="dialog-header-left" onclick="openUserProfile(currentChat)">
                    <div class="dialog-avatar" id="dialogAvatar">
                        <img src="" style="display: none;" id="dialogAvatarImg">
                        <span id="dialogAvatarText">?</span>
                    </div>
                    <div class="dialog-info">
                        <div class="dialog-name">
                            <span id="dialogName">Загрузка...</span>
                            <button class="logout-btn" id="logoutBtn" onclick="logout()">Выйти</button>
                        </div>
                        <div class="dialog-status" id="dialogStatus">в сети</div>
                    </div>
                </div>
                <div class="dialog-header-icons">
                    <span>🔍</span>
                    <span>⋮</span>
                </div>
            </div>

            <div class="messages-area" id="messagesArea">
                <div style="color: #666; text-align: center; padding: 20px;">Выберите чат</div>
            </div>

            <div class="input-area" id="inputArea" style="display: none;">
                <span class="attach-icon" onclick="document.getElementById('file-input').click()">📎</span>
                <span class="emoji-icon" onclick="toggleEmojiPicker()">😊</span>
                <input type="text" id="messageInput" placeholder="Сообщение..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button class="send-btn" onclick="sendMessage()">➤</button>
                <input type="file" id="file-input" accept="image/*" onchange="uploadImage()" style="display: none;">
            </div>

            <div id="loginScreen" style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; padding: 20px;">
                <h2 style="color: white;">Вход</h2>
                <input type="text" id="loginUsername" placeholder="Логин" style="width: 80%; padding: 12px; margin: 8px;">
                <input type="password" id="loginPassword" placeholder="Пароль" style="width: 80%; padding: 12px; margin: 8px;">
                <div style="display: flex; gap: 10px;">
                    <button onclick="login()">Войти</button>
                    <button onclick="register()">Регистрация</button>
                </div>
            </div>
        </div>
    </div>

    <div id="emojiPicker" class="emoji-picker" style="display: none;">
        <span onclick="addEmoji('😊')">😊</span>
        <span onclick="addEmoji('😂')">😂</span>
        <span onclick="addEmoji('❤️')">❤️</span>
        <span onclick="addEmoji('🔥')">🔥</span>
        <span onclick="addEmoji('👍')">👍</span>
    </div>

    <div id="profileModal" style="display: none;" class="profile-modal">
        <div class="profile-content">
            <h3 id="profileTitle">Профиль</h3>
            <div class="profile-avatar" id="profileAvatar" onclick="document.getElementById('avatar-input').click()">
                <img src="" style="display: none;" id="profileAvatarImg">
                <span id="profileAvatarText"></span>
            </div>
            <input type="text" id="profileUsername" class="profile-input" placeholder="Логин" readonly>
            <input type="text" id="profileDisplayName" class="profile-input" placeholder="Имя">
            <input type="text" id="profileStatus" class="profile-input" placeholder="Статус">
            <textarea id="profileBio" class="profile-input" placeholder="О себе"></textarea>
            <div class="profile-buttons">
                <button class="save-btn" onclick="saveProfile()">Сохранить</button>
                <button class="cancel-btn" onclick="closeProfile()">Отмена</button>
            </div>
            <input type="file" id="avatar-input" accept="image/*" style="display: none;" onchange="uploadAvatar()">
        </div>
    </div>

    <script>
        let currentUser = localStorage.getItem('pahantalk_user');
        let currentChat = null;
        let allUsers = [];
        let currentProfileUser = null;

        async function apiCall(url, data) {
            const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
            return r.json();
        }

        async function register() {
            const u = document.getElementById('loginUsername').value;
            const p = document.getElementById('loginPassword').value;
            const res = await apiCall('/register', {username:u, password:p});
            alert(res.success ? 'OK' : 'Ошибка');
        }

        async function login() {
            const u = document.getElementById('loginUsername').value;
            const p = document.getElementById('loginPassword').value;
            const res = await apiCall('/login', {username:u, password:p});
            if(res.success) {
                currentUser = u;
                localStorage.setItem('pahantalk_user', u);
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('dialogHeader').style.display = 'flex';
                document.getElementById('inputArea').style.display = 'flex';
                loadMyProfile();
                loadChats();
                loadAllUsers();
            }
        }

        function logout() {
            currentUser = null;
            localStorage.removeItem('pahantalk_user');
            location.reload();
        }

        async function loadMyProfile() {
            const r = await fetch('/user/' + currentUser);
            const user = await r.json();
            if(user.avatar) {
                document.getElementById('myAvatarImg').src = user.avatar;
                document.getElementById('myAvatarImg').style.display = 'block';
                document.getElementById('myAvatarText').style.display = 'none';
            }
        }

        async function sendMessage() {
            if(!currentChat) return;
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            if(!text) return;
            await apiCall('/send', {from:currentUser, to:currentChat, text:text});
            input.value = '';
            loadMessages();
            loadChats();
        }

        async function uploadImage() {
            const input = document.getElementById('file-input');
            if(!input.files.length) return;
            const fd = new FormData();
            fd.append('image', input.files[0]);
            fd.append('from', currentUser);
            fd.append('to', currentChat);
            await fetch('/upload', {method:'POST', body:fd});
            input.value = '';
            loadMessages();
            loadChats();
        }

        async function loadMessages() {
            if(!currentChat) return;
            const r = await fetch('/messages/' + currentUser + '?with=' + currentChat);
            const msgs = await r.json();
            const area = document.getElementById('messagesArea');
            area.innerHTML = msgs.reverse().map(m => {
                const own = m.from === currentUser;
                let content = m.text || (m.image ? `<img src="${m.image}">` : '');
                return `<div class="message ${own ? 'own' : 'other'}">
                    ${!own ? '<b>' + m.from + '</b> ' : ''}${content}
                    <small>${m.time || ''}</small>
                </div>`;
            }).join('');
        }

        async function loadChats() {
            const r = await fetch('/chats/' + currentUser);
            const chats = await r.json();
            const list = document.getElementById('chatsList');
            list.innerHTML = '';
            for(let c of chats) {
                const ur = await fetch('/user/' + c.username);
                const u = await ur.json();
                list.innerHTML += `<div class="chat-item ${c.username === currentChat ? 'active' : ''}" onclick="selectChat('${c.username}')">
                    <div class="chat-avatar">${u.avatar ? `<img src="${u.avatar}">` : c.username[0].toUpperCase()}</div>
                    <div class="chat-info">
                        <div><b>${u.display_name || c.username}</b> <small>${c.last_time || ''}</small></div>
                        <div>${c.last_msg || ''}</div>
                    </div>
                </div>`;
            }
        }

        async function loadAllUsers() {
            const r = await fetch('/users');
            allUsers = await r.json();
        }

        function searchUsers() {
            const q = document.getElementById('userSearch').value.toLowerCase();
            const res = document.getElementById('searchResults');
            if(q.length < 2) { res.style.display = 'none'; return; }
            const filtered = allUsers.filter(u => u.includes(q) && u !== currentUser).slice(0,5);
            if(!filtered.length) { res.style.display = 'none'; return; }
            res.innerHTML = filtered.map(u => `<div class="search-result-item" onclick="selectChat('${u}')">${u}</div>`).join('');
            res.style.display = 'block';
        }

        function selectChat(u) {
            currentChat = u;
            document.getElementById('searchResults').style.display = 'none';
            document.getElementById('userSearch').value = '';
            document.getElementById('dialogName').innerText = u;
            loadMessages();
            loadChats();
        }

        function toggleEmojiPicker() {
            const p = document.getElementById('emojiPicker');
            p.style.display = p.style.display === 'none' ? 'grid' : 'none';
        }

        function addEmoji(e) {
            document.getElementById('messageInput').value += e;
            toggleEmojiPicker();
        }

        if(currentUser) {
            (async () => {
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('dialogHeader').style.display = 'flex';
                document.getElementById('inputArea').style.display = 'flex';
                await loadMyProfile();
                await loadChats();
                await loadAllUsers();
            })();
        }

        setInterval(() => { if(currentChat) loadMessages(); }, 3000);
    </script>
</body>
</html>"""

HTML = HTML_HEAD

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

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'success': False})
    file = request.files['image']
    from_user = request.form.get('from')
    to_user = request.form.get('to')
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        url = '/uploads/' + filename
        conn = sqlite3.connect('pahantalk.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (from_user, to_user, image) VALUES (?, ?, ?)",
                  (from_user, to_user, url))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({'success': False})
    file = request.files['avatar']
    username = request.form.get('username')
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        path = os.path.join(AVATAR_FOLDER, filename)
        file.save(path)
        url = '/avatars/' + filename
        conn = sqlite3.connect('pahantalk.db')
        c = conn.cursor()
        c.execute("UPDATE users SET avatar=? WHERE username=?", (url, username))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/user/<username>')
def get_user(username):
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("SELECT username, display_name, avatar, status, bio FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({
            'username': row[0],
            'display_name': row[1],
            'avatar': row[2],
            'status': row[3],
            'bio': row[4]
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

@app.route('/messages/<username>')
def get_messages(username):
    with_user = request.args.get('with', '')
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    if with_user:
        c.execute("""SELECT from_user, to_user, text, image,
                     strftime('%H:%M', timestamp) as time 
                     FROM messages 
                     WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?)
                     ORDER BY timestamp DESC LIMIT 50""",
                  (username, with_user, with_user, username))
    else:
        c.execute("""SELECT from_user, to_user, text, image,
                     strftime('%H:%M', timestamp) as time 
                     FROM messages 
                     WHERE from_user=? OR to_user=?
                     ORDER BY timestamp DESC LIMIT 50""",
                  (username, username))
    msgs = []
    for r in c.fetchall():
        msg = {'from': r[0], 'to': r[1], 'time': r[4]}
        if r[2]: msg['text'] = r[2]
        if r[3]: msg['image'] = r[3]
        msgs.append(msg)
    conn.close()
    return jsonify(msgs)

@app.route('/chats/<username>')
def get_chats(username):
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    # Получаем список собеседников
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
        # Последнее сообщение
        c2 = conn.cursor()
        c2.execute("""SELECT text, image, 
                      strftime('%H:%M', timestamp) 
                      FROM messages 
                      WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?)
                      ORDER BY timestamp DESC LIMIT 1""",
                   (username, chat_user, chat_user, username))
        last = c2.fetchone()
        last_msg = 'Нет сообщений'
        last_time = ''
        if last:
            if last[0]:
                last_msg = last[0]
            elif last[1]:
                last_msg = '🖼️ Фото'
            last_time = last[2] or ''
        chats.append({
            'username': chat_user,
            'last_msg': last_msg,
            'last_time': last_time
        })
    conn.close()
    return jsonify(chats)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route('/avatars/<filename>')
def avatar_file(filename):
    return send_file(os.path.join(AVATAR_FOLDER, filename))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
