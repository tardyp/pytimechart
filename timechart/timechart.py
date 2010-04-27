# timechart project
# the timechart model with all loading facilities

from numpy import amin, amax, arange, searchsorted, sin, pi, linspace
import numpy as np
from enthought.traits.api import HasTraits, Instance, Str, Float,Delegate,\
    DelegatesTo,Int,Enum,Color,List,Bool,CArray,Property, cached_property, String
from enthought.traits.ui.api import Group, HGroup, Item, View, spring, Handler,VGroup
from enthought.enable.colors import ColorTrait

import cPickle
import random
import numpy
import sys 
def read_u64(fid,num):
    """helper read function"""
    a1 = numpy.fromstring(fid.read(num*8),'uint64')
    if num ==1:
        return a1[0]
    return a1
def read_u64_struct(fid,num,fields):
    fields = [(i,'uint64') for i in fields]
    a1 = numpy.fromstring(fid.read(num*8*len(fields)),fields,num)
    return a1
class Timechart(HasTraits):
    name = String
    start_ts = CArray 
    end_ts = CArray 
    types = CArray 
    has_comments = Bool(True)
    total_time = Property(Int)
    max_types = Property(Int)
    bg_color = Property(ColorTrait)
    max_latency = Property(Int)
    max_latency_ts = Property(CArray)
    
    @cached_property
    def _get_total_time(self):
        return sum(self.end_ts-self.start_ts)
    @cached_property
    def _get_max_types(self):
        return amax(self.types)
    @cached_property
    def _get_bg_color(self):
        return (1,.9,.9,1)
    def random(self,length,vrange,hrange):
        start_ts = []
        end_ts = []
        types = []
        t = 0
        while t < length:
            t += random.randint(0,hrange)
            start_ts.append(t)
            types.append(random.randint(0,vrange))
            t += random.randint(0,hrange)
            end_ts.append(t)
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.types = types
    def get_comment(self,i):
        return "%d"%(self.types[i])
    @cached_property
    def _get_max_latency(self):
        return -1
class Process(Timechart):
    name = Property(String) # overide TimeChart
    # start_ts=CArray # inherited from TimeChart
    # end_ts=CArray # inherited from TimeChart
    # values = CArray   # inherited from TimeChart
    pid = Int
    ppid = Int
    comm = String
    cpus = CArray
    comments = CArray
    has_comments = Bool(True)
    project = None
    @cached_property
    def _get_name(self):
        if self.total_time > 1000000:
            total_time = self.total_time/1000000.
            return "%s:%d (%.1f s)"%(self.comm,self.pid,total_time)
        if self.total_time > 1000:
            total_time = self.total_time/1000.
            return "%s:%d (%.1f ms)"%(self.comm,self.pid,total_time)
        total_time = self.total_time
        return "%s:%d (%.1f us)"%(self.comm,self.pid,total_time)
    def get_comment(self,i):
        if len(self.comments)>i:
            return "%d"%(self.comments[i])
        elif len(self.cpus)>i:
            return "%d"%(self.cpus[i])
        else:
            return ""
    @cached_property
    def _get_max_latency(self):
        if self.pid==0 and self.comm.startswith("irq"):
            return 1000

    @cached_property
    def _get_max_latency_ts(self):
        if self.max_latency > 0:
            indices = np.nonzero((self.end_ts - self.start_ts) > self.max_latency)[0]
            print indices
            return np.array(sorted(map(lambda i:self.start_ts[i], indices)))
        return []
                                
        
    @cached_property
    def _get_bg_color(self):
        if self.max_latency >0 and max(self.end_ts - self.start_ts)>self.max_latency:
            return (1,.1,.1,1)
        if self.pid==0:
            if self.comm.startswith("irq"):
                return (.9,1,.9,1)
            if self.comm.startswith("softirq"):
                return (.7,1,.7,1)
            if self.comm.startswith("work"):
                return (.5,1,.5,1)
            return (.3,1,.3,1)
        else:
            return (.9,.9,1,1)
    
