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

    #this sets the server settings from the client
    message = client_socket.recv(1024).decode()
    if message == "file":
        message = client_socket.recv(1024).decode()
        max_message_size = read_input_file(message)
    else:
        max_message_size = client_socket.recv(1024).decode()

    client_socket.sendall(max_message_size.encode())

    while message != "End":
        server_recive(client_socket, int(max_message_size))

        message = client_socket.recv(1024).decode()

    client_socket.close()


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
    acks = []
    needed_ack = 0
    skip_ack = 0
    while True:
        try:
            # Receive message from the client
            message = client_socket.recv(max_message_size + 10).decode()  # Buffer size adjusted for headers

            if not message:
                print("Client disconnected.")
                break

            if message == "done":
                print("End of message")
                break

            # Parse the sequence number and chunk from the message
            if message.startswith("M"):
                parts = message.split(":")
                if len(parts) == 2:
                    sequence_number = int(parts[0][1:])  # Extract sequence number (e.g., "M1")
                    chunk = parts[1]  # Extract chunk data

                    print(f"Received chunk {sequence_number}: {chunk}")
                    # Store the chunk by sequence number
                    if sequence_number not in received_data:  # Avoid overwriting
                        received_data[sequence_number] = chunk
                        acks.extend([False] * (sequence_number - len(acks) + 1))


                    if sequence_number  == needed_ack:
                        #needed_ack += 1

                        print(f"Sent acknowledgment: {needed_ack}")
                        ack_message = f"ACK{needed_ack}"
                        client_socket.sendall(ack_message.encode())
                        acks[needed_ack] = True

                        while needed_ack < len(received_data) and acks[needed_ack] is not False:
                            needed_ack += 1
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

    complete_message = "".join(received_data[i] for i in sorted(received_data.keys()))
    print(f"Complete message received: {complete_message}")



if __name__ == "__main__":
    # Set the maximum allowed message size (e.g., 1024 bytes)
    start_server()

