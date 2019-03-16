# SMODERP 2D
# Created by Tomas Edlman, CTU Prague, 2015-2016

import os
import sys
import arcpy
from arcpy.sa import *

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.stream_preparation import StreamPreparationBase
from smoderp2d.providers.base.stream_preparation import StreamPreparationError, ZeroSlopeError
from smoderp2d.providers.arcgis.terrain import compute_products
from smoderp2d.providers.arcgis.manage_fields import ManageFields

class StreamPreparation(StreamPreparationBase, ManageFields):
    def __init__(self, args):
        super(StreamPreparation, self).__init__(args)
        
        # Overwriting output
        arcpy.env.overwriteOutput = 1
        
        # Check extensions
        arcpy.CheckOutExtension("3D")
        arcpy.CheckOutExtension("Spatial")

        arcpy.env.snapRaster = self.dem

    def _set_output(self):
        """Define output temporary folder and geodatabase.
        """
        self.temp = os.path.join(self.output, "stream_prep")
        if not os.path.exists(self.temp):
            os.makedirs(self.temp)
        self.tempgdb = arcpy.CreateFileGDB_management(
            self.temp, "stream_prep.gdb"
        )

    def _setnull(self):
        """Define mask.
        """
        # water flows according dem
        dem_fill, flow_direction, flow_accumulation, slope = \
            compute_products(self.dem_clip, self.temp, None)

        try:
            setnull = arcpy.sa.SetNull(
                flow_accumulation, 1, "VALUE < 300")
            setnull.save(os.path.join(self.temp, self._data["setnull"]))
        except:
            raise StreamPreparationError(
                "Unexpected error during setnull calculation: {}".format(
                    sys.exc_info()[0]
                ))

    def _clip_streams(self):
        """
        Clip streams with intersect of input data (from data_preparation).

        :return toky:
        :return toky_loc:
        """
        streams = os.path.join(
            self.temp, "{}.shp".format(self._data['streams'])
        )
        streams_loc = os.path.join(
            self.temp, "{}.shp".format(self._data['streams_loc'])
        )
        aoi = os.path.join(
            self.temp, "{}.shp".format(self._data['aoi'])
        )
        
        aoi = arcpy.Clip_analysis(
            self.null, self.intersect, aoi
        )

        aoi_buffer = arcpy.Buffer_analysis(
            aoi,
            os.path.join(self.temp, "{}.shp".format(self._data['aoi_buffer']),
            -self.spix / 3, "FULL", "ROUND", "NONE")

        streams = arcpy.Clip_analysis(
            self.stream, aoi_buffer, streams
        )

        # TODO: MK - nevim proc se maze neco, co v atributove tabulce vubec neni
        self._delete_fields(
            streams,
            ["EX_JH", "POZN", "PRPROP_Z", "IDVT", "UTOKJ_ID", "UTOKJN_ID", "UTOKJN_F"]
        )

        return streams, streams_loc # TODO: where defined ?

    def _stream_direction(self, streams):
        """
        Compute elevation of start/end point of stream parts.
        Add code of ascending stream part into attribute table.
        
        :param streams:
        """
        # TODO: vyresit mazani atributu v atributove tabulce (jestli je to potreba)
        # TODO: vyresit nasledujici:
        #
        # Nasledujici blok je redundantni, nicmene do "streams"
        # pridava nekolik sloupecku, u kterych jsem nemohl dohledat,
        # jestli se s nimi neco dela. Proto to tu zatim nechavam.
        start = arcpy.FeatureVerticesToPoints_management(
            streams, os.path.join(self.temp, self._data["start"]), "START"
        )
        end = arcpy.FeatureVerticesToPoints_management(
            streams, os.path.join(self.temp, self._data["end"]), "END"
        )
        arcpy.sa.ExtractMultiValuesToPoints(
            start, [[self.dem_clip, self._data["start_elev"]]], "NONE"
        )
        arcpy.sa.ExtractMultiValuesToPoints(
            end, [[self.dem_clip, self._data["end_elev"]]], "NONE"
        )

        # Join
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

        start = arcpy.FeatureVerticesToPoints_management(
            streams, self.temp + os.sep + "start", "START")
        end = arcpy.FeatureVerticesToPoints_management(
            streams, self.temp + os.sep + "end", "END")
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
        self._join_table(streams, "FID", start, "ORIG_FID")
        self._join_table(streams, "FID", end, "ORIG_FID")

        self._delete_fields(
            streams,
            ["NAZ_TOK_1", "NAZ_TOK_12", "TOK_ID_1", "TOK_ID_12"]
        )

        field = ["FID", "start_elev", "POINT_X", "end_elev", "POINT_X_1"]
        with arcpy.da.SearchCursor(streams, field) as cursor:
            for row in cursor:
                if row[1] > row[3]:
                    continue
                arcpy.FlipLine_edit(streams) ### ? all
        self._add_field(streams, "to_node", "DOUBLE", -9999)

        fields = ["FID", "POINT_X", "POINT_Y", "POINT_X_1", "POINT_Y_1", "to_node"]
        with arcpy.da.SearchCursor(streams, fields) as cursor_start:
            for row in cursor_start:
                a = (row[1], row[2])
                d = row[0]
                with arcpy.da.UpdateCursor(streams, fields) as cursor_end:
                    for row in cursor_end:
                        b = (row[3], row[4])
                        if a == b:
                            row[5] = d
                            cursor_end.updateRow(row)
                        else:
                            row[5] = "-9999"

        self._delete_fields(
            streams,
            ["SHAPE_LEN", "SHAPE_LE_1", "SHAPE_LE_2", "SHAPE_LE_3", "SHAPE_LE_4", "SHAPE_LE_5",
             "SHAPE_LE_6", "SHAPE_LE_7", "SHAPE_LE_8", "SHAPE_LE_9", "SHAPE_L_10", "SHAPE_L_11",
             "SHAPE_L_12", "SHAPE_L_13", "SHAPE_L_14"]
        )
        
        self._delete_fields(
            streams, ["ORIG_FID", "ORIG_FID_1", "SHAPE_L_14"]
        )

    def _get_mat_stream_seg(self, streams):
        """Get numpy array of integers detecting whether there is a stream on
        corresponding pixel of raster (number equal or greater than
        1000 in return numpy array) or not (number 0 in return numpy
        array).

        :param streams: Polyline with streams in the area.
        :return mat_stream_seg: Numpy array
        """
        stream_rst1 = os.path.join(self.temp, self._data["stream_rst"])
        stream_rst = arcpy.PolylineToRaster_conversion(
            streams, "FID", stream_rst1, "MAXIMUM_LENGTH", "NONE", self.spix
        )

        stream_seg = os.path.join(self.temp, self._data["stream_seg"])
        arcpy.gp.Reclassify_sa(
            stream_rst, "VALUE", "NoDataValue 1000", stream_seg, "DATA"
        )

        ll_corner = arcpy.Point(
            self.data['xllcorner'], self.data['yllcorner']
        )
        mat_stream_seg = arcpy.RasterToNumPyArray(
            stream_seg, ll_corner, self.cols, self.rows
        )
        mat_stream_seg = mat_stream_seg.astype('int16')

        count = arcpy.GetCount_management(stream_seg)
        no_of_streams = int(count.getOutput(0))

        self._get_mat_stream_seg_(mat_stream_seg)
        
        return mat_stream_seg

    def _stream_slope(self, streams):
        """
        :param streams:
        """
        fields = ["FID", "start_elev", "end_elev", "sklon", "SHAPE@LENGTH", "length"]
        with arcpy.da.UpdateCursor(streams, fields) as cursor:
            for row in cursor:
                slope = (row[1] - row[2]) / row[4]
                if slope == 0:
                    raise ZeroSlopeError(row[0])
                row[3] = slope
                cursor.updateRow(row) # needed?
                row[5] = row[4]
                cursor.updateRow(row)

    def _get_streamslist(self, streams):
        """Compute shape of streams.

        :param streams:
        """
        stream_shape_dbf = os.path.join(self.temp, "{}.dbf".format(
            self._data['stream_shape']
        ))
        arcpy.CopyRows_management(self.tab_stream_shape, stream_shape_dbf)

        try:
            self._join_table(
                streams, self.tab_stream_shape_code, stream_shape_dbf,
                self.tab_stream_shape_code,
                "number;shape;b;m;roughness;Q365"
            )
        except:
            self._add_field(streams, "smoderp", "TEXT", "0")
            self._join_table(streams, self.tab_stream_shape_code,
                             stream_shape_dbf, self.tab_stream_shape_code,
                             "number;shape;b;m;roughness;Q365")

        sfields = ["number", "smoderp", "shape", "b", "m", "roughness", "Q365"]
        with arcpy.da.SearchCursor(streams, sfields) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    if row[i] == " ":
                        raise StreamPreparationError(
                            "Value in tab_stream_shape are no correct - STOP, "
                            "check shp file streams in output"
                        )

        fields = arcpy.ListFields(streams)
        self.field_names = [field.name for field in fields]
        self.streams_tmp = []

        for row in arcpy.SearchCursor(streams):
            field_vals = [row.getValue(field) for field in self.field_names]
            self.streams_tmp.append(field_vals)

        self._streamlist()
