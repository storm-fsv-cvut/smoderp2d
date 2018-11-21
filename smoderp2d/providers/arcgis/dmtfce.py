import arcpy
import sys
import os

def dmtfce(dmt, save_dir, fl_dir=None):
    """

    :param str dmt: DMT raster name
    :param str save_dir: directory where to save output
    :param str fl_dir: flow direction raster name or None
    """
    # loading file soil_type_values
    # filling the sink areas in raster
    try:
        dmt_fill = arcpy.sa.Fill(dmt)
    except:
        # TODO: use our own exceptions...
        arcpy.AddMessage(
            "Unexpected error during raster fill calculation:",
            sys.exc_info()[0])
        raise

    # flow direction calculation
    try:
        if not fl_dir:
            flow_direction = arcpy.sa.FlowDirection(dmt_fill)
            flow_direction.save(os.path.join(save_dir, "fl_dir"))
        else:
            flow_direction = fl_dir
    except:
        arcpy.AddMessage(
            "Unexpected error during flow direction calculation:",
            sys.exc_info()[0])
        raise

    # flow accumulation calculation
    try:
        flow_accumulation = arcpy.sa.FlowAccumulation(flow_direction)
        flow_accumulation.save(os.path.join(save_dir, "facc"))
    except:
        arcpy.AddMessage(
            "Unexpected error during flow accumulation calculation:",
            sys.exc_info()[0])
        raise

    # slope calculation
    try:
        slope = arcpy.sa.Slope(dmt, "PERCENT_RISE", 1)
        slope.save(os.path.join(save_dir, "slope"))
    except:
        arcpy.AddMessage(
            "Unexpected error during slope calculation:",
            sys.exc_info()[0])
        raise

    return dmt_fill, flow_direction, flow_accumulation, slope
