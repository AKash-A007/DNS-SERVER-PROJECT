from collections import defaultdict
import time
from client import client_requests
# Client request log: {IP: [timestamps]}
RATE_LIMIT = 5  # Max requests per client (adjustable)
TIME_WINDOW = 10  # Time window in seconds (adjustable)

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

