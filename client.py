import socket
import random
import time
from collections import defaultdict

# Load Balancer Address
LOAD_BALANCER_HOST = '127.0.0.1'
LOAD_BALANCER_PORT = 1245

# Simulated clients
CLIENTS = ["192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4"]

# Rate limiting configuration
RATE_LIMIT = 5  # Max requests per client
TIME_WINDOW = 10  # Time window in seconds

# Client request log: {IP: [timestamps]}
client_requests = defaultdict(list)

def is_rate_limited(client_ip):
    """
    Check if a client exceeds the rate limit.
    Removes outdated requests from the log and returns True if the client
    has exceeded the rate limit within the time window.
    """
    now = time.time()
    requests = client_requests[client_ip]
    # Remove requests older than the time window
    client_requests[client_ip] = [t for t in requests if now - t <= TIME_WINDOW]
    
    # If the number of requests in the time window exceeds the limit, block the client
    return len(client_requests[client_ip]) >= RATE_LIMIT

def log_request(client_ip):
    """
    Log a request made by a client.
    Adds the current timestamp to the client's request log.
    """
    client_requests[client_ip].append(time.time())

def log_rate_limit(client_ip):
    """
    Log when a client exceeds the rate limit.
    """
    print(f"Rate limit exceeded for {client_ip}")

def simulate_client_requests():
    """
    Simulate multiple clients sending requests to the DNS load balancer.
    """
    while True:
        client_ip = random.choice(CLIENTS)
        print("_______________________\n")
        print(client_requests)
        print("-------------------\n")
        
        if is_rate_limited(client_ip):
            log_rate_limit(client_ip)  # Log if the client exceeds the rate limit
            continue  # Skip sending the request if the client is rate-limited
        
        log_request(client_ip)

        # Create the message
        message = f"Request from {client_ip}: {random.randint(1, 100)}".encode()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
                client_socket.sendto(message, (LOAD_BALANCER_HOST, LOAD_BALANCER_PORT))
                
                client_socket.settimeout(3)
                response, _ = client_socket.recvfrom(512)
                print(f"Client {client_ip} -> Response: {response.decode()}")
        except socket.timeout:
            print(f"Client {client_ip} -> Error: Timeout waiting for response")
        except Exception as e:
            print(f"Client {client_ip} -> Error: {e}")

        time.sleep(random.uniform(0.5, 2.0))

if __name__ == "__main__":
    print("Starting client simulation...")
    simulate_client_requests()
