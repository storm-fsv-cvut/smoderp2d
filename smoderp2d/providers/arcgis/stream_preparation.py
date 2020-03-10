# SMODERP 2D
# Created by Tomas Edlman, CTU Prague, 2015-2016

import os
import sys
import arcpy
from arcpy.sa import *

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.stream_preparation import StreamPreparationBase
from smoderp2d.providers.base.stream_preparation import StreamPreparationError, ZeroSlopeError
from smoderp2d.providers.arcgis.manage_fields import ManageFields

class StreamPreparation(StreamPreparationBase, ManageFields):
    def __init__(self, args, writter):
        super(StreamPreparation, self).__init__(args, writter)

        # Check extensions
        arcpy.CheckOutExtension("3D")
        arcpy.CheckOutExtension("Spatial")

        arcpy.env.snapRaster = self.dem

    def _setnull(self):
        """Define mask.
        """

        try:
            setnull = arcpy.sa.SetNull(
                self.flow_accumulation_clip, 1, "VALUE < 300"
            )
            setnull.save(self.storage.output_filepath('setnull'))
        except:
            raise StreamPreparationError(
                "Unexpected error during setnull calculation: {}".format(
                    sys.exc_info()[0]
                ))

    def _clip_stream(self):
        """
        Clip stream with intersect of input data (from data_preparation).

        :return stream:
        :return stream_loc:
        """

#        stream = os.path.join(
#            self.temp, "{}.shp".format(self._data['stream'])
#        )
#        stream_loc = os.path.join(
#            self.temp, "{}.shp".format(self._data['stream_loc'])
#        )
#        aoi = os.path.join(
#            self.temp, "{}.shp".format(self._data['aoi'])
#        )

#        aoi_buffer = arcpy.Buffer_analysis(
#            aoi,
#            os.path.join(self.temp, "{}.shp".format(self._data['aoi_buffer'])),
#            -self.spix / 3, "FULL", "ROUND", "NONE"
#        )

        stream = self.storage.output_filepath('stream', item='')
        stream_loc = self.storage.output_filepath('stream_loc')
        aoi = self.storage.output_filepath('aoi')

        aoi = arcpy.Clip_analysis(
            self.null, self.intersect, aoi
        )

        aoi_buffer = arcpy.Buffer_analysis(
            aoi,
            self.storage.output_filepath('aoi_buffer'),
            -self.spix / 3, "FULL", "ROUND", "NONE"
        )

        stream = arcpy.Clip_analysis(
            self.stream, aoi_buffer, stream
        )

        # TODO: MK - nevim proc se maze neco, co v atributove tabulce vubec neni
        self._delete_fields(
            stream,
            ["EX_JH", "POZN", "PRPROP_Z", "IDVT", "UTOKJ_ID", "UTOKJN_ID", "UTOKJN_F"]
        )

        return stream, stream_loc # TODO: where defined ?

    def _stream_direction(self, stream):
        """
        Compute elevation of start/end point of stream parts.
        Add code of ascending stream part into attribute table.
        
        :param stream: vector stream features
        """
        # TODO: vyresit mazani atributu v atributove tabulce (jestli je to potreba)
        # TODO: vyresit nasledujici:
        #
        # Nasledujici blok je redundantni, nicmene do "stream"
        # pridava nekolik sloupecku, u kterych jsem nemohl dohledat,
        # jestli se s nimi neco dela. Proto to tu zatim nechavam.

#        start = arcpy.FeatureVerticesToPoints_management(
#            stream, os.path.join(self.temp, self._data["start"]), "START"
#        )

