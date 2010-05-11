#!/bin/sh
# stop.sh
mount -t debugfs none /sys/kernel/debug 2>/dev/null
cd /sys/kernel/debug/tracing
echo >set_event
echo 0 >tracing_enabled
cat trace > ~/trace.txt
