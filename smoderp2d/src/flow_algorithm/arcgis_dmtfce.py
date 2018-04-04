import arcpy
import arcgisscripting
gp = arcgisscripting.create()
import sys
import os


def dmtfce(dmt, save_dir, fill, filtr, fl_dir):
    # loading file soil_type_values
    # filling the sink areas in raster
    try:
        dmt_fill = arcpy.sa.Fill(dmt)
    except:
        arcpy.AddMessage(
            "Unexpected error during raster fill calculation:",
            sys.exc_info()[0])
        raise

    # flow direction calculation
    try:  # tady by pak meslo jit pridavat pripraven fl dir
        if fl_dir == "NONE":
            flow_direction = arcpy.sa.FlowDirection(dmt_fill)
            flow_direction.save(save_dir + os.sep + "fl_dir")
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
        flow_accumulation.save(save_dir + os.sep + "facc")
        # mat_fa = arcpy.RasterToNumPyArray(flow_accumulation)
    except:
        arcpy.AddMessage(
            "Unexpected error during flow accumulation calculation:",
            sys.exc_info()[0])
        raise

    # slope calculation
    try:
        slope = arcpy.sa.Slope(dmt, "PERCENT_RISE", 1)
        # ExtractByMask (slope, raster_dmt)
        slope.save(save_dir + "\\slope")
    except:
        arcpy.AddMessage(
            "Unexpected error during slope calculation:",
            sys.exc_info()[0])
        raise
    return dmt_fill, flow_direction, flow_accumulation, slope
