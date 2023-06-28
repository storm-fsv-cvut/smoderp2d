class Argument:

    def __init__(self, label):
        self.label = label


class Section:

    def __init__(self, label, section_arguments=()):
        self.label = label
        self.arguments = section_arguments


arguments = {
    'elevation': Argument('Input surface raster'),
    'soil': Argument('Soil polygons feature layer'),
    'landuse': Argument('Landuse polygons feature layer'),
    'points': Argument('Input points feature layer'),
    'stream': Argument('Stream network feature layer'),
    'rainfall': Argument('Definition of the rainfall event'),
    'output': Argument('Output directory'),
    'max_time_step': Argument('Maximum time step [s]'),
    'total_time': Argument('Total running time [min]'),
    'computation_type': Argument('Computation type'),
    'soil_type_field': Argument('Field with the soil type identifier'),
    'landuse_type_field': Argument('Field with the landuse type identifier'),
    'soil_landuse_table': Argument('Soils and landuse parameters table'),
    'soil_landuse_field': Argument('Field with the connection between landuse and soil'),
    'channel_type_identifier': Argument(
        'Field with the channel type identifier'
    ),
    'channel_properties': Argument('Channel properties table'),
    'preparation_only': Argument('Do the data preparation only'),
}


sections = [
    Section(
        'Spatial data',
        (
            'elevation', 'soil', 'soil_type_field', 'landuse',
            'soil_landuse_table', 'points', 'stream', 'rainfall'
        )
    ),
    Section(
        'Control tables',
        (
            'landuse_type_field', 'soil_landuse_field', 'channel_properties',
            'channel_type_identifier'
        )
    ),
    Section(
        'Computation options',
        ('output', 'max_time_step', 'total_time')
    ),
    Section('Advanced', ())  # TODO: Add ('preparation_only',))
]
