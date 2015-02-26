# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import jtskit
from . import base


RESULTS = {
    'incorrect_headers': {
        'id': 'incorrect_headers',
        'name': 'Incorrect Headers',
        'msg': 'The headers do not match the schema.'
    },
    'incorrect_dimensions': {
        'id': 'incorrect_dimensions',
        'name': 'Incorrect Dimensions',
        'msg': 'The row dimensions do not match the header dimensions.'
    },
    'incorrect_type': {
        'id': 'incorrect_type',
        'name': 'Incorrect Type',
        'msg': 'The value is not a valid {0}.'
    },
    'required_field': {
        'id': 'required_field',
        'name': 'Required Field',
        'msg': 'Column {0} is a required field, but no value can be found in this row.'
    }
}


class SchemaValidator(base.Validator):

    """Validate data against a JSON Table Schema."""

    name = 'schema'

    def __init__(self, fail_fast=False, transform=False, report_limit=1000,
                 row_limit=30000, schema=None, ignore_field_order=True,
                 report_stream=None, report=None, **kwargs):

        super(SchemaValidator, self).__init__(
            fail_fast=fail_fast, transform=transform,
            report_limit=report_limit, row_limit=row_limit,
            report_stream=report_stream, report=report)

        self.ignore_field_order = ignore_field_order
        if not schema:
            self.schema = None
        else:
            self.schema = self.schema_model(schema)

    def schema_model(self, schema):
        return jtskit.models.JSONTableSchema(schema)

#    def pre_run(self, data_table):
#        if self.schema is None:
#            # make a schema
#            # TODO: 50 here is arbitrary
#            sample_data = [row for row in data_table.values][:50]
#            guessed_schema = table_schema.make(data_table.headers, sample_data)
#            self.schema = self.schema_model(guessed_schema)
#
#        return True, data_table

    def run_header(self, headers, header_index=0):

        valid = True

        if self.schema:
            if self.ignore_field_order:
                if not (set(headers) == set(self.schema.headers)):

                    valid = False
                    _type = RESULTS['incorrect_headers']
                    entry = self.make_entry(
                        self.name,
                        self.RESULT_CATEGORY_HEADER,
                        self.RESULT_LEVEL_ERROR,
                        _type['msg'],
                        _type['id'],
                        _type['name'],
                        headers,
                        header_index,
                        self.RESULT_HEADER_ROW_NAME
                    )

                    self.report.write(entry)
                    if self.fail_fast:
                        return valid, headers

            else:
                if not (headers == self.schema.headers):

                    valid = False
                    _type = RESULTS['incorrect_headers']
                    entry = self.make_entry(
                        self.name,
                        self.RESULT_CATEGORY_HEADER,
                        self.RESULT_LEVEL_ERROR,
                        _type['msg'],
                        _type['id'],
                        _type['name'],
                        headers,
                        header_index,
                        self.RESULT_HEADER_ROW_NAME,
                    )

                    self.report.write(entry)
                    if self.fail_fast:
                        return valid, headers

        return valid, headers

    def run_row(self, headers, index, row):

        valid = True
        row_name = self.get_row_id(headers, row)

        if self.schema:
            if not (len(headers) == len(row)):

                valid = False
                _type = RESULTS['incorrect_dimensions']
                entry = self.make_entry(
                    self.name,
                    self.RESULT_CATEGORY_ROW,
                    self.RESULT_LEVEL_ERROR,
                    _type['msg'],
                    _type['id'],
                    _type['name'],
                    row,
                    index,
                    row_name,
                )

                self.report.write(entry)
                if self.fail_fast:
                    return valid, headers, index, row

            else:
                for column_name, column_value in zip(headers, row):
                    # check type and format
                    if not self.schema.cast(column_name, column_value):

                        valid = False
                        _type = RESULTS['incorrect_type']
                        entry = self.make_entry(
                            self.name,
                            self.RESULT_CATEGORY_ROW,
                            self.RESULT_LEVEL_ERROR,
                            _type['msg'].format(self.schema.get_type(column_name).name.title()),
                            _type['id'],
                            _type['name'],
                            row,
                            index,
                            row_name,
                            headers.index(column_name),
                            column_name
                        )

                        self.report.write(entry)
                        if self.fail_fast:
                            return valid, headers, index, row

                    # CONSTRAINTS
                    constraints = self.schema.get_constraints(column_name)
                    if constraints:
                        # check constraints.required
                        if constraints.get('required') and not column_value:

                            valid = False
                            _type = RESULTS['required_field']
                            entry = self.make_entry(
                                self.name,
                                self.RESULT_CATEGORY_ROW,
                                self.RESULT_LEVEL_ERROR,
                                _type['msg'].format(column_name),
                                _type['id'],
                                _type['name'],
                                row,
                                index,
                                row_name,
                                headers.index(column_name),
                                column_name
                            )

                            self.report.write(entry)
                            if self.fail_fast:
                                return valid, headers, index, row

                    # TODO: check constraints.unique
                    # TODO: check constraints.min* and constraints.max*

        return valid, headers, index, row
