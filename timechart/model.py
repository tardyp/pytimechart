# timechart project
# the timechart model with all loading facilities

from numpy import amin, amax, arange, searchsorted, sin, pi, linspace
import numpy as np
import traceback
import re
from enthought.traits.api import HasTraits, Instance, Str, Float,Delegate,\
    DelegatesTo, Int, Long, Enum, Color, List, Bool, CArray, Property, cached_property, String, Button
from enthought.traits.ui.api import Group, HGroup, Item, View, spring, Handler,VGroup,TableEditor
from enthought.enable.colors import ColorTrait
from process_table import process_table_editor
import colors

import numpy
import sys

def _pretty_time(time):
    if time > 1000000:
        time = time/1000000.
        return "%.1f s"%(time)
    if time > 1000:
        time = time/1000.
        return "%.1f ms"%(time)
    return "%.1f us"%(time)

class tcGeneric(HasTraits):
    name = String
    start_ts = CArray
    end_ts = CArray
    types = CArray
    has_comments = Bool(True)
    total_time = Property(Int)
    max_types = Property(Int)
    max_latency = Property(Int)
    max_latency_ts = Property(CArray)

    @cached_property
    def _get_total_time(self):
        return sum(self.end_ts-self.start_ts)
    @cached_property
    def _get_max_types(self):
        return amax(self.types)
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

    # UI traits
    default_bg_color = Property(ColorTrait)
    bg_color = Property(ColorTrait)
    @cached_property
    def _get_bg_color(self):
        return colors.get_traits_color_by_name("idle_bg")

class tcIdleState(tcGeneric):
    def get_comment(self,i):
        return colors.get_colorname_by_id(self.types[i])
class tcFrequencyState(tcGeneric):
    def get_comment(self,i):
        return "%d"%(self.types[i])

class tcProcess(tcGeneric):
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
    comments = []
    has_comments = Bool(True)
    show = Bool(True)
    process_type = String
    project = None
    @cached_property
    def _get_name(self):
        return "%s:%d (%s)"%(self.comm,self.pid, _pretty_time(self.total_time))

    def get_comment(self,i):
        if len(self.comments)>i:
            return "%s"%(self.comments[int(i)])
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
        return colors.get_traits_color_by_name(self.process_type+"_bg")

    def _get_bg_color(self):
        if self.project != None and self in self.project.selected:
            return  colors.get_traits_color_by_name("selected_bg")
        return self.default_bg_color


class tcProject(HasTraits):
    c_states = List(tcGeneric)
    p_states = List(tcGeneric)
    processes = List(tcProcess)
    selected =  List(tcProcess)
    filtered_processes = List(tcProcess)
    plot_redraw = Long()
    filter =  Str("")
    filter_invalid = Property(depends_on="filter")
    filename = Str("")
    power_event = CArray
    num_cpu = Property(Int,depends_on='c_states')
    num_process = Property(Int,depends_on='process')
    traits_view = View(
        VGroup(Item('filter',invalid="filter_invalid")),
        Item( 'filtered_processes',
              show_label  = False,
              height=40,
              editor      = process_table_editor
              )
        )
    first_ts = 0
    def _get_filter_invalid(self):
        try:
            r = re.compile(self.filter)
        except:
            return True
        return False
    def _filter_changed(self):
        try:
            r = re.compile(self.filter)
        except:
            return False
        self.filtered_processes = filter(lambda p:r.search(p.comm), self.processes)
    def _processes_changed(self):
        self._filter_changed()
    def _on_show(self):
        for i in self.selected:
            i.show = True
        self.plot_redraw +=1
    def _on_hide(self):
        for i in self.selected:
            i.show = False
        self.plot_redraw +=1
    def _on_select_all(self):
        if self.selected == self.processes:
            self.selected = []
        else:
            self.selected = self.processes
        self.plot_redraw +=1

    def _on_invert(self):
        for i in self.filtered_processes:
            i.show = not i.show
        self.plot_redraw +=1

    @cached_property
    def _get_num_cpu(self):
        return len(self.c_states)
    def _get_num_process(self):
        return len(self.processes)
    def process_list_selected(self, selection):
        print selection
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
    def get_selection_text(self,start,end):
        low_line = -1
        high_line = -1
        low_i = searchsorted(self.timestamps,start)
        high_i = searchsorted(self.timestamps,end)
        low_line = self.linenumbers[low_i]
        high_line = self.linenumbers[high_i]
        return self.get_partial_text(self.filename, low_line, high_line)
