"""Statická kontrola, že se numpy.ma nevrátilo do převedených modulů.

Po dokončení dílčího kroku 2x se převedené soubory přidají do seznamu a tenhle
skript hlídá, že tam maskovaná pole nikdo omylem nevrátí. Deterministické,
běží nad AST, nespouští model.

POUŽITÍ
-------
    python no_ma_check.py smoderp2d/core/cumulative_max.py smoderp2d/processes
    python no_ma_check.py --list prevedene.txt

Návratový kód 0 = čisté, 1 = nalezeno použití numpy.ma.
"""

import argparse
import ast
import os
import sys


class Finder(ast.NodeVisitor):
    """Najde importy numpy.ma a přístupy na ma.* / np.ma.*."""

    def __init__(self):
        self.aliases = set()      # jména, pod kterými je numpy.ma naimportované
        self.hits = []            # (radek, text)

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
    ap.add_argument('--list', help='textovy soubor s cestami, jedna na radek')
    a = ap.parse_args()
    targets = list(a.targets)
    if a.list:
        with open(a.list) as fd:
            targets += [l.strip() for l in fd
                        if l.strip() and not l.startswith('#')]
    files = expand(targets)
    if not files:
        print('nic ke kontrole'); return 0

    bad = 0
    print('=' * 62)
    print('KONTROLA: numpy.ma v prevedenych modulech')
    print('=' * 62)
    for p in files:
        hits = check(p)
        if hits:
            bad += 1
            print('\n%s  -- %d vyskytu' % (p, len(hits)))
            for ln, what, text in hits[:12]:
                print('   r.%-5d %-22s %s' % (ln, what, text[:60]))
            if len(hits) > 12:
                print('   ... a dalsich %d' % (len(hits) - 12))
        else:
            print('  OK  %s' % p)
    print('\n' + '-' * 62)
    print('souboru zkontrolovano: %d | s numpy.ma: %d' % (len(files), bad))
    print('-> %s' % ('CISTE' if bad == 0 else 'NALEZENO numpy.ma'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
