from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>ПАХАНТАЛК</h1><p>Тест порта</p>'

if __name__ == '__main__':
    # Жёстко фиксируем порт
    app.run(host='0.0.0.0', port=10000, debug=False)
