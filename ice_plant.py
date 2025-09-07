import serial
import time

# Protocol constants
DLE = 0x10
STX = 0x02
ETX = 0x03
POLY = 0x1021  # CCITT CRC-16

def crc_ccitt(data: bytes) -> bytes:
    """Compute CRC-16 (CCITT) over the block."""
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ POLY
            else:
                crc <<= 1
            crc &= 0xFFFF
    return bytes([crc >> 8, crc & 0xFF])

def build_block(payload: bytes) -> bytes:
    """Wrap payload in DLE STX ... DLE ETX + CRC."""
    block = bytearray([DLE, STX])
    for b in payload:
        block.append(b)
        if b == DLE:  # double DLE in payload
            block.append(DLE)
    block.extend([DLE, ETX])
    block.extend(crc_ccitt(block))
    return bytes(block)

# Open the serial port
ser = serial.Serial('/dev/serial0', baudrate=1200, bytesize=8,
                    parity='N', stopbits=1, timeout=1)

# Build polling and go commands
poll_cmd = build_block(b'?C')  # request CTG block
go_cmd = build_block(b'G')     # enable auto-send mode

print("Starting in polling mode...")

got_data = False
while not got_data:
    # Send a polling request
    ser.write(poll_cmd)
    time.sleep(1.0)

    data = ser.read(256)
    if data:
        print("Received CTG data block (polling):", data.hex(' '))
        got_data = True

# Switch to auto-send mode
ser.write(go_cmd)
print("Sent 'G' command, monitor should now auto-send data every second.")

# Continuous read loop
try:
    while True:
        data = ser.read(512)
        if data:
            print("CTG block:", data.hex(' '))
except KeyboardInterrupt:
    pass
