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
            return data.get('message'), int(data.get('maximum_msg_size')), float(data.get('timeout'))
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

# def send_chunks(chunks, window_size, base, next_seq_num, client_socket):
#     """
#     Sends chunks within the current window.
#     """
#     while next_seq_num < base + window_size and next_seq_num < len(chunks):
#         try:
#             client_socket.sendall(chunks[next_seq_num].encode())  # Send the chunk
#             print(f"Sent chunk: {next_seq_num} -> {chunks[next_seq_num]}")
#             next_seq_num += 1
#         except socket.error as e:
#             print(f"Error sending chunk {next_seq_num}: {e}")
#             return next_seq_num, False  # Indicate a failure in sending
#
#     return next_seq_num, True  # Indicate successful sending
#
#
# def receive_acks(ack_received, base, timeout, client_socket):
#     """
#     Receives and processes acknowledgments from the client.
#     Ensures the sliding window moves correctly when the first chunk is acknowledged.
#     """
#     start_time = time.time()
#     while time.time() - start_time < timeout:
#         try:
#             ack_str = client_socket.recv(1024).decode().strip()
#             print(f"Received acknowledgment: {ack_str}")
#
#             # Parse acknowledgment
#             if ack_str.startswith("ACK:"):
#                 ack_num = int(ack_str.split(":")[-1])  # Extract ACK number
#
#                 # Mark the corresponding chunk as acknowledged
#                 if 0 <= ack_num < len(ack_received):
#                     ack_received[ack_num] = True
#                     print(f"ACK for chunk {ack_num} received.")
#
#                     # Slide the window base when the first unacknowledged chunk is acknowledged
#                     while base < len(ack_received) and ack_received[base]:
#                         base += 1
#                         print(f"Sliding window to base {base}.")
#
#                     # Break early if all chunks are acknowledged
#                     if base == len(ack_received):
#                         return base, True  # Transmission complete
#
#             else:
#                 print(f"Invalid ACK format: {ack_str}")
#         except socket.timeout:
#             print("Timeout waiting for acknowledgment.")
#             return base, False  # Indicate timeout
#
#     return base, False  # Indicate timeout if loop ends without success
#
#
# def ack_handler(chunks, window_size, timeout, client_socket):
#     """
#     Manages the entire sending and acknowledgment process with a sliding window.
#     """
#     ack_received = [False] * len(chunks)  # Track received ACKs
#     base = 0  # Base of the sliding window
#     next_seq_num = 0  # Next sequence number to be sent
#
#     client_socket.settimeout(timeout)  # Set timeout for receiving ACKs
#
#     while base < len(chunks):
#         # Send chunks within the window
#         next_seq_num, success = send_chunks(chunks, window_size, base, next_seq_num, client_socket)
#         if not success:
#             print("Failed to send chunks. Terminating transmission.")
#             return
#
#         # Wait for and process acknowledgments
#         base, success = receive_acks(ack_received, base, timeout, client_socket)
#         if not success:
#             print("Timeout occurred, resending unacknowledged chunks.")
#             next_seq_num = base  # Reset next_seq_num to the base for retransmission
#
#     print("All chunks sent and acknowledged successfully!")


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
            print(f"First ack received moving window by 1")
            window_base += 1
            window_moved = True
            sending_time = time.time()

        time_passed = time.time() - sending_time

        if timeout < time_passed:
            for i in range(window_base, min(window_base + window_size, len(chunks))):
                client_socket.sendall(chunks[i].encode())
                print(f"Timeout resending chunk {chunks[i]}")

                current_ack = ack_handler(client_socket)
                for ack in range(current_ack + 1):
                    ack_received[ack] = True
            sending_time = time.time()


def ack_handler(client_socket):
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
# def send_chunks(chunks, window_size, timeout, client_socket):
#
#
#     ack_received = [False] * len(chunks)  # Initialize ACK received list
#     base = 0  # Base of the sliding window
#     next_seq_num = 0  # Next sequence number to be sent
#
#     # Set socket timeout for receiving ACKs
#     client_socket.settimeout(timeout)
#
#     while base < len(chunks):
#         # Send all chunks within the window
#         while next_seq_num < base + window_size and next_seq_num < len(chunks):
#             try:
#                 print(chunks[next_seq_num])
#                 client_socket.sendall(chunks[next_seq_num].encode())  # Send the chunk
#                 print(f"Sent chunk: {next_seq_num}")
#                 next_seq_num += 1
#             except socket.error as e:
#                 print(f"Error sending chunk {next_seq_num}: {e}")
#                 return
#         # Start timer for the base chunk
#         start_time = time.time()
#
#         while True:
#             try:
#                 ack_str = client_socket.recv(1024).decode().strip()
#                 ack_num = int(ack_str.split(':')[-1])  # Extract number from ACK string
#                 ack_received[ack_num] = True  # Mark ACK as received
#
#                 # Slide window if the base is acknowledged
#                 while base < len(chunks) and ack_received[base]:
#                     base += 1
#
#                 if base == len(chunks):
#                     break  # Transmission complete
#
#             except socket.timeout:
#                 # Resend all chunks in the window if timeout
#                 if time.time() - start_time > timeout:
#                     next_seq_num = base
#                     break
#             except ValueError:
#                 print(f"Invalid ACK received: {ack_str}")  # Handle invalid ACK format



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

    # Close the socket when done
    client_socket.close()

