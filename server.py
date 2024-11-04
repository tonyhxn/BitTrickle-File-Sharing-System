from socket import *
import sys
from datetime import datetime

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"{timestamp}: {server_address} {message}")

# Usage: python3 server.py SERVER_PORT
if len(sys.argv) != 2:
    print("\n===== Usage: python3 server.py SERVER_PORT ======\n")
    exit(0)

# Load credentials from credentials.txt
def load_credentials(filename="server/credentials.txt"):
    credentials = {}
    with open(filename, "r") as file:
        for line in file:
            username, password = line.strip().split()
            credentials[username] = password
    return credentials

# Authentication logic
def authenticate(username, password, active_users):
    if username not in credentials:
        return "ERR: Unknown username"
    elif credentials[username] != password:
        return "ERR: Incorrect password"
    elif username in active_users:
        return "ERR: User already active"
    else:
        active_users.add(username)
        return "OK: Authentication successful"

# Server setup
server_host = "127.0.0.1"
server_port = int(sys.argv[1])
server_address = (server_host, server_port)
# define socket for the server side and bind address
# SOCK_DGRAM is for User Datagram Protocol (UDP)
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(server_address)
log_message("Server is listening on port " + str(server_port))

# define a set to store active users
credentials = load_credentials()
active_users = set()

while True:
    message, client_address = serverSocket.recvfrom(1024)

    # 2.1. Authentication
    username, password = message.decode().split()
    log_message(f"Received AUTH from {username}")
    response = authenticate(username, password, active_users)
    if response.startswith("ERR"):
        log_message(f"Sent ERR to {username}")
    elif response.startswith("OK"):
        log_message(f"Sent OK to {username}")

    serverSocket.sendto(response.encode(), client_address)
