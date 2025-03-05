#!/usr/bin/env python3
import serial
import sys
import fcntl

def cobs_encode_with_trailing_zero(src):
    # minor refactor of example from stuart and baker (1999)
    P = len(src)
    out = bytearray(P + (P + 253) // 254 + 2)
    code = 0x01
    dst = 1
    code_ptr = 0

    for byte in src:
        flush = False
        if byte == 0:
            flush = True
        else:
            out[dst] = byte
            dst += 1
            code += 1

            if 0xFF == code:
                flush = True

        if flush:
            out[code_ptr] = code
            code_ptr = dst
            dst += 1
            code = 0x01

    out[code_ptr] = code
    out[dst] = 0

    return bytes(out)[0:(dst + 1)]

def crc(seed: int, src: bytes) -> int:
    e, f = 0, 0
    for i in src:
        e = (seed ^ i) & 0xFF
        f = e ^ ((e << 4) & 0xFF)
        seed = (seed >> 8) ^ (((f << 8) & 0xFFFF) ^ ((f << 3) & 0xFFFF)) ^ (f >> 4)
    return seed

def finalize_packet(packet: bytearray) -> bytes:
    checksum = crc(0, packet)
    packet[2] = checksum & 0xFF
    packet[3] = (checksum >> 8) & 0xFF
    return cobs_encode_with_trailing_zero(packet)

def get_pub_header(node_id: int) -> bytearray:
    return (
        bytearray.fromhex("02000000")
        + node_id.to_bytes(8, "little")
        + bytearray.fromhex("0101")
    )

def spotter_tx(node_id: int, data: bytes) -> bytes:
    topic = b"spotter/transmit-data"
    packet = (
        get_pub_header(node_id)
        + len(topic).to_bytes(2, "little")
        + topic
        + b"\x01"
        + data
    )
    return finalize_packet(packet)

def spotter_log(node_id: int, filename: str, data: str) -> bytes:
    topic = b"spotter/fprintf"
    packet = (
        get_pub_header(node_id)
        + len(topic).to_bytes(2, "little")
        + topic
        + (b"\x00" * 8)
        + len(filename).to_bytes(2, "little")
        + (len(data) + 1).to_bytes(2, "little")
        + str.encode(filename)
        + str.encode(data)
        + str.encode("\n")
    )
    return finalize_packet(packet)

def spotter_log_console(node_id: int, data: str) -> bytes:
    topic = b"spotter/printf"
    packet = (
        get_pub_header(node_id)
        + len(topic).to_bytes(2, "little")
        + topic
        + (b"\x00" * 8)
        + (b"\x00" * 2)
        + (len(data) + 1).to_bytes(2, "little")
        + str.encode(data)
        + str.encode("\n")
    )
    return finalize_packet(packet)

def lock_uart_and_write_bytes(uart, bytes: bytes):
    fcntl.lockf(uart, fcntl.LOCK_EX)
    uart.write(bytes)
    fcntl.lockf(uart, fcntl.LOCK_UN)

def get_node_id():
    # TODO: replace this with get_node_id() as prototyped by Tiago
    return 0xC0FFEEEEF0CACC1A

if __name__ == '__main__':
    import time
    def main():
        node_id = get_node_id()

        interval = 5
        last_send = time.time() - interval
        uart = serial.Serial(port=sys.argv[1], baudrate=115200)

        while True:
            now = time.time()
            if now - last_send >= interval:
                last_send += interval
                print("publishing at " + str(now), file=sys.stderr)

                lock_uart_and_write_bytes(uart, spotter_tx(node_id, b"sensor12: 1234.56, binary_ok_too: \x00\x01\x02\x03\xff\xfe\xfd"))
                lock_uart_and_write_bytes(uart, spotter_log(node_id, "testmctest.log", "Sensor 1: 1234.56. More detailed human-readable info for the SD card logs."))
                lock_uart_and_write_bytes(uart, spotter_log_console(node_id, "spotter_log_console : printf hello world!, does not save to sd card"))

    main()
