import socket
import struct
import time
from handshakes import four_way_handshake
from socket_utilities import pack_message, pack_file, checksum_calculator
from config import PEER1_PORT, PEER2_PORT, PEER2_IP
import os

terminate = False
ack_received = False
fourway_hs = 0
received_ack = set()


# def parse_header(header_data):
#     try:
#         # Unpacking header assuming it has 4 integers (each 4 bytes)
#         header = struct.unpack("!IIII", header_data[:16])  
#         return header
#     except Exception as e:
#         print(f"Error parsing header: {e}")
#         return None

# def validate_checksum(message, expected_checksum):
#     actual_checksum = checksum_calculator(message)
#     if actual_checksum != expected_checksum:
#         print("ERROR: Data corrupted")
#         return False
#     return True

# def handle_message(message, sender_address, header):
#     global terminate, fourway_hs

#     # Handling "END" or "FIN" messages
#     if message == "END":
#         print("Received END, initiating four-way handshake")
#         four_way_handshake(sender_address)
#         terminate = True
#     elif message == "FIN":
#         print("Received FIN, responding with ACK")
#         four_way_handshake(sender_address)
#         terminate = True

#     # Printing the message
#     print(f"Received from {header[1]}: {message}")


def receive_messages(sock, send_sock):
    global terminate, ack_received, received_ack
    message_fragments = {}

    while not terminate:
        try:
            full_packet, sender_address = sock.recvfrom(2048)

            # Handle ACKs
            if len(full_packet) == 4:
                ack_seq = struct.unpack("!I", full_packet)[0]
                received_ack.add(ack_seq)
                ack_received = True
                print(f"ACK received for fragment {ack_seq + 1}")
                continue



            header = struct.unpack("!IIIIIII", full_packet[:28])

            sender_port = header[0]
            sequence_number = header[4]
            total_fragments = header[5]
            file_indicator = header[6]

            if file_indicator == 1:
                name_len = struct.unpack("!H", full_packet[28:30])[0]
                file_name = struct.unpack(f"!{name_len}s", full_packet[30:30+name_len])[0].decode()
                ext_len = struct.unpack("!H", full_packet[30+name_len:32+name_len])[0]
                file_extension = struct.unpack(f"!{ext_len}s", full_packet[32+name_len:32+name_len+ext_len])[0].decode()

                message_fragment = full_packet[32 + name_len + ext_len:]
            else:
                message_fragment = full_packet[28:]


            # Validate checksum
            checksum = checksum_calculator(message_fragment)
            if checksum != header[3]:
                print("ERROR: Data corrupted")
                continue

            print("Good fragment was received!")
            ack_packet = struct.pack("!I", sequence_number)
            send_sock.sendto(ack_packet, sender_address)
            print(f"ACK sent for fragment {sequence_number + 1}")

            # Store fragment
            if sender_address not in message_fragments:
                message_fragments[sender_address] = {}
            message_fragments[sender_address][sequence_number] = message_fragment

            print(f"Received fragment {sequence_number + 1}/{total_fragments} from {sender_port}")

            if file_indicator == 0:
                
                print(f"Fragment {round(sequence_number + 1 / total_fragments)} content: {message_fragment.decode(errors='ignore')}")

                # Check if all fragments are received
                if len(message_fragments[sender_address]) == total_fragments:
                    full_message = b"".join(
                        message_fragments[sender_address][i] for i in range(total_fragments)
                    )
                    print(f"Received complete message from {sender_port}: {full_message.decode()}")
                    del message_fragments[sender_address]  # Clear stored fragments
            
            elif file_indicator == 1:
                print("Checking on all fragments!")
                # Checking if all fragments are received
                if len(message_fragments[sender_address]) == total_fragments:
                    print(f"All fragments received. Total: {total_fragments}")  # Debugging line

                    # Ensure fragments are in order
                    full_file_data = b"".join(
                        message_fragments[sender_address][i] for i in range(total_fragments)
                    )

                    # Save the reassembled file
                    output_file = f"{file_name}{file_extension}" 

                    if os.path.exists(output_file):
                        print(f"File '{output_file}' already exists.")
                        response = input(f"Do you want to overwrite it? (y/n): ").strip().lower()
                        if response == 'y':
                            with open(output_file, 'wb') as file:
                                file.write(full_file_data)
                            print(f"File overwritten and saved as {output_file}")
                        else:
                            new_name = input(f"Enter a new name for the file (default: {file_name}_new{file_extension}): ").strip()
                            if not new_name:
                                new_name = f"{file_name}_new{file_extension}"
                            with open(new_name, 'wb') as file:
                                file.write(full_file_data)
                            print(f"File saved as {new_name}")
                    else:
                        with open(output_file, 'wb') as file:
                            file.write(full_file_data)
                        print(f"File received and saved as {output_file}")

                    # Clear stored fragments for this sender
                    del message_fragments[sender_address]  # Clear stored fragments
                else:
                    print(f"Waiting for more fragments... Current count: {len(message_fragments[sender_address])} / {total_fragments}")

                    # del message_fragments[sender_address]  # Clear stored fragments

        except socket.timeout:
            continue

WINDOW_SIZE = 256  # Adjustable as per requirement

def send_messages(sock, send_sock, peer1_port, peer2_port):
    global ack_received
    while True:
        try:
            user_input = input("Enter /file to send a file or /message to send a text message: ").strip().lower()

            if user_input == "/file":
                # Ask for the file path
                file_path = input("Enter the file path to send: ").strip()
                fragments = pack_file(file_path, peer1_port, peer2_port)

                if not fragments:
                    print("No fragments were generated. Please check the file path.")
                    continue

            elif user_input == "/message":
                message = input("Enter your message: ").encode()
                fragments = pack_message(message, peer1_port, peer2_port)  # Get all fragments for message

            else:
                print("Invalid input. Please enter /file or /message.")
                continue

            # Sliding window logic
            base = 0
            next_seq_num = 0
            sent_time = {}

            while base < len(fragments):
                # Send packets within the window
                while next_seq_num < base + WINDOW_SIZE and next_seq_num < len(fragments):
                    sock.sendto(fragments[next_seq_num], (PEER2_IP, peer2_port))
                    sent_time[next_seq_num] = time.time()
                    print(f"Sent fragment {next_seq_num + 1}")
                    next_seq_num += 1

                # Wait for ACKs and handle retransmissions
                while base < next_seq_num:
                    if base in received_ack:
                        print(f"ACK received for fragment {base + 1}")
                        base += 1  # Slide the window forward
                    else:
                        # Check for timeout
                        current_time = time.time()
                        for seq_num in range(base, next_seq_num):
                            if current_time - sent_time[seq_num] > 1.0:  # Timeout
                                print(f"Timeout: Resending fragment {seq_num + 1}")
                                sock.sendto(fragments[seq_num], (PEER2_IP, peer2_port))
                                sent_time[seq_num] = time.time()
                    
                    time.sleep(0.01)  # Small delay to reduce CPU usage
            received_ack.clear()
            print(f"Sent entire data in {len(fragments)} fragment(s).")

        except Exception as e:
            print(f"Error while sending: {e}")