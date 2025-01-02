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
            return data.get('message'), int(data.get('maximum_msg_size')), int(data.get('timeout'))
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


def send_chunks(chunks, window_size, timeout, client_socket):

    ack_received = [False] * len(chunks)  # Initialize ACK received list
    base = 0  # Base of the sliding window
    next_seq_num = 0  # Next sequence number to be sent

    # Set socket timeout for receiving ACKs
    client_socket.settimeout(timeout)

    while base < len(chunks):
        # Send all chunks within the window
        while next_seq_num < base + window_size and next_seq_num < len(chunks):
            try:
                print(chunks[next_seq_num])
                client_socket.sendall(chunks[next_seq_num].encode())  # Send the chunk
                print(f"Sent chunk: {next_seq_num}")
                next_seq_num += 1
            except socket.error as e:
                print(f"Error sending chunk {next_seq_num}: {e}")
                return
        # Start timer for the base chunk
        start_time = time.time()

        while True:
            try:
                ack_str = client_socket.recv(1024).decode().strip()
                ack_num = int(ack_str.split(':')[-1])  # Extract number from ACK string
                ack_received[ack_num] = True  # Mark ACK as received

                # Slide window if the base is acknowledged
                while base < len(chunks) and ack_received[base]:
                    base += 1

                if base == len(chunks):
                    break  # Transmission complete

            except socket.timeout:
                # Resend all chunks in the window if timeout
                if time.time() - start_time > timeout:
                    next_seq_num = base
                    break
            except ValueError:
                print(f"Invalid ACK received: {ack_str}")  # Handle invalid ACK format



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
            client_socket.send("no".encode())
            break

        input_file = input("Do you want to send a file? (yes/no): ")

        if input_file == "yes":
            input_file = input("Enter file path: ")

            message = read_input_file(input_file)[0]
            if message is None:
                print("Error: The file could not be read or is empty. Exiting...")
                return  # Exit or handle error if data is None


            chunks = chunk_maker(message, max_size)

            send_chunks(chunks, window_size, timeout, client_socket)

        elif input_file == "no":
            # Get user input if no input file
            request = input("Enter message to send: ")

            # Send the request to the server
            client_socket.send(request.encode())
            print(f"Request sent: {request}")

        else:
            print("incorrect input")


# Example usage of the client function
if __name__ == "__main__":
    # Set up the socket connection
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 12345))  # Connect to the server (localhost, port 12345)

    client(client_socket)

    # Start sending the message from the client to the server

    # Close the socket when done
    client_socket.close()

