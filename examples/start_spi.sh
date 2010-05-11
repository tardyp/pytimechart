mount -t debugfs none /sys/kernel/debug 2>/dev/null
cd /sys/kernel/debug/tracing
echo 50000 > buffer_size_kb
echo function > current_tracer
echo ‘spi*’ > set_ftrace_filter
echo ‘max3110’ >> set_ftrace_filter
echo sched:sched_wakeup > set_event
echo power: >>set_event>> set_event
echo irq:* >>set_event
echo 1 >tracing_enabled
echo >trace
