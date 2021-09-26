import os
import sys

from fastapi import APIRouter

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

alive_router = APIRouter(
    prefix='/alive',
    tags=['alive'],
    responses={404: {'description': 'Not found'}},
)


@alive_router.get('')
async def alive():
    """
    return whether or not the service is alive
    """
    return {'alive': True}
