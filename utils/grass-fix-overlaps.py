#!/usr/bin/env python

from grass.pygrass.vector import VectorTopo
from grass.pygrass.modules import Module

# VERY DIRTY WORKAROUND
# -> work in progress

vector = 'puda'
multi = []
with VectorTopo(vector, mode='r') as fd:
    for area in fd.viter('areas'):
        cats = list(area.cats().get_list())
        if len(cats) > 1:
            multi.append((area.centroid().id, cats[:-1]))

for fid, cats in multi:
    Module('v.edit', map=vector,
           tool='catdel', ids=fid,
           cats=','.join(map(lambda x: str(x), cats)))
