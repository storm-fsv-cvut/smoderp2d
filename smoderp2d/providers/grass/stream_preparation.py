import os
from subprocess import PIPE

from grass.script.core import tempfile
from grass.pygrass.modules import Module
from grass.pygrass.raster import raster2numpy
from grass.pygrass.vector import Vector, VectorTopo

from smoderp2d.providers.base.stream_preparation import StreamPreparationBase
from smoderp2d.providers.base.stream_preparation import StreamPreparationError, ZeroSlopeError
from smoderp2d.providers.grass.manage_fields import ManageFields

class StreamPreparation(StreamPreparationBase, ManageFields):
    def __init__(self, args, writter):
        super(StreamPreparation, self).__init__(args, writter)

        os.environ['GRASS_OVERWRITE'] = '1'

        # set computation region
        Module('g.region',
               raster=self.dem
        )

    def _setnull(self):
        """Define mask.
        """
        Module('r.mapcalc',
               expression='{o} = if({i} < 300, null(), {i})'.format(
                   o='setnull', i=self.flow_accumulation_clip
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
               output='aoi'
        )

        Module('v.buffer',
               input='aoi',
               output='aoi_buffer',
               distance=-self.spix / 3
        )

        stream_clip = 'stream_clip'
        Module('v.clip',
               input=self.stream,
               clip='aoi_buffer',
               output=stream_clip
        )

        # TODO: MK - nevim proc se maze neco, co v atributove tabulce vubec neni
        self._delete_fields(
            stream_clip,
            ["EX_JH", "POZN", "PRPROP_Z", "IDVT", "UTOKJ_ID", "UTOKJN_ID", "UTOKJN_F"]
        )

        return stream_clip, None # TODO: ?

    def _stream_direction(self, stream):
        """
        Compute elevation of start/end point of stream parts.
        Add code of ascending stream part into attribute table.
        
        :param stream: vector stream features
        """
        # calculate start_elev (point_x, point_y) + end_elev (point_x_1, point_y_1)
        columns = ['point_x', 'point_y']
        for what in ('start', 'end'):
            # compute start/end elevation
            Module('v.to.points',
                   input=stream,
                   use=what,
                   output=what,
            )
            column = '{}_elev'.format(what)
            Module('v.what.rast',
                   map=what,
                   raster=self.dem_clip,
                   column=self._data[column]
            )
            self._join_table(
                stream, self._primary_key,
                '{}_1'.format(what), self._primary_key,
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

        # flip segments if end_elev > start_elev
        fields = [self._primary_key, "start_elev", "end_elev",
                  "point_x", "point_y", "point_x_1", "point_y_1"]
        # TODO: rewrite using pygrass
        ret = Module('v.db.select',
                     flags='c',
                     map=stream,
                     columns=fields,
                     stdout_=PIPE)
        cats = {}
        for line in ret.outputs.stdout.splitlines():
            row = line.split('|')
            if float(row[1]) < float(row[2]):
                cats[row[0]] = (row[1], row[2], row[3], row[4], row[5], row[6])
        if cats:
            # flip stream direction (end_elev > start_elev)
            Module('v.edit',
                   map=stream,
                   tool='flip',
                   cats=','.join(cats)
            )
            # update also attributes
            tmpfile = tempfile(create=False)
            with open(tmpfile, 'w') as fd:
                for k, v in cats.items():
                    # v (0:start_elev, 1:end_elev,
                    #    2:point_x, 3:point_y,
                    #    4:point_x_1, 5:point_y_1)
                    # start_elev -> end_elev
                    fd.write('UPDATE {} SET {} = {} WHERE {} = {};\n'.format(
                        stream, fields[1], v[1], fields[0], k))
                    # end_elev -> start_elev
                    fd.write('UPDATE {} SET {} = {} WHERE {} = {};\n'.format(
                        stream, fields[2], v[0], fields[0], k))
                    # point_x -> point_x_1
                    fd.write('UPDATE {} SET {} = {} WHERE {} = {};\n'.format(
                        stream, fields[3], v[4], fields[0], k))
                    # point_y -> point_y_1
                    fd.write('UPDATE {} SET {} = {} WHERE {} = {};\n'.format(
                        stream, fields[4], v[5], fields[0], k))
                    # point_x_1 -> point_x
                    fd.write('UPDATE {} SET {} = {} WHERE {} = {};\n'.format(
                        stream, fields[5], v[2], fields[0], k))
                    # point_y_1 -> point_y
                    fd.write('UPDATE {} SET {} = {} WHERE {} = {};\n'.format(
                        stream, fields[6], v[3], fields[0], k))

            Module('db.execute',
                   input=tmpfile
            )

        # calculates to_node (fid of preceding segment)
        self._add_field(stream, "to_node", "DOUBLE", -9999)
        to_node = {}
        with VectorTopo(stream) as stream_vect:
            for line in stream_vect:
                start, end = line.nodes()
                cat = line.cat
                for start_line in start.lines():
                    if start_line.cat != cat:
                        to_node[cat] = start_line.cat

        if to_node:
            # TODO: rewrite using pygrass
            tmpfile = tempfile(create=False)
            with open(tmpfile, 'w') as fd:
                for c, n in to_node.items():
                    fd.write('UPDATE {} SET to_node = {} WHERE {} = {};\n'.format(
                        stream, n, self._primary_key, c
                    ))
            Module('db.execute',
                  input=tmpfile
            )

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
               output='stream_rst',
               use='cat'
        )
        # TODO: probably not needed, see relevant code in arcgis provider
        Module('r.mapcalc',
               # expression='{o} = if(isnull({i}), 1000, {i})'.format(
               expression='{o} = {i}'.format(
                   o='stream_seg', i='stream_rst'
        ))
        # TODO: probably not needed
        # Module('g.region',
        #        w=self.ll_corner[0],
        #        s=self.ll_corner[1],
        #        cols=self.cols,
        #        rows=self.rows
        # )
        mat_stream_seg = raster2numpy('stream_seg')
        mat_stream_seg = mat_stream_seg.astype('int16')

        # TODO: ?
        no_of_streams = mat_stream_seg.max()

        self._get_mat_stream_seg_(mat_stream_seg, no_of_streams)

        return mat_stream_seg

    def _stream_slope(self, stream):
        """
        :param stream:
        """
        # calculate stream length
        Module('v.to.db',
               map=stream,
               option='length',
               columns='length'
        )

        # calculate slope
        Module('v.db.update',
               map=stream,
               column='slope',
               query_column='(start_elev - end_elev) / length'
        )

        # TODO: rewrite into pygrass syntax
        ret = Module('v.db.select',
                     flags='c',
                     map=stream,
                     columns='cat,slope',
                     stdout_=PIPE
        )
        for row in ret.outputs.stdout.splitlines():
            cat, slope = row.split('|')
            if float(slope) == 0:
                raise ZeroSlopeError(int(cat))

    def _get_streamlist(self, stream):
        """Compute shape of stream.

        :param stream:
        """
        Module('db.copy',
               from_table=self.tab_stream_shape,
               from_database='$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db',
               to_table='stream_shape'
        )

        # TODO: (check if smoderp column exists)
        sfields = ["number", "shapetype", "b", "m", "roughness", "q365"]
        try:
            self._join_table(
                stream, self.tab_stream_shape_code, 'stream_shape',
                self.tab_stream_shape_code,
                sfields
            )
        except:
            self._add_field(
                stream, "smoderp", "TEXT", "0"
            )
            self._join_table(
                stream, self.tab_stream_shape_code,
                'stream_shape', self.tab_stream_shape_code,
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
