#!/usr/bin/env python

############################################################################
#
# MODULE:      r.smoderp2d
# AUTHOR(S):   Martin Landa and Smoderp2d development team
# PURPOSE:     Performs Smoderp 2D soil erosion model.
# COPYRIGHT:   (C) 2018-2019 by Martin Landa and Smoderp2d development team
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
#%option G_OPT_R_ELEV
#% description: Input surface raster
#%end
#%option G_OPT_V_INPUT
#% key: soil
#% description: Input soil polygon features
#%end
#%option G_OPT_DB_COLUMN
#% key: soil_type
#% description: Soil types
#% required: yes
#%end
#%option G_OPT_V_INPUT
#% key: vegetation
#% description: Input land use polygon features
#%end
#%option
#% key: vegetation_type
#% description: Land use types
#% required: yes
#%end
#%option G_OPT_F_INPUT
#% key: rainfall_file
#% description: Rainfall file
#%end
#%option
#% key: maxdt
#% type: double
#% description: Max time step [sec]
#% answer: 30
#% required: yes
#%end
#%option
#% key: end_time
#% type: double
#% description: Total running time [min]
#% answer: 5
#% required: yes
#%end
#%option G_OPT_V_INPUT
#% key: points
#% description:  Input points features
#% required: no
#%end
#%option G_OPT_M_DIR
#% key: output
#% description: Output folder
#% required: yes
#%end
#%option G_OPT_DB_TABLE
#% key: table_soil_vegetation
#% description: Table of soil and land use information
#%end
#%option G_OPT_DB_COLUMN
#% key: table_soil_vegetation_code
#% description: Soil land use code
#%end
#%option G_OPT_V_INPUT
#% key: streams
#% description:  Reach feture
#% required: no
#%end
#%option G_OPT_DB_TABLE
#% key: table_stream_shape
#% description: Reach shapes table
#%end
#%option G_OPT_DB_COLUMN
#% key: table_stream_shape_code
#% description: Reach shape table code
#%end

import os
import sys
import grass.script as gs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from smoderp2d import run
from smoderp2d.exceptions import ProviderError

if __name__ == "__main__":
    options, flags = gs.parser()
    try:
        sys.exit(run())
    except ProviderError as e:
        sys.exit(e)
