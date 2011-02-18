from timechart.plugin import *
from timechart import colors
from timechart.model import tcProcess, c_state_table

class cpu_idle(plugin):
    additional_colors = """
"""
    additional_ftrace_parsers = [
        ('cpu_idle',  'state=%d cpu_id=%d', 'state', 'cpuid'),
        ]

    additional_process_types = {
        }

    @staticmethod
    def do_event_cpu_idle(self,event):
        self.ensure_cpu_allocated(event.cpuid)
        tc = self.tmp_c_states[event.cpuid]
        if event.state != 4294967295 :
            if len(tc['start_ts'])>len(tc['end_ts']):
                tc['end_ts'].append(event.timestamp)
                self.missed_power_end +=1
                if self.missed_power_end < 10:
                    print "warning: missed cpu_idle end"
                if self.missed_power_end == 10:
                    print "warning: missed cpu_idle end: wont warn anymore!"
            tc['start_ts'].append(event.timestamp)
            tc['types'].append(colors.get_color_id(c_state_table[int(event.state)]))
            tc['linenumbers'].append(event.linenumber)
        else :
            if len(tc['start_ts'])>len(tc['end_ts']):
                tc['end_ts'].append(event.timestamp)

plugin_register(cpu_idle)

