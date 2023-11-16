# unfortunately Python version shipped by ArcGIS 10 lacks Enum

class CompType:
    sheet_only = 0
    rill = 1
    sheet_stream = 2
    stream_rill = 3
    subflow_rill = 4
    stream_subflow_rill = 5

    @classmethod
    def __getitem__(cls, key):
        if key == 'sheet_only':
            return cls.sheet_only
        elif key == 'rill':
            return cls.rill
        elif key == 'sheet_stream':
            return cls.sheet_stream
        elif key == 'stream_rill':
            return cls.stream_rill
        elif key == 'subflow_rill':
            return cls.subflow_rill
        else:
            return cls.stream_subflow_rill
