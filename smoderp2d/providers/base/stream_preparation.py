from smoderp2d.providers.base import Logger

# definice erroru  na urovni modulu
#
class StreamPreparationError(Exception):
    pass

class ZeroSlopeError(Exception):
    """Exception raised for zero slope of a reach.
    """
    def __init__(self, fid):
        self.msg = 'Reach FID: {} has zero slope'.format(
            fid
        )

class StreamPreparationBase(object):
    def __init__(self, args, writter):
        self.stream = args[0]
        self.tab_stream_shape = args[1]
        self.tab_stream_shape_code = args[2]
        self.dem = args[3]
        self.null = args[4]
        self.spix = args[5]
        self.rows = args[6]
        self.cols = args[7]
        self.ll_corner = args[8]
        self.output = args[9]
        self.dem_clip = args[10]
        self.intersect = args[11]
        self._primary_key = args[12]
        self.flow_accumulation_clip = args[13]

        # internal data
        self._data = {
                'setnull': 'temp',
                'stream': 'control',
                'stream_loc': 'control',
                'aoi': 'control',
                'aoi_buffer': 'control',
                'start': 'temp',
                'end': 'temp',
                'start_elev': 'start_elev',
                'end_elev': 'end_elev',
            # TODO: not used            
            #   'stream_rst': 'control',
                'stream_seg': 'control',
                'stream_shape': 'control'
        }

        self.storage = writter

    def prepare(self):
        self._setnull() # not used for anything, just saves setnull

        Logger.info("Clip stream...")
        stream, stream_loc = self._clip_stream()

        Logger.info("Computing stream direction and elevation...")
        self._stream_direction(stream)

        mat_stream_seg = self._get_mat_stream_seg(stream)

        Logger.info("Computing stream hydraulics...")
        self._stream_hydraulics(stream)

        self._stream_slope(stream)

        self._get_streamlist(stream)

        return self.streamlist, mat_stream_seg, stream_loc

    def _setnull(self):
        raise NotImplemented("Not implemented for base provider")

    def _clip_stream(self):
        raise NotImplemented("Not implemented for base provider")

    def _stream_direction(self, stream):
        raise NotImplemented("Not implemented for base provider")

    def _get_mat_stream_seg(self, stream):
        raise NotImplemented("Not implemented for base provider")

    def _get_mat_stream_seg_(self, mat_stream_seg, no_of_streams):
        # each element of stream has a number assigned from 0 to
        # no. of stream parts
        for i in range(self.rows):
            for j in range(self.cols):
                if mat_stream_seg[i][j] > 0:
                    mat_stream_seg[i][j] += 999

    def _stream_hydraulics(self, stream):
        """TODO: is it used?"""
        self._add_field(stream, "length", "DOUBLE", 0.0)  # (m)
        self._add_field(stream, "slope", "DOUBLE", 0.0)  # (-)
        self._add_field(stream, "V_infl_ce", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "V_infl_us", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "V_infl", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "Q_outfl", "DOUBLE", 0.0)  # (m3/s)
        self._add_field(stream, "V_outfl", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "V_outfl_tm", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "V_zbyt", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "V_zbyt_tm", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "V", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "h", "DOUBLE", 0.0)  # (m)
        self._add_field(stream, "vs", "DOUBLE", 0.0)  # (m/s)
        self._add_field(stream, "NS", "DOUBLE", 0.0)  # (m)
        self._add_field(stream, "total_Vic", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "total_Viu", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "max_Q", "DOUBLE", 0.0)  # (m3/s)
        self._add_field(stream, "max_h", "DOUBLE", 0.0)  # (m)
        self._add_field(stream, "max_vs", "DOUBLE", 0.0)  # (m/s)
        self._add_field(stream, "total_Vo", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "total_Vi", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "total_NS", "DOUBLE", 0.0)  # (m3)
        self._add_field(stream, "total_Vz", "DOUBLE", 0.0)  # (m3)

    def _get_streamlist(self, stream):
        raise NotImplemented("Not implemented for base provider") 

    def _streamlist(self):
        self.streamlist = []
        for field_name in [self._primary_key,
                           'point_x',
                           'point_y',
                           'point_x_1',
                           'point_y_1',
                           'to_node',
                           'length',
                           'slope',
                           'smoderp',
                           'number',
                           'shapetype',
                           'b',
                           'm',
                           'roughness',
                           'q365']:
            try:
                idx = self.field_names.index(field_name)
            except ValueError:
                idx = self.field_names.index(field_name.upper())

            self.streamlist.append(
                self.stream_tmp[idx]
            )
