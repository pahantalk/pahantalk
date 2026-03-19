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

        /* Основной контейнер — три колонки */
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

        /* ========== Левая панель (узкая) ========== */
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

        /* ========== Центральная колонка (список чатов) ========== */
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

        .search-box::placeholder {
            color: #6b6f77;
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

        /* ========== Правая колонка (открытый диалог) ========== */
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

        /* Сообщения */
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

        /* Поле ввода */
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

        /* Скроллбары */
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

        ::-webkit-scrollbar-thumb:hover {
            background: #4a4a4a;
        }

        /* Адаптация под мобилки */
        @media (max-width: 900px) {
            .left-panel { width: 60px; }
            .chats-panel { width: 280px; }
        }

        @media (max-width: 700px) {
            .chats-panel { display: none; }
            .left-panel { width: 60px; }
        }
    </style>
</head>
<body>
    <div class="tg-container">
        <!-- Левая панель -->
        <div class="left-panel">
            <div class="avatar">2K</div>
            <div class="nav-icon active">💬</div>
            <div class="nav-icon">👥</div>
            <div class="nav-icon">📞</div>
            <div class="nav-icon">⚙️</div>
        </div>

        <!-- Центр: список чатов -->
        <div class="chats-panel">
            <div class="chats-header">
                <h2>Чаты</h2>
                <input class="search-box" type="text" placeholder="Поиск">
            </div>
            <div class="chats-list">
                <div class="chat-item active">
                    <div class="chat-avatar">П</div>
                    <div class="chat-info">
                        <div class="chat-row">
                            <span class="chat-name">Пахан</span>
                            <span class="chat-time">12:45</span>
                        </div>
                        <div class="chat-last-msg">Привет, бро 🔥</div>
                    </div>
                </div>
                <div class="chat-item">
                    <div class="chat-avatar">А</div>
                    <div class="chat-info">
                        <div class="chat-row">
                            <span class="chat-name">Артур</span>
                            <span class="chat-time">11:20</span>
                        </div>
                        <div class="chat-last-msg">Го завтра встретимся?</div>
                    </div>
                </div>
                <div class="chat-item">
                    <div class="chat-avatar">С</div>
                    <div class="chat-info">
                        <div class="chat-row">
                            <span class="chat-name">Саня</span>
                            <span class="chat-time">10:05</span>
                        </div>
                        <div class="chat-last-msg">Код залил, глянь</div>
                    </div>
                </div>
                <div class="chat-item">
                    <div class="chat-avatar">Т</div>
                    <div class="chat-info">
                        <div class="chat-row">
                            <span class="chat-name">Тимур</span>
                            <span class="chat-time">09:30</span>
                        </div>
                        <div class="chat-last-msg">Там че по серверу?</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Правая колонка: открытый диалог -->
        <div class="dialog-panel">
            <!-- Шапка диалога -->
            <div class="dialog-header">
                <div class="dialog-header-left">
                    <div class="dialog-avatar">П</div>
                    <div class="dialog-info">
                        <div class="dialog-name">Пахан</div>
                        <div class="dialog-status">в сети</div>
                    </div>
                </div>
                <div class="dialog-header-icons">
                    <span>🔍</span>
                    <span>⋮</span>
                </div>
            </div>

            <!-- Сообщения -->
            <div class="messages-area">
                <div class="message other">
                    <strong>Пахан</strong>
                    Привет, бро! Как дела?
                    <small>12:30</small>
                </div>
                <div class="message own">
                    Здарова, норм! А ты?
                    <span class="status"></span>
                    <small>12:32</small>
                </div>
                <div class="message other">
                    Тоже норм, че делаешь?
                    <small>12:33</small>
                </div>
                <div class="message own">
                    Да код пилю, ПАХАНТАЛК делаю
                    <span class="status"></span>
                    <small>12:34</small>
                </div>
                <div class="message other">
                    Красавчик, скинь потом ссылку
                    <small>12:35</small>
                </div>
                <div class="message own">
                    Обижаешь, брат. Ща скину
                    <span class="status"></span>
                    <small>12:36</small>
                </div>
            </div>

            <!-- Поле ввода -->
            <div class="input-area">
                <span class="attach-icon">📎</span>
                <span class="emoji-icon">😊</span>
                <input type="text" placeholder="Написать сообщение...">
                <button class="send-btn">➤</button>
            </div>
        </div>
    </div>
</body>
</html>
"""               (data['username'], data['password']))
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
