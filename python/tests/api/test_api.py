import copy
import csv
import os

import json
import requests
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from lib import row_to_json

TEST_DIR = os.path.dirname(__file__)
CSV_FILE = os.path.join(TEST_DIR, '../..', '..', 'datasource', 'netflix_titles.csv')

TEST_URL = os.getenv('TEST_URL', 'http://localhost:8000')
SHOWS_API = f'{"/".join([TEST_URL, "shows"])}'
NUM_TEST_SHOWS = 50

TEST_SHOW = {
    'type': 'TV Show',
    'title': 'Welcome Back, Kotter',
    'director': '',
    'cast': (
        'Gabe Kaplan, Marcia Strassman, John Sylvester White, Robert Hegyes, Lawrence Hilton-Jacobs, '
        'Ron Palillo, John Travolta'
    ),
    'country': 'United States',
    'release_year': '1975',
    'rating': '',
    'duration': '30m',
    'listed_in': 'TV Shows',
    'description': (
        "Gabe Kotter returns to his old high school -- this time as a teacher. He's put in charge of a class "
        "full of unruly remedial students called the Sweathogs. They're a bunch of wisecracking, "
        "underachieving and incorrigible students, and it takes all of Mr. Kotter's humor -- and experience as "
        "a former Sweathog himself -- to deal with his class."
    )
}


class TestApi(unittest.TestCase):
    shows = []

    @classmethod
    def to_url(cls, show):
        return ''.join([TEST_URL, show['uri']])

    @classmethod
    def delete_all(cls):
        while True:
            response = requests.get(SHOWS_API)
            response.raise_for_status()
            shows = response.json()
            if not shows:
                break
            for s in response.json():
                requests.delete(cls.to_url(s)).raise_for_status()

    @classmethod
    def setUpClass(cls) -> None:
        cls.delete_all()
        with open(CSV_FILE) as handle:
            reader = csv.reader(handle, delimiter=',', quotechar='"')
            next(reader)
            for i in range(NUM_TEST_SHOWS):
                show = row_to_json(tuple(next(reader)))
                cls.shows.append(cls.create(show))

        cls.shows = sorted(cls.shows, key=lambda s: s['title'])

    def setUp(self) -> None:
        self.to_delete = []

    def tearDown(self) -> None:
        for s in self.to_delete:
            response = requests.delete(self.to_url(s))
            if response.status_code != 404:
                response.raise_for_status()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.delete_all()
        response = requests.get(SHOWS_API)
        response.raise_for_status()
        assert len(response.json()) == 0

    def test_alive(self):
        response = requests.get(f'{TEST_URL}/alive')
        response.raise_for_status()
        self.assertDictEqual({'alive': True}, response.json())

    def test_pagination_limit(self):
        self.__assert_pagination(0, 10)

    def test_pagination_offset(self):
        self.__assert_pagination(5, 25)

    def __assert_pagination(self, offset: int, limit: int):
        response = requests.get(f'{SHOWS_API}?offset={offset}&limit={limit}')
        response.raise_for_status()
        shows = response.json()
        assert len(shows) == limit
        for i in range(len(shows)):
            response = requests.get(f'{TEST_URL}{shows[i]["uri"]}')
            response.raise_for_status()
            self.assertDictEqual(shows[i], self.shows[i + offset])

    def test_crud(self):
        # create the show
        response = requests.post(f'{SHOWS_API}/', json=TEST_SHOW)
        self.cleanup_after(response)
        self.assert_response(TEST_SHOW, response)
        created_show = response.json()

        # get the newly created show
        show_url = ''.join([TEST_URL, created_show['uri']])
        response = requests.get(show_url)
        self.assert_response(TEST_SHOW, response)

        # update the show
        show = copy.deepcopy(TEST_SHOW)
        show['title'] = 'Welcome Back, Kotter!!!'
        show['release_year'] = '2075'
        response = requests.put(show_url, json=show)
        self.assert_response(show, response)

        response = requests.get(show_url)
        self.assert_response(show, response)

        # delete the show
        response = requests.delete(show_url)
        response.raise_for_status()

        # make sure the show was deleted
        response = requests.get(show_url)
        assert response.status_code == 404

    def test_create_required_fields_only(self):
        show = {
            'type': 'TV Show',
            'title': 'Welcome Back, Kotter!!!'
        }
        response = requests.post(f'{SHOWS_API}/', json=show)
        self.cleanup_after(response)
        self.assert_response(show, response)

    def test_filter(self):
        response = requests.post(f'{SHOWS_API}/', json=TEST_SHOW)
        self.cleanup_after(response)
        self.assert_response(TEST_SHOW, response)

        filter_url = f'{SHOWS_API}?filter=title={TEST_SHOW["title"]}&filter=type={TEST_SHOW["type"]}'
        response = requests.get(filter_url)
        response.raise_for_status()
        response_json = response.json()
        assert len(response_json) == 1, f'unexpected response:\n{json.dumps(response_json, indent=2, sort_keys=True)}'
        self.assert_show(TEST_SHOW, response.json()[0])

        filter_url = f'{SHOWS_API}?filter=title={TEST_SHOW["title"]}&filter=type=not-{TEST_SHOW["type"]}'
        response = requests.get(filter_url)
        response.raise_for_status()
        response_json = response.json()
        assert len(response_json) == 0

    def test_double_delete(self):
        response = requests.post(f'{SHOWS_API}/', json=TEST_SHOW)
        self.cleanup_after(response)
        self.assert_response(TEST_SHOW, response)

        show_url = self.to_url(response.json())
        response = requests.delete(show_url)
        response.raise_for_status()
        response = requests.delete(show_url)
        response.raise_for_status()

    @classmethod
    def create(cls, show: dict) -> dict:
        response = requests.post(f'{SHOWS_API}/', json=show)
        response.raise_for_status()
        return response.json()

    def cleanup_after(self, response):
        if response.status_code == 200:
            self.to_delete.append(response.json())

    def assert_response(self, show: dict, response):
        response.raise_for_status()
        self.assert_show(show, response.json())

    def assert_show(self, expected, actual):
        actual = {k: v for k, v in actual.items() if k in expected}
        self.assertDictEqual(expected, actual)
