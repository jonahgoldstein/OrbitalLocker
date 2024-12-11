import time
import board
import busio
import digitalio
import adafruit_rfm9x

# Pin setup
CS_PIN = digitalio.DigitalInOut(board.D16)
RESET_PIN = digitalio.DigitalInOut(board.D25)

# SPI interface
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialize RFM9x module
rfm96w = adafruit_rfm9x.RFM9x(spi, CS_PIN, RESET_PIN, 433.0)
rfm96w.tx_power = 23  # Max power for long-distance transmission

# Constants
READY_MESSAGE = "READY_TO_SEND"
ACK_MESSAGE = "ACK"
EOF_MESSAGE = "END_"
CHUNK_SIZE = 248

def receive_packets(rfm):
    """Receive packets and save data to a file."""
    received_data = bytearray()
    print("Waiting for packets...")
    
    while True:
        packet = rfm.receive(timeout=5.0)
        if packet:
            try:
                # Extract sequence number and chunk
                sequence_number = packet[:4].decode("utf-8")  # First 4 bytes
                data_chunk = packet[4:]  # Remaining bytes
                print(f"Received packet {sequence_number}: size={len(data_chunk)} bytes")

                # Acknowledge packet
                rfm.send(ACK_MESSAGE.encode())
                print(f"Acknowledged packet {sequence_number}")

                # Check for EOF message
                if sequence_number == "END_":
                    print("End of file received.")
                    break

                # Add chunk to collected data
                received_data.extend(data_chunk)

            except UnicodeDecodeError:
                print("Malformed packet received. Ignoring.")

        else:
            print("No packet received. Waiting...")

    # Save the collected data to a file
    with open("received_image.jpg", "wb") as file:
        file.write(received_data)
    print("File saved as 'received_image.jpg'")


def send_ack_ready(rfm):
    """Send ACK for readiness."""
    while True:
        packet = rfm.receive(timeout=1.0)
        if packet:
            try:
                message = packet.decode("utf-8")
                if message == READY_MESSAGE:
                    print("Ready signal received from sender.")
                    rfm.send(ACK_MESSAGE.encode())
                    print("Acknowledged sender readiness.")
                    return
            except UnicodeDecodeError:
                print("Malformed packet received. Ignoring.")


def main():
    send_ack_ready(rfm96w)
    start_time = time.time()
    receive_packets(rfm96w)
    end_time = time.time()
    print("Elapsed time: " + str(start_time - end_time))


if __name__ == "__main__":
    main()
