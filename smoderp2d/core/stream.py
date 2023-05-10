import numpy.ma as ma

from smoderp2d.stream_functions import stream_f
from smoderp2d.core.general import GridGlobals, Globals as Gl
from smoderp2d.providers import Logger
from smoderp2d.exceptions import ProviderError

class Reach(object):
    def __init__(self, stream_segment_id,
                 stream_segment_next_down_id, stream_segment_length, stream_segment_inclination,
                 channel_profile, channel_shape_id, channel_shapetype, channel_bottom_width, channel_bank_steepness, channel_bed_roughness, channel_q365):

        self.segment_id = stream_segment_id
        self.next_down_id = stream_segment_next_down_id
        self.length = stream_segment_length
        if stream_segment_inclination < 0:
            Logger.info(
                "Slope in reach part {} indicated minus slope in stream".format(stream_segment_id)
            )
        self.inclination = abs(stream_segment_inclination)
        self.profile = channel_profile
        self.shape_id = channel_shape_id
        self.shapetype = channel_shapetype

        self.b = channel_bottom_width
        self.m = channel_bank_steepness
        self.roughness = channel_bed_roughness
        self.q365 = channel_q365
        self.V_in_from_field = 0.0
        self.V_in_from_field_cum = 0.0
        self.V_in_from_reach = 0.0
        self.V_out_cum = 0.0   # L^3
        self.vol_rest = 0.0
        self.h = 0.0  # jj mozna pocatecni podminka? ikdyz to je asi q365 co...
        self.h_max = 0.0
        self.timeh_max = 0.0
        self.V_out = 0.0
        self.vs = 0.0
        self.Q_out = 0.0
        self.Q_max = 0.0
        self.timeQ_max = 0.0
        self.V_out_domain = 0.0


        if channel_shapetype == 0:  # obdelnik
            self.outflow_method = stream_f.rectangle
        elif channel_shapetype == 1:  # trapezoid
            self.outflow_method = stream_f.trapezoid
        elif channel_shapetype == 2:  # triangle
            self.outflow_method = stream_f.triangle
        elif channel_shapetype == 3:  # parabola
            self.outflow_method = stream_f.parabola
            #ToDO - ve stream_f-py - mame u paraboly napsano, ze nefunguje
        else:
            self.outflow_method = stream_f.rectangle
            #ToDo - zahodit posledni else a misto toho dat hlasku, ze to je mimo rozsah


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
            args = {k:v[i] for k,v in self.streams.items()}
            self.reach[int(self.streams['stream_segment_id'][i])] = Reach(**args)

        self.mat_stream_reach = Gl.mat_stream_reach

        self.state = self.mat_stream_reach

        self.STREAM_RATIO = Gl.STREAM_RATIO

    def reset_inflows(self):
        for r in self.reach.values():
            r.V_in_from_field = 0

    # Documentation for a reach inflows.
    #  @param fid feature id
    def reach_inflows(self, fid, inflows, indices):
        try:
            self.reach[fid].V_in_from_field += ma.where(indices, inflows, 0)
        except KeyError:
            raise ProviderError(
                "Unable to reach inflow. Feature id {} not found in {}".format(
                    fid,
                    ','.join(list(map(lambda x: str(x), self.reach.keys())))
            ))

    def stream_reach_outflow(self, dt):
        for r in self.reach.values():
            r.outflow_method(r, dt)

    def stream_reach_inflow(self):
        for r in self.reach.values():
            r.V_in_from_reach = 0
            r.V_out_domain = 0

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
            if ma.any(r.Q_out > r.Q_max):
                r.Q_max = r.Q_out
                r.timeQ_max = time
            if ma.any(r.h > r.h_max):
                r.h_max = r.h
                r.timeh_max = time

    def return_stream_str_vals(self, i, j, sep, dt, extraOut):
        fid = int(self.state[i, j] - Gl.streams_flow_inc)
        # Time;   V_runoff  ;   Q   ;    V_from_field  ;  V_rests_in_stream
        # print fid, self.reach[fid].Q_out, str(self.reach[fid].V_out)
        r = self.reach[fid]
        if not(extraOut):
            line = '{h}{sep}{q}{sep}{cumvol}'.format(
                h=r.h, q=r.Q_out, cumvol=r.V_out_cum, sep=sep
            )
        else:
            line = '{h}{sep}{v}{sep}{q}{sep}{vi}{sep}{vo}'.format(
                h=r.h, v=r.V_out, q=r.Q_out, vi=r.V_in_from_field,
                vo=r.vol_rest, sep=sep
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
