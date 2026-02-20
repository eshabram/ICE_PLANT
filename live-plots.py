import argparse
import csv
import os
import time
from collections import deque
from pathlib import Path
from typing import Optional

DATA_DIR = Path("data")
LEVELS = " .:-=+*#%@"

def latest_csv_path() -> Optional[Path]:
    files = list(DATA_DIR.glob("ctg_frames_*.csv"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)

def payload_byte(payload_hex: str, index: int) -> Optional[int]:
    parts = payload_hex.strip().split()
    if index < 0 or index >= len(parts):
        return None
    return int(parts[index], 16)

def render_sparkline(values: deque[int], width: int) -> str:
    if not values:
        return ""
    vals = list(values)[-width:]
    out = []
    for v in vals:
        level = int(v * (len(LEVELS) - 1) / 255)
        out.append(LEVELS[level])
    return "".join(out)

def main() -> None:
    parser = argparse.ArgumentParser(description="Live ASCII plot from CTG CSV logs.")
    parser.add_argument("--byte", type=int, default=0,
                        help="Payload byte index to plot (default: 0).")
    parser.add_argument("--width", type=int, default=80,
                        help="Plot width in characters (default: 80).")
    parser.add_argument("--from-start", action="store_true",
                        help="Start from beginning of the current CSV.")
    parser.add_argument("--poll", type=float, default=0.2,
                        help="Polling interval in seconds (default: 0.2).")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    values: deque[int] = deque(maxlen=args.width)

    path = latest_csv_path()
    if path is None:
        print("No CSV files found in data/. Start ice_plant.py first.")
        return

    while True:
        if path is None or not path.exists():
            path = latest_csv_path()
            time.sleep(args.poll)
            continue

        with open(path, newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not args.from_start:
                for _ in reader:
                    pass

            while True:
                line = f.readline()
                if not line:
                    latest = latest_csv_path()
                    if latest and latest != path:
                        path = latest
                        break
                    time.sleep(args.poll)
                    continue
                row = line.strip().split(",", 2)
                if len(row) < 3:
                    continue
                ts = row[0]
                payload_hex = row[2]
                val = payload_byte(payload_hex, args.byte)
                if val is None:
                    continue
                values.append(val)
                spark = render_sparkline(values, args.width)
                os.write(1, f"\033[2J\033[Hbyte={args.byte} last={val} ts={ts}\n{spark}\n".encode())

if __name__ == "__main__":
    main()
