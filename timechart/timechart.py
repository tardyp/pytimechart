# timechart project
# the timechart model with all loading facilities

from numpy import amin, amax, arange, searchsorted, sin, pi, linspace
import numpy as np
from enthought.traits.api import HasTraits, Instance, Str, Float,Delegate,\
    DelegatesTo,Int,Long,Enum,Color,List,Bool,CArray,Property, cached_property, String, Button
from enthought.traits.ui.api import Group, HGroup, Item, View, spring, Handler,VGroup,TableEditor
from enthought.enable.colors import ColorTrait
from enthought.traits.ui.table_column \
    import ObjectColumn, ExpressionColumn

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
    default_bg_color = Property(ColorTrait)
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
    def get_partial_tables(self,start,end):
        low_i = searchsorted(self.end_ts,start)
        high_i = searchsorted(self.start_ts,end)
        ends = self.end_ts[low_i:high_i].copy()
        starts = self.start_ts[low_i:high_i].copy()
        if len(starts)==0:
            return np.array([]),np.array([]),[]
        # take care of activities crossing the selection
        if starts[0]<start:
            starts[0] = start
        if ends[-1]>end:
            ends[-1] = end
        types = self.types[low_i:high_i]
        return starts,ends,types
class Process(Timechart):
    name = Property(String) # overide TimeChart
    # start_ts=CArray # inherited from TimeChart
    # end_ts=CArray # inherited from TimeChart
    # values = CArray   # inherited from TimeChart
    pid = Long
    ppid = Long
    selection_time = Long(0)
    selection_pc = Float(0)
    comm = String
    cpus = CArray
    comments = CArray
    has_comments = Bool(True)
    show = Bool(True)
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
            return np.array(sorted(map(lambda i:self.start_ts[i], indices)))
        return []

    @cached_property
    def _get_default_bg_color(self):
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
    def _get_bg_color(self):
        if self.project != None and self in self.project.selected:
            return  (0.678, 0.847, 0.902, 1.0)
        return self.default_bg_color

# we subclass ObjectColumn to be able to change the text color depending of whether the Process is shown
class coloredObjectColumn(ObjectColumn):
    def get_text_color(self,i):
        if i.show:
            return "#111111"
        else:
            return  "#777777"
    def get_cell_color(self,i):
        r,g,b,a = i.default_bg_color
        return "#%02X%02X%02X"%(255*r,255*g,255*b)
        
# The definition of the process TableEditor:
process_table_editor = TableEditor(
    columns = [
                coloredObjectColumn( name = 'comm',  width = 0.45 ,editable=False),
                coloredObjectColumn( name = 'pid',  width = 0.10  ,editable=False),
                coloredObjectColumn( name = 'selection_time',label="stime",  width = 0.20  ,editable=False),
                ExpressionColumn( 
                    label = 'stime%', 
                    width = 0.20,
                    expression = "'%.2f' % (object.selection_pc)" )
                ],
    deletable   = False,
    editable   = False,
    sort_model  = False,
    auto_size   = False,
    orientation = 'vertical',
    show_toolbar = False,
    selection_mode = 'rows',
    selected = "selected"
    )

class TimechartProject(HasTraits):
    c_states = List(Timechart)
    p_states = List(Timechart)
    processes = List(Process)
    selected =  List(Process)
    show = Button()
    hide = Button()
    selectall = Button()
    filename = Str("")
    power_event = CArray
    num_cpu = Property(Int,depends_on='c_states')
    num_process = Property(Int,depends_on='process')
    traits_view = View( 
        HGroup(Item('show'), Item('hide') ,Item('selectall',label='all'),show_labels  = False),
        Item( 'processes',
              show_label  = False,
              height=40,
              editor      = process_table_editor
              )
        )
    def _show_changed(self):
        for i in self.selected:
            i.show = True
    def _hide_changed(self):
        for i in self.selected:
            i.show = False
    def _selectall_changed(self):
        if self.selected == self.processes:
            self.selected = []
        else:
            self.selected = self.processes

    @cached_property
    def _get_num_cpu(self):
        return len(self.c_states)
    def _get_num_process(self):
        return len(self.processes)
    def process_list_selected(self, selection):
        print selection
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
        self.filename = filename
        if filename.endswith(".tmct"):
            return self.load_tmct(filename)
        else:
            return self.load_ftrace(filename)
