#!/usr/bin/env python3
import serial
import sys
import fcntl
import subprocess

def lock_uart_and_write_bytes(uart, bytes: bytes):
    fcntl.lockf(uart, fcntl.LOCK_EX)
    uart.write(bytes)
    fcntl.lockf(uart, fcntl.LOCK_UN)

uart = serial.Serial(port=sys.argv[1], baudrate=115200)

# send a cobs packet containing '?'
lock_uart_and_write_bytes(uart, b"\x02\x3f\x00")

# loop until we get the expected response. TODO: repeat the request after timeout
while True:
    line = uart.readline().decode('utf-8').strip()
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

    subprocess.run(command.split(' '), shell=False)
    break
