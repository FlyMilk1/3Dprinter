#!/usr/bin/env python3
import serial
import sys
import time
import glob
import os

def list_serial_ports():
    """List available serial ports."""
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    return ports

def open_serial(port, baud):
    """Open serial connection with retry."""
    try:
        ser = serial.Serial(port, baud, timeout=5)
        time.sleep(2)  # wait for printer reset
        ser.flushInput()
        print(f"Connected to {port} at {baud} baud.")
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port {port}: {e}")
        sys.exit(1)

def wait_for_ok(ser):
    """Wait for 'ok' or truncated response from printer."""
    buffer = ""
    start_time = time.time()
    while True:
        line = ser.readline().decode(errors='ignore').strip()
        if not line:
            # Timeout safety (10 seconds)
            if time.time() - start_time > 10:
                print("⚠️  Timeout waiting for response, continuing anyway...")
                break
            continue
        print(f"<< {line}")
        buffer += line.lower()
        if buffer.startswith('ok') or buffer == 'o' or 'ok' in buffer:
            break

def send_gcode_file(filename, port, baud):
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        sys.exit(1)

    ser = open_serial(port, baud)
    with open(filename, 'r', errors='ignore') as f:
        lines = f.readlines()

    print(f"Sending {len(lines)} lines of G-code...\n")
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith(';'):
            continue  # skip comments and blanks

        print(f">> {line}")
        try:
            ser.write((line + '\n').encode())
            wait_for_ok(ser)
        except serial.SerialException as e:
            print(f"Serial error: {e}. Retrying...")
            time.sleep(1)
            ser.close()
            ser = open_serial(port, baud)
        except KeyboardInterrupt:
            print("\n⛔ Interrupted by user.")
            break

        time.sleep(0.05)  # small delay for stability

    print("\n✅ Done sending file.")
    ser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./send_gcode.py <file.gcode> [baudrate] [port]")
        sys.exit(1)

    filename = sys.argv[1]
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

    ports = list_serial_ports()
    if not ports:
        print("❌ No serial ports found.")
        sys.exit(1)

    print("Available ports:")
    for p in ports:
        print(f"  {p}")

    port = sys.argv[3] if len(sys.argv) > 3 else ports[0]
    print(f"Using {port}\n")

    send_gcode_file(filename, port, baud)
