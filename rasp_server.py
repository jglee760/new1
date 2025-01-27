# rasp_server.py
import socket
import threading
import sys
from typing import Optional
from led import LED

class RaspberryServer:
    def __init__(self, port: int):
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.led = LED()
        self.running = True
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(5)
            print(f"====== Raspberry Pi - Android Communication =======")
            print(f"Server started on port {self.port}")
            
            while self.running:
                print("Waiting for client connection...")
                self.client_socket, addr = self.server_socket.accept()
                print(f"Connected Client IP: {addr[0]}")
                print(f"Client Port Num: {addr[1]}\n")
                
                client_thread = threading.Thread(target=self.handle_client)
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.cleanup()
            
    def handle_client(self):
        try:
            while self.running:
                # Protocol packet is 15 bytes (2 STX + 4 obj_id + 4 data1 + 4 data2 + 1 ETX)
                data = self.client_socket.recv(15)
                if not data:
                    break
                    
                # Print received data in hexadecimal for debugging
                print("Received raw data:", ' '.join([f"{b:02x}" for b in data]))
                
                if len(data) != 15:
                    print(f"Invalid packet length: {len(data)}")
                    continue
                    
                # Check STX and ETX
                if data[0:2] != b'\xfd\xfe' or data[-1:] != b'\xff':
                    print("Invalid packet markers")
                    continue
                
                # Parse packet fields
                obj_id = int.from_bytes(data[2:6], byteorder='little')
                data1 = int.from_bytes(data[6:10], byteorder='little')
                data2 = int.from_bytes(data[10:14], byteorder='little')
                
                print(f"Parsed packet: obj_id={obj_id}, data1={data1}, data2={data2}")
                
                # Handle LED control (obj_id = 1 for LED)
                if obj_id == 1:
                    self.led.control_led(data1)
                    led_states = self.led.get_led_states()
                    print(f"LED states after change: {led_states}")
                    
        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
                
    def cleanup(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        self.led.gpio.cleanup()

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <port>")
        print(f"    ex) python {sys.argv[0]} 50002")
        sys.exit(1)
        
    port = int(sys.argv[1])
    server = RaspberryServer(port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server.cleanup()

if __name__ == "__main__":
    main()