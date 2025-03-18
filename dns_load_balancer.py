import socket
import threading
import time
from collections import defaultdict
from log_utils import log_request, log_response, log_rate_limit
import sqlite3

HOST = '127.0.0.1'
PORT = 1245                                                                                                                                                                                                                                                                                            
BACKENDS = [
    ('127.0.0.2', 1250),  # Backend 1
    ('127.0.0.3', 1251),  # Backend 2
]
RATE_LIMIT = 5  # Max requests per client in a time window
TIME_WINDOW = 10  # Time window in seconds                                                                          
CACHE_TTL = 60  # Cache time-to-live in seconds
DB_PATH = 'cache.db'

# Server state
client_requests = defaultdict(list)
server_health = {backend: True for backend in BACKENDS}
current_backend = 0

def init_db():
    """Initialize the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB,
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
    """Store value in the cache with a TTL."""
    timestamp = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT OR REPLACE INTO cache (key, value, timestamp)
            VALUES (?, ?, ?)
        ''', (key, value, timestamp))

def get_cache(key):
    """Retrieve value from the cache if it exists and is not expired."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('SELECT value, timestamp FROM cache WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row:
            value, timestamp = row
            if int(time.time()) - timestamp <= CACHE_TTL:
                return value
            else:
                conn.execute('DELETE FROM cache WHERE key = ?', (key,))
    return None

def update_active_client(ip):
    """Update or insert the client's last request time."""
    timestamp = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT OR REPLACE INTO active_clients (ip, last_request)
            VALUES (?, ?)
        ''', (ip, timestamp))

def get_active_clients():
    """Get all active clients from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('SELECT ip, last_request FROM active_clients')
        clients = cursor.fetchall()
    return {client[0]: client[1] for client in clients}

# Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

def is_rate_limited(client_ip):
    """Check if a client has exceeded the rate limit."""
    now = time.time()
    requests = client_requests[client_ip]
    client_requests[client_ip] = [t for t in requests if now - t <= TIME_WINDOW]
    
    if len(client_requests[client_ip]) >= RATE_LIMIT:
        log_rate_limit(client_ip)
        return True
    return False

def get_next_backend():
    """Return the next available backend using round-robin."""
    global current_backend
    healthy_backends = [b for b, healthy in server_health.items() if healthy]
    if not healthy_backends:
        raise Exception("No healthy backends available")
    backend = healthy_backends[current_backend % len(healthy_backends)]
    current_backend += 1
    return backend

def health_check():
    """Periodically check the health of the backend servers."""
    CHECK_INTERVAL = 5
    while True:
        for backend in BACKENDS:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.settimeout(1)  # Timeout for health check
                    s.sendto(b'health_check', backend)  # Simulate a health check
                    s.recvfrom(512)  # Wait for response
                    server_health[backend] = True
            except socket.timeout:
                server_health[backend] = False
        time.sleep(CHECK_INTERVAL)

# Health check thread
threading.Thread(target=health_check, daemon=True).start()

def handle_request(data, client_address):
    """Handle incoming DNS requests."""
    client_ip = client_address[0]
    if is_rate_limited(client_ip):
        log_rate_limit(client_ip)
        return
    
    try:
        cached_response = get_cache(data)
        if cached_response:
            sock.sendto(cached_response, client_address)
            log_response(client_address, "cache")
        else:
            backend = get_next_backend()
            log_request(client_address, backend)
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as backend_sock:
                backend_sock.sendto(data, backend)
                response, _ = backend_sock.recvfrom(512)
                set_cache(data, response)
                sock.sendto(response, client_address)
                log_response(client_address, backend)
        
        # Update active client information
        update_active_client(client_ip)
    except Exception as e:
        print(f"Error: {e}")

# Initialize the database
init_db()

# Main loop to listen for incoming requests
while True:
    try:
        data, client_address = sock.recvfrom(512)  # Receive client request
        threading.Thread(target=handle_request, args=(data, client_address), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down...")
        break
