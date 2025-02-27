#!/usr/bin/env python3
# this script should be placed in /usr/local/bin/
import serial
import sys
import fcntl
import os

def lock_uart_and_write_bytes(uart, bytes: bytes):
    fcntl.lockf(uart, fcntl.LOCK_EX)
    uart.write(bytes)
    fcntl.lockf(uart, fcntl.LOCK_UN)

uart = serial.Serial(port=sys.argv[1], baudrate=115200, timeout=1)

# send a cobs packet containing '?'
lock_uart_and_write_bytes(uart, b"\x02\x3f\x00")

# loop until we get the expected response
while True:
    line = uart.readline().decode('utf-8')

    # if the above returns without a newline, it timed out, we should repeat the request
    if line == '':
        lock_uart_and_write_bytes(uart, b"\x02\x3f\x00")
        continue

    # strip newline and ignore empty lines
    line = line.strip()
    if line == '': continue

    print(line, file=sys.stderr)

    # check for and remove the expected prefix, ignoring other lines
    command = line.removeprefix('sbc_command: ')
    if line == command: continue

    # TODO: validate a checksum

    # TODO: smarter validation of which commands can be run?
    if not command.startswith('systemctl start '):
        print('ignoring unexpected command', file=sys.stderr)
        continue

    # close uart just in case the command results in something (gpsd) opening it
    uart.close()

    # replace this process with the command
    args = command.split(' ')
    os.execvp(args[0], args)
    # not reached
