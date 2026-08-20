from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# ORM tables (circuits, races, results, drivers, constructors, standings,
# predictions, weather) go here once the SQLite schema is designed —
# that's the next planning step after this scaffold, not done yet.
