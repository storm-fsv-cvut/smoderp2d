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

The simulated end time is a parameter. The default 6 min covers the whole
rainfall record plus one minute; a longer end time adds the recession, which
changes how representative the measured ratio is for a full event. Configs
generated with a non-default end time get a name suffix and their own output
directory, so they never collide with the default ones:

    python priprava_gate.py --endtime 13 --suffix=-e13
    -> cfg/4Gti-e13.ini writing to bench_out_4Gti-e13

Note the '=' in --suffix=-e13. A value starting with a dash has to be
attached with '=', otherwise argparse reads it as another option.
"""

import argparse
import os

CFG = """[data]
rainfall: {rain}
pickle: {save}
[time]
maxdt: 5
endtime: {endtime}
[output]
outdir: bench_out_{name}
printtimes:
[logging]
level: {level}
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
    ap.add_argument('--endtime', default='6',
                    help='simulated end time in minutes (default 6)')
    ap.add_argument('--level', default='ERROR',
                    help='log level; INFO also writes the progress blocks '
                         'that the log comparison reads (default ERROR)')
    ap.add_argument('--suffix', default='',
                    help='appended to the config name and to the output '
                         'directory, e.g. -e13')
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
        tag = name + a.suffix
        p = os.path.join(a.out, tag + '.ini')
        with open(p, 'w') as fd:
            fd.write(CFG.format(rain=rain.replace('\\', '/'),
                                save=save.replace('\\', '/'),
                                name=tag, mfda=mfda,
                                endtime=a.endtime, level=a.level))
        mb = os.path.getsize(save) / 1e6
        print('  OK %-8s %-14s %6.0f MB   -> %s' % (tag, folder, mb, p))
        made.append(p)

    print('\ndone, %d configs  (endtime %s min, log level %s)'
          % (len(made), a.endtime, a.level))
    print('\nNext step:')
    print('  python gate.py --ref <cesta k 01_source_code_from_GIT> \\')
    print('                 --new <cesta k 04_kod_zrychleny_v2> \\')
    print('                 --config "%s" \\'
          % os.path.join(a.out, '5Gor' + a.suffix + '.ini'))
    print('                 --label step1-5Gor --reps 1')


if __name__ == '__main__':
    main()