class TimechartProject(HasTraits):

    c_states = List(Timechart)
    p_states = List(Timechart)
    processes = List(Process)
    power_event = CArray
    num_cpu = Property(Int,depends_on='c_states')
    num_process = Property(Int,depends_on='process')
    @cached_property
    def _get_num_cpu(self):
        return len(self.c_states)
    def _get_num_process(self):
        return len(self.processes)

    def load_random(self,num_cpu,num_process,length):
        c_states = [ Timechart(name="CCPU%d"%(i)) for i in xrange(num_cpu)]
        p_states = [ Timechart(name="FCPU%d"%(i)) for i in xrange(num_cpu)]
        processes = [ Process(comm="program#%d"%(i),pid=i,ppid=i-1) for i in xrange(num_process)]
        
        for i in xrange(num_cpu):
            c_states[i].random(length,6,100)
            p_states[i].random(length,1000,1000)
        for i in xrange(num_process):
            processes[i].random(length,2,1000)
        self.c_states = c_states
        self.p_states = p_states
        self.processes = processes
    def load(self,filename):
        if filename.endswith(".tmct"):
            return self.load_tmct(filename)
        else:
            return self.load_ftrace(filename)

######### ftrace parsing part ##########

    def ftrace_power_frequency(self,event):
        if event.type==2:# p_state
            tc = self.tmp_p_states[event.cpu]
            tc['start_ts'].append(event.timestamp)
            tc['types'].append(event.state)
    def ftrace_power_start(self,event):
        if event.type==1:# c_state
            tc = self.tmp_c_states[event.cpu]
            if len(tc['start_ts'])>len(tc['end_ts']):
                tc['end_ts'].append(event.timestamp)
                self.missed_power_end +=1
                if self.missed_power_end < 10:
                    print "warning: missed power_end"
                if self.missed_power_end == 10:
                    print "warning: missed power_end: wont warn anymore!"
                    
            tc['start_ts'].append(event.timestamp)
            tc['types'].append(event.state)
    def ftrace_power_end(self,event):
        tc = self.tmp_c_states[event.cpu]
        if len(tc['start_ts'])>len(tc['end_ts']):
            tc['end_ts'].append(event.timestamp)

    def ftrace_find_process(self,pid,comm):
        if self.tmp_process.has_key((pid,comm)):
            return self.tmp_process[(pid,comm)]
        tmp = {'comm':comm,'pid':pid,'start_ts':[],'end_ts':[],'types':[],'cpus':[],'comments':[]}
        if not (pid==0 and comm =="swapper"):
            self.tmp_process[(pid,comm)] = tmp
        return tmp

    def ftrace_process_start(self,process,event):
        if process['comm']=='swapper' and process['pid']==0:
            return # ignore swapper event
        if len(process['start_ts'])>len(process['end_ts']):
            process['end_ts'].append(event.timestamp)

        self.cur_process_by_pid[process['pid']] = process
        p_stack = self.cur_process[event.cpu]
        if p_stack:
            p = p_stack[-1]
            if len(p['start_ts'])>len(p['end_ts']):
                p['end_ts'].append(event.timestamp)
            # mark old process to wait for cpu 
            p['start_ts'].append(event.timestamp)
            p['types'].append(2) 
            p['cpus'].append(event.cpu)
            p_stack.append(process)
        else:
            self.cur_process[event.cpu] = [process]
        # mark process to use cpu
        process['start_ts'].append(event.timestamp)
        process['types'].append(1) 
        process['cpus'].append(event.cpu)
    def ftrace_process_end(self,process,event):
        if process['comm']=='swapper' and process['pid']==0:
            return # ignore swapper event
        if len(process['start_ts'])>len(process['end_ts']):
            process['end_ts'].append(event.timestamp)
        p_stack = self.cur_process[event.cpu]
        if p_stack:
            p = p_stack.pop()
            if p['pid'] != process['pid']:
                print  "warning: process premption stack following failure on CPU",event.cpu, p['comm'],p['pid'],process['comm'],process['pid'],map(lambda a:"%s:%d"%(a['comm'],a['pid']),p_stack),event.linenumber
                p_stack = []
            if p_stack:
                p = p_stack[-1]
                if len(p['start_ts'])>len(p['end_ts']):
                    p['end_ts'].append(event.timestamp)
                # mark old process to run on cpu 
                p['start_ts'].append(event.timestamp)
                p['types'].append(1)
                p['cpus'].append(event.cpu)
        
    def ftrace_sched_switch(self,event):
        prev = self.ftrace_find_process(event.prev_pid,event.prev_comm)
        next = self.ftrace_find_process(event.next_pid,event.next_comm)

        self.ftrace_process_end(prev,event)

        if event.__dict__.has_key('prev_state') and event.prev_state == 'R':# mark prev to be waiting for cpu
            prev['start_ts'].append(event.timestamp)
            prev['types'].append(2) 
            prev['cpus'].append(event.cpu)

        self.ftrace_process_start(next,event)
        
    def ftrace_sched_wakeup(self,event):
        p_stack = self.cur_process[event.cpu]
        if p_stack:
            p = p_stack[-1]
            self.wake_events.append(((p['comm'],p['pid']),(event.wakee_comm,event.wakee_pid),event.timestamp))
        else:
            self.wake_events.append(((event.comm,event.pid),event.wakee_pid,event.timestamp))
    def ftrace_irq_handler_entry(self,event,soft=""):
        process = self.ftrace_find_process(0,"%sirq%d:%s"%(soft,event.irq,event.handler))
        self.last_irq[(event.irq,soft)] = process
        self.ftrace_process_start(process,event)
    def ftrace_irq_handler_exit(self,event,soft=""):
        try:
            process = self.last_irq[(event.irq,soft)]
        except KeyError:
            print "error did not find last irq"
            print self.last_irq.keys(),(event.irq,soft)
            return
        self.ftrace_process_end(process,event)
    def ftrace_softirq_entry(self,event):
        return self.ftrace_irq_handler_entry(event,"soft")
    def ftrace_softirq_exit(self,event):
        return self.ftrace_irq_handler_exit(event,"soft")
        
    def ftrace_spi_sync(self,event):
        process = self.ftrace_find_process(0,"spi:%s"%(event.caller))
        self.last_spi.append(process)
        self.ftrace_process_start(process,event)
    def ftrace_spi_complete(self,event):
        process = self.last_spi.pop(0)
        self.ftrace_process_end(process,event)
    def ftrace_spi_async(self,event):
        if event.caller != 'spi_sync':
            self.ftrace_spi_sync(event)
    def ftrace_workqueue_execution(self,event):
        process = self.ftrace_find_process(0,"work:%s"%(event.func))
        self.ftrace_process_start(process,event)
        self.ftrace_process_end(process,event)
        
    def ftrace_function_default(self,event):
        process = self.ftrace_find_process(0,"kernel function:%s"%(event.callee))
        self.ftrace_process_start(process,event)
        self.ftrace_process_end(process,event)
    def ftrace_event_default(self,event):
        process = self.ftrace_find_process(0,"event:%s"%(event.event))
        self.ftrace_process_start(process,event)
        self.ftrace_process_end(process,event)

    def ftrace_callback(self,event):
        # ensure we have enough per_cpu p/s_states timecharts
        while len(self.tmp_c_states)<=event.cpu:
            self.tmp_c_states.append({'start_ts':[],'end_ts':[],'types':[]})
        while len(self.tmp_p_states)<=event.cpu:
            self.tmp_p_states.append({'start_ts':[],'end_ts':[],'types':[]})


        callback = "ftrace_"+event.event
        if event.event=='function':
            callback = "ftrace_"+event.callee
        if self.methods.has_key(callback):
            self.methods[callback](event)
        elif event.event=='function':
            self.ftrace_function_default(event)
        else:
            self.ftrace_event_default(event)

    def load_ftrace(self,filename):
        from ftrace import parse_ftrace
        self.tmp_c_states = []
        self.tmp_p_states = []
        self.tmp_process = {}
        self.cur_process_by_pid = {}
        self.wake_events = []
        self.cur_process = [None]*20
        self.last_irq={}
        self.last_spi=[]
        self.methods = {}
        self.missed_power_end = 0
        for name in dir(self):
            method = getattr(self, name)
            if callable(method):
                self.methods[name] = method
        parse_ftrace(filename,self.ftrace_callback)
        
        #put generated data in unresizable numpy format
        c_states = []
        i=0
        for tc in self.tmp_c_states:
            t = Timechart(name='cpu%d'%(i))
            while len(tc['start_ts'])>len(tc['end_ts']):
                tc['end_ts'].append(tc['start_ts'][-1])
            t.start_ts = numpy.array(tc['start_ts'])
            t.end_ts = numpy.array(tc['end_ts'])
            t.types = numpy.array(tc['types'])
            c_states.append(t)
            i+=1
        self.c_states=c_states
        i=0
        p_states = []
        for tc in self.tmp_p_states:
            t = Timechart(name='cpu%d'%(i))
            t.start_ts = numpy.array(tc['start_ts'])
            t.end_ts = numpy.array(tc['end_ts'])
            t.types = numpy.array(tc['types'])
            i+=1
            p_states.append(t)
        self.wake_events = numpy.array(self.wake_events,dtype=[('waker',tuple),('wakee',tuple),('time','uint64')])
        self.p_states=p_states
        processes = []
        for pid,comm in self.tmp_process:
            t = Process(pid=pid,comm=comm)
            tc = self.tmp_process[pid,comm]
            while len(tc['start_ts'])>len(tc['end_ts']):
                tc['end_ts'].append(tc['start_ts'][-1])
            t.start_ts = numpy.array(tc['start_ts'])
            t.end_ts = numpy.array(tc['end_ts'])
            t.types = numpy.array(tc['types'])
            t.cpus = numpy.array(tc['cpus'])
            t.comments = numpy.array(tc['comments'])
            processes.append(t)
        processes.sort(lambda x,y:cmp(x.name,y.name))
        processes.sort(lambda x,y:cmp(x.pid,y.pid))
        self.processes = processes
        self.p_states=p_states
        self.tmp_c_states = []
        self.tmp_p_states = []
        self.tmp_process = {}
        

