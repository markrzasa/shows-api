import os
import sys

from fastapi import APIRouter

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import DatabaseConnection

alive_router = APIRouter(
    prefix='/alive',
    tags=['alive'],
    responses={404: {'description': 'Not found'}},
)


@alive_router.get('')
async def alive():
    return {'alive': True if DatabaseConnection.get_connection() else False}
