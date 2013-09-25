from .base import BackendTestCase
import sys
class TestFtrace(BackendTestCase):
    def test_retrace(self):
        proj = self.load_file("retrace.txt", "ftrace")
        self.assertHasProcess("cpu1/freq:400000 (211.0 ms)")
        self.assertHasProcess("event:u8500_set_ape_opp:0 (0.0 us)")
    def test_rpm(self):
        self.load_file("rpm-trace.txt.gz", "ftrace")
        self.assertHasProcess("rpm_cb:usb1:0 (76.0 us)")
