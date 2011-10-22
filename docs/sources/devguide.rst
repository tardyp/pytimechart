pyTimechart Developer Guide
===========================
This section is here to explain how to extend pyTimechart to parse your own traces

Installation for developement
-----------------------------

pytimechart installer is based on distutils. It is best to use it for developement installation::

  git clone git://gitorious.org/pytimechart/pytimechart.git
  cd pytimechart
  sudo python setup.py develop


This will install a pytimechart binary that points to your git environment

Code organisation
-----------------

Here are the main section of code:

* timechart/

   main directory for the source code of the python "timechart" module

* backends/

   The parsers backend.  ftrace, perf and tracecmd are supported

* plugins/

   The event parsers. Those files handle the translation from events to pytimechart process events

* window.py

  This handle the main window UI

* action.py

  This handle the list of actions that converts into toolbuttons or menubutton. Several classes can implement the actual action for each action, including window, plot or project instances.

* model.py

  This contains main classes, and algorithms. The data is first generated as python arrays for convenience, and then are converted to numpy arrays for speed.
  numpy array's length are not muteable. This is why python array are used during parsing.

* plot.py

  This is the chaco frontend, that converts the model into a plot.

Writing a plugin
----------------

the template.py file
^^^^^^^^^^^^^^^^^^^^

You can start writting your plugin by copying the template.py file. Here you can find an example on how to write a plugin. Following are more detailled information to understand the template.py file, and be able to modify it.

You can also look at the other plugins for more examples.

the plugin class
^^^^^^^^^^^^^^^^

plugins are searched in the timechart.plugin python module. Futur version of pytimechart will allow to search for a more extended path, in order to develop plugins in another source tree.

Each plugin file consist of a class that extends the "plugin" class, and that defines conventional attributes

* additional_colors: This is a string that defines colors for the plot each colors are in the for "#rrggbb"

  You can look at runtime_pm.py to see extended usage of this feature.

* additional_ftrace_parsers: a list of tuples describing an event for the ftrace parser

  syntax is::

  ('event_name', 'attributes_fscanf_style_string', 'attribute1', 'attribute2'...)

  The fscanf style string is translated into a regular expression for parsing. This allows you to copy paste the trace_printk format, or the ftrace event description header.

  Only '%s' and '%d' are supported. Each '%d' or '%s' will generate a value that will be stored in the corresponding attribute

* additional_process_types: The types definition of process, that you give to the generic_find_process method

  This is used to sort the process by types, and to specify a background color.

  For each "process_type" you define, a "process_type_bg" color needs to be defined in additional_colors

* do_event_<event_name>: a @static method that is called each time the event <event_name> is seen in the trace::

      @static
      def do_event_<event_name>(proj,event):
      """ @param proj: the project instance. You can called its methods do generate process events, or wake events
          @param event: the event instance. Represents the event, has various attribute you can access
      """

* do_function_<function_name>: a @static method that is called each time the function <function_name> is seen in the trace

    Same prototype as do_event_<event_name>.

the project class
^^^^^^^^^^^^^^^^^

a project class instance is passed to your event callbacks. You can use following methods:

* proj.generic_find_process(process_pid, process_name, process_type)

   Used to find or create a process. process are identified by their (pid,name)

   - process_pid: the pid of the process

   - process_name: the name of the process

   - process_type: the type, that is used to order the plot, and find a background color

* proj.generic_process_start(process, event)

   Used to start a process event. The timestamp is taken in the event object

* proj.generic_process_stop(process, event)

   Used to stop a process event. The timestamp is taken in the event object

* proj.generic_add_wake(caller, callee, event)

   Used to generate a wake event. This translate into arrows that go from one process to another, at a particular time. Usefull to show process interactions

Those function are very simple and generic, you will see in some plugins that they are directly changing the project's attributes. You can do it as well, but it is undocumented :-}

the event class
^^^^^^^^^^^^^^^
a event class instance is passed to your event callbacks. You can use following attributes:

* linenumber: The linenumber in the trace
* common_comm: The comm of the linux process where the trace happened
* common_pid: The pid of the linux process where the trace happened
* common_cpu: The cpu number where the trace happened
* timestamp: timestamp of the trace

Other attributes are generated from the ftrace parsers, or by perf and tracecmd backends. They generally have the same name as the one defined in the original linux trace_event

