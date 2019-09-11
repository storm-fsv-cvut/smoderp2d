from grass.pygrass.modules import Module

def compute_products(elev, fldir=None):
    """
    Computes terrain products from elevation.

    Computes:
     * filled elevation
     * flow direction
     * flow accumulation
     * slope (percentage)

    :param str elev: DTM raster name
    :param str fldir: flow direction raster name or None

    :return: flow_direction, flow_accumulation, slope
    """
    elev_fill = 'fill'
    flow_direction = 'fldir'
    flow_accumulation = 'facc'
    slope = 'slope'
    # filling the sink areas in raster
    # flow direction calculation
    Module('g.region',
           raster=elev
    )
    # Module('r.fill.dir',
    #                input=elev,
    #                output=elev_fill,
    #                direction=flow_direction
    # )

    # Module('r.flow',
    #                elevation=elev_fill,
    #                flowaccumulation=flow_accumulation
    # )
    Module('r.watershed',
           flags='as',
           elevation=elev,
           drainage=flow_direction + '_grass',
           accumulation=flow_accumulation,
           depression=elev
    )
    if not fldir:
        # recalculate flow dir to ArcGIS notation
        # https://idea.isnew.info/how-to-import-arcgis-flow-direction-into-grass-gis.html
        reclass = """
    -1 1 = 128
    -2 2 = 64
    -3 3 = 32
    -4 4 = 16
    -5 5 = 8
    -6 6 = 4
    -7 7 = 2
    -8 8 = 1
    """
        Module('r.reclass',
               input=flow_direction + '_grass',
               output=flow_direction,
               rules='-',
               stdin_=reclass
        )
    else:
        flow_direction = fldir

    # computing slope from original DEM seems to be closer to ArcGIS
    # results
    Module('r.slope.aspect',
           elevation=elev,
           format='percent',
           slope=slope
    )
    
    return flow_direction, flow_accumulation, slope
