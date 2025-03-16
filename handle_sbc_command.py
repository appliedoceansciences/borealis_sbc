#!/usr/bin/env python3
# this script should be placed in /usr/local/bin/
import serial
import sys
import fcntl
import os

import time
import calendar

def handle_gpzda_or_gprmc(line):
    if line[0] != '$': return False

    try: payload, suffix = line[1:].split('*')
    except: return False

    checksum = 0
    for byte in payload:
        checksum ^= ord(byte)

    if int(suffix, 16) != checksum:
        print('nmea checksum error', file=sys.stderr)
        return False

    if 'ZDA' == payload[1:3]:
        try:
            tokens = payload.split(',')
            hour = int(tokens[1][0:2])
            minute = int(tokens[1][2:4])
            sec = float(tokens[1][4:])
            day = int(tokens[2])
            month = int(tokens[3])
            year = int(tokens[4])
        except: return False

    elif 'RMC' == line[2:4]:
        try:
            tokens = payload.split(',')
            hour = int(tokens[1][0:2])
            minute = int(tokens[1][2:4])
            sec = float(tokens[1][4:])
            day = int(tokens[9][0:2])
            month = int(tokens[9][2:4])
            year = int(tokens[9][4:6]) + 2000
        except: return False
    else: return False

    unixsec = calendar.timegm((year, month, day, hour, minute, sec))
    time.clock_settime(time.CLOCK_REALTIME, unixsec)
    return True

def lock_uart_and_write_bytes(uart, bytes: bytes):
    fcntl.lockf(uart, fcntl.LOCK_EX)
    uart.write(bytes)
    fcntl.lockf(uart, fcntl.LOCK_UN)

uart = serial.Serial(port=sys.argv[1], baudrate=115200, timeout=1)

# send a cobs packet containing '?'
lock_uart_and_write_bytes(uart, b"\x02\x3f\x00")

handled_time = False
sbc_command = None

# loop until we get the expected response
while not handled_time and sbc_command is None:
    line = uart.readline().decode('utf-8')

    # if the above returns without a newline, it timed out, we should repeat the request
    if line == '':
        lock_uart_and_write_bytes(uart, b"\x02\x3f\x00")
        continue

    # strip newline and ignore empty lines
    line = line.strip()
    if line == '': continue

    print(line, file=sys.stderr)

    if handle_gpzda_or_gprmc(line):
        handled_time = True
        continue

    # check for and remove the expected prefix, ignoring other lines
    command = line.removeprefix('sbc_command: ')
    if line == command: continue

    # TODO: validate a checksum

    # TODO: validation of which commands can be run?

    sbc_command = command

# close uart just in case the command results in something (gpsd) opening it
uart.close()

# replace this process with the command
args = sbc_command.split(' ')
os.execvp(args[0], args)
# not reached
