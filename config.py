import socket

PEER2_IP = "127.0.0.1"
PEER1_PORT = int(input("Enter your port: "))
PEER2_PORT = int(input("Enter your friend's port: "))

def initialize_sockets():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    return sock, send_sock
