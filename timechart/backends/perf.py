
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

def load_perf(filename):
    # @todo revisit with subprocess
    os.setcwd(os.path.dirname(filename))
    os.system("perf trace -s %s &"%(__file__))
    return None
def detect_perf(filename):
    if os.path.basename(filename) == "perf.dat":
        return load_perf
    return None
