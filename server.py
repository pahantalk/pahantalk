from flask import Flask
import os
import sys

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>ПАХАНТАЛК</h1><p>Сервер работает на порту 10000</p>'

if __name__ == '__main__':
    print("Starting server...", file=sys.stderr)
    port = 10000
    print(f"Using port: {port}", file=sys.stderr)
    app.run(host='0.0.0.0', port=port, debug=False)
