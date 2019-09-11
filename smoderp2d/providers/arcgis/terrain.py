import arcpy
import sys
import os

from smoderp2d.exceptions import ProviderError

def compute_products(elev, save_dir, fldir=None):
    """
    Computes terrain products from elevation.

    Computes:
     * filled elevation
     * flow direction
     * flow accumulation
     * slope (percentage)

    :param str elev: DTM raster name
    :param str save_dir: directory where to save output
    :param str fldir: flow direction raster name or None

    :return: flow_direction, flow_accumulation, slope
    """
    # loading file soil_type_values
    # filling the sink areas in raster
    try:
        elev_fill = arcpy.sa.Fill(elev)
        elev_fill.save(os.path.join(save_dir, 'temp', "fill"))
    except:
        raise ProviderError(
            "Unexpected error during raster fill calculation: {}".format(
                sys.exc_info()[0]
            ))

    # flow direction calculation
    try:
        if not fldir:
            flow_direction = arcpy.sa.FlowDirection(elev_fill)
            flow_direction.save(os.path.join(save_dir, 'control', "flowdir_inter"))
        else:
            flow_direction = fldir
    except:
        raise ProviderError(
            "Unexpected error during flow direction calculation: {}".format(
                sys.exc_info()[0]
            ))

    # flow accumulation calculation
    try:
        flow_accumulation = arcpy.sa.FlowAccumulation(flow_direction)
        flow_accumulation.save(os.path.join(save_dir, 'temp', "facc"))
    except:
        raise ProviderError(
            "Unexpected error during flow accumulation calculation: {}".format(
                sys.exc_info()[0]
            ))

    # slope calculation
    try:
        slope = arcpy.sa.Slope(elev, "PERCENT_RISE", 1)
        slope.save(os.path.join(save_dir, 'temp', "slope_inter"))
    except:
        raise ProviderError(
            "Unexpected error during slope calculation: {}".format(
                sys.exc_info()[0]
            ))

    return flow_direction, flow_accumulation, slope
