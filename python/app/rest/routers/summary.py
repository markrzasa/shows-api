import os
import sys

from fastapi import APIRouter

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import Engine, persistence

summary_router = APIRouter(
    prefix='/summary',
    tags=['shows_summary'],
    responses={404: {'description': 'Not found'}},
)


def _total(session) -> int:
    return session.query(persistence.Show).count()


def _total_for_listed_in(session, listed_in: str) -> int:
    return session.query(persistence.ListedIn).filter(persistence.ListedIn.listed_in == listed_in).count()


def _listed_in_totals(session) -> dict:
    return {
        listing.listed_in: _total_for_listed_in(session, listing.listed_in)
        for listing in session.query(persistence.ListedIn).distinct(persistence.ListedIn.listed_in).all()
    }


def _total_for_type(session, show_type: str) -> int:
    return session.query(persistence.Show).filter(persistence.Show.type == show_type).count()


def _type_totals(session) -> dict:
    return {
        show.type: _total_for_type(session, show.type)
        for show in session.query(persistence.Show).distinct(persistence.Show.type).all()
    }


def _summarize(session) -> dict:
    return {
        'total': _total(session),
        'total_by_listed_in': _listed_in_totals(session),
        'total_by_type': _type_totals(session)
    }


@summary_router.get('')
async def shows_summary():
    """
    return aggregated data for the shows managed by this service
    """
    with Engine.new_session() as session:
        return _summarize(session)
