from socket import *
import sys

# Client setup
if len(sys.argv) != 2:
    print("\n===== Usage: python3 client.py SERVER_PORT ======\n")
    sys.exit(1)

server_port = int(sys.argv[1])
client_socket = socket(AF_INET, SOCK_DGRAM)
server_address = ("127.0.0.1", server_port)

# 2.1. Authentication
while True:
    username = input("Enter username: ")
    password = input("Enter password: ")
    credentials = f"{username} {password}"

    client_socket.sendto(credentials.encode(), server_address)
    response, _ = client_socket.recvfrom(1024)
    response = response.decode()

    if response.startswith("OK"):
        print("Welcome to BitTrickle!")
        break  # Exit loop on successful authentication
    else:
        print("Authentication failed. Please try again.")
