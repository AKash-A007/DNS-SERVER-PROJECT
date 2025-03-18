import socket
import threading
import time

# Backend servers (IP addresses and ports)
BACKENDS = [
    ('127.0.0.2', 1250),
    ('127.0.0.3', 1251),
]

# Server health status (True if the server is healthy, False otherwise)
server_health = {backend: True for backend in BACKENDS}
current_backend = 0  # Track the last backend server used

def get_next_backend():
    """
    Select the next healthy backend server using round-robin strategy.
    Ensures at least one healthy backend is available before returning.
    """
    global current_backend
    healthy_backends = [b for b, healthy in server_health.items() if healthy]
    if not healthy_backends:
        raise Exception("No healthy backends available")
    
    # Round-robin selection
    backend = healthy_backends[current_backend % len(healthy_backends)]
    current_backend += 1
    return backend

def health_check():
    """
    Periodically check the health of backend servers.
    Uses a loop to continuously check backend health and updates server_health.
    """
    CHECK_INTERVAL = 5  # Health check interval in seconds
    while True:
        for backend in BACKENDS:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.settimeout(1)  # Timeout for health checks
                    s.sendto(b'health_check', backend)  # Send health check packet
                    s.recvfrom(512)  # Wait for a response
                    server_health[backend] = True
            except socket.timeout:
                server_health[backend] = False
        time.sleep(CHECK_INTERVAL)

# Start health check thread
threading.Thread(target=health_check, daemon=True).start()
