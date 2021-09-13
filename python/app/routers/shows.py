import datetime
import os
from typing import List

import sys
import uuid

from fastapi import APIRouter, HTTPException
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


@shows_router.get('/')
async def list_shows(limit: int = 50, offset: int = 0, sort: List[str] = None):
    if not sort:
        sort = ['title']

    invalid_columns = [c for c in SQL_COLUMNS if c not in SQL_COLUMNS]
    if invalid_columns:
        raise HTTPException(status_code=400, detail=f'invalid sort parameter {", ".join(sort)}')

    conn = DatabaseConnection.get_connection()
    with conn.cursor() as cursor:
        # postgres sort like python to make testing either
        cursor.execute(f'SELECT * FROM shows ORDER BY {",".join(sort)} collate "C" LIMIT {limit} OFFSET {offset};')
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
