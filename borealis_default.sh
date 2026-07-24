#!/bin/sh
exec systemctl start gpsd cobs_to_shm replay_stub
