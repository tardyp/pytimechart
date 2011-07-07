import sys,os

additional_event_field = [
    ('softirq_entry', 'name'),
    ]

def get_softirq_entry_name(event):
    softirq_list = ["HI", "TIMER", "NET_TX", "NET_RX", "BLOCK", "BLOCK_IOPOLL", "TASKLET", "SCHED", "HRTIMER", "RCU"]
    return softirq_list[event.vec]

class TraceCmdEventWrapper:
    def __init__(self,event):
        self.tracecmd_event = event
        self.event = str(event.name)
        self.linenumber = 0
        self.common_cpu = int(event.cpu)
        self.common_comm = str(event.comm)
        self.common_pid = int(event.pid)
        self.timestamp = event.ts/1000

    def __getattr__(self,name):
        try:
            f = self.tracecmd_event[name]
        except :
            attr = self.get_additional_event_field(name)
            if attr:
                return attr
            raise  AttributeError(name+ " not in "+str( self.tracecmd_event.keys()))
        try:
            return long(f)
        except :
            return str(f)

    def get_additional_event_field(self, name):
        for field in additional_event_field:
            event = field[0]
            attr = field[1]
            if ((self.event==event) & (name==attr)):
                func = eval("get_"+event+"_"+attr)
                return func(self)

def parse_tracecmd(filename,callback):
    try:
        import tracecmd
    except ImportError:
        raise Exception("please compile python support in trace-cmd and add trace-cmd directory into your PYTHONPATH environment variable")
    t = tracecmd.Trace(str(filename))
    # the higher level assumes events are already system sorted, but tracecmd sort them by cpus.
    # so we have to manually sort them.
    cpu_event_list_not_empty = t.cpus
    events = [ t.read_event(cpu) for cpu in xrange(t.cpus)]
    availble_cpu = range(0, t.cpus)
    while cpu_event_list_not_empty > 0:
        ts = 0xFFFFFFFFFFFFFFFF
        if len(availble_cpu):
            first_cpu = availble_cpu[0]
        else:
            break
        for cpu in availble_cpu:
            if events[cpu].ts < ts:
                first_cpu = cpu
                ts = events[cpu].ts
        callback(TraceCmdEventWrapper(events[first_cpu]))

        events[first_cpu] = t.read_event(first_cpu)
        if events[first_cpu] == None:
            cpu_event_list_not_empty -= 1
            availble_cpu.remove(first_cpu)

def get_partial_text(fn,start,end):
    text = ""
    return text

def load_tracecmd(fn):
    from timechart.model import tcProject
    proj = tcProject()
    proj.filename = fn
    proj.start_parsing(get_partial_text)
    parse_tracecmd(fn,proj.handle_trace_event)
    proj.finish_parsing()
    return proj

def detect_tracecmd(fn):
    if fn.endswith(".dat"):
        return load_tracecmd
    return None
