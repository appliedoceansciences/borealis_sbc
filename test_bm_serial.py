#!/usr/bin/env python3
import serial
import sys
import fcntl

# Adapted from https://github.com/cmcqueen/cobs-python
def cobs_encode(in_bytes: bytes) -> bytes:
    final_zero = True
    out_bytes = bytearray()
    idx = 0
    search_start_idx = 0
    for in_char in in_bytes:
        if in_char == 0:
            final_zero = True
            out_bytes.append(idx - search_start_idx + 1)
            out_bytes += in_bytes[search_start_idx:idx]
            search_start_idx = idx + 1
        else:
            if idx - search_start_idx == 0xFD:
                final_zero = False
                out_bytes.append(0xFF)
                out_bytes += in_bytes[search_start_idx : idx + 1]
                search_start_idx = idx + 1
        idx += 1
    if idx != search_start_idx or final_zero:
        out_bytes.append(idx - search_start_idx + 1)
        out_bytes += in_bytes[search_start_idx:idx]
    return bytes(out_bytes)

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
    return cobs_encode(packet) + b"\x00"

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

def write_bytes_to_uart(path, bytes: bytes, baudrate=115200):
    uart = serial.Serial(port=path, baudrate=baudrate)
    fcntl.lockf(uart, fcntl.LOCK_EX)

    uart.write(bytes)

    fcntl.lockf(uart, fcntl.LOCK_UN)
    uart.close()

import time

node_id = 0xC0FFEEEEF0CACC1A

last_send = time.time()
while True:
    now = time.time()
    if now - last_send > 5:
        last_send = now
        print("publishing" + str(now),file=sys.stderr)

        write_bytes_to_uart(sys.argv[1], spotter_tx(node_id, b"sensor12: 1234.56, binary_ok_too: \x00\x01\x02\x03\xff\xfe\xfd"))

        write_bytes_to_uart(sys.argv[1], spotter_log(node_id, "testmctest.log", "Sensor 1: 1234.56. More detailed human-readable info for the SD card logs."))
