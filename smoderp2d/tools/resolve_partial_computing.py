# @package smoderp2d.tools.resolve_partial_computing
#
#  smodepr2d can be run in several modes
#  full mode, only data preparation mode and only runoff mode
#  the handing of those modes is platform dependent
#  there there two methods get_indata_lin for linux machine
#  and get_indata_win for for windows machine are defined in the package
#  the functionality of is the same for both platforms


import os
import sys


import smoderp2d.constants as constants
from smoderp2d.tools.tools import get_argv
from smoderp2d.tools.tools import set_argv
from smoderp2d.tools.tools import prt_sys_argv
from smoderp2d.tools.tools import int_comp_type
from smoderp2d.tools.tools import logical_argv
from smoderp2d.exceptions import RainfallFileMissing

#
# from inspect import currentframe, getframeinfo
# frameinfo = getframeinfo(currentframe())
#


def get_indata_lin(tc, args):

    if tc == 'roff':

        import ConfigParser
        import smoderp2d.tools.save_load_data as sld
        import smoderp2d.processes.rainfall as rainfall

        # import  smoderp2d.tools.save_load_data_nopickle    as sld   #
        # preparated
        Config = ConfigParser.ConfigParser()
        Config.read(args.indata)
        indata = Config.get('Other', 'indata')

        # the data are loared from a pickle file
        boundaryRows, boundaryCols, \
            mat_boundary, rrows, rcols, outletCells, \
            x_coordinate, y_coordinate,\
            NoDataValue, array_points, \
            cols, rows, combinatIndex, delta_t,  \
            mat_pi, mat_ppl, \
            surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_reten,\
            mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
            mat_a,   \
            mat_n,   \
            output, pixel_area, points, poradi,  end_time, spix, state_cell, \
            temp, type_of_computing, vpix, mfda, sr, itera, \
            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = sld.load_data(
                indata)

        # some variables configs can be changes after loading from pickle.dump
        # such as
        #  end time of simulation
        if Config.get('time', 'endtime') != '-':
            end_time = Config.getfloat('time', 'endtime') * 60.0

        #  time of flow algorithm
        if Config.get('Other', 'mfda') != '-':
            mfda = Config.getboolean('Other', 'mfda')

        #  type of computing:
        #    0 sheet only,
        #    1 sheet and rill flow,
        #    2 sheet and subsurface flow,
        #    3 sheet, rill and reach flow
        if Config.get('Other', 'typecomp') != '-':
            type_of_computing = Config.get('Other', 'typecomp')

        #  output directory is always set
        output = Config.get('Other', 'outdir')

        #  rainfall data can be saved
        if (not(os.path.isfile(Config.get('srazka', 'file')))):
            raise RainfallFileMissing(Config.get('srazka', 'file'))

        if Config.get('srazka', 'file') != '-':
            sr, itera = rainfall.load_precipitation(
                Config.get('srazka', 'file'))

        # some configs are not in pickle.dump
        extraOut = Config.getboolean('Other', 'extraout')
        #  rainfall data can be saved
        prttimes = Config.get('Other', 'printtimes')

        maxdt = Config.getfloat('time', 'maxdt')
        if os.path.exists(output):
            import shutil
            shutil.rmtree(output)
        if not os.path.exists(output):
            os.makedirs(output)
            # os.makedirs(output+os.sep+'prubeh')

        return boundaryRows, boundaryCols, \
            mat_boundary, rrows, rcols, outletCells, \
            x_coordinate, y_coordinate,\
            NoDataValue, array_points, \
            cols, rows, combinatIndex, delta_t,  \
            mat_pi, mat_ppl, \
            surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_reten,\
            mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
            mat_a,   \
            mat_n,   \
            output, pixel_area, points, poradi,  end_time, spix, state_cell, \
            temp, type_of_computing, vpix, mfda, sr, itera, \
            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc, extraOut, prttimes, maxdt

    else:
        print "on a linux machine work only roff mode"
        return None


