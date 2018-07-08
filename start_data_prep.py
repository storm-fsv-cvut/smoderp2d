#!/usr/bin/env python
import os
import sys


if __name__ == "__main__":
    from smoderp2d.data_preparation.data_preparation import PrepareData
    prep = PrepareData()
#   prep.prepare_data(sys.argv)
    prep.prepare_data()

else:
    import arcpy
    arcpy.AddMessage("Problem.")
