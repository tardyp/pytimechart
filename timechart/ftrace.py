import re
import sys
# take the TP_printk from the /include/trace/events dir
# syntax is event_name, printk, printk_args...
events_desc = [
    ('power_start',   'type=%d state=%d', 'type','state'),
    ('power_frequency',   'type=%d state=%d', 'type','state'),
    #('power_end', 'nothing interesting to parse'),
    ('sched_switch',  'task %s:%d [%d] (%s) ==> %s:%d [%d]',
     'prev_comm', 'prev_pid', 'prev_prio','prev_state' ,
     'next_comm', 'next_pid', 'next_prio'),
    ('sched_switch',  'task %s:%d [%d] ==> %s:%d [%d]',
     'prev_comm', 'prev_pid', 'prev_prio'  ,
     'next_comm', 'next_pid', 'next_prio'),
    ('sched_switch',  'prev_comm=%s prev_pid=%d prev_prio=%d prev_state=%s ==> next_comm=%s next_pid=%d next_prio=%d',
     'prev_comm', 'prev_pid', 'prev_prio'  , 'prev_state',
     'next_comm', 'next_pid', 'next_prio'),
    ('sched_wakeup','task %s:%d [%d] success=%d [%d]','wakee_comm', 'wakee_pid', 'wakee_prio', 'success', 'wakee_cpu'),
    ('sched_wakeup','task %s:%d [%d] success=%d','wakee_comm', 'wakee_pid', 'wakee_prio', 'success'),
    ('sched_wakeup','comm=%s pid=%d prio=%d success=%d target_cpu=%d','wakee_comm', 'wakee_pid', 'wakee_prio', 'success', 'wakee_cpu'),
    ('softirq_entry','softirq=%d action=%s','irq','handler'),
    ('softirq_exit','softirq=%d action=%s','irq','handler'),
    ('softirq_entry','vec=%d [action=%s]','irq','handler'),
    ('softirq_exit','vec=%d [action=%s]','irq','handler'),
    ('irq_handler_entry', 'irq=%d handler=%s','irq','handler'),
    ('irq_handler_entry', 'irq=%d name=%s','irq','handler'),
    ('irq_handler_exit', 'irq=%d return=%s','irq','return'),
    ('irq_handler_exit', 'irq=%d ret=%s','irq','return'),
    ('workqueue_execution','thread=%s func=%s\\+%s/%s','thread','func','func_offset','func_size'),
    ('workqueue_execution','thread=%s func=%s','thread','func')
    ]

# pre process our descriptions to transform it into re
events_re = {}
num_func = 0
for event in events_desc:
    name = event[0]
    printk = event[1]
    args = event[2:]
    args_l = []
    for i in '()[]':
        printk = printk.replace(i,'\\'+i)
    # we replace %d %s by the equivalent regular expression, and keep the type in memory for later
    i = 0
    func = "def my_dispatch_func%d(event,group):\n"%(num_func)
    for arg in args:
        idx = printk.index('%')
        format = printk[idx+1]
        if format=='d':
            filt=int
            regex="([0-9]+)"
            func+=" event['%s'] = int(group[%d])\n"%(arg,i)
        elif format=='s':
            filt=str
            regex="(.*)"
            func+=" event['%s'] = group[%d]\n"%(arg,i)
        printk = printk.replace("%"+format,regex,1)
        args_l.append((arg,filt))
        i+=1
    if not events_re.has_key(name):
        events_re[name] = []
    exec func
    events_re[name].append((name,re.compile(printk),eval("my_dispatch_func%d"%num_func)))
    num_func+=1

# event class passed to callback, this is more convenient than passing a dictionary
class Event:
    def __init__(self,event):
        self.__dict__=event
