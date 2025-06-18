from flask import Flask, request, jsonify, render_template, redirect
import sqlite3
from threading import Lock
from datetime import datetime
import logging
import os

# Configuração básica
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuração do banco de dados
DB_FILE = 'dados_sonoros.db'
db_lock = Lock()

# Configurações de otimização do SQLite
SQLITE_PRAGMAS = {
    'journal_mode': 'WAL',
    'synchronous': 'NORMAL',
    'foreign_keys': 'ON'
}

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def init_db():
    """Inicializa o banco de dados com a estrutura necessária"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            for pragma, value in SQLITE_PRAGMAS.items():
                conn.execute(f"PRAGMA {pragma}={value}")
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS medicoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nivel_ruido REAL NOT NULL,
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            logging.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logging.error(f"Falha na inicialização do banco: {str(e)}")
        raise
    finally:
        conn.close()

def get_db_connection():
    """Obtém uma conexão com o banco de dados"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30)
        conn.row_factory = sqlite3.Row
        for pragma, value in SQLITE_PRAGMAS.items():
            conn.execute(f"PRAGMA {pragma}={value}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Erro ao conectar ao banco: {str(e)}")
        if conn:
            conn.close()
        raise

@app.route('/')
def home():
    """Rota principal que redireciona para o dashboard"""
    return redirect('/dashboard')

@app.route('/api/dados', methods=['POST'])
def receber_dados():
    """Endpoint para receber dados do ESP32"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type deve ser application/json"}), 415
            
        data = request.get_json()
        nivel_ruido = float(data.get('nivel_ruido', 0))
        
        if not 0 <= nivel_ruido <= 130:
            return jsonify({"error": "Valor de dB deve estar entre 0 e 130"}), 400
        
        with db_lock:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO medicoes (nivel_ruido) VALUES (?)",
                (round(nivel_ruido, 2),)
            )
            conn.commit()
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"Erro em /api/dados: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/ultimos-dados', methods=['GET'])
def get_ultimos_dados():
    """Endpoint para fornecer dados ao dashboard"""
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.execute('''
                SELECT 
                    nivel_ruido,
                    strftime('%Y-%m-%d %H:%M:%S', data_hora) as data_hora
                FROM medicoes
                ORDER BY data_hora DESC
                LIMIT 15
            ''')
            dados = [dict(row) for row in cursor.fetchall()]
            dados.reverse()  # Ordem cronológica para o gráfico
            
            return jsonify({
                "status": "success",
                "data": dados
            }), 200
    except Exception as e:
        logging.error(f"Erro em /api/ultimos-dados: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/dashboard')
def dashboard():
    """Rota do dashboard principal"""
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.execute('''
                SELECT 
                    id,
                    nivel_ruido,
                    strftime('%d/%m/%Y %H:%M:%S', data_hora) as data_hora
                FROM medicoes
                ORDER BY data_hora DESC
                LIMIT 20
            ''')
            medicoes = [dict(row) for row in cursor.fetchall()]
        
        return render_template('dashboard.html', medicoes=medicoes)
    except Exception as e:
        logging.error(f"Erro no dashboard: {str(e)}")
        return render_template('error.html', error=str(e)), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.after_request
def add_security_headers(response):
    """Adiciona headers de segurança"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

if __name__ == '__main__':
    # Verifica se o banco de dados existe ou precisa ser criado
    if not os.path.exists(DB_FILE):
        init_db()
    
    # Configuração do servidor
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )