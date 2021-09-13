import csv
import os
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


class TestApp(unittest.TestCase):
    shows = []

    @classmethod
    def setUpClass(cls) -> None:
        response = requests.get(SHOWS_API)
        response.raise_for_status()
        for s in response.json():
            requests.delete(''.join([TEST_URL, s['uri']])).raise_for_status()

        with open(CSV_FILE) as handle:
            reader = csv.reader(handle, delimiter=',', quotechar='"')
            next(reader)
            for i in range(NUM_TEST_SHOWS):
                show = row_to_json(tuple(next(reader)))
                cls.shows.append(cls.create(show))

        cls.shows = sorted(cls.shows, key=lambda s: s['title'])

    @classmethod
    def tearDownClass(cls) -> None:
        for show in cls.shows:
            response = requests.delete(''.join([TEST_URL, show['uri']]))
            response.raise_for_status()

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
        show = {
            'type': 'TV Show',
            'title': 'Welcome Back, Kotter!!!',
            'director': '',
            'cast': (
                'Gabe Kaplan, Marcia Strassman, John Sylvester White, Robert Hegyes, Lawrence Hilton-Jacobs, '
                'Ron Palillo, John Travolta'
            ),
            'country': 'United States',
            'release_year': '2075',
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
        # create the show
        response = requests.post(f'{SHOWS_API}/', json=show)
        self.assert_response(response, show)
        created_show = response.json()

        # get the newly created show
        show_url = ''.join([TEST_URL, created_show['uri']])
        response = requests.get(show_url)
        self.assert_response(response, show)

        # update the show
        show['title'] = 'Welcome Back, Kotter'
        show['release_year'] = '1975'
        response = requests.put(show_url, json=show)
        self.assert_response(response, show)

        response = requests.get(show_url)
        self.assert_response(response, show)

        # delete the show
        response = requests.delete(show_url)
        response.raise_for_status()

        # make sure the show was deleted
        response = requests.get(show_url)
        assert response.status_code == 404

    @classmethod
    def create(cls, show: dict) -> dict:
        response = requests.post(f'{SHOWS_API}/', json=show)
        response.raise_for_status()
        return response.json()

    def assert_response(self, response, show: dict):
        response.raise_for_status()
        response_json = response.json()
        del response_json['show_id']
        del response_json['date_added']
        del response_json['uri']

        # make sure the created show matches the POST body
        self.assertDictEqual(show, response_json)
