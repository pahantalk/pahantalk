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

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ПАХАНТАЛК — Профили</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
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
            max-width: 800px;
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
        .flex {
            display: flex;
            gap: 20px;
        }
        .sidebar {
            width: 200px;
            background: #1a1a1a;
            border-radius: 12px;
            padding: 15px;
        }
        .main {
            flex: 1;
        }
        .profile-card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
            cursor: pointer;
            border: 1px solid #3a3a3a;
        }
        .profile-card:hover {
            border-color: gold;
        }
        .avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: gold;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            color: black;
            margin-bottom: 10px;
            overflow: hidden;
        }
        .avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
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
        .search-result {
            padding: 8px;
            cursor: pointer;
            border-bottom: 1px solid #3a3a3a;
        }
        .search-result:hover {
            background: #2a2a2a;
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
            background: #2a2a2a;
            padding: 30px;
            border-radius: 16px;
            max-width: 400px;
            width: 90%;
        }
        .emoji-picker {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 5px;
            padding: 10px;
            background: #1a1a1a;
            border-radius: 8px;
            margin-top: 5px;
        }
        .emoji-picker span {
            font-size: 24px;
            text-align: center;
            cursor: pointer;
            padding: 5px;
        }
        .emoji-picker span:hover {
            background: #3a3a3a;
            border-radius: 4px;
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
            <div class="flex">
                <div class="sidebar">
                    <div class="profile-card" onclick="openMyProfile()">
                        <div class="avatar" id="myAvatar"></div>
                        <div><strong id="myName">Загрузка...</strong></div>
                        <div style="font-size: 12px; color: gold;" id="myStatus"></div>
                    </div>
                    <h3>Чаты</h3>
                    <div id="chatsList"></div>
                    <h3>Поиск</h3>
                    <input type="text" id="searchInput" placeholder="Найти пользователя..." oninput="searchUsers()">
                    <div id="searchResults"></div>
                </div>
                <div class="main">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 id="chatWith">Выберите чат</h2>
                        <button onclick="logout()" style="width: auto;">Выйти</button>
                    </div>
                    <div id="messages"></div>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="messageInput" placeholder="Сообщение..." style="flex: 1;">
                        <button onclick="toggleEmoji()" style="width: auto;">😊</button>
                        <button onclick="sendMessage()" style="width: auto;">➤</button>
                    </div>
                    <div id="emojiPicker" class="emoji-picker hidden">
                        <span onclick="addEmoji('😊')">😊</span>
                        <span onclick="addEmoji('😂')">😂</span>
                        <span onclick="addEmoji('❤️')">❤️</span>
                        <span onclick="addEmoji('🔥')">🔥</span>
                        <span onclick="addEmoji('👍')">👍</span>
                        <span onclick="addEmoji('😢')">😢</span>
                        <span onclick="addEmoji('🎉')">🎉</span>
                        <span onclick="addEmoji('💀')">💀</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="profileModal" class="modal hidden">
        <div class="modal-content">
            <h2 id="modalTitle">Профиль</h2>
            <div class="avatar" id="modalAvatar" onclick="document.getElementById('avatarInput').click()"></div>
            <input type="text" id="modalDisplayName" placeholder="Отображаемое имя">
            <input type="text" id="modalStatus" placeholder="Статус">
            <textarea id="modalBio" placeholder="О себе"></textarea>
            <button onclick="saveProfile()">Сохранить</button>
            <button onclick="closeModal()">Закрыть</button>
            <input type="file" id="avatarInput" accept="image/*" style="display: none;" onchange="uploadAvatar()">
        </div>
    </div>

    <script>
        let currentUser = null;
        let currentChat = null;
        let allUsers = [];

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
                loadProfile();
                loadChats();
                loadAllUsers();
            } else {
                alert('Неверный логин/пароль');
            }
        }

        function logout() {
            currentUser = null;
            currentChat = null;
            document.getElementById('loginScreen').classList.remove('hidden');
            document.getElementById('chatScreen').classList.add('hidden');
        }

       async function loadProfile() {
    if (!currentUser) return;
    try {
        const res = await fetch('/user/' + currentUser);
        if (!res.ok) {
            console.error('Ошибка сервера');
            return;
        }
        const user = await res.json();
        if (user && user.username) {
            document.getElementById('myName').innerText = user.display_name || currentUser;
            document.getElementById('myStatus').innerText = user.status || '';
            const avatar = document.getElementById('myAvatar');
            if (user.avatar) {
                avatar.innerHTML = `<img src="${user.avatar}">`;
            } else {
                avatar.innerText = (currentUser[0] || '').toUpperCase();
            }
        } else {
            // Если профиля нет — создаём заглушку
            document.getElementById('myName').innerText = currentUser;
            document.getElementById('myStatus').innerText = '';
            document.getElementById('myAvatar').innerText = (currentUser[0] || '').toUpperCase();
        }
    } catch (e) {
        console.error('Ошибка загрузки профиля:', e);
    }
} 

        async function loadChats() {
            const res = await fetch('/chats/' + currentUser);
            const chats = await res.json();
            const list = document.getElementById('chatsList');
            list.innerHTML = '';
            for (let chat of chats) {
                const u = await (await fetch('/user/' + chat.username)).json();
                list.innerHTML += `
                    <div class="profile-card" onclick="selectChat('${chat.username}')">
                        <div class="avatar">${u.avatar ? `<img src="${u.avatar}">` : chat.username[0]}</div>
                        <div><strong>${u.display_name || chat.username}</strong></div>
                        <div style="font-size: 12px;">${chat.last_msg || ''}</div>
                    </div>
                `;
            }
        }

        async function loadAllUsers() {
            const res = await fetch('/users');
            allUsers = await res.json();
        }

        function searchUsers() {
            const q = document.getElementById('searchInput').value.toLowerCase();
            const res = document.getElementById('searchResults');
            if (q.length < 2) {
                res.innerHTML = '';
                return;
            }
            const filtered = allUsers.filter(u => u.includes(q) && u !== currentUser).slice(0,5);
            res.innerHTML = filtered.map(u => 
                `<div class="search-result" onclick="selectChat('${u}')">@${u}</div>`
            ).join('');
        }

        function selectChat(u) {
            currentChat = u;
            document.getElementById('chatWith').innerText = 'Чат с @' + u;
            loadMessages();
        }

        async function sendMessage() {
            if (!currentChat) return;
            const text = document.getElementById('messageInput').value;
            if (!text) return;
            await apiCall('/send', {from: currentUser, to: currentChat, text});
            document.getElementById('messageInput').value = '';
            loadMessages();
        }

        async function loadMessages() {
            if (!currentChat) return;
            const res = await fetch('/messages/' + currentUser + '?with=' + currentChat);
            const msgs = await res.json();
            const container = document.getElementById('messages');
            container.innerHTML = msgs.reverse().map(m => 
                `<div class="message ${m.from === currentUser ? 'my-message' : 'other-message'}">
                    <b>${m.from}:</b> ${m.text}
                    <small>${m.time || ''}</small>
                </div>`
            ).join('');
        }

        function toggleEmoji() {
            document.getElementById('emojiPicker').classList.toggle('hidden');
        }

        function addEmoji(e) {
            document.getElementById('messageInput').value += e;
            toggleEmoji();
        }

        function openMyProfile() {
            openProfile(currentUser);
        }

        async function openProfile(username) {
            const res = await fetch('/user/' + username);
            const user = await res.json();
            document.getElementById('modalTitle').innerText = 'Профиль @' + username;
            document.getElementById('modalDisplayName').value = user.display_name || '';
            document.getElementById('modalStatus').value = user.status || '';
            document.getElementById('modalBio').value = user.bio || '';
            const avatar = document.getElementById('modalAvatar');
            avatar.innerHTML = user.avatar ? `<img src="${user.avatar}">` : (username[0] || '').toUpperCase();
            document.getElementById('profileModal').classList.remove('hidden');
        }

        function closeModal() {
            document.getElementById('profileModal').classList.add('hidden');
        }

        async function saveProfile() {
            const data = {
                display_name: document.getElementById('modalDisplayName').value,
                status: document.getElementById('modalStatus').value,
                bio: document.getElementById('modalBio').value
            };
            await apiCall('/update_profile/' + currentUser, data);
            loadProfile();
            closeModal();
        }

        async function uploadAvatar() {
            const input = document.getElementById('avatarInput');
            if (!input.files.length) return;
            const fd = new FormData();
            fd.append('avatar', input.files[0]);
            fd.append('username', currentUser);
            await fetch('/upload-avatar', {method: 'POST', body: fd});
            loadProfile();
            closeModal();
        }

        setInterval(() => { if (currentChat) loadMessages(); }, 3000);
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
        c2.execute("""SELECT text FROM messages 
                      WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?)
                      ORDER BY timestamp DESC LIMIT 1""",
                   (username, chat_user, chat_user, username))
        last = c2.fetchone()
        chats.append({'username': chat_user, 'last_msg': last[0] if last else ''})
    conn.close()
    return jsonify(chats)

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

@app.route('/update_profile/<username>', methods=['POST'])
def update_profile(username):
    data = request.json
    conn = sqlite3.connect('pahantalk.db')
    c = conn.cursor()
    c.execute("UPDATE users SET display_name=?, status=?, bio=? WHERE username=?",
              (data['display_name'], data['status'], data['bio'], username))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

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

@app.route('/avatars/<filename>')
def avatar_file(filename):
    return send_file(os.path.join(AVATAR_FOLDER, filename))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
