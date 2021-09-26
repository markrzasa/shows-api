import copy
import csv
import os

import json

import logging
import requests
import sys
import unittest

import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

TEST_DIR = os.path.dirname(__file__)
CSV_FILE = os.path.join(TEST_DIR, '../..', '..', 'datasource', 'netflix_titles.csv')

TEST_URL = os.getenv('TEST_URL', 'http://localhost:8000')
SHOWS_API = f'{"/".join([TEST_URL, "shows"])}'
SUMMARY_API = f'{"/".join([TEST_URL, "summary"])}'
NUM_TEST_SHOWS = 50

SHOW_FIELDS = [
    'type', 'title', 'director', 'cast', 'country', 'date_added', 'release_year',
    'rating', 'duration', 'listed_in', 'description'
]

TEST_SHOW = {
    'type': 'TV Show',
    'title': 'Welcome Back, Kotter',
    'director': '',
    'cast': [
        'Gabe Kaplan', 'Marcia Strassman', 'John Sylvester White', 'Robert Hegyes', 'Lawrence Hilton-Jacobs',
        'Ron Palillo', 'John Travolta'
    ],
    'country': 'United States',
    'release_year': '1975',
    'rating': '',
    'duration': '30m',
    'listed_in': ['TV Shows'],
    'description': (
        "Gabe Kotter returns to his old high school -- this time as a teacher. He's put in charge of a class "
        "full of unruly remedial students called the Sweathogs. They're a bunch of wisecracking, "
        "underachieving and incorrigible students, and it takes all of Mr. Kotter's humor -- and experience as "
        "a former Sweathog himself -- to deal with his class."
    )
}


class TestApi(unittest.TestCase):
    logger = None
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
                cls.logger.info(f'deleting show {s["title"]}')
                requests.delete(cls.to_url(s)).raise_for_status()
                cls.logger.info(f'deleted show {s["title"]}')

    @classmethod
    def setUpClass(cls) -> None:
        cls.logger = logging.getLogger('api-tests')
        cls.logger.setLevel(logging.INFO)
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(logging.Formatter('%(asctime)-15s %(message)s'))
        cls.logger.addHandler(stdout_handler)

        cls.logger.info('populating service with shows')
        cls.delete_all()
        with open(CSV_FILE) as handle:
            reader = csv.reader(handle, delimiter=',', quotechar='"')
            next(reader)
            for i in range(NUM_TEST_SHOWS):
                row = next(reader)
                show = {SHOW_FIELDS[i - 1]: row[i] for i in range(1, len(SHOW_FIELDS))}
                cls.logger.info(f'creating show {show["title"]}')
                show['cast'] = [a.strip() for a in show['cast'].split(',')]
                show['listed_in'] = [s.strip() for s in show['listed_in'].split(',')]
                cls.shows.append(cls.create(show))
                cls.logger.info(f'created show {show["title"]}')
        cls.shows = sorted(cls.shows, key=lambda s: s['title'])
        cls.logger.info('populated service with shows')

    def setUp(self) -> None:
        self.logger.info(f'========== start {self._testMethodName} ==========')
        self.to_delete = []

    def tearDown(self) -> None:
        for s in self.to_delete:
            response = requests.delete(self.to_url(s))
            self.logger.info(f'deleting show {s["title"]}')
            if response.status_code == 404:
                self.logger.info(f'show {s["title"]} already deleted')
            else:
                response.raise_for_status()
                self.logger.info(f'deleted show {s["title"]}')
        self.logger.info(f'========== end {self._testMethodName} ==========')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.logger.info('deleting all shows')
        cls.delete_all()
        response = requests.get(SHOWS_API)
        response.raise_for_status()
        assert len(response.json()) == 0
        cls.logger.info('deleted all shows')

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
        created_show = self.create_for_test(TEST_SHOW)

        # get the newly created show
        show_url = self.to_url(created_show)
        response = requests.get(show_url)
        self.assert_response(TEST_SHOW, response)

        # update the show
        show = copy.deepcopy(TEST_SHOW)
        show['title'] = 'Welcome Back, Kotter!!!'
        show['release_year'] = '2075'
        self.put(show_url, show)

        self.get(show_url)

        # delete the show
        self.delete(show_url)

        # make sure the show was deleted
        response = requests.get(show_url)
        assert response.status_code == 404

    def test_create_required_fields_only(self):
        show = {
            'type': 'TV Show',
            'title': 'Welcome Back, Kotter!!!'
        }
        self.create_for_test(show)

    def test_filter(self):
        self.create_for_test(TEST_SHOW)

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
        created_show = self.create_for_test(TEST_SHOW)

        show_url = self.to_url(created_show)
        self.delete(show_url)
        self.delete(show_url)

    def test_summary(self):
        summary_show = copy.deepcopy(TEST_SHOW)
        listings = [str(uuid.uuid4()), str(uuid.uuid4())]
        summary_show['listed_in'] = listings

        show_url = self.to_url(self.create_for_test(summary_show))

        summary = self.get_summary()
        for li in listings:
            self.assertEqual(1, summary['total_by_listed_in'][li])

        listings.append(str(uuid.uuid4()))
        summary_show['listed_in'] = listings
        self.put(show_url, summary_show)

        summary = self.get_summary()
        for li in listings:
            self.assertEqual(1, summary['total_by_listed_in'][li])

        deleted_listing = listings.pop(0)
        summary_show['listed_in'] = listings
        self.put(show_url, summary_show)

        summary = self.get_summary()
        for li in listings:
            self.assertEqual(1, summary['total_by_listed_in'][li])
        self.assertNotIn(deleted_listing, summary['total_by_listed_in'])

        self.delete(show_url)
        updated_summary = self.get_summary()
        self.assertEqual(
            summary['total_by_type'][summary_show['type']] - 1,
            updated_summary['total_by_type'][summary_show['type']])
        for li in listings:
            self.assertNotIn(li, updated_summary['total_by_listed_in'])

    @classmethod
    def create(cls, show: dict) -> dict:
        response = requests.post(f'{SHOWS_API}/', json=show)
        response.raise_for_status()
        return response.json()

    def create_for_test(self, show: dict) -> dict:
        response = requests.post(f'{SHOWS_API}/', json=show)
        response.raise_for_status()
        self.cleanup_after(response)
        self.assert_response(show, response)
        return response.json()

    @classmethod
    def get(cls, show_url: str) -> dict:
        response = requests.get(show_url)
        response.raise_for_status()
        return response.json()

    @classmethod
    def put(cls, show_url, show: dict) -> dict:
        response = requests.put(show_url, json=show)
        response.raise_for_status()
        return response.json()

    @classmethod
    def delete(cls, show_url):
        response = requests.delete(show_url)
        response.raise_for_status()

    @classmethod
    def get_summary(cls):
        response = requests.get(SUMMARY_API)
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
        if 'listed_in' in expected:
            expected['listed_in'] = sorted(expected['listed_in'])
        self.assertDictEqual(expected, actual)
