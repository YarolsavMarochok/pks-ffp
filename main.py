import threading
from config import initialize_sockets, PEER1_PORT, PEER2_PORT, PEER2_IP
from handshakes import three_way_handshake
from communication import receive_messages, send_messages, keep_alive_sender

# Initialize sockets
sock, send_sock = initialize_sockets()

# Perform three-way handshake
three_way_handshake(sock, send_sock)
 
# Start threads for sending and receiving
recv_thread = threading.Thread(target=receive_messages, args=(sock, send_sock))  # Pass send_sock
send_thread = threading.Thread(target=send_messages, args=(sock, send_sock, PEER1_PORT, PEER2_PORT))
keep_thread = threading.Thread(target=keep_alive_sender, args=(sock, 5, PEER2_IP, PEER2_PORT))

recv_thread.start()
send_thread.start()
keep_thread.start()

recv_thread.join()
send_thread.join()
keep_thread.join()

sock.close()
