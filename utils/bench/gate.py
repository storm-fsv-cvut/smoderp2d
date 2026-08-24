"""Acceptance gate for a single change. One command, two separate verdicts.

It follows the project rule that for an equivalent refactor the criterion is
agreement at float roundoff level, not a tolerance. Correctness is binary,
performance is reported separately. This script does exactly that - and
refuses to merge the two.

WHAT IT DOES
------------
It takes two working trees (typically two git worktrees: the accepted state
and the candidate), runs the same config over the same data in both, and
reports:

  CORRECTNESS  byte comparison of all output files      -> PASS / FAIL
  PERFORMANCE  median of N runs on both sides           -> ratio
  PROGRESS     numpy.ma calls per time step             -> deterministic

A row is appended to ledger.csv, so the trend is visible in the history.

WHY BYTE COMPARISON AND NOT AGAINST THE REFERENCE DATA
------------------------------------------------------
The repository does not currently reproduce its own `tests/data/reference`
even with unchanged code - a different numpy version is enough to shift the
dt selection. Bit equality can therefore only be verified as an A/B on the
SAME machine in the SAME environment, which is what this script provides.
The output files are also formatted to %.4e, so comparing against a stored
file from a different machine carries no information.

SETUP
-----
    git worktree add ../smoderp-ref <hash-of-accepted-state>
    git worktree add ../smoderp-new <hash-of-candidate>

USAGE
-----
    python gate.py --ref ../smoderp-ref --new ../smoderp-new \\
                   --config bench/cfg/4Gti.ini --label "2b-cumulative" --reps 3

The config path is relative to the working tree and must exist in both (or
pass an absolute path to an .ini whose data paths are absolute too).
"""

import argparse
import csv
import datetime
import filecmp
import json
import os
import shutil
import statistics
import subprocess
import sys

RUNNER = r'''
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
'''


def run_once(tree, config, count_dir=None, install=''):
    """A single run in the given working tree. Returns a dict."""
    script = os.path.join(tree, '_gate_runner.py')
    with open(script, 'w') as fd:
        fd.write(RUNNER)
    cmd = [sys.executable, '_gate_runner.py', config]
    env = dict(os.environ, PYTHONPATH=os.path.abspath(tree),
               GATE_INSTALL=install or '')
    if count_dir:
        env['GATE_COUNT_DIR'] = os.path.abspath(count_dir)
    else:
        env.pop('GATE_COUNT_DIR', None)
    p = subprocess.run(cmd, cwd=tree, capture_output=True, text=True, env=env)
    os.remove(script)
    for line in p.stdout.splitlines():
        if line.startswith('GATEJSON '):
            return json.loads(line[9:])
    raise RuntimeError('run failed in %s:\n%s' % (tree, p.stderr[-3000:]))


def outdir_of(tree, config):
    import configparser
    cp = configparser.ConfigParser()
    cp.read(config if os.path.isabs(config) else os.path.join(tree, config))
    return os.path.join(tree, cp.get('output', 'outdir'))


def compare(d1, d2):
    same, diff, only1, only2 = [], [], [], []
    f1, f2 = set(), set()
    for base, acc in ((d1, f1), (d2, f2)):
        for root, _, files in os.walk(base):
            for fn in files:
                if fn == 'smoderp2d.log':
                    continue
                acc.add(os.path.relpath(os.path.join(root, fn), base))
    for rel in sorted(f1 | f2):
        if rel not in f2:
            only1.append(rel)
        elif rel not in f1:
            only2.append(rel)
        elif filecmp.cmp(os.path.join(d1, rel), os.path.join(d2, rel),
                         shallow=False):
            same.append(rel)
        else:
            diff.append(rel)
    return same, diff, only1, only2


