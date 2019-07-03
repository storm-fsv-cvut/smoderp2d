import os
import tempfile
from subprocess import PIPE

from grass.pygrass.modules import Module
from grass.pygrass.raster import raster2numpy
from grass.pygrass.vector import Vector

from smoderp2d.providers.base.stream_preparation import StreamPreparationBase
from smoderp2d.providers.base.stream_preparation import StreamPreparationError, ZeroSlopeError
from smoderp2d.providers.grass.terrain import compute_products
from smoderp2d.providers.grass.manage_fields import ManageFields

class StreamPreparation(StreamPreparationBase, ManageFields):
    def __init__(self, args):
        super(StreamPreparation, self).__init__(args)

        os.environ['GRASS_OVERWRITE'] = '1'

        # set computation region
        Module('g.region',
               raster=self.dem
        )

    def _set_output(self):
        """Define output temporary folder and geodatabase.
        """
        pass
        # Module('g.mapset',
        #                flags='c',
        #                mapset='stream_prep'
        # )

    def _setnull(self):
        """Define mask.
        """
        # water flows according dem
        dem_fill, flow_direction, flow_accumulation, slope = \
            compute_products(self.dem_clip, None)

        Module('r.mapcalc',
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

        :return streams:
        :return streams_loc:
        """
        # TODO: unfortunately dissolving clip layer does not work in
        # GRASS as expected, ugly workaround below
        Module('v.db.addcolumn',
               map=self.intersect,
               columns="clip int"
        )
        Module('v.db.update',
               map=self.intersect,
               column="clip",
               value=1
        )
        clip_map = "{}_clip".format(self.intersect)
        Module('v.dissolve',
               input=self.intersect,
               output=clip_map,
               column="clip",
        )
        Module('v.clip',
               input=self.null,
               clip=clip_map,
               output=self._data['aoi']
        )

        Module('v.buffer',
               input=self._data['aoi'],
               output=self._data['aoi_buffer'],
               distance=-self.spix / 3
        )

        Module('v.clip',
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
        columns = ['point_x', 'point_y']
        for what in ('start', 'end'):
            # compute start/end elevation
            Module('v.to.points',
                   input=stream,
                   use=what,
                   output=self._data[what],
            )
            column = '{}_elev'.format(what)
            Module('v.what.rast',
                   map=self._data[what],
                   raster=self.dem_clip,
                   column=self._data[column]
            )
            self._join_table(
                stream, "cat",
                '{}_1'.format(self._data[what]), "cat",
                [column]
            )

            # start/end coordinates needs to be stored also in attribute table
            if what == 'end':
                columns = list(map(lambda x: x + '_1', columns))
            Module('v.to.db',
                   map=stream,
                   option=what,
                   columns=columns
            )

        # TODO: not needed?
        # self._delete_fields(
        #     stream,
        #     ["SHAPE_LEN", "SHAPE_LENG", "SHAPE_LE_1", "NAZ_TOK_1", "TOK_ID_1", "SHAPE_LE_2",
        #      "SHAPE_LE_3", "NAZ_TOK_12", "TOK_ID_12", "SHAPE_LE_4", "ORIG_FID_1"]
        # )

        # self._delete_fields(
        #     stream,
        #     ["NAZ_TOK_1", "NAZ_TOK_12", "TOK_ID_1", "TOK_ID_12"]
        # )

        # flip segments if end_elev > start_elev
        field = ["cat", "start_elev", "end_elev"]
        # TODO: rewrite using pygrass
        ret = Module('v.db.select',
                     flags='c',
                     map=stream,
                     columns=field,
                     stdout_=PIPE)
        cats = []
        for line in ret.outputs.stdout.splitlines():
            row = line.split('|')
            if float(row[1]) < float(row[2]):
                cats.append(int(row[0]))
        if cats:
            # TODO: attributes must be recalculated
            Module('v.edit',
                   map=stream,
                   tool='flip',
                   cats=','.join(cats)
            )
        self._add_field(stream, "to_node", "DOUBLE", -9999)

        fields = ["cat", "start_elev", "end_elev", "to_node"]
        # TODO: could be used start/end_2 tables instead
        Module('v.db.update',
               map=stream,
               column=fields[-1],
               value=fields[0],
               where="{} == {}".format(
                   fields[2], fields[1]
        ))

        # TODO: not needed probably
        # self._delete_fields(
        #     stream,
        #     ["SHAPE_LEN", "SHAPE_LE_1", "SHAPE_LE_2", "SHAPE_LE_3", "SHAPE_LE_4", "SHAPE_LE_5",
        #      "SHAPE_LE_6", "SHAPE_LE_7", "SHAPE_LE_8", "SHAPE_LE_9", "SHAPE_L_10", "SHAPE_L_11",
        #      "SHAPE_L_12", "SHAPE_L_13", "SHAPE_L_14"]
        # )
        # self._delete_fields(
        #     stream, ["ORIG_FID", "ORIG_FID_1", "SHAPE_L_14"]
        # )

    def _get_mat_stream_seg(self, stream):
        """Get numpy array of integers detecting whether there is a stream on
        corresponding pixel of raster (number equal or greater than
        1000 in return numpy array) or not (number 0 in return numpy
        array).

        :param stream: Polyline with stream in the area.
        :return mat_stream_seg: Numpy array
        """
        Module('g.region',
               vector=stream,
               res=self.spix
        )
        Module('v.to.rast',
               input=stream,
               type='line',
               output=self._data['stream_rst'],
               use='cat'
        )
        # TODO: probably not needed, see relevant code in arcgis provider
        Module('r.mapcalc',
               expression='{o} = if(isnull({i}), 1000, {i})'.format(
                   o=self._data['stream_seg'], i=self._data['stream_rst']
        ))
        # TODO: probably not needed
        # Module('g.region',
        #        w=self.ll_corner[0],
        #        s=self.ll_corner[1],
        #        cols=self.cols,
        #        rows=self.rows
        # )
        mat_stream_seg = raster2numpy(self._data['stream_seg'])
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
        fields = [self._primary_key, "start_elev", "end_elev", "sklon",
                  "SHAPE@LENGTH", "length"]

        # TODO: rewrite into pygrass syntax
        ret = Module('v.db.select',
                     map=stream,
                     columns=fields,
                     stdout_=PIPE
        )
        sql = []
        for row in ret.outputs.stdout.splitlines():
            slope = (float(row[1]) - float(row[2])) / float(row[4])
            if slope == 0:
                raise ZeroSlopeError(int(row[0]))
            sql.append(
                'update {} set {} = {}, {} = {} where {} = {}'.format(
                    stream, fileds[4], slope, fields[5], row[4], fields[0], row[0]
            ))
        tmpfile = next(tempfile._get_candidate_names())
        with open(tmpfile, 'w') as fd:
            fd.write(';\n'.join(sql))
        Module('db.execute',
               input=tmpfile
        )

    def _get_streamlist(self, stream):
        """Compute shape of stream.

        :param stream:
        """
        Module('db.copy',
               from_table=self.tab_stream_shape,
               from_database='$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db',
               to_table=self._data['stream_shape']
        )

        # TODO: (check if smoderp column exists)
        sfields = ["number", "shapetype", "b", "m", "roughness", "q365"]
        try:
            self._join_table(
                stream, self.tab_stream_shape_code, self._data['stream_shape'],
                self.tab_stream_shape_code,
                sfields
            )
        except:
            self._add_field(
                stream, "smoderp", "TEXT", "0"
            )
            self._join_table(
                stream, self.tab_stream_shape_code,
                self._data['stream_shape'], self.tab_stream_shape_code,
                sfields
            )

        sfields.insert(1, "smoderp")
        # TODO: rewrite into pygrass syntax
        ret = Module('v.db.select',
                     flags='c',
                     map=stream,
                     columns=sfields,
                     stdout_=PIPE
        )
        for row in ret.outputs.stdout.splitlines():
            for value in row.split('|'):
                if value == '':
                    raise StreamPreparationError(
                        "Empty value in {} found.".format(stream)
                    )

        with Vector(stream) as data:
            self.field_names = data.table.columns.names()
        self.stream_tmp = [[] for field in self.field_names]

        # TODO: rewrite into pygrass syntax
        ret = Module('v.db.select',
                     flags='c',
                     map=stream,
                     columns=self.field_names,
                     stdout_=PIPE
        )
        for row in ret.outputs.stdout.splitlines():
            i = 0
            for val in row.split('|'):
                self.stream_tmp[i].append(float(val))
                i += 1

        self.streamlist = []
        self._streamlist()
