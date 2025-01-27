# rasp_server.py
import socket
import threading
import sys
import time
import select
import signal
from typing import Optional
from led import LED

class RaspberryServer:
    def __init__(self, port: int):
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.led = LED()
        self.running = True
        self.client_address = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle termination signals"""
        print("\nReceived termination signal. Shutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
            
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Set socket timeout
        self.server_socket.settimeout(1.0)
        
        try:
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(5)
            print(f"====== Raspberry Pi - Android Communication =======")
            print(f"Server started on port {self.port}")
            print("Press Ctrl+C to stop the server")
            
            while self.running:
                try:
                    # Accept with timeout
                    self.client_socket, self.client_address = self.server_socket.accept()
                    print(f"\nConnected Client IP: {self.client_address[0]}")
                    print(f"Client Port Num: {self.client_address[1]}")
                    
                    self.handle_client_connection()
                    
                except socket.timeout:
                    # Check if we should continue running
                    continue
                except socket.error as e:
                    if self.running:
                        print(f"Socket accept error: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            if self.running:
                print(f"Server error: {e}")
        finally:
            self.cleanup()
            
    def handle_client_connection(self):
        """Handle a single client connection"""
        if not self.client_socket:
            return
            
        # Set client socket timeout
        self.client_socket.settimeout(1.0)
        buffer = bytearray()
        packet_size = 15
        
        while self.running:
            try:
                ready = select.select([self.client_socket], [], [], 1.0)
                if ready[0]:
                    data = self.client_socket.recv(packet_size)
                    if not data:
                        print("Client disconnected")
                        break
                    
                    buffer.extend(data)
                    
                    while len(buffer) >= packet_size:
                        packet = buffer[:packet_size]
                        buffer = buffer[packet_size:]
                        self.process_packet(packet)
                        
            except socket.timeout:
                continue
            except socket.error as e:
                if self.running:
                    print(f"Socket error while receiving data: {e}")
                break
        
        self.close_client()
    
    def process_packet(self, packet_data: bytes):
        """Process a single packet"""
        try:
            if not self.running:
                return
                
            print("Processing packet:", ' '.join([f"{b:02x}" for b in packet_data]))
            
            if packet_data[0:2] != b'\xfd\xfe' or packet_data[-1:] != b'\xff':
                print("Invalid packet markers")
                return
            
            obj_id = int.from_bytes(packet_data[2:6], byteorder='little')
            data1 = int.from_bytes(packet_data[6:10], byteorder='little')
            data2 = int.from_bytes(packet_data[10:14], byteorder='little')
            
            print(f"Parsed packet: obj_id={obj_id}, data1={data1}, data2={data2}")
            
            if obj_id == 1:
                self.led.control_led(data1)
                led_states = self.led.get_led_states()
                print(f"LED states after change: {led_states}")
                
        except Exception as e:
            if self.running:
                print(f"Error processing packet: {e}")
                
    def close_client(self):
        """Close the current client connection"""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            self.client_address = None
            if self.running:
                print("Client connection closed")
                
    def cleanup(self):
        """Clean up server resources"""
        print("\nCleaning up server...")
        self.running = False
        
        # Close client socket
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        # Cleanup GPIO
        try:
            self.led.gpio.cleanup()
        except:
            pass
            
        print("Server cleanup completed")

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
        sys.exit(0)

if __name__ == "__main__":
    main()