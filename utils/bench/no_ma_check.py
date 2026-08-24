"""Static check that numpy.ma has not crept back into converted modules.

Once a conversion step is finished, the converted files are added to the list
and this script guards against anyone reintroducing masked arrays there.
Deterministic, works on the AST, does not run the model.

USAGE
-----
    python no_ma_check.py smoderp2d/core/cumulative_max.py smoderp2d/processes
    python no_ma_check.py --list converted.txt
    python no_ma_check.py smoderp2d/          # whole package

Exit code 0 = clean, 1 = numpy.ma usage found.
"""

import argparse
import ast
import os
import sys


class Finder(ast.NodeVisitor):
    """Find numpy.ma imports and ma.* / np.ma.* attribute accesses."""

    def __init__(self):
        # 'ma' is always watched, not only when an import is visible.
        # Without that, a broken intermediate state passes as "clean": one
        # where `import numpy.ma as ma` has already been removed but
        # `ma.power(...)` is still left in the body. Such a file would fail
        # at run time with NameError, but the static check has to catch it
        # first.
        self.aliases = {'ma'}     # names numpy.ma is imported under
        self.hits = []            # (line number, text)

    def visit_Import(self, node):
        for a in node.names:
            if a.name in ('numpy.ma', 'numpy.ma.core'):
                self.aliases.add(a.asname or a.name.split('.')[0])
                self.hits.append((node.lineno, 'import ' + a.name))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        mod = node.module or ''
        if mod.startswith('numpy.ma'):
            self.hits.append((node.lineno, 'from %s import ...' % mod))
        elif mod == 'numpy':
            for a in node.names:
                if a.name == 'ma':
                    self.aliases.add(a.asname or 'ma')
                    self.hits.append((node.lineno, 'from numpy import ma'))
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # ma.where(...)  /  np.ma.where(...)
        v = node.value
        if isinstance(v, ast.Name) and v.id in self.aliases:
            self.hits.append((node.lineno, '%s.%s' % (v.id, node.attr)))
        elif (isinstance(v, ast.Attribute) and v.attr == 'ma'
              and isinstance(v.value, ast.Name)):
            self.hits.append((node.lineno, '%s.ma.%s'
                              % (v.value.id, node.attr)))
        self.generic_visit(node)


def check(path):
    with open(path, encoding='utf-8') as fd:
        src = fd.read()
    f = Finder()
    f.visit(ast.parse(src, filename=path))
    lines = src.splitlines()
    return [(ln, what, lines[ln - 1].strip() if ln <= len(lines) else '')
            for ln, what in sorted(set(f.hits))]


def expand(targets):
    out = []
    for t in targets:
        if os.path.isdir(t):
            for root, _, files in os.walk(t):
                out += [os.path.join(root, fn) for fn in sorted(files)
                        if fn.endswith('.py')]
        elif t.endswith('.py'):
            out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('targets', nargs='*')
    ap.add_argument('--list', help='text file with paths, one per line')
    a = ap.parse_args()
    targets = list(a.targets)
    if a.list:
        with open(a.list) as fd:
            targets += [l.strip() for l in fd
                        if l.strip() and not l.startswith('#')]
    files = expand(targets)
    if not files:
        print('nothing to check'); return 0

    bad = 0
    print('=' * 62)
    print('CHECK: numpy.ma in converted modules')
    print('=' * 62)
    for p in files:
        hits = check(p)
        if hits:
            bad += 1
            print('\n%s  -- %d occurrences' % (p, len(hits)))
            for ln, what, text in hits[:12]:
                print('   r.%-5d %-22s %s' % (ln, what, text[:60]))
            if len(hits) > 12:
                print('   ... and %d more' % (len(hits) - 12))
        else:
            print('  OK  %s' % p)
    print('\n' + '-' * 62)
    print('files checked: %d | with numpy.ma: %d' % (len(files), bad))
    print('-> %s' % ('CLEAN' if bad == 0 else 'FOUND numpy.ma'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
