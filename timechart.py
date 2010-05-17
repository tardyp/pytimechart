#!/usr/bin/python
#------------------------------------------------------------------------------
import os,sys
from enthought.etsconfig.api import ETSConfig
#ETSConfig.toolkit = 'qt4'
ETSConfig.toolkit = 'wx'
from timechart.timechart_window import TimechartWindow
from timechart.timechart import TimechartProject
from enthought.pyface.api import GUI

# workaround bug in kiva's font manager that fails to find a correct default font on linux
if os.name=="posix":
    from  enthought.kiva.fonttools.font_manager import fontManager, FontProperties
    font = FontProperties()
    font.set_name("DejaVu Sans")
    fontManager.defaultFont = fontManager.findfont(font)

class Event():
	def __init__(self,sec,nsec,**kw):
		self.__dict__=kw
		self.timestamp = sec*1000000+nsec/1000

def trace_begin():
	global proj
	proj = TimechartProject()
	proj.start_parsing()
def trace_end():
	proj.finish_parsing()
	# Create and open the main window.
	window = TimechartWindow(project = proj)
	window.configure_traits()

def sched__sched_switch(event_name, context, common_cpu,
	common_secs, common_nsecs, common_pid, common_comm,
	prev_comm, prev_pid, prev_prio, prev_state, 
	next_comm, next_pid, next_prio):
	proj.do_event_sched_switch(
		Event(common_secs, common_nsecs,cpu=common_cpu,
		      prev_pid=prev_pid,prev_comm=prev_comm,prev_prio=prev_prio,prev_state=prev_state,
		      next_pid=next_pid,next_comm=next_comm,next_prio=next_prio))

def sched__sched_wakeup(event_name, context, common_cpu,
	common_secs, common_nsecs, common_pid, common_comm,
	comm, pid, prio, success, 
	target_cpu):
	proj.do_event_sched_wakeup(
		Event(common_secs, common_nsecs,cpu=common_cpu,
		      pid=common_pid,comm=common_comm,
		      wakee_comm=comm,wakee_pid=pid,success=success))

def power__power_end(event_name, context, common_cpu,
	common_secs, common_nsecs, common_pid, common_comm,
	dummy):
	proj.do_event_power_end(Event(common_secs, common_nsecs,cpu=common_cpu))

def power__power_frequency(event_name, context, common_cpu,
	common_secs, common_nsecs, common_pid, common_comm,
	type, state):
	global proj
	proj.do_event_power_frequency(Event(common_secs, common_nsecs,cpu=common_cpu,type=type,state=state))

def power__power_start(event_name, context, common_cpu,
	common_secs, common_nsecs, common_pid, common_comm,
	type, state):
	proj.do_event_power_start(Event(common_secs, common_nsecs,cpu=common_cpu,type=type,state=state))

def trace_unhandled(event_name, context, common_cpu, common_secs, common_nsecs,
		common_pid, common_comm):
	print "unhandled!",event_name


import wx
def open_file():
    dlg = wx.FileDialog(None, "Choose a file", "", "", "*.txt", wx.OPEN)
    rv = None
    if dlg.ShowModal() == wx.ID_OK:
        filename=dlg.GetFilename()
        dirname=dlg.GetDirectory()
        rv = os.path.join(dirname, filename)

    dlg.Destroy()
    return rv
    
# Application entry point if not used with perf.
prof=0
if __name__ == '__main__' and not os.environ.has_key('PERF_EXEC_PATH'):
    # Create the GUI (this does NOT start the GUI event loop).
    gui = GUI()
    import sys
    proj = TimechartProject()
    if len(sys.argv)>1:
        fn = sys.argv[1]
    else:
        fn = open_file()
        if not fn:
            sys.exit(1)
    if prof:
        import cProfile
        cProfile.run('proj.load(fn)','timechart_load.prof')
    else:
        proj.load(fn)
    # Create and open the main window.
    window = TimechartWindow(project = proj)
    window.edit_traits()
    # Start the GUI event loop!
    if prof:
        import cProfile
        cProfile.run('gui.start_event_loop()','timechart.prof')
    else:
        gui.start_event_loop()

##### EOF #####################################################################

