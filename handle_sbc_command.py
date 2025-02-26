#!/usr/bin/env python3
import serial
import sys
import fcntl

def lock_uart_and_write_bytes(uart, bytes: bytes):
    fcntl.lockf(uart, fcntl.LOCK_EX)
    uart.write(bytes)
    fcntl.lockf(uart, fcntl.LOCK_UN)

if __name__ == '__main__':
    def main():
        uart = serial.Serial(port=sys.argv[1], baudrate=115200)
        lock_uart_and_write_bytes(uart,b"\x02\x3f\x00")
        while True:
            line = uart.readline().decode('utf-8').strip()
            if line == '': continue
            print(line, file=sys.stderr)
            if line.startswith('sbc_command: '):
                command = line.removeprefix('sbc_command: ')
                print(command)
                break

    main()

