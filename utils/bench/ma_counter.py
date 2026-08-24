"""Counter of numpy.ma calls - a deterministic progress metric.

Why this exists: wall-clock time is noisy depending on machine load, so for
small incremental changes it does not tell you whether the refactor is making
progress. The number of `numpy.ma` calls, by contrast, is deterministic - for
the same data it always comes out the same. The goal is to drive it to zero.

Installed by monkeypatching the `numpy.ma` module; the model is not modified.

USAGE
-----
    import ma_counter; ma_counter.install()
    ...run the model...
    ma_counter.report(steps=<number of time steps>)

or from the command line (it counts the steps itself):

    python ma_counter.py --config bench/cfg/4Gti.ini
    python ma_counter.py --config bench/cfg/4Gti.ini --vec     # with vec_inflow

Output: a table of calls per function plus the total and the per-time-step
figure, and a JSON line for machine processing.
"""

import argparse
import collections
import json
import os
import sys

# the functions the model actually uses (found by grepping smoderp2d/)
FUNCS = [
    'where', 'masked_array', 'power', 'maximum', 'filled', 'any', 'array',
    'logical_and', 'copy', 'all', 'unique', 'minimum', 'logical_or',
    'logical_not', 'pow', 'equal', 'argmax', 'zeros', 'sum', 'sqrt',
    'is_masked', 'greater', 'amax',
]

COUNT = collections.Counter()
_installed = [False]
_orig = {}


def install():
    """Wrap the numpy.ma callables in a counter. Call before importing the core."""
    if _installed[0]:
        return
    import numpy.ma as ma

    for name in FUNCS:
        fn = getattr(ma, name, None)
        if fn is None or not callable(fn):
            continue
        _orig[name] = fn

        def make(nm, f):
            def wrapper(*a, **k):
                COUNT[nm] += 1
                return f(*a, **k)
            return wrapper
        setattr(ma, name, make(name, fn))

    # scalar writes into a MaskedArray - these dominated the profile before
    # vectorisation
    MA = ma.MaskedArray
    _orig['__setitem__'] = MA.__setitem__
    _orig['__getitem__'] = MA.__getitem__

    def setitem(self, *a, **k):
        COUNT['MaskedArray.__setitem__'] += 1
        return _orig['__setitem__'](self, *a, **k)

    def getitem(self, *a, **k):
        COUNT['MaskedArray.__getitem__'] += 1
        return _orig['__getitem__'](self, *a, **k)

    MA.__setitem__ = setitem
    MA.__getitem__ = getitem
    _installed[0] = True


def reset():
    COUNT.clear()


def report(steps=None, label='', as_json=True):
    """Print the table and return a dict."""
    total = sum(COUNT.values())
    print()
    print('=' * 58)
    print('numpy.ma calls' + (f' - {label}' if label else ''))
    print('=' * 58)
    print(f"{'function':<30}{'calls':>12}{'per step':>14}")
    print('-' * 58)
    for name, n in COUNT.most_common():
        per = f'{n/steps:,.1f}' if steps else '—'
        print(f'{name:<30}{n:>12,}{per:>14}')
    print('-' * 58)
    per = f'{total/steps:,.1f}' if steps else '—'
    print(f"{'TOTAL':<30}{total:>12,}{per:>14}")
    if steps:
        print(f'\ntime steps: {steps}')
    out = {'label': label, 'steps': steps, 'total': total,
           'per_step': (total / steps) if steps else None,
           'by_func': dict(COUNT)}
    if as_json:
        print('JSON ' + json.dumps(out))
    return out


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--vec', action='store_true',
                    help='install vec_inflow as well')
    a = ap.parse_args()

    sys.path[:0] = [os.getcwd(), os.path.join(os.getcwd(), 'bin')]
    os.environ['SMODERP2D_CONFIG_FILE'] = a.config

    install()                       # BEFORE importing the core
    from smoderp2d.runners.base import Runner
    r = Runner()
    r._provider.load()
    if a.vec:
        import vec_inflow
        vec_inflow.install(verify=False)

    # count the time steps without further instrumentation
    import smoderp2d.time_step as TS
    steps = [0]
    _orig_next = TS.TimeStep.do_next_h

    def do_next_h(self, *aa, **kk):
        steps[0] += 1
        return _orig_next(self, *aa, **kk)
    TS.TimeStep.do_next_h = do_next_h

    reset()
    from smoderp2d.runoff import Runoff
    Runoff(r._provider).run()
    label = os.path.basename(a.config) + (' +vec' if a.vec else '')
    report(steps=steps[0], label=label)


if __name__ == '__main__':
    _main()
