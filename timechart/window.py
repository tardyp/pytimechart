import sys,os
from enthought.traits.api import  HasTraits,Str
from enthought.traits.ui.api import InstanceEditor,Item,View,HSplit,VSplit,Handler, StatusItem
from enthought.traits.ui.menu import Action, MenuBar, ToolBar, Menu
from timechart.model import tcProject
from timechart.plot import tcPlot, create_timechart_container
from enthought.enable.component_editor import ComponentEditor

# workaround bug in kiva's font manager that fails to find a correct default font on linux
if os.name=="posix":
    from  enthought.kiva.fonttools.font_manager import fontManager, FontProperties
    font = FontProperties()
    font.set_name("DejaVu Sans")
    fontManager.defaultFont = fontManager.findfont(font)


class tcWindow(HasTraits):
    project = tcProject
    plot = tcPlot
    def __init__(self,project):
        self.project = project
        self.plot =  create_timechart_container(project)
        self.plot_range_tools = self.plot.range_tools
        self.trait_view().title = "PyTimechart: "+project.filename
    def get_title(self):
        return "PyTimechart:"+self.project.filename
    # Create an action that exits the application.
    exit_action = Action(name='e&xit', action='do_action_exit')
    open_action = Action(name='&Open', action='do_action_open')
    edit_property_action = Action(name='view properties', action='do_action_edit_properties')
    about_action = Action(name='About',action='do_action_about')
    status = Str("Welcome to PyTimechart")
    class myHandler(Handler):
        def do_actionj_exit(self, UIInfo):
            view = UIInfo.ui.context['object']
            view.close()
        def do_action_open(self, UIInfo):
            open_file(None)
        def do_action_about(self, UIInfo):
            view = UIInfo.ui.context['object']
            view.about()
        def do_action_edit_properties(self, UIInfo):
            view = UIInfo.ui.context['object']
            view.plot.options.edit_traits()
    traits_view = View(
        HSplit(
            VSplit(
                Item('project', show_label = False, editor=InstanceEditor(view = 'process_view'), style='custom',width=150),
                Item('plot_range_tools', show_label = False, editor=InstanceEditor(view = 'selection_view'), style='custom',width=150,height=100)),
            Item('plot', show_label = False, editor = ComponentEditor()),
                
            ),
        toolbar = ToolBar(),
        menubar = MenuBar(Menu(open_action,exit_action, name = '&File'),
                          Menu(edit_property_action, name = '&View'),
                          Menu(about_action, name = '&Help')),
        statusbar = [StatusItem(name='status'),],
        resizable = True,
        width = 1280,
        height = 1024,
        handler = myHandler()               
        )
    def close(self,n=None):
        sys.exit(0)
    def about(self):
        pass


prof = 0

import wx
def open_dialog():
    dlg = wx.FileDialog(None, "Choose a file", "", "", "*.txt", wx.OPEN)
    rv = None
    if dlg.ShowModal() == wx.ID_OK:
        filename=dlg.GetFilename()
        dirname=dlg.GetDirectory()
        rv = os.path.join(dirname, filename)

    dlg.Destroy()
    return rv
    
def open_file(fn=None):
    from timechart.backends.perf import detect_perf
    from timechart.backends.ftrace import detect_ftrace
    from timechart.backends.tracecmd import detect_tracecmd
    if fn == None:
        fn = open_dialog()
        if fn == None:
            return 0
    parser = None
    for func in detect_ftrace, detect_perf, detect_tracecmd:
        parser = func(fn)
        if parser:
            break
    if prof:
        import cProfile
        cProfile.run('proj = parser(fn)','timechart_load.prof')
    else:
        proj = parser(fn)
    if proj:
        # Create and open the main window.
        window = tcWindow(project = proj)
        window.edit_traits()
        # Traits has the bad habbit of autoselecting the first row in the table_editor. Workaround this.
        proj.selected = []
        return 1
    return 0
