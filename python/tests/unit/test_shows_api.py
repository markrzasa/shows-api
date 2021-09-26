import os
import sys
import unittest

from fastapi import HTTPException
from unittest.mock import patch, MagicMock, call

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import persistence
from app.rest.models.shows import Show, ShowCreate
from app.rest.routers.shows import list_shows, get, put, create


class TestShowsApi(unittest.IsolatedAsyncioTestCase):
    async def test_list_invalid_sort_field(self):
        with self.assertRaises(HTTPException):
            await list_shows(sort=['not valid', 'also not valid'], filter=[])

    @patch('app.rest.routers.shows.Engine')
    async def test_list_valid_sort_field(self, engine):
        session, query = self.mock_session(engine)
        sort_setting = ['title', 'description']
        await list_shows(sort=sort_setting, filter=[])
        self.assertListEqual(
            [call(persistence.Show.title), call(persistence.Show.description)],
            query.order_by.call_args_list)

    async def test_list_invalid_filters_field(self):
        with self.assertRaises(HTTPException):
            await list_shows(sort=[], filter=['not valid', 'also not valid'])

    @patch('app.rest.routers.shows.Engine')
    async def test_list_valid_filters_field(self, engine):
        session, query = self.mock_session(engine)
        filters = ['title=unittest', 'type=TV Show']
        await list_shows(sort=['title'], filter=filters)
        self.assertEqual(
            [str(persistence.Show.title.like('unittest')), str(persistence.Show.type.like('TV Show'))],
            [str(al.args[0]) for al in query.filter.call_args_list]
        )

    @patch('app.rest.routers.shows.Engine')
    async def test_get_not_found(self, engine):
        _, query = self.mock_session(engine)
        query.all.return_value = []
        with self.assertRaises(HTTPException):
            await get(1)

    @patch('app.rest.routers.shows.Engine')
    async def test_get_found_too_many(self, engine):
        _, query = self.mock_session(engine)
        query.all.return_value = [MagicMock(), MagicMock()]
        with self.assertRaises(HTTPException):
            await get(1)

    @patch('app.rest.routers.shows.Engine')
    async def test_put_not_found(self, engine):
        _, query = self.mock_session(engine)
        query.all.return_value = []
        show = Show.construct(show_id=123, title='Unit the Test', type='TV Show')
        with self.assertRaises(HTTPException):
            await put(1, show)

    @patch('app.rest.routers.shows.Engine')
    async def test_put_found_too_many(self, engine):
        _, query = self.mock_session(engine)
        query.all.return_value = [MagicMock(), MagicMock()]
        show = Show.construct(show_id=123, title='Unit the Test', type='TV Show')
        with self.assertRaises(HTTPException):
            await put(1, show)

    @patch('app.rest.routers.shows.Engine')
    async def test_create(self, engine):
        title = 'Unit the Test'
        type = 'TV Show'
        _, query = self.mock_session(engine)
        filter = MagicMock()
        db_show = MagicMock()
        db_show.id = 1
        db_show.title = title
        db_show.type = type
        filter.one.return_value = db_show
        query.filter.return_value = filter
        show = ShowCreate.construct(title=title, type=type)
        created_show = await create(show)
        self.assertIsNotNone(created_show.date_added)
        self.assertIsNotNone(created_show.id)

    @classmethod
    def mock_session(cls, engine: MagicMock) -> (MagicMock, MagicMock):
        session = MagicMock()
        query = MagicMock()
        engine.new_session.return_value.__enter__.return_value = session
        session.query.return_value = query
        query.filter.return_value = query
        query.order_by.return_value = query
        return session, query
