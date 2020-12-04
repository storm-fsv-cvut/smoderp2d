import os

from smoderp2d.core.general import GridGlobals, Globals
from smoderp2d.providers import Logger

SEP = ';'
os.linesep='\n'

class Hydrographs:
    def __init__(self, item='core'):
        points = Globals.get_array_points()
        ipi = points.shape[0]
        jpj = 5
        point_int = [[0] * jpj for i in range(ipi)]

        rr, rc = GridGlobals.get_region_dim()
        pixel_area = GridGlobals.get_pixel_area()

        self.inSurface = []
        self.inStream = []

        for ip in range(ipi):
            for jp in [0, 1, 2]:
                point_int[ip][jp] = int(points[ip][jp])

        for ip in range(ipi):
            for jp in [3, 4]:
                point_int[ip][jp] = points[ip][jp]

        # tento cylkus meze budy, ktere jsou
        # v i,j cylku o jednu vedle rrows a rcols
        outsideDomain = False
        del_ = []
        for ip in range(ipi):
            l = point_int[ip][1]
            m = point_int[ip][2]
            for ipp in rr:
                if l == ipp:
                    for jpp in rc[ipp]:
                        if m == jpp:
                            outsideDomain = True
            if not(outsideDomain):
                del_.append(ip)
            outsideDomain = False
        point_int = [i for j, i in enumerate(point_int) if j not in del_]
        ipi -= len(del_)

        counter = 0

        # mat_stream_seg is alway presented if stream == True
        # if (mat_stream_seg != None) and (stream == True):
        if Globals.isStream:
            for ip in range(ipi):
                l = point_int[ip][1]
                m = point_int[ip][2]

                if Globals.get_mat_stream_reach(l, m) >= 1000:
                    self.inStream.append(counter)
                    counter += 1
                else:
                    self.inSurface.append(counter)
                    counter += 1
        else:
            self.inSurface = [i for i in range(ipi)]

        self.inStream.append(-99)
        self.inSurface.append(-99)

        self.n = ipi
        self.point_int = point_int
        self.subflow = Globals.subflow
        self.rill = Globals.isRill
        self.stream = Globals.isStream
        self.pixel_area = pixel_area

        iStream = 0
        iSurface = 0

        self.header = []

        for i in range(self.n):
            header = '# Hydrograph at the point with coordinates: {} {}{}'.format(
                self.point_int[i][3], self.point_int[i][4], os.linesep)
            header += '# A pixel size is [m2]: {}{}'.format(
                    GridGlobals.pixel_area,os.linesep)
            if i == self.inStream[iStream]:

                if not Globals.extraOut:
                    header += 'time[s]{sep}deltaTime[s]{sep}rainfall[m]'\
                              '{sep}reachWaterLevel[m]{sep}reachFlow[m3/s]'\
                              '{sep}reachVolRunoff[m3]'.format(sep=SEP)
                else:
                    header += 'time[s]{sep}deltaTime[s]{sep}Rainfall[m]'\
                              '{sep}Waterlevel[m]{sep}V_runoff[m3]{sep}Q[m3/s]'\
                              '{sep}V_from_field[m3]{sep}V_rests_in_stream[m3]'.format(sep=SEP)
                header += os.linesep
                iStream += 1
                self.header.append(header)

            elif i == self.inSurface[iSurface]:

                if not Globals.extraOut:
                    header += 'time[s]{sep}deltaTime[s]{sep}rainfall[m]'\
                              '{sep}totalWaterLevel[m]{sep}surfaceFlow[m3/s]'\
                              '{sep}surfaceVolRunoff[m3]'\
                              '{linesep}'.format(sep=SEP, linesep = os.linesep)
                else:
                    header += 'time[s]{sep}deltaTime[s]{sep}Rainfall[m]{sep}'\
                              'Water_level_[m]{sep}Sheet_Flow[m3/s]{sep}Sheet_V_runoff[m3]{sep}'\
                              'Sheet_flow_velocity[m/s]{sep}'\
                              'Sheet_V_rest[m3]{sep}Infiltration[m]{sep}Surface_retetion[m]{sep}'\
                              'State{sep}V_inflow[m3]{sep}WlevelTotal[m]'.format(sep=SEP)

                    if Globals.isRill:
                        header += '{sep}WlevelRill[m]{sep}Rill_width[m]'\
                                  '{sep}Rill_flow[m3/s]{sep}Rill_V_runoff[m3]'\
                                  '{sep}Rill_flow_velocity[m/s]'\
                                  '{sep}Rill_V_rest{sep}Surface_Flow[m3/s]'\
                                  '{sep}Surface_V_runoff[m3]'.format(sep=SEP)
                    header += '{sep}SurfaceBil[m3]'.format(sep=SEP)
                    if Globals.subflow:
                        header += '{sep}Sub_Water_level_[m]{sep}Sub_Flow_[m3/s]'\
                        '{sep}Sub_V_runoff[m3]{sep}Sub_V_rest[m3]'\
                        '{sep}Percolation[]{sep}exfiltration[]'.format(sep=SEP)
                    if Globals.extraOut:
                        header += '{sep}V_to_rill.m3.{sep}ratio{sep}courant'\
                        '{sep}courantrill{sep}iter'.format(sep=SEP)
                    header += os.linesep

                iSurface += 1
                self.header.append(header)

        self.files = []
        for i in range(self.n):
            filename = 'point{}.csv'.format(
                str(self.point_int[i][0]).zfill(3)
            )
            fd = open(os.path.join(Globals.get_outdir(), filename), 'w')
            fd.writelines(self.header[i])
            self.files.append(fd)

        del self.inStream[-1]
        del self.inSurface[-1]

        Logger.info("Hydrographs files has been created...")

    def write_hydrographs_record(self, i, j, fc, courant, dt, surface, subsurface,
                                 currRain, inStream=False, sep=SEP):
        ratio = fc.ratio
        total_time = fc.total_time + dt
        iter_ = fc.iter_

        courantMost = courant.cour_most
        courantRill = courant.cour_most_rill

        if inStream:
            for ip in self.inStream:
                l = self.point_int[ip][1]
                m = self.point_int[ip][2]
                self.files[ip].writelines(
                    '{0:.4e}{sep}{1:.4e}{sep}{2:.4e}{sep}{3}{linesep}'.format(
                    total_time, dt, currRain,
                    surface.return_stream_str_vals(l, m, SEP, dt, Globals.extraOut),
                    sep=sep, linesep=os.linesep
                ))
        else:
            for ip in self.inSurface:
                l = self.point_int[ip][1]
                m = self.point_int[ip][2]
                if i == l and j == m:
                    linebil = surface.return_str_vals(l, m, SEP, dt, Globals.extraOut)
                    line = '{0:.4e}{sep}{1:.4e}{sep}{2:.4e}{sep}{3}'.format(
                        total_time, dt, currRain,
                        linebil[0],
                        sep=sep
                    )
                    # line += subsurface.return_str_vals(l,m,SEP,dt) + sep   #
                    # prozatim
                    if Globals.extraOut:
                        line += '{sep}{0:.4e}{sep}{0:.4e}{sep}{2:.4e}{sep}{3:.4e}{sep}'\
                        '{4:.4e}{sep}{5:.4e}'.format(
                            linebil[1], surface.arr[l][m].vol_to_rill,
                            ratio, courantMost, courantRill, iter_,
                            sep=sep)
                    line += os.linesep
                    self.files[ip].writelines(line)

    def _output_path(self, output, directory='core'):
        dir_name = os.path.join(
            Globals.outdir,
            directory
            )

        if not os.path.exists(dir_name):
           os.makedirs(dir_name)

        return os.path.join(
            dir_name,
            output
        )

    def __del__(self):
        for fd in self.files:
            Logger.debug('Hydrographs file "{}" closed'.format(fd.name))
            fd.close()

class HydrographsPass:
    def write_hydrographs_record(self, i, j, fc, courant, dt, surface, subsurface,
                                 currRain, inStream=False, sep=SEP):
        pass

    def _output_path(self, output, directory='core'):
        pass
