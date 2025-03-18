from flask import Flask, jsonify, render_template
from robin import server_health  # Assuming this file contains server health data
from client import client_requests  # Assuming this file contains client requests data
import sqlite3
import time

# Flask app for the dashboard
app = Flask(__name__)

# SQLite DB path for cache
DB_PATH = 'cache.db'

def init_db():
    """Initialize the SQLite database and create cache table if not exists."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                timestamp INTEGER
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS active_clients (
                ip TEXT PRIMARY KEY,
                last_request INTEGER
            )
        ''')

def set_cache(key, value, ttl=60):
    """Set cache in the SQLite database with TTL."""
    timestamp = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT OR REPLACE INTO cache (key, value, timestamp)
            VALUES (?, ?, ?)
        ''', (key, value, timestamp))

def get_cache(key):
    """Get cache from SQLite database if not expired."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('SELECT value, timestamp FROM cache WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row:
            value, timestamp = row
            if int(time.time()) - timestamp <= 60:  # TTL of 60 seconds
                return value
            else:
                conn.execute('DELETE FROM cache WHERE key = ?', (key,))
    return None

def get_active_clients():
    """Get all active clients from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('SELECT ip, last_request FROM active_clients')
        clients = cursor.fetchall()
    return {client[0]: client[1] for client in clients}

# Initialize database
init_db()

@app.route('/')
def index():
    """
    Serve the HTML dashboard.
    """
    return render_template('dashboard.html')

@app.route('/api/data')
def api_data():
    """
    API to provide server health, client rate limit information, and cache statistics.
    """
    formatted_server_health = {f"{ip}:{port}": status for (ip, port), status in server_health.items()}
    active_clients = get_active_clients()  # Retrieve active clients from the database

    # Fetch cache size from SQLite
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('SELECT COUNT(*) FROM cache')
        cache_size = cursor.fetchone()[0]

    return jsonify({
        "server_health": formatted_server_health,
        "active_clients": active_clients,  # Active clients data from database
        "cache_size": cache_size,  # Cache statistics from SQLite
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
