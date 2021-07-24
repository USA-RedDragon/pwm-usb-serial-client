import serial
import time

def main():
    try:
        ser = serial.Serial('COM7', 9600, timeout=0.1)
        while True:
            serMessage = ser.readline()
            print(serMessage)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
