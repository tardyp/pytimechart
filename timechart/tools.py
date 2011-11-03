from enthought.chaco.tools.api import PanTool, ZoomTool, RangeSelection, PanTool
try:
    from enthought.chaco.tools.tool_states import ZoomState, PanState, GroupedToolState, ToolState
except:
  pass
from copy import copy

class myZoomTool(ZoomTool):
    """ a zoom tool which change y range only when control is pressed
    it also hande some page up page down to zoom via keyboard 
    """
    def normal_mouse_wheel(self, event):
        if event.control_down:
            self.tool_mode = "box"
        else:
            self.tool_mode = "range"
            oldrange = copy(self.component.value_mapper.range)

        super(myZoomTool, self).normal_mouse_wheel(event)
        # restore default zoom mode
        if event.control_down:
            self.tool_mode = "range"
        else:
            self.component.value_mapper.range = oldrange

    def normal_key_pressed(self, event):
        super(myZoomTool, self).normal_key_pressed(event)
        class fake_event:
            pass
        my_fake_event = fake_event()
        c = self.component
        my_fake_event.x = event.x#(c.x+c.x2)/2
        my_fake_event.y = event.x#(c.y+c.y2)/2
        my_fake_event.control_down = event.control_down
        my_fake_event.mouse_wheel = 0
        if event.character == 'Page Up':
            my_fake_event.mouse_wheel = 1
        if event.character == 'Page Down':
            my_fake_event.mouse_wheel = -1
        if event.shift_down:
            my_fake_event.mouse_wheel*=10
        if event.alt_down:
            my_fake_event.mouse_wheel*=2
        if my_fake_event.mouse_wheel:
            self.normal_mouse_wheel(my_fake_event)
    def zoom_in(self, factor=0):
        if self.tool_mode != "range":
            return super(myZoomTool, self).zoom_in(factor)
        if factor == 0:
            factor = self.zoom_factor
        new_index_factor = self._index_factor * factor
        new_value_factor = self._value_factor

        location = self.position
        x_map = self._get_x_mapper()
        y_map = self._get_y_mapper()
        x = x_map.map_data(location[0])
        cx = x_map.map_data(self.component.bounds[0]/2)

        next = ( x + (cx - x)*(self._index_factor/new_index_factor),
		y_map.map_data(self.component.bounds[1]/2))
        prev = (cx,
                y_map.map_data(self.component.bounds[1]/2))

        pan_state = PanState(prev, next)
        zoom_state = ZoomState((self._index_factor, self._value_factor),
                                   (new_index_factor, new_value_factor))

        states = GroupedToolState([pan_state, zoom_state])
        states.apply(self)
        self._append_state(states)
    def zoom_out(self, factor=0):
        if self.tool_mode != "range":
            return super(myZoomTool, self).zoom_in(factor)
        if factor == 0:
            factor = self.zoom_factor

        new_index_factor = self._index_factor / factor

        new_value_factor = self._value_factor
        location = self.position
        x_map = self._get_x_mapper()
        y_map = self._get_y_mapper()
        x = x_map.map_data(location[0])
        cx = x_map.map_data(self.component.bounds[0]/2)

        next = ( x + (cx - x)*(self._index_factor/new_index_factor),
		y_map.map_data(self.component.bounds[1]/2))
        prev = (cx,
                y_map.map_data(self.component.bounds[1]/2))

        pan_state = PanState(prev, next)
        zoom_state = ZoomState((self._index_factor, self._value_factor),
                                   (new_index_factor, new_value_factor))

        states = GroupedToolState([pan_state, zoom_state])
        states.apply(self)
        self._append_state(states)


# left down conflicts with the panning tool
# just overide and disable change state to moving
# change the moving binding to middle click
class myRangeSelection(RangeSelection):
    def selected_left_down(self, event):
        RangeSelection.selected_left_down(self,event)
        if self.event_state == "moving":
            self.event_state = "selected"
    def selected_middle_down(self, event):
        RangeSelection.selected_left_down(self,event)
    def moving_middle_up(self, event):
        RangeSelection.moving_left_up(self,event)
    def selecting_middle_up(self, event):
        RangeSelection.selected_left_up(self,event)
# immediatly refresh the plot for better fluidity
class myPanTool(PanTool):
    def panning_mouse_move(self,event):
        PanTool.panning_mouse_move(self,event)
        self.component.immediate_invalidate()
