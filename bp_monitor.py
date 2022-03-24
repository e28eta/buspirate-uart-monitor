#!/usr/bin/env python
# encoding: utf-8
"""
Connect to a Bus Pirate, put it into UART live monitor mode, and wait
"""
import sys
from time import sleep
import serial
from serial.tools.miniterm import key_description
import argparse
from typing import Optional

class DoNotTx(serial.tools.miniterm.Transform):
    def tx(self, text):
        return ''

serial.tools.miniterm.TRANSFORMATIONS['do-not-tx'] = DoNotTx

commands = {
        'BBIO1': b'\x00',    # Enter reset binary mode
        'ART1':  b'\x03',    # Enter binary UART mode
        'RESET': b'\x0F',    # Reset Bus Pirate
}

def EnterBinaryMode(connection: serial.Serial) -> bool:
    connection.reset_output_buffer()
    connection.reset_input_buffer()
    # > The Bus Pirate user terminal could be stuck in a configuration menu when your program attempts to enter binary mode. 
    # > One way to ensure that you're at the command line is to send <enter> at least 10 times, and then send '#' to reset. 
    # > Next, send 0x00 to the command line 20+ times until you get the BBIOx version string
    connection.write(b'\n' * 10 + b'#' + b'\n')
    connection.reset_input_buffer()
    if connection.in_waiting:
        connection.read(connection.in_waiting)
    # Conflicting docs on entering binary mode:
    # > Send 0x00 to the user terminal (max.) 20 times
    # > you must now enter 0x00 at least 20 times to enter raw bitbang mode
    for _ in range(25):
        connection.write(commands['BBIO1'])
        if connection.read(5) == b'BBIO1':
            return True
    return False

def Send(connection: serial.Serial, message: bytes, expected_response: bytes, error_message: Optional[str] = None, raise_on_fail: bool = True):
    connection.write(message)
    response = connection.read(len(expected_response))
    if response != expected_response:
        error_message = error_message or f'Response to "{message.hex()}" was "{response.hex()}" instead of expected value "{expected_response.hex()}"'
        if raise_on_fail:
            connection.close()
            raise RuntimeError(error_message)
        else:
            sys.stderr.write(error_message + '\n')

def main():
    parser = argparse.ArgumentParser(description = 'Bus Pirate UART monitor')

    parser.add_argument(
            '--port', '-p',
            help = 'TTY device for Bus Pirate',
            default = '/dev/tty.usbserial-A6024B6I')

    args = parser.parse_args()

    baud = 115200
    # also 115200, despite error on http://dangerousprototypes.com/docs/UART_(binary)#0110xxxx_-_Set_UART_speed
    uart_connection_speed_command = b'\x69'

    sys.stderr.write(f'Connecting to: {args.port} at baudrate {baud}\n')
    try:
        connection = serial.Serial(args.port, baud, timeout=0.1)
    except Exception as e:
        sys.stderr.write(f'Connection cannot be opened\nError({e.errno}): {e.strerror}\n')
        return

    sys.stderr.write('Entering binary mode\n')
    if not EnterBinaryMode(connection):
        connection.close()
        raise RuntimeError('Bus Pirate failed to enter binary mode')

    sys.stderr.write('Entering UART Mode\n')
    Send(connection, commands['ART1'], b'ART1', 'Bus Pirate failed to enter UART mode')
    Send(connection, uart_connection_speed_command, b'\x01', 'Failed to set connection speed')
    Send(connection, b'\x80', b'\x01', 'Failed to configure UART settings (HiZ, 8/N/1, RX idle high)')
    Send(connection, b'\x02', b'\x01', 'Turning on echo UART RX failed')

    connection.timeout = None
    _ = connection.read(connection.in_waiting) # pretty reliably getting a 0x00 from the device, ignore it if there

    miniterm = serial.tools.miniterm.Miniterm(connection, filters=['do-not-tx'])
    miniterm.exit_character = chr(0x03) # Ctrl-C
    miniterm.set_rx_encoding('UTF-8')
    miniterm.set_tx_encoding('UTF-8')

    sys.stderr.write(f'--- UART Log | Quit: {key_description(miniterm.exit_character)} ---\n')

    miniterm.start()
    try:
        miniterm.join(True)
    except KeyboardInterrupt:
        pass
    sys.stderr.write('\n--- exit ---\n')
    miniterm.join()

    connection.reset_output_buffer()
    connection.reset_input_buffer()

    connection.write(b'\x03')
    response = connection.read(connection.in_waiting or 1)
    if not response.endswith(b'\x01'):
        # I haven't yet figured out how to make this robust
        sys.stderr.write(f'Turning off echo UART RX failed, the rest of cleanup may not go correctly. Response: {response.hex()}\n')
    
    sys.stderr.write('Closing connection.\n')
    Send(connection, commands['BBIO1'], b'BBIO1', raise_on_fail=False) # 'Switching back to bitbang mode failed'
    Send(connection, commands['RESET'], b'\x01', raise_on_fail=False) # 'Resetting Bus Pirate hardware failed'

    connection.close()

if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        sys.stderr.write(f'\nA fatal error of some sort occurred: { repr(e) }\n')
        sys.exit(2)