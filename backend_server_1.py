import socket

HOST = '127.0.0.2'  # Change for other backends (127.0.0.3 for backend 2)
PORT = 1250  # Change for other backends (1251 for backend 2)

# Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

def handle_request():
    """Simulate processing of client queries."""
    while True:
        data, addr = sock.recvfrom(512)
        print(f'data:{data} address:{addr}')
        if data == b'health_check':
            # Respond to health check with an acknowledgment
            sock.sendto(b'healthy', addr)
        else:
            # Simulate processing of DNS queries
            response = f"Response for {data.decode()}".encode()
            sock.sendto(response, addr)

if __name__ == '__main__':
    print(f"Backend server running on {HOST}:{PORT}")
    handle_request()
