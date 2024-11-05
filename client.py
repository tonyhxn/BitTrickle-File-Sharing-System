from socket import *
import sys
import threading
import time

# Client setup
if len(sys.argv) != 2:
    print("\n===== Usage: python3 client.py SERVER_PORT ======\n")
    sys.exit(1)

server_port = int(sys.argv[1])
client_socket = socket(AF_INET, SOCK_DGRAM)
server_address = ("127.0.0.1", server_port)

# 2.1 Authentication
while True:
    username = input("Enter username: ")
    password = input("Enter password: ")
    credentials = f"login:{username} {password}"

    client_socket.sendto(credentials.encode(), server_address)
    response, _ = client_socket.recvfrom(1024)
    response = response.decode()

    if response.startswith("OK"):
        print("Welcome to BitTrickle!")
        break  # Exit loop on successful authentication
    else:
        print("Authentication failed. Please try again.")

# 2.2 Heartbeat Mechanism
def send_heartbeat():
    while True:
        heartbeat_message = f"HBT {username}"
        client_socket.sendto(heartbeat_message.encode(), server_address)
        time.sleep(2)

# 2.2 Start the heartbeat thread
heartbeat_thread = threading.Thread(target=send_heartbeat)
heartbeat_thread.start()

# 2.3 Client Commands
def handle_commands():
    while True:
        print("Available commands are: get, lap,lpf, pub, sch, unp, xit")
        command = input("> ").strip()
        if command == "xit":
            print("Exiting BitTrickle...")
            break
        client_socket.sendto(command.encode(), server_address)
        response, _ = client_socket.recvfrom(1024)
        print(response.decode("utf-8"))

# Start command handling loop
handle_commands()

client_socket.close()