import socket
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
            return data
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except PermissionError:
        print(f"Error: Permission denied when accessing {file_path}.")
    except UnicodeDecodeError:
        print(f"Error: Could not decode the file with UTF-8 encoding.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
    return None  # In case of error, return None




def request_max_message_size(client_socket : socket, input_file=None):
    # Determine input source: user or file
    if input_file:
        # Read the maximum message size from the file
        data = read_input_file(input_file)
        request = data.get('message')
        print(f"Input from file: {data}")
    else:
        # Get user input
        request = "max_message_size"

    # Send the request to the server
    client_socket.send(request.encode())
    print(f"Request sent: {request}")

    # Receive the server's response
    response = client_socket.recv(1024).decode()  # Buffer size of 1024 bytes
    print(f"Response from server: {response}")

    return response #returns the size (in bytes) that the server can handle

# Send a window of chunks and wait for acknowledgment
def send_window(window_index, window, client_socket, window_size):
    print(f"Sending window {window_index + 1}...")

    # Send each chunk in the window with a sequence number
    for chunk_index, chunk in enumerate(window):
        sequence_number = window_index * window_size + chunk_index  # Sequence number for each chunk
        message = f"M{sequence_number}: {chunk}"  # Label the chunk with sequence number
        client_socket.send(message.encode())  # Send chunk over the socket
        print(f"Sent chunk {message}")

    # Wait for acknowledgment of the entire window (with timeout)
    try:
        ack = client_socket.recv(1024).decode()  # Receive acknowledgment (with timeout)
        if ack == "ACK":
            print(f"Window {window_index + 1} sent successfully.")
        else:
            print(f"Unexpected response for window {window_index + 1}: {ack}")
    except socket.timeout:
        print(f"Timeout waiting for acknowledgment for window {window_index + 1}. Retrying...")
        return False  # Indicating timeout occurred
    return True


# Main client function to send the message with sliding window
def client_send_message(client_socket: socket, max_size: int):
    while True:
        # asking if the client wants to send a file or text
        input_file = input("Do you want to send a file (yes/no) to logout ent 0: ")
        if input_file == "yes":
            input_file = input("Enter file path: ")

            data = read_input_file(input_file)

            if data is None:
                print("Error: The file could not be read or is empty. Exiting...")
                return  # Exit or handle error if data is None

            message = data.get('message')
            if message is None:
                print("Error: 'message' field is missing in the input file.")
                return  # Exit or handle error if 'message' is missing in the file

            # Safely get 'maximum_msg_size', default to 0 if missing or None
            maximum_msg_size = data.get('maximum_msg_size')

            if maximum_msg_size is None:
                print("Error: 'maximum_msg_size' is missing in the file. Exiting...")
                break  # Exit or handle the error appropriately
            else:
                maximum_msg_size = int(maximum_msg_size)  # Convert to int

            # If the message is bigger than the max size allowed by the server
            if maximum_msg_size > max_size:
                # Get window size and timeout from input file
                window_size = int(data.get('window_size'))
                timeout = int(data.get('timeout'))

                # Set timeout for the socket
                client_socket.settimeout(timeout)

                # Split the message into chunks based on max_size
                chunks = [message[i:i + max_size] for i in range(0, len(message), max_size)]

                # Split the chunks into windows based on window size
                windows = [chunks[i:i + window_size] for i in range(0, len(chunks), window_size)]

                # Send the windows with the sliding window protocol
                for window_index, window in enumerate(windows):
                    success = send_window(window_index, window, client_socket, window_size)
                    if not success:
                        print(f"Failed to send window {window_index + 1}. Retrying...")
                        # You can add retry logic here if needed
            else:
                # If the message fits within the max_size, just send it directly
                client_socket.send(message.encode())
                print(f"Sent message: {message}")

        elif input_file == "no":
            # Get user input if no input file
            request = input("Enter message to send: ")

            # Send the request to the server
            client_socket.send(request.encode())
            print(f"Request sent: {request}")

        #stops the loop and gets out of function
        elif input_file == "0":
            break
        else:
            print("incorrect input")


# Example usage of the client function
if __name__ == "__main__":
    # Set up the socket connection
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 12345))  # Connect to the server (localhost, port 12345)

    # Assume maximum message size specified by server is 20 bytes
    max_size = int(request_max_message_size(client_socket))


    client_send_message(client_socket, max_size)

    # Start sending the message from the client to the server

    # Close the socket when done
    client_socket.close()

