from timechart.plugin import *
from timechart import colors
from timechart.model import tcProcess

c_state_table = ["C0","C1","C2","C4","C6","S0i1","S0i3"]

class cpu_idle(plugin):
    additional_colors = """
C0			#000000
C1			#bbbbff
C2			#7777ff
C3			#5555ff
C4			#3333ff
C5			#1111ff
C6			#0000ff
S0i3			#0011ff
S0i1			#0022ff
"""
    additional_ftrace_parsers = [
        ('cpu_idle',  'state=%d cpu_id=%d', 'state', 'cpuid'),
        ]

    additional_process_types = {
        }

    # stable event support
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
        else :
            if len(tc['start_ts'])>len(tc['end_ts']):
                tc['end_ts'].append(event.timestamp)
    # legacy event support
    @staticmethod
    def do_event_power_start(self,event):
        self.ensure_cpu_allocated(event.common_cpu)
        if event.type==1:# c_state
            tc = self.tmp_c_states[event.common_cpu]
            if len(tc['start_ts'])>len(tc['end_ts']):
                tc['end_ts'].append(event.timestamp)
                self.missed_power_end +=1
                if self.missed_power_end < 10:
                    print "warning: missed power_end"
                if self.missed_power_end == 10:
                    print "warning: missed power_end: wont warn anymore!"
            tc['start_ts'].append(event.timestamp)
            tc['types'].append(colors.get_color_id(c_state_table[int(event.state)]))

    @staticmethod
    def do_event_power_end(self,event):
        self.ensure_cpu_allocated(event.common_cpu)

        tc = self.tmp_c_states[event.common_cpu]
        if len(tc['start_ts'])>len(tc['end_ts']):
            tc['end_ts'].append(event.timestamp)

    @staticmethod
    def do_event_power_frequency(self,event):
        self.ensure_cpu_allocated(event.common_cpu)
        if event.type==2:# p_state
            tc = self.tmp_p_states[event.common_cpu]
            tc['start_ts'].append(event.timestamp)
            tc['types'].append(event.state)

plugin_register(cpu_idle)

