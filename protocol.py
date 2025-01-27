

# protocol.py
import struct
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ProtocolPacket:
    STX: bytes = b'\xfd\xfe'
    obj_id: int = 0
    data1: int = 0
    data2: int = 0
    ETX: bytes = b'\xff'
    
    def pack(self) -> bytes:
        return struct.pack('<2sIIIc', self.STX, self.obj_id, self.data1, self.data2, self.ETX)
    
    @classmethod
    def unpack(cls, data: bytes) -> 'ProtocolPacket':
        stx, obj_id, data1, data2, etx = struct.unpack('<2sIIIc', data)
        return cls(stx, obj_id, data1, data2, etx)

    def validate(self) -> bool:
        return self.STX == b'\xfd\xfe' and self.ETX == b'\xff'

