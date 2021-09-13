import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from lib import SQL_COLUMNS, row_to_json, rows_to_json


class TestLib(unittest.TestCase):
    def test_row_to_json(self):
        row = tuple([c for c in SQL_COLUMNS])
        expected = {c: c for c in SQL_COLUMNS}
        expected.update({'uri': '/shows/show_id'})
        self.assertDictEqual(expected, row_to_json(row))

    def test_rows_to_json(self):
        num_rows = 5
        rows = [tuple([f'{c}-{i}' for c in SQL_COLUMNS]) for i in range(num_rows)]
        expected = [{c: f'{c}-{i}' for c in SQL_COLUMNS} for i in range(num_rows)]
        for e in expected:
            e['uri'] = f'/shows/{e["show_id"]}'
        self.assertListEqual(expected, rows_to_json(rows))
