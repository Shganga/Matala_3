import socket

def start_server(host='127.0.0.1', port=12345, max_message_size=1024):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
    server_socket.bind((host, port))  # Bind to the specified host and port
    server_socket.listen(5)  # Listen for up to 5 connections
    print(f"Server listening on {host}:{port}")

    client_socket, client_address = server_socket.accept()  # Accept a client connection
    print(f"Connection established with {client_address}")

    # Receive a request from the client
    request = client_socket.recv(1024).decode()  # Buffer size of 1024 bytes
    if request.lower() == "max_message_size":
        # Respond with the maximum message size
        client_socket.send(str(max_message_size).encode())
    else:
        client_socket.send(b"Invalid request")

    handle_client()

    client_socket.close()  # Close the connection

def handle_client(client_socket : socket):
    while True:
        return


if __name__ == "__main__":
    # Set the maximum allowed message size (e.g., 1024 bytes)
    max_message_size = 120
    start_server(max_message_size=max_message_size)

