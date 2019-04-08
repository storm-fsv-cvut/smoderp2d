import os

import grass.script as gs
from grass.script import array as garray

from smoderp2d.providers.base.stream_preparation import StreamPreparationBase
from smoderp2d.providers.grass.terrain import compute_products
from smoderp2d.providers.grass.manage_fields import ManageFields

class StreamPreparation(StreamPreparationBase, ManageFields):
    def __init__(self, args):
        super(StreamPreparation, self).__init__(args)

        os.environ['GRASS_OVERWRITE'] = '1'

        # set computation region
        gs.run_command('g.region',
                       raster=self.dem
        )

    def _set_output(self):
        """Define output temporary folder and geodatabase.
        """
        pass
        # gs.run_command('g.mapset',
        #                flags='c',
        #                mapset='stream_prep'
        # )

    def _setnull(self):
        """Define mask.
        """
        # water flows according dem
        dem_fill, flow_direction, flow_accumulation, slope = \
            compute_products(self.dem_clip, None)

        gs.run_command('r.mapcalc',
                       expression='{o} = if({i} < 300, null(), {i})'.format(
                           o=self._data['setnull'], i=flow_accumulation
        ))

        # TODO
        # raise StreamPreparationError(
        #     "Unexpected error during setnull calculation: {}".format(
        #         sys.exc_info()[0]
        #     ))

    def _clip_stream(self):
        """
        Clip stream with intersect of input data (from data_preparation).

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
                       output=self._data['stream']
        )

        # TODO: MK - nevim proc se maze neco, co v atributove tabulce vubec neni
        self._delete_fields(
            self._data['stream'],
            ["EX_JH", "POZN", "PRPROP_Z", "IDVT", "UTOKJ_ID", "UTOKJN_ID", "UTOKJN_F"]
        )

        return self._data['stream'], None # TODO: ?

    def _stream_direction(self, stream):
        """
        Compute elevation of start/end point of stream parts.
        Add code of ascending stream part into attribute table.
        
        :param stream:
        """
        for what in ('start', 'end'):
            gs.run_command('v.to.points',
                           input=stream,
                           use=what,
                           output=self._data[what],
            )
            gs.run_command('v.what.rast',
                           map=self._data[what],
                           raster=self.dem_clip,
                           column=self._data['{}_elev'.format(what)]
            )

            self._join_table(stream, "cat", '{}_1'.format(self._data[what]), "cat")

        self._delete_fields(
            stream,
            ["SHAPE_LEN", "SHAPE_LENG", "SHAPE_LE_1", "NAZ_TOK_1", "TOK_ID_1", "SHAPE_LE_2",
             "SHAPE_LE_3", "NAZ_TOK_12", "TOK_ID_12", "SHAPE_LE_4", "ORIG_FID_1"]
        )
        self._delete_fields(
            stream,
            ["start_elev", "end_elev", "ORIG_FID", "ORIG_FID_1"]
        )

        self._delete_fields(
            stream,
            ["NAZ_TOK_1", "NAZ_TOK_12", "TOK_ID_1", "TOK_ID_12"]
        )

        # TODO
        # field = ["cat", "start_elev", "POINT_X", "end_elev", "POINT_X_1"]
        # ret = gs.read_command('v.db.select',
        #                       map=stream,
        #                       columns=field)
        # for row in ret.splitlines():
        #     if row[1] > row[3]:
        #         continue
        #     gs.run_command('v.edit',
        #                    map=stream,
        #                    tool='flip'
        #     )
        #     self._add_field(stream, "to_node", "DOUBLE", -9999)

        # fields = ["cat", "POINT_X", "POINT_Y", "POINT_X_1", "POINT_Y_1", "to_node"]
        # gs.run_command('v.db.update',
        #                map=stream,
        #                column=field_start[-1],
        #                value='-9999'
        # )
        # gs.run_command('v.db.update',
        #                map=stream,
        #                column=field_start[-1],
        #                value=field_start[0],
        #                where="{} == {} and {} == {}".format(
        #                    row[1], row[3], row[2], row[4]
        # ))

        self._delete_fields(
            stream,
            ["SHAPE_LEN", "SHAPE_LE_1", "SHAPE_LE_2", "SHAPE_LE_3", "SHAPE_LE_4", "SHAPE_LE_5",
             "SHAPE_LE_6", "SHAPE_LE_7", "SHAPE_LE_8", "SHAPE_LE_9", "SHAPE_L_10", "SHAPE_L_11",
             "SHAPE_L_12", "SHAPE_L_13", "SHAPE_L_14"]
        )

        self._delete_fields(
            stream, ["ORIG_FID", "ORIG_FID_1", "SHAPE_L_14"]
        )

    def _get_mat_stream_seg(self, stream):
        """Get numpy array of integers detecting whether there is a stream on
        corresponding pixel of raster (number equal or greater than
        1000 in return numpy array) or not (number 0 in return numpy
        array).

        :param stream: Polyline with stream in the area.
        :return mat_stream_seg: Numpy array
        """
        gs.run_command('g.region',
                       vector=stream,
                       res=self.spix
        )
        gs.run_command('v.to.rast',
                       input=stream,
                       type='line',
                       output=self._data['stream_rst'],
                       use='cat'
        )
        gs.run_command('r.mapcalc',
                       expression='{o} = if(isnull({i}), 1000, {i})'.format(
                           o=self._data['stream_seg'], i=self._data['stream_rst']
        ))
        gs.run_command('g.region',
                       w=self.ll_corner[0],
                       s=self.ll_corner[1],
                       cols=self.cols,
                       rows=self.rows
        )
        mat_stream_seg = garray.array()
        mat_stream_seg.read(self._data['stream_seg'])
        mat_stream_seg = mat_stream_seg.astype('int16')

        # TODO: ?
        no_of_streams = 0

        self._get_mat_stream_seg_(mat_stream_seg, no_of_streams)

        return mat_stream_seg

    def _stream_slope(self, stream):
        """
        :param stream:
        """
        # TODO !
        return
        fields = ["FID", "start_elev", "end_elev", "sklon", "SHAPE@LENGTH", "length"]
        ret = gs.read_command('v.db.select',
                              map=stream,
                              columns=fields)
        sql = []
        for row in ret.splitlines():
            slope = (float(row[1]) - float(row[2])) / float(row[4])
            if slope == 0:
                raise ZeroSlopeError(int(row[0]))
            sql.append(
                'update {} set {} = {}, {} = {} where {} = {}'.format(
                    stream, fileds[4], slope, fields[5], row[4], fields[0], row[0]
            ))
        tmpfile = gs.tempfile()
        with open(tmpfile, 'w') as fd:
            fd.write(';\n'.join(sql))
        gs.run_command('db.execute',
                       input=tmpfile
        )

    def _get_streamlist(self, stream):
        """Compute shape of stream.

        :param stream:
        """
        gs.run_command('db.copy',
                       from_table=self.tab_stream_shape,
                       from_database='$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db',
                       to_table=self._data['stream_shape']
        )

        # todo
        # try:
        #     self._join_table(
        #         stream, self.tab_stream_shape_code, self._data['stream_shape'],
        #         self.tab_stream_shape_code,
        #         "number;shape;b;m;roughness;Q365"
        #     )
        # except:
        #     self._add_field(stream, "smoderp", "TEXT", "0")
        #     self._join_table(stream, self.tab_stream_shape_code,
        #                      self._data['stream_shape'], self.tab_stream_shape_code,
        #                      "number;shape;b;m;roughness;Q365")

        # sfields = ["number", "smoderp", "shape", "b", "m", "roughness", "Q365"]
        # for row in gs.vector_db_select(
        #         map=stream,
        #         columns=sfields)['values']:
        #     for i in range(len(row)):
        #         if row[i] == " ":
        #             raise StreamPreparationError(
        #                 "Value in tab_stream_shape are no correct - STOP, "
        #                 "check shp file stream in output"
        #             )

        self.field_names = gs.vector_db_select(map=stream)['columns']
        self.stream_tmp = [[] for field in self.field_names]

        # for row in gs.vector_db_select(
        #         map=stream,
        #         columns=self.field_names)['values']:
        #   for i in range(len(row)):
        # self.stream_tmp[i].append(row[i])


        self.streamlist = []
        ### self._streamlist()
