import serial
import time
import csv
import shutil
from pathlib import Path
from typing import List, Optional

# Protocol constants
DLE = 0x10
STX = 0x02
ETX = 0x03
POLY = 0x1021  # CCITT CRC-16

# settings
DATA_DIR = Path("data")
MAX_CSV_FILES = 2000
MIN_FREE_BYTES = 250 * 1024 * 1024

def crc_ccitt_bytes(data: bytes) -> bytes:
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

def crc_ccitt_value(data: bytes) -> int:
    """Compute CRC-16 (CCITT) over the block and return as int."""
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ POLY
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

def build_block(payload: bytes) -> bytes:
    """Wrap payload in DLE STX ... DLE ETX + CRC."""
    block = bytearray([DLE, STX])
    for b in payload:
        block.append(b)
        if b == DLE:  # double DLE in payload
            block.append(DLE)
    block.extend([DLE, ETX])
    block.extend(crc_ccitt_bytes(block))
    return bytes(block)

def unescape_payload(payload: bytes) -> bytes:
    """Collapse doubled DLE bytes inside payload."""
    out = bytearray()
    i = 0
    while i < len(payload):
        b = payload[i]
        if b == DLE and i + 1 < len(payload) and payload[i + 1] == DLE:
            out.append(DLE)
            i += 2
            continue
        out.append(b)
        i += 1
    return bytes(out)

def extract_frames(buffer: bytearray) -> List[bytes]:
    """Extract complete frames from buffer, leaving any partial tail."""
    frames: List[bytes] = []
    i = 0
    while i < len(buffer) - 1:
        if buffer[i] == DLE and buffer[i + 1] == STX:
            # Find DLE ETX, then ensure 2 CRC bytes exist.
            j = i + 2
            while j < len(buffer) - 1:
                if buffer[j] == DLE and buffer[j + 1] == ETX:
                    end = j + 2
                    if end + 2 <= len(buffer):
                        frame = bytes(buffer[i:end + 2])
                        frames.append(frame)
                        i = end + 2
                        break
                    # Need more bytes for CRC.
                    i = i
                    j = len(buffer)
                    break
                j += 1
            else:
                break
        else:
            i += 1
    if i > 0:
        del buffer[:i]
    return frames

def validate_frame(frame: bytes) -> Optional[bytes]:
    """Return unescaped payload if CRC is valid; otherwise None."""
    if len(frame) < 6 or frame[0:2] != bytes([DLE, STX]):
        return None
    if frame[-4:-2] != bytes([DLE, ETX]):
        return None
    body = frame[:-2]
    received_crc = int.from_bytes(frame[-2:], "big")
    computed_crc = crc_ccitt_value(body)
    if received_crc != computed_crc:
        return None
    raw_payload = frame[2:-4]
    return unescape_payload(raw_payload)

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


def ensure_space_and_limit():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = sorted(DATA_DIR.glob("ctg_frames_*.csv"), key=lambda p: p.stat().st_mtime)
    while len(csv_files) > MAX_CSV_FILES:
        oldest = csv_files.pop(0)
        oldest.unlink(missing_ok=True)
    usage = shutil.disk_usage(DATA_DIR)
    while usage.free < MIN_FREE_BYTES and csv_files:
        oldest = csv_files.pop(0)
        oldest.unlink(missing_ok=True)
        usage = shutil.disk_usage(DATA_DIR)

def open_csv_for_hour(ts: float):
    hour_stamp = time.strftime("%Y%m%d_%H00", time.localtime(ts))
    ensure_space_and_limit()
    csv_path = DATA_DIR / f"ctg_frames_{hour_stamp}.csv"
    csv_file = open(csv_path, "w", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["timestamp", "payload_len", "payload_hex"])
    print(f"Writing frames to {csv_path}")
    return csv_file, csv_writer, hour_stamp

csv_file, csv_writer, current_hour_stamp = open_csv_for_hour(time.time())

# Continuous read loop
try:
    buffer = bytearray()
    ok_frames = 0
    bad_frames = 0
    space_check_counter = 0
    while True:
        data = ser.read(512)
        if data:
            buffer.extend(data)
            for frame in extract_frames(buffer):
                payload = validate_frame(frame)
                if payload is None:
                    bad_frames += 1
                    print("Frame CRC FAIL:", frame.hex(" "))
                    continue
                ok_frames += 1
                now = time.time()
                hour_stamp = time.strftime("%Y%m%d_%H00", time.localtime(now))
                if hour_stamp != current_hour_stamp:
                    csv_file.close()
                    csv_file, csv_writer, current_hour_stamp = open_csv_for_hour(now)
                space_check_counter += 1
                if space_check_counter >= 100:
                    ensure_space_and_limit()
                    space_check_counter = 0
                csv_writer.writerow([now, len(payload), payload.hex(" ")])
                print(f"Frame OK #{ok_frames} (bad {bad_frames}): len={len(payload)}")
except KeyboardInterrupt:
    pass
finally:
    csv_file.close()
