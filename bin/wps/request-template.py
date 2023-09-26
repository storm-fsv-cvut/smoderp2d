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
data_dir = os.path.join(tests_dir, 'data')

if 'profile1d' in args.template:
    d = {
        'input': file_content(
            os.path.join(data_dir, 'profile1d', 'data1D.csv')
        ),
        'soil_types': file_content(
            os.path.join(data_dir, 'profile1d', 'data1D_soil_types.csv')
        ),
        'rainfall': file_content(os.path.join(data_dir, 'rainfall.txt')),
        'config': file_content(os.path.join(tests_dir, 'profile1d.ini'))
    }
else:  # smoderp2d
    d = {
        'input': file_content(os.path.join(data_dir, 'destak.save')),
        'rainfall': file_content(os.path.join(data_dir, 'rainfall.txt')),
        'config': file_content(os.path.join(tests_dir, 'quicktest.ini'))
    }

with open(args.template, 'r') as f:
    src = Template(f.read())
    result = src.substitute(d)
    print(result)
