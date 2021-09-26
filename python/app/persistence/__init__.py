import inspect
from sqlalchemy import Column, String, ForeignKey, PrimaryKeyConstraint, Integer
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Show(Base):
    __tablename__ = 'shows'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(collation='C'))
    title = Column(String(collation='C'))
    director = Column(String(collation='C'))
    country = Column(String(collation='C'))
    date_added = Column(String(collation='C'))
    release_year = Column(String(collation='C'))
    rating = Column(String(collation='C'))
    duration = Column(String(collation='C'))
    description = Column(String(collation='C'))


class Actor(Base):
    __tablename__ = 'actor'
    __table_args__ = (
        PrimaryKeyConstraint('id', 'name'),
    )
    id = Column(Integer, ForeignKey('shows.id', ondelete='CASCADE'))
    name = Column(String)
    items = relationship('Show')


class ListedIn(Base):
    __tablename__ = 'listed_in'
    __table_args__ = (
        PrimaryKeyConstraint('id', 'listed_in'),
    )
    id = Column(Integer, ForeignKey('shows.id', ondelete='CASCADE'))
    listed_in = Column(String)
    items = relationship('Show')


SQL_COLUMNS = [
    m[0] for m in inspect.getmembers(Show, lambda a:not(inspect.isroutine(a)))
    if not m[0].startswith('_') and m[0] not in ['metadata', 'registry']
]
