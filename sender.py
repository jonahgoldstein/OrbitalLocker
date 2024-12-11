import time
import board
import busio
import digitalio
import adafruit_rfm9x

# Pin setup
CS_PIN = digitalio.DigitalInOut(board.CE1)
RESET_PIN = digitalio.DigitalInOut(board.D25)

# SPI interface
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialize RFM9x module
rfm96w = adafruit_rfm9x.RFM9x(spi, CS_PIN, RESET_PIN, 433.0)
rfm96w.tx_power = 23  # Max power for long-distance transmission

# Constants
CHUNK_SIZE = 248  # RFM9x payload limit
READY_MESSAGE = "READY_TO_SEND"
ACK_MESSAGE = "ACK"
EOF_MESSAGE = "END_OF_FILE"


def send_ready_signal(rfm):
    """Send the ready signal and wait for ACK."""
    print("Sending ready signal...")
    rfm.send(READY_MESSAGE.encode())

    # Wait for acknowledgment
    print("Waiting for receiver to acknowledge readiness...")
    start_time = time.time()
    while time.time() - start_time < 5:  # Wait up to 5 seconds for ACK
        ack = rfm.receive(timeout=1.0)
        if ack:
            try:
                if ack.decode("utf-8") == ACK_MESSAGE:
                    print("Receiver acknowledged readiness.")
                    return True
            except UnicodeDecodeError:
                print("Received malformed packet. Ignoring.")
    print("No acknowledgment received. Retrying...")
    return False


def send_image(rfm, image_path):
    """Send an image file in properly formatted chunks."""
    with open(image_path, "rb") as file:
        chunk_num = 0
        while True:
            # Read CHUNK_SIZE minus space for sequence number
            data_payload_size = CHUNK_SIZE - 4  # Reserve 4 bytes for the sequence number
            chunk = file.read(data_payload_size)
            if not chunk:
                break  # End of file

            # Create packet with sequence number
            sequence_number = f"{chunk_num:04d}".encode()  # 4-byte sequence number
            packet = sequence_number + chunk  # Full packet
            print(f"Packet {chunk_num} created: {packet[:20]}... (size: {len(packet)})")

            # Send packet
            print(f"Sending packet {chunk_num}...")
            rfm.send(packet)

            # Wait for acknowledgment
            while True:
                ack = rfm.receive(timeout=5.0)
                if ack:
                    try:
                        if ack.decode("utf-8") == ACK_MESSAGE:
                            print(f"Packet {chunk_num} acknowledged")
                            break
                    except UnicodeDecodeError:
                        print("Received malformed packet. Ignoring.")
                print("No ACK received. Resending packet {chunk_num}...")
                rfm.send(packet)

            chunk_num += 1
            time.sleep(0.1)  # Small delay to prevent overwhelming the receiver

    # Send EOF message
    print("Sending EOF...")
    rfm.send(EOF_MESSAGE.encode())
    while True:
        ack = rfm.receive(timeout=5.0)
        if ack:
            try:
                if ack.decode("utf-8") == ACK_MESSAGE:
                    print("EOF acknowledged. Transfer complete.")
                    break
            except UnicodeDecodeError:
                print("Received malformed packet. Ignoring.")
        print("No ACK for EOF. Resending...")
        rfm.send(EOF_MESSAGE.encode())


def main():
    image_path = "image.jpg"
    while True:
        if send_ready_signal(rfm96w):  # Keep sending ready signal until ACK is received
            send_image(rfm96w, image_path)
            break


if __name__ == "__main__":
    main()
