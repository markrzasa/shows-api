from typing import Optional

import json
from pydantic import BaseModel

from app import escape_value
from lib import SQL_COLUMNS, show_uri


class Show(BaseModel):
    show_id: Optional[str] = None
    type: str
    title: str
    director: Optional[str] = ''
    cast: Optional[str] = ''
    country: Optional[str] = ''
    date_added: Optional[str] = ''
    release_year: Optional[str] = ''
    rating: Optional[str] = ''
    duration: Optional[str] = ''
    listed_in: Optional[str] = ''
    description: Optional[str] = ''
    uri: Optional[str] = None

    def to_values(self) -> str:
        show_json = json.loads(self.json())
        return ','.join([escape_value(show_json[c]) for c in SQL_COLUMNS])

    def to_sql_set(self) -> str:
        show_json = json.loads(self.json())
        return ','.join([f'"{c}" = {escape_value(show_json[c])}' for c in SQL_COLUMNS if show_json[c]])

    def to_uri(self) -> str:
        return show_uri(self.show_id)
