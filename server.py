from socket import *
import sys
import time
from datetime import datetime, timedelta
import threading

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{timestamp}: {message}")

# 2.1.1. Load credentials from credentials.txt
def load_credentials(filename="credentials.txt"):
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
        active_users[username] = datetime.now()
        return "OK: Authentication successful"

# Heartbeat monitor to check for inactive users
def monitor_heartbeats():
    while True:
        now = datetime.now()
        inactive_users = [user for user, last_beat in active_users.items() if now - last_beat > timedelta(seconds=3)]
        for user in inactive_users:
            del active_users[user]
            log_message(f"{user} marked as inactive due to missed heartbeat.")
        time.sleep(1)

# Server setup
if len(sys.argv) != 2:
    print("\n===== Usage: python3 server.py SERVER_PORT ======\n")
    exit(1)

server_port = int(sys.argv[1])
server_address = ("127.0.0.1", server_port)
server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(server_address)
log_message("Server is listening on port " + str(server_port))

# Load credentials
credentials = load_credentials()
active_users = {}  # Track active users and their last heartbeat time

# Start the heartbeat monitoring thread
heartbeat_thread = threading.Thread(target=monitor_heartbeats, daemon=True)
heartbeat_thread.start()

while True:
    message, client_address = server_socket.recvfrom(1024)
    message = message.decode()

    if message.startswith("HBT"):
        username = message.split()[1]
        active_users[username] = datetime.now()
        log_message(f"Received HBT from {username}")

    else:
        # Handle authentication
        username, password = message.split()
        log_message(f"Received AUTH from {username}")
        response = authenticate(username, password, active_users)

        if response.startswith("ERR"):
            log_message(f"Sent ERR to {username}")
        elif response.startswith("OK"):
            log_message(f"Sent OK to {username}")

        server_socket.sendto(response.encode(), client_address)
