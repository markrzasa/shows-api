from typing import List

SQL_COLUMNS = [
    'show_id', 'type', 'title', 'director', 'cast', 'country', 'date_added', 'release_year', 'rating',
    'duration', 'listed_in', 'description'
]


def show_uri(show_id: str) -> str:
    return f'/shows/{show_id}'


def row_to_json(row: tuple) -> dict:
    show = {SQL_COLUMNS[i]: row[i] for i in range(len(row))}
    cast = show.get('cast')
    listed_in = show.get('listed_in')
    show.update({
        'uri': show_uri(row[0]),
        'cast': [a.strip() for a in cast.split(',')],
        'listed_in': [li.strip() for li in listed_in.split(',')]
    })
    return show


def rows_to_json(rows: List[tuple]) -> List[dict]:
    return [row_to_json(row) for row in rows]
