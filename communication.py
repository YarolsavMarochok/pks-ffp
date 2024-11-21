import socket
import struct
from handshakes import four_way_handshake
from socket_utilities import pack_message, checksum_calculator
from config import PEER1_PORT, PEER2_PORT, PEER2_IP
 
terminate = False
fourway_hs = 0

def parse_header(header_data):
    try:
        # Unpacking header assuming it has 4 integers (each 4 bytes)
        header = struct.unpack("!IIII", header_data[:16])  
        return header
    except Exception as e:
        print(f"Error parsing header: {e}")
        return None

def validate_checksum(message, expected_checksum):
    actual_checksum = checksum_calculator(message)
    if actual_checksum != expected_checksum:
        print("ERROR: Data corrupted")
        return False
    return True

def handle_message(message, sender_address, header):
    global terminate, fourway_hs

    # Handling "END" or "FIN" messages
    if message == "END":
        print("Received END, initiating four-way handshake")
        four_way_handshake(sender_address)
        terminate = True
    elif message == "FIN":
        print("Received FIN, responding with ACK")
        four_way_handshake(sender_address)
        terminate = True

    # Printing the message
    print(f"Received from {header[1]}: {message}")


def receive_messages(sock, send_sock):
    global terminate
    message_fragments = {}  # Store fragments for reassembly: {source: {seq: fragment}}

    while not terminate:
        try:
            full_packet, sender_address = sock.recvfrom(2048)
            header = struct.unpack("!IIIIII", full_packet[:24])
            message_fragment = full_packet[24:]

            sender_port = header[0]
            sequence_number = header[4]
            total_fragments = header[5]

            # Validate checksum
            checksum = checksum_calculator(message_fragment)
            if checksum != header[3]:
                print("ERROR: Data corrupted")
                continue

            print(f"Fragment {round(sequence_number + 1 / total_fragments)} content: {message_fragment.decode(errors='ignore')}")

            # Store fragment
            if sender_address not in message_fragments:
                message_fragments[sender_address] = {}
            message_fragments[sender_address][sequence_number] = message_fragment

            # Check if all fragments are received
            if len(message_fragments[sender_address]) == total_fragments:
                full_message = b"".join(
                    message_fragments[sender_address][i] for i in range(total_fragments)
                )
                print(f"Received complete message from {sender_port}: {full_message.decode()}")
                del message_fragments[sender_address]  # Clear stored fragments

        except socket.timeout:
            continue


# # Main function to receive messages
# def receive_messages(sock, send_sock):
#     global terminate, fourway_hs
#     while not terminate:
#         try:
#             # Receiving the packet
#             full_packet, sender_address = sock.recvfrom(1024)
#             header = parse_header(full_packet[:16])
            
#             if header is None:
#                 continue  # Skip this packet if the header parsing failed

#             message = full_packet[16:]

#             if not validate_checksum(message, header[3]):
#                 continue  # Skip this packet if checksum validation failed

#             message = message.decode()

#             handle_message(message, sender_address, header)
            
#         except socket.timeout:
#             continue

# Function to send messages
def send_messages(sock, send_sock, peer1_port, peer2_port):
        while True:
            try:
                message = input("\nEnter message: ").encode()
                fragments = pack_message(message, peer1_port, peer2_port)  # Get all fragments

                for fragment in fragments:
                    sock.sendto(fragment, (PEER2_IP, peer2_port))  # Send each fragment
                    print("Sent a fragment.")
                print(f"Sent entire message in {len(fragments)} fragment(s).")
            except Exception as e:
                print(f"Error while sending message: {e}")