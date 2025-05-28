# models.py
from typing import Optional, List
from sqlmodel import SQLModel, Field, create_engine, Session
import datetime


class FavoriteCity(SQLModel, table=True):
    place_id: str = Field(primary_key=True)
    name: str
    coordinate: str
    position: int
    temperature: Optional[int] = Field(default=None)
    weather_condition: str = Field(default="")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


sqlite_file_name = "weather.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def store_new_favorite_cities(locations: List[dict]):
    seen = set()
    favorite_cities = [
        FavoriteCity(
            place_id=location["placeID"],
            name=location["city"],
            coordinate=location["coordinate"],
            position=location["position"],
            temperature=location["temperature"],
            weather_condition=location["condition"],
        )
        for location in locations
        if not (location["placeID"] in seen or seen.add(location["placeID"]))
    ]

    with Session(engine) as session:
        session.query(FavoriteCity).delete()
        session.add_all(favorite_cities)
        session.commit()