#        end = arcpy.FeatureVerticesToPoints_management(
#            stream, os.path.join(self.temp, self._data["end"]), "END"
#        )

        start = arcpy.FeatureVerticesToPoints_management(
            stream, self.storage.output_filepath("start"), "START"
        )

        end = arcpy.FeatureVerticesToPoints_management(
            stream, self.storage.output_filepath("end"), "END"
        )
        arcpy.sa.ExtractMultiValuesToPoints(
            start, [[self.dem_clip, self._data["start_elev"]]], "NONE"
        )
        arcpy.sa.ExtractMultiValuesToPoints(
            end, [[self.dem_clip, self._data["end_elev"]]], "NONE"
        )

        # Join
        self._join_table(stream, self._primary_key, start, "ORIG_FID")
        self._join_table(stream, self._primary_key, end, "ORIG_FID")

        self._delete_fields(
            stream,
            ["SHAPE_LEN", "SHAPE_LENG", "SHAPE_LE_1", "NAZ_TOK_1", "TOK_ID_1", "SHAPE_LE_2",
             "SHAPE_LE_3", "NAZ_TOK_12", "TOK_ID_12", "SHAPE_LE_4", "ORIG_FID_1"]
        )
        self._delete_fields(
            stream,
            ["start_elev", "end_elev", "ORIG_FID", "ORIG_FID_1"]
        )

        start = arcpy.FeatureVerticesToPoints_management(
            stream, self.storage.output_filepath("start"), "START")

        end = arcpy.FeatureVerticesToPoints_management(
            stream, self.storage.output_filepath("end"), "END")

        arcpy.sa.ExtractMultiValuesToPoints(
            start,
            [[self.dem_clip, "start_elev"]], "NONE"
        )
        arcpy.sa.ExtractMultiValuesToPoints(
            end, [[self.dem_clip, "end_elev"]], "NONE"
        )
        arcpy.AddXY_management(start)
        arcpy.AddXY_management(end)

        # Join
        self._join_table(stream, self._primary_key, start, "ORIG_FID")
        self._join_table(stream, self._primary_key, end, "ORIG_FID")

        self._delete_fields(
            stream,
            ["NAZ_TOK_1", "NAZ_TOK_12", "TOK_ID_1", "TOK_ID_12"]
        )

        field = [self._primary_key, "start_elev", "POINT_X", "end_elev", "POINT_X_1"]
        with arcpy.da.SearchCursor(stream, field) as cursor:
            for row in cursor:
                if row[1] > row[3]:
                    continue
                arcpy.FlipLine_edit(stream) ### TODO: ? all
        self._add_field(stream, "to_node", "DOUBLE", -9999)

        fields = [self._primary_key, "POINT_X", "POINT_Y", "POINT_X_1", "POINT_Y_1", "to_node"]

        # if stream is saved in gdb, it's id field begins with 1
        # in further computation (stream.py) it would exceed array length
        # MK 4.4.19
        fid_offset_flag = True
        fid_offset = 0
        with arcpy.da.SearchCursor(stream, fields) as cursor_start:
            for row in cursor_start:

                if fid_offset_flag:
                    fid_offset = row[0]
                    fid_offset_flag = False

                a = (row[1], row[2])
                d = row[0] - fid_offset

                with arcpy.da.UpdateCursor(stream, fields) as cursor_end:
                    for row in cursor_end:
                        b = (row[3], row[4])
                        if a == b:
                            row[5] = d
                            cursor_end.updateRow(row)
                        else:
                            row[5] = "-9999"

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
        stream_seg = self.storage.output_filepath('stream_seg')
        arcpy.PolylineToRaster_conversion(
            stream, self._primary_key, stream_seg,
            "MAXIMUM_LENGTH", "NONE", self.spix
        )

        # TODO: reclassification rule is invalid, stream_seg is the same as stream_rst
        # stream_seg = self.storage.output_filepath('stream_seg')
        # arcpy.gp.Reclassify_sa(
        #     stream_rst, "VALUE",
        #     "NoDataValue 1000", stream_seg, "DATA"
        # )

        ll_corner = arcpy.Point(
            self.ll_corner[0], self.ll_corner[1]
        )
        mat_stream_seg = arcpy.RasterToNumPyArray(
            stream_seg, ll_corner, self.cols, self.rows
        )
        mat_stream_seg = mat_stream_seg.astype('int16')

        # TODO: is no_of_streams needed (-> mat_stream_seg.max())
        count = arcpy.GetCount_management(stream_seg)
        no_of_streams = int(count.getOutput(0))
        self._get_mat_stream_seg_(mat_stream_seg, no_of_streams)
        
        return mat_stream_seg

    def _stream_slope(self, stream):
        """
        :param stream:
        """
        fields = [self._primary_key, "start_elev", "end_elev", "slope", "SHAPE@LENGTH", "length"]

        with arcpy.da.UpdateCursor(stream, fields) as cursor:
            for row in cursor:
                slope = (row[1] - row[2]) / row[4]
                if slope == 0:
                    raise ZeroSlopeError(row[0])
                row[3] = slope
                cursor.updateRow(row) # needed?
                row[5] = row[4]
                cursor.updateRow(row)

    def _get_streamlist(self, stream):
        """Compute shape of stream.

        :param stream:
        """
        stream_shape_dbf = self.storage.output_filepath('stream_shape')
        arcpy.CopyRows_management(self.tab_stream_shape, stream_shape_dbf)

        try:
            # TODO: hardcoded columns
            self._join_table(
                stream, self.tab_stream_shape_code, stream_shape_dbf,
                self.tab_stream_shape_code,
                "number;shapetype;b;m;roughness;Q365"
            )
        except:
            self._add_field(stream, "smoderp", "TEXT", "0")
            self._join_table(stream, self.tab_stream_shape_code,
                             stream_shape_dbf, self.tab_stream_shape_code,
                             "number;shapetype;b;m;roughness;Q365")

        sfields = ["number", "smoderp", "shapetype", "b", "m", "roughness", "Q365"]
        with arcpy.da.SearchCursor(stream, sfields) as cursor:
            try:
                for row in cursor:
                    for i in range(len(row)):
                        if row[i] == " ":
                            raise StreamPreparationError(
                                "Empty value in tab_stream_shape found."
                            )
            except RuntimeError: 
                raise StreamPreparationError(
                        "Check if fields code in tab_stream_shape are correct. Columns are hardcoded. Proper columns codes are: {}".format(sfields)
                )

        fields = arcpy.ListFields(stream)
        self.field_names = [field.name for field in fields]
        self.stream_tmp = [[] for field in fields]

        for row in arcpy.SearchCursor(stream):
            field_vals = [row.getValue(field) for field in self.field_names]
            for i in range(len(field_vals)):
                self.stream_tmp[i].append(field_vals[i])

        # check if ID field starts from 1, if so, make it start from 0
        # it could not be done in stream feature class, bcs it's id field is locked
        # MK 4.4.19
        if self.stream_tmp[0][0] == 1:
            for i in range(len(self.stream_tmp[0])):
                self.stream_tmp[0][i] -= 1

        self._streamlist()
