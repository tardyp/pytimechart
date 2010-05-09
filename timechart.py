#!/usr/bin/python
#------------------------------------------------------------------------------
import os,sys

# workaround bug in kiva's font manager that fails to find a correct default font on linux
if os.name=="posix":
    from  enthought.kiva.fonttools.font_manager import fontManager, FontProperties
    font = FontProperties()
    font.set_name("DejaVu Sans")
    fontManager.defaultFont = fontManager.findfont(font)


# Enthought library imports.
from enthought.pyface.api import ApplicationWindow, GUI
from enthought.pyface.action.api import Action, MenuManager, MenuBarManager
from enthought.pyface.action.api import StatusBarManager, ToolBarManager
from enthought.pyface.action.api import Group as ActionGroup

from enthought.pyface.api import SplitApplicationWindow, SplitPanel
from enthought.traits.ui.api import Item, Group, View,spring,HGroup,TableEditor
from enthought.traits.api import HasTraits,Button,Str
from enthought.traits.ui.menu import OKButton

from enthought.enable.api import Component, ComponentEditor, Window

from enthought.pyface.api import ImageResource
from enthought.pyface.dock.api \
    import *
from timechart.timechart import TimechartProject
from timechart.timechart_plot import create_timechart_container

class myDockSizer(DockSizer):
    def _contents_items_changed ( self, event ):
        """ Handles the 'contents' trait being changed.
        """
        self._is_notebook = None
        for item, in event.added:
            item.parent = self
        self.calc_min( True )
        self.modified = True


class HelpWindow(HasTraits):
    ok_button = Button('Ok')
    version_text = Str("PyTimeChart v0.03 (Alpha)")
    dev_text = Str('Python License')
    dev_text1 = Str('Based on')
    dev_text2 = Str('  Python')
    dev_text3 = Str('  Chaco')
    copyright_text = Str("Copyright (c) 2010 Pierre Tardy")
    view = View(
                HGroup(spring,Item('version_text',style='readonly',show_label = False, emphasized = True),spring),
                spring,
                Item('dev_text',style='readonly',show_label = False),
                Item('dev_text1',style='readonly',show_label = False),
                Item('dev_text2',style='readonly',show_label = False),
                Item('dev_text3',style='readonly',show_label = False),
                spring,
                Item('copyright_text',style='readonly',show_label = False),
                spring,
                #HGroup(spring,Item('ok_button',show_label = False),spring),
                title='About PyTimeChart',
                width = 350,
                height = 200,
                buttons = [OKButton]  
                )
    
    def _ok_button_fired(self):
        self.destroy()

class MainWindow(ApplicationWindow):
    """ The main application window. """
    proj = TimechartProject
    using_old = False
    ###########################################################################
    # 'object' interface.
    ###########################################################################
    def __init__(self, **traits):
        """ Creates a new application window. """

        # Base class constructor.
        super(MainWindow, self).__init__(**traits)

        # Create an action that exits the application.
        exit_action = Action(name='exit', on_perform=self.close)
        help_action = Action(name='About', on_perform = self.show_about)
        
        # Add a menu bar.
        self.menu_bar_manager = MenuBarManager(
            MenuManager(exit_action ,name='&File'),
            MenuManager(help_action,name='Help')
        )

        # Add a status bar.
        self.status_bar_manager = StatusBarManager()
        self.status_bar_manager.message = 'Welcome to timechart'
        
        return
    def open_file(self):
        self.status_bar_manager.message=open_file()
    def on_range_changed(self,r):
        time = r[1]-r[0]
        self.status_bar_manager.message = "total view: %d.%03d %03ds %d"%(time/1000000,(time/1000)%1000,time%1000,time)
    def _create_contents(self, parent):

        window  = DockWindow( parent ).control
        self.window=window
        self.plot =  create_timechart_container(self.proj)
        options_confview = self.plot.options.edit_traits(parent=window,kind='panel',scrollable=True)
        range_tools_confview = self.plot.range_tools.edit_traits(parent=window,kind='panel',scrollable=True)
        project_confview = self.plot.proj.edit_traits(parent=window,kind='panel',scrollable=True)

        plotwindow = Window(parent=window,kind='panel',component = self.plot)
        self.plot.index_range.on_trait_change(self.on_range_changed, "updated")
        self.plot_control = DockControl( name      = 'Plot',
                                         closeable = False,
                                         control   = plotwindow.control, 
                                         width=600,
                                         style     = 'horizontal' )
        sizer   = myDockSizer( contents = 
                      [ [
                DockControl( name      = 'Plot',
                             closeable = False,
                             control   = options_confview.control, 
                             style     = 'horizontal' ),
                DockControl( name      = 'Plot',
                             closeable = False,
                             control   = range_tools_confview.control, 
                             style     = 'horizontal' ),
                             ],
                self.plot_control,
                DockControl( name      = 'Plot',
                             closeable = False,
                             control   = project_confview.control, 
                             style     = 'horizontal' )
                        ])
        self.sizer = sizer
        window.SetSizer( sizer )
        window.SetAutoLayout( True )
    
        return window
    def show_about(self):
        help_window = HelpWindow()
        help_window.configure_traits()
        

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
    
# Application entry point.
prof=1
if __name__ == '__main__':
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
    window = MainWindow(proj = proj,size=(1024,768),title="PyTimechart:%s"%(fn))
    window.open()
    # Start the GUI event loop!
    if prof:
        import cProfile
        cProfile.run('gui.start_event_loop()','timechart.prof')
    else:
        gui.start_event_loop()

##### EOF #####################################################################

