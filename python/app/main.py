import os
import sys

from fastapi import FastAPI

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import DatabaseConnection, init_logging
from app.routers.alive import alive_router
from app.routers.shows import shows_router


app = FastAPI(
    on_startup=[init_logging, DatabaseConnection.get_connection],
    on_shutdown=[DatabaseConnection.close_connection]
)

app.include_router(alive_router)
app.include_router(shows_router)
