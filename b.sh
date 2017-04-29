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
# '''

python main.py \
- \
- \
- \
- \
- \
indata/srazka.txt \
60 \
40 \
00.0  \
10.0 \
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
indata/dp_hodne_bodu_tok.save \
roff \
true
