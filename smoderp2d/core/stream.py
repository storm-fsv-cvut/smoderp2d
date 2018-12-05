from smoderp2d.stream_functions import stream_f
from smoderp2d.core.general import GridGlobals, Globals as Gl
from smoderp2d.providers import Logger

class Reach(object):
    def __init__(self, id_, POINT_X, POINT_Y, POINT_X_1, POINT_Y_1,
                 to_node, length, sklon, smoderp, CISLO, TVAR, B, M, DRSNOST, Q365):

        self.id_ = id_
        self.pointsFrom = [POINT_X, POINT_Y]
        self.pointsTo = [POINT_X_1, POINT_Y_1]
        self.to_node = to_node
        self.length = length
        if sklon < 0:
            Logger.info("Slope in reach part {} indicated minus slope in stream".format(id_))
        self.slope = abs(sklon)
        self.smoderp = smoderp
        self.no = CISLO
        self.shape = TVAR

        self.b = B
        self.m = M
        self.roughness = DRSNOST
        self.Q365 = Q365
        self.V_in_from_field = 0.0
        self.V_in_from_field_cum = 0.0
        self.V_in_from_reach = 0.0
        self.V_out_cum = 0.0   # L^3
        self.V_rest = 0.0
        self.h = 0.0  # jj mozna pocatecni podminka? ikdyz to je asi Q365 co...
        self.h_max = 0.0
        self.timeh_max = 0.0
        self.V_out = 0.0
        self.vs = 0.0
        self.Q_out = 0.0
        self.Q_max = 0.0
        self.timeQ_max = 0.0
        self.V_out_domain = 0.0


        if TVAR == 0:  # obdelnik
            self.outflow_method = stream_f.rectangle
        elif TVAR == 1:  # trapezoid
            self.outflow_method = stream_f.trapezoid
        elif TVAR == 2:  # triangle
            self.outflow_method = stream_f.triangle
        elif TVAR == 3:  # parabola
            self.outflow_method = stream_f.parabola
        else:
            self.outflow_method = stream_f.rectangle


# Documentation for a class.
#
#  More details.

# Bacha na id, je id v shp toku v sestupnem poradi. To musi jinak bude
# chyba ve tvorbe reach
class Stream(object):

    # The constructor.

    def __init__(self):
        super(Stream, self).__init__()
        Logger.info('Stream: ON')
        self.toky = Gl.toky  # tu jsou nactena data z data preparation cca lajna 970

        self.nReaches = len(self.toky[0])

        self.cell_stream = Gl.cell_stream

        self.reach = []

        for i in range(self.nReaches):
            self.reach.append(
                Reach(self.toky[0][i],
                      self.toky[1][i],
                      self.toky[2][i],
                      self.toky[3][i],
                      self.toky[4][i],
                      self.toky[5][i],
                      self.toky[6][i],
                      self.toky[7][i],
                      self.toky[8][i],
                      self.toky[9][i],
                      self.toky[10][i],
                      self.toky[11][i],
                      self.toky[12][i],
                      self.toky[13][i],
                      self.toky[14][i]))
        
        
        self.toky_loc = Gl.toky_loc
        self.mat_tok_reach = Gl.mat_tok_reach

        for i in self.rr:
            for j in self.rc[i]:
                self.arr[i][j].state += self.mat_tok_reach[i][j]

        self.STREAM_RATIO = Gl.STREAM_RATIO

    def reset_inflows(self):
        for id_ in range(self.nReaches):
            self.reach[id_].V_in_from_field = 0

    # Documentation for a reach inflows.
    #  @param id_ starts in 0 not 1000
    def reach_inflows(self, id_, inflows):
        self.reach[id_].V_in_from_field += inflows
        #print inflows, self.reach[id_].V_in_from_field

    def stream_reach_outflow(self, dt):
        for id_ in range(self.nReaches):
            self.reach[id_].outflow_method(self.reach[id_], dt)

    def stream_reach_inflow(self):
        for id_ in range(self.nReaches):
            self.reach[id_].V_in_from_reach = 0
            self.reach[id_].V_out_domain = 0

        for id_ in range(self.nReaches):
            id_to_node = int(self.reach[id_].to_node)
            if id_to_node == -9999:
                self.reach[id_].V_out_domain += self.reach[id_].V_out
            else:
                self.reach[id_to_node].V_in_from_reach += self.reach[id_].V_out

    # jj jeste dodelat ty maxima a kumulativni zbyle
    def stream_cumulative(self, time):
        for id_ in range(self.nReaches):
            self.reach[id_].V_out_cum += self.reach[id_].V_out
            self.reach[
                id_].V_in_from_field_cum += self.reach[
                    id_].V_in_from_field
            if self.reach[id_].Q_out > self.reach[id_].Q_max:
                self.reach[id_].Q_max = self.reach[id_].Q_out
                self.reach[id_].timeQ_max = time
            if self.reach[id_].h > self.reach[id_].h_max:
                self.reach[id_].h_max = self.reach[id_].h
                self.reach[id_].timeh_max = time

    def return_stream_str_vals(self, i, j, sep, dt, extraOut):
        id_ = int(self.arr[i][j].state - 1000)
        # Time;   V_runoff  ;   Q   ;    V_from_field  ;  V_rests_in_stream
        # print id_, self.reach[id_].Q_out, str(self.reach[id_].V_out)
        if not(extraOut):
            line = str(self.reach[id_].h) + sep + str(
                self.reach[id_].Q_out) + sep + str(self.reach[id_].V_out)
        else:
            line = str(self.reach[id_].h) + sep + str(self.reach[id_].V_out) + sep + str(self.reach[id_].Q_out) + sep + \
                str(self.reach[id_].V_in_from_field) + sep + str(
                self.reach[id_].V_rest)
        return line


class StreamPass(object):

    def __init__(self):
        super(StreamPass, self).__init__()
        Logger.info('Stream: OFF')

    def reset_inflows(self):
        pass

    def reach_inflows(self, id_, inflows):
        pass

    def stream_reach_inflow(self):
        pass

    def stream_reach_outflow(self, dt):
        pass

    # jj jeste dodelat ty maxima a kumulativni zbyle
    def stream_cumulative(self, dt):
        pass