def get_indata_win(tc, args):

    # full computation
    #      data_preparation + runoff model
    if tc == 'full':
        from smoderp2d.data_preparation import prepare_data

        return prepare_data(sys.argv)

    # only data_preparation
    #      data are saved in dump, can be stored and loaded later on
    elif tc == 'dpre':

        from smoderp2d.data_preparation import prepare_data
        import smoderp2d.tools.save_load_data as sld

        boundaryRows, boundaryCols, mat_boundary, rrows, rcols, outletCells, x_coordinate, y_coordinate,\
            NoDataValue, array_points, \
            cols, rows, combinatIndex, delta_t,  \
            mat_pi, mat_ppl, \
            surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_reten, \
            mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
            mat_a,   \
            mat_n,   \
            output, pixel_area, points, poradi,  end_time, spix, state_cell, \
            temp, type_of_computing, vpix, mfda, sr, itera, \
            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = prepare_data(
                sys.argv)

        # import  smoderp2d.tools.save_load_data_nopickle    as sld   #
        # preparate

        dataList = [
            boundaryRows, boundaryCols, mat_boundary, rrows, rcols, outletCells, x_coordinate, y_coordinate,
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
            constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY) + os.sep + get_argv(
                constants.PARAMETER_INDATA)
        sld.save_data(dataList, outoutdat)
        # sld.save(dataList,get_argv(constants.PARAMETER_INDATA))    #
        # preparated

        print "Data praparation finished\n\t Data saved in ", outoutdat
        return False

        """ puvocne ty bylo sys.exit coz ale neni dobre pokud bezi skript v nadrazenem programu
    sys.exit pak muze shodit i ten. Taze se tu vrati False az do mainu a tam se nespusti
    runoff protoze tu chci jen data praparation"""

    # only runoff model
    #       data can be restored from previously prepared *.save file
    #
    elif tc == 'roff':

        logical_argv(constants.PARAMETER_ARCGIS)
        logical_argv(constants.PARAMETER_EXTRA_OUTPUT)
        logical_argv(constants.PARAMETER_MFDA)
        indata = get_argv(constants.PARAMETER_INDATA)

        import smoderp2d.tools.save_load_data as sld
        import smoderp2d.processes.rainfall as rainfall
        # import  smoderp2d.tools.save_load_data_nopickle    as sld   #
        # preparated

        # the data are loared from a pickle file
        boundaryRows, boundaryCols, \
            mat_boundary, rrows, rcols, outletCells, \
            x_coordinate, y_coordinate,\
            NoDataValue, array_points, \
            cols, rows, combinatIndex, delta_t,  \
            mat_pi, mat_ppl, \
            surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_reten,\
            mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
            mat_a,   \
            mat_n,   \
            output, pixel_area, points, poradi,  end_time, spix, state_cell, \
            temp, type_of_computing, vpix, mfda, sr, itera, \
            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = sld.load_data(
                indata)

        # some variables configs can be changes after loading from pickle.dump
        # such as
        #  end time of simulation
        if Config.get('time', 'endtime') != '-':
            end_time = Config.getfloat('time', 'endtime') * 60.0

        #  time of flow algorithm
        if Config.get('Other', 'mfda') != '-':
            mfda = Config.getboolean('Other', 'mfda')

        #  type of computing:
        #    0 sheet only,
        #    1 sheet and rill flow,
        #    2 sheet and subsurface flow,
        #    3 sheet, rill and reach flow
        if Config.get('Other', 'typecomp') != '-':
            type_of_computing = Config.get('Other', 'typecomp')

        #  output directory is always set
        output = Config.get('Other', 'outdir')

        #  rainfall data can be saved
        if Config.get('srazka', 'file') != '-':
            sr, itera = rainfall.load_precipitation(
                Config.get('srazka', 'file'))

        # some configs are not in pickle.dump
        extraOut = Config.getboolean('Other', 'extraout')
        #  rainfall data can be saved
        prttimes = Config.get('Other', 'printtimes')

        maxdt = Config.getfloat('time', 'maxdt')
        if os.path.exists(output):
            import shutil
            shutil.rmtree(output)
        if not os.path.exists(output):
            os.makedirs(output)
            # os.makedirs(output+os.sep+'prubeh')

        return boundaryRows, boundaryCols, \
            mat_boundary, rrows, rcols, outletCells, \
            x_coordinate, y_coordinate,\
            NoDataValue, array_points, \
            cols, rows, combinatIndex, delta_t,  \
            mat_pi, mat_ppl, \
            surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_reten,\
            mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
            mat_a,   \
            mat_n,   \
            output, pixel_area, points, poradi,  end_time, spix, state_cell, \
            temp, type_of_computing, vpix, mfda, sr, itera, \
            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc, extraOut, prttimes, maxdt
