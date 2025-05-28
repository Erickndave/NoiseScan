from flask import Flask, request, jsonify, render_template, redirect
from threading import Lock
import sqlite3
import time
import os
import logging
from datetime import datetime

# Configuração básica de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
DB_FILE = 'dados_sonoros.db'
db_lock = Lock()

# Configurações otimizadas para SQLite
SQLITE_PRAGMAS = {
    'journal_mode': 'WAL',
    'synchronous': 'NORMAL',
    'busy_timeout': 30000,
    'foreign_keys': 'ON'
}

def init_db():
    """Inicializa o banco de dados com tabelas e configurações"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_FILE)
            try:
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
                app.logger.info("Banco de dados inicializado com sucesso")
            except sqlite3.Error as e:
                app.logger.error(f"Erro ao criar tabelas: {str(e)}")
                raise
            finally:
                conn.close()
    except Exception as e:
        app.logger.critical(f"Falha crítica na inicialização do DB: {str(e)}")
        raise

def get_db_connection():
    """Obtém conexão com o banco de dados com tratamento de erros"""
    attempts = 0
    last_error = None
    
    while attempts < 3:
        try:
            conn = sqlite3.connect(DB_FILE, timeout=30)
            conn.row_factory = sqlite3.Row
            for pragma, value in SQLITE_PRAGMAS.items():
                conn.execute(f"PRAGMA {pragma}={value}")
            return conn
        except sqlite3.Error as e:
            last_error = e
            app.logger.warning(f"Tentativa {attempts+1} de conexão falhou: {str(e)}")
            time.sleep(1)
            attempts += 1
    
    app.logger.error("Falha ao conectar ao banco de dados após 3 tentativas")
    raise Exception(f"Não foi possível conectar ao banco: {str(last_error)}")

@app.route('/')
def home():
    """Rota principal que redireciona para o dashboard"""
    app.logger.debug("Acesso à rota raiz, redirecionando para /dashboard")
    return redirect('/dashboard')

@app.route('/api/dados', methods=['POST'])
def receber_dados():
    """Endpoint para receber dados do ESP32"""
    app.logger.debug(f"Requisição recebida: {request.data}")
    
    if not request.is_json:
        app.logger.warning("Requisição sem Content-Type application/json")
        return jsonify({"erro": "Content-Type deve ser application/json"}), 415

    try:
        data = request.get_json()
        if 'nivel_ruido' not in data:
            app.logger.warning("Campo 'nivel_ruido' faltando no JSON")
            return jsonify({"erro": "Campo 'nivel_ruido' obrigatório"}), 400
            
        nivel_ruido = float(data['nivel_ruido'])
        app.logger.info(f"Dado recebido: {nivel_ruido} dB")
        
        with db_lock:
            conn = get_db_connection()
            try:
                conn.execute(
                    "INSERT INTO medicoes (nivel_ruido) VALUES (?)",
                    (nivel_ruido,)
                )
                conn.commit()
                app.logger.debug("Dado armazenado no banco com sucesso")
                return jsonify({
                    "status": "success",
                    "message": f"Dado {nivel_ruido} dB recebido",
                    "timestamp": datetime.now().isoformat()
                }), 200
            finally:
                conn.close()
                
    except ValueError as e:
        app.logger.error(f"Erro de valor: {str(e)}")
        return jsonify({"erro": "Valor de nível de ruído inválido"}), 400
    except Exception as e:
        app.logger.error(f"Erro inesperado: {str(e)}")
        return jsonify({"erro": "Falha no processamento"}), 500

@app.route('/dashboard')
def dashboard():
    """Rota do dashboard de monitoramento"""
    try:
        with db_lock:
            conn = get_db_connection()
            try:
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
                app.logger.debug(f"Retornando {len(medicoes)} medições para o dashboard")
                return render_template('dashboard.html', medicoes=medicoes)
            finally:
                conn.close()
    except Exception as e:
        app.logger.critical(f"Erro no dashboard: {str(e)}")
        return f"Erro no banco de dados: {str(e)}", 500

@app.after_request
def log_requests(response):
    """Middleware para log de todas as requisições"""
    app.logger.info(
        f"{request.remote_addr} {request.method} {request.path} "
        f"{response.status_code} {response.content_length}bytes"
    )
    return response

if __name__ == '__main__':
    try:
        if not os.path.exists(DB_FILE):
            app.logger.info("Inicializando banco de dados pela primeira vez")
            init_db()
        
        app.logger.info("Iniciando servidor Flask")
        app.run(
            host='192.168.21.30',
            port=5000,
            debug=True,
            threaded=True,
            use_reloader=False,
            passthrough_errors=True
        )
    except Exception as e:
        app.logger.critical(f"Falha na inicialização: {str(e)}")
        raise