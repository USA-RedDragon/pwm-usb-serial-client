import serial
import threading
import time
import tkinter as tk

from google import protobuf
from cobs import cobs

import state_pb2


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.serial = serial.Serial('COM7', 9600, bytesize=8, parity='N', stopbits=1, timeout=1)
        self.deviceState = state_pb2.DeviceState()
        self.serial_thread = threading.Thread(target=self.serial_loop)
        self.serial_thread_stop_event = threading.Event()
        self.master = master
        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.pack()
        self.create_widgets()
        self.serial_thread.start()

    def on_closing(self):
        self.serial_thread_stop_event.set()
        self.serial_thread.join(0.1)
        self.serial.close()
        self.master.quit()
        self.master.destroy()

    def update_ui(self):
        self.usb0_button["text"] = f"Turn {'Off' if self.deviceState.usb0.power else 'On'} USB 0"
        self.usb1_button["text"] = f"Turn {'Off' if self.deviceState.usb1.power else 'On'} USB 1"
        self.usb0_pwm.set(self.deviceState.usb0.dutyCycle)
        self.usb1_pwm.set(self.deviceState.usb1.dutyCycle)

    def parse_message(self, proto_message):
        try:
            if self.deviceState.ParseFromString(proto_message):
                print('USB0: ' +
                      str(self.deviceState.usb0.power) +
                      f', Duty Cycle: {self.deviceState.usb0.dutyCycle}, ' +
                      'Default State: ' +
                      str(self.deviceState.configuration.usb0Restore.power) +
                      ', Duty Cycle: ' +
                      str(self.deviceState.configuration.usb0Restore.dutyCycle))
                print('USB1: ' +
                      str(self.deviceState.usb1.power) +
                      f', Duty Cycle: {self.deviceState.usb1.dutyCycle}, ' +
                      'Default State: ' +
                      str(self.deviceState.configuration.usb1Restore.power) +
                      ', Duty Cycle: ' +
                      str(self.deviceState.configuration.usb1Restore.dutyCycle)
                      + '\n')
                self.update_ui()
        except protobuf.message.DecodeError as _:
            print('Received non-proto message: ', proto_message)

    def serial_loop(self):
        while not self.serial_thread_stop_event.is_set():
            data = []
            serial_byte = self.serial.read()
            if serial_byte == b'':
                pass
            while serial_byte != b'\x00' and serial_byte != b'':
                data.append(serial_byte)
                serial_byte = self.serial.read()
            data = b''.join(data)
            try:
                proto_message = cobs.decode(data)
                self.parse_message(proto_message)
            except cobs.DecodeError as err:
                print(err)
            time.sleep(0.1)

    def create_widgets(self):
        self.usb0_button = tk.Button(
            self,
            text="Turn on USB 0",
            command=lambda: self.toggle_usb(0))
        self.usb0_button.pack(side="top")

        self.usb0_pwm = tk.Scale(
            self.master,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            command=lambda dc: self.set_duty_cycle(0, dc))
        self.usb0_pwm.pack(side="top")

        self.usb1_button = tk.Button(
            self,
            text="Turn on USB 1",
            command=lambda: self.toggle_usb(1))
        self.usb1_button.pack(side="bottom")

        self.usb1_pwm = tk.Scale(
            self.master,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            command=lambda dc: self.set_duty_cycle(1, dc))
        self.usb1_pwm.pack(side="bottom")

        self.config_button = tk.Button(
            self,
            text="Save as power-on defaults",
            command=self.save_defaults)
        self.config_button.pack(side="bottom")

    def toggle_usb(self, usb_index):
        current_usb_state = getattr(self.deviceState, f"usb{str(usb_index)}")
        print(f"Toggle USB{str(usb_index)}: {not current_usb_state.power}")
        new_state = state_pb2.DeviceState()
        new_state.CopyFrom(self.deviceState)
        new_usb_state = state_pb2.PowerState()
        new_usb_state.power = not current_usb_state.power
        new_usb_state.dutyCycle = current_usb_state.dutyCycle
        getattr(new_state, f"usb{str(usb_index)}").CopyFrom(new_usb_state)
        self.serial.write(cobs.encode(new_state.SerializeToString()) + b'\x00')

    def save_defaults(self):
        new_state = state_pb2.DeviceState()
        new_state.CopyFrom(self.deviceState)
        new_config = state_pb2.Configuration()
        new_config.usb0Restore.CopyFrom(self.deviceState.usb0)
        new_config.usb1Restore.CopyFrom(self.deviceState.usb1)
        new_state.configuration.CopyFrom(new_config)
        self.serial.write(cobs.encode(new_state.SerializeToString()) + b'\x00')

    def set_duty_cycle(self, usb_index, duty_cycle):
        current_usb_state = getattr(self.deviceState, f"usb{str(usb_index)}")
        print(f"Set USB{str(usb_index)} Duty Cycle: {duty_cycle}")
        new_state = state_pb2.DeviceState()
        new_state.CopyFrom(self.deviceState)
        new_usb_state = state_pb2.PowerState()
        new_usb_state.power = current_usb_state.power
        new_usb_state.dutyCycle = int(duty_cycle)
        getattr(new_state, f"usb{str(usb_index)}").CopyFrom(new_usb_state)
        self.serial.write(cobs.encode(new_state.SerializeToString()) + b'\x00')


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
