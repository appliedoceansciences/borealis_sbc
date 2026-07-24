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
from parse_acoustic_packets import yield_acoustic_packets

CATCH_UP_MARGIN_S = 1.0


def yield_packet_bytes_from_shm(source):
    for packet_with_logging_header in shared_memory_ringbuffer_generator(source):
        _, timestamp_lsbs, timestamp_msbs = struct.unpack(
            "<HHI", packet_with_logging_header[0:8]
        )
        logged_timestamp_microseconds = ((timestamp_msbs << 16) | timestamp_lsbs) * 16
        yield packet_with_logging_header[8:], logged_timestamp_microseconds


def caught_up(packet_timestamp, now):
    return now - packet_timestamp < CATCH_UP_MARGIN_S


def main():
    from bm_sbc_gateway import replay_caught_up

    # Wait for log path to exist and validate replay is enabled
    init_log_path = "/var/run/bristlemouth_init_log.txt"
    while not os.path.exists(init_log_path):
        time.sleep(1)

    replay_enabled = False
    with open(init_log_path, "r") as f:
        for line in f.readlines():
            if "enable_replay: " in line:
                match = re.search(r"\d", line)
                if not match:
                    # maybe another line has an integer...
                    continue
                value = int(match.group())
                replay_enabled = True if value != 0 else False
                break
    if not replay_enabled:
        print("Replay not enabled, exiting")
        exit(0)

    source = (
        sys.argv[1].split(":")[1]
        if len(sys.argv) > 1 and "shm:" in sys.argv[1]
        else "/cobs_to_shm"
    )
    for packet in yield_acoustic_packets(yield_packet_bytes_from_shm, source, None):
        if caught_up(packet.timestamp, time.time()):
            print("replay caught up to realtime, notifying gateway", file=sys.stderr)
            replay_caught_up()
            return


if __name__ == "__main__":
    main()
