import json
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

# Save published files to JSON
def save_published_files(filename="published_files.json"):
    # Convert sets to lists for JSON serialization
    serializable_data = {user: list(files) for user, files in published_files.items()}
    with open(filename, "w") as file:
        json.dump(serializable_data, file)

# Load published files from JSON
def load_published_files(filename="published_files.json"):
    try:
        with open(filename, "r") as file:
            # Convert lists back to sets after loading from JSON
            data = json.load(file)
            return {user: set(files) for user, files in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# 2.1 Authentication logic
def authenticate(username, password, active_users, client_address):
    if username in credentials and credentials[username] == password and username not in active_users:
        active_users[username] = datetime.now()
        client_addresses[client_address] = username  # Store the address-to-username mapping
        return OK, "OK: Authenticated"
    else:
        return ERROR, "ERR: Authentication failed"

# 2.2 Heartbeat monitor to check for inactive users
def monitor_heartbeats():
    while True:
        now = datetime.now()
        inactive_users = [user for user, last_beat in active_users.items() if now - last_beat > timedelta(seconds=3)]
        for user in inactive_users:
            active_users.pop(user, None)  # Remove inactive user
            # Remove inactive user's address mapping
            client_address = None
            for addr, u in client_addresses.items():
                if u == user:
                    client_address = addr
                    break

            if client_address:
                client_addresses.pop(client_address, None) # Remove address mapping
            published_files.pop(user, None)  # Clear user's published files
            save_published_files()  # Save to JSON after update
            log_message(f"{user} marked as inactive due to missed heartbeat.")
        time.sleep(1)

# 2.3.1 get <filename>
def get_file(filename, user_requesting):
    for username, files in published_files.items():
        if filename in files and username != user_requesting:
            for addr, u in client_addresses.items():
                if u == username:
                    server, port = addr
                    client_address = f"{server}:{port}"
                    return OK, client_address
    return ERROR, "File not found"

# 2.3.2 lap
def list_active_peers(user_requesting):
    active_peers = [user for user in active_users if user != user_requesting]
    if active_peers:
        active_count = len(active_peers)
        peer_word = "peers" if active_count > 1 else "peer"
        return OK, f"{active_count} active {peer_word}:\n" + "\n".join(active_peers)
    else:
        return OK, "No active peers"

# 2.3.3 lpf
def list_published_files(user_requesting):
    files = published_files.get(user_requesting, [])
    if files:
        file_count = len(files)
        file_word = "files" if file_count > 1 else "file"
        file_list = "\n".join(files)

        return OK, f"{file_count} {file_word} published:\n{file_list}"
    else:
        return OK, "No files published"

# 2.3.4 pub <filename>
def publish_file(username, filename):
    if username not in published_files:
        published_files[username] = set()

    if filename not in published_files[username]:
        published_files[username].add(filename)
        save_published_files()  # Save to JSON after publishing a file

    return OK, "File published successfully"

# 2.3 Command handling
def handle_command(raw_command, username):
    command = raw_command[:4].lower().strip()
    log_message(f"Received {command.upper()} from {username}")

    # 2.3.1 get <filename>
    if command == "get":
        filename = raw_command[4:].strip()
        return get_file(filename, username)
    # 2.3.2 lap
    elif command == "lap":
        return list_active_peers(username)
    # 2.3.3 lpf
    elif command == "lpf":
        return list_published_files(username)
    # 2.3.4 pub <filename>
    elif command == "pub":
        filename = raw_command[4:].strip()
        return publish_file(username, filename)
    elif command == "sch":
        return ERROR, "Received SCH command"
    elif command == "unp":
        return ERROR, "Received UNP command"
    elif command == "xit":
        return OK, "Exiting client session"
    else:
        return ERROR, "ERR: Unknown command"

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
published_files = load_published_files()  # Load published files from JSON on startup

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
        status, response = authenticate(username, password, active_users, client_address)
        server_socket.sendto(response.encode(), client_address)
        if status == ERROR:
            log_message(f"Sent ERR to {username}")
        elif status == OK:
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
