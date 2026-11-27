import os

from smoderp2d.core.general import GridGlobals, Globals
from smoderp2d.providers import Logger

SEP = ';'
os.linesep = '\n'


class Hydrographs:
    def __init__(self):
        points = Globals.get_array_points()
        ipi = points.shape[0]
        jpj = 5
        point_int = [[0] * jpj for _ in range(ipi)]

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
            if not outsideDomain:
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
                mat_stream_reach = Globals.get_mat_stream_reach(l, m)

                if mat_stream_reach >= Globals.streams_flow_inc:
                    self.inStream.append(counter)
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
            header = '# Hydrograph at the point with coordinates: ' \
                     '{:.8} {:.8}{}'.format(
                float(self.point_int[i][3]), float(self.point_int[i][4]),
                os.linesep
            )
            header += '# A pixel size is [m2]: {}{}'.format(
                    GridGlobals.pixel_area, os.linesep
            )
            if i == self.inStream[iStream]:

                if not Globals.extraOut:
                    header += 'time[s]{sep}deltaTime[s]{sep}rainfall[m]'\
                              '{sep}reachWaterLevel[m]{sep}reachFlow[m3/s]'\
                              '{sep}cumReachVolRunoff[m3]'.format(sep=SEP)
                else:
                    header += 'time[s]{sep}deltaTime[s]{sep}rainfall[m]'\
                              '{sep}waterlevel[m]{sep}vRunoff[m3]{sep}q[m3/s]'\
                              '{sep}vFromField[m3]{sep}' \
                              'vRestsInStream[m3]'.format(sep=SEP)
                header += os.linesep
                iStream += 1
                self.header.append(header)

            elif i == self.inSurface[iSurface]:

                if not Globals.extraOut:
                    header += 'time[s]{sep}rainfall[m]'\
                              '{sep}totalWaterLevel[m]{sep}surfaceFlow[m3/s]'\
                              '{sep}cumSurfaceVolRunoff[m3]'\
                              '{linesep}'.format(sep=SEP, linesep=os.linesep)
                else:
                    header += 'time[s]{sep}deltaTime[s]{sep}rainfall[m]{sep}'\
                              'waterLevel[m]{sep}sheetFlow[m3/s]{sep}' \
                              'sheetVRunoff[m3]{sep}sheetFlowVelocity[m/s]' \
                              '{sep}sheetVRest[m3]{sep}infiltration[m]{sep}' \
                              'surfaceRetetion[m]{sep}state{sep}vInflow[m3]' \
                              '{sep}wLevelTotal[m]'.format(sep=SEP)

                    if Globals.isRill:
                        header += '{sep}wLevelRill[m]{sep}rillWidth[m]'\
                                  '{sep}rillFlow[m3/s]{sep}rillVRunoff[m3]'\
                                  '{sep}rillFlowVelocity[m/s]'\
                                  '{sep}rillVRest{sep}surfaceFlow[m3/s]'\
                                  '{sep}surfaceVRunoff[m3]'.format(sep=SEP)
                    header += '{sep}surfaceBil[m3]'.format(sep=SEP)
                    if Globals.subflow:
                        header += '{sep}subWaterLevel[m]{sep}subFlow[m3/s]'\
                                  '{sep}subVRunoff[m3]{sep}subVRest[m3]'\
                                  '{sep}percolation[]{sep}' \
                                  'exfiltration[]'.format(sep=SEP)
                    if Globals.extraOut:
                        header += '{sep}vToRill[m3]{sep}courant'\
                                  '{sep}courantRill{sep}iter'.format(sep=SEP)
                    header += os.linesep

                iSurface += 1
                self.header.append(header)

        self.files = []
        target_dir = os.path.join(Globals.get_outdir(), 'control_point')
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        for i in range(self.n):
            filename = 'point{}.csv'.format(
                str(self.point_int[i][0]).zfill(3)
            )
            fd = open(os.path.join(target_dir, filename), 'w')
            fd.writelines(self.header[i])
            self.files.append(fd)

        del self.inStream[-1]
        del self.inSurface[-1]

        Logger.info("Hydrographs files has been created...")

    def write_hydrographs_record(self, i, j, fc, courant, dt, surface,
            subsurface, cumulative, currRain, inStream=False, sep=SEP):

        total_time = fc.total_time + dt
        iter_ = fc.iter_

        # the hydrography is recorded only
        # at the top of each minute
        # the function ends here ohterwise
        if not Globals.extraOut:
            time_minutes = (total_time.max())/60.
            if time_minutes - int(time_minutes) != 0:
                return

        courantMost = courant.cour_most
        courantRill = courant.cour_most_rill

        if inStream:
            for ip in self.inStream:
                l = self.point_int[ip][1]
                m = self.point_int[ip][2]
                self.files[ip].writelines(
                    '{0:.4e}{sep}{1:.4e}{sep}{2:.4e}{sep}{3}{linesep}'.format(
                        total_time, dt, currRain[l, m],
                        surface.return_stream_str_vals(
                            l, m, SEP, Globals.extraOut
                        ),
                        sep=sep, linesep=os.linesep
                    )
                )
        else:
            for ip in self.inSurface:
                l = self.point_int[ip][1]
                m = self.point_int[ip][2]

                if i is not None and j is not None:
                    if i != l or j != m:
                        continue

                linebil = surface.return_str_vals(
                    l, m, SEP, dt, Globals.extraOut
                )
                cumulativelines = cumulative.return_str_val(l, m)
                line = '{0:.4e}{sep}{1}{sep}{2}{sep}{3}'.format(
                    total_time, cumulativelines[0],
                    linebil[0], cumulativelines[1],
                    sep=sep
                )
                if Globals.extraOut:
                    line = '{0:.4e}{sep}{1:.4e}{sep}{2:.4e}'\
                           '{sep}{3}{sep}{4:.4e}'.format(
                        total_time, dt, currRain[l, m],
                        linebil[0], linebil[1], sep=sep
                    )
                if Globals.subflow:
                    subline = subsurface.return_str_vals(l,m,SEP,dt) + sep 
                    line += subline
                if Globals.extraOut:
                    line += '{sep}{0:.4e}'\
                            '{sep}{1:.4e}{sep}{2:.4e}{sep}' \
                            '{3:.4e}'.format(
                        surface.arr.vol_to_rill[l, m],
                        courantMost, courantRill, iter_, sep=sep
                    )
                line += os.linesep
                self.files[ip].writelines(line)

    def __del__(self):
        for fd in self.files:
            Logger.debug('Hydrographs file "{}" closed'.format(fd.name))
            fd.close()


class HydrographsPass:
    def write_hydrographs_record(self, i, j, fc, courant, dt, surface,
            subsurface, currRain, inStream=False, sep=SEP):
        pass
