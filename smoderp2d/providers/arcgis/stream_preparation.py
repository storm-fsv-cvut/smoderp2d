#!/usr/bin/python
# -*- coding: latin-1 -*-
# SMODERP 2D
# Created by Tomas Edlman, CTU Prague, 2015-2016

# posledni uprava
__author__ = "edlman"
__date__ = "$29.12.2015 18:20:20$"

from smoderp2d.providers.arcgis.terrain import compute_products

# importing system moduls
import arcpy
import os
import sys
import numpy as np
from arcpy.sa import *

from smoderp2d.providers.base import Logger

from smoderp2d.providers.base.stream_preparation import StreamPreparationBase
from smoderp2d.providers.base.stream_preparation import StreamPreparationError, ZeroSlopeError

class StreamPreparation(StreamPreparationBase):
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

        return streams, streams_loc

    def _delete_fields(self, table, fields):
        """Delete attributes.

        :param str table: attrubute table
        :param list fields: attributes to delete
        """
        arcpy.DeleteField_management(table, fields)

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

        self._delete_fields(streams,
                            ["NAZ_TOK_1", "NAZ_TOK_12", "TOK_ID_1", "TOK_ID_12"]
        )

        field = ["FID", "start_elev", "POINT_X", "end_elev", "POINT_X_1"]

        with arcpy.da.SearchCursor(streams, field) as cursor:
            for row in cursor:
                if row[1] > row[3]:
                    continue
                else:
                    arcpy.FlipLine_edit(streams)
        self._add_field(streams, "to_node", "DOUBLE", -9999)

        field_start = ["FID", "POINT_X", "POINT_Y", "POINT_X_1", "POINT_Y_1", "to_node"]
        field_end = ["FID", "POINT_X", "POINT_Y", "POINT_X_1", "POINT_Y_1", "to_node"]
        with arcpy.da.SearchCursor(streams, field_start) as cursor_start:
            for row in cursor_start:
                a = (row[1], row[2])
                d = row[0]
                with arcpy.da.UpdateCursor(streams, field_end) as cursor_end:
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

    def _get_mat_tok_usek(self, streams):
        """
        Get numpy array of integers detecting whether there is a stream on corresponding pixel of raster (number equal
        or greater than 1000 in return numpy array) or not (number 0 in return numpy array).

        :param streams: Polyline with streams in the area.
        :return mat_tok_usek: Numpy array
        """

        stream_rst1 = os.path.join(self.temp, "stream_rst")
        stream_rst = arcpy.PolylineToRaster_conversion(
            streams, "FID", stream_rst1, "MAXIMUM_LENGTH", "NONE", self.spix
        )
        tok_usek = os.path.join(self.temp, "tok_usek")

        arcpy.gp.Reclassify_sa(
            stream_rst, "VALUE", "NoDataValue 1000", tok_usek, "DATA"
        )
        mat_tok_usek = arcpy.RasterToNumPyArray(
            tok_usek, self.ll_corner, self.cols, self.rows
        )
        mat_tok_usek = mat_tok_usek.astype('int16')

        count = arcpy.GetCount_management(tok_usek)
        no_of_streams = int(count.getOutput(0))

        # each element of stream has a number assigned from 0 to no. of stream parts
        for i in range(self.rows):
            for j in range(self.cols):
                if mat_tok_usek[i][j] > no_of_streams - 1:
                    mat_tok_usek[i][j] = 0
                else:
                    mat_tok_usek[i][j] += 1000
        
        return mat_tok_usek


    def _stream_slope(self, streams):
        """
        :param streams:
        """
        # sklon
        field = ["FID", "start_elev", "end_elev", "sklon", "SHAPE@LENGTH", "length"]
        with arcpy.da.UpdateCursor(streams, field) as cursor:
            for row in cursor:
                sklon_koryta = (row[1] - row[2]) / row[4]
                if sklon_koryta == 0:
                    raise ZeroSlopeError(row[0])
                row[3] = sklon_koryta
                cursor.updateRow(row)
                row[5] = row[4]
                cursor.updateRow(row)

    def _get_streamslist(self, streams):
        """
        Compute shape of streams.
        :param streams:
        """

        # tvar koryt
        stream_tvar_dbf = os.path.join(self.temp, "stream_tvar.dbf")
        arcpy.CopyRows_management(self.tab_stream_tvar, stream_tvar_dbf)
        sfield = ["cislo", "smoderp", "tvar", "b", "m", "drsnost", "Q365"]

        try:
            self._join_table(
                streams, self.tab_stream_tvar_code, stream_tvar_dbf,
                self.tab_stream_tvar_code,
                "cislo;tvar;b;m;drsnost;Q365"
            )
        except:
            self._add_field(streams, "smoderp", "TEXT", "0")
            self._join_table(streams, self.tab_stream_tvar_code,
                             stream_tvar_dbf, self.tab_stream_tvar_code,
                             "cislo;tvar;b;m;drsnost;Q365")

        with arcpy.da.SearchCursor(streams, sfield) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    if row[i] == " ":
                        Logger.info(
                            "Value in tab_stream_tvar are no correct - STOP, check shp file streams in output")
                        # sys.exit() -> raise

        fields = arcpy.ListFields(streams)
        self.field_names = [field.name for field in fields]
        self.streams_tmp = [[] for field in fields]

        for row in arcpy.SearchCursor(streams):
            field_vals = [row.getValue(field) for field in self.field_names]
            # field_vals
            for i in range(len(field_vals)):
                self.streams_tmp[i].append(field_vals[i])

        self.streamslist = []
        self._append_value('FID')
        self._append_value('POINT_X')
        self._append_value('POINT_Y')
        self._append_value('POINT_X_1')
        self._append_value('POINT_Y_1')
        self._append_value('to_node')
        self._append_value('length')
        self._append_value('sklon')

        self._append_value('smoderp', 'SMODERP')
        self._append_value('cislo', 'CISLO')
        self._append_value('tvar','TVAR')
        self._append_value('b', 'B')
        self._append_value('m', 'M')
        self._append_value('drsnost', 'DRSNOST')
        self._append_value('q365', 'Q365')

