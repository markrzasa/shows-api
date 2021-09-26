from typing import Optional, List, Type, Any

from pydantic import BaseModel


class ShowCreate(BaseModel):
    type: str
    title: str
    director: Optional[str] = ''
    cast: Optional[List[str]] = []
    country: Optional[str] = ''
    date_added: Optional[str] = ''
    release_year: Optional[str] = ''
    rating: Optional[str] = ''
    duration: Optional[str] = ''
    listed_in: Optional[List[str]] = []
    description: Optional[str] = ''


class Show(ShowCreate):
    id: Optional[int] = None
    uri: Optional[str] = None

    class Config:
        orm_mode = True
