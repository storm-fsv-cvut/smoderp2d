from grass.pygrass.modules import Module
from grass.pygrass.vector import Vector

# TODO: rewrite to pygrass syntax
class ManageFields(object):
    def _add_field(self, vector, newfield, datatype, default_value):
        """
        Adds field into attribute field of feature class.

        :param vector: Feature class to which new field is to be added.
        :param newfield:
        :param datatype:
        :param default_value:
        """
        with Vector(vector) as data:
            found = newfield in data.table.columns.names()
        if found:
            Module('v.db.dropcolumn',
                   map=vector,
                   columns=newfield
            )

        Module('v.db.addcolumn',
               map=vector,
               columns='{} {}'.format(newfield, datatype)
        )

        Module('v.db.update',
               map=vector,
               column=newfield,
               value=default_value
        )

    def _join_table(self, in_vector, in_field,
                    join_table, join_field, fields=None):
        """
        Join attribute table.

        :param in_vector: input data layer
        :param in_field: input column
        :param join_table: table to join
        :param join_field: column to join
        :param fields: list of fields (None for all fields)
        """
        kwargs = {}
        if fields:
            kwargs['subset_columns'] = fields
        Module('v.db.join',
               map=in_vector,
               column=in_field,
               other_table=join_table,
               other_column=join_field,
               **kwargs
        )

    def _delete_fields(self, table, fields):
        """Delete attributes.

        :param str table: attrubute table
        :param list fields: attributes to delete
        """
        Module('v.db.dropcolumn',
               map=table,
               columns=','.join(fields)
        )
