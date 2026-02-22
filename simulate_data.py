import csv
import math
import random
import time
from pathlib import Path

DATA_DIR = Path("/home/pi/ICE_PLANT/data")
SAMPLE_RATE = 4.0
BLOCK_INTERVAL = 1.0

def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

def encode_hr_sample(bpm: float, quality: int, fmp: int) -> bytes:
    value = int(round(bpm / 0.25))
    value = max(0, min(1200, value))
    hi = ((value >> 8) & 0x07) | ((quality & 0x03) << 5) | ((fmp & 0x03) << 3)
    lo = value & 0xFF
    return bytes([hi, lo])

def generate_hr_series(base: float, amp: float, drift: float, phase: float, count: int) -> list[float]:
    out = []
    for i in range(count):
        t = time.time() + i / SAMPLE_RATE
        val = base + amp * math.sin(t * 2.0 * math.pi * drift + phase)
        val += random.uniform(-2.0, 2.0)
        out.append(clamp(val, 60.0, 200.0))
    return out

def generate_toco_series(base: float, count: int) -> list[int]:
    out = []
    for i in range(count):
        t = time.time() + i / SAMPLE_RATE
        wave = 10.0 * math.sin(t * 2.0 * math.pi * 0.02)
        bump = 0.0
        if int(t) % 90 < 10:
            bump = 30.0 * math.sin((t % 10) * math.pi / 10.0)
        val = clamp(base + wave + bump + random.uniform(-1.0, 1.0), 0.0, 127.0)
        out.append(int(round(val)))
    return out

def build_payload() -> bytes:
    payload = bytearray()
    payload.append(ord("S"))
    payload.extend([0x80, 0x00])

    hr1 = generate_hr_series(140.0, 8.0, 0.03, 0.0, 4)
    hr2 = generate_hr_series(130.0, 6.0, 0.035, 1.2, 4)
    mhr = generate_hr_series(80.0, 4.0, 0.02, 2.4, 4)

    for bpm in hr1:
        payload.extend(encode_hr_sample(bpm, quality=2, fmp=0))
    for bpm in hr2:
        payload.extend(encode_hr_sample(bpm, quality=1, fmp=0))
    for bpm in mhr:
        payload.extend(encode_hr_sample(bpm, quality=2, fmp=0))

    toco = generate_toco_series(10.0, 4)
    payload.extend(toco)

    payload.extend([0x21, 0x10])
    payload.append(0x04)
    payload.append(0x00)
    return bytes(payload)

def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / time.strftime("ctg_frames_sim_%Y%m%d_%H%M%S.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "payload_len", "payload_hex"])
        print(f"Writing simulated data to {csv_path}")
        while True:
            payload = build_payload()
            writer.writerow([time.time(), len(payload), payload.hex(" ")])
            f.flush()
            time.sleep(BLOCK_INTERVAL)

if __name__ == "__main__":
    main()
