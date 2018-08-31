#!/usr/bin/env python

############################################################################
#
# MODULE:      r.smoderp2d
# AUTHOR(S):   Martin Landa and Smoderp2d development team
# PURPOSE:     Performs Smoderp2d soil erosion model.
# COPYRIGHT:   (C) 2018 by Martin Landa and Smoderp2d development team
#
#              This program is free software under the GNU General Public
#              License (>=v3.0) and comes with ABSOLUTELY NO WARRANTY.
#              See the file COPYING that comes with GRASS
#              for details.
#
#
#############################################################################

#%module
#% description: Performs Smoderp2d soil erosion model.
#% keyword: raster
#% keyword: hydrology
#% keyword: soil
#% keyword: erosion
#%end

import sys
import grass.script as gs

def main():
    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
