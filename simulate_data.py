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

def smooth_step(value: float, step: float, lo: float, hi: float) -> float:
    return clamp(value + random.uniform(-step, step), lo, hi)

def generate_toco_series(base: float, count: int) -> list[int]:
    out = []
    for i in range(count):
        t = time.time() + i / SAMPLE_RATE
        wave = 6.0 * math.sin(t * 2.0 * math.pi * 0.015)
        bump = 0.0
        # Contraction: ~20s rise/fall every ~60s.
        if int(t) % 60 < 20:
            bump = 50.0 * math.sin((t % 20) * math.pi / 20.0)
        val = clamp(base + wave + bump + random.uniform(-0.5, 0.5), 0.0, 127.0)
        out.append(int(round(val)))
    return out

def contraction_factor(t: float) -> float:
    phase = t % 60.0
    if phase >= 20.0:
        return 0.0
    # Asymmetric rise/fall for a more realistic contraction shape.
    rise = phase / 8.0
    fall = (20.0 - phase) / 12.0
    return min(rise, fall)

BASELINE_HR1 = 140.0
BASELINE_HR2 = 135.0
BASELINE_MHR = 80.0

def build_payload() -> bytes:
    global BASELINE_HR1, BASELINE_HR2, BASELINE_MHR
    payload = bytearray()
    payload.append(ord("S"))
    payload.extend([0x80, 0x00])

    hr1 = []
    hr2 = []
    mhr = []
    for i in range(4):
        t = time.time() + i / SAMPLE_RATE
        cf = contraction_factor(t)
        # Slow random-walk baselines.
        BASELINE_HR1 = smooth_step(BASELINE_HR1, 0.4, 120.0, 160.0)
        BASELINE_HR2 = smooth_step(BASELINE_HR2, 0.5, 115.0, 155.0)
        BASELINE_MHR = smooth_step(BASELINE_MHR, 0.3, 65.0, 95.0)

        # HR1: mild accelerations during contractions.
        hr1_val = BASELINE_HR1 + 6.0 * cf + random.uniform(-1.0, 1.0)
        # HR2: subtle late decelerations (delay by ~5s).
        cf_late = contraction_factor(t - 5.0)
        hr2_val = BASELINE_HR2 - 10.0 * cf_late + random.uniform(-1.5, 1.5)
        # MHR: steady adult rate with low variance.
        mhr_val = BASELINE_MHR + random.uniform(-0.8, 0.8)

        hr1.append(clamp(hr1_val, 110.0, 170.0))
        hr2.append(clamp(hr2_val, 100.0, 165.0))
        mhr.append(clamp(mhr_val, 60.0, 110.0))

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
