from smoderp2d.stream_functions import stream_f
from smoderp2d.core.general import GridGlobals, Globals as Gl
from smoderp2d.providers import Logger
from smoderp2d.exceptions import ProviderError

class Reach(object):
    def __init__(self, fid, point_x, point_y, point_x_1, point_y_1,
                 to_node, length, slope, smoderp, number, shapetype, b, m, roughness, q365):

        self.fid = fid
        self.pointsFrom = [point_x, point_y]
        self.pointsTo = [point_x_1, point_y_1]
        self.to_node = to_node
        self.length = length
        if slope < 0:
            Logger.info(
                "Slope in reach part {} indicated minus slope in stream".format(fid
                ))
        self.slope = abs(slope)
        self.smoderp = smoderp
        self.no = number
        self.shapetype = shapetype

        self.b = b
        self.m = m
        self.roughness = roughness
        self.q365 = q365
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


        if shapetype == 0:  # obdelnik
            self.outflow_method = stream_f.rectangle
        elif shapetype == 1:  # trapezoid
            self.outflow_method = stream_f.trapezoid
        elif shapetype == 2:  # triangle
            self.outflow_method = stream_f.triangle
        elif shapetype == 3:  # parabola
            self.outflow_method = stream_f.parabola
        else:
            self.outflow_method = stream_f.rectangle


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

        self.nReaches = len(self.streams['fid'])

        self.cell_stream = Gl.cell_stream

        self.reach = {}

        for i in range(self.nReaches):
            args = {k:v[i] for k,v in self.streams.items()}
            self.reach[int(self.streams['fid'][i])] = Reach(**args)

        self.streams_loc = Gl.streams_loc
        self.mat_stream_reach = Gl.mat_stream_reach

        for i in self.rr:
            for j in self.rc[i]:
                self.arr[i][j].state = self.mat_stream_reach[i][j]

        self.STREAM_RATIO = Gl.STREAM_RATIO

    def reset_inflows(self):
        for r in self.reach.values():
            r.V_in_from_field = 0

    # Documentation for a reach inflows.
    #  @param fid feature id
    def reach_inflows(self, fid, inflows):
        try:
            self.reach[fid].V_in_from_field += inflows
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
            fid_to_node = int(r.to_node)
            if fid_to_node == -9999:
                r.V_out_domain += r.V_out
            else:
                self.reach[fid_to_node].V_in_from_reach += r.V_out

    # jj jeste dodelat ty maxima a kumulativni zbyle
    def stream_cumulative(self, time):
        for r in self.reach.values():
            r.V_out_cum += r.V_out
            r.V_in_from_field_cum += r.V_in_from_field
            if r.Q_out > r.Q_max:
                r.Q_max = r.Q_out
                r.timeQ_max = time
            if r.h > r.h_max:
                r.h_max = r.h
                r.timeh_max = time

    def return_stream_str_vals(self, i, j, sep, dt, extraOut):
        fid = int(self.arr[i][j].state - Gl.streams_flow_inc)
        # Time;   V_runoff  ;   Q   ;    V_from_field  ;  V_rests_in_stream
        # print fid, self.reach[fid].Q_out, str(self.reach[fid].V_out)
        r = self.reach[fid]
        if not(extraOut):
            line = '{h}{sep}{q}{sep}{v}'.format(
                h=r.h, q=r.Q_out, v=r.V_out, sep=sep
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

    def reach_inflows(self, fid, inflows):
        pass

    def stream_reach_inflow(self):
        pass

    def stream_reach_outflow(self, dt):
        pass

    # jj jeste dodelat ty maxima a kumulativni zbyle
    def stream_cumulative(self, dt):
        pass
