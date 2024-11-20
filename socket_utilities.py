import struct
import zlib

def checksum_calculator(data):
    """Generate checksum for the given data."""
    return zlib.crc32(data)

def pack_message(message, sender_port, receiver_port):
    """Pack message with protocol header."""
    header = struct.pack("!IIII", sender_port, receiver_port, len(message), checksum_calculator(message))
    return header + message
