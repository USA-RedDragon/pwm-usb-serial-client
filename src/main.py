import serial
import time

from google import protobuf
from google.protobuf import json_format
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
                print(cobs.decode(data))
                if deviceState.ParseFromString(cobs.decode(data)):
                    print(
                        json_format.MessageToJson(
                            deviceState, including_default_value_fields=True)
                    )
            except protobuf.message.DecodeError as err:
                print(err)
            except cobs.DecodeError as err:
                print(err)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
