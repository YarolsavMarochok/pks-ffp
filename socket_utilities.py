import struct
import zlib

def checksum_calculator(data):
    """Generate checksum for the given data."""
    return zlib.crc32(data)

def pack_message(message, peer1_port, peer2_port):
    MAX_FRAGMENT_SIZE = 64  # Maximum size for each fragment payload
    message_length = len(message)

    # If message fits within one packet, no fragmentation needed
    if message_length <= MAX_FRAGMENT_SIZE:
        checksum = checksum_calculator(message)
        header = struct.pack(
            "!IIIIII",
            peer1_port,          # Sender port
            peer2_port,          # Receiver port
            message_length,      # Payload length
            checksum,            # CRC32 checksum
            0,                   # Sequence number (0 for single fragment)
            1                    # Total fragments (1 since there's no fragmentation)
        )
        return [header + message]  # Return a list with one packet

    # Otherwise, fragment the message
    fragments = []
    total_fragments = (message_length + MAX_FRAGMENT_SIZE - 1) // MAX_FRAGMENT_SIZE  # Calculate total fragments

    for sequence_number in range(total_fragments):
        # Slice the message into fragments
        fragment_start = sequence_number * MAX_FRAGMENT_SIZE
        fragment_end = fragment_start + MAX_FRAGMENT_SIZE
        fragment_payload = message[fragment_start:fragment_end]

        # Compute checksum for this fragment
        checksum = checksum_calculator(fragment_payload)

        # Pack the header
        header = struct.pack(
            "!IIIIII",
            peer1_port,               # Sender port
            peer2_port,               # Receiver port
            len(fragment_payload),    # Payload length
            checksum,                 # CRC32 checksum
            sequence_number,          # Fragment sequence number
            total_fragments           # Total fragments
        )

        # Append the fragment (header + payload)
        fragments.append(header + fragment_payload)

    return fragments
