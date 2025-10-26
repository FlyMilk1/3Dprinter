#!/usr/bin/env python3
import serial
import time
import sys
import os

def find_serial_port():
    """Try to auto-detect a likely 3D printer serial port."""
    import glob
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    return ports

def send_gcode(port, baud, gcode_path):
    """Send a G-code file line by line to the 3D printer."""
    if not os.path.exists(gcode_path):
        print(f"Error: G-code file '{gcode_path}' not found.")
        sys.exit(1)

    with serial.Serial(port, baud, timeout=5) as ser:
        # Wait for printer to initialize
        print(f"Connected to {port} at {baud} baud.")
        time.sleep(2)  # Allow printer to reset

        # Clear startup text
        ser.reset_input_buffer()

        with open(gcode_path, 'r') as f:
            lines = f.readlines()

        print(f"Sending {len(lines)} lines of G-code...")
        try:
            for i, line in enumerate(lines, start=1):
                clean = line.strip()
                if not clean or clean.startswith(';'):
                    continue  # Skip comments and blank lines
                ser.write((clean + '\n').encode('utf-8'))
                print(f">> {clean}")
                
                # Wait for 'ok' before sending the next line
                while True:
                    response = ser.readline().decode('utf-8').strip()
                    if response:
                        print(f"<< {response}")
                    if 'ok' in response.lower():
                        break

            print("✅ Finished sending G-code file.")
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user, closing connection...")
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: send_gcode.py <file.gcode> [baudrate] [port]")
        print("Example: ./send_gcode.py cube.gcode 115200 /dev/ttyUSB0")
        sys.exit(1)

    gcode_path = sys.argv[1]
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200
    port = sys.argv[3] if len(sys.argv) > 3 else None

    if not port:
        ports = find_serial_port()
        if not ports:
            print("No serial ports found. Plug in your printer and try again.")
            sys.exit(1)
        print("Available ports:")
        for p in ports:
            print(" ", p)
        port = ports[0]
        print(f"Using {port}")

    send_gcode(port, baud, gcode_path)

if __name__ == "__main__":
    main()
