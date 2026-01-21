import serial
import time

PORT = "COM7"   # change this to your ESP32 port
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

print("Connected to Plant Pet 🌱")

while True:
    line = ser.readline().decode(errors="ignore").strip()
    if line.startswith("TEMP"):
        print(line)
