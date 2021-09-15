import os
import sys
import unittest

from fastapi import HTTPException
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.routers.shows import list_shows


class TestSortApi(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_sort_field(self):
        with self.assertRaises(HTTPException):
            await list_shows(sort=['not valid', 'also not valid'], filter=[])

    @patch('app.routers.shows.DatabaseConnection')
    async def test_valid_sort_field(self, db_connection):
        _, cursor = self.mock_connection(db_connection)
        sort_setting = ['title', 'description']
        await list_shows(sort=sort_setting, filter=[])
        cursor.execute.assert_called_with(
            f'SELECT * FROM shows ORDER BY {",".join(sort_setting)} collate "C" LIMIT 50 OFFSET 0;')

    async def test_invalid_filters_field(self):
        with self.assertRaises(HTTPException):
            await list_shows(sort=[], filter=['not valid', 'also not valid'])

    @patch('app.routers.shows.DatabaseConnection')
    async def test_valid_filters_field(self, db_connection):
        _, cursor = self.mock_connection(db_connection)
        filters = ['title=unittest', 'type=TV Show']
        where_clause = ' AND '.join([
            f'{c.split("=", 1)[0].strip()} LIKE \'%{c.split("=", 1)[-1].strip()}%\'' for c in filters
        ])
        await list_shows(sort=['title'], filter=filters)
        cursor.execute.assert_called_with((
            f'SELECT * FROM shows WHERE {where_clause} ORDER BY title collate "C" LIMIT 50 OFFSET 0;'
        ))

    @classmethod
    def mock_connection(cls, db_connection):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchmany.return_value = []
        conn.cursor.return_value.__enter__.return_value = cursor
        db_connection.get_connection.return_value = conn
        return conn, cursor
