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
                  bio TEXT DEFAULT '',
                  last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  from_user TEXT NOT NULL,
                  to_user TEXT NOT NULL,
                  text TEXT,
                  image TEXT,
                  file TEXT,
                  file_name TEXT,
                  file_size INTEGER,
                  voice TEXT,
                  reply_to INTEGER DEFAULT 0,
                  forwarded_from TEXT,
                  reactions TEXT DEFAULT '',
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user1 TEXT NOT NULL,
                  user2 TEXT NOT NULL,
                  last_message TEXT,
                  last_time TIMESTAMP,
                  is_pinned BOOLEAN DEFAULT 0,
                  is_archived BOOLEAN DEFAULT 0,
                  UNIQUE(user1, user2))''')
    try:
        c.execute("INSERT OR IGNORE INTO users (username, password, display_name) VALUES (?, ?, ?)",
                  ("2kenta", "123", "Кента"))
        c.execute("INSERT OR IGNORE INTO users (username, password, display_name) VALUES (?, ?, ?)",
                  ("pahan", "123", "Пахан"))
        c.execute("INSERT OR IGNORE INTO users (username, password, display_name) VALUES (?, ?, ?)",
                  ("artur", "123", "Артур"))
        c.execute("INSERT OR IGNORE INTO users (username, password, display_name) VALUES (?, ?, ?)",
                  ("sanya", "123", "Саня"))
    except:
        pass
    conn.commit()
    conn.close()

init_db()

HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ПАХАНТАЛК — Telegram Web</title>
    <style>
        /* ===== СБРОС И ГЛОБАЛЬНЫЕ ===== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        body {
            background: #e6ebf0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }

        .tg-container {
            display: flex;
            width: 1440px;
            max-width: 100%;
            height: 95vh;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }

        /* ===== ЛЕВАЯ ПАНЕЛЬ (64px) ===== */
        .left-panel {
            width: 64px;
            background: #ffffff;
            border-right: 1px solid #f0f0f0;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 16px 0;
        }

        .avatar-wrapper {
            position: relative;
            margin-bottom: 24px;
        }

        .avatar-32 {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #2aabee;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            overflow: hidden;
        }

        .avatar-32 img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .online-dot {
            position: absolute;
            bottom: 2px;
            right: 2px;
            width: 8px;
            height: 8px;
            background: #2ecc71;
            border: 2px solid white;
            border-radius: 50%;
        }

        .nav-icon {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6d7a8d;
            font-size: 20px;
            margin: 4px 0;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }

        .nav-icon:hover {
            background: #f0f0f0;
            color: #2aabee;
        }

        .nav-icon.active {
            background: #e8f4ff;
            color: #2aabee;
        }

        .nav-icon[data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            left: 48px;
            background: #1f2a3a;
            color: white;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .spacer {
            flex: 1;
        }

        .bottom-icon {
            margin-top: auto;
        }

        /* ===== ЦЕНТРАЛЬНАЯ ПАНЕЛЬ (320px) ===== */
        .chats-panel {
            width: 320px;
            background: #ffffff;
            border-right: 1px solid #f0f0f0;
            display: flex;
            flex-direction: column;
        }

        .search-section {
            padding: 12px 16px;
            border-bottom: 1px solid #f0f0f0;
        }

        .search-wrapper {
            position: relative;
        }

        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #8e9aab;
            font-size: 16px;
        }

        .search-input {
            width: 100%;
            padding: 10px 12px 10px 40px;
            border: none;
            background: #f4f6f9;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
            transition: 0.2s;
        }

        .search-input:focus {
            background: #ffffff;
            box-shadow: 0 0 0 2px rgba(42, 171, 238, 0.1);
        }

        .filters {
            display: flex;
            gap: 8px;
            padding: 12px 16px;
            border-bottom: 1px solid #f0f0f0;
            overflow-x: auto;
            scrollbar-width: none;
        }

        .filter-chip {
            padding: 6px 16px;
            background: #f4f6f9;
            border-radius: 20px;
            font-size: 13px;
            color: #1f2a3a;
            cursor: pointer;
            white-space: nowrap;
            transition: 0.2s;
        }

        .filter-chip:hover {
            background: #e8f4ff;
        }

        .filter-chip.active {
            background: #2aabee;
            color: white;
        }

        .chats-list {
            flex: 1;
            overflow-y: auto;
        }

        .archive-header {
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #6d7a8d;
            font-size: 13px;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
        }

        .archive-header:hover {
            background: #f4f6f9;
        }

        .archive-count {
            margin-left: auto;
            background: #f0f0f0;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
        }

        .chat-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            position: relative;
            transition: 0.2s;
            border-left: 3px solid transparent;
        }

        .chat-item:hover {
            background: #f4f6f9;
        }

        .chat-item:hover .chat-actions {
            display: flex;
        }

        .chat-item.active {
            background: #e8f4ff;
            border-left-color: #2aabee;
        }

        .chat-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: #2aabee;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 18px;
            margin-right: 12px;
            overflow: hidden;
            flex-shrink: 0;
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
            align-items: center;
            margin-bottom: 4px;
        }

        .chat-name {
            font-weight: 600;
            font-size: 15px;
            color: #1f2a3a;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .chat-time {
            font-size: 11px;
            color: #8e9aab;
        }

        .chat-last-msg {
            font-size: 13px;
            color: #8e9aab;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .chat-badge {
            min-width: 20px;
            height: 20px;
            background: #2aabee;
            color: white;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 600;
            padding: 0 6px;
            margin-left: 8px;
        }

        .chat-pinned {
            color: #8e9aab;
            font-size: 12px;
            margin-left: 8px;
        }

        .chat-actions {
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            display: none;
            gap: 4px;
            background: white;
            padding: 4px;
            border-radius: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .chat-action {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6d7a8d;
            font-size: 14px;
            cursor: pointer;
        }

        .chat-action:hover {
            background: #f0f0f0;
        }

        /* ===== ПРАВАЯ ПАНЕЛЬ (ОТКРЫТЫЙ ЧАТ) ===== */
        .dialog-panel {
            flex: 1;
            background: #ffffff;
            display: flex;
            flex-direction: column;
        }

        .dialog-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
            border-bottom: 1px solid #f0f0f0;
            background: #ffffff;
        }

        .dialog-info {
            display: flex;
            align-items: center;
            cursor: pointer;
        }

        .dialog-avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: #2aabee;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 18px;
            margin-right: 14px;
            overflow: hidden;
        }

        .dialog-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .dialog-name-block {
            line-height: 1.3;
        }

        .dialog-name {
            font-weight: 600;
            font-size: 16px;
            color: #1f2a3a;
        }

        .dialog-status {
            font-size: 13px;
            color: #8e9aab;
        }

        .dialog-header-icons {
            display: flex;
            gap: 16px;
        }

        .header-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6d7a8d;
            font-size: 20px;
            cursor: pointer;
            transition: 0.2s;
        }

        .header-icon:hover {
            background: #f0f0f0;
        }

        .messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: #f9f9f9;
        }

        .date-divider {
            text-align: center;
            margin: 16px 0 8px;
            font-size: 12px;
            color: #8e9aab;
            position: relative;
        }

        .date-divider span {
            background: #f9f9f9;
            padding: 0 12px;
            z-index: 1;
            position: relative;
        }

        .date-divider::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: #f0f0f0;
            z-index: 0;
        }

        .message-wrapper {
            display: flex;
            flex-direction: column;
            max-width: 70%;
        }

        .message-wrapper.own {
            align-self: flex-end;
        }

        .message {
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
            background: #2aabee;
            color: white;
            border-bottom-right-radius: 6px;
        }

        .message.other {
            background: #ffffff;
            color: #1f2a3a;
            border: 1px solid #f0f0f0;
            border-bottom-left-radius: 6px;
        }

        .message.forwarded {
            margin-top: 4px;
            padding-top: 8px;
            border-top: 1px dashed rgba(0,0,0,0.1);
        }

        .forward-label {
            font-size: 12px;
            color: #8e9aab;
            margin-bottom: 4px;
        }

        .reply-block {
            background: rgba(0,0,0,0.05);
            padding: 8px 12px;
            border-radius: 12px;
            margin-bottom: 4px;
            font-size: 13px;
            border-left: 3px solid #2aabee;
        }

        .message-image {
            max-width: 300px;
            border-radius: 12px;
            margin-top: 5px;
            cursor: pointer;
        }

        .message-file {
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(0,0,0,0.03);
            padding: 10px;
            border-radius: 12px;
            margin-top: 5px;
        }

        .file-icon {
            font-size: 24px;
        }

        .file-info {
            flex: 1;
        }

        .file-name {
            font-weight: 600;
            font-size: 13px;
        }

        .file-size {
            font-size: 11px;
            color: #8e9aab;
        }

        .file-progress {
            height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            margin-top: 4px;
            width: 100%;
        }

        .file-progress-fill {
            height: 100%;
            background: #2aabee;
            border-radius: 2px;
            width: 45%;
        }

        .voice-message {
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 200px;
        }

        .voice-play {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #2aabee;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }

        .voice-wave {
            flex: 1;
            height: 30px;
            background: linear-gradient(90deg, #2aabee 20%, #e0e0e0 20%);
            border-radius: 15px;
        }

        .voice-duration {
            font-size: 12px;
            color: #8e9aab;
        }

        .message-footer {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 4px;
            margin-top: 4px;
            font-size: 11px;
            color: #8e9aab;
        }

        .message-status {
            font-size: 12px;
        }

        .reactions {
            display: flex;
            gap: 4px;
            margin-top: 4px;
        }

        .reaction {
            background: rgba(0,0,0,0.05);
            border-radius: 20px;
            padding: 2px 8px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
        }

        .reaction:hover {
            background: rgba(0,0,0,0.1);
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
            background: #ffffff;
            border: 1px solid #f0f0f0;
            border-radius: 20px;
            width: fit-content;
            margin: 8px 0;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: #8e9aab;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-8px); opacity: 1; }
        }

        .input-area {
            padding: 12px 20px;
            background: #ffffff;
            border-top: 1px solid #f0f0f0;
            display: flex;
            align-items: flex-end;
            gap: 12px;
        }

        .input-tools {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .tool-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6d7a8d;
            font-size: 20px;
            cursor: pointer;
        }

        .tool-icon:hover {
            background: #f0f0f0;
        }

        .message-input-wrapper {
            flex: 1;
            background: #f4f6f9;
            border-radius: 24px;
            padding: 8px 16px;
        }

        .message-input {
            width: 100%;
            border: none;
            background: transparent;
            outline: none;
            font-size: 14px;
 
