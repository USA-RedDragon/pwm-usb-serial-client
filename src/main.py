import serial
import time

from google import protobuf
from cobs import cobs

import state_pb2


def main():
    try:
        ser = serial.Serial('COM7', 9600, timeout=0.1)
        while True:
            data = []
            serByte = ser.read()
            if serByte == b'':
                pass
            while serByte != b'\x00' and serByte != b'':
                data.append(serByte)
                serByte = ser.read()
            data = b''.join(data)
            deviceState = state_pb2.DeviceState()
            try:
                if deviceState.ParseFromString(cobs.decode(data)):
                    print('USB0: ' +
                          str(deviceState.usb0.power) +
                          f', Duty Cycle: {deviceState.usb0.dutyCycle}, ' +
                          'Default State: ' +
                          str(deviceState.configuration.usb0Restore.power) +
                          ', Duty Cycle: ' +
                          str(deviceState.configuration.usb0Restore.dutyCycle))
                    print('USB1: ' +
                          str(deviceState.usb1.power) +
                          f', Duty Cycle: {deviceState.usb1.dutyCycle}, ' +
                          'Default State: ' +
                          str(deviceState.configuration.usb1Restore.power) +
                          ', Duty Cycle: ' +
                          str(deviceState.configuration.usb1Restore.dutyCycle)
                          + '\n')
            except protobuf.message.DecodeError as err:
                print(err)
            except cobs.DecodeError as err:
                print(err)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
