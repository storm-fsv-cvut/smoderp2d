#!/usr/bin/env python

############################################################################
#
# MODULE:      r.smoderp2d
# AUTHOR(S):   Martin Landa and SMODERP2D development team
# PURPOSE:     Performs SMODERP2D soil erosion model.
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
#% description: Performs SMODERP2D soil erosion model.
#% keyword: raster
#% keyword: hydrology
#% keyword: soil
#% keyword: erosion
#%end
#%option G_OPT_R_ELEV
#% description: Input surface raster
#% guisection: Data preparation
#%end
#%option G_OPT_V_INPUT
#% key: soil
#% label: Input soil polygon features
#% guisection: Data preparation
#%end
#%option G_OPT_DB_COLUMN
#% key: soil_type
#% description: Soil types
#% required: yes
#% guisection: Data preparation
#%end
#%option G_OPT_V_INPUT
#% key: vegetation
#% label: Input land use polygon features
#% guisection: Data preparation
#%end
#%option G_OPT_DB_COLUMN
#% key: vegetation_type
#% description: Land use types
#% required: yes
#% guisection: Data preparation
#%end
#%option G_OPT_F_INPUT
#% key: rainfall_file
#% description: Rainfall file
#% guisection: Computation
#%end
#%option
#% key: maxdt
#% type: double
#% description: Max time step [sec]
#% answer: 30
#% required: yes
#% guisection: Settings
#%end
#%option
#% key: end_time
#% type: double
#% description: Total running time [min]
#% answer: 5
#% required: yes
#% guisection: Computation
#%end
#%option G_OPT_V_INPUT
#% key: points
#% label: Input points features
#% required: no
#% guisection: Data preparation
#%end
#%option G_OPT_DB_TABLE
#% key: table_soil_vegetation
#% description: Table of soil and land use information
#% guisection: Settings
#%end
#%option G_OPT_DB_COLUMN
#% key: table_soil_vegetation_code
#% description: Soil land use code
#% guisection: Settings
#%end
#%option G_OPT_V_INPUT
#% key: stream
#% label: Reach feature
#% required: no
#% guisection: Data preparation
#%end
#%option G_OPT_DB_TABLE
#% key: table_stream_shape
#% description: Reach shapes table
#% guisection: Settings
#%end
#%option G_OPT_DB_COLUMN
#% key: table_stream_shape_code
#% description: Reach shape table code
#% guisection: Settings
#%end

import os
import sys
import grass.script as gs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from smoderp2d import GrassRunner
from smoderp2d.exceptions import ProviderError

if __name__ == "__main__":
    options, flags = gs.parser()
    try:
        runner = GrassRunner()
        runner.set_options(options) # flags skipped (empty)
        sys.exit(runner.run())
    except ProviderError as e:
        gs.fatal(e)
