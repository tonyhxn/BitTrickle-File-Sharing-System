from socket import *
import sys

# Usage: python3 server.py SERVER_PORT
if len(sys.argv) != 2:
    print("\n===== Error usage, python3 server.py SERVER_PORT ======\n")
    exit(0)

serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# define socket for the server side and bind address
# SOCK_DGRAM is for User Datagram Protocol (UDP)
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(serverAddress)
