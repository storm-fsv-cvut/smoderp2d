# unfortunately Python version shipped by ArcGIS 10 lacks Enum

class CompType:
    sheet_only = 0
    rill = 1
    sheet_stream = 2
    stream_rill = 3
    subflow = 4
    subflow_rill = 5
    stream_subflow_rill = 6

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
        elif key == 'subflow':
            return cls.subflow
        elif key == 'subflow_rill':
            return cls.subflow_rill
        elif key == 'stream_subflow_rill':
            return cls.stream_subflow_rill
        else:
            return cls.stream_subflow_rill
