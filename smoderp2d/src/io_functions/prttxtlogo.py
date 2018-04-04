from __future__ import print_function

import os

def prttxtlogo():
    """Print Smoderp2d ascii-style logo to standard output."""
    with open(os.path.join(os.path.dirname(__file__), 'txtlogo.txt'), 'r') as f :
        d = f.readlines()
        try:
            # TODO: avoid arcpy import (should be solved by providers - ArcGIS, GRASS, ...)
            import arcpy
            for line in d:
                arcpy.AddMessage(line.replace('\n', ''))
        except ImportError:
            for line in d:
                print(line, end='')
            print(os.linesep)