########## tmct parsing part ##########
# job is done by perf buildin-timechart
# just fits the data our prefered way
    def load_tmct(self,filename):
        f = open(filename)
        numcpus = read_u64(f,1)
        self.first_time = read_u64(f,1)
        self.last_time = read_u64(f,1)
        process_list = []
        n_samples = read_u64(f,1)
        comms_dict = {}
        while n_samples < 0xffffffff:
            pid = int(read_u64(f,1))
            ppid = int(read_u64(f,1))
            comm = f.read(256)
            comm = comm[:comm.index('\0')]
            samples = read_u64_struct(f,n_samples,['start_ts','end_ts','types','cpu'])
            if n_samples>0:
                samples.sort(axis=0,order=['start_ts'])
                comms_dict[pid] = comm # @todo, a pid can have several comms
                process = Process(project = self,
                                  pid=pid,
                                  ppid=ppid,
                                  comm=comm,
                                  start_ts=samples['start_ts'],
                                  end_ts=samples['end_ts'],
                                  types=samples['types'],
                                  cpus= samples['cpu'])
                process_list.append(process)
            n_samples = read_u64(f,1)
        self.processes = process_list
        n_samples = read_u64(f,1)
        power_events = read_u64_struct(f,n_samples,['type','state','start_ts','end_ts','cpu'])
        filt = (power_events['start_ts']>0) & (power_events['end_ts']>0)
        power_events = power_events.compress(filt)
        power_events.sort(axis=0,order=['start_ts'])
        n_samples = read_u64(f,1)
        self.wake_events = read_u64_struct(f,n_samples,['waker','wakee','time'])
        self.wake_events.sort(axis=0,order=['time'])

        c_states = []
        p_states = []
        for i in xrange(numcpus):
            filt = (power_events['type']==1) & (power_events['cpu']==i)
            samples = numpy.compress(filt,power_events)
            c_state = Timechart(name="cpu%d"%(i),
                                start_ts=samples['start_ts'],
                                end_ts=samples['end_ts'],
                                types=samples['state'])
            c_states.append(c_state)
            filt = (power_events['type']==2) & (power_events['cpu']==i)
            samples = numpy.compress(filt,power_events)
            p_state = Timechart(name="cpu%d"%(i),
                                start_ts=samples['start_ts'],
                                end_ts=samples['end_ts'],
                                types=samples['state'])
            p_states.append(p_state)
        self.c_states = c_states
        self.p_states = p_states
