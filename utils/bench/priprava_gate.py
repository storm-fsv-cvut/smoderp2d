"""Generate the configurations for gate.py. Run once, then only gate.py.

Writes .ini files with ABSOLUTE paths to the data and a RELATIVE output
directory. That way a single config serves both working trees: the data is
not copied anywhere (for the 1 m sets that would be 122 MB a piece) and each
tree writes its output next to itself, so the runs do not overwrite each
other.

USAGE
-----
    cd D:\\_Claude_projekty\\SMODERP\\02_fork_from_GIT_to_improve\\smoderp2d\\utils\\bench
    python priprava_gate.py

Optionally a different project root directory:

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
    # the project root is 4 levels up (bench -> utils ->
    # smoderp2d -> 02_fork_from_GIT_to_improve -> SMODERP)
    ap.add_argument('--base', default=os.path.abspath(
        os.path.join(here, '..', '..', '..', '..')))
    ap.add_argument('--out', default=os.path.join(here, 'cfg'))
    a = ap.parse_args()

    data = os.path.join(a.base, '02_added_data_in')
    rain = os.path.join(data, 'rainfall_nucice.txt')
    if not os.path.exists(rain):
        raise SystemExit('not found: %s\nuse --base' % rain)
    os.makedirs(a.out, exist_ok=True)

    print('project root  : %s' % a.base)
    print('configs go to : %s\n' % a.out)
    made = []
    for name, folder, mfda in SETS:
        save = os.path.join(data, folder, 'dpre.save')
        if not os.path.exists(save):
            print('  - %-6s skipped, missing %s' % (name, save))
            continue
        p = os.path.join(a.out, name + '.ini')
        with open(p, 'w') as fd:
            fd.write(CFG.format(rain=rain.replace('\\', '/'),
                                save=save.replace('\\', '/'),
                                name=name, mfda=mfda))
        mb = os.path.getsize(save) / 1e6
        print('  OK %-6s %-14s %6.0f MB   -> %s' % (name, folder, mb, p))
        made.append(p)

    print('\ndone, %d configs' % len(made))
    print('\nNext step:')
    print('  python gate.py --ref <cesta k 01_source_code_from_GIT> \\')
    print('                 --new <cesta k 04_kod_zrychleny_v2> \\')
    print('                 --config "%s" \\'
          % os.path.join(a.out, '5Gor.ini'))
    print('                 --label step1-5Gor --reps 1')


if __name__ == '__main__':
    main()
