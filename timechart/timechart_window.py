import sys
from enthought.traits.api import  HasTraits,Str
from enthought.traits.ui.api import InstanceEditor,Item,View,HSplit,VSplit,Handler, StatusItem
from enthought.traits.ui.menu import Action, MenuBar, ToolBar, Menu
from timechart import TimechartProject
from timechart_plot import TimechartPlot, create_timechart_container
from enthought.enable.component_editor import ComponentEditor

class TimechartWindow(HasTraits):
    project = TimechartProject
    plot = TimechartPlot
    def __init__(self,project):
        self.project = project
        self.plot =  create_timechart_container(project)
        self.plot_options = self.plot.options
        self.plot_range_tools = self.plot.range_tools

    # Create an action that exits the application.
    exit_action = Action(name='exit', action='do_action_exit')
    about_action = Action(name='About',action='do_action_about')
    status = Str("Welcome to PyTimechart")
    class myHandler(Handler):
        def do_action_exit(self, UIInfo):
            view = UIInfo.ui.context['object']
            view.close()
        def do_action_about(self, UIInfo):
            view = UIInfo.ui.context['object']
            view.about()
    
    traits_view = View(
        HSplit( 
            VSplit(
                Item('plot_options', show_label = False, editor=InstanceEditor(view = 'option_view'), style='custom',width=150),
                Item('plot_range_tools', show_label = False, editor=InstanceEditor(view = 'selection_view'), style='custom',width=150)
                ),
            Item('plot', show_label = False, editor = ComponentEditor()),
            Item('project', show_label = False, editor=InstanceEditor(view = 'process_view'), style='custom',width=150)),
        toolbar = ToolBar(),
        menubar = MenuBar(Menu(exit_action, name = '&File'),
                          Menu(about_action, name = '&Help')),
        statusbar = [StatusItem(name='status'),],
        title = "PyTimechart",
        resizable = True,
        width = 1280,
        height = 1024,
        handler = myHandler()               
        )
    def close(self):
        sys.exit(0)