class TraceCmdEventWrapper:
    def __init__(self,event):
        self.tracecmd_event = event
        self.timestamp = event.ts/1000
        self.cpu = int(event.cpu)
        self.pid = int(event.pid)
        self.comm = event.comm
        self.event = event.name
        if self.event == "sched_wakeup":
            self.wakee_pid = self.tracecmd_event.num_field("pid")
            self.wakee_comm = self.tracecmd_event.str_field("comm")
            self.wakee_prio = self.tracecmd_event.num_field("prio")
            self.wakee_cpu = self.tracecmd_event.num_field("cpu")
        if self.event == "sched_switch":
            self.prev_state = { 0:'',1: 'S' , 2:'D',4:'T', 8:'t',16:'Z',32:'X',64:'x',128:'W' }[self.tracecmd_event.num_field("prev_state")]
            self.prev_comm = self.tracecmd_event.str_field("prev_comm")
            self.next_comm = self.tracecmd_event.str_field("next_comm")
        if self.event == "softirq_entry" or self.event == "softirq_exit":
            softirq_names = ["HI","TIMER","NET_TX","NET_RX","BLOCK","BLOCK_IOPOLL","TASKLET","SCHED","HRTIMER","RCU"]
            self.irq = self.tracecmd_event.num_field("vec")
            self.handler = softirq_names[self.irq]
        if self.event == "irq_handler_entry":
            self.handler = "0x%X"%(self.tracecmd_event.num_field("name"))
        if self.event == "workqueue_execution":
            self.func = "0x%X"%(self.tracecmd_event.num_field("func"))
    def __getattr__(self,name):
        return self.tracecmd_event.num_field(name)
def load_tracecmd(filename,callback):
    try:
        import tracecmd
    except ImportError:
        raise Exception("please compile python support in trace-cmd and add trace-cmd directory into your PYTHONPATH environment variable")
    t = tracecmd.Trace(filename)
    # the higher level assumes events are already system sorted, but tracecmd sort them by cpus.
    # so we have to manually sort them.
    cpu_event_list_not_empty = t.cpus
    events = [ t.read_event(cpu) for cpu in xrange(t.cpus)]
    while cpu_event_list_not_empty > 0:
        ts = 0xFFFFFFFFFFFFFFFF
        first_cpu = 0
        for cpu in range(0, t.cpus):
            if events[cpu].ts < ts:
                first_cpu = cpu
                ts = events[cpu].ts
        callback(TraceCmdEventWrapper(events[first_cpu]))
        
        events[first_cpu] = t.read_event(first_cpu)
        if not events[first_cpu]:
            cpu_event_list_not_empty -= 1

#@profile
def parse_ftrace(filename,callback):
    if filename.endswith(".dat"):
        return load_tracecmd(filename,callback)
    fid = open(filename,"r")

    # the base regular expressions
    event_re = re.compile(
        r'\s*(.+)-([0-9]+)\s+\[([0-9]+)\]\s+([0-9.]+): (.*): (.*)')
    function_re = re.compile(
        r'\s*(.+)-([0-9]+)\s+\[([0-9]+)\]\s+([0-9.]+): (.*) <-(.*)')
    last_timestamp = 0
    linenumber = 0
    for line in fid:
        linenumber+=1
        line = line.rstrip()
        res = event_re.match(line)
        if res:
            groups = res.groups()
            event_name = groups[4]
            event = {
                'linenumber': linenumber,
                'comm' : groups[0],
                'pid' :  int(groups[1]),
                'cpu' : int(groups[2]),
                'timestamp' : int(float(groups[3])*1000000),
                'event' : event_name,
                'event_arg' : groups[5]
                }
            if last_timestamp == event['timestamp']:
                event['timestamp']+=1
            last_timestamp = event['timestamp']
            to_match = event['event_arg']
            try:
                for name,regex,func in events_re[event_name]:
                    res = regex.search(to_match)
                    if res:
                        func(event,res.groups())
            except KeyError:
                pass
            callback(Event(event))
            continue

        res = function_re.match(line)
        if res:
            event = {
                'linenumber': linenumber,
                'comm' : res.group(1),
                'pid' :  int(res.group(2)),
                'cpu' : int(res.group(3)),
                'timestamp' : int(float(res.group(4))*1000000),
                'event':'function',
                'callee' : res.group(5),
                'caller' : res.group(6)
                }
            callback(Event(event))
            continue
    fid.close()
#### TEST ######################################################################
if __name__ == "__main__":
    def callback(event):
        #print event.__dict__
        pass
    parse_ftrace(sys.argv[1],callback)

#### EOF ######################################################################
