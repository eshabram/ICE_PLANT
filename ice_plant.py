import serial

ser = serial.Serial('/dev/serial0', 9600, timeout=1)

while True:
    line = ser.readline()
    if line:
        print(line)
