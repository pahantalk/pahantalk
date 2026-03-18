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
    <style>
        body { background: #111; color: gold; font-family: Arial; padding:20px; max-width:600px; margin:0 auto; }
        .container { background: #222; padding:20px; border-radius:10px; border:2px solid gold; }
        input, button { padding:10px; margin:5px; background:#333; border:1px solid gold; color:gold; width:100%; }
        button { background:gold; color:black; font-weight:bold; cursor:pointer; }
        #messages { background:#1a1a1a; padding:10px; border-radius:5px; height:300px; overflow-y:auto; }
        .msg { border-bottom:1px solid #333; padding:5px; }
    </style>
</head>
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