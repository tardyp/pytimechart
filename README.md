# PyTimechart [![Build Status](https://travis-ci.org/tardyp/pytimechart.png?branch=master)](https://travis-ci.org/tardyp/pytimechart)


a tool to display ftrace (or perf) traces

<img src="https://github.com/tardyp/pytimechart/blob/master/docs/sources/images/pytimechart-overview.png?raw=true">
</img>

This is a reimplemetation of some of the main features of timechart from Arjan Van de Ven.

pyTimechart is aimed at helping kernel developer to browse into large scale traces.

Based on very powerful and efficient plotting library Chaco, pytimechart UI feels very smooth.

Based on the python language, its plugin based architecture allow developer to very quickly implement parsing and representation of new trace-event function-trace or trace_printk

Kernel traces are parsed as trace-events, and organised into processes, each process is displayed in its own line. The x-axis representing the time, process is represented as intervals when it is scheduled in the system.

pyTimechart processes are not only process in the common unix sense, it can be any group of activities in the system. Thus pytimechart display activities of:

- cpuidle states
- cpufreq states
- runtime_pm
- irqs
- tasklets
- works
- timers
- kernel threads
- user process
- whatever there is a plugin for
- pyTimechart also represent graphically the wakeup events between two process.

## More Info

### See online Documentation for user and installation guide at:
- http://packages.python.org/pytimechart/

### Video of ELCE 2011 Conference about pytimechart:

<a href="http://free-electrons.com/pub/video/2011/elce/elce-2011-tardy-pytimechart-real-world-analysis.webm">
<img src="http://free-electrons.com/pub/video/2011/elce/vidcaps/elce-2011-tardy-pytimechart-real-world-analysis-thumb.jpg"></img>
</a>

## Submitting Patches
Patches are very much welcome, especially to support new versions of the tracepoints.

Please send pull request via github:
- https://github.com/tardyp/pytimechart/pull/new/master

