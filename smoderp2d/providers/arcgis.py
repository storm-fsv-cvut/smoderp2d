# TODO: not tested yet
import sys
from base import BaseProvider

class ArcGisProvider(BaseProvider):
    import arcpy
    
    def __init__(self):
        # TODO
        self.partial_comp = get_argv(constants.PARAMETER_PARTIAL_COMPUTING)
        sys.argv.append(type_of_computing)

        # ???
        sys.argv.append('#')  # mfda
        sys.argv.append(False)  # extra output
        sys.argv.append('outdata.save')  # in data
        sys.argv.append('full')  # castence nee v arcgis
        sys.argv.append(False)  # debug print
        sys.argv.append('-')               # print times

    def _load_dpre(self):
        # TODO: rewrite
        from smoderp2d.data_preparation import prepare_data
        from smoderp2d.tools.save_load_data import save_data

        boundaryRows, boundaryCols, mat_boundary, rrows, rcols, \
            outletCells, x_coordinate, y_coordinate,\
            NoDataValue, array_points, \
            cols, rows, combinatIndex, delta_t,  \
            mat_pi, mat_ppl, \
            surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, \
            mat_reten, \
            mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
            mat_a,   \
            mat_n,   \
            output, pixel_area, points, poradi,  end_time, spix, state_cell, \
            temp, type_of_computing, vpix, mfda, sr, itera, \
            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = \
            prepare_data(sys.argv)

        # TODO: use dict
        dataList = [
            boundaryRows, boundaryCols, mat_boundary, rrows, rcols,
            outletCells, x_coordinate, y_coordinate,
            NoDataValue, array_points,
            cols, rows, combinatIndex, delta_t,
            mat_pi, mat_ppl,
            surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_reten,
            mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan,
            mat_a,
            mat_n,
            output, pixel_area, points, poradi, end_time, spix, state_cell,
            temp, type_of_computing, vpix, mfda, sr, itera,
            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc]
        
        outoutdat = get_argv(
            os.path.join(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY),
            get_argv(constants.PARAMETER_INDATA)
        )
        save_data(dataList, outoutdat)

    def _load_full(self):
        # TODO: rewrite
        from smoderp2d.data_preparation import prepare_data
        return prepare_data(sys.argv)

    def load(self):
        if self._args.typecomp in ('roff', 'full'):
            # TODO: ?
            logical_argv(constants.PARAMETER_ARCGIS)
            logical_argv(constants.PARAMETER_EXTRA_OUTPUT)
            logical_argv(constants.PARAMETER_MFDA)

            if self._args.typecomp == 'roff':
                data = self._load_roff(
                    get_argv(constants.PARAMETER_INDATA)
                )
            else:
                data = self._load_full()

            self._set_globals(data)
            self._cleanup()

        elif self._args.typecomp == 'dpre':
            self._load_dpre()
        else:
            raise Exception('Unsupported partial computing: {}'.format(
                self._args.typecomp
            ))

        return data
    
    def message(self, line):
        """Print string.

        :param str line: string to be printed
        """
        arcpy.AddMessage(line)
