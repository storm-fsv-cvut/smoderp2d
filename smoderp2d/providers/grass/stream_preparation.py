import grass.script as gs

from smoderp2d.providers.base.stream_preparation import StreamPreparationBase

class StreamPreparation(StreamPreparationBase):
    def __init__(self, args):
        super(StreamPreparation, self).__init__(args)

        os.environ['GRASS_OVERWRITE'] = '1'

        # set computation region
        gs.run_command('g.region'
                       raster=self.dem
        )

    def _set_output(self):
        """Define output temporary folder and geodatabase.
        """
        gs.run_command('g.mapcalc',
                       mapset='stream_prep'
        )

    def _setnull(self):
        """Define mask.
        """
        # water flows according dem
        dem_fill, flow_direction, flow_accumulation, slope = \
            compute_products(self.dem_clip, self.temp, None)

        gs.run_command('r.mapcalc',
                       expression='{o} = if({i} < 300, null(), {i}'.format(
                           o=self._data['setnull'], i=flow_accumulation
        ))

        # TODO
        # raise StreamPreparationError(
        #     "Unexpected error during setnull calculation: {}".format(
        #         sys.exc_info()[0]
        #     ))

    def _clip_streams(self):
        """
        Clip streams with intersect of input data (from data_preparation).

        :return toky:
        :return toky_loc:
        """
        gs.run_command('v.clip',
                       input=self.null,
                       clip=self.intersect,
                       output=self._data['aoi']
        )

        gs.run_command('v.buffer',
                       input=self._data['aoi'],
                       output=self._data['aoi_buffer'],
                       distance=-self.spix / 3
        )

        gs.run_command('v.clip',
                       input=self.stream,
                       clip=self._data['aoi_buffer'],
                       output=self._data['streams']
        )

        # TODO: MK - nevim proc se maze neco, co v atributove tabulce vubec neni
        self._delete_fields(
            self._data['streams'],
            ["EX_JH", "POZN", "PRPROP_Z", "IDVT", "UTOKJ_ID", "UTOKJN_ID", "UTOKJN_F"]
        )

        return streams, streams_loc

    def _delete_fields(self, table, fields):
        """Delete attributes.

        :param str table: attrubute table
        :param list fields: attributes to delete
        """
        gs.run_command('v.db.dropcolumn',
                       map=table,
                       columns=','.join(fields)
        )

    def _stream_direction(self, streams):
        """
        Compute elevation of start/end point of stream parts.
        Add code of ascending stream part into attribute table.
        
        :param streams:
        """
        for what in ('start', 'end'):
            gs.run_command('v.to.points',
                           input=streams,
                           use=what,
                           output=self._data[what]
            )
            gs.run_command('v.what.rast',
                           map=self._data[what],
                           raster=self.dem_clip,
                           column=self._data['{}_elev'.format(what)]
            )

        self._join_table(streams, "FID", start, "ORIG_FID")
        self._join_table(streams, "FID", end, "ORIG_FID")

        self._delete_fields(
            streams,
            ["SHAPE_LEN", "SHAPE_LENG", "SHAPE_LE_1", "NAZ_TOK_1", "TOK_ID_1", "SHAPE_LE_2",
             "SHAPE_LE_3", "NAZ_TOK_12", "TOK_ID_12", "SHAPE_LE_4", "ORIG_FID_1"]
        )
        self._delete_fields(
            streams,
            ["start_elev", "end_elev", "ORIG_FID", "ORIG_FID_1"]
        )