######### stats part ##########

    def c_states_stats(self,start,end):
        l = []
        for tc in self.c_states: # walk cstates per cpus
            starts,ends,types = tc.get_partial_tables(start,end)
            stats = {}
            tot = 0
            for t in np.unique(types):
                inds = np.where(types==t)
                time = sum(ends[inds]-starts[inds])
                tot += time
                stats[t] = time
            stats[0] = (end-start)-tot
            l.append(stats)  
        return l
    def process_stats(self,start,end):
        fact = 100./(end-start)
        for tc in self.processes:
            starts,ends,types = tc.get_partial_tables(start,end)
            #@todo, need to take care of running vs waiting
            inds = np.where(types==1)
            tot = sum(ends[inds]-starts[inds])
            tc.selection_time = int(tot)
            tc.selection_pc = tot*fact

######### generic parsing part ##########


    def generic_find_process(self,pid,comm):
        if self.tmp_process.has_key((pid,comm)):
            return self.tmp_process[(pid,comm)]
        tmp = {'comm':comm,'pid':pid,'start_ts':[],'end_ts':[],'types':[],'cpus':[],'comments':[]}
        if not (pid==0 and comm =="swapper"):
            self.tmp_process[(pid,comm)] = tmp
        return tmp

    def generic_process_start(self,process,event, build_p_stack=True):
        if process['comm']=='swapper' and process['pid']==0:
            return # ignore swapper event
        if len(process['start_ts'])>len(process['end_ts']):
            process['end_ts'].append(event.timestamp)

        self.cur_process_by_pid[process['pid']] = process
        if build_p_stack :
            p_stack = self.cur_process[event.common_cpu]
            if p_stack:
                p = p_stack[-1]
                if len(p['start_ts'])>len(p['end_ts']):
                    p['end_ts'].append(event.timestamp)
                # mark old process to wait for cpu 
                p['start_ts'].append(int(event.timestamp))
                p['types'].append(2) 
                p['cpus'].append(event.common_cpu)
                p_stack.append(process)
            else:
                self.cur_process[event.common_cpu] = [process]
        # mark process to use cpu
        process['start_ts'].append(event.timestamp)
        process['types'].append(1) 
        process['cpus'].append(event.common_cpu)

    def generic_process_end(self,process,event, build_p_stack=True):
        if process['comm']=='swapper' and process['pid']==0:
            return # ignore swapper event
        if len(process['start_ts'])>len(process['end_ts']):
            process['end_ts'].append(event.timestamp)
        if build_p_stack :
            p_stack = self.cur_process[event.common_cpu]
            if p_stack:
                p = p_stack.pop()
                if p['pid'] != process['pid']:
                    print  "warning: process premption stack following failure on CPU",event.common_cpu, p['comm'],p['pid'],process['comm'],process['pid'],map(lambda a:"%s:%d"%(a['comm'],a['pid']),p_stack),event.linenumber
                    p_stack = []
                if p_stack:
                    p = p_stack[-1]
                    if len(p['start_ts'])>len(p['end_ts']):
                        p['end_ts'].append(event.timestamp)
                    # mark old process to run on cpu 
                    p['start_ts'].append(event.timestamp)
                    p['types'].append(1)
                    p['cpus'].append(event.common_cpu)
        
    def do_event_sched_switch(self,event):
        prev = self.generic_find_process(event.prev_pid,event.prev_comm)
        next = self.generic_find_process(event.next_pid,event.next_comm)

        self.generic_process_end(prev,event)

        if event.__dict__.has_key('prev_state') and event.prev_state == 'R':# mark prev to be waiting for cpu
            prev['start_ts'].append(event.timestamp)
            prev['types'].append(2) 
            prev['cpus'].append(event.common_cpu)

        self.generic_process_start(next,event)
        
    def do_event_sched_wakeup(self,event):
        p_stack = self.cur_process[event.common_cpu]
        if p_stack:
            p = p_stack[-1]
            self.wake_events.append(((p['comm'],p['pid']),(event.comm,event.pid),event.timestamp))
        else:
            self.wake_events.append(((event.common_comm,event.common_pid),(event.comm,event.pid),event.timestamp))
    def do_event_irq_handler_entry(self,event,soft=""):
        process = self.generic_find_process(0,"%sirq%d:%s"%(soft,event.irq,event.name))
        self.last_irq[(event.irq,soft)] = process
        self.generic_process_start(process,event)
    def do_event_irq_handler_exit(self,event,soft=""):
        try:
            process = self.last_irq[(event.irq,soft)]
        except KeyError:
            print "error did not find last irq"
            print self.last_irq.keys(),(event.irq,soft)
            return
        self.generic_process_end(process,event)
    def do_event_softirq_entry(self,event):
        event.irq = event.vec
        event.name = ""
        return self.do_event_irq_handler_entry(event,"soft")
    def do_event_softirq_exit(self,event):
        event.irq = event.vec
        event.name = ""
        return self.do_event_irq_handler_exit(event,"soft")
        
    def do_event_spi_sync(self,event):
        process = self.generic_find_process(0,"spi:%s"%(event.caller))
        self.last_spi.append(process)
        self.generic_process_start(process,event,False)
    def do_event_spi_complete(self,event):
        process = self.last_spi.pop(0)
        self.generic_process_end(process,event,False)
    def do_event_spi_async(self,event):
        if event.caller != 'spi_sync':
            self.do_event_spi_sync(event,False)

    def do_event_wakelock_lock(self,event):
        process = self.generic_find_process(0,"wakelock:%s"%(event.name))
        self.generic_process_start(process,event,False)
        self.wake_events.append(((event.common_comm,event.common_pid),(process['comm'],process['pid']),event.timestamp))

    def do_event_wakelock_unlock(self,event):
        process = self.generic_find_process(0,"wakelock:%s"%(event.name))
        self.generic_process_end(process,event,False)
        self.wake_events.append(((event.common_comm,event.common_pid),(process['comm'],process['pid']),event.timestamp))

    def do_event_workqueue_execution(self,event):
        process = self.generic_find_process(0,"work:%s"%(event.func))
        self.generic_process_start(process,event)
        self.generic_process_end(process,event)
        
    def do_event_power_frequency(self,event):
        self.ensure_cpu_allocated(event.common_cpu)
        if event.type==2:# p_state
            tc = self.tmp_p_states[event.common_cpu]
            tc['start_ts'].append(event.timestamp)
            tc['types'].append(event.state)

    def do_event_power_start(self,event):
        self.ensure_cpu_allocated(event.common_cpu)
        if event.type==1:# c_state
            tc = self.tmp_c_states[event.common_cpu]
            if len(tc['start_ts'])>len(tc['end_ts']):
                tc['end_ts'].append(event.timestamp)
                self.missed_power_end +=1
                if self.missed_power_end < 10:
                    print "warning: missed power_end"
                if self.missed_power_end == 10:
                    print "warning: missed power_end: wont warn anymore!"
                    
            tc['start_ts'].append(event.timestamp)
            tc['types'].append(event.state)

    def do_event_power_end(self,event):
        self.ensure_cpu_allocated(event.common_cpu)

        tc = self.tmp_c_states[event.common_cpu]
        if len(tc['start_ts'])>len(tc['end_ts']):
            tc['end_ts'].append(event.timestamp)

    def do_function_default(self,event):
        process = self.generic_find_process(0,"kernel function:%s"%(event.callee))
        self.generic_process_start(process,event)
        self.generic_process_end(process,event)

    def do_event_default(self,event):
        process = self.generic_find_process(0,"event:%s"%(event.event))
        self.generic_process_start(process,event)
        self.generic_process_end(process,event)


    def start_parsing(self):
        self.tmp_c_states = []
        self.tmp_p_states = []
        self.tmp_process = {}
        self.cur_process_by_pid = {}
        self.wake_events = []
        self.cur_process = [None]*20
        self.last_irq={}
        self.last_spi=[]
        self.missed_power_end = 0
        self.methods = {}
        for name in dir(self):
            method = getattr(self, name)
            if callable(method):
                self.methods[name] = method

    def finish_parsing(self):
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
            t = Process(pid=pid,comm=comm,project=self)
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
    def ensure_cpu_allocated(self,cpu):
        # ensure we have enough per_cpu p/s_states timecharts
        while len(self.tmp_c_states)<=cpu:
            self.tmp_c_states.append({'start_ts':[],'end_ts':[],'types':[]})
        while len(self.tmp_p_states)<=cpu:
            self.tmp_p_states.append({'start_ts':[],'end_ts':[],'types':[]})
                                     
######### ftrace specific parsing part ##########
        
    def ftrace_callback(self,event):
                                         

        callback = "do_event_"+event.event
        if event.event=='function':
            callback = "do_event_"+event.callee
        if self.methods.has_key(callback):
            self.methods[callback](event)
        elif event.event=='function':
            self.do_function_default(event)
        else:
            self.do_event_default(event)

    def load_ftrace(self,filename):
        from ftrace import parse_ftrace
        self.start_parsing()
        parse_ftrace(filename,self.ftrace_callback)
        self.finish_parsing()
