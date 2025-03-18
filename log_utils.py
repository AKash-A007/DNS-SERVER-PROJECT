import logging

# Configure logging level
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_request(client_address, backend):
    logging.info(f"Request from {client_address} forwarded to backend {backend}")

def log_response(client_address, backend):
    logging.info(f"Response from backend {backend} sent to {client_address}")

def log_rate_limit(client_address):
    logging.warning(f"Rate limit exceeded for {client_address}")
