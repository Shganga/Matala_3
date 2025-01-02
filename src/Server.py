import socket

MAX_HEADER_SIZE = 10

def start_server():
    host = '127.0.0.1'
    port = 12345
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
    server_socket.bind((host, port))  # Bind to the specified host and port
    server_socket.listen(5)  # Listen for up to 5 connections
    print(f"Server listening on {host}:{port}")

    client_socket, client_address = server_socket.accept()  # Accept a client connection
    print(f"Connection established with {client_address}")

    message = client_socket.recv(1024).decode()
    if message == "file":
        message = client_socket.recv(1024).decode()
        max_message_size = read_input_file(message)
    else:
        max_message_size = client_socket.recv(1024).decode()

    client_socket.send(max_message_size.encode())

    server_recive(client_socket, int(max_message_size))

    client_socket.close()  # Close the connection

# Utility function to read input data from a file
def read_input_file(file_path):
    try:
        print(f"Attempting to open the file at: {file_path}")  # Debug: Check file path
        with open(file_path, 'r', encoding='utf-8') as file:  # Specify UTF-8 encoding
            data = {}
            for line in file:
                print(f"Reading line: {line}")  # Debug: Print each line
                if ':' not in line:
                    print(f"Skipping malformed line: {line}")  # Debug: Warn about malformed lines
                    continue  # Skip lines that don't contain a colon
                key, value = line.strip().split(':', 1)
                key = key.strip()
                value = value.strip().strip('"')
                data[key] = value
            return data.get('maximum_msg_size')
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except PermissionError:
        print(f"Error: Permission denied when accessing {file_path}.")
    except UnicodeDecodeError:
        print(f"Error: Could not decode the file with UTF-8 encoding.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
    return None  # In case of error, return None

def server_recive(client_socket : socket,max_message_size):
    received_data = {}  # Dictionary to store received chunks by sequence number

    while True:
        try:
            # Receive message from the client
            message = client_socket.recv(1024).decode()

            if not message:
                # Connection might have been closed
                print("Client disconnected.")
                break
            if message == "End":
                break
            else:
                message = client_socket.recv(max_message_size + MAX_HEADER_SIZE).decode()
                print(message)
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
    start_server()

