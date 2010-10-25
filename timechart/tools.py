from enthought.chaco.tools.api import PanTool, ZoomTool

class myZoomTool(ZoomTool):
    """ a zoom tool which change y range only when control is pressed
    it also hande some page up page down to zoom via keyboard 
    """
    def normal_mouse_wheel(self, event):
        if event.control_down:
            self.tool_mode = "box"
        else:
            self.tool_mode = "range"
        super(myZoomTool, self).normal_mouse_wheel(event)
        # restore default zoom mode
        if event.control_down:
            self.tool_mode = "range"
    def normal_key_pressed(self, event):
        super(myZoomTool, self).normal_key_pressed(event)
        print event
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
