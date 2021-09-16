import os
import sys

from fastapi import APIRouter

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import DatabaseConnection, SHOWS_TABLE, LISTED_IN_TABLE, to_db_value

summary_router = APIRouter(
    prefix='/summary',
    tags=['shows_summary'],
    responses={404: {'description': 'Not found'}},
)


def _total(cursor) -> int:
    cursor.execute(f'SELECT count(*) FROM {SHOWS_TABLE};')
    row = cursor.fetchone()
    return int(row[0])


def _total_for_listed_in(cursor, listed_in: str) -> int:
    cursor.execute(f'SELECT count(*) FROM {LISTED_IN_TABLE} WHERE listed_in={to_db_value(listed_in)};')
    row = cursor.fetchone()
    return int(row[0])


def _listed_in_totals(cursor) -> dict:
    cursor.execute(f'SELECT DISTINCT listed_in FROM {LISTED_IN_TABLE};')
    rows = cursor.fetchall()
    return {t: _total_for_listed_in(cursor, t) for t in [r[0] for r in rows]}


def _total_for_type(cursor, show_type: str) -> int:
    cursor.execute(f'SELECT count(*) FROM {SHOWS_TABLE} WHERE type={to_db_value(show_type)};')
    row = cursor.fetchone()
    return int(row[0])


def _type_totals(cursor) -> dict:
    cursor.execute(f'SELECT DISTINCT type FROM {SHOWS_TABLE};')
    rows = cursor.fetchall()
    return {t: _total_for_type(cursor, t) for t in [r[0] for r in rows]}


def _summarize(cursor) -> dict:
    return {
        'total': _total(cursor),
        'total_by_listed_in': _listed_in_totals(cursor),
        'total_by_type': _type_totals(cursor)
    }


@summary_router.get('')
async def shows_summary():
    """
    return aggregated data for the shows managed by this service
    """
    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        return _summarize(cursor)
