import numpy as np
import numpy.ma as ma
from smoderp2d.core.general import Globals, GridGlobals
# from smoderp2d.exceptions import NegativeWaterLevel

# set error level of numpy float underflow only to warning instead of errors
np.seterr(under='warn')


# base infiltration is philips infiltration
class SingleSoilBI(object):
    """Philip infiltration for a single soil type."""

    def __init__(self, ks, s):
        """Store the soil type parameters.

        :param ks: saturated hydraulic conductivity
        :param s: sorptivity
        """
        # saturated hydraulic conductivity
        self._ks = ks
        # sorptivity
        self._s = s
        # only global variable
        # stores the infiltration height
        # for a given time step
        self.infiltration = 0

    def philip(self, deltaT, totalT):
        """Philip's formula.

        The potential infiltration in the time step is computed as
        a difference of the cumulative infiltration at the end and at the
        beginning of the time step.

        :param deltaT: time step
        :param totalT: time since the beginning of the infiltration
        """
        NoDataValue = GridGlobals.get_no_data()
        k = self._ks
        s = self._s

        if k and s == NoDataValue:
            self.infiltration = NoDataValue
        else:
            infiltration1 = ma.where(
                totalT == 0,
                s * 0.0000001 ** 0.5 + k * 0.0000001,
                s * totalT ** 0.5 + k * totalT
            )
            infiltration2 = s * (totalT + deltaT)**0.5 + k * (totalT + deltaT)

            self.infiltration = infiltration2 - infiltration1


class BaseInfiltration(object):
    """Base infiltration (Philip infiltration).

    Other infiltration types inherit from this class and define their own
    precalculation of the potential infiltration for each soil type.
    """

    def __init__(self, soils_data):
        """Make instances of SingleSoilBI for each soil type.

        :param soils_data: combinatIndex in the smoderp2d code, i.e. list of
            [soil type id, ks, s, infiltration]; the soil type id is equal to
            the index in the list
        """
        self._n = len(soils_data)
        self._soil = []
        for i in range(self._n):
            self._soil.append(SingleSoilBI(
                ks=soils_data[i][1], s=soils_data[i][2]))

    def precalc(self, dt, total_time, cprec):
        """Precalculate potential infiltration for each soil type.

        The precalculated value is stored in the infiltration attribute of
        the single soil instances.

        :param dt: time step
        :param total_time: time since the beginning of the infiltration
        :param cprec: current precipitation height (not used in Philip)
        """
        for i in range(self._n):
            self._soil[i].philip(dt, total_time)

    def current_infiltration(self, soil_type, bil):
        """Return the actual infiltrated water height.

        The potential infiltration of each soil type is limited by the
        current water level.

        :param soil_type: array of soil types in the cells
        :param bil: array of current water levels
        :return: tuple of water level reduced by the infiltration (in the
            implicit computation the water level is returned unchanged) and
            the infiltration
        """
        infiltration = self._soil[0].infiltration
        for soil_id in range(self._n):
            soil_infiltration = self._soil[soil_id].infiltration
            # if ma.all(bil < 0):
            #     raise NegativeWaterLevel()

            infilt_bil_cond = soil_infiltration > bil

            if Globals.computationType == 'explicit':
                infiltration = ma.where(
                    soil_type == soil_id,
                    ma.where(infilt_bil_cond, bil, soil_infiltration),
                    infiltration
                )

                bil = ma.where(
                    soil_type == soil_id,
                    ma.where(infilt_bil_cond, 0, bil - soil_infiltration),
                    bil
                )
            else:
                infiltration = ma.where(
                    soil_type == soil_id,
                    ma.where(infilt_bil_cond, bil, soil_infiltration),
                    infiltration
                )

        return bil, infiltration
