from enthought.pyface.api import ProgressDialog as pyfaceProgressDialog

show_progress = True
def disable_progress_bar():
    global show_progress
    show_progress = False

def ProgressDialog(*arg, **kw):
    if show_progress:
        return pyfaceProgressDialog(*arg, **kw)
    else:
        import mock
        ret = mock.Mock()
        ret.update.return_value = (1,0)
        return ret