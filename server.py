# server.py - ПАХАНТАЛК для Render
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

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
                  text TEXT NOT NULL,
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

# HTML интерфейс
HTML = """<!DOCTYPE html>
<html>
<head>
    <title>ПАХАНТАЛК</title>
    <meta charset="utf-8">
</head> <style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background: #e7ebf0;
        min-height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 12px;
    }
    
    .container {
        width: 100%;
        max-width: 450px;
        background: white;
        border-radius: 24px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
    
    h1 {
        font-size: 24px;
        font-weight: 600;
        text-align: center;
        padding: 20px 16px 12px;
        color: #222;
        border-bottom: 1px solid #e9ecef;
        margin: 0;
    }
    
    .login-section, .chat-section {
        padding: 16px;
    }
    
    .input-group {
        margin-bottom: 12px;
    }
    
    input, button {
        width: 100%;
        padding: 14px 16px;
        border: none;
        border-radius: 14px;
        font-size: 16px;
        outline: none;
        transition: all 0.2s;
    }
    
    input {
        background: #f4f6f9;
        border: 1px solid #e9ecef;
    }
    
    input:focus {
        border-color: #3390ec;
        background: white;
    }
    
    button {
        background: #3390ec;
        color: white;
        font-weight: 500;
        cursor: pointer;
        margin-top: 8px;
    }
    
    button:hover {
        background: #2a7ad0;
    }
    
    button.secondary {
        background: #f4f6f9;
        color: #222;
        border: 1px solid #e9ecef;
    }
    
    button.secondary:hover {
        background: #e9ecef;
    }
    
    .chat-header {
        background: white;
        padding: 12px 16px;
        border-bottom: 1px solid #e9ecef;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .user-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #3390ec;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 18px;
    }
    
    .username {
        font-weight: 600;
        color: #222;
    }
    
    .logout-btn {
        background: #f4f6f9;
        color: #222;
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 14px;
        border: 1px solid #e9ecef;
        width: auto;
    }
    
    .logout-btn:hover {
        background: #e9ecef;
    }
    
    .compose-area {
        padding: 12px 16px;
        background: white;
        border-top: 1px solid #e9ecef;
    }
    
    .to-input {
        width: 100%;
        padding: 10px 12px;
        background: #f4f6f9;
        border-radius: 20px;
        border: 1px solid #e9ecef;
        margin-bottom: 8px;
        font-size: 14px;
    }
    
    .message-input-row {
        display: flex;
        gap: 10px;
        align-items: center;
        background: #f4f6f9;
        border-radius: 25px;
        padding: 4px;
        border: 1px solid #e9ecef;
    }
    
    .message-input-row input {
        flex: 1;
        background: transparent;
        border: none;
        padding: 10px 12px;
    }
    
    .message-input-row button {
        width: auto;
        padding: 10px 20px;
        border-radius: 25px;
        margin: 0;
        background: #3390ec;
    }
    
    .messages-area {
        height: 450px;
        overflow-y: auto;
        padding: 16px;
        background: #e7ebf0;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .message {
        max-width: 80%;
        padding: 10px 14px;
        border-radius: 18px;
        word-wrap: break-word;
        animation: messagePop 0.2s ease;
        position: relative;
        font-size: 15px;
        line-height: 1.4;
    }
    
    @keyframes messagePop {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    .message.own {
        background: #3390ec;
        color: white;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
    }
    
    .message.other {
        background: white;
        color: #222;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .message strong {
        display: block;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 4px;
        color: inherit;
        opacity: 0.9;
    }
    
    .message small {
        display: block;
        font-size: 11px;
        margin-top: 4px;
        opacity: 0.7;
        text-align: right;
    }
    
    .message.own small {
        color: rgba(255,255,255,0.8);
    }
    
    .message.other small {
        color: #8e959f;
    }
    
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 12px 16px;
        background: white;
        border-radius: 18px;
        width: fit-content;
        margin: 8px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .typing-indicator span {
        width: 8px;
        height: 8px;
        background: #8e959f;
        border-radius: 50%;
        animation: typing 1.4s infinite;
    }
    
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
        30% { transform: translateY(-8px); opacity: 1; }
    }
    
    /* Скроллбар как в Telegram */
    ::-webkit-scrollbar {
        width: 5px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #b8c0c9;
        border-radius: 10px;
    }
    
    /* Дата-разделитель */
    .date-divider {
        text-align: center;
        margin: 16px 0 8px;
        font-size: 12px;
        color: #8e959f;
        position: relative;
    }
    
    .date-divider span {
        background: #e7ebf0;
        padding: 0 12px;
    }
    
    .date-divider::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #d4d9e0;
        z-index: 0;
    }
    
    /* Аватарка в сообщении (для чужих) */
    .message-row {
        display: flex;
        gap: 8px;
        margin: 4px 0;
    }
    
    .message-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #3390ec;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 16px;
        flex-shrink: 0;
    }
    
    @media (max-width: 450px) {
        .container {
            border-radius: 18px;
        }
        
        .message {
            max-width: 85%;
        }
        
        .messages-area {
            height: 400px;
        }
    }
</style>
<body>
    <div class="container">
        <h1>💬 ПАХАНТАЛК</h1>
        
        <div id="loginSection">
            <input id="loginUser" placeholder="Логин" value="2kenta">
            <input id="loginPass" type="password" placeholder="Пароль" value="123">
            <button onclick="login()">Войти</button>
            <button onclick="register()">Регистрация</button>
        </div>
        
        <div id="appSection" style="display:none;">
            <div style="display:flex; justify-content:space-between;">
                <span id="userDisplay"></span>
                <button onclick="logout()" style="width:auto;">Выйти</button>
            </div>
            <input id="toUser" placeholder="Кому" value="pahan">
            <div style="display:flex;">
                <input id="messageText" placeholder="Сообщение" style="flex:1;">
                <button onclick="sendMessage()" style="width:auto;">➡️</button>
            </div>
            <div id="messages"></div>
        </div>
    </div>
    
    <script>
        let currentUser = null;
        
        async function apiCall(url, data) {
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                return await res.json();
            } catch(e) {
                alert('Ошибка: ' + e);
                return null;
            }
        }
        
        async function register() {
            const username = document.getElementById('loginUser').value;
            const password = document.getElementById('loginPass').value;
            const result = await apiCall('/register', {username, password});
            alert(result?.success ? 'Рега успешна!' : 'Ошибка');
        }
        
        async function login() {
            const username = document.getElementById('loginUser').value;
            const password = document.getElementById('loginPass').value;
            const result = await apiCall('/login', {username, password});
            if (result?.success) {
                currentUser = username;
                document.getElementById('loginSection').style.display = 'none';
                document.getElementById('appSection').style.display = 'block';
                document.getElementById('userDisplay').innerText = username;
                loadMessages();
            } else {
                alert('Неверный логин/пароль');
            }
        }
        
        function logout() {
            currentUser = null;
            document.getElementById('loginSection').style.display = 'block';
            document.getElementById('appSection').style.display = 'none';
        }
        
        async function sendMessage() {
            if (!currentUser) return;
            const to = document.getElementById('toUser').value;
            const text = document.getElementById('messageText').value;
            if (!text.trim()) return;
            
            await apiCall('/send', {from: currentUser, to, text});
            document.getElementById('messageText').value = '';
            loadMessages();
        }
        
        async function loadMessages() {
            if (!currentUser) return;
            const res = await fetch('/messages/' + currentUser);
            const messages = await res.json();
            const html = messages.reverse().map(m => 
                `<div class="msg"><b>${m.from}</b> → ${m.to}: ${m.text}</div>`
            ).join('');
            document.getElementById('messages').innerHTML = html;
        }
        
        setInterval(() => { if (currentUser) loadMessages(); }, 3000);
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
    c.execute("""SELECT from_user, to_user, text, timestamp 
                 FROM messages 
                 WHERE from_user=? OR to_user=? OR to_user='all'
                 ORDER BY timestamp DESC LIMIT 50""",
              (username, username))
    msgs = [{'from': row[0], 'to': row[1], 'text': row[2], 'time': str(row[3])} for row in c.fetchall()]
    conn.close()
    return jsonify(msgs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
