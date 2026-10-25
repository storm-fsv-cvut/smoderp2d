#!/usr/bin/env python3

############################################################################
#
# MODULE:      r.smoderp2d
# AUTHOR(S):   Martin Landa and SMODERP2D development team
# PURPOSE:     Performs SMODERP2D soil erosion model.
# COPYRIGHT:   (C) 2018-2024 by Martin Landa and Smoderp2d development team
#
#              This program is free software under the GNU General Public
#              License (>=v3.0) and comes with ABSOLUTELY NO WARRANTY.
#              See the file COPYING that comes with GRASS
#              for details.
#
#
#############################################################################

# %module
# % description: Performs SMODERP2D soil erosion model.
# % keyword: raster
# % keyword: hydrology
# % keyword: soil
# % keyword: erosion
# %end
# %flag
# % key: t
# % description: Generate also temporary data
# % guisection: Advanced
# %end
# %option G_OPT_R_ELEV
# % description: Input surface raster
# % guisection: Spatial data
# %end
# %option G_OPT_V_INPUT
# % key: soil
# % label: Soil polygons feature layer
# % guidependency: soil_type_fieldname
# % guisection: Spatial data
# %end
# %option G_OPT_DB_COLUMN
# % key: soil_type_fieldname
# % description: Field with the soil type identifier
# % required: yes
# % guisection: Spatial data
# %end
# %option G_OPT_V_INPUT
# % key: vegetation
# % label: Landuse polygons feature layer
# % guidependency: vegetation_type_fieldname
# % guisection: Spatial data
# %end
# %option G_OPT_DB_COLUMN
# % key: vegetation_type_fieldname
# % description: Field with the landuse type identifier
# % required: yes
# % guisection: Spatial data
# %end
# %option G_OPT_V_INPUT
# % key: points
# % label: Input points feature layer
# % required: no
# % guidependency: points_fieldname
# % guisection: Spatial data
# %end
# %option G_OPT_DB_COLUMN
# % key: points_fieldname
# % description: Field with the input points idenfifier
# % required: no
# % guisection: Spatial data
# %end
# %option G_OPT_V_INPUT
# % key: streams
# % label: Stream network feature layer
# % required: no
# % guisection: Spatial data
# %end
# %option G_OPT_F_INPUT
# % key: rainfall_file
# % description: Definition of the rainfall event
# % guisection: Spatial data
# %end
# %option G_OPT_DB_TABLE
# % key: table_soil_vegetation
# % description: Soils and landuse parameters table
# % guidependency: table_soil_vegetation_fieldname
# % guisection: Model parameters
# %end
# %option G_OPT_DB_COLUMN
# % key: table_soil_vegetation_fieldname
# % description: Field with the connection between landuse and soil
# % guisection: Model parameters
# %end
# %option G_OPT_DB_TABLE
# % key: channel_properties_table
# % description: Channel properties table
# % guidependency: streams_channel_type_fieldname
# % guisection: Model parameters
# %end
# %option G_OPT_DB_COLUMN
# % key: streams_channel_type_fieldname
# % description: Field with the channel type identifier
# % guisection: Model parameters
# %end
# %option G_OPT_M_DIR
# % key: output
# % description: Output directory
# % required: yes
# % guisection: Computation options
# %end
# %option
# % key: maxdt
# % type: double
# % description: Maximum time step [s]
# % answer: 30
# % required: yes
# % guisection: Computation options
# %end
# %option
# % key: end_time
# % type: double
# % description: Total running time [min]
# % answer: 5
# % required: yes
# % guisection: Computation options
# %end
# %option
# % key: flow_direction
# % description: Flow direction
# % guisection: Advanced
# % options: single,multiple
# % answer: single
# %end
# %option
# % key: wave
# % description: Wave type
# % guisection: Advanced
# % options: kinematic,diffusion
# % answer: kinematic
# %end

import os
import sys
import grass.script as gs

if __name__ == "__main__":
    options, flags = gs.parser()
    options['generate_temporary'] = flags['t']

    from smoderp2d.runners.grass import GrassGisRunner
    from smoderp2d.providers.base import WorkflowMode
    from smoderp2d.exceptions import ProviderError, MaxIterationExceeded

    try:
        runner = GrassGisRunner()
        runner.set_options(options)
        runner.run()
        runner.finish()
    except (ProviderError, MaxIterationExceeded) as e:
        gs.fatal(e)
