#!/usr/bin/env python3
"""Watch acoustic packets from shm and tell the gateway once replay has
caught up to realtime.

Usage: ./replay_stub.py [shm[:path]]
"""

import os
import struct
import sys
import time
import re

from shared_memory_ringbuffer_reader import shared_memory_ringbuffer_generator
from parse_acoustic_packets import parse_acoustic_packet

WINDOW_S = 5.0
CAUGHT_UP_RATIO_MIN = 0.95
CAUGHT_UP_RATIO_MAX = 1.05
CAUGHT_UP_WINDOWS = 2


def yield_packet_bytes_from_shm(source):
    for packet_with_logging_header in shared_memory_ringbuffer_generator(source):
        _, timestamp_lsbs, timestamp_msbs = struct.unpack(
            "<HHI", packet_with_logging_header[0:8]
        )
        logged_timestamp_microseconds = ((timestamp_msbs << 16) | timestamp_lsbs) * 16
        yield packet_with_logging_header[8:], logged_timestamp_microseconds


def replay_ratio(seqnum_start, logged_us_start, seqnum, logged_us, packet_duration_s):
    packets = (seqnum - seqnum_start) % 65536
    if logged_us_start == logged_us:
        return 0.0
    return packets * packet_duration_s / ((logged_us - logged_us_start) / 1e6)


def next_acoustic_packet(yield_packet_bytes_function, source):
    for packet_bytes, logged_timestamp_microseconds in yield_packet_bytes_function(
        source
    ):
        # attempt to parse the packet bytes as an acoustic packet
        packet = parse_acoustic_packet(packet_bytes, logged_timestamp_microseconds)
        if not packet:
            continue

        return packet


def main():
    from bm_sbc_gateway import replay_caught_up

    # Wait for log path to exist and validate replay is enabled
    init_log_path = "/var/run/bristlemouth_init_log.txt"
    while not os.path.exists(init_log_path):
        time.sleep(1)

    replay_enabled = False
    with open(init_log_path, "r") as f:
        for line in f.readlines():
            # init log lines are "key: value\r\n", so take the value after the key
            match = re.search(r"enable_replay:\s*(\d+)", line)
            if match:
                replay_enabled = int(match.group(1)) != 0
                break
    if not replay_enabled:
        print("Replay not enabled, exiting")
        sys.exit(0)

    source = (
        sys.argv[1].split(":")[1]
        if len(sys.argv) > 1 and "shm:" in sys.argv[1]
        else "/cobs_to_shm"
    )
    window_start = None
    windows_caught_up = 0

    while True:
        # Read from SHM every WINDOW_S to see if data has caught up
        time.sleep(WINDOW_S)
        packet = next_acoustic_packet(yield_packet_bytes_from_shm, source)
        if not packet:
            print("cobs_to_shm is no longer running, exiting now...", file=sys.stderr)
            sys.exit(0)

        if window_start is None:
            window_start = (packet.seqnum, packet.logged_timestamp_microseconds)
            continue

        seqnum_start, logged_us_start = window_start
        ratio = replay_ratio(
            seqnum_start,
            logged_us_start,
            packet.seqnum,
            packet.logged_timestamp_microseconds,
            packet.samples.shape[0] / packet.fs,
        )
        window_start = (packet.seqnum, packet.logged_timestamp_microseconds)

        if CAUGHT_UP_RATIO_MIN < ratio <= CAUGHT_UP_RATIO_MAX:
            windows_caught_up += 1
        else:
            windows_caught_up = 0
        print("replay running at %.2fx realtime" % ratio, file=sys.stderr)

        if windows_caught_up >= CAUGHT_UP_WINDOWS:
            print("replay caught up to realtime, notifying gateway", file=sys.stderr)
            replay_caught_up()
            return


if __name__ == "__main__":
    main()
