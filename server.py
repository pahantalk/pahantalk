from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>ПАХАНТАЛК</h1><p>Сервер работает. Кнопки должны нажиматься.</p><button onclick="alert(\'Кнопка работает!\')">Нажми меня</button>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
