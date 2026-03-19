# server.py - ПАХАНТАЛК с профилями и аватарками
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
        c.execute("INSERT OR IGNORE INTO users (username, password, display_name, avatar, status) VALUES (?, ?, ?, ?, ?)",
                  ("2kenta", "123", "Кента", "/avatars/default.png", "в сети"))
        c.execute("INSERT OR IGNORE INTO users (username, password, display_name, avatar, status) VALUES (?, ?, ?, ?, ?)",
                  ("pahan", "123", "Пахан", "/avatars/default.png", "в сети"))
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
            position: relative;
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
            object-fit: cover;
        }

        .avatar:hover {
            border-color: #4e9bef;
            transform: scale(1.02);
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
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .search-result-item:hover {
            background: #3a3a3a;
        }

        .search-result-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #2a7ad0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 14px;
        }

        .search-result-avatar img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
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
                <input class="search-box" id="userSearch" type="text" placeholder="Поиск пользователей..." oninput="searchUsers()">
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
                            <span id="dialogDisplayName" style="color: #8e959f; font-size: 13px;"></span>
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

    <div id="profileModal" style="display: none;" class="profile-modal">
        <div class="profile-content">
            <h3 id="profileTitle">Профиль</h3>
            <div class="profile-avatar" id="profileAvatar" onclick="document.getElementById('avatar-input').click()">
                <img src="" style="display: none;" id="profileAvatarImg">
                <span id="profileAvatarText"></span>
            </div>
            <input type="text" id="profileUsername" class="profile-input" placeholder="Логин" readonly>
            <input type="text" id="profileDisplayName" class="profile-input" placeholder="Отображаемое имя">
            <input type="text" id="profileStatus" class="profile-input" placeholder="Статус">
            <textarea id="profileBio" class="profile-input" placeholder="О себе" rows="3"></textarea>
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
                loadMyProfile();
                loadChats();
                loadAllUsers();
            } else {
                alert('Неверный логин или пароль');
            }
        }

        async function loadMyProfile() {
            const response = await fetch('/user/' + currentUser);
            const user = await response.json();
            if (user.avatar) {
                document.getElementById('myAvatarImg').src = user.avatar;
                document.getElementById('myAvatarImg').style.display = 'block';
                document.getElementById('myAvatarText').style.display = 'none';
            } else {
                document.getElementById('myAvatarText').innerText = currentUser[0].toUpperCase();
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

        async function uploadAvatar() {
            const fileInput = document.getElementById('avatar-input');
            if (!fileInput.files.length || !currentProfileUser) return;
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('avatar', file);
            formData.append('username', currentProfileUser);

            try {
                const response = await fetch('/upload-avatar', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (result.success) {
                    if (currentProfileUser === currentUser) {
                        loadMyProfile();
                    }
                    if (currentProfileUser === currentChat) {
                        loadUserProfile(currentChat);
                    }
                    loadChats();
                    alert('Аватар обновлён');
                } else {
                    alert('Ошибка загрузки');
                }
            } catch(e) {
                console.error('Avatar upload error:', e);
                alert('Ошибка');
            }
            fileInput.value = '';
            closeProfile();
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
                
                for (let chat of chats) {
                    const userResponse = await fetch('/user/' + chat.username);
                    const user = await userResponse.json();
                    chat.displayName = user.display_name || chat.username;
                    chat.avatar = user.avatar;
                }
                
                list.innerHTML = chats.map(chat => `
                    <div class="chat-item ${chat.username === currentChat ? 'active' : ''}" onclick="selectChat('${chat.username}')">
                        <div class="chat-avatar">
                            ${chat.avatar ? `<img src="${chat.avatar}">` : chat.username[0].toUpperCase()}
                        </div>
                        <div class="chat-info">
                            <div class="chat-row">
                                <span class="chat-name">${chat.displayName}</span>
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

        async function searchUsers() {
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

            let html = '';
            for (let username of filtered) {
                const response = await fetch('/user/' + username);
                const user = await response.json();
                html += `<div class="search-result-item" onclick="selectChat('${username}')">
                    <div class="search-result-avatar">
                        ${user.avatar ? `<img src="${user.avatar}">` : username[0].toUpperCase()}
                    </div>
                    <div>
                        <div style="font-weight: 600;">${user.display_name || username}</div>
                        <div style="font-size: 12px; color: #8e959f;">@${username}</div>
                    </div>
                </div>`;
            }
            
            resultsDiv.innerHTML = html;
            resultsDiv.style.display = 'block';
        }

        function selectChat(username) {
            currentChat = username;
            document.getElementById('searchResults').style.display = 'none';
            document.getElementById('userSearch').value = '';
            loadUserProfile(username);
            loadMessages();
            loadChats();
        }

        async function loadUserProfile(username) {
            const response = await fetch('/user/' + username);
            const user = await response.json();
            document.getElementById('dialogName').innerText = user.display_name || username;
            document.getElementById('dialog
