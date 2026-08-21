"""Počítadlo volání numpy.ma — deterministická metrika postupu kroku 2.

Proč to existuje: wall-clock čas šumí podle zatížení stroje, takže se z něj
u malých dílčích změn nepozná, jestli refaktor postupuje. Počet volání
`numpy.ma` je naopak deterministický — pro stejná data vyjde vždy stejně.
Cíl kroku 2 je dostat ho na nulu.

Instaluje se monkeypatchem na modul `numpy.ma`, model se nemění.

POUŽITÍ
-------
    import ma_counter; ma_counter.install()
    ...spustit model...
    ma_counter.report(steps=<pocet casovych kroku>)

nebo z příkazové řádky (spočítá si kroky sám):

    python ma_counter.py --config bench/cfg/4Gti.ini
    python ma_counter.py --config bench/cfg/4Gti.ini --vec     # s vec_inflow

Výstup: tabulka volání podle funkce + součet a přepočet na jeden časový krok,
plus JSON řádek pro strojové zpracování.
"""

import argparse
import collections
import json
import os
import sys

# funkce, které model reálně používá (zjištěno grepem přes smoderp2d/)
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
    """Obalí numpy.ma callables počítadlem. Volat před importem jádra."""
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

    # skalární zápis do MaskedArray — dominoval profilu před vektorizací
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
    """Vypíše tabulku a vrátí dict."""
    total = sum(COUNT.values())
    print()
    print('=' * 58)
    print('Volání numpy.ma' + (f' — {label}' if label else ''))
    print('=' * 58)
    print(f"{'funkce':<30}{'volání':>12}{'na krok':>14}")
    print('-' * 58)
    for name, n in COUNT.most_common():
        per = f'{n/steps:,.1f}' if steps else '—'
        print(f'{name:<30}{n:>12,}{per:>14}')
    print('-' * 58)
    per = f'{total/steps:,.1f}' if steps else '—'
    print(f"{'CELKEM':<30}{total:>12,}{per:>14}")
    if steps:
        print(f'\ncasovych kroku: {steps}')
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
                    help='nainstalovat i vec_inflow')
    a = ap.parse_args()

    sys.path[:0] = [os.getcwd(), os.path.join(os.getcwd(), 'bin')]
    os.environ['SMODERP2D_CONFIG_FILE'] = a.config

    install()                       # PŘED importem jádra
    from smoderp2d.runners.base import Runner
    r = Runner()
    r._provider.load()
    if a.vec:
        import vec_inflow
        vec_inflow.install(verify=False)

    # spočítat časové kroky bez další instrumentace
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
