from smoderp2d.processes.infiltration import BaseInfiltration
class RichardsInfiltration(BaseInfiltration):

    def __init__(self, combinatIndex):

        self._combinat_index = combinatIndex

    def precalc(self, dt, total_time):
        raise NotImplemented("Not implemented for Richards infiltration")

    def current_infiltration(self, soil, bil):
        raise NotImplemented("Not implemented for Richards infiltration")