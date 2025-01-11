Start up commands:
$ python3 server.py server_port

$ python3 client.py server_port

To provide some context, a high-level example of BitTrickle’s primary file sharing functionality is
shown in Figure 1. In addition to the central indexing server, there are two authenticated, active peers
in the network, “A” and “B”. The exchange of messages are:
1. “A” informs the server that they wish to make “X.mp3” available to the network.
2. The server responds to “A” indicating that the file has been successfully indexed.
3. “B” queries the server where they might find “X.mp3”.
4. The server responds to “B” indicating that “A” has a copy of “X.mp3”.
5. “B” establishes a TCP connection with “A” and requests “X.mp3”.
6. “A” reads “X.mp3” from disk and sends it over the established TCP connection, which “B”
receives and writes to disk.

![image](https://github.com/user-attachments/assets/2bd80935-ec60-4e38-8b04-de76006e0163)
![image](https://github.com/user-attachments/assets/4f3ae916-1452-4e08-ac18-e2fae0d570ef)
