import datetime
import os

import sys

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import Engine, persistence
from app.persistence import SQL_COLUMNS, ListedIn, Actor
from app.rest.models.shows import Show, ShowCreate
from lib import show_uri

shows_router = APIRouter(
    prefix='/shows',
    tags=['shows'],
    responses={404: {'description': 'Not found'}},
)


def from_db_show(session, show_id: int) -> Show:
    db_show = session.query(persistence.Show).filter(persistence.Show.id == show_id).one()
    cast = session.query(persistence.Actor).filter(persistence.Actor.id == show_id).all()
    listed_in = session.query(persistence.ListedIn).filter(persistence.ListedIn.id == show_id).all()
    show = Show(type=db_show.type, title=db_show.title)
    show.director = db_show.director
    show.cast = sorted([actor.name for actor in cast])
    show.country = db_show.country
    show.date_added = db_show.date_added
    show.release_year = db_show.release_year
    show.rating = db_show.rating
    show.duration = db_show.duration
    show.listed_in = sorted([listing.listed_in for listing in listed_in])
    show.description = db_show.description
    show.id = db_show.id
    show.uri = show_uri(db_show.id)
    return show


def to_db_show(show: ShowCreate) -> persistence.Show:
    return persistence.Show(
        type=show.type,
        title=show.title,
        director=show.director,
        country=show.country,
        date_added=show.date_added,
        release_year=show.release_year,
        rating=show.rating,
        duration=show.duration,
        description=show.description
    )


def update_cast(session, show_id: int, show: ShowCreate, db_show: persistence.Show = None):
    actors = session.query(persistence.Actor).filter(persistence.Actor.id == show_id).all()
    db_actors = [a.name for a in actors]
    to_delete = list(set([a for a in db_actors if a not in show.cast]))
    for d in to_delete:
        actor = session.query(persistence.Actor).filter(
            persistence.Actor.id == show_id).filter(
            persistence.Actor.name == d).one()
        session.delete(actor)

    to_add = list(set([a for a in show.cast if a not in db_actors]))
    for a in to_add:
        actor = Actor()
        actor.id = db_show.id
        actor.name = a
        session.add(actor)


def update_listed_in(session, show_id: int, show: ShowCreate, db_show: persistence.Show = None):
    listings = session.query(persistence.ListedIn).filter(persistence.ListedIn.id == show_id).all()
    db_listed_in = [listing.listed_in for listing in listings]
    to_delete = list(set([listing for listing in db_listed_in if listing not in show.listed_in]))
    for d in to_delete:
        listed_in = session.query(persistence.ListedIn).filter(
            persistence.ListedIn.id == show_id).filter(
            persistence.ListedIn.listed_in == d).one()
        session.delete(listed_in)

    to_add = list(set([listing for listing in show.listed_in if listing not in db_listed_in]))
    for a in to_add:
        listed_in = ListedIn()
        listed_in.id = db_show.id
        listed_in.listed_in = a
        session.add(listed_in)


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

    filters = {}
    if filter:
        filters = {f.split('=', 1)[0].strip(): f.split('=', 1)[-1].strip() for f in filter}
        invalid_filter_columns = [c for c in filters.keys() if c not in SQL_COLUMNS]
        if invalid_filter_columns:
            raise HTTPException(status_code=400, detail=f'invalid filters parameter {filter}')

    with Engine.new_session() as session:
        q = session.query(persistence.Show)
        for s in sort_list:
            q = q.order_by(persistence.Show.__dict__[s])
        for k, v in filters.items():
            q = q.filter(persistence.Show.__dict__[k].like(v))
        shows = q.offset(offset).limit(limit).all()
        return [from_db_show(session, s.id) for s in shows]


@shows_router.get('/{show_id}', response_model=Show)
async def get(show_id: int):
    """
    return the show with the given id
    - **show_id**: return the show with this show_id
    """
    with Engine.new_session() as session:
        shows = session.query(persistence.Show).filter_by(id=show_id).all()
        if len(shows) > 1:
            raise HTTPException(status_code=500, detail='unexpected number of shows found')
        if len(shows) < 1:
            raise HTTPException(status_code=404, detail='show not found')
        return from_db_show(session, shows[0].id)


@shows_router.put('/{show_id}', response_model=Show)
async def put(show_id: int, show: Show):
    """
    update the show with the given show_id
    - **show_id**: the id of the show to update
    - **show**: body containing fields to update
    """
    with Engine.new_session() as session:
        shows = session.query(persistence.Show).filter_by(id=show_id).all()
        if len(shows) > 1:
            raise HTTPException(status_code=500, detail='unexpected number of shows found')
        if len(shows) < 1:
            raise HTTPException(status_code=404, detail='show not found')

        if show.type:
            shows[0].type = show.type
        if show.title:
            shows[0].title = show.title
        if show.director:
            shows[0].director = show.director
        if show.cast:
            shows[0].cast = ','.join(show.cast)
        if show.country:
            shows[0].country = show.country
        if show.date_added:
            shows[0].date_added = show.date_added
        if show.release_year:
            shows[0].release_year = show.release_year
        if show.rating:
            shows[0].rating = show.rating
        if show.duration:
            shows[0].duration = show.duration
        if show.description:
            shows[0].description = show.description
        update_cast(session, show_id, show, shows[0])
        update_listed_in(session, show_id, show, shows[0])
        session.commit()
        return from_db_show(session, shows[0].id)


@shows_router.post('/', response_model=Show)
async def create(show: ShowCreate):
    """
    create a show
    - **show**: create a show with these fields. The fields type and title are required.
    """
    if not show.date_added:
        show.date_added = datetime.datetime.utcnow().strftime('%B %m %Y')
    db_show = to_db_show(show)
    with Engine.new_session() as session:
        session.add(db_show)
        update_cast(session, db_show.id, show, db_show)
        update_listed_in(session, db_show.id, show, db_show)
        session.commit()
        return from_db_show(session, db_show.id)


@shows_router.delete('/{show_id}')
async def delete(show_id: int):
    """
    delete the show with the given id
    - **show_id**: the show with this id will be deleted
    """
    with Engine.new_session() as session:
        shows = session.query(persistence.Show).filter_by(id=show_id).all()
        if len(shows) > 1:
            raise HTTPException(status_code=500, detail='unexpected number of shows to delete')
        if len(shows) == 1:
            session.delete(shows[0])
            session.commit()
