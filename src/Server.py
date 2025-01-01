import socket

def start_server(host='127.0.0.1', port=12345, max_message_size=1024):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
    server_socket.bind((host, port))  # Bind to the specified host and port
    server_socket.listen(5)  # Listen for up to 5 connections
    print(f"Server listening on {host}:{port}")

    client_socket, client_address = server_socket.accept()  # Accept a client connection
    print(f"Connection established with {client_address}")

    # Receive a request from the client
    request = client_socket.recv(max_message_size).decode()  # Buffer size of 1024 bytes
    if request.lower() == "max_message_size":
        # Respond with the maximum message size
        client_socket.send(str(max_message_size).encode())
    else:
        client_socket.send(b"Invalid request")

    server_recive(client_socket, buffer_size = max_message_size)

    client_socket.close()  # Close the connection

def server_recive(client_socket : socket, buffer_size=1024):
    received_data = {}  # Dictionary to store received chunks by sequence number

    while True:
        try:
            # Receive message from the client
            message = client_socket.recv(buffer_size).decode()

            if not message:
                # Connection might have been closed
                print("Client disconnected.")
                break

            # Parse the sequence number and chunk from the message
            if message.startswith("M"):
                parts = message.split(":")
                if len(parts) == 2:
                    sequence_number = int(parts[0][1:])  # Extract sequence number
                    chunk = parts[1]  # Extract chunk data

                    # Store the chunk by sequence number
                    received_data[sequence_number] = chunk
                    print(f"Received chunk {sequence_number}: {chunk}")

                    # Send acknowledgment for the chunk
                    ack_message = f"ACK:{sequence_number}"
                    client_socket.send(ack_message.encode())
                    print(f"Sent acknowledgment: {ack_message}")
                else:
                    print(f"Invalid message format: {message}")
            else:
                print(f"Unexpected message: {message}")

        except socket.timeout:
            print("Timeout waiting for data.")
            break
        except Exception as e:
            print(f"Error occurred: {e}")
            break

    # Optionally, reconstruct the full message from received chunks
    complete_message = "".join(received_data[i] for i in sorted(received_data.keys()))
    print(f"Complete message received: {complete_message}")


if __name__ == "__main__":
    # Set the maximum allowed message size (e.g., 1024 bytes)
    max_message_size = 120
    start_server(max_message_size=max_message_size)

