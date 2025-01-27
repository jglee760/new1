# websocket_server.py
import asyncio
import websockets
import signal
from led import LED

class WebSocketServer:
    def __init__(self, host='localhost', port=50002):
        self.host = host
        self.port = port
        self.led = LED()
        self.running = True
        self.server = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle termination signals"""
        print("\nReceived termination signal. Shutting down...")
        self.running = False
        self.cleanup()
    
    async def handle_client(self, websocket, path):
        """Handle client connection"""
        print(f"Client connected from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                if not self.running:
                    break
                    
                try:
                    # Verify packet format
                    if len(message) != 15:
                        print(f"Invalid packet length: {len(message)}")
                        continue
                    
                    # Convert bytes to integers
                    data = bytearray(message)
                    
                    # Check STX and ETX
                    if data[0:2] != b'\xfd\xfe' or data[-1:] != b'\xff':
                        print("Invalid packet markers")
                        continue
                    
                    # Parse packet fields
                    obj_id = int.from_bytes(data[2:6], byteorder='little')
                    data1 = int.from_bytes(data[6:10], byteorder='little')
                    data2 = int.from_bytes(data[10:14], byteorder='little')
                    
                    print(f"Received packet: obj_id={obj_id}, data1={data1}, data2={data2}")
                    
                    # Handle LED control (obj_id = 1 for LED)
                    if obj_id == 1:
                        self.led.control_led(data1)
                        led_states = self.led.get_led_states()
                        print(f"LED states after change: {led_states}")
                        
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        except Exception as e:
            print(f"Error handling client: {e}")
    
    async def start(self):
        """Start the WebSocket server"""
        print(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        print("Server is running. Press Ctrl+C to stop.")
        
        try:
            await self.server.wait_closed()
        except Exception as e:
            print(f"Server error: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up server...")
        if self.server:
            self.server.close()
        self.led.gpio.cleanup()
        print("Server cleanup completed")

async def main():
    server = WebSocketServer()
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down...")