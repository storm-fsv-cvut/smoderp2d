from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataBase

class PrepareData(PrepareDataBase):
    def __init__(self):
        os.environ['GRASS_OVERWRITE'] = '1'
        
    def run(self):
        """Main function of data_preparation class. Returns computed
        parameters from input data using GRASS GIS in a form of a
        dictionary.

        :return data: dictionary with model parameters.
        """
        # get input parameters from GRASS UI
        # TODO: TBD