def _ledger(a, ok, diff, o1, o2, res, ratio, cnt):
    """Append a row to the ledger. res/ratio/cnt may be None."""
    row = {
        'datum': datetime.date.today().isoformat(), 'label': a.label,
        'config': os.path.basename(a.config),
        'korektnost': 'PASS' if ok else 'FAIL',
        'odlisnych_souboru': len(diff) + len(o1) + len(o2),
        'ref_s': round(res['ref']['wall'], 2) if res else '',
        'new_s': round(res['new']['wall'], 2) if res else '',
        'zrychleni': round(ratio, 3) if ratio else '',
        'kroku': res['new']['steps'] if res else '',
        'rss_mb': round(res['new']['rss'], 0) if res else '',
        'ma_na_krok_ref': round(cnt['ref'], 1) if cnt else '',
        'ma_na_krok_new': round(cnt['new'], 1) if cnt else '',
    }
    new_file = not os.path.exists(a.ledger)
    with open(a.ledger, 'a', newline='') as fd:
        w = csv.DictWriter(fd, fieldnames=list(row))
        if new_file:
            w.writeheader()
        w.writerow(row)
    print('\nwritten to %s' % os.path.abspath(a.ledger))
    print('=' * 62)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True,
                    help='working tree of the accepted state')
    ap.add_argument('--new', required=True,
                    help='working tree of the candidate')
    ap.add_argument('--config', required=True)
    ap.add_argument('--label', required=True,
                    help='step label, goes into the ledger')
    ap.add_argument('--reps', type=int, default=3)
    ap.add_argument('--ledger', default='ledger.csv')
    ap.add_argument('--only', choices=['all', 'correctness'], default='all',
                    help='correctness = byte comparison only, 2 runs instead of 10')
    ap.add_argument('--install-new', default='',
                    help='modules to install() on the --new side only, comma separated')
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))

    print('=' * 62)
    print('ACCEPTANCE GATE  |  %s' % a.label)
    print('=' * 62)

    # --- correctness: one run on each side, then a byte comparison ---
    print('\n[1/3] CORRECTNESS  (byte comparison of the outputs)')
    for tree in (a.ref, a.new):
        shutil.rmtree(outdir_of(tree, a.config), ignore_errors=True)
    run_once(a.ref, a.config)
    run_once(a.new, a.config, install=a.install_new)
    same, diff, o1, o2 = compare(outdir_of(a.ref, a.config),
                                 outdir_of(a.new, a.config))
    ok = not diff and not o1 and not o2
    print('      identical %d | differing %d | only in ref %d | only in new %d'
          % (len(same), len(diff), len(o1), len(o2)))
    for f in (diff + o1 + o2)[:10]:
        print('        ! ' + f)
    print('      -> %s' % ('PASS' if ok else 'FAIL'))
    if not ok:
        print('\n      The change is NOT an equivalent refactor. Either it has a')
        print('      bug, or it belongs to the other category (a change of the')
        print('      numerical method) and has to be validated against')
        print('      measurements, not against a reference run.')

    if a.only == 'correctness':
        print('\n[2/3] PERFORMANCE  skipped (--only correctness)')
        print('[3/3] PROGRESS     skipped (--only correctness)')
        _ledger(a, ok, diff, o1, o2, None, None, None)
        sys.exit(0 if ok else 1)

    # --- performance: reported separately, regardless of the verdict above ---
    print('\n[2/3] PERFORMANCE  (median of %d runs)' % a.reps)
    res = {}
    for tag, tree in (('ref', a.ref), ('new', a.new)):
        w, s, m = [], None, None
        for _ in range(a.reps):
            r = run_once(tree, a.config,
                         install=a.install_new if tag == 'new' else '')
            w.append(r['wall']); s = r['steps']; m = r['rss_mb']
        res[tag] = {'wall': statistics.median(w), 'min': min(w),
                    'steps': s, 'rss': m}
        print('      %-4s %8.2f s (min %.2f)  steps %d  RSS %.0f MB'
              % (tag, res[tag]['wall'], res[tag]['min'], s, m))
    ratio = res['ref']['wall'] / res['new']['wall']
    print('      -> %.2fx' % ratio)
    if res['ref']['steps'] != res['new']['steps']:
        print('      WARNING: different number of time steps (%d vs %d) => the '
              'numerics changed' % (res['ref']['steps'], res['new']['steps']))

    # --- progress: a deterministic metric ---
    print('\n[3/3] PROGRESS  (numpy.ma calls per time step)')
    cnt = {}
    for tag, tree in (('ref', a.ref), ('new', a.new)):
        r = run_once(tree, a.config, count_dir=here,
                     install=a.install_new if tag == 'new' else '')
        cnt[tag] = r['ma_total'] / max(r['steps'], 1)
        print('      %-4s %10.1f' % (tag, cnt[tag]))
    d = cnt['new'] - cnt['ref']
    print('      -> %+.1f  (%+.1f %%)'
          % (d, 100 * d / cnt['ref'] if cnt['ref'] else 0))

    _ledger(a, ok, diff, o1, o2, res, ratio, cnt)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
