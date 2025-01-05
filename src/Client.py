import socket
import sys
import time

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
            if not data:
                print(f"Warning: The file {file_path} is empty or malformed.")
                return None  # Return None if no data was parsed

            return data.get('message'), int(data.get('window_size')), float(data.get('timeout'))

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except PermissionError:
        print(f"Error: Permission denied when accessing {file_path}.")
    except UnicodeDecodeError:
        print(f"Error: Could not decode the file with UTF-8 encoding.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
    return None  # In case of error, return None



def chunk_maker(message, max_message_size):
    chunks = []
    msg_bytes = message.encode()
    chunk_index = 0
    message_number = 0

    while chunk_index < len(msg_bytes):
        chunk_number = f"M{message_number}:"
        remaining_message = msg_bytes[chunk_index:]
        second_part_of_message = remaining_message[:max_message_size]

        while True:
            try:
                second_part_of_message_decoded = second_part_of_message.decode()
                break
            except UnicodeDecodeError:
                second_part_of_message = second_part_of_message[:-1]

        chunk = f"{chunk_number}{second_part_of_message_decoded}"
        chunks.append(chunk)

        chunk_index += len(second_part_of_message)
        message_number += 1

    print(chunks)

    return chunks


def send_chunks(chunks,window_size, timeout, client_socket):
    ack_received = [False] * len(chunks)  # Initialize ACK received list
    window_moved = True
    window_base = 0
    sending_time = time.time()

    while window_base < len(chunks):
        if window_moved:
            for i in range(window_base, min(window_base + window_size, len(chunks))):
                if not ack_received[i]:
                    client_socket.sendall(chunks[i].encode())
                    print(f"Sent: {chunks[i]} to server")


                current_ack = ack_handler(client_socket)
                if current_ack is not None and current_ack < len(chunks):
                    ack_received[current_ack] = True

        window_moved = False

        while window_base < len(chunks) and ack_received[window_base]:
            print(f"ack number {window_base} received moving window by 1")
            window_base += 1
            window_moved = True
            sending_time = time.time()

        time_passed = time.time() - sending_time

        if timeout < time_passed:
            print(f"Timeout, resending window")
            for i in range(window_base, min(window_base + window_size, len(chunks))):
                print(chunks[i])
                client_socket.sendall(chunks[i].encode())

                current_ack = ack_handler(client_socket)
                if current_ack is not None and current_ack < len(chunks):
                    for ack in range(current_ack + 1):
                        ack_received[ack] = True
            sending_time = time.time()



    client_socket.sendall("done".encode())



def ack_get_and_send(client_socket):
    try:
        client_socket.settimeout(1)
        ack = client_socket.recv(1024).decode()
        if ack.startswith("ACK"):
            ack = int(ack[3:])
            print(f"ACK {ack} received")
            return ack
        else:
            print(f"{ack} Unexpected response")
            return None
    except socket.timeout:
        print("Timeout while waiting for ack")
        return None
    except  (ValueError, SyntaxError):
        print("got an invalid Ack response")
    finally:
        client_socket.settimeout(None)



# Main client function to send the message with sliding window
def client(client_socket: socket):

    while True:
        data = input("Do you want to send a file to set the server settings? (yes/no)")
        if data == 'no':
            client_socket.send("no".encode())
            client_socket.send(input("What is the maximum message size? ").encode())
            max_size = int(client_socket.recv(1024).decode().strip())
            window_size = int(input("What is the the window size?"))
            timeout = int(input("What is the timeout?"))
            break

        elif data == 'yes':
            client_socket.send("file".encode())
            input_file = input("Enter the file path: ")
            client_socket.send(input_file.encode())
            max_size = int(client_socket.recv(1024).decode().strip())
            message, window_size, timeout = read_input_file(input_file)
            break
        else:
            print("invalid input")


    while True:
        # asking if the client wants to send a file or text

        input_file = input("Do you want to continue? (yes/no): ")
        if input_file == 'no':
            client_socket.send("End".encode())
            break

        input_file = input("Do you want to send a file? (yes/no): ")

        if input_file == "yes":
            input_file = input("Enter file path: ")

            message = read_input_file(input_file)[0]
            if message is None:
                print("Error: The file could not be read or is empty. Exiting...")
                return  # Exit or handle error if data is None


            chunks = chunk_maker(message, max_size)

            #ack_handler(chunks, window_size, timeout, client_socket)
            send_chunks(chunks, window_size, timeout, client_socket)

        elif input_file == "no":
            # Get user input if no input file
            message = input("Enter message to send: ")

            # Send the message to the server
            client_socket.send(message.encode())
            print(f"Message sent: {message}")

            chunks = chunk_maker(message, max_size)

            send_chunks(chunks, window_size, timeout, client_socket)

        else:
            print("incorrect input")


# Example usage of the client function
if __name__ == "__main__":
    # Set up the socket connection
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 12345))  # Connect to the server (localhost, port 12345)

    client(client_socket)

    # Start sending the message from the client to the server

