#!/bin/sh
# Pin UART threads to core 0 at RT priority.
# IRQ thread PIDs change every boot
set -u
FOUND=0
for pid in $(pgrep -f 'irq/[0-9]+-.*(pl011)') ; do
    taskset -cp 0 "$pid" || true
    chrt -f -p 85 "$pid"  || true
    FOUND=1
done
if [ "$FOUND" -eq 0 ]; then
    echo "no threaded IRQ threads found" \
         "(is 'threadirqs' on the kernel cmdline?)" >&2
    exit 1
fi
