import grass.script as gs

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

    :return: elev_fill, flow_direction, flow_accumulation, slope
    """
    elev_fill = 'fill'
    flow_direction = 'fldir'
    flow_accumulation = 'facc'
    slope = 'slope'
    # filling the sink areas in raster
    # flow direction calculation
    gs.run_command('r.fill.dir',
                   input=elev,
                   output=elev_fill,
                   direction=flow_direction
    )

    gs.run_command('r.flow',
                   elevation=elev_fill,
                   flowaccumulation=flow_accumulation
    )

    gs.run_command('r.slope.aspect',
                   elevation=elev_fill,
                   format='percent',
                   slope=slope
    )
    
    return elev_fill, flow_direction if fldir else None, flow_accumulation, slope
            
