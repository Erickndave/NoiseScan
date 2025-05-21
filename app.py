from flask import Flask, request, jsonify, render_template, redirect  # Adicionei redirect aqui
import sqlite3
import os
from threading import Lock

app = Flask(__name__)
DB_FILE = 'dados_sonoros.db'
db_lock = Lock()

def init_db():
    """Inicializa o banco de dados"""
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS medicoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nivel_ruido REAL NOT NULL,
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        finally:
            conn.close()

def get_db():
    """Obtém conexão com o banco de dados"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    """Redireciona para o dashboard"""
    return redirect('/dashboard')  # Agora usando a função importada corretamente

@app.route('/api/dados', methods=['POST'])
def receber_dados():
    try:
        data = request.get_json()
        if not data or 'nivel_ruido' not in data:
            return jsonify({"erro": "Dados inválidos"}), 400
            
        nivel_ruido = float(data['nivel_ruido'])
        
        with db_lock:
            conn = get_db()
            try:
                conn.execute("INSERT INTO medicoes (nivel_ruido) VALUES (?)", (nivel_ruido,))
                conn.commit()
                return jsonify({"status": "Dados salvos!"}), 200
            finally:
                conn.close()
    except ValueError:
        return jsonify({"erro": "Valor numérico inválido"}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/dashboard')
def dashboard():
    try:
        with db_lock:
            conn = get_db()
            try:
                cursor = conn.execute('''
                    SELECT id, nivel_ruido, 
                    strftime('%d/%m/%Y %H:%M:%S', data_hora) as data_hora
                    FROM medicoes 
                    ORDER BY data_hora DESC 
                    LIMIT 20
                ''')
                
                # Convertendo cada Row para dicionário
                medicoes = [dict(row) for row in cursor.fetchall()]
                
                return render_template('dashboard.html', medicoes=medicoes)
            finally:
                conn.close()
    except Exception as e:
        return f"Erro no banco de dados: {str(e)}", 500

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)