from smoderp2d.providers.base import Logger

# definice erroru  na urovni modulu
#
class StreamPreparationError(Exception):
    pass

class ZeroSlopeError(Error):
    """Exception raised for zero slope of a reach.
    """
    def __init__(self, fid):
        self.msg = 'Reach FID: {} has zero slope'.format(
            fid
        )

class StreamPreparationBase(object):
    def __init__(self, args):
        self.stream = args[0]
        self.tab_stream_tvar = args[1]
        self.tab_stream_tvar_code = args[2]
        self.dem = args[3]
        self.null = args[4]
        self.spix = args[5]
        self.rows = args[6]
        self.cols = args[7]
        self.ll_corner = args[8]
        self.output = args[9]
        self.dem_clip = args[10]
        self.intersect = args[11]
        self._add_field = args[12]
        self._join_table = args[13]

        # internal data
        self._data = {}
        for item in [
                'setnull',
                'streams',
                'streams_loc',
                'aoi',
                'aoi_buffer',
                'start',
                'end',
                'start_elev',
                'end_elev']:
            self._data[item] = item
        
    def prepare_streams(self):
        Logger.info("Creating output...")
        self._set_output()

        self._setnull() #not used for anything, just saves setnull

        Logger.info("Clip streams...")
        toky, toky_loc = self._clip_streams()

        Logger.info("Computing stream direction and elevation...")
        self._stream_direction(toky)

        mat_tok_usek = self._get_mat_tok_usek(toky)

        Logger.info("Computing stream hydraulics...")
        self._stream_hydraulics(toky)

        self._stream_slope(toky)

        self._get_tokylist(toky)

        return self.tokylist, mat_tok_usek, toky_loc

    def _set_output(self):
        raise NotImplemented("Not implemented for base provider")

    def _setnull(self):
        raise NotImplemented("Not implemented for base provider")

    def _clip_streams(self):
        raise NotImplemented("Not implemented for base provider")

    def _delete_fields(self, table, fields):
        raise NotImplemented("Not implemented for base provider")

    def _stream_direction(self, toky):
        raise NotImplemented("Not implemented for base provider")

    def _get_mat_tok_usek(self, toky):
        raise NotImplemented("Not implemented for base provider")

    def _stream_hydraulics(self, toky):
        """TODO: is it used?"""
        # HYDRAULIKA TOKU
        self._add_field(toky, "length", "DOUBLE", 0.0)  # (m)
        self._add_field(toky, "sklon", "DOUBLE", 0.0)  # (-)
        self._add_field(toky, "V_infl_ce", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "V_infl_us", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "V_infl", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "Q_outfl", "DOUBLE", 0.0)  # (m3/s)
        self._add_field(toky, "V_outfl", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "V_outfl_tm", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "V_zbyt", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "V_zbyt_tm", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "V", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "h", "DOUBLE", 0.0)  # (m)
        self._add_field(toky, "vs", "DOUBLE", 0.0)  # (m/s)
        self._add_field(toky, "NS", "DOUBLE", 0.0)  # (m)
        self._add_field(toky, "total_Vic", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "total_Viu", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "max_Q", "DOUBLE", 0.0)  # (m3/s)
        self._add_field(toky, "max_h", "DOUBLE", 0.0)  # (m)
        self._add_field(toky, "max_vs", "DOUBLE", 0.0)  # (m/s)
        self._add_field(toky, "total_Vo", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "total_Vi", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "total_NS", "DOUBLE", 0.0)  # (m3)
        self._add_field(toky, "total_Vz", "DOUBLE", 0.0)  # (m3)

    def _get_tokylist(self, toky):
        raise NotImplemented("Not implemented for base provider") 

    def _append_value(self, field_name_try, field_name_except = None):
        if field_name_except == None:
            self.tokylist.append(
                self.toky_tmp[self.field_names.index(field_name_try)]
            )
        else:
            try:
                self.tokylist.append(
                    self.toky_tmp[self.field_names.index(field_name_try)]
                )
            except ValueError:
                self.tokylist.append(
                    self.toky_tmp[self.field_names.index(field_name_except)]
                )
