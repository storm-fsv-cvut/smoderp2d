#!/bin/bash


# '''
# onlyshallowsurface
# shallowandrillsurface
# diffuseshallowsurface
# surfaceandsubsurfaceflow
# shallowrillstreamsurface
# surfaceandsubsurfacestreamflow

# indata/nucice_rillsheetstream_dem20m.save
# indata/bikovice0.save
# indata/dp_vse.save
# indata/dp_hodne_bodu_tok.save
# indata/DS_plochamalyNx.save
# indata/ada.save
# indata/nucice_rillsheet_dem20m.save
# '''

python main.py \
- \
- \
- \
- \
- \
indata/srazka.txt \
30 \
25 \
00.0  \
- \
out \
shallowandrillsurface \
false \
- \
- \
- \
- \
- \
False \
true  \
indata/nucice_rillsheet_dem20m.save \
roff \
true
