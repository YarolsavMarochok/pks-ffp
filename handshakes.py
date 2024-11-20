import socket  # Ensure socket is imported
import struct
import zlib
from config import PEER1_PORT, PEER2_IP, PEER2_PORT
from socket_utilities import pack_message

def three_way_handshake(sock, send_sock):
    """Perform the three-way handshake process."""
    from config import PEER1_PORT, PEER2_IP, PEER2_PORT
    sock.bind(('', PEER1_PORT))
    role = 0
    state = 'INIT'

    print("Initiating three-way handshake")
    send_sock.sendto(b"SYN_1", (PEER2_IP, PEER2_PORT))
    print("First SYN was sent")

    while state != 'CONNECTED':
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8')
            print(f"Received message: {message} from {addr}")

            if state == 'INIT' and message == 'SYN_1':
                role = 1
                print("SYN_1 received, sending SYN_ACK")
                send_sock.sendto(b"SYN_ACK", (PEER2_IP, PEER2_PORT))
                state = 'SYN_RECEIVED'

            elif state == 'SYN_RECEIVED' and message == 'ACK':
                print("Received ACK, connection established as responder")
                state = 'CONNECTED'

            elif state == 'INIT' and message == 'SYN_ACK':
                print("Received SYN_ACK, sending ACK")
                send_sock.sendto(b"ACK", (PEER2_IP, PEER2_PORT))
                state = 'CONNECTED'

        except socket.timeout:  # Correctly handles the timeout exception
            if state == 'INIT' and role == 0:
                print("Resending SYN_1 (no response)")
                send_sock.sendto(b"SYN_1", (PEER2_IP, PEER2_PORT))
            elif state == 'SYN_RECEIVED':
                print("Waiting for ACK...")

    print("Connection established, exiting handshake process.")

def four_way_handshake(sock, send_sock):
    """Perform the four-way handshake to terminate the connection."""
    print("Initiating four-way handshake...")
    send_sock.sendto(pack_message(b"FIN", PEER1_PORT, PEER2_PORT), (PEER2_IP, PEER2_PORT))
    print("Sent FIN")

    state = 0
    while state < 2:
        try:
            full_packet, sender_address = sock.recvfrom(1024)
            header = struct.unpack("!IIII", full_packet[:16])
            message = full_packet[16:].decode()

            if state == 0 and message == "FIN":
                print("Received FIN from peer, sending ACK")
                sock.sendto(pack_message(b"ACK", PEER1_PORT, PEER2_PORT), sender_address)
                state = 1
            elif state == 1 and message == "ACK":
                print("Received final ACK, connection terminated")
                state = 2

        except socket.timeout:
            print("Timeout during four-way handshake, retrying...")
            send_sock.sendto(pack_message(b"FIN", PEER1_PORT, PEER2_PORT), (PEER2_IP, PEER2_PORT))

    print("Four-way handshake completed.")