######### generic parsing part ##########


    def generic_find_process(self,pid,comm,ptype):
        if self.tmp_process.has_key((pid,comm)):
            return self.tmp_process[(pid,comm)]
        tmp = {'type':ptype,'comm':comm,'pid':pid,'start_ts':[],'end_ts':[],'types':[],'cpus':[],'comments':[]}
        if not (pid==0 and comm =="swapper"):
            self.tmp_process[(pid,comm)] = tmp
        return tmp

    def generic_process_start(self,process,event, build_p_stack=True):
        if process['comm']=='swapper' and process['pid']==0:
            return # ignore swapper event
        if len(process['start_ts'])>len(process['end_ts']):
            process['end_ts'].append(event.timestamp)
        if self.first_ts == 0:
            self.first_ts = event.timestamp
        self.cur_process_by_pid[process['pid']] = process
        if build_p_stack :
            p_stack = self.cur_process[event.common_cpu]
            if p_stack:
                p = p_stack[-1]
                if len(p['start_ts'])>len(p['end_ts']):
                    p['end_ts'].append(event.timestamp)
                # mark old process to wait for cpu
                p['start_ts'].append(int(event.timestamp))
                p['types'].append(colors.get_color_id("waiting_for_cpu"))
                p['cpus'].append(event.common_cpu)
                p_stack.append(process)
            else:
                self.cur_process[event.common_cpu] = [process]
        # mark process to use cpu
        process['start_ts'].append(event.timestamp)
        process['types'].append(colors.get_color_id("running"))
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
                elif p['comm'] != process['comm']:
                    # this is the fork and exec case.
                    # fix the temporary process that had the comm of the parent
                    # remove old pid,comm from process list
                    del self.tmp_process[(p['pid'],p['comm'])]
                    # add new pid,comm to process list
                    p['comm'] = process['comm']
                    self.tmp_process[(p['pid'],p['comm'])] = p
                    if len(p['start_ts'])>len(p['end_ts']):
                        p['end_ts'].append(event.timestamp)

                if p_stack:
                    p = p_stack[-1]
                    if len(p['start_ts'])>len(p['end_ts']):
                        p['end_ts'].append(event.timestamp)
                    # mark old process to run on cpu 
                    p['start_ts'].append(event.timestamp)
                    p['types'].append(colors.get_color_id("running"))
                    p['cpus'].append(event.common_cpu)

    def do_event_sched_switch(self,event):
        prev = self.generic_find_process(event.prev_pid,event.prev_comm,"user_process")
        next = self.generic_find_process(event.next_pid,event.next_comm,"user_process")

        self.generic_process_end(prev,event)

        if event.__dict__.has_key('prev_state') and event.prev_state == 'R':# mark prev to be waiting for cpu
            prev['start_ts'].append(event.timestamp)
            prev['types'].append(colors.get_color_id("waiting_for_cpu"))
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
        process = self.generic_find_process(0,"%sirq%d:%s"%(soft,event.irq,event.name),soft+"irq")
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
        try:
            if event.ret=="unhandled":
                process['types'][-1]=4
	except:
	    pass
    def do_event_softirq_entry(self,event):
        event.irq = event.vec
        event.name = ""
        return self.do_event_irq_handler_entry(event,"soft")
    def do_event_softirq_exit(self,event):
        event.irq = event.vec
        event.name = ""
        return self.do_event_irq_handler_exit(event,"soft")

    def do_event_workqueue_execution(self,event):
        process = self.generic_find_process(0,"work:%s"%(event.func),"work")
        self.generic_process_start(process,event)
        self.generic_process_end(process,event)

    def do_function_default(self,event):
        process = self.generic_find_process(0,"kernel function:%s"%(event.callee),"function")
        self.generic_process_start(process,event)
        self.generic_process_end(process,event)

    def do_event_default(self,event):
        event.name = event.event.split(":")[0]
        process = self.generic_find_process(0,"event:%s"%(event.name),"event")
        self.generic_process_start(process,event)
        process['comments'].append(event.event)
        self.generic_process_end(process,event)


    def start_parsing(self, get_partial_text):
        # we build our data into python data formats, who are resizeable
        # once everything is parsed, we will transform it into numpy array, for fast access
        self.tmp_c_states = []
        self.tmp_p_states = []
        self.tmp_process = {}
        self.timestamps = []
        self.linenumbers = []
        self.cur_process_by_pid = {}
        self.wake_events = []
        self.cur_process = [None]*20
        self.last_irq={}
        self.last_spi=[]
        self.missed_power_end = 0
        self.get_partial_text = get_partial_text
        self.methods = {}
        for name in dir(self):
            method = getattr(self, name)
            if callable(method):
                self.methods[name] = method
        import plugin
        colors.parse_colors(plugin.get_plugins_additional_colors())
        self.plugin_methods = plugin.get_plugins_additional_methods()
        self.process_types = {
            "irq":(tcProcess, plugin.IRQ_CLASS),
            "softirq":(tcProcess, plugin.IRQ_CLASS),
            "work":(tcProcess, plugin.WORK_CLASS),
            "function":(tcProcess, plugin.MISC_TRACES_CLASS),
            "event":(tcProcess, plugin.MISC_TRACES_CLASS),
            "kernel_process":(tcProcess, plugin.KERNEL_CLASS),
            "user_process":(tcProcess, plugin.KERNEL_CLASS)}
        self.process_types.update(plugin.get_plugins_additional_process_types())
    def finish_parsing(self):
        #put generated data in unresizable numpy format
        c_states = []
        i=0
        for tc in self.tmp_c_states:
            t = tcIdleState(name='cpu%d'%(i))
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
            t = tcFrequencyState(name='cpu%d'%(i))
            t.start_ts = numpy.array(tc['start_ts'])
            t.end_ts = numpy.array(tc['end_ts'])
            t.types = numpy.array(tc['types'])
            i+=1
            p_states.append(t)
        self.wake_events = numpy.array(self.wake_events,dtype=[('waker',tuple),('wakee',tuple),('time','uint64')])
        self.p_states=p_states
        processes = []
        last_ts = 0
        for pid,comm in self.tmp_process:
            tc = self.tmp_process[pid,comm]
            if len(tc['end_ts'])>0 and last_ts < tc['end_ts'][-1]:
                last_ts = tc['end_ts'][-1]
        for pid,comm in self.tmp_process:
            tc = self.tmp_process[pid,comm]
            if self.process_types.has_key(tc['type']):
                klass, order = self.process_types[tc['type']]
                t = klass(pid=pid,comm=comm,project=self)
            else:
                t = tcProcess(pid=pid,comm=comm,project=self)
            while len(tc['start_ts'])>len(tc['end_ts']):
                tc['end_ts'].append(last_ts)
            t.start_ts = numpy.array(tc['start_ts'])
            t.end_ts = numpy.array(tc['end_ts'])
            t.types = numpy.array(tc['types'])
            t.cpus = numpy.array(tc['cpus'])
            t.comments = tc['comments'] #numpy.array(tc['comments'])
            t.process_type = tc["type"]
            processes.append(t)
        def cmp_process(x,y):
            # sort process by type, pid, comm
            def type_index(t):
                try:
                    return self.process_types[t][1]
                except ValueError:
                    return len(order)+1
            c = cmp(type_index(x.process_type),type_index(y.process_type))
            if c != 0:
                return c
            c = cmp(x.pid,y.pid)
            if c != 0:
                return c
            c = cmp(x.comm,y.comm)
            return c

        processes.sort(cmp_process)
        self.processes = processes
        self.p_states=p_states
        self.tmp_c_states = []
        self.tmp_p_states = []
        self.tmp_process = {}

    def ensure_cpu_allocated(self,cpu):
        # ensure we have enough per_cpu p/c_states timecharts
        while len(self.tmp_c_states)<=cpu:
            self.tmp_c_states.append({'start_ts':[],'end_ts':[],'types':[]})
        while len(self.tmp_p_states)<=cpu:
            self.tmp_p_states.append({'start_ts':[],'end_ts':[],'types':[]})

    def handle_trace_event(self,event):
        callback = "do_event_"+event.event
        self.linenumbers.append(event.linenumber)
        self.timestamps.append(event.timestamp)
        if event.event=='function':
            callback = "do_function_"+event.callee
        if self.plugin_methods.has_key(callback):
            try:
                self.plugin_methods[callback](self,event)
                return
            except AttributeError:
                if not hasattr(self.plugin_methods[callback],"num_exc"):
                    self.plugin_methods[callback].num_exc = 0
                self.plugin_methods[callback].num_exc += 1
                if self.plugin_methods[callback].num_exc <10:
                    print "bug in ",self.plugin_methods[callback],"still continue.."
                    traceback.print_exc()
                    print event
                if self.plugin_methods[callback].num_exc == 10:
                    print self.plugin_methods[callback], "is too buggy, disabling, please report bug!"
                    del self.plugin_methods[callback]
        if self.methods.has_key(callback):
            self.methods[callback](event)
        elif event.event=='function':
            self.do_function_default(event)
        else:
            self.do_event_default(event)

