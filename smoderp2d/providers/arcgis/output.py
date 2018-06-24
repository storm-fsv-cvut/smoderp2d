import arcpy

from smoderp2d.base.general import GridGlobals, Globals
from smoderp2d.base.output import RasterAsciiBase

class RasterAscii(RasterAsciiBase):
    def __init__(self, filename):
        super(RasterAscii, self).__init__(filename)

        arcpy.env.workspace = Globals.outdir

    def write(self, array, fs=None):
        ll_corner = arcpy.Point(*GridGlobals.get_llcorner())
        size = GridGlobals.get_size()
        
        outName = output + os.sep + outname
        saveAG = arcpy.NumPyArrayToRaster(
            out_array,
            ll_corner,
            size[0],
            size[1],
            self.no_data)
        saveAG.save(os.path.join(Globals.outdir, filename))
