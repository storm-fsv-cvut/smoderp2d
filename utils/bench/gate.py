"""Akceptační brána pro jednu změnu. Jeden příkaz, dva oddělené verdikty.

Vychází z pravidla 2 projektu: u ekvivalentního refaktoru je kritérium shoda
na úrovni float roundoff, ne tolerance. Korektnost je binární, výkon se
reportuje zvlášť. Tenhle skript to dělá přesně tak — a odmítá je slučovat.

CO DĚLÁ
-------
Vezme dva pracovní stromy (typicky dva git worktrees: přijatý stav a kandidát),
pustí v obou tentýž config nad týmiž daty a vydá:

  KOREKTNOST  bajtové porovnání všech výstupních souborů  -> PASS / FAIL
  VÝKON       medián z N běhů na obou stranách            -> násobek
  POSTUP      počet volání numpy.ma na časový krok        -> deterministicky

Řádek se připíše do ledger.csv, takže je z historie vidět trend.

PROČ BAJTOVĚ A NE PROTI REFERENCI
---------------------------------
Repozitář dnes nereprodukuje vlastní `tests/data/reference` ani beze změny kódu
— stačí jiná verze numpy a rozjede se volba dt. Bit-shodu jde proto ověřit
jen jako A/B na TÉMŽE stroji v TÉMŽE prostředí, což tenhle skript zajišťuje.
Výstupní soubory jsou navíc formátované na %.4e, takže porovnání proti uloženému
souboru z jiného stroje nemá vypovídací hodnotu.

PŘÍPRAVA
--------
    git worktree add ../smoderp-ref <hash-prijateho-stavu>
    git worktree add ../smoderp-new <hash-kandidata>

POUŽITÍ
-------
    python gate.py --ref ../smoderp-ref --new ../smoderp-new \\
                   --config bench/cfg/4Gti.ini --label "2b-cumulative" --reps 3

Config je relativní k pracovnímu stromu; musí existovat v obou (nebo dej
absolutní cestu k .ini, jehož cesty k datům jsou taky absolutní).
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
    """Peak RSS v MB. resource je POSIX-only, na Windows pres psapi."""
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
# volitelny monkeypatch modul (pro zmeny, ktere jeste nejsou ve zdrojacich)
for _m in filter(None, os.environ.get('GATE_INSTALL', '').split(',')):
    __import__(_m).install()
import smoderp2d.time_step as TS
steps = [0]; _o = TS.TimeStep.do_next_h
def dn(self, *a, **k):
    steps[0] += 1
    return _o(self, *a, **k)
TS.TimeStep.do_next_h = dn
if count is not None:
    count.reset()          # pocitat jen bezici vypocet, ne nacitani dat
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
    """Jeden běh v daném pracovním stromě. Vrací dict."""
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
    raise RuntimeError('beh selhal v %s:\n%s' % (tree, p.stderr[-3000:]))


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
    """Pripise radek do ledgeru. res/ratio/cnt mohou byt None."""
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
    print('\nzapsano do %s' % os.path.abspath(a.ledger))
    print('=' * 62)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True, help='pracovni strom prijateho stavu')
    ap.add_argument('--new', required=True, help='pracovni strom kandidata')
    ap.add_argument('--config', required=True)
    ap.add_argument('--label', required=True, help='oznaceni kroku, jde do ledgeru')
    ap.add_argument('--reps', type=int, default=3)
    ap.add_argument('--ledger', default='ledger.csv')
    ap.add_argument('--only', choices=['vse','korektnost'], default='vse',
                    help='korektnost = jen bajtove porovnani, 2 behy misto 10')
    ap.add_argument('--install-new', default='',
                    help='moduly k install() jen na strane --new, oddelene carkou')
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))

    print('=' * 62)
    print('AKCEPTACNI BRANA  |  %s' % a.label)
    print('=' * 62)

    # --- korektnost: jeden bezi na kazde strane, pak bajtove ---
    print('\n[1/3] KOREKTNOST  (bajtove porovnani vystupu)')
    for tree in (a.ref, a.new):
        shutil.rmtree(outdir_of(tree, a.config), ignore_errors=True)
    run_once(a.ref, a.config)
    run_once(a.new, a.config, install=a.install_new)
    same, diff, o1, o2 = compare(outdir_of(a.ref, a.config),
                                 outdir_of(a.new, a.config))
    ok = not diff and not o1 and not o2
    print('      identickych %d | odlisnych %d | jen v ref %d | jen v new %d'
          % (len(same), len(diff), len(o1), len(o2)))
    for f in (diff + o1 + o2)[:10]:
        print('        ! ' + f)
    print('      -> %s' % ('PASS' if ok else 'FAIL'))
    if not ok:
        print('\n      Zmena NENI ekvivalentni refaktor. Bud je v ni chyba,')
        print('      nebo patri do kategorie B (zmena numericke metody) a')
        print('      validuje se proti merenim, ne proti referencnimu behu.')

    if a.only == 'korektnost':
        print('\n[2/3] VYKON     preskoceno (--only korektnost)')
        print('[3/3] POSTUP    preskoceno (--only korektnost)')
        _ledger(a, ok, diff, o1, o2, None, None, None)
        sys.exit(0 if ok else 1)

    # --- vykon: reportuje se zvlast, bez ohledu na verdikt vyse ---
    print('\n[2/3] VYKON  (median z %d behu)' % a.reps)
    res = {}
    for tag, tree in (('ref', a.ref), ('new', a.new)):
        w, s, m = [], None, None
        for _ in range(a.reps):
            r = run_once(tree, a.config,
                         install=a.install_new if tag == 'new' else '')
            w.append(r['wall']); s = r['steps']; m = r['rss_mb']
        res[tag] = {'wall': statistics.median(w), 'min': min(w),
                    'steps': s, 'rss': m}
        print('      %-4s %8.2f s (min %.2f)  kroku %d  RSS %.0f MB'
              % (tag, res[tag]['wall'], res[tag]['min'], s, m))
    ratio = res['ref']['wall'] / res['new']['wall']
    print('      -> %.2fx' % ratio)
    if res['ref']['steps'] != res['new']['steps']:
        print('      POZOR: jiny pocet casovych kroku (%d vs %d) => zmenila se '
              'numerika' % (res['ref']['steps'], res['new']['steps']))

    # --- postup: deterministicka metrika ---
    print('\n[3/3] POSTUP  (volani numpy.ma na casovy krok)')
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
