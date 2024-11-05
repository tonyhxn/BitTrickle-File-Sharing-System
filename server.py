from socket import *
import sys
from datetime import datetime, timedelta
import threading
import time

ERROR = False
OK = True

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{timestamp}: {message}")

# 2.1.1 Load credentials from credentials.txt
def load_credentials(filename="credentials.txt"):
    credentials = {}
    with open(filename, "r") as file:
        for line in file:
            username, password = line.strip().split()
            credentials[username] = password
    return credentials

# 2.1 Authentication logic
def authenticate(username, password, active_users, client_address):
    if username not in credentials:
        return "ERR: Unknown username"
    elif credentials[username] != password:
        return "ERR: Incorrect password"
    elif username in active_users:
        return "ERR: User already active"
    else:
        active_users[username] = datetime.now()
        client_addresses[client_address] = username  # Store the address-to-username mapping
        return "OK: Authentication successful"

# 2.2 Heartbeat monitor to check for inactive users
def monitor_heartbeats():
    while True:
        now = datetime.now()
        inactive_users = [user for user, last_beat in active_users.items() if now - last_beat > timedelta(seconds=3)]
        for user in inactive_users:
            active_users.pop(user, None)  # Remove inactive user
            # Remove inactive user's address mapping
            for addr, u in client_addresses.items():
                if u == user:
                    client_address = addr
                    break

            if client_address:
                client_addresses.pop(client_address, None) # Remove address mapping
            log_message(f"{user} marked as inactive due to missed heartbeat.")
        time.sleep(1)

# 2.3.1 get <filename>
def get_file(filename, user_requesting):
    for username, files in published_files.items():
        if filename in files and username != user_requesting:
            for addr, u in client_addresses.items():
                if u == username:
                    client_address = addr
                    return client_address, username
    return ERROR, "File not found"

# 2.3.2 lap
def list_active_peers(user_requesting):
    active_peers = [user for user in active_users if user != user_requesting]
    if active_peers:
        return OK, "Active peers: " + ", ".join(active_peers)
    else:
        return OK, "No active peers"

# 2.3.3 lpf
def list_published_files(user_requesting):
    files = published_files.get(user_requesting, [])
    if files:
        return OK, f"{len(files)} File{'s' if len(files) > 1 else ''}:\n{'\n'.join(files)}"
    else:
        return OK, "No files published."

# 2.3.4 pub <filename>
def publish_file(username, filename):
    if username not in published_files:
        published_files[username] = set()

    if filename not in published_files[username]:
        published_files[username].add(filename)

    log_message(f"{username} published file: {filename}")
    return OK, f"File published successfully"


# 2.3 Command handling
def handle_command(command, username):
    log_message(f"Received {command.upper()} from {username}")

    # 2.3.1 get <filename>
    if command.startswith("get "):
        filename = command.removeprefix("get ")
        return get_file(filename, username)
    # 2.3.2 lap
    elif command == "lap":
        return list_active_peers(username)
    # 2.3.3 lpf
    elif command == "lpf":
        return list_published_files(username)
    # 2.3.4 pub <filename>
    elif command.startswith("pub "):
        filename = command.removeprefix("get ")
        return publish_file(username, filename)
    elif command.startswith("sch "):
        return "Received SCH command"
    elif command.startswith("unp "):
        return "Received UNP command"
    elif command == "xit":
        return "Exiting client session"
    else:
        return "ERR: Unknown command"

# Server setup
if len(sys.argv) != 2:
    print("\n===== Usage: python3 server.py SERVER_PORT ======\n")
    exit(1)

server_port = int(sys.argv[1])
server_address = ("127.0.0.1", server_port)
server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(server_address)
log_message("Server is listening on port " + str(server_port))

# 2.1.1 Load credentials
credentials = load_credentials()
active_users = {}  # Track active users and their last heartbeat time
client_addresses = {}  # Track client addresses to identify them by address
published_files = {}

# 2.2 Start the heartbeat monitoring thread
heartbeat_thread = threading.Thread(target=monitor_heartbeats, daemon=True)
heartbeat_thread.start()

while True:
    message, client_address = server_socket.recvfrom(1024)
    message = message.decode()

    if message.startswith("HBT"):
        # 2.2 Update heartbeat
        username = client_addresses.get(client_address)
        if username:
            active_users[username] = datetime.now()
            log_message(f"Received HBT from {username}")

    elif message.startswith("login:"):
        # 2.1 Handle authentication
        username, password = message.split('login:')[1].split() # Extract username and password
        log_message(f"Received AUTH from {username}")
        response = authenticate(username, password, active_users, client_address)
        server_socket.sendto(response.encode(), client_address)
        if response.startswith("ERR: "):
            log_message(f"Sent ERR to {username}")
        elif response.startswith("OK"):
            log_message(f"Sent OK to {username}")

    else:
        # 2.3 Handle commands
        username = client_addresses.get(client_address)
        if username:
            status, response = handle_command(message, username)
            server_socket.sendto(response.encode(), client_address)
            if status == ERROR:
                log_message(f"Sent ERR to {username}")
            elif status == OK:
                log_message(f"Sent OK to {username}")
        else:
            log_message(f"Received command from unrecognized address: {client_address}")
            response = "ERR: Unauthenticated or unknown client"
            server_socket.sendto(response.encode(), client_address)
