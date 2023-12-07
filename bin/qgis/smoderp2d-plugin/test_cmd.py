import sys
sys.path.append(r'C:\Users\martin\Documents\GitHub\smoderp2d\bin\qgis\smoderp2d-plugin')

from connect_grass import find_grass_bin

grass_bin = find_grass_bin()

import grass.script.setup as gsetup

gisdb = r"C:\Users\martin\Documents\grassdata"
gsetup.init(gisdb, "world_latlong_wgs84", 'PERMANENT')

from grass.pygrass.modules import Module

from subprocess import PIPE
m = Module("g.gisenv", stdout_=PIPE)
print(m.outputs.stdout)
print("done")