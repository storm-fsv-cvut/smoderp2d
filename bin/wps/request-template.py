import os
import argparse
from string import Template

def file_content(filename):
    with open(filename, 'r') as fd:
        return fd.read()

parser = argparse.ArgumentParser("Template WPS request")

parser.add_argument(
    '--template',
    help='XML request template',
    type=str,
    required=True
)

args = parser.parse_args()
tests_dir = os.path.join('..', '..', 'tests')
if 'smoderp1d' in args.template:
    d = {
        'input': file_content(os.path.join(tests_dir, 'data', 'nogis', 'data1D.csv')),
        'soil_types': file_content(os.path.join(tests_dir, 'data', 'nogis', 'data1D_soil_types.csv')),
        'rainfall': file_content(os.path.join(tests_dir, 'data', 'rainfall.txt')),
        'config': file_content(os.path.join(tests_dir, 'nogis.ini'))
    }
else: # smoderp2d
    d = {
        'input': file_content(os.path.join(tests_dir, 'data', 'destak.save')),
        'rainfall': file_content(os.path.join(tests_dir, 'data', 'rainfall.txt')),
        'config': file_content(os.path.join(tests_dir, 'quicktest.ini'))
    }

with open(args.template, 'r') as f:
    src = Template(f.read())
    result = src.substitute(d)
    print(result)
