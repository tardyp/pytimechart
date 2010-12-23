#!/usr/bin/python
#------------------------------------------------------------------------------
import sys
from enthought.etsconfig.api import ETSConfig
# select the toolkit we want to use
# WX is more stable for now
#ETSConfig.toolkit = 'qt4'
ETSConfig.toolkit = 'wx'

from enthought.pyface.api import GUI
from timechart.window import open_file


prof=0
if __name__ == '__main__':
    # Create the GUI (this does NOT start the GUI event loop).
    gui = GUI()
    if len(sys.argv)>1:
        fn = sys.argv[1]
    else:
        fn = None
    if open_file(fn):
        if prof:
            import cProfile
            cProfile.run('gui.start_event_loop()','timechart.prof')
        else:
            gui.start_event_loop()

import timechart.py2exe_wximports

##### EOF #####################################################################

