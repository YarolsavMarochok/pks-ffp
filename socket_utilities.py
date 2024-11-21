import os
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
            "!IIIIIII",
            peer1_port,          # Sender port
            peer2_port,          # Receiver port
            message_length,      # Payload length
            checksum,            # CRC32 checksum
            0,                   # Sequence number (0 for single fragment)
            1,                    # Total fragments (1 since there's no fragmentation)
            0
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
        file_indicator = 0  # 1 means file (0 would mean text message)
        header = struct.pack(
            "!IIIIIII",
            peer1_port,               # Sender port
            peer2_port,               # Receiver port
            len(fragment_payload),    # Payload length
            checksum,                 # CRC32 checksum
            sequence_number,          # Fragment sequence number
            total_fragments,           # Total fragments
            file_indicator
        )

        # Append the fragment (header + payload)
        fragments.append(header + fragment_payload)

    return fragments

def pack_file(file_path, peer1_port, peer2_port):
    MAX_FRAGMENT_SIZE = 1400  # Maximum size for each fragment payload
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: The file '{file_path}' does not exist.")
        
        file_size = os.path.getsize(file_path)  # Get the size of the file
        total_fragments = (file_size + MAX_FRAGMENT_SIZE - 1) // MAX_FRAGMENT_SIZE  # Calculate total fragments


        # Extract the file name and extension
        file_name, file_extension = os.path.splitext(os.path.basename(file_path))
        file_name = file_name.encode()  # Convert to bytes
        file_extension = file_extension.encode()  # Convert to bytes

        with open(file_path, 'rb') as file:
            file_data = file.read(MAX_FRAGMENT_SIZE)  # Read first chunk
            fragment_number = 0
            fragments = []

            # Prepare a header to indicate that this is a file
            while file_data:
                # Compute checksum for this fragment
                checksum = checksum_calculator(file_data)

                # Pack the header
                header = struct.pack(
                    "!IIIIIII",  # Format for 6 integers
                    peer1_port,               # Sender port
                    peer2_port,               # Receiver port
                    len(file_data),           # Payload length
                    checksum,                 # CRC32 checksum
                    fragment_number,          # Fragment sequence number
                    total_fragments,           # Total fragments
                    1
                )

                header += struct.pack("!H", len(file_name))  # Length of the file name
                header += struct.pack(f"!{len(file_name)}s", file_name)  # File name
                header += struct.pack("!H", len(file_extension))  # Length of the file extension
                header += struct.pack(f"!{len(file_extension)}s", file_extension)  # File extension

                # # Add a file indicator to distinguish file fragments from message fragments
                # header += struct.pack("!I", file_indicator)

                # Append the fragment (header + payload)
                fragments.append(header + file_data)
                print(f"Preparing fragment {fragment_number + 1}/{total_fragments}")

                # Read the next fragment
                fragment_number += 1
                file_data = file.read(MAX_FRAGMENT_SIZE)
        
        print("File has been fragmented successfully!")
        return fragments

    except FileNotFoundError as e:
        print(e)
        return []
    except Exception as e:
        print(f"Error while packing the file: {e}")
        return []