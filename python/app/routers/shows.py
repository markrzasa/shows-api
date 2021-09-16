import datetime
import os

import sys
import uuid

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.models.shows import Show
from app import DatabaseConnection, INSERT_COLUMNS, LISTED_IN_TABLE, to_db_value
from lib import rows_to_json, row_to_json, SQL_COLUMNS

shows_router = APIRouter(
    prefix='/shows',
    tags=['shows'],
    responses={404: {'description': 'Not found'}},
)


def get_show_from_database(cursor, show_id: str) -> dict:
    cursor.execute(f'SELECT * FROM shows WHERE show_id=\'{show_id}\';')
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='show not fond')
    return row_to_json(row)


def update_listed_in(cursor, show_id: str, show: Show, show_in_db: dict = None):
    db_listed_in = show_in_db.get('listed_in', []) if show_in_db else []
    to_delete = list(set(db_listed_in) - set(show.listed_in))
    to_delete = [to_db_value(to_delete) for d in to_delete]
    if to_delete:
        cursor.execute(f'DELETE FROM {LISTED_IN_TABLE} WHERE listed_in IN ({",".join(to_delete)});')
    for l_in in show.listed_in:
        cursor.execute((
            f"INSERT INTO {LISTED_IN_TABLE} (show_id, listed_in) VALUES('{show_id}', {to_db_value(l_in)}) "
            "ON CONFLICT (show_id, listed_in) DO NOTHING;"
        ))


@shows_router.get('')
async def list_shows(
        limit: Optional[int] = 50,
        offset: Optional[int] = 0,
        sort: Optional[List[str]] = Query(default=['title']),
        filter: Optional[List[str]] = Query(default=[])):
    """
    list a set of shows
    - **limit**: the maximum number of shows to return
    - **offset**: return results starting at this offset
    - **sort**: sort results based on this list of fields. sort can be used more than once
    - **filter**: filter results based on shows with fields like these filters. filter can be used more than once
    """
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
    """
    return the show with the given id
    - **show_id**: return the show with this show_id
    """
    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        return jsonable_encoder(get_show_from_database(cursor, show_id))


@shows_router.put('/{show_id}', response_model=Show)
async def put(show_id: str, show: Show):
    """
    update the show with the given show_id
    - **show_id**: the id of the show to update
    - **show**: body containing fields to update
    """
    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        retrieved_show = get_show_from_database(cursor, show_id)
        show.uri = retrieved_show['uri']
        cursor.execute(f'UPDATE shows SET {show.to_sql_set()} WHERE show_id=\'{show_id}\';')
        update_listed_in(cursor, show_id, show, retrieved_show)
        conn.commit()
        return jsonable_encoder(show)


@shows_router.post('/', response_model=Show)
async def create(show: Show):
    """
    create a show
    - **show**: create a show with these fields. The fields type and title are required.
    """
    show.show_id = str(uuid.uuid4())
    if not show.date_added:
        show.date_added = datetime.datetime.utcnow().strftime('%B %m %Y')
    show.uri = show.to_uri()
    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        cmd = f"INSERT INTO shows ({INSERT_COLUMNS}) VALUES({(show.to_values())});"
        cursor.execute(cmd)
        update_listed_in(cursor, show.show_id, show)
        conn.commit()
        return show


@shows_router.delete('/{show_id}')
async def delete(show_id: str):
    """
    delete the show with the given id
    - **show_id**: the show with this id will be deleted
    """
    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        cmd = f"DELETE FROM shows WHERE show_id='{show_id}';"
        cursor.execute(cmd)
        conn.commit()
