from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

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
                  text TEXT NOT NULL,
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
        body {
            font-family: Arial, sans-serif;
            background: #0e1621;
            color: white;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #17212b;
            border-radius: 12px;
            padding: 20px;
        }
        h1 { color: #2b7ad0; text-align: center; margin-bottom: 20px; }
        .row { display: flex; gap: 20px; }
        .col {
            flex: 1;
            background: #1e2a36;
            padding: 15px;
            border-radius: 8px;
        }
        input, button {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: none;
            border-radius: 5px;
        }
        button {
            background: #2b7ad0;
            color: white;
            cursor: pointer;
        }
        .chat-item {
            padding: 10px;
            border-bottom: 1px solid #253441;
            cursor: pointer;
        }
        .chat-item:hover { background: #253441; }
        .message {
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 12px;
            max-width: 70%;
        }
        .my-message {
            background: #2b5278;
            margin-left: auto;
        }
        .other-message {
            background: #1e2a36;
        }
        #messages {
            height: 400px;
            overflow-y: auto;
            padding: 10px;
            background: #17212b;
            border-radius: 8px;
        }
        .hidden { display: none; }
        .search-result {
            padding: 8px;
            cursor: pointer;
            border-bottom: 1px solid #253441;
        }
        .search-result:hover { background: #253441; }
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
            <div class="row">
                <div class="col" style="max-width: 300px;">
                    <h3>Чаты</h3>
                    <input type="text" id="searchInput" placeholder="Поиск пользователей..." oninput="searchUsers()">
                    <div id="searchResults"></div>
                    <div id="chatsList"></div>
                </div>
                <div class="col">
                    <div style="display: flex; justify-content: space-between;">
                        <h3 id="currentChat">Выберите чат</h3>
                        <button onclick="logout()">Выйти</button>
                    </div>
                    <div id="messages"></div>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="messageInput" placeholder="Сообщение" style="flex: 1;">
                        <button onclick="sendMessage()" style="width: auto;">➤</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        let currentUser = localStorage.getItem('pahantalk_user');
        let currentChat = null;
        let allUsers = [];

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
                currentUser = u;
                localStorage.setItem('pahantalk_user', u);
                document.getElementById('loginScreen').classList.add('hidden');
                document.getElementById('chatScreen').classList.remove('hidden');
                loadChats();
                loadAllUsers();
            } else alert('Неверный логин/пароль');
        }

        function logout() {
            currentUser = null;
            localStorage.removeItem('pahantalk_user');
            location.reload();
        }

        async function loadChats() {
            const res = await fetch('/chats/' + currentUser);
            const chats = await res.json();
            const list = document.getElementById('chatsList');
            list.innerHTML = '<h4>Ваши чаты:</h4>';
            for(let chat of chats) {
                list.innerHTML += `<div class="chat-item" onclick="selectChat('${chat.username}')">
                    <b>${chat.username}</b><br>
                    <small>${chat.last_msg || ''}</small>
                </div>`;
            }
        }

        async function loadAllUsers() {
            const res = await fetch('/users');
            allUsers = await res.json();
        }

        function searchUsers() {
            const q = document.getElementById('searchInput').value.toLowerCase();
            const results = document.getElementById('searchResults');
            if(q.length < 2) { results.innerHTML = ''; return; }
            const filtered = allUsers.filter(u => u.includes(q) && u !== currentUser).slice(0,5);
            results.innerHTML = filtered.map(u => 
                `<div class="search-result" onclick="selectChat('${u}')">@${u}</div>`
            ).join('');
        }

        async function selectChat(username) {
            currentChat = username;
            document.getElementById('currentChat').innerText = 'Чат с @' + username;
            document.getElementById('searchResults').innerHTML = '';
            document.getElementById('searchInput').value = '';
            loadMessages();
        }

        async function sendMessage() {
            if(!currentChat) return;
            const input = document.getElementById('messageInput');
            const text = input.value;
            if(!text) return;
            await apiCall('/send', {from:currentUser, to:currentChat, text});
            input.value = '';
            loadMessages();
            loadChats();
        }

        async function loadMessages() {
            if(!currentChat) return;
            const res = await fetch('/messages/' + currentUser + '?with=' + currentChat);
            const msgs = await res.json();
            const area = document.getElementById('messages');
            area.innerHTML = msgs.reverse().map(m => {
                const own = m.from === currentUser;
                return `<div class="message ${own ? 'my-message' : 'other-message'}">
                    <b>${m.from}</b> ${m.text}<br>
                    <small>${m.time || ''}</small>
                </div>`;
            }).join('');
            area.scrollTop = area.scrollHeight;
        }

        if(currentUser) {
            document.getElementById('loginScreen').classList.add('hidden');
            document.getElementById('chatScreen').classList.remove('hidden');
            loadChats();
            loadAllUsers();
        }

        setInterval(() => { if(currentChat) loadMessages(); }, 3000);
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
        c2.execute("""SELECT text FROM messages 
                      WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?)
                      ORDER BY timestamp DESC LIMIT 1""",
                   (username, chat_user, chat_user, username))
        last = c2.fetchone()
        chats.append({'username': chat_user, 'last_msg': last[0] if last else ''})
    conn.close()
    return jsonify(chats)

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
