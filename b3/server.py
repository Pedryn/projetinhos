from flask import Flask, jsonify, request, g, send_from_directory
import sqlite3
import hashlib
import requests
import yfinance as yf
import os
from datetime import datetime

DB_PATH = 'dados.db'

app = Flask(__name__, static_folder='web', static_url_path='/')

# --- DB helpers
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT UNIQUE,
        senha_hash TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ativos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        ticker TEXT,
        quantidade REAL,
        preco_medio REAL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )''')
    conn.commit()
    conn.close()


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

# --- Usuarios
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json or {}
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    if not (nome and email and senha):
        return jsonify({'error': 'missing_fields'}), 400
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)', (nome, email, hash_senha(senha)))
        conn.commit()
        return jsonify({'ok': True}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'email_exists'}), 409
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    email = data.get('email')
    senha = data.get('senha')
    if not (email and senha):
        return jsonify({'error': 'missing_fields'}), 400
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id, nome, email, senha_hash FROM usuarios WHERE email=?', (email,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'invalid_credentials'}), 401
    if row['senha_hash'] != hash_senha(senha):
        return jsonify({'error': 'invalid_credentials'}), 401
    # Return minimal user info (no token for simplicity)
    return jsonify({'id': row['id'], 'nome': row['nome'], 'email': row['email']})

# --- Tickers / mercado
@app.route('/api/tickers')
def api_tickers():
    # Optional query: q (search), sort (Mais Caro/Mais Barato/A-Z/Z-A)
    q = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'Mais Barato')
    url = 'https://brapi.dev/api/quote/list'
    try:
        resp = requests.get(url, timeout=8)
        stocks = resp.json().get('stocks', [])
    except Exception as e:
        print('erro list tickers', e)
        stocks = []
    items = []
    for s in stocks:
        item = {
            'ticker': s.get('stock'),
            'name': s.get('name', ''),
            'close': s.get('close'),
            'change': s.get('change')
        }
        items.append(item)
    if q:
        qU = q.upper()
        items = [x for x in items if qU in (x['ticker'] or '').upper() or qU in (x['name'] or '').upper()]
    if sort == 'Mais Caro':
        items.sort(key=lambda x: x.get('close') or 0, reverse=True)
    elif sort == 'Mais Barato':
        items.sort(key=lambda x: x.get('close') or 0)
    elif sort == 'A-Z':
        items.sort(key=lambda x: x.get('ticker') or '')
    elif sort == 'Z-A':
        items.sort(key=lambda x: x.get('ticker') or '', reverse=True)
    return jsonify({'tickers': items})

@app.route('/api/ticker/<symbol>')
def api_ticker_detail(symbol):
    # Use yfinance for detail
    sym = symbol.upper()
    if not sym.endswith('.SA'):
        sym_y = sym + '.SA'
    else:
        sym_y = sym
    try:
        info = yf.Ticker(sym_y).info
    except Exception as e:
        print('yfinance error', e)
        info = {}
    return jsonify({'symbol': sym, 'info': info})

# --- Portfolio endpoints (simple, requires user_id in payload for auth simplicity)
@app.route('/api/portfolio/<int:user_id>', methods=['GET'])
def api_get_portfolio(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id, ticker, quantidade, preco_medio FROM ativos WHERE usuario_id=?', (user_id,))
    rows = c.fetchall()
    conn.close()
    positions = []
    for r in rows:
        positions.append({'id': r['id'], 'ticker': r['ticker'], 'quantidade': r['quantidade'], 'preco_medio': r['preco_medio']})
    return jsonify({'user_id': user_id, 'positions': positions})

@app.route('/api/portfolio/<int:user_id>', methods=['POST'])
def api_add_position(user_id):
    data = request.json or {}
    ticker = (data.get('ticker') or '').upper().replace('.SA', '')
    try:
        quantidade = float(data.get('quantidade'))
        preco_medio = float(data.get('preco_medio'))
    except Exception:
        return jsonify({'error': 'invalid_numbers'}), 400
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO ativos (usuario_id, ticker, quantidade, preco_medio) VALUES (?, ?, ?, ?)', (user_id, ticker, quantidade, preco_medio))
    conn.commit()
    conn.close()
    return jsonify({'ok': True}), 201

@app.route('/api/portfolio/<int:user_id>/<int:asset_id>', methods=['DELETE'])
def api_delete_position(user_id, asset_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM ativos WHERE id=? AND usuario_id=?', (asset_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# --- Static frontend
@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

if __name__ == '__main__':
    criar_tabelas()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)
