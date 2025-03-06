#!/usr/bin/env python3
import serial
import sys
import fcntl
import os
import secrets
import string

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
        + len(data).to_bytes(2, "little")
        + str.encode(data)
    )
    return finalize_packet(packet)

def lock_uart_and_write_bytes(uart, bytes: bytes):
    fcntl.lockf(uart, fcntl.LOCK_EX)
    uart.write(bytes)
    fcntl.lockf(uart, fcntl.LOCK_UN)

def get_node_id():
    
    node_id = None
    
    try:
        # Use unique RPi serial number of the CPU
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line[0:6]=='Serial':
                    node_id = line[10:26]
    except:
        # In case CPU method doesn't work, create random, persistent node_id file
        node_id_path = "./node_id"

        # First try to open file, since node_id may already exist
        if os.path.exists(node_id_path):
            with open(node_id_path, "r") as f:
                node_id = f.read().strip()
            generate_node_id = False
    
            # Sanity check if node_id is in expected format - 16 hex characters - otherwhise a new one must be generated
            if not ((len(node_id) == 16) and all(c in string.hexdigits for c in node_id)):
                generate_node_id = True
        else:
            generate_node_id = True

        # In case it doesn't exist or it is incorrectly formatted, generate a new one
        if generate_node_id:
            node_id = secrets.token_hex(8)
            with open(node_id_path, "w") as f:
                f.write(node_id)
    
    node_id = int(node_id, 16)

    return node_id

if __name__ == '__main__':
    node_id = get_node_id()
    uart = serial.Serial(port=sys.argv[1], baudrate=115200)
    lock_uart_and_write_bytes(uart, spotter_log_console(node_id, "hello world from borealis sbc"))
