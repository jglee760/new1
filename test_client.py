# test_client.py
import socket
import sys
import time
import select
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
        self.connected = False
        self.running = True

    def connect(self):
        try:
            if self.socket:
                self.socket.close()
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 second timeout
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to server at {self.host}:{self.port}")
            time.sleep(0.5)  # Wait for connection to stabilize
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.connected = False
            return False

    def reconnect(self, max_attempts=3):
        print("Attempting to reconnect...")
        for attempt in range(max_attempts):
            print(f"Reconnection attempt {attempt + 1}/{max_attempts}")
            self.close()
            time.sleep(1)
            if self.connect():
                time.sleep(0.5)  # Wait for connection to stabilize
                return True
        return False

    def send_led_control(self, led_pattern: int, retry_on_fail=True) -> bool:
        if not self.connected:
            print("Not connected to server")
            if retry_on_fail and self.reconnect():
                return self.send_led_control(led_pattern, retry_on_fail=False)
            return False

        packet = ProtocolPacket(
            obj_id=1,  # 1 is LED object ID
            data1=led_pattern,
            data2=0
        )
        
        try:
            data = packet.pack()
            print(f"Sending LED control packet: pattern={bin(led_pattern)}")
            print("Raw data:", ' '.join([f"{b:02x}" for b in data]))
            
            # Send the packet
            bytes_sent = self.socket.send(data)
            if bytes_sent != len(data):
                raise socket.error("Failed to send complete packet")
            
            # Wait briefly for the packet to be processed
            time.sleep(0.2)
            
            # Check if the socket is still connected
            try:
                ready = select.select([self.socket], [], [], 0.1)
                if ready[0]:
                    check_data = self.socket.recv(1, socket.MSG_PEEK)
                    if not check_data:
                        raise socket.error("Connection lost")
            except socket.error:
                if retry_on_fail:
                    print("Connection seems lost, attempting to reconnect...")
                    if self.reconnect():
                        return self.send_led_control(led_pattern, retry_on_fail=False)
                return False
                
            return True
            
        except socket.error as e:
            print(f"Failed to send packet: {e}")
            self.connected = False
            if retry_on_fail and self.reconnect():
                return self.send_led_control(led_pattern, retry_on_fail=False)
            return False

    def close(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False
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
        if not client.send_led_control(pattern):
            print(f"Failed to execute {description}")
            return False
        time.sleep(0.5)  # Wait between patterns
        
    print("\nTest sequence completed successfully")
    return True

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
            while client.running:
                print("\nTest Menu:")
                print("1. Run automatic LED test sequence")
                print("2. Control LED1")
                print("3. Control LED2")
                print("4. Control both LEDs")
                print("5. Turn off all LEDs")
                print("6. Reconnect to server")
                print("7. Exit")
                
                try:
                    choice = input("\nEnter your choice (1-7): ")
                except EOFError:
                    break
                
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
                    client.reconnect()
                elif choice == '7':
                    break
                else:
                    print("Invalid choice. Please try again.")
                
                time.sleep(0.1)
                    
    except KeyboardInterrupt:
        print("\nTest client shutting down...")
    finally:
        client.close()

if __name__ == "__main__":
    main()