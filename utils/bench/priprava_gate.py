"""Připraví konfigurace pro gate.py. Spustit jednou, pak už jen gate.py.

Vygeneruje .ini s ABSOLUTNÍMI cestami k datům a RELATIVNÍM výstupním
adresářem. Díky tomu stačí jeden config pro oba pracovní stromy — data se
nikam nekopírují (u 1 m sad by to bylo 122 MB na kus) a každý strom si píše
výstup k sobě, takže se běhy nepřebíjejí.

POUŽITÍ
-------
    cd D:\\_Claude_projekty\\SMODERP\\02_fork_from_GIT_to_improve\\smoderp2d\\utils\\bench
    python priprava_gate.py

Volitelně jiný korenový adresář projektu:

    python priprava_gate.py --base D:\\_Claude_projekty\\SMODERP
"""

import argparse
import os

CFG = """[data]
rainfall: {rain}
pickle: {save}
[time]
maxdt: 5
endtime: 6
[output]
outdir: bench_out_{name}
printtimes:
[logging]
level: ERROR
[processes]
typecomp: stream_rill
mfda: {mfda}
wave: kinematic
"""

SETS = [
    ('1010', 'Save_1010', 'False'),
    ('4Gor', 'Save_4Gor', 'False'),
    ('4Gti', 'Save_4Gti', 'False'),
    ('5Gor', 'Save_5Gor', 'False'),
    ('5Gti', 'Save_5Gti', 'False'),
    ('LASor', 'Save_LASor', 'False'),
    ('LASti', 'Save_LASti', 'False'),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    # here = .../02_fork_from_GIT_to_improve/smoderp2d/utils/bench
    # korenovy adresar projektu je o 4 urovne vys (bench -> utils ->
    # smoderp2d -> 02_fork_from_GIT_to_improve -> SMODERP)
    ap.add_argument('--base', default=os.path.abspath(
        os.path.join(here, '..', '..', '..', '..')))
    ap.add_argument('--out', default=os.path.join(here, 'cfg'))
    a = ap.parse_args()

    data = os.path.join(a.base, '02_added_data_in')
    rain = os.path.join(data, 'rainfall_nucice.txt')
    if not os.path.exists(rain):
        raise SystemExit('nenalezen %s\npouzij --base' % rain)
    os.makedirs(a.out, exist_ok=True)

    print('korenovy adresar : %s' % a.base)
    print('configy pujdou do: %s\n' % a.out)
    made = []
    for name, folder, mfda in SETS:
        save = os.path.join(data, folder, 'dpre.save')
        if not os.path.exists(save):
            print('  - %-6s preskoceno, chybi %s' % (name, save))
            continue
        p = os.path.join(a.out, name + '.ini')
        with open(p, 'w') as fd:
            fd.write(CFG.format(rain=rain.replace('\\', '/'),
                                save=save.replace('\\', '/'),
                                name=name, mfda=mfda))
        mb = os.path.getsize(save) / 1e6
        print('  OK %-6s %-14s %6.0f MB   -> %s' % (name, folder, mb, p))
        made.append(p)

    print('\nhotovo, %d configu' % len(made))
    print('\nDalsi krok:')
    print('  python gate.py --ref <cesta k 01_source_code_from_GIT> \\')
    print('                 --new <cesta k 04_kod_zrychleny_v2> \\')
    print('                 --config "%s" \\'
          % os.path.join(a.out, '5Gor.ini'))
    print('                 --label krok1-5Gor --reps 1')


if __name__ == '__main__':
    main()
