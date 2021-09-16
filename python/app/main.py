import os
import sys

from fastapi import FastAPI

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import DatabaseConnection, init_logging
from app.routers.alive import alive_router
from app.routers.shows import shows_router
from app.routers.summary import summary_router

tags_metadata = [
    {
        'name': 'shows',
        'description': 'this API allows you to manage a library of shows'
    },
    {
        'name': 'shows_summary',
        'description': 'this API retrieves an aggregated summary of the shows stored in the shows services'
    },
    {
        'name': 'alive',
        'description': 'determine if the service backing this API is healthy'
    }
]

app = FastAPI(
    on_startup=[init_logging, DatabaseConnection.get_connection],
    on_shutdown=[DatabaseConnection.close_connection],
    openapi_tags=tags_metadata
)

app.include_router(alive_router)
app.include_router(shows_router)
app.include_router(summary_router)
