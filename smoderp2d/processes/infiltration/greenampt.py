from smoderp2d.processes.infiltration import BaseInfiltration
class GreenAmptInfiltration(BaseInfiltration):

    def __init__(self, combinatIndex):

        self._combinat_index = combinatIndex
        #TODO include into inputs, should be changeable
        self._psi = -10/100 # soil water potential at the wetting front
        #TODO include into inputs, should be changeable
        self._d_theta = 0.4 # theta difference
        
        
    

    def precalc(self, dt, total_time):
        raise NotImplemented("Not implemented for Green Ampt infiltration")

    def current_infiltration(self, soil, bil):
        raise NotImplemented("Not implemented for Green Ampt infiltration")