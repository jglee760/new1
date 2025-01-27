# test_client.py
import socket
import sys
import time
from dataclasses import dataclass
import struct

@dataclass
class ProtocolPacket:
    STX: bytes = b'\xfd\xfe'
    obj_id: int = 0
    data1: int = 0
    data2: int = 0
    ETX: bytes = b'\xff'
    
    def pack(self) -> bytes:
        return struct.pack('<2sIIIc', self.STX, self.obj_id, self.data1, self.data2, self.ETX)

class TestClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def send_led_control(self, led_pattern: int):
        """
        Send LED control packet
        led_pattern: binary pattern for LED control (e.g., 0b01 for LED1, 0b10 for LED2, 0b11 for both)
        """
        packet = ProtocolPacket(
            obj_id=1,  # 1 is LED object ID
            data1=led_pattern,
            data2=0
        )
        try:
            self.socket.send(packet.pack())
            print(f"Sent LED control packet: pattern={bin(led_pattern)}")
        except Exception as e:
            print(f"Failed to send packet: {e}")

    def close(self):
        if self.socket:
            self.socket.close()
            print("Connection closed")

def led_test_sequence(client: TestClient):
    """Run a test sequence for LED control"""
    test_patterns = [
        (0b00, "All LEDs OFF"),
        (0b01, "LED1 ON"),
        (0b10, "LED2 ON"),
        (0b11, "Both LEDs ON"),
    ]

    for pattern, description in test_patterns:
        print(f"\nTesting: {description}")
        client.send_led_control(pattern)
        time.sleep(2)  # Wait 2 seconds between patterns

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        print(f"    ex) python {sys.argv[0]} localhost 50002")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    
    client = TestClient(host, port)
    
    try:
        if client.connect():
            print("\nStarting LED test sequence...")
            while True:
                print("\nTest Menu:")
                print("1. Run automatic LED test sequence")
                print("2. Control LED1")
                print("3. Control LED2")
                print("4. Control both LEDs")
                print("5. Turn off all LEDs")
                print("6. Exit")
                
                choice = input("\nEnter your choice (1-6): ")
                
                if choice == '1':
                    led_test_sequence(client)
                elif choice == '2':
                    client.send_led_control(0b01)
                elif choice == '3':
                    client.send_led_control(0b10)
                elif choice == '4':
                    client.send_led_control(0b11)
                elif choice == '5':
                    client.send_led_control(0b00)
                elif choice == '6':
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
    except KeyboardInterrupt:
        print("\nTest client shutting down...")
    finally:
        client.close()

if __name__ == "__main__":
    main()