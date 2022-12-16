import arcpy

class ManageFields(object):
    def _add_field(self, vector, newfield, datatype, default_value):
        """
        Adds field into attribute field of feature class.

        :param vector: Feature class to which new field is to be added.
        :param newfield:
        :param datatype:
        :param default_value:
        """
        try:
            arcpy.management.DeleteField(vector, newfield)
        except:
            pass

        arcpy.management.AddField(vector, newfield, datatype)
        arcpy.management.CalculateField(vector, newfield, default_value, "PYTHON")

    def _join_table(self, in_vector, in_field, join_table, join_field, fields=None):
        """
        Join attribute table.

        :param in_vector: input data layer
        :param in_field: input column
        :param join_table: table to join
        :param join_field: column to join
        :param fields: list of fields (None for all fields)
        """
        arcpy.management.JoinField(in_vector, in_field, join_table, join_field, fields)

    def _delete_fields(self, table, fields):
        """Delete attributes.

        :param str table: attribute table
        :param list fields: attribute fields to be deleted
        """
        for f in fields:
            arcpy.management.DeleteField(table, f)
