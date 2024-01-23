import numpy as np
import numpy.ma as ma

from smoderp2d.stream_functions import stream_f
from smoderp2d.core.general import GridGlobals, Globals as Gl
from smoderp2d.providers import Logger
from smoderp2d.exceptions import ProviderError


class Reach(object):
    def __init__(self, stream_segment_id, stream_segment_next_down_id,
                 stream_segment_length, stream_segment_inclination,
                 channel_shape_id, channel_shapetype, channel_bottom_width,
                 channel_bank_steepness, channel_bed_roughness, channel_q365):

        self.segment_id = stream_segment_id
        self.next_down_id = stream_segment_next_down_id
        self.length = stream_segment_length
        if stream_segment_inclination < 0:
            Logger.info(
                "Slope in reach part {} indicated minus slope in "
                "stream".format(stream_segment_id)
            )
        self.inclination = abs(stream_segment_inclination)
        self.shape_id = channel_shape_id
        self.shapetype = channel_shapetype

        self.b = channel_bottom_width
        self.m = channel_bank_steepness
        self.roughness = channel_bed_roughness
        self.q365 = channel_q365
        self.V_in_from_field = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.V_in_from_field_cum = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.V_in_from_reach = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.V_out_cum = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )   # L^3
        self.vol_rest = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.h = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )  # jj mozna pocatecni podminka? ikdyz to je asi q365 co...
        self.h_max = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.timeh_max = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.V_out = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vs = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.Q_out = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.Q_max = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.timeQ_max = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.V_out_domain = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )

        if channel_shapetype == 0:  # obdelnik
            self.outflow_method = stream_f.rectangle
        elif channel_shapetype == 1:  # trapezoid
            self.outflow_method = stream_f.trapezoid
        elif channel_shapetype == 2:  # triangle
            self.outflow_method = stream_f.triangle
        elif channel_shapetype == 3:  # parabola
            self.outflow_method = stream_f.parabola
            # ToDO - ve stream_f-py - mame u paraboly napsano, ze nefunguje
        else:
            self.outflow_method = stream_f.rectangle
            # ToDo - zahodit posledni else a misto toho dat hlasku, ze to
            #        je mimo rozsah


# Documentation for a class.
#
#  More details.

# Bacha na id, je id v shp toku v sestupnem poradi. To musi jinak bude
# chyba ve tvorbe reach
class Stream(object):

    def __init__(self):
        super(Stream, self).__init__()
        Logger.info('Stream: ON')
        self.streams = Gl.streams

        self.nReaches = len(self.streams['stream_segment_id'])

        self.cell_stream = Gl.cell_stream

        self.reach = {}

        for i in range(self.nReaches):
            args = {k: v[i] for k, v in self.streams.items()}
            self.reach[self.streams['stream_segment_id'][i]] = Reach(**args)

        self.mat_stream_reach = Gl.mat_stream_reach

        self.arr.state = ma.where(
            self.mat_stream_reach > Gl.streams_flow_inc,
            self.mat_stream_reach,
            0
        )

        self.STREAM_RATIO = Gl.STREAM_RATIO

    def reset_inflows(self):
        for r in self.reach.values():
            r.V_in_from_field = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
            )

    # Documentation for a reach inflows.
    #  @param fid feature id
    def reach_inflows(self, fid, inflows, indices):
        try:
            # TODO: Would be nice to avoid the loop
            for fid_cur in self.reach.keys():
                self.reach[fid_cur].V_in_from_field += ma.sum(
                    ma.where(
                        ma.logical_and(indices, fid == fid_cur), inflows, 0
                    )
                )
        except KeyError:
            raise ProviderError(
                "Unable to reach inflow. Feature id {} not found in {}".format(
                    fid,
                    ','.join(list(map(lambda x: str(x), self.reach.keys())))
                )
            )

    def stream_reach_outflow(self, dt):
        for r in self.reach.values():
            r.outflow_method(r, dt)

    def stream_reach_inflow(self):
        for r in self.reach.values():
            r.V_in_from_reach = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
            )
            r.V_out_domain = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
            )

        for r in self.reach.values():
            fid_to_node = int(r.next_down_id)
            if fid_to_node == Gl.streamsNextDownIdNoSegment:
                r.V_out_domain += r.V_out
            else:
                self.reach[fid_to_node].V_in_from_reach += r.V_out

    # jj jeste dodelat ty maxima a kumulativni zbyle
    def stream_cumulative(self, time):
        for r in self.reach.values():
            r.V_out_cum += r.V_out
            r.V_in_from_field_cum += r.V_in_from_field

            r.timeQ_max = ma.where(
                r.Q_out > r.Q_max,
                time,
                r.timeQ_max
            )
            r.Q_max = ma.maximum(r.Q_out, r.Q_max)
            r.timeh_max = ma.where(
                r.h > r.h_max,
                time,
                r.timeh_max
            )
            r.h_max = ma.maximum(r.h, r.h_max)

    def return_stream_str_vals(self, i, j, sep, extraOut):
        fid = int(self.arr.state[i, j] - Gl.streams_flow_inc)
        # Time;   V_runoff  ;   Q   ;    V_from_field  ;  V_rests_in_stream
        r = self.reach[fid]
        if not extraOut:
            line = '{h:.4e}{sep}{q:.4e}{sep}{cumvol:.4e}'.format(
                h=r.h[i, j], q=r.Q_out[i, j], cumvol=r.V_out_cum[i, j], sep=sep
            )
        else:
            line = '{h:.4e}{sep}{v:.4e}{sep}{q:.4e}{sep}{vi:.4e}{sep}' \
                   '{vo:.4e}'.format(
                h=r.h[i, j], v=r.V_out[i, j], q=r.Q_out[i, j],
                vi=r.V_in_from_field[i, j], vo=r.vol_rest[i, j], sep=sep
            )

        return line


class StreamPass(object):

    def __init__(self):
        super(StreamPass, self).__init__()
        self.reach = None
        Logger.info('Stream: OFF')

    def reset_inflows(self):
        pass

    def reach_inflows(self, fid, inflows, indices):
        pass

    def stream_reach_inflow(self):
        pass

    def stream_reach_outflow(self, dt):
        pass

    # jj jeste dodelat ty maxima a kumulativni zbyle
    def stream_cumulative(self, dt):
        pass
