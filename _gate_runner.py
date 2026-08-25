
import sys, os, time, json
def _rss_mb():
    """Peak RSS in MB. resource is POSIX-only, on Windows go through psapi."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.
    except ImportError:
        import ctypes
        from ctypes import wintypes
        class _PMC(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD),
                        ('PageFaultCount', wintypes.DWORD),
                        ('PeakWorkingSetSize', ctypes.c_size_t),
                        ('WorkingSetSize', ctypes.c_size_t),
                        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                        ('PagefileUsage', ctypes.c_size_t),
                        ('PeakPagefileUsage', ctypes.c_size_t)]
        c = _PMC(); c.cb = ctypes.sizeof(c)
        ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
        return c.PeakWorkingSetSize / 1048576.

sys.path[:0] = [os.getcwd(), os.path.join(os.getcwd(), 'bin')]
os.environ['SMODERP2D_CONFIG_FILE'] = sys.argv[1]
count = None
if os.environ.get('GATE_COUNT_DIR'):
    sys.path.insert(0, os.environ['GATE_COUNT_DIR'])
    import ma_counter; ma_counter.install(); count = ma_counter
from smoderp2d.runners.base import Runner
r = Runner(); r._provider.load()
# optional monkeypatch module (for changes not yet in the sources)
for _m in filter(None, os.environ.get('GATE_INSTALL', '').split(',')):
    __import__(_m).install()
import smoderp2d.time_step as TS
steps = [0]; _o = TS.TimeStep.do_next_h
def dn(self, *a, **k):
    steps[0] += 1
    return _o(self, *a, **k)
TS.TimeStep.do_next_h = dn
if count is not None:
    count.reset()          # count the running computation only, not data loading
from smoderp2d.runoff import Runoff
t = time.perf_counter(); ro = Runoff(r._provider); ro.run()
wall = time.perf_counter() - t
ro.save_output()
out = {'wall': wall, 'steps': steps[0],
       'rss_mb': _rss_mb()}
if count is not None:
    out['ma_total'] = sum(count.COUNT.values())
    out['ma_by_func'] = dict(count.COUNT)
print('GATEJSON ' + json.dumps(out))
