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
    ('sched_wakeup','task %s:%d [%d] success=%d [%d]','wakee_comm', 'wakee_pid', 'wakee_prio', 'success', 'wakee_cpu'),
    ('sched_wakeup','task %s:%d [%d] success=%d','wakee_comm', 'wakee_pid', 'wakee_prio', 'success'),
    ('softirq_entry','softirq=%d action=%s','irq','handler'),
    ('softirq_exit','softirq=%d action=%s','irq','handler'),
    ('irq_handler_entry', 'irq=%d handler=%s','irq','handler'),
    ('irq_handler_exit', 'irq=%d return=%s','irq','return'),
    ('workqueue_execution','thread=%s func=%s\\+%s/%s','thread','func','func_offset','func_size')
    ]

# pre process our descriptions to transform it into re
events_re = []
for event in events_desc:
    name = event[0]
    printk = event[1]
    args = event[2:]
    args_l = []
    for i in '()[]':
        printk = printk.replace(i,'\\'+i)
    # we replace %d %s by the equivalent regular expression, and keep the type in memory for later
    for arg in args:
        idx = printk.index('%')
        format = printk[idx+1]
        if format=='d':
            filt=int
            regex="([0-9]+)"
        elif format=='s':
            filt=str
            regex="(.*)"
        printk = printk.replace("%"+format,regex,1)
        args_l.append((arg,filt))
    events_re.append((name,re.compile(printk),args_l))

# event class passed to callback, this is more convenient than passing a dictionary
class Event:
    def __init__(self,event):
        self.__dict__=event

def parse_ftrace(filename,callback):
    fid = open(filename,"r")

    # the base regular expressions
    event_re = re.compile(
        r'\s*(.+)-([0-9]+)\s+\[([0-9]+)\]\s+([0-9.]+): (.*): (.*)')
    function_re = re.compile(
        r'\s*(.+)-([0-9]+)\s+\[([0-9]+)\]\s+([0-9.]+): (.*) <-(.*)')
    last_timestamp = 0
    for line in fid:
        line = line.rstrip()
        event=None
        res = event_re.match(line)
        if res:
            event = {
                'comm' : res.group(1),
                'pid' :  int(res.group(2)),
                'cpu' : int(res.group(3)),
                'timestamp' : int(float(res.group(4))*1000000),
                'event' : res.group(5),
                'event_arg' : res.group(6)
                }
            if last_timestamp == event['timestamp']:
                event['timestamp']+=1
            last_timestamp = event['timestamp']
            to_match = event['event_arg']
            for name,regex,args in events_re:
                res = regex.search(to_match)
                if res:
                    i=1
                    for name,typ in args:
                        event[name] = typ(res.group(i))
                        i+=1
            callback(Event(event))
            continue

        res = function_re.match(line)
        if res:
            event = {
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
        print event.__dict__
    parse_ftrace("trace_test.txt",callback)

#### EOF ######################################################################
