# server.py - ПАХАНТАЛК с картинками
from flask import Flask, request, jsonify, send_file
import sqlite3
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# База данных
def init_db():
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  from_user TEXT NOT NULL,
                  to_user TEXT NOT NULL,
                  text TEXT,
                  image TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    try:
        c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                  ("2kenta", "123"))
        c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                  ("pahan", "123"))
    except:
        pass
    conn.commit()
    conn.close()

init_db()

HTML = """<!DOCTYPE html>
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
            transition: 0.2s;
            border: 2px solid transparent;
        }

        .avatar:hover {
            border-color: #4e9bef;
            transform: scale(1.02);
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
            transition: 0.2s;
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
            transition: 0.2s;
        }

        .search-box:focus {
            border-color: #2a7ad0;
            background: #2f2f2f;
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
            transition: 0.2s;
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
            flex-shrink: 0;
            font-size: 18px;
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
            display: inline-block;
        }

        .dialog-header-icons {
            display: flex;
            gap: 16px;
            color: #8e959f;
            font-size: 22px;
        }

        .dialog-header-icons span {
            cursor: pointer;
            transition: 0.2s;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        .dialog-header-icons span:hover {
            background: #2a2a2a;
            color: #ffffff;
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
            animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
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

        .message .status {
            display: inline-flex;
            align-items: center;
            gap: 2px;
            font-size: 12px;
            margin-left: 8px;
            color: rgba(255, 255, 255, 0.6);
        }

        .message.own .status::after {
            content: '✓✓';
            letter-spacing: -2px;
            font-size: 13px;
            margin-left: 4px;
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
            transition: 0.2s;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        .attach-icon:hover, .emoji-icon:hover {
            background: #2a2a2a;
            color: #ffffff;
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
            transition: 0.2s;
        }

        .input-area input:focus {
            border-color: #2a7ad0;
            background: #2f2f2f;
        }

        .input-area input::placeholder {
            color: #6b6f77;
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
            transition: 0.2s;
        }

        .send-btn:hover {
            background: #1f6abc;
            transform: scale(1.05);
        }

        ::-webkit-scrollbar {
            width: 5px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1a1a;
        }

        ::-webkit-scrollbar-thumb {
            background: #3a3a3a;
            border-radius: 10px;
        }

        @media (max-width: 900px) {
            .left-panel { width: 60px; }
            .chats-panel { width: 280px; }
        }

        @media (max-width: 700px) {
            .chats-panel { display: none; }
            .left-panel { width: 60px; }
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
        }

        .search-result-item:hover {
            background: #3a3a3a;
        }

        #file-input {
            display: none;
        }
    </style>
</head>
<body>
    <div class="tg-container">
        <div class="left-panel">
            <div class="avatar" onclick="location.reload()">2K</div>
            <div class="nav-icon active">💬</div>
            <div class="nav-icon">👥</div>
            <div class="nav-icon">📞</div>
            <div class="nav-icon">⚙️</div>
        </div>

        <div class="chats-panel">
            <div class="chats-header">
                <h2>Чаты</h2>
                <input class="search-box" id="userSearch" type="text" placeholder="Поиск пользователей..." oninput="searchUsers()">
                <div id="searchResults" class="search-results" style="display: none;"></div>
            </div>
            <div class="chats-list" id="chatsList"></div>
        </div>

        <div class="dialog-panel">
            <div class="dialog-header" id="dialogHeader" style="display: none;">
                <div class="dialog-header-left">
                    <div class="dialog-avatar" id="dialogAvatar">?</div>
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
                <input type="text" id="messageInput" placeholder="Написать сообщение..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button class="send-btn" onclick="sendMessage()">➤</button>
                <input type="file" id="file-input" accept="image/*" onchange="uploadImage()" style="display: none;">
            </div>

            <div id="loginScreen" style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; padding: 20px;">
                <h2 style="color: white; margin-bottom: 20px;">Вход в ПАХАНТАЛК</h2>
                <input type="text" id="loginUsername" placeholder="Логин" style="width: 80%; padding: 12px; margin: 8px; border-radius: 8px; border: none;">
                <input type="password" id="loginPassword" placeholder="Пароль" style="width: 80%; padding: 12px; margin: 8px; border-radius: 8px; border: none;">
                <div style="display: flex; gap: 10px; margin-top: 15px;">
                    <button onclick="login()" style="padding: 12px 30px; background: #2a7ad0; color: white; border: none; border-radius: 8px; cursor: pointer;">Войти</button>
                    <button onclick="register()" style="padding: 12px 30px; background: #3a3a3a; color: white; border: none; border-radius: 8px; cursor: pointer;">Регистрация</button>
                </div>
                <p style="color: #8e959f; margin-top: 20px;">Тестовые: 2kenta / 123</p>
            </div>
        </div>
    </div>

    <div id="emojiPicker" class="emoji-picker" style="display: none;">
        <span onclick="addEmoji('😊')">😊</span>
        <span onclick="addEmoji('😂')">😂</span>
        <span onclick="addEmoji('❤️')">❤️</span>
        <span onclick="addEmoji('🔥')">🔥</span>
        <span onclick="addEmoji('👍')">👍</span>
        <span onclick="addEmoji('👎')">👎</span>
        <span onclick="addEmoji('😢')">😢</span>
        <span onclick="addEmoji('😍')">😍</span>
        <span onclick="addEmoji('🎉')">🎉</span>
        <span onclick="addEmoji('💀')">💀</span>
    </div>

    <script>
        let currentUser = localStorage.getItem('pahantalk_user');
        let currentChat = null;
        let allUsers = [];

        async function apiCall(url, data) {
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                return await response.json();
            } catch(e) {
                console.error('API Error:', e);
                return null;
            }
        }

        async function register() {
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            if (!username || !password) {
                alert('Введи логин и пароль');
                return;
            }
            const result = await apiCall('/register', {username, password});
            if (result && result.success) {
                alert('Регистрация успешна! Теперь войди.');
            } else {
                alert('Ошибка: пользователь уже существует');
            }
        }

        async function login() {
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            if (!username || !password) {
                alert('Введи логин и пароль');
                return;
            }
            const result = await apiCall('/login', {username, password});
            if (result && result.success) {
                currentUser = username;
                localStorage.setItem('pahantalk_user', username);
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('dialogHeader').style.display = 'flex';
                document.getElementById('inputArea').style.display = 'flex';
                loadChats();
                loadAllUsers();
            } else {
                alert('Неверный логин или пароль');
            }
        }

        function logout() {
            currentUser = null;
            currentChat = null;
            localStorage.removeItem('pahantalk_user');
            document.getElementById('loginScreen').style.display = 'flex';
            document.getElementById('dialogHeader').style.display = 'none';
            document.getElementById('inputArea').style.display = 'none';
            document.getElementById('messagesArea').innerHTML = '<div style="color: #666; text-align: center; padding: 20px;">Выберите чат</div>';
            document.getElementById('chatsList').innerHTML = '';
        }

        async function sendMessage() {
            if (!currentUser || !currentChat) {
                alert('Сначала выбери чат');
                return;
            }
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            if (!text) return;

            const result = await apiCall('/send', {
                from: currentUser,
                to: currentChat,
                text: text
            });

            if (result && result.success) {
                input.value = '';
                loadMessages();
                loadChats();
            }
        }

        async function uploadImage() {
            const fileInput = document.getElementById('file-input');
            if (!fileInput.files.length) return;
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('image', file);
            formData.append('from', currentUser);
            formData.append('to', currentChat);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (result.success) {
                    loadMessages();
                    loadChats();
                } else {
                    alert('Ошибка загрузки');
                }
            } catch(e) {
                console.error('Upload error:', e);
                alert('Ошибка');
            }
            fileInput.value = '';
        }

        async function loadMessages() {
            if (!currentUser || !currentChat) return;
            try {
                const response = await fetch('/messages/' + currentUser + '?with=' + currentChat);
                const messages = await response.json();
                const area = document.getElementById('messagesArea');
                area.innerHTML = messages.reverse().map(msg => {
                    const isOwn = msg.from === currentUser;
                    let content = '';
                    if (msg.text) {
                        content = msg.text;
                    } else if (msg.image) {
                        content = `<img src="${msg.image}" onclick="window.open(this.src)" style="max-width: 200px; max-height: 200px;">`;
                    }
                    return `<div class="message ${isOwn ? 'own' : 'other'}">
                        ${!isOwn ? '<strong>' + msg.from + '</strong>' : ''}
                        ${content}
                        <small>${msg.time || ''}</small>
                        ${isOwn ? '<span class="status"></span>' : ''}
                    </div>`;
                }).join('');
                area.scrollTop = area.scrollHeight;
            } catch(e) {
                console.error('Load messages error:', e);
            }
        }

        async function loadChats() {
            if (!currentUser) return;
            try {
                const response = await fetch('/chats/' + currentUser);
                const chats = await response.json();
                const list = document.getElementById('chatsList');
                list.innerHTML = chats.map(chat => `
                    <div class="chat-item ${chat.username === currentChat ? 'active' : ''}" onclick="selectChat('${chat.username}')">
                        <div class="chat-avatar">${chat.username[0].toUpperCase()}</div>
                        <div class="chat-info">
                            <div class="chat-row">
                                <span class="chat-name">${chat.username}</span>
                                <span class="chat-time">${chat.last_time || ''}</span>
                            </div>
                            <div class="chat-last-msg">${chat.last_msg || 'Нет сообщений'}</div>
                        </div>
                    </div>
                `).join('');
            } catch(e) {
                console.error('Load chats error:', e);
            }
        }

        async function loadAllUsers() {
            try {
                const response = await fetch('/users');
                allUsers = await response.json();
            } catch(e) {
                console.error('Load users error:', e);
            }
        }

        function searchUsers() {
            const query = document.getElementById('userSearch').value.toLowerCase();
            const resultsDiv = document.getElementById('searchResults');
            if (!query || query.length < 2) {
                resultsDiv.style.display = 'none';
                return;
            }
            const filtered = allUsers.filter(u => 
                u.toLowerCase().includes(query) && u !== currentUser
            ).slice(0, 5);
            
            if (filtered.length === 0) {
                resultsDiv.style.display = 'none';
                return;
            }

            resultsDiv.innerHTML = filtered.map(u => 
                `<div class="search-result-item" onclick="selectChat('${u}')">${u}</div>`
            ).join('');
            resultsDiv.style.display = 'block';
        }

        function selectChat(username) {
            currentChat = username;
            document.getElementById('dialogName').innerText = username;
            document.getElementById('dialogAvatar').innerText = username[0].toUpperCase();
            document.getElementById('searchResults').style.display = 'none';
            document.getElementById('userSearch').value = '';
            loadMessages();
            loadChats();
        }

        function toggleEmojiPicker() {
            const picker = document.getElementById('emojiPicker');
            picker.style.display = picker.style.display === 'none' ? 'grid' : 'none';
        }

        function addEmoji(emoji) {
            const input = document.getElementById('messageInput');
            input.value += emoji;
            toggleEmojiPicker();
        }

        if (currentUser) {
            (async () => {
                const result = await apiCall('/login', {username: currentUser, password: ''});
                if (result && result.success) {
                    document.getElementById('loginScreen').style.display = 'none';
                    document.getElementById('dialogHeader').style.display = 'flex';
                    document.getElementById('inputArea').style.display = 'flex';
                    loadChats();
                    loadAllUsers();
                } else {
                    localStorage.removeItem('pahantalk_user');
                }
            })();
        }

        setInterval(() => {
            if (currentUser && currentChat) loadMessages();
            if (currentUser) loadChats();
        }, 3000);
    </script>
</body>
</html>"""

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
    if not data.get('password'):
        return jsonify({'success': False})
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
        return jsonify({'success': False, 'error': 'No file'})
    
    file = request.files['image']
    from_user = request.form.get('from')
    to_user = request.form.get('to')
    
    if not from_user or not to_user:
        return jsonify({'success': False, 'error': 'Missing user'})
    
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        image_url = '/uploads/' + filename
        
        conn = sqlite3.connect('pahantalk.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (from_user, to_user, image) VALUES (?, ?, ?)",
                  (from_user, to_user, image_url))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'url': image_url})
    
    return jsonify({'success': False, 'error': 'Invalid file'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

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
    for row in c.fetchall():
        msg = {'from': row[0], 'to': row[1], 'time': row[4]}
        if row[2]:
            msg['text'] = row[2]
        if row[3]:
            msg['image'] = row[3]
        msgs.append(msg)
    conn.close()
    return jsonify(msgs)

@app.route('/chats/<username>')
def get_chats(username):
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("""SELECT DISTINCT 
                    CASE WHEN from_user=? THEN to_user ELSE from_user END as chat_user,
                    (SELECT COALESCE(text, image) FROM messages WHERE (from_user=? AND to_user=chat_user) OR (from_user=chat_user AND to_user=?) ORDER BY timestamp DESC LIMIT 1) as last_msg,
                    (SELECT strftime('%H:%M', timestamp) FROM messages WHERE (from_user=? AND to_user=chat_user) OR (from_user=chat_user AND to_user=?) ORDER BY timestamp DESC LIMIT 1) as last_time
                 FROM messages 
                 WHERE from_user=? OR to_user=?""",
              (username, username, username, username, username, username, username))
    chats = [{'username': row[0], 'last_msg': row[1] if row[1] else '🖼️ Фото', 'last_time': row[2]} for row in c.fetchall() if row[0]]
    conn.close()
    return jsonify(chats)

@app.route('/users')
def get_users():
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify(users)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
