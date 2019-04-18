import numpy as np

from smoderp2d.base.general import GridGlobals, Globals

class RasterAsciiBase(object):
    def __init__(self, filename):
        self.filename = filename
        self._fd = None

    def create_array(self, array, fs=None):
        rrows, rcols = GridGlobals.get_region_dim()

        # create empty array
        out_array = np.empty(array.shape, array.dtype)

        # no-data
        if np.issubdtype(array.dtype, int):
            self.no_data = Globals.NoDataInt
        else:
            self.no_data = Globals.NoDataValue
        if self._fd:
            self._fd.write("nodata_value {0}{nl}".format(
                self.no_data, nl=os.linesep
            ))
        out_array.fill(self.no_data)

        # copy values
        for i in rrows:
            for j in rcols[i]:
                out_array[i][j] = array[i][j]

        if fs:
            # TODO: explain
            for i in rrows:
                for j in rcols[i]:
                    if fs[i][j] >= 1000:
                        out_array[i][j] = no_data

        return out_array

class RasterAscii(RasterAsciiBase):
    def __init__(self, filename):
        super(RasterAscii, self).__init__(filename)

        self._fd = open(
            os.path.join(Globals.outdir, filename + '.asc'),
            'w')
        self._fd.write("ncols {0}{nl}nrows {1}{nl}".format(
            *GridGlobals.get_dim(), nl=os.linesep
        ))
        self._fd.write("xllcorner {0}{nl}yllcorner {1}{nl}".format(
            *GridGlobals.get_llcorner(), nl=os.linesep
        ))
        self._fd.write("cellsize {0}{nl}".format(
            GridGlobals.get_size()[0], nl=os.linesep
        ))

    def __del__(self):
        self._fd.close()
    
    def write(self, array, fs=None):
        out_array = create_array(array, fs)
        
        # write array to target file
        nrows, ncols = GridGlobals.get_dim()
        for i in range(nrows):
            line = ""
            for j in range(ncols):
                line += '{}\t'.format(out_array[i][j])
            line += os.linesep
            self._fd.write(line)
