#!/usr/bin/python
#------------------------------------------------------------------------------
import sys
from enthought.etsconfig.api import ETSConfig
# select the toolkit we want to use
# WX is more stable for now
#ETSConfig.toolkit = 'qt4'
ETSConfig.toolkit = 'wx'

# workaround bad bg color in ubuntu, with Ambiance theme
# wxgtk (or traitsGUI, I dont know) looks like using the menu's bgcolor 
# for all custom widgets bg colors. :-(

if ETSConfig.toolkit == 'wx':
    import wx, os
    if "gtk2" in wx.PlatformInfo:
        from gtk import rc_parse, MenuBar
        m = MenuBar()
        if m.rc_get_style().bg[0].red_float < 0.5: # only customize dark bg
            rc_parse(os.path.join(os.path.dirname(__file__),"images/gtkrc"))
        m.destroy()

# workaround bug in kiva's font manager that fails to find a correct default font on linux
if os.name=="posix":
    import warnings
    def devnull(*args):
        pass
    warnings.showwarning = devnull
    from  enthought.kiva.fonttools.font_manager import fontManager, FontProperties
    font = FontProperties()
    font.set_name("DejaVu Sans")
    fontManager.defaultFont = fontManager.findfont(font)
    fontManager.warnings = None

from enthought.pyface.api import GUI
from window import open_file



def main(prof = len(sys.argv)>2):
    # Create the GUI (this does NOT start the GUI event loop).
    gui = GUI()
    if len(sys.argv)>1:
        fn = sys.argv[1]
    else:
        fn = None
    if open_file(fn):
        if prof:
            import cProfile
            dict = {"gui":gui}
            cProfile.runctx('gui.start_event_loop()',dict,dict,'timechart.prof')
        else:
            gui.start_event_loop()

# used for profiling, and regression tests
def just_open(prof = len(sys.argv)>2):
    if len(sys.argv)>1:
        fn = sys.argv[1]
    else:
        fn = None
    if prof:
        import cProfile
        dict = {"open_file":open_file,"fn":fn}
        cProfile.runctx('open_file(fn)',dict,dict,'timechart.prof')
    else:
        open_file(fn)

if __name__ == '__main__':
    main()
import py2exe_wximports

##### EOF #####################################################################
