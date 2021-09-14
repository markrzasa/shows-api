import datetime
import os

import sys
import uuid

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.models.shows import Show
from app import DatabaseConnection, INSERT_COLUMNS
from lib import rows_to_json, row_to_json, SQL_COLUMNS

shows_router = APIRouter(
    prefix='/shows',
    tags=['shows'],
    responses={404: {'description': 'Not found'}},
)


def __get_show_from_database(cursor, show_id: str) -> dict:
    cursor.execute(f'SELECT * FROM shows WHERE show_id=\'{show_id}\';')
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='show not fond')
    return row_to_json(row)


@shows_router.get('')
async def list_shows(
        limit: Optional[int] = 50,
        offset: Optional[int] = 0,
        sort: Optional[List[str]] = Query(default=['title']),
        filter: Optional[List[str]] = Query(default=[])):
    sort_list = [c.strip() for c in sort]
    invalid_sort_columns = [c for c in sort_list if c not in SQL_COLUMNS]
    if invalid_sort_columns:
        raise HTTPException(status_code=400, detail=f'invalid sort parameter {", ".join(sort_list)}')

    filter_columns = {}
    if filter:
        filter_columns = {f.split('=', 1)[0].strip(): f.split('=', 1)[-1].strip() for f in filter}
        invalid_filter_columns = [c for c in filter_columns.keys() if c not in SQL_COLUMNS]
        if invalid_filter_columns:
            raise HTTPException(status_code=400, detail=f'invalid filters parameter {filter}')

    where_clause = ''
    if filter_columns:
        where_clause = 'WHERE ' + ' AND '.join([f"{c} LIKE '%{v}%'" for c, v in filter_columns.items()])
        where_clause = where_clause + ' '

    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        # postgres sort like python to make testing either
        cursor.execute((
            f'SELECT * FROM shows {where_clause}ORDER BY {",".join(sort_list)} '
            f'collate "C" LIMIT {limit} OFFSET {offset};'
        ))
        response = []
        rows = cursor.fetchmany(10)
        while rows:
            response.extend(rows_to_json(rows))
            rows = cursor.fetchmany(10)
        return response


@shows_router.get('/{show_id}', response_model=Show)
async def get(show_id: str):
    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        return jsonable_encoder(__get_show_from_database(cursor, show_id))


@shows_router.put('/{show_id}', response_model=Show)
async def put(show_id: str, show: Show):
    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        retrieved_show = __get_show_from_database(cursor, show_id)
        show.uri = retrieved_show['uri']
        cursor.execute(f'UPDATE shows SET {show.to_sql_set()} WHERE show_id=\'{show_id}\';')
        return jsonable_encoder(show)


@shows_router.post('/', response_model=Show)
async def create(show: Show):
    show.show_id = str(uuid.uuid4())
    if not show.date_added:
        show.date_added = datetime.datetime.utcnow().strftime('%B %m %Y')
    show.uri = show.to_uri()
    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        cmd = f"INSERT INTO shows ({INSERT_COLUMNS}) VALUES({(show.to_values())});"
        cursor.execute(cmd)
        conn.commit()
        return show


@shows_router.delete('/{show_id}')
async def delete(show_id: str):
    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        cmd = f"DELETE FROM shows WHERE show_id='{show_id}';"
        cursor.execute(cmd)
        conn.commit()