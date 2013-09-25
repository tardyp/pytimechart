import os
import unittest
from timechart.backends.perf import detect_perf
from timechart.backends.ftrace import detect_ftrace
from timechart.backends.trace_cmd import detect_tracecmd
from timechart.progress import disable_progress_bar

backends = dict(perf=detect_perf, ftrace=detect_ftrace,
                tracecmd=detect_tracecmd)


class BackendTestCase(unittest.TestCase):
    def setUp(self):
        disable_progress_bar()
    def load_file(self, fn, expected_backend):
        fn = os.path.join(os.path.dirname(__file__), "test_db", fn)
        ret = None
        for backend, detect in backends.iteritems():
            parser = detect(fn)
            if parser:
                self.assertEqual(expected_backend, backend)
                self.proj = ret = parser(fn)
        self.assertIsNotNone(ret)
        return ret

    def assertHasProcess(self, name):
        names = []
        for p in self.proj.processes:
            if p.name.startswith(name):
                return
            names.append(p.name)
        self.assertTrue(False, "trace should generate process %s, but only has %s" %
                        (name, " ".join(names)))
    def assertIsNotNone(self, val):  #py2.7
        return self.assertTrue(val is not None)