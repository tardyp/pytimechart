import sys,os
from enthought.traits.api import  HasTraits,Str
from enthought.traits.ui.api import InstanceEditor,Item,View,HSplit,VSplit,Handler, StatusItem
from enthought.traits.ui.menu import Action, MenuBar, ToolBar, Menu
from model import tcProject
from plot import tcPlot, create_timechart_container
from enthought.enable.component_editor import ComponentEditor
from enthought.pyface.image_resource \
    import ImageResource

# workaround bug in kiva's font manager that fails to find a correct default font on linux
if os.name=="posix":
    from  enthought.kiva.fonttools.font_manager import fontManager, FontProperties
    font = FontProperties()
    font.set_name("DejaVu Sans")
    fontManager.defaultFont = fontManager.findfont(font)


class tcActionHandler(Handler):
    handler_list = []
    def chooseAction(self, UIInfo,name):
        window = UIInfo.ui.context['object']
        handler_list = [window, window.project, window.plot, window.plot.options, window.plot.range_tools]
        for i in handler_list:
            fn = getattr(i, name, None)
            if fn is not None:
                fn()

def _buildAction(desc):
    exec("tcActionHandler.%s = lambda self,i:self.chooseAction(i,'_on_%s')"%(desc["name"],desc["name"]))
    return Action(name=desc["name"], action=desc["name"],
                  tooltip=desc["tooltip"],
                  image=ImageResource(desc["name"]))

def _create_toolbar_actions():
    actions = ( 
        {"name": "show","tooltip":'show selected processes in the timechart'},
        {"name": "hide","tooltip":'hide selected processes in the timechart'},
        {"name": "hide_others","tooltip":'Hide process that are not shown at current zoom window'},
        {"name": "hide_onscreen","tooltip":'Hide process that are shown at current zoom window'},
        {"name": "invert","tooltip":'invert processes show/hide value.\nThis is useful, when you are fully zoomed,\nand you want to see if you are not missing some valuable info\nin the hidden processes'},
        {"name": "select_all","tooltip":'select_all/unselect_all'},
        {"name": "zoom","tooltip":'zoom on the selection'},
        {"name": "trace_text","tooltip":'show the text trace of the selection'},
        {"name": "unzoom","tooltip":'unzoom to show the whole trace'},
        {"name": "view_properties","tooltip":'edit plot view options'},
        )
    ret = []
    for i in actions:
        ret.append(_buildAction(i))
    return tuple(ret)
def _create_menubar_actions():
    desc = (('&File', ( {"name": "open","tooltip":'open new file into pytimechart'},
                        {"name": "exit","tooltip":'exit pytimechart'})),
            ('&View', ( {"name": "view_properties","tooltip":'edit plot view options'},)),
            ('&Help', ( {"name": "about","tooltip":'about'},)))
    ret = []
    for menu in desc:
        actions = []
        for action in menu[1]:
            actions.append(_buildAction(action))
        ret.append(Menu(*tuple(actions), name = menu[0]))
    return tuple(ret)
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
    exit_action = Action(name='e&xit', action='exit')
    open_action = Action(name='&Open', action='open')
    edit_property_action = Action(name='view properties', action='edit_properties')
    about_action = Action(name='About',action='do_action_about')
    status = Str("Welcome to PyTimechart")
    traits_view = View(
        HSplit(
            VSplit(
                Item('project', show_label = False, editor=InstanceEditor(view = 'process_view'), style='custom',width=150),
                Item('plot_range_tools', show_label = False, editor=InstanceEditor(view = 'selection_view'), style='custom',width=150,height=100)),
            Item('plot', show_label = False, editor = ComponentEditor()),
                
            ),
        toolbar = ToolBar(*_create_toolbar_actions(),
                           image_size      = ( 24, 24 ),
                           show_tool_names = False),
        menubar = MenuBar(*_create_menubar_actions()),
        statusbar = [StatusItem(name='status'),],
        resizable = True,
        width = 1280,
        height = 1024,
        handler = tcActionHandler()
        )
    def _on_open(self):
        open_file(None)
    def _on_view_properties(self):
        self.plot.options.edit_traits()
    def _on_exit(self,n=None):
        self.close()
    def close(self,n=None):
        sys.exit(0)
    def _on_about(self):
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
    from backends.perf import detect_perf
    from backends.ftrace import detect_ftrace
    from backends.tracecmd import detect_tracecmd
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
