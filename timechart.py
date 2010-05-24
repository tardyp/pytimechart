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
	def __init__(self,name,kw):
		self.__dict__=kw
                self.event = name
		self.timestamp = self.common_s*1000000+self.common_ns/1000

def trace_begin():
	global proj
	proj = TimechartProject()
	proj.start_parsing()
def trace_end():
	proj.finish_parsing()
	# Create and open the main window.
	window = TimechartWindow(project = proj)
	window.configure_traits()


def trace_unhandled(event_name, context, field_dict):
    event_name = event_name[event_name.find("__")+2:]
    proj.ftrace_callback(Event(event_name,field_dict))


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

