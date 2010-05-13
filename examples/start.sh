#!/bin/sh
#start.sh
mount -t debugfs none /sys/kernel/debug 2>/dev/null
cd /sys/kernel/debug/tracing
#echo 1 >options/global-clock
echo sched:sched_wakeup > set_event
echo sched:sched_switch >> set_event
echo workqueue:workqueue_execution >> set_event
echo power:* >>set_event
echo irq:* >>set_event
echo >trace
echo 1 >tracing_enabled
