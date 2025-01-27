# mock_gpio.py

class GPIO:
    # GPIO modes
    BCM = "BCM"
    BOARD = "BOARD"
    
    # Pin modes
    OUT = "OUT"
    IN = "IN"
    
    # Pin states
    HIGH = 1
    LOW = 0
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GPIO, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if not self.initialized:
            self.pin_states = {}
            self.mode = None
            self.initialized = True
            print("Initialized Mock GPIO")
    
    def setmode(self, mode):
        self.mode = mode
        print(f"GPIO mode set to: {mode}")
    
    def setup(self, pin, mode):
        self.pin_states[pin] = {"mode": mode, "state": self.LOW}
        print(f"Pin {pin} setup as {mode}")
    
    def output(self, pin, state):
        if pin in self.pin_states:
            self.pin_states[pin]["state"] = state
            state_str = 'HIGH' if state == self.HIGH else 'LOW'
            print(f"Pin {pin} set to {state_str}")
        else:
            raise RuntimeError(f"Pin {pin} not setup")
    
    def cleanup(self):
        self.pin_states.clear()
        print("GPIO cleanup completed")
    
    def get_pin_state(self, pin):
        return self.pin_states.get(pin, {}).get("state", None)

# Create a singleton instance
GPIO = GPIO()