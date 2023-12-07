import sys
sys.path.append('/home/martin/git/storm-fsv-cvut/smoderp2d/bin/qgis/smoderp2d-plugin')

from connect_grass import find_grass_bin

grass_bin = find_grass_bin()

import grass.script.setup as gsetup

gisdb = "/home/martin/grassdata/"
gsetup.init(gisdb, "world_latlong_wgs84", 'PERMANENT')

from grass.pygrass.modules import Module

from subprocess import PIPE
m = Module("g.gisenv", stdout_=PIPE)
print(m.outputs.stdout)
print("done")